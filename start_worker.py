#!/usr/bin/env python3
"""
Start Celery worker with proper task registration.
"""

import os

# Set environment variables
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("REDIS_BACKEND", "redis://localhost:6379/1")

# Import celery app first
from celery_app import celery


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
