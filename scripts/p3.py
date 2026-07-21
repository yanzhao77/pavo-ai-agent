import os, shutil
# Create app/vectorstore
os.makedirs("backend/app/vectorstore", exist_ok=True)

# Copy existing VectorStore base from mcp_server/vectorstore/
src = "backend/mcp_server/vectorstore/base.py"
dst = "backend/app/vectorstore/__init__.py"
if os.path.exists(src):
    content = open(src, "r", encoding="utf-8").read()
    with open(dst, "w", encoding="utf-8") as f:
        f.write(content)
    print("Phase 3: VectorStore moved to app/vectorstore/")
else:
    # Create new VectorStore abstraction
    content = '''"""VectorStore abstraction for sqlite-vec."""
import json, logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List, Tuple

logger = logging.getLogger(__name__)


class VectorStore(ABC):
    """Abstract vector store interface."""

    @abstractmethod
    async def upsert(self, id: str, vector: list[float], metadata: dict) -> None:
        ...

    @abstractmethod
    async def search(self, vector: list[float], top_k: int = 5, filters: dict = None) -> list[tuple[str, float, dict]]:
        ...

    @abstractmethod
    async def delete(self, id: str) -> bool:
        ...


class SqliteVecStore(VectorStore):
    """sqlite-vec implementation using vec0 virtual table."""

    def __init__(self):
        from app.db.database import async_session
        self.async_session = async_session

    async def upsert(self, id: str, vector: list[float], metadata: dict) -> None:
        vec_json = json.dumps(vector)
        meta_json = json.dumps(metadata)
        async with self.async_session() as session:
            from sqlalchemy import text
            await session.execute(text("INSERT INTO vec_memories (id,content,embedding) VALUES (:id,:content,:embedding) ON CONFLICT(id) DO UPDATE SET embedding=excluded.embedding,content=excluded.content"), {"id": id, "content": meta_json, "embedding": vec_json})
            await session.execute(text("INSERT INTO vec_memories_vec (id,embedding) VALUES (:id,:embedding) ON CONFLICT(id) DO UPDATE SET embedding=excluded.embedding"), {"id": id, "embedding": vec_json})
            await session.commit()

    async def search(self, vector: list[float], top_k: int = 5, filters: dict = None) -> list[tuple[str, float, dict]]:
        vec_json = json.dumps(vector)
        async with self.async_session() as session:
            from sqlalchemy import text
            try:
                r = await session.execute(text("SELECT v.id, v.distance, m.content FROM vec_memories_vec v LEFT JOIN vec_memories m ON v.id = m.id WHERE v.embedding MATCH :vec ORDER BY v.distance LIMIT :top_k"), {"vec": vec_json, "top_k": top_k})
                rows = r.fetchall()
                return [(str(row[0]), float(row[1]) if row[1] else 0.5, json.loads(row[2]) if row[2] else {}) for row in rows]
            except Exception as e:
                logger.warning(f"Vector search failed: {e}")
                return []

    async def delete(self, id: str) -> bool:
        async with self.async_session() as session:
            from sqlalchemy import text
            r = await session.execute(text("DELETE FROM vec_memories WHERE id = :id"), {"id": id})
            await session.execute(text("DELETE FROM vec_memories_vec WHERE id = :id"), {"id": id})
            await session.commit()
            return r.rowcount > 0


class VectorStoreFactory:
    @staticmethod
    def create(backend: str = "sqlite") -> VectorStore:
        if backend == "sqlite":
            return SqliteVecStore()
        raise ValueError(f"Unknown backend: {backend}")
'''
    with open(dst, "w", encoding="utf-8") as f:
        f.write(content)
    print("Phase 3: VectorStore created at app/vectorstore/")

# Clean up old mcp_server/vectorstore if exists
if os.path.exists("backend/mcp_server/vectorstore"):
    shutil.rmtree("backend/mcp_server/vectorstore", ignore_errors=True)
    print("Phase 3: old mcp_server/vectorstore removed")
