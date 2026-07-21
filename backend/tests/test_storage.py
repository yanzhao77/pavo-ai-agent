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
        """Ensure boto3 is not imported (as an import statement) in storage module."""
        import ast, importlib, sys
        sys.modules.pop("app.services.storage", None)
        import app.services.storage as m
        src = Path(m.__file__).read_text(encoding="utf-8")
        tree = ast.parse(src)
        imported_names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_names.extend(n.name.split(".")[0] for n in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_names.append(node.module.split(".")[0])
        assert "boto3" not in imported_names, "boto3 must not be imported in storage.py"
        assert "botocore" not in imported_names, "botocore must not be imported in storage.py"
