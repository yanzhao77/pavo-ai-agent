"""Memory store implementation with SQLAlchemy + pgvector compatibility."""

import uuid
import json
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import Column, String, Text, DateTime, JSON, Float, Integer, Index, and_
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func

from app.db.database import Base
from .interfaces import MemoryProvider
from .importance import ImportanceStrategy
from .embedding_client import get_embedding_client

logger = logging.getLogger(__name__)


# ---- ORM Models ----

class UserMemoryORM(Base):
    """User long-term memory ORM model."""
    __tablename__ = "user_memories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(64), nullable=False, index=True)
    memory_type = Column(String(32), nullable=False)  # style/character/scene/preference/story_arc/feedback
    content = Column(JSON, default=dict)
    embedding = Column(JSON, default=list)  # stored as JSON list for SQLite; pgvector for production
    importance = Column(Float, default=0.5)
    source = Column(String(32), default="auto_extracted")  # user_saved/auto_extracted/feedback_derived
    tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    accessed_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_user_memories_user_type", "user_id", "memory_type"),
        Index("idx_user_memories_importance", "user_id", "importance"),
    )


class KnowledgeBaseORM(Base):
    """Knowledge base ORM model."""
    __tablename__ = "knowledge_base"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category = Column(String(64), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, default="")
    tags = Column(JSON, default=list)
    embedding = Column(JSON, default=list)
    source = Column(String(255), default="")
    priority = Column(Integer, default=3)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_knowledge_category_priority", "category", "priority"),
    )


class SessionContextORM(Base):
    """Session context ORM model."""
    __tablename__ = "session_contexts"

    session_id = Column(String(128), primary_key=True)
    user_id = Column(String(64), nullable=False, index=True)
    project_id = Column(String(64), nullable=True)
    messages = Column(JSON, default=list)
    context = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(minutes=30))


# ---- Memory Store Implementation ----

class MemoryStore(MemoryProvider):
    """SQLAlchemy-based memory store with vector search capabilitiess."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.embedding_client = get_embedding_client()

    async def save_memory(self, memory: dict) -> dict:
        mem_id = memory.get("id", uuid.uuid4())
        if isinstance(mem_id, str):
            mem_id = uuid.UUID(mem_id)

        content = memory.get("content", {})
        importance = memory.get("importance", 0.5)

        # Generate embedding if content exists
        embedding = []
        if content:
            try:
                text_for_vector = json.dumps(content, ensure_ascii=False)
                embedding = await self.embedding_client.embed(text_for_vector)
            except Exception as e:
                logger.warning(f"Embedding generation failed: {e}")

        orm = UserMemoryORM(
            id=mem_id,
            user_id=memory.get("user_id", ""),
            memory_type=memory.get("memory_type", "preference"),
            content=content,
            embedding=embedding,
            importance=importance,
            source=memory.get("source", "user_saved"),
            tags=memory.get("tags", []),
        )
        self.session.add(orm)
        await self.session.commit()
        await self.session.refresh(orm)
        return self._orm_to_dict(orm)

    async def search_memory(
        self,
        user_id: str,
        query_text: str,
        memory_types: list[str] | None = None,
        limit: int = 5,
        min_importance: float = 0.0,
    ) -> list[dict]:
        stmt = select(UserMemoryORM).where(UserMemoryORM.user_id == user_id)

        if memory_types:
            stmt = stmt.where(UserMemoryORM.memory_type.in_(memory_types))
        if min_importance > 0:
            stmt = stmt.where(UserMemoryORM.importance >= min_importance)

        stmt = stmt.order_by(UserMemoryORM.importance.desc()).limit(limit)
        result = await self.session.execute(stmt)
        memories = [self._orm_to_dict(row) for row in result.scalars().all()]

        # Update accessed_at for retrieved memories
        for mem in memories:
            await self._update_accessed(mem["id"])

        return memories

    async def list_memories(
        self,
        user_id: str,
        memory_type: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        query = select(UserMemoryORM).where(UserMemoryORM.user_id == user_id)
        count_query = select(func.count(UserMemoryORM.id)).where(UserMemoryORM.user_id == user_id)

        if memory_type:
            query = query.where(UserMemoryORM.memory_type == memory_type)
            count_query = count_query.where(UserMemoryORM.memory_type == memory_type)

        # Total count
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Paginated query
        offset = (page - 1) * page_size
        query = query.order_by(UserMemoryORM.updated_at.desc()).offset(offset).limit(page_size)
        result = await self.session.execute(query)
        memories = [self._orm_to_dict(row) for row in result.scalars().all()]

        return memories, total

    async def delete_memory(self, user_id: str, memory_id: str) -> bool:
        try:
            mem_uuid = uuid.UUID(memory_id) if isinstance(memory_id, str) else memory_id
            stmt = delete(UserMemoryORM).where(
                and_(UserMemoryORM.id == mem_uuid, UserMemoryORM.user_id == user_id)
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except Exception as e:
            logger.error(f"Delete memory failed: {e}")
            return False

    async def cleanup_low_importance(self, max_days: int = 30) -> int:
        """Remove low-importance memories older than max_days."""
        cutoff = datetime.utcnow() - timedelta(days=max_days)
        stmt = delete(UserMemoryORM).where(
            and_(UserMemoryORM.importance < 0.2, UserMemoryORM.updated_at < cutoff)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount

    async def get_session_context(self, session_id: str) -> dict:
        stmt = select(SessionContextORM).where(SessionContextORM.session_id == session_id)
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        if not row:
            return {}
        return {
            "session_id": row.session_id,
            "user_id": row.user_id,
            "project_id": row.project_id,
            "messages": row.messages,
            "context": row.context,
        }

    async def update_session_context(self, session_id: str, context: dict) -> None:
        stmt = select(SessionContextORM).where(SessionContextORM.session_id == session_id)
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()

        if row:
            row.context = context
            row.messages = context.get("messages", row.messages)
        else:
            new_row = SessionContextORM(
                session_id=session_id,
                user_id=context.get("user_id", ""),
                project_id=context.get("project_id"),
                messages=context.get("messages", []),
                context=context,
            )
            self.session.add(new_row)

        await self.session.commit()

    async def touch_session(self, session_id: str) -> None:
        """Refresh session TTL (sliding window)."""
        stmt = select(SessionContextORM).where(SessionContextORM.session_id == session_id)
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        if row:
            row.expires_at = datetime.utcnow() + timedelta(minutes=30)
            await self.session.commit()

    async def extract_and_promote(self, session_id: str) -> int:
        """Extract important info from session and promote to long-term memory."""
        session = await self.get_session_context(session_id)
        if not session:
            return 0

        messages = session.get("messages", [])
        promoted = 0

        # Simple extraction: count mentions of key concepts
        mention_counter = {}
        for msg in messages:
            text = msg.get("content", "")
            if not text:
                continue
            # Basic keyword extraction
            for keyword in ["温馨", "治愈", "悬疑", "动作", "家庭", "校园", "科幻"]:
                if keyword in text:
                    mention_counter[keyword] = mention_counter.get(keyword, 0) + 1

        for keyword, mentions in mention_counter.items():
            if mentions >= 2:  # Mentioned at least twice
                importance = ImportanceStrategy.from_auto_extracted(mentions=mentions)
                if importance >= ImportanceStrategy.auto_promote_threshold():
                    memory = {
                        "user_id": session.get("user_id", ""),
                        "memory_type": "preference",
                        "content": {"keyword": keyword, "mentions": mentions},
                        "importance": importance,
                        "source": "auto_extracted",
                        "tags": [keyword],
                    }
                    await self.save_memory(memory)
                    promoted += 1

        return promoted

    @staticmethod
    def _orm_to_dict(row) -> dict:
        return {
            "id": str(row.id),
            "user_id": row.user_id,
            "memory_type": row.memory_type,
            "content": row.content,
            "importance": row.importance,
            "source": row.source,
            "tags": row.tags,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
            "accessed_at": row.accessed_at.isoformat() if row.accessed_at else None,
        }

    async def _update_accessed(self, memory_id: str) -> None:
        try:
            stmt = select(UserMemoryORM).where(UserMemoryORM.id == uuid.UUID(memory_id))
            result = await self.session.execute(stmt)
            row = result.scalar_one_or_none()
            if row:
                row.accessed_at = datetime.utcnow()
                await self.session.commit()
        except Exception:
            pass
