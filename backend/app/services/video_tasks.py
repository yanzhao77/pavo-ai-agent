import asyncio
import logging
from datetime import datetime
from celery import shared_task
from app.services.agnes_client import agnes_client

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run an async coroutine synchronously for Celery tasks."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # We're in an async context - create new loop
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(coro)
            finally:
                new_loop.close()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


@shared_task(bind=True, max_retries=3, default_retry_delay=5, acks_late=True)
def generate_video_shot(self, prompt: str, shot_number: int, project_id: str = ""):
    """Celery task to generate a single video shot via Agnes AI.
    Falls back to synchronous execution for async API calls.
    """
    try:
        result = _run_async(agnes_client.generate_video(prompt))
        output = {
            "shot_number": shot_number,
            "result": result,
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat(),
        }
        logger.info(f"Shot {shot_number} completed")
        return output
    except Exception as e:
        logger.error(f"Video task failed for shot {shot_number}: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True)
def generate_video_batch(self, prompts: list[dict], project_id: str = ""):
    """Generate multiple video shots asynchronously as a task group."""
    from celery import group

    tasks = [
        generate_video_shot.s(p["prompt"], p["shot_number"], project_id)
        for p in prompts
    ]
    job = group(tasks)
    result = job.apply_async()
    return {
        "task_group_id": result.id,
        "shot_count": len(prompts),
        "status": "queued",
        "project_id": project_id,
    }
