"""RAG builder — knowledge base construction pipeline."""
import logging, os, glob
from sqlalchemy.ext.asyncio import AsyncSession
from .interfaces import RAGProvider
from .retriever import RAGRetriever

logger = logging.getLogger(__name__)

class RAGBuilder:
    """Knowledge base construction pipeline — imports markdown to vector store."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.retriever = RAGRetriever(session)

    async def build_from_directory(self, dir_path: str) -> dict:
        """Import all markdown files from a directory."""
        if not os.path.isdir(dir_path):
            return {"status": "error", "message": f"Directory not found: {dir_path}"}

        md_files = glob.glob(os.path.join(dir_path, "**/*.md"), recursive=True)
        total_imported = 0
        results = []

        for file_path in md_files:
            try:
                count = await self.retriever.build_from_markdown(file_path)
                total_imported += count
                results.append({"file": os.path.basename(file_path), "imported": count})
            except Exception as e:
                logger.error(f"Failed to import {file_path}: {e}")
                results.append({"file": os.path.basename(file_path), "error": str(e)})

        return {"status": "completed", "total_imported": total_imported, "files": results}

    async def get_statistics(self) -> dict:
        """Get knowledge base statistics."""
        from sqlalchemy import select, func
        from ..memory.store import KnowledgeBaseORM

        stmt = select(
            KnowledgeBaseORM.category,
            func.count(KnowledgeBaseORM.id)
        ).group_by(KnowledgeBaseORM.category)
        r = await self.session.execute(stmt)
        categories = {row[0]: row[1] for row in r}

        total = sum(categories.values())
        return {"total_entries": total, "by_category": categories}
