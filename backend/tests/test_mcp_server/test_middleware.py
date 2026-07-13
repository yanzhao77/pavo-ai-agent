"""Memory Middleware unit tests.

MemoryMiddleware.pre_process internally calls MemoryStore.search_memory which
invokes EmbeddingClient.  We patch _call_embedding_api to prevent real HTTP
calls, and initialise a fresh in-memory SQLite DB so the ORM queries succeed.
"""
import os
import pytest
import pytest_asyncio
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("AGNES_API_KEY", "test-key")

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.db.database import Base
from mcp_server.middleware.memory_middleware import MemoryMiddleware
from mcp_server.memory.embedding_client import EmbeddingClient


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Create tables in a fresh in-memory DB and patch async_session."""
    import mcp_server.memory.store  # noqa: F401 — register ORM models

    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    TestSession = async_sessionmaker(test_engine, expire_on_commit=False)

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    import app.db.database as db_module
    original_session = db_module.async_session
    db_module.async_session = TestSession

    yield

    db_module.async_session = original_session
    await test_engine.dispose()


@pytest.fixture(autouse=True)
def mock_embed():
    """Patch EmbeddingClient._call_embedding_api to return mock vectors."""
    async def _fake_call(self, texts):
        return [[0.1] * 1536 for _ in texts]

    with patch.object(EmbeddingClient, "_call_embedding_api", _fake_call):
        yield


@pytest.mark.asyncio
async def test_middleware_empty_args():
    mw = MemoryMiddleware()
    result = await mw.pre_process("test_tool", {})
    assert "context" not in result


@pytest.mark.asyncio
async def test_middleware_with_user():
    mw = MemoryMiddleware()
    result = await mw.pre_process("test_tool", {"user_id": "alice"})
    assert result.get("context", {}).get("user_id") == "alice"


@pytest.mark.asyncio
async def test_middleware_degradation():
    mw = MemoryMiddleware()
    result = await mw.pre_process("test_tool", {"user_id": None})
    assert result is not None


@pytest.mark.asyncio
async def test_middleware_metrics():
    mw = MemoryMiddleware()
    await mw.pre_process("tool_a", {"user_id": "bob"})
    await mw.pre_process("tool_b", {"user_id": "bob"})
    metrics = mw.get_metrics()
    assert metrics["pre_process_count"] == 2
    assert "fallback_count" in metrics
