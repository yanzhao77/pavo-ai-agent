"""Memory provider abstract interface."""

from abc import ABC, abstractmethod
from typing import Optional


class MemoryProvider(ABC):
    """Memory storage abstract interface."""

    @abstractmethod
    async def save_memory(self, memory: dict) -> dict:
        ...

    @abstractmethod
    async def search_memory(
        self,
        user_id: str,
        query_text: str,
        memory_types: list[str] | None = None,
        limit: int = 5,
        min_importance: float = 0.0,
    ) -> list[dict]:
        ...

    @abstractmethod
    async def list_memories(
        self,
        user_id: str,
        memory_type: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        ...

    @abstractmethod
    async def delete_memory(self, user_id: str, memory_id: str) -> bool:
        ...

    @abstractmethod
    async def get_session_context(self, session_id: str) -> dict:
        ...

    @abstractmethod
    async def update_session_context(self, session_id: str, context: dict) -> None:
        ...

    @abstractmethod
    async def touch_session(self, session_id: str) -> None:
        """Refresh session TTL (sliding window)."""
        ...
