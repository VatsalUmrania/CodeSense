import boto3
from botocore.exceptions import ClientError
from botocore.config import Config
from typing import Optional, BinaryIO, Dict
from app.core.config import settings

class StorageService:
    def __init__(self):
        self.client = boto3.client(
            "s3",
            endpoint_url=str(settings.MINIO_URL),
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            config=Config(signature_version="s3v4"),
        )
        self.bucket = settings.MINIO_BUCKET_NAME
        self._ensure_bucket()

    def _ensure_bucket(self):
        """Idempotent bucket creation handling concurrency."""
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError as e:
            # 404 means it doesn't exist
            if e.response["Error"]["Code"] == "404":
                try:
                    self.client.create_bucket(Bucket=self.bucket)
                except ClientError as ce:
                    # Handle race condition: another worker created it just now
                    if ce.response["Error"]["Code"] not in ("BucketAlreadyOwnedByYou", "BucketAlreadyExists"):
                        raise RuntimeError(f"Failed to create bucket: {ce}")
            else:
                raise

    def upload_object(
        self, 
        path: str, 
        data: bytes | BinaryIO, 
        content_type: str = "application/octet-stream",
        metadata: Optional[Dict[str, str]] = None
    ):
        """
        Atomic upload using If-None-Match="*".
        If object exists, it silently returns (idempotency).
        """
        extra_args = {
            "ContentType": content_type, 
            "IfNoneMatch": "*"
        }
        if metadata:
            extra_args["Metadata"] = metadata

        try:
            if isinstance(data, bytes):
                self.client.put_object(
                    Bucket=self.bucket, Key=path, Body=data, **extra_args
                )
            else:
                self.client.upload_fileobj(
                    data, self.bucket, path, ExtraArgs=extra_args
                )
        except ClientError as e:
            # 412 Precondition Failed means object already exists
            if e.response["Error"]["Code"] in ("PreconditionFailed", "412"):
                return
            raise RuntimeError(f"Storage upload failed for {path}: {str(e)}")

    def get_object(self, path: str, max_bytes: int = 10 * 1024 * 1024) -> bytes:
        """Fetch small artifacts only (Max 10MB default)."""
        try:
            # Check size before downloading
            head = self.client.head_object(Bucket=self.bucket, Key=path)
            if head["ContentLength"] > max_bytes:
                raise ValueError(f"Object {path} is too large ({head['ContentLength']} bytes) for memory.")

            response = self.client.get_object(Bucket=self.bucket, Key=path)
            return response["Body"].read()
        except ClientError as e:
            raise FileNotFoundError(f"Object {path} not found: {str(e)}")

    def get_presigned_url(self, path: str, expiration: int = 3600) -> str:
        try:
            return self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": path},
                ExpiresIn=expiration,
            )
        except ClientError as e:
            raise RuntimeError(f"URL generation failed for {path}: {str(e)}")