"""SQLite database module — zero external dependency database layer."""

import os, asyncio, logging, json
from datetime import datetime
from pathlib import Path

import aiosqlite
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String, Text, DateTime, JSON, Integer, Float, select, text

logger = logging.getLogger(__name__)

PAVO_HOME = Path.home() / ".pavo"
PAVO_HOME.mkdir(parents=True, exist_ok=True)
DB_PATH = PAVO_HOME / "pavo.db"
DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

engine = create_async_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class SystemConfig(Base):
    """System configuration key-value store."""
    __tablename__ = "system_config"
    key = Column(String(128), primary_key=True)
    value = Column(Text, default="")
    updated_at = Column(DateTime, default=datetime.utcnow)


class TaskStatus(Base):
    """Async task status tracking."""
    __tablename__ = "task_status"
    id = Column(String(64), primary_key=True)
    type = Column(String(64), default="", index=True)
    status = Column(String(32), default="pending")  # pending/running/done/failed
    progress = Column(Integer, default=0)
    result = Column(JSON, default=dict)
    error = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class VecMemory(Base):
    """Vector memory storage for user memories."""
    __tablename__ = "vec_memories"
    id = Column(String(64), primary_key=True)
    user_id = Column(String(64), index=True)
    memory_type = Column(String(32), default="preference")
    content = Column(JSON, default=dict)
    importance = Column(Float, default=0.5)
    tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


async def init_db():
    """Initialize database — create tables and enable WAL mode."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("PRAGMA journal_mode=WAL"))
        await conn.execute(text("PRAGMA foreign_keys=ON"))
    logger.info(f"SQLite database initialized at {DB_PATH}")


async def get_session() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_config(key: str, default: str = "") -> str:
    async with async_session() as session:
        stmt = select(SystemConfig).where(SystemConfig.key == key)
        result = await session.execute(stmt)
        row = result.scalar_one_or_none()
        return row.value if row else default


async def set_config(key: str, value: str) -> None:
    async with async_session() as session:
        stmt = select(SystemConfig).where(SystemConfig.key == key)
        result = await session.execute(stmt)
        row = result.scalar_one_or_none()
        if row:
            row.value = value
            row.updated_at = datetime.utcnow()
        else:
            session.add(SystemConfig(key=key, value=value))
        await session.commit()
