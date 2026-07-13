"""Async task queue — replaces Celery for video generation."""
import asyncio, logging, uuid, json
from datetime import datetime
from typing import Callable, Any

logger = logging.getLogger(__name__)


class AsyncTaskQueue:
    """In-memory async task queue with worker and status tracking."""

    def __init__(self, max_concurrent: int = 3):
        self._queue = asyncio.Queue()
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._worker_task: asyncio.Task | None = None
        self._running = False

    async def submit(self, task_type: str, fn: Callable, *args, **kwargs) -> str:
        task_id = str(uuid.uuid4())
        await self._queue.put({"id": task_id, "type": task_type, "fn": fn, "args": args, "kwargs": kwargs})
        await self._update_status(task_id, "pending")
        return task_id

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
        task_id, task_type = item["id"], item["type"]
        try:
            await self._update_status(task_id, "running")
            fn = item["fn"]
            result = await fn(*item["args"], **item["kwargs"]) if asyncio.iscoroutinefunction(fn) else fn(*item["args"], **item["kwargs"])
            await self._update_status(task_id, "done", result)
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            await self._update_status(task_id, "failed", error=str(e))
        finally:
            self._queue.task_done()

    async def _update_status(self, task_id: str, status: str, result: Any = None, error: str = ""):
        try:
            from app.db.database import async_session
            from app.db.database import TaskStatus
            from sqlalchemy import select
            async with async_session() as session:
                r = await session.execute(select(TaskStatus).where(TaskStatus.id == task_id))
                row = r.scalar_one_or_none()
                if row:
                    row.status = status
                    if result: row.result = result if isinstance(result, dict) else {"data": str(result)}
                    if error: row.error = error
                else:
                    session.add(TaskStatus(id=task_id, type="video", status=status, result=result if isinstance(result, dict) else {"data": str(result)} if result else None, error=error))
                await session.commit()
        except Exception as e:
            logger.warning(f"Status update failed: {e}")

    def status(self) -> dict:
        return {"queue_size": self._queue.qsize(), "running": self._running}


task_queue = AsyncTaskQueue()
