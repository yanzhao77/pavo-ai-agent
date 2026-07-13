"""SQLite database engine with sqlite-vec vector storage."""
import os, logging
from datetime import datetime
from pathlib import Path
from sqlalchemy import Column, String, Text, DateTime, JSON, Integer, Float, event
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

logger = logging.getLogger(__name__)

_env_home = os.environ.get("PAVO_HOME", "")
PAVO_HOME = Path(_env_home) if _env_home else Path.home() / ".pavo"
PAVO_HOME.mkdir(parents=True, exist_ok=True)
DB_PATH = PAVO_HOME / "pavo.db"

# Allow DATABASE_URL env override (used in tests and CI)
DATABASE_URL = os.environ.get("DATABASE_URL") or f"sqlite+aiosqlite:///{DB_PATH}"

# aiosqlite in-memory databases require same-connection semantics
_connect_args: dict = {}
if ":memory:" not in DATABASE_URL:
    _connect_args["check_same_thread"] = False

engine = create_async_engine(DATABASE_URL, echo=False, connect_args=_connect_args)


@event.listens_for(engine.sync_engine, "connect")
def _load_sqlite_vec(dbapi_conn, _connection_record):
    """Load sqlite-vec extension on every new aiosqlite connection.

    aiosqlite wraps sqlite3 in a worker thread.  The 'connect' event fires
    on the *calling* thread (the asyncio event-loop thread), so we push a
    callable into aiosqlite's internal thread-queue (_tx) so it executes in
    the correct worker thread.

    IMPORTANT: we use fire-and-forget (no done.wait()) to avoid a deadlock
    that occurs when the event-loop thread blocks on done.wait() while the
    aiosqlite worker thread is itself waiting for the event loop to drain
    its queue.  Loading failures are only logged as warnings.
    """
    try:
        import sqlite_vec
        aiosqlite_conn = getattr(dbapi_conn, "_connection", None)
        if aiosqlite_conn is None:
            logger.warning("sqlite-vec: cannot find aiosqlite connection object")
            return

        def _do_load():
            try:
                raw = aiosqlite_conn._conn  # real sqlite3.Connection
                raw.enable_load_extension(True)
                sqlite_vec.load(raw)
                raw.enable_load_extension(False)
                logger.debug("sqlite-vec loaded successfully")
            except Exception as exc:
                logger.warning(f"sqlite-vec not available, vector search disabled: {exc}")

        # Fire-and-forget: push into aiosqlite's worker-thread queue without
        # blocking the calling thread.  The extension will be ready before any
        # SQL that uses vec0 virtual tables is executed (because all SQL also
        # goes through the same worker-thread queue, which is FIFO).
        aiosqlite_conn._tx.put_nowait((None, _do_load))
    except Exception as e:
        logger.warning(f"sqlite-vec load hook failed: {e}")


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
