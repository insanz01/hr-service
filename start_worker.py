#!/usr/bin/env python3
"""
Start Celery worker with proper task registration.
"""

import os

# Set environment variables
os.environ.setdefault("REDIS_URL", "redis://redis:6379/0")
os.environ.setdefault("REDIS_BACKEND", "redis://redis:6379/1")

# Import celery app first
from src.workers.celery_app import celery

# Import tasks to register them
from src.workers import tasks


def main():
    print("Starting Celery worker with tasks...")
    print("Registered tasks:", list(celery.tasks.keys()))

    # Start worker
    celery.worker_main(
        [
            "worker",
            "--loglevel=info",
            "--concurrency=4",
            "--queues=default,upload,evaluation",
        ]
    )


if __name__ == "__main__":
    main()
