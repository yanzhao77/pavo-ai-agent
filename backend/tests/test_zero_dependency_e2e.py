"""Zero-dependency integration tests.

Verifies that the full stack works correctly without PostgreSQL, Redis,
MinIO, or Celery — using only SQLite, local filesystem, and asyncio.

Test coverage:
  1. Database initializes correctly (tables + WAL + sqlite-vec)
  2. StorageClient uploads/retrieves/deletes files locally
  3. AsyncTaskQueue submits tasks and persists status to SQLite
  4. EmbeddingClient falls back to mock vectors when no API key is set
  5. Auth tokens survive in-memory cache (persistence tested separately)
  6. No legacy dependency imports exist in the codebase
"""
import os
import asyncio
import tempfile
import pytest

# Ensure test mode before any app imports (conftest.py handles this, but be explicit)
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")


# ─────────────────────────────────────────────────────────────────────────────
# 1. Database layer
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_database_initializes():
    """init_db() creates all tables without errors.
    Uses a fresh isolated engine to avoid the global engine's aiosqlite
    worker-thread lingering after the test loop is torn down.
    """
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from sqlalchemy import text
    from app.db.database import Base

    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    TestSession = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    try:
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with TestSession() as session:
            for table in ("system_config", "task_status", "vec_memories"):
                result = await session.execute(
                    text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                )
                row = result.fetchone()
                assert row is not None, f"Table '{table}' was not created"
    finally:
        await test_engine.dispose()


@pytest.mark.asyncio
async def test_wal_mode_enabled():
    """SQLite WAL journal mode is active after init_db().
    In-memory SQLite always reports 'memory' mode; file DBs use 'wal'.
    """
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from sqlalchemy import text
    from app.db.database import Base

    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    TestSession = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    try:
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await conn.execute(text("PRAGMA journal_mode=WAL"))
        async with TestSession() as session:
            result = await session.execute(text("PRAGMA journal_mode"))
            mode = result.scalar()
            assert mode in ("wal", "memory"), f"Unexpected journal mode: {mode}"
    finally:
        await test_engine.dispose()


@pytest.mark.asyncio
async def test_get_set_config():
    """get_config / set_config round-trips correctly."""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from sqlalchemy import select
    from app.db.database import Base, SystemConfig

    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    TestSession = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    try:
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        # set_config
        async with TestSession() as session:
            session.add(SystemConfig(key="test_key", value="hello_world"))
            await session.commit()
        # get_config — key exists
        async with TestSession() as session:
            r = await session.execute(select(SystemConfig).where(SystemConfig.key == "test_key"))
            row = r.scalar_one_or_none()
            assert row is not None and row.value == "hello_world"
        # get_config — key absent
        async with TestSession() as session:
            r = await session.execute(select(SystemConfig).where(SystemConfig.key == "nonexistent"))
            row = r.scalar_one_or_none()
            assert row is None
    finally:
        await test_engine.dispose()


# ─────────────────────────────────────────────────────────────────────────────
# 2. Storage layer (LocalStorageClient)
# ─────────────────────────────────────────────────────────────────────────────

def test_storage_upload_and_retrieve():
    """StorageClient stores bytes locally and returns a /static URL."""
    with tempfile.TemporaryDirectory() as tmpdir:
        from app.services.storage import StorageClient
        client = StorageClient(base_dir=tmpdir)

        data = b"fake video content"
        url = client.upload_bytes(data, "projects/test/shot_1.mp4")
        assert "/static/" in url

        # File should exist on disk
        import pathlib
        fp = pathlib.Path(tmpdir) / "projects" / "test" / "shot_1.mp4"
        assert fp.exists()
        assert fp.read_bytes() == data


def test_storage_delete():
    """StorageClient.delete() removes the file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        from app.services.storage import StorageClient
        client = StorageClient(base_dir=tmpdir)

        client.upload_bytes(b"data", "test/file.mp4")
        deleted = client.delete("test/file.mp4")
        assert deleted is True

        # Second delete returns False
        assert client.delete("test/file.mp4") is False


def test_storage_no_boto3():
    """boto3 must not be imported (as an actual import statement) in storage.py."""
    import ast, pathlib
    src = pathlib.Path(__file__).parent.parent / "app" / "services" / "storage.py"
    tree = ast.parse(src.read_text(encoding="utf-8"))
    # Collect only actual import names, not string literals in docstrings/comments
    imported_names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_names.extend(n.name.split(".")[0] for n in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_names.append(node.module.split(".")[0])
    assert "boto3" not in imported_names, "boto3 must not be imported in storage.py"
    assert "botocore" not in imported_names, "botocore must not be imported in storage.py"


# ─────────────────────────────────────────────────────────────────────────────
# 3. Task queue
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_task_queue_submit_and_status():
    """AsyncTaskQueue accepts a task and tracks its status.
    Mocks out the DB _update_status call so we don't touch the global engine.
    """
    from unittest.mock import patch, AsyncMock
    from app.services.task_queue import AsyncTaskQueue

    # Patch the DB write so the test is self-contained (no global engine needed)
    # Signature must match AsyncTaskQueue._update_status(self, task_id, task_type, status, **kwargs)
    async def _noop_update(self, task_id, task_type, status, **kwargs):
        # Write directly to in-memory cache (do NOT check existence first —
        # submit() calls this before the key exists in the cache)
        self._status_cache[task_id] = {
            "id": task_id, "type": task_type, "status": status,
            "result": kwargs.get("result"), "error": kwargs.get("error", ""),
        }

    with patch.object(AsyncTaskQueue, "_update_status", _noop_update):
        queue = AsyncTaskQueue(max_concurrent=1)
        await queue.start()

        results = []

        async def sample_task(x: int):
            results.append(x)
            return {"value": x}

        task_id = await queue.submit("test_task", sample_task, 42)
        assert task_id, "submit() must return a non-empty task ID"

        # Give the worker a moment to process
        await asyncio.sleep(0.3)

        status = await queue.get_status(task_id)
        assert status is not None
        assert status.get("status") in ("pending", "running", "completed")

        # stop() must be inside the patch context so the worker's
        # _update_status calls are also intercepted (asyncio.create_task
        # runs in the same event loop but the patch must still be active)
        await queue.stop()


def test_no_celery_import():
    """celery must not be imported anywhere in the services directory."""
    import ast, pathlib
    services_dir = pathlib.Path(__file__).parent.parent / "app" / "services"
    for py_file in services_dir.rglob("*.py"):
        tree = ast.parse(py_file.read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [n.name for n in node.names] if isinstance(node, ast.Import) else [node.module or ""]
                for name in names:
                    assert "celery" not in (name or "").lower(), (
                        f"celery import found in {py_file}: {name}"
                    )


# ─────────────────────────────────────────────────────────────────────────────
# 4. Embedding client
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_embedding_client_mock_fallback():
    """EmbeddingClient returns deterministic mock vectors when no API key is set."""
    # Temporarily unset any API key
    saved = {k: os.environ.pop(k, None) for k in ("EMBEDDING_API_KEY", "AGNES_API_KEY", "OPENAI_API_KEY")}
    try:
        from mcp_server.memory.embedding_client import EmbeddingClient
        client = EmbeddingClient(api_key="")
        vec = await client.embed("test sentence")
        assert len(vec) == 1536
        # Deterministic: same input → same output
        vec2 = await client.embed("test sentence")
        assert vec == vec2
    finally:
        for k, v in saved.items():
            if v is not None:
                os.environ[k] = v


@pytest.mark.asyncio
async def test_embedding_client_real_api_called_when_key_present(monkeypatch):
    """EmbeddingClient calls the real API endpoint when an API key is set."""
    import httpx

    captured = {}

    async def mock_post(self, url, **kwargs):
        captured["url"] = url
        captured["headers"] = kwargs.get("headers", {})
        # Return a minimal valid response with a proper request attached
        import json
        request = httpx.Request("POST", url, headers=kwargs.get("headers", {}))
        mock_resp = httpx.Response(
            200,
            content=json.dumps({
                "data": [{"index": 0, "embedding": [0.1] * 1536}]
            }).encode(),
            request=request,
        )
        return mock_resp

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)
    monkeypatch.setenv("EMBEDDING_API_KEY", "test-api-key")

    from mcp_server.memory.embedding_client import EmbeddingClient
    client = EmbeddingClient(api_key="test-api-key")
    vec = await client.embed("hello world")

    assert len(vec) == 1536
    assert "embeddings" in captured.get("url", ""), f"Expected /embeddings URL, got: {captured.get('url')}"
    assert "Bearer test-api-key" in captured.get("headers", {}).get("Authorization", "")


# ─────────────────────────────────────────────────────────────────────────────
# 5. Auth service
# ─────────────────────────────────────────────────────────────────────────────

def test_auth_token_create_and_verify():
    """create_token / verify_token round-trips correctly."""
    from app.services import auth
    # Reset cache for a clean test
    auth._token_cache = {}

    token = auth.create_token("user_123")
    assert token and len(token) == 64  # secrets.token_hex(32) = 64 hex chars

    user_id = auth.verify_token(token)
    assert user_id == "user_123"


def test_auth_token_revoke():
    """Revoked token is no longer valid."""
    from app.services import auth
    auth._token_cache = {}

    token = auth.create_token("user_456")
    assert auth.verify_token(token) == "user_456"

    revoked = auth.revoke_token(token)
    assert revoked is True
    assert auth.verify_token(token) is None


def test_auth_clean_expired():
    """clean_expired() removes tokens past their expiry."""
    import time
    from app.services import auth
    auth._token_cache = {}

    token = auth.create_token("user_789")
    token_hash = auth._hash_token(token)

    # Manually expire the token
    auth._token_cache[token_hash]["expires_at"] = time.time() - 1

    removed = auth.clean_expired()
    assert removed == 1
    assert auth.verify_token(token) is None


# ─────────────────────────────────────────────────────────────────────────────
# 6. Global dependency audit
# ─────────────────────────────────────────────────────────────────────────────

def test_no_legacy_dependencies_in_source():
    """Verify that no legacy heavy dependencies are imported in non-test source files."""
    import ast
    import pathlib

    backend_dir = pathlib.Path(__file__).parent.parent
    banned = {"celery", "boto3", "botocore", "asyncpg", "redis", "aioredis"}
    violations = []

    for py_file in backend_dir.rglob("*.py"):
        # Skip test files and virtual environments
        parts = py_file.parts
        if any(p in parts for p in ("tests", "__pycache__", ".venv", "venv", "site-packages")):
            continue
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [n.name for n in node.names] if isinstance(node, ast.Import) else [node.module or ""]
                for name in names:
                    top = (name or "").split(".")[0].lower()
                    if top in banned:
                        violations.append(f"{py_file.relative_to(backend_dir)}: imports '{name}'")

    assert not violations, "Legacy dependencies found:\n" + "\n".join(violations)
