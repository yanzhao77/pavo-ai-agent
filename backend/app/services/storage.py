"""Local file storage — replaces MinIO/S3 (boto3).

Public interface is intentionally kept compatible with the old StorageClient:
  upload_bytes(data, object_name, content_type) -> str
  get_url(object_name) -> str
  delete(object_name) -> bool
  mount_static(app)          — mount FastAPI StaticFiles

Files are stored under ~/.pavo/storage/ (or $PAVO_HOME/storage/).
The static server exposes them at /static/<object_name>.
"""
import logging
import os
from pathlib import Path

from fastapi.staticfiles import StaticFiles

logger = logging.getLogger(__name__)

# ── Storage root ──────────────────────────────────────────────────────────────
_env_home = os.environ.get("PAVO_HOME", "")
_PAVO_HOME = Path(_env_home) if _env_home else Path.home() / ".pavo"
STORAGE_DIR = _PAVO_HOME / "storage"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

_STATIC_PORT = int(os.environ.get("PAVO_STATIC_PORT", "18080"))


class StorageClient:
    """Local filesystem storage client — drop-in replacement for MinIO."""

    def __init__(self, base_dir: str = ""):
        self.base_dir = Path(base_dir) if base_dir else STORAGE_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def upload_bytes(self, data: bytes, object_name: str,
                     content_type: str = "video/mp4") -> str:
        fp = self.base_dir / object_name
        fp.parent.mkdir(parents=True, exist_ok=True)
        with open(fp, "wb") as f:
            f.write(data)
        logger.info(f"Saved {len(data)} bytes to {fp}")
        return self.get_url(object_name)

    def get_url(self, object_name: str) -> str:
        return f"http://localhost:{_STATIC_PORT}/static/{object_name}"

    def delete(self, object_name: str) -> bool:
        fp = self.base_dir / object_name
        if fp.exists():
            fp.unlink()
            logger.info(f"Deleted {fp}")
            return True
        return False

    def mount_static(self, app) -> None:
        if self.base_dir.exists():
            app.mount("/static", StaticFiles(directory=str(self.base_dir)), name="static")
            logger.info(f"Static files served from {self.base_dir} at /static")


_storage: StorageClient | None = None


def get_storage() -> StorageClient:
    global _storage
    if _storage is None:
        _storage = StorageClient()
    return _storage
