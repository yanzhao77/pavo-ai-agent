"""MCP Memory Store unit tests.

Key design decisions:
  1. Each test gets a *fresh* in-memory SQLite engine (not the global one) so
     tests are fully isolated and the engine can be disposed cleanly.
  2. `_call_embedding_api` is patched via an autouse fixture to return
     deterministic mock vectors, preventing real HTTP calls to the embedding
     API (which would time out with a test API key).
  3. The engine is explicitly disposed after each test to prevent the known
     aiosqlite background-thread hang on process exit.
"""
import os
import pytest
import pytest_asyncio
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("AGNES_API_KEY", "test-key")

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.db.database import Base
from mcp_server.memory.store import MemoryStore, UserMemoryORM, SessionContextORM, KnowledgeBaseORM
from mcp_server.memory.importance import ImportanceStrategy
from mcp_server.memory.embedding_client import EmbeddingClient


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def test_db():
    """Yield an async session backed by a fresh in-memory SQLite engine.

    A new engine is created per test so tests are fully isolated.
    The engine is disposed after the test to prevent aiosqlite thread hangs.
    """
    # Import store module to ensure all ORM models are registered with Base
    import mcp_server.memory.store  # noqa: F401

    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    TestSession = async_sessionmaker(test_engine, expire_on_commit=False)

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSession() as session:
        yield session

    # Explicit dispose prevents aiosqlite worker thread from hanging on exit
    await test_engine.dispose()


@pytest.fixture(autouse=True)
def mock_embed():
    """Auto-use fixture: patch EmbeddingClient._call_embedding_api to return
    deterministic 1536-dim mock vectors without any HTTP call.
    Applied to every test in this module automatically.
    """
    async def _fake_call(self, texts):
        return [[0.1] * 1536 for _ in texts]

    with patch.object(EmbeddingClient, "_call_embedding_api", _fake_call):
        yield


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_save_and_search_memory(test_db):
    store = MemoryStore(test_db)
    memory = {
        "user_id": "test_user",
        "memory_type": "style",
        "content": {"preferred_genre": "悬疑", "tone": "紧张"},
        "importance": 0.8,
        "source": "user_saved",
        "tags": ["风格", "偏好"],
    }
    saved = await store.save_memory(memory)
    assert saved["user_id"] == "test_user"
    assert saved["memory_type"] == "style"
    assert saved["importance"] == 0.8

    results = await store.search_memory("test_user", "悬疑", limit=5)
    assert len(results) >= 1


@pytest.mark.asyncio
async def test_list_memories_pagination(test_db):
    store = MemoryStore(test_db)
    for i in range(5):
        await store.save_memory({
            "user_id": "user_a", "memory_type": "preference",
            "content": {"test": f"item_{i}"}, "importance": 0.5,
            "source": "auto_extracted", "tags": [],
        })
    page1, total = await store.list_memories("user_a", page=1, page_size=3)
    assert len(page1) <= 3
    assert total == 5


@pytest.mark.asyncio
async def test_delete_memory(test_db):
    store = MemoryStore(test_db)
    saved = await store.save_memory({
        "user_id": "user_b", "memory_type": "character",
        "content": {"name": "主角"}, "importance": 0.9,
        "source": "user_saved", "tags": [],
    })
    assert saved["id"] is not None
    deleted = await store.delete_memory("user_b", saved["id"])
    assert deleted is True
    deleted2 = await store.delete_memory("user_b", saved["id"])
    assert deleted2 is False


@pytest.mark.asyncio
async def test_importance_filter(test_db):
    store = MemoryStore(test_db)
    await store.save_memory({
        "user_id": "user_c", "memory_type": "style",
        "content": {"a": 1}, "importance": 0.9,
        "source": "user_saved", "tags": [],
    })
    await store.save_memory({
        "user_id": "user_c", "memory_type": "style",
        "content": {"b": 2}, "importance": 0.1,
        "source": "auto_extracted", "tags": [],
    })
    results = await store.search_memory("user_c", "test", min_importance=0.5)
    assert len(results) == 1
    assert results[0]["importance"] >= 0.5


@pytest.mark.asyncio
async def test_importance_strategy():
    assert ImportanceStrategy.from_user_saved() == 0.9
    assert ImportanceStrategy.from_feedback_derived("up") == 0.7
    assert ImportanceStrategy.from_feedback_derived("down") == 0.2
    auto = ImportanceStrategy.from_auto_extracted(mentions=3, recency_days=0)
    assert 0.5 <= auto <= 0.8
    assert ImportanceStrategy.auto_promote_threshold() == 0.5


@pytest.mark.asyncio
async def test_embedding_cache():
    """EmbeddingClient cache returns same vector for same input (mock mode)."""
    saved = {k: os.environ.pop(k, None)
             for k in ("EMBEDDING_API_KEY", "AGNES_API_KEY", "OPENAI_API_KEY")}
    try:
        client = EmbeddingClient(api_key="")
        assert not client.api_key, "Expected empty api_key for mock mode"
        v1 = await client.embed("hello world")
        v2 = await client.embed("hello world")
        assert v1 == v2, "Cache must return identical vectors for same input"
        assert client.get_stats()["hits"] >= 1, "Cache hit counter must be >= 1"
    finally:
        for k, v in saved.items():
            if v is not None:
                os.environ[k] = v


@pytest.mark.asyncio
async def test_session_context(test_db):
    store = MemoryStore(test_db)
    await store.update_session_context("sess_001", {"user_id": "alice", "messages": []})
    ctx = await store.get_session_context("sess_001")
    assert ctx["user_id"] == "alice"
    await store.touch_session("sess_001")
    ctx2 = await store.get_session_context("sess_001")
    assert ctx2["user_id"] == "alice"


@pytest.mark.asyncio
async def test_cleanup_low_importance(test_db):
    store = MemoryStore(test_db)
    await store.save_memory({
        "user_id": "user_d", "memory_type": "preference",
        "content": {"x": 1}, "importance": 0.1,
        "source": "auto_extracted", "tags": [],
    })
    cleaned = await store.cleanup_low_importance(max_days=0)
    assert cleaned >= 1
