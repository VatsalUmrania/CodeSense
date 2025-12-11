from minio import Minio
import io
import json
import os

class StorageService:
    def __init__(self):
        self.client = Minio(
            "minio:9000", 
            access_key="minioadmin",
            secret_key="minioadmin",
            secure=False
        )
        self.bucket = "repos"
        self._ensure_bucket()

    def _ensure_bucket(self):
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)

    def _get_object_path(self, repo_id: str, filename: str) -> str:
        """Standardizes path generation: {repo_id}/{filename}"""
        return f"{repo_id}/{filename}"

    def upload_file(self, file_path: str, repo_id: str, filename: str = "source.zip"):
        """Uploads a file to the repo's specific folder."""
        object_name = self._get_object_path(repo_id, filename)
        self.client.fput_object(self.bucket, object_name, file_path)
        print(f"Uploaded {object_name} to MinIO.")

    def upload_json(self, data: dict, repo_id: str, filename: str = "graph.json"):
        """Uploads JSON data to the repo's specific folder."""
        object_name = self._get_object_path(repo_id, filename)
        json_bytes = json.dumps(data).encode('utf-8')
        self.client.put_object(
            self.bucket,
            object_name,
            io.BytesIO(json_bytes),
            len(json_bytes),
            content_type="application/json"
        )
        print(f"Uploaded {object_name} to MinIO.")

    def get_json(self, repo_id: str, filename: str = "graph.json") -> dict:
        """Retrieves a specific JSON artifact for a repo."""
        object_name = self._get_object_path(repo_id, filename)
        try:
            response = self.client.get_object(self.bucket, object_name)
            content = response.read().decode('utf-8')
            return json.loads(content)
        except Exception as e:
            print(f"Error fetching {object_name}: {e}")
            return {}

    def get_file_content(self, repo_id: str, file_path: str):
        """Extracts a file from the source.zip within the repo folder."""
        import zipfile
        object_name = self._get_object_path(repo_id, "source.zip")
        
        try:
            # Clean path
            if file_path.startswith('/'):
                file_path = file_path[1:]

            response = self.client.get_object(self.bucket, object_name)
            with zipfile.ZipFile(io.BytesIO(response.read())) as z:
                with z.open(file_path) as f:
                    return f.read().decode('utf-8', errors='ignore')
        except Exception as e:
            print(f"Error fetching file {file_path} from {repo_id}: {e}")
            return None

    def list_files(self, repo_id: str):
        """Lists files inside the source.zip."""
        import zipfile
        object_name = self._get_object_path(repo_id, "source.zip")
        
        try:
            response = self.client.get_object(self.bucket, object_name)
            with zipfile.ZipFile(io.BytesIO(response.read())) as z:
                return [f for f in z.namelist() if not f.endswith('/') and '/.' not in f and not f.startswith('.')]
        except Exception as e:
            print(f"List files error: {e}")
            return []

    def delete_repo(self, repo_id: str):
        """
        Deletes ALL objects with the prefix {repo_id}/.
        This is much more robust than deleting specific files manually.
        """
        # List all objects in the "folder"
        objects_to_delete = self.client.list_objects(self.bucket, prefix=f"{repo_id}/", recursive=True)
        
        # MinIO/S3 requires deleting objects one by one or in batch
        # list_objects returns an iterator of objects
        count = 0
        for obj in objects_to_delete:
            self.client.remove_object(self.bucket, obj.object_name)
            count += 1
            
        print(f"Deleted {count} objects for repo {repo_id}")