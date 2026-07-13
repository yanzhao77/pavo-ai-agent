"""Local file storage - replaces MinIO."""
import logging
from pathlib import Path
from fastapi.staticfiles import StaticFiles
logger = logging.getLogger(__name__)
STORAGE_DIR = Path.home() / ".pavo" / "storage"

class LocalStorageClient:
    def __init__(self, base_dir=""):
        self.base_dir = Path(base_dir) if base_dir else STORAGE_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)
    def upload(self, data: bytes, object_name: str) -> str:
        fp = self.base_dir / object_name; fp.parent.mkdir(parents=True, exist_ok=True)
        with open(fp, "wb") as f: f.write(data)
        logger.info(f"Saved {len(data)}B to {fp}"); return str(fp)
    def delete(self, object_name: str) -> bool:
        fp = self.base_dir / object_name
        if fp.exists(): fp.unlink(); return True
        return False
    def get_url(self, object_name: str) -> str: return f"/static/{object_name}"
    def mount_static(self, app):
        if self.base_dir.exists(): app.mount("/static", StaticFiles(directory=str(self.base_dir)), name="static")

local_storage = LocalStorageClient()
