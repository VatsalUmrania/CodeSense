from minio import Minio
import os

class StorageService:
    def __init__(self):
        self.client = Minio(
            "minio:9000", # Docker service name
            access_key="minioadmin",
            secret_key="minioadmin",
            secure=False
        )
        self.bucket = "repos"
        self._ensure_bucket()

    def _ensure_bucket(self):
        """Create the bucket if it doesn't exist."""
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)

    def upload_file(self, file_path: str, object_name: str):
        """Upload a file to MinIO."""
        self.client.fput_object(
            self.bucket, object_name, file_path
        )
        print(f"Uploaded {object_name} to MinIO.")