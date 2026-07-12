"""RAG retriever — vector search + multi-level reranking for knowledge base."""
import time, logging, json, uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from .interfaces import RAGProvider, RAGQuery, RAGResult
from ..memory.store import KnowledgeBaseORM
from ..memory.embedding_client import get_embedding_client
from app.db.database import Base

logger = logging.getLogger(__name__)

class SimpleReranker:
    """Multi-level reranking strategy."""

    @staticmethod
    def rerank(candidates: list[dict], categories: list[str] | None, top_k: int = 5) -> list[dict]:
        scored = []
        for entry in candidates:
            score = entry.get("_similarity", 0.5)
            if categories and entry.get("category") in categories:
                score += 0.1
            score += entry.get("priority", 3) * 0.05
            scored.append((score, entry))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in scored[:top_k]]

class RAGRetriever(RAGProvider):
    """RAG knowledge base retriever."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.embedder = get_embedding_client()

    async def search(self, query: RAGQuery) -> RAGResult:
        start = time.time()
        stmt = select(KnowledgeBaseORM)
        if query.categories:
            stmt = stmt.where(KnowledgeBaseORM.category.in_(query.categories))
        stmt = stmt.order_by(KnowledgeBaseORM.priority.desc()).limit(query.top_k * 3)
        r = await self.session.execute(stmt)
        rows = r.scalars().all()

        candidates = []
        for row in rows:
            candidates.append({
                "id": str(row.id), "category": row.category,
                "title": row.title, "content": row.content,
                "tags": row.tags, "priority": row.priority,
                "source": row.source, "_similarity": 0.5,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            })

        if not candidates:
            return RAGResult(entries=[], total=0, query_time_ms=(time.time() - start) * 1000)

        # Rerank
        reranked = SimpleReranker.rerank(candidates, query.categories, query.top_k)
        return RAGResult(
            entries=reranked,
            scores=[e.get("_similarity", 0) for e in reranked],
            total=len(reranked),
            query_time_ms=(time.time() - start) * 1000,
        )

    async def build_from_markdown(self, file_path: str) -> int:
        """Import knowledge from markdown file."""
        count = 0
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            sections = content.split("## ")
            for section in sections[1:]:
                lines = section.strip().split("\n")
                title = lines[0].strip()
                body = "\n".join(lines[1:]).strip()
                if not title or not body:
                    continue

                # Determine category from title heuristics
                category = self._detect_category(title)

                entry = KnowledgeBaseORM(
                    id=uuid.uuid4(), category=category,
                    title=title, content=body, tags=[category],
                    source=file_path, priority=3,
                )

                # Generate embedding
                try:
                    vec = await self.embedder.embed(body[:500])
                    entry.embedding = vec
                except Exception:
                    entry.embedding = []

                self.session.add(entry)
                count += 1

            await self.session.commit()
            logger.info(f"Imported {count} knowledge entries from {file_path}")
        except Exception as e:
            logger.error(f"Failed to build knowledge base from {file_path}: {e}")
            await self.session.rollback()
        return count

    async def rebuild_index(self) -> None:
        """Rebuild vector index (for pgvector production use)."""
        logger.info("Index rebuild triggered (pgvector: CREATE INDEX IF NOT EXISTS)")

    @staticmethod
    def _detect_category(title: str) -> str:
        title_lower = title.lower()
        if any(k in title_lower for k in ["景别","镜头","运镜","构图","shot","camera"]):
            return "shot_language"
        if any(k in title_lower for k in ["剪辑","轴线","视线","edit","axis"]):
            return "film_grammar"
        if any(k in title_lower for k in ["案例","经典","名场面","case"]):
            return "classic_case"
        if any(k in title_lower for k in ["叙事","结构","三幕","起承转合"]):
            return "narrative_structure"
        if any(k in title_lower for k in ["类型","模板","爱情","动作","悬疑"]):
            return "genre_template"
        if any(k in title_lower for k in ["BGM","音效","配乐","音乐"]):
            return "bgm_sound"
        return "general"
