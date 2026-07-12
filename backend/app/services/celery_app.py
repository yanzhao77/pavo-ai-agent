from celery import Celery
from app.config import settings

celery_app = Celery(
    "pavo_agent",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.services.video_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)
