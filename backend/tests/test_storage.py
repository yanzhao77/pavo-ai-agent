"""Tests for MinIO storage module (T3.4)."""
import pytest
from unittest.mock import patch, MagicMock


class TestStorageClient:
    def test_upload_bytes(self):
        with patch("app.services.storage.boto3.client") as mock_client:
            mock_s3 = MagicMock()
            mock_client.return_value = mock_s3
            from app.services.storage import StorageClient
            client = StorageClient(lazy=True)
            # Manually replace the client
            client._client = mock_s3
            url = client.upload_bytes(b"test", "v/test.mp4")
            assert "test.mp4" in url
            mock_s3.put_object.assert_called_once()

    def test_get_url(self):
        from app.services.storage import StorageClient
        client = StorageClient(lazy=True)
        url = client.get_url("v/test.mp4")
        assert url.endswith("test.mp4")

    def test_delete(self):
        with patch("app.services.storage.boto3.client") as mock_client:
            mock_s3 = MagicMock()
            mock_client.return_value = mock_s3
            from app.services.storage import StorageClient
            client = StorageClient(lazy=True)
            client._client = mock_s3
            result = client.delete("v/test.mp4")
            assert result is True
