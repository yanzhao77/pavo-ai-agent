"""RAG retriever unit tests."""
import pytest, pytest_asyncio, os
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("AGNES_API_KEY", "test-key")
from app.db.database import Base, engine, async_session
from mcp_server.rag.retriever import RAGRetriever, SimpleReranker
from mcp_server.rag.builder import RAGBuilder
from mcp_server.rag.interfaces import RAGQuery


@pytest_asyncio.fixture
async def test_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_rag_retriever_empty(db_session):
    retriever = RAGRetriever(db_session)
    result = await retriever.search(RAGQuery(query_text="test", top_k=5))
    assert result.total == 0
    assert result.entries == []


@pytest.mark.asyncio
async def test_rag_builder(db_session):
    builder = RAGBuilder(db_session)
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
    assert reranked[0]["category"] == "shot_language"


@pytest.mark.asyncio
async def test_entity_detection():
    from mcp_server.rag.retriever import RAGRetriever as R
    assert R._detect_category("景别分类大全") == "shot_language"
    assert R._detect_category("经典案例：肖申克的救赎") == "classic_case"
    assert R._detect_category("BGM配乐建议") == "bgm_sound"
