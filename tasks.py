from datetime import timedelta

from celery_app import celery
from workers import process_uploaded_file, run_job


@celery.task(name="upload.process", autoretry_for=(Exception,), retry_backoff=5, retry_kwargs={"max_retries": 3})
def process_uploaded_file_task(doc_id: int, path: str, doc_type: str) -> None:
    process_uploaded_file(doc_id=doc_id, path=path, doc_type=doc_type)


@celery.task(name="evaluate.run_job", bind=True, autoretry_for=(Exception,), retry_backoff=10, retry_kwargs={"max_retries": 5})
def run_job_task(self, job_id: int) -> None:
    # Optional soft time limit to avoid long-hanging tasks
    self.request.timelimit = (None, int(timedelta(minutes=10).total_seconds()))
    run_job(job_id=job_id)