import io
from enum import Enum
from minio import Minio
from app.core.config import settings

# 1. Define Artifact Types
class ArtifactType(str, Enum):
    GRAPH_DATA = "graph_data"
    MANIFEST = "manifest"
    AST_DATA = "ast_data"
    SOURCE_CODE = "source_code"
    SOURCE_TREE = "source_tree"  # Complete source tarball for call graph analysis

# 2. Define Path Helper
class StoragePaths:
    @staticmethod
    def get_artifact_path(provider: str, owner: str, name: str, commit_sha: str, artifact_type: ArtifactType) -> str:
        """
        Generates a structured path for object storage.
        Format: github/owner/repo/commit_sha/artifact_type
        """
        # Ensure we use the value of the enum if passed
        type_str = artifact_type.value if isinstance(artifact_type, ArtifactType) else artifact_type
        return f"{provider}/{owner}/{name}/{commit_sha}/{type_str}"

# 3. Define the Storage Service (MinIO Implementation)
class StorageService:
    def __init__(self):
        # --- FIX: DEFINE 'endpoint' VARIABLE FIRST ---
        # Strip http/https because MinIO client expects "host:port"
        endpoint = settings.MINIO_URL.replace("http://", "").replace("https://", "")

        # --- NOW USE IT ---
        self.client = Minio(
            endpoint=endpoint,  # <--- Now this variable exists!
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False,
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME
        
        self._ensure_bucket()

    def _ensure_bucket(self):
        if not self.client.bucket_exists(self.bucket_name):
            self.client.make_bucket(self.bucket_name)

    def upload_object(self, path: str, data: bytes, content_type: str = "application/octet-stream"):
        """
        Uploads bytes to MinIO.
        """
        file_data = io.BytesIO(data)
        self.client.put_object(
            bucket_name=self.bucket_name,
            object_name=path,
            data=file_data,
            length=len(data),
            content_type=content_type
        )

    def download_object(self, path: str) -> bytes:
        """
        Downloads bytes from MinIO.
        """
        response = None
        try:
            response = self.client.get_object(self.bucket_name, path)
            return response.read()
        finally:
            if response:
                response.close()
                
    def get_presigned_url(self, path: str, method: str = "GET") -> str:
        """
        Generates a presigned URL for frontend access.
        """
        return self.client.get_presigned_url(
            method,
            self.bucket_name,
            path
        )