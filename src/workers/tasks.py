from datetime import timedelta

from src.workers.celery_app import celery
from src.core.evaluation import evaluate_candidate_job


@celery.task(name="upload.process", autoretry_for=(Exception,), retry_backoff=5, retry_kwargs={"max_retries": 3})
def process_uploaded_file_task(doc_id: int, path: str, doc_type: str) -> None:
    """Process uploaded file in background"""
    # This would need implementation for file processing
    # For now, keeping placeholder
    pass


@celery.task(name="evaluate.run_job", bind=True, autoretry_for=(Exception,), retry_backoff=10, retry_kwargs={"max_retries": 5})
def run_job_task(self, job_id: int) -> None:
    """Run evaluation job in background"""
    # Optional soft time limit to avoid long-hanging tasks
    self.request.timelimit = (None, int(timedelta(minutes=10).total_seconds()))

    success, message = evaluate_candidate_job(job_id)
    if not success:
        raise Exception(f"Evaluation failed: {message}")