# from minio import Minio
# import os

# class StorageService:
#     def __init__(self):
#         self.client = Minio(
#             "minio:9000", # Docker service name
#             access_key="minioadmin",
#             secret_key="minioadmin",
#             secure=False
#         )
#         self.bucket = "repos"
#         self._ensure_bucket()

#     def _ensure_bucket(self):
#         """Create the bucket if it doesn't exist."""
#         if not self.client.bucket_exists(self.bucket):
#             self.client.make_bucket(self.bucket)

#     def upload_file(self, file_path: str, object_name: str):
#         """Upload a file to MinIO."""
#         self.client.fput_object(
#             self.bucket, object_name, file_path
#         )
#         print(f"Uploaded {object_name} to MinIO.")

from minio import Minio
import os
import zipfile
import io

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

    def upload_file(self, file_path: str, object_name: str):
        self.client.fput_object(self.bucket, object_name, file_path)
        print(f"Uploaded {object_name} to MinIO.")

    def get_file_content(self, repo_id: str, file_path: str):
        """Extracts a single file from the stored repo zip."""
        try:
            # Get the zip object from MinIO
            response = self.client.get_object(self.bucket, f"{repo_id}.zip")
            # Read zip into memory
            with zipfile.ZipFile(io.BytesIO(response.read())) as z:
                # Read the specific file
                with z.open(file_path) as f:
                    return f.read().decode('utf-8', errors='ignore')
        except Exception as e:
            print(f"Error fetching file {file_path} from {repo_id}: {e}")
            return None