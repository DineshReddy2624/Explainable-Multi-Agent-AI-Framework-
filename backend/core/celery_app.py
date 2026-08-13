import os
from celery import Celery
from core.config import settings

celery_app = Celery(
    "data_quality_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=360,
    task_soft_time_limit=300,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    worker_concurrency=getattr(settings, "CELERY_WORKER_CONCURRENCY", 4),
    result_expires=86400,
)

# Auto-discover tasks in backend.tasks
celery_app.autodiscover_tasks(["tasks.background_tasks"])
