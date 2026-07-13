"""Tests for local file storage (replaces MinIO/boto3)."""
import pytest
import tempfile
from pathlib import Path


class TestStorageClient:
    def test_upload_bytes_creates_file(self, tmp_path):
        from app.services.storage import StorageClient
        client = StorageClient(base_dir=str(tmp_path))
        url = client.upload_bytes(b"hello world", "videos/test.mp4")
        assert (tmp_path / "videos" / "test.mp4").exists()
        assert "test.mp4" in url

    def test_get_url_format(self, tmp_path):
        from app.services.storage import StorageClient
        client = StorageClient(base_dir=str(tmp_path))
        url = client.get_url("videos/test.mp4")
        assert url.startswith("http://localhost:")
        assert "test.mp4" in url

    def test_delete_existing_file(self, tmp_path):
        from app.services.storage import StorageClient
        client = StorageClient(base_dir=str(tmp_path))
        client.upload_bytes(b"data", "v/shot.mp4")
        assert client.delete("v/shot.mp4") is True
        assert not (tmp_path / "v" / "shot.mp4").exists()

    def test_delete_nonexistent_file(self, tmp_path):
        from app.services.storage import StorageClient
        client = StorageClient(base_dir=str(tmp_path))
        assert client.delete("nonexistent.mp4") is False

    def test_no_boto3_import(self):
        """Ensure boto3 is not imported anywhere in storage module."""
        import importlib, sys
        # Remove cached module to force fresh import
        sys.modules.pop("app.services.storage", None)
        import app.services.storage as m
        src = Path(m.__file__).read_text()
        assert "boto3" not in src
        assert "botocore" not in src
