"""Video generation tasks — replaces Celery @shared_task with plain async functions.

These functions are submitted to AsyncTaskQueue via task_queue.submit().
"""
import logging
from datetime import datetime

from app.services.agnes_client import agnes_client

logger = logging.getLogger(__name__)


async def generate_video_shot(prompt: str, shot_number: int,
                               project_id: str = "") -> dict:
    """Generate a single video shot via Agnes AI.

    Returns a result dict on success; raises on failure (queue will mark it failed).
    """
    result = await agnes_client.generate_video(prompt)
    output = {
        "shot_number": shot_number,
        "result": result,
        "status": "completed",
        "timestamp": datetime.utcnow().isoformat(),
        "project_id": project_id,
    }
    logger.info(f"Shot {shot_number} completed for project {project_id}")
    return output


async def generate_video_batch(prompts: list[dict],
                                project_id: str = "") -> dict:
    """Submit multiple video-shot tasks to the async task queue.

    Each prompt dict must contain 'prompt' and 'shot_number'.
    Returns immediately with the queued task IDs.
    """
    from app.services.task_queue import task_queue

    task_ids = []
    for p in prompts:
        tid = await task_queue.submit(
            "video_shot",
            generate_video_shot,
            p["prompt"],
            p["shot_number"],
            project_id,
        )
        task_ids.append(tid)

    logger.info(f"Queued {len(task_ids)} shots for project {project_id}")
    return {
        "task_ids": task_ids,
        "shot_count": len(prompts),
        "status": "queued",
        "project_id": project_id,
    }
