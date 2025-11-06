import os
from celery import Celery


def make_celery() -> Celery:
    """Create and configure Celery instance.

    Uses Redis by default. Configure via env:
    - REDIS_URL: broker URL (default: redis://localhost:6379/0)
    - REDIS_BACKEND: result backend (default: redis://localhost:6379/1)
    """
    broker = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    backend = os.getenv("REDIS_BACKEND", os.getenv("REDIS_URL", "redis://localhost:6379/1"))

    celery = Celery("hr_service", broker=broker, backend=backend)
    celery.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone=os.getenv("TZ", "UTC"),
        enable_utc=True,
        worker_max_tasks_per_child=1000,
    )
    return celery


celery = make_celery()