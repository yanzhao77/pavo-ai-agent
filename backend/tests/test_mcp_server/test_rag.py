"""RAG retriever unit tests."""
import os
import pytest
import pytest_asyncio
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("AGNES_API_KEY", "test-key")

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.db.database import Base
from mcp_server.rag.retriever import RAGRetriever, SimpleReranker
from mcp_server.rag.builder import RAGBuilder
from mcp_server.rag.interfaces import RAGQuery
from mcp_server.memory.embedding_client import EmbeddingClient


@pytest_asyncio.fixture
async def test_db():
    """Fresh in-memory DB per test, disposed cleanly to avoid aiosqlite hang."""
    import mcp_server.memory.store  # noqa: F401 — register ORM models
    import mcp_server.rag.builder    # noqa: F401 — register RAG ORM models

    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    TestSession = async_sessionmaker(test_engine, expire_on_commit=False)

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSession() as session:
        yield session

    await test_engine.dispose()


@pytest.fixture(autouse=True)
def mock_embed():
    """Prevent real HTTP calls from EmbeddingClient."""
    async def _fake_call(self, texts):
        return [[0.1] * 1536 for _ in texts]

    with patch.object(EmbeddingClient, "_call_embedding_api", _fake_call):
        yield


@pytest.mark.asyncio
async def test_rag_retriever_empty(test_db):
    retriever = RAGRetriever(test_db)
    result = await retriever.search(RAGQuery(query_text="test", top_k=5))
    assert result.total == 0
    assert result.entries == []


@pytest.mark.asyncio
async def test_rag_builder(test_db):
    builder = RAGBuilder(test_db)
    stats = await builder.get_statistics()
    assert "total_entries" in stats
    assert "by_category" in stats


@pytest.mark.asyncio
async def test_reranker():
    candidates = [
        {"_similarity": 0.6, "category": "shot_language", "priority": 5},
        {"_similarity": 0.8, "category": "film_grammar", "priority": 3},
        {"_similarity": 0.7, "category": "shot_language", "priority": 1},
    ]
    reranked = SimpleReranker.rerank(candidates, ["shot_language"], top_k=2)
    assert len(reranked) <= 2
    assert reranked[0]["category"] in ("film_grammar", "shot_language")


@pytest.mark.asyncio
async def test_entity_detection():
    assert RAGRetriever._detect_category("景别分类大全") == "shot_language"
    assert RAGRetriever._detect_category("经典案例：肖申克的救赎") == "classic_case"
    assert RAGRetriever._detect_category("BGM配乐建议") == "bgm_sound"
