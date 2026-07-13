"""Pavo AI Agent — FastAPI application and CLI entry points.

Entry points (pyproject.toml):
  pavo-mcp-server  →  mcp_server.main:main   (MCP stdio server only)
  pavo-start       →  app.main:start_app     (MCP + static file server + optional frontend)
"""
import asyncio
import logging
import os
import subprocess
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import settings
from app.db.database import init_db, PAVO_HOME
from app.api.routes import router


# ── Logging ───────────────────────────────────────────────────────────────────

def setup_logging(pavo_home: Path) -> None:
    """Configure file + console logging without duplicate output."""
    log_dir = pavo_home / "logs"
    log_dir.mkdir(exist_ok=True)

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    # File handler — full format
    fh = logging.FileHandler(log_dir / "pavo.log", encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    root.addHandler(fh)

    # Console handler — concise format
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    root.addHandler(ch)


logger = logging.getLogger(__name__)


# ── Cache-control middleware ──────────────────────────────────────────────────

class CacheControlMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        if request.url.path.startswith("/static/"):
            ext = request.url.path.rsplit(".", 1)[-1].lower()
            if ext in ("mp4", "webm", "mov"):
                response.headers["Cache-Control"] = "public, max-age=86400"
            else:
                response.headers["Cache-Control"] = "public, max-age=3600"
        return response


# ── FastAPI app ───────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    # Mount local storage static files
    from app.services.storage import get_storage
    get_storage().mount_static(app)
    # Start async task queue worker
    from app.services.task_queue import task_queue
    worker_task = asyncio.create_task(task_queue.start())
    yield
    worker_task.cancel()
    from app.db.database import engine
    await engine.dispose()


app = FastAPI(title=settings.app_name, version="2.3.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(CacheControlMiddleware)
app.include_router(router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok", "app": settings.app_name, "version": "2.3.0"}


# ── Shared boot logic ─────────────────────────────────────────────────────────

def _boot() -> None:
    """Common startup checks run by both CLI commands."""
    setup_logging(PAVO_HOME)

    # Write-permission check
    test_file = PAVO_HOME / ".write_check"
    try:
        test_file.touch()
        test_file.unlink()
    except OSError as e:
        logging.error(f"Cannot write to {PAVO_HOME}: {e}. Check permissions.")
        sys.exit(1)

    logging.info(f"Pavo home: {PAVO_HOME}")


# ── CLI: pavo-start ───────────────────────────────────────────────────────────

def start_app() -> None:
    """Entry point for `pavo-start`: launches API server + optional frontend."""
    _boot()

    frontend_port = int(os.environ.get("PAVO_FRONTEND_PORT", "3000"))
    frontend_proc: subprocess.Popen | None = None

    # Try to start Next.js frontend (optional — skip if npm not found)
    frontend_dir = Path(__file__).resolve().parents[2] / "frontend"
    if frontend_dir.exists():
        try:
            frontend_proc = subprocess.Popen(
                ["npm", "run", "dev", "--", "--port", str(frontend_port)],
                cwd=str(frontend_dir),
            )
            logging.info(f"Frontend started on port {frontend_port}")
        except FileNotFoundError:
            logging.error(
                "npm command not found. Install Node.js 18+ and ensure npm is in PATH, "
                "or use `pavo-mcp-server` to run the MCP server only."
            )
            # Non-fatal: continue running the API server without frontend

    try:
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=settings.static_port,
            log_level=settings.log_level.lower(),
        )
    finally:
        if frontend_proc and frontend_proc.poll() is None:
            frontend_proc.terminate()
            logging.info("Frontend process terminated")
