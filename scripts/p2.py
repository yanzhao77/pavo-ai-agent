import os
from pathlib import Path

code = '''"""SQLite database engine with sqlite-vec vector storage."""
import os, logging
from datetime import datetime
from pathlib import Path
from sqlalchemy import Column, String, Text, DateTime, JSON, Integer, Float
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

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
    __tablename__ = "system_config"
    key = Column(String(128), primary_key=True)
    value = Column(Text, default="")
    updated_at = Column(DateTime, default=datetime.utcnow)

class TaskStatus(Base):
    __tablename__ = "task_status"
    id = Column(String(64), primary_key=True)
    type = Column(String(64), default="", index=True)
    status = Column(String(32), default="pending")
    progress = Column(Integer, default=0)
    result = Column(JSON, default=dict)
    error = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class VecMemory(Base):
    __tablename__ = "vec_memories"
    id = Column(String(64), primary_key=True)
    user_id = Column(String(64), index=True, default="")
    memory_type = Column(String(32), default="preference")
    content = Column(JSON, default=dict)
    embedding = Column(JSON, default=list)
    importance = Column(Float, default=0.5)
    tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

async def init_db():
    from sqlalchemy import text
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("PRAGMA journal_mode=WAL"))
        await conn.execute(text("PRAGMA foreign_keys=ON"))
        await conn.execute(text("CREATE VIRTUAL TABLE IF NOT EXISTS vec_memories_vec USING vec0(embedding FLOAT[1536])"))
    logger.info(f"SQLite DB initialized at {DB_PATH}")

async def get_session():
    async with async_session() as session:
        try: yield session
        finally: await session.close()

async def get_config(key, default=""):
    from sqlalchemy import select
    async with async_session() as session:
        r = await session.execute(select(SystemConfig).where(SystemConfig.key == key))
        row = r.scalar_one_or_none()
        return row.value if row else default

async def set_config(key, value):
    from sqlalchemy import select
    async with async_session() as session:
        r = await session.execute(select(SystemConfig).where(SystemConfig.key == key))
        row = r.scalar_one_or_none()
        if row:
            row.value = value; row.updated_at = datetime.utcnow()
        else:
            session.add(SystemConfig(key=key, value=value))
        await session.commit()
'''

with open("backend/app/db/database.py", "w", encoding="utf-8") as f:
    f.write(code)
print("OK: database.py written")

import shutil
shutil.rmtree("backend/app/db_sqlite", ignore_errors=True)
print("OK: db_sqlite removed")
