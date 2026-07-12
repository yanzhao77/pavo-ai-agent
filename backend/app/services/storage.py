import logging
import boto3
from botocore.exceptions import ClientError
from app.config import settings

logger = logging.getLogger(__name__)


class StorageClient:
    """MinIO/S3 storage client for video files. Lazy initialization."""

    def __init__(self, lazy=True):
        self.endpoint_url = settings.minio_endpoint
        self.bucket = settings.minio_bucket
        self._client = None
        self._lazy = lazy
        if not lazy:
            self._get_client()

    def _get_client(self):
        if self._client is None:
            self._client = boto3.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=settings.minio_access_key,
                aws_secret_access_key=settings.minio_secret_key,
            )
        return self._client

    def _ensure_bucket(self):
        try:
            client = self._get_client()
            try:
                client.head_bucket(Bucket=self.bucket)
            except ClientError:
                client.create_bucket(Bucket=self.bucket)
                logger.info(f"Created bucket: {self.bucket}")
        except Exception as e:
            logger.warning(f"Cannot access bucket {self.bucket}: {e}")

    def upload_bytes(self, data: bytes, object_name: str, content_type: str = "video/mp4") -> str:
        try:
            client = self._get_client()
            self._ensure_bucket()
            client.put_object(
                Bucket=self.bucket, Key=object_name,
                Body=data, ContentType=content_type,
            )
            url = f"{self.endpoint_url}/{self.bucket}/{object_name}"
            logger.info(f"Uploaded {object_name}")
            return url
        except ClientError as e:
            logger.error(f"Upload failed: {e}")
            return ""

    def get_url(self, object_name: str) -> str:
        return f"{self.endpoint_url}/{self.bucket}/{object_name}"

    def delete(self, object_name: str) -> bool:
        try:
            client = self._get_client()
            client.delete_object(Bucket=self.bucket, Key=object_name)
            return True
        except ClientError as e:
            logger.error(f"Delete failed: {e}")
            return False


# Lazy singleton - only created when first used
_storage: StorageClient = None

def get_storage() -> StorageClient:
    global _storage
    if _storage is None:
        _storage = StorageClient()
    return _storage
