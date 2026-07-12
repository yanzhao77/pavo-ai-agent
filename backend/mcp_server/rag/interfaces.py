"""RAG provider abstract interface."""

from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Optional


class RAGQuery(BaseModel):
    """RAG retrieval query."""
    query_text: str
    categories: list[str] | None = None
    top_k: int = 5


class RAGResult(BaseModel):
    """RAG retrieval result."""
    entries: list[dict] = []
    scores: list[float] = []
    total: int = 0
    query_time_ms: float = 0.0


class RAGProvider(ABC):
    """RAG knowledge base abstract interface."""

    @abstractmethod
    async def search(self, query: RAGQuery) -> RAGResult:
        ...

    @abstractmethod
    async def build_from_markdown(self, file_path: str) -> int:
        """Import knowledge from markdown file."""
        ...

    @abstractmethod
    async def rebuild_index(self) -> None:
        ...
