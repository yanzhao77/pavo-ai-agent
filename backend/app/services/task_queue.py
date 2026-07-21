"""Async task queue — replaces Celery for video generation."""
import asyncio, logging, uuid
from datetime import datetime
from typing import Callable, Any, Optional

logger = logging.getLogger(__name__)


class AsyncTaskQueue:
    """In-memory async task queue with worker and SQLite status tracking."""

    def __init__(self, max_concurrent: int = 3):
        self._queue: asyncio.Queue = asyncio.Queue()
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._worker_task: Optional[asyncio.Task] = None
        self._running = False
        # In-memory status cache for fast get_status queries
        self._status_cache: dict = {}

    async def submit(self, task_type: str, fn: Callable, *args, **kwargs) -> str:
        """Submit a task and return its task_id."""
        task_id = str(uuid.uuid4())
        await self._queue.put({"id": task_id, "type": task_type, "fn": fn, "args": args, "kwargs": kwargs})
        await self._update_status(task_id, task_type, "pending")
        return task_id

    async def get_status(self, task_id: str) -> Optional[dict]:
        """Return the current status dict for a task_id, or None if not found."""
        if task_id in self._status_cache:
            return self._status_cache[task_id]
        try:
            from app.db.database import async_session, TaskStatus
            from sqlalchemy import select
            async with async_session() as session:
                r = await session.execute(select(TaskStatus).where(TaskStatus.id == task_id))
                row = r.scalar_one_or_none()
                if row:
                    return {"id": row.id, "type": row.type, "status": row.status,
                            "progress": row.progress, "result": row.result, "error": row.error}
        except Exception as e:
            logger.warning(f"get_status DB query failed: {e}")
        return None

    async def start(self):
        self._running = True
        self._worker_task = asyncio.create_task(self._worker_loop())

    async def stop(self):
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try: await self._worker_task
            except asyncio.CancelledError: pass

    async def _worker_loop(self):
        while self._running:
            try:
                item = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                async with self._semaphore:
                    await self._process(item)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Worker error: {e}")

    async def _process(self, item: dict):
        task_id = item["id"]
        task_type = item.get("type", "unknown")
        try:
            await self._update_status(task_id, task_type, "running")
            fn = item["fn"]
            if asyncio.iscoroutinefunction(fn):
                result = await fn(*item["args"], **item["kwargs"])
            else:
                result = fn(*item["args"], **item["kwargs"])
            await self._update_status(task_id, task_type, "completed", result=result)
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            await self._update_status(task_id, task_type, "failed", error=str(e))
        finally:
            self._queue.task_done()

    async def _update_status(self, task_id: str, task_type: str, status: str,
                              result: Any = None, error: str = ""):
        # Always update in-memory cache first
        self._status_cache[task_id] = {
            "id": task_id, "type": task_type, "status": status,
            "result": result, "error": error,
        }
        # Persist to SQLite (best-effort)
        try:
            from app.db.database import async_session, TaskStatus
            from sqlalchemy import select
            result_data = (result if isinstance(result, dict)
                           else {"data": str(result)} if result is not None else {})
            async with async_session() as session:
                r = await session.execute(select(TaskStatus).where(TaskStatus.id == task_id))
                row = r.scalar_one_or_none()
                if row:
                    row.status = status
                    row.type = task_type
                    row.updated_at = datetime.utcnow()
                    if result is not None:
                        row.result = result_data
                    if error:
                        row.error = error
                else:
                    session.add(TaskStatus(id=task_id, type=task_type, status=status,
                                           result=result_data, error=error))
                await session.commit()
        except Exception as e:
            logger.warning(f"Status DB update failed (non-fatal): {e}")

    def status(self) -> dict:
        """Return queue-level status (queue size and running state)."""
        return {"queue_size": self._queue.qsize(), "running": self._running}


task_queue = AsyncTaskQueue()
