#!/usr/bin/env python3
"""
Simple Redis-based Worker untuk menggantikan Celery
Lebih transparan dan mudah di-debug
"""

import os
import json
import time
import logging
import traceback
import random
from datetime import datetime, timezone
from typing import Dict, Any, Optional

import redis
from src.models.database import Job, Document
from src.core.ai_engine import evaluate_cv, evaluate_project, synthesize_overall

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleWorker:
    def __init__(self):
        """Initialize worker dengan Redis connection"""
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self.redis_client = self._create_redis_connection()

        # Queue names
        self.queue_name = "evaluation_queue"
        self.result_prefix = "job_result:"

        logger.info(f"Worker initialized with Redis: {self.redis_url}")

    def _create_redis_connection(self):
        """Create Redis connection with retry mechanism"""
        max_retries = 5
        base_delay = 2.0

        for attempt in range(max_retries + 1):
            try:
                client = redis.from_url(self.redis_url, decode_responses=True)
                # Test connection
                client.ping()
                logger.info(f"Redis connection established (attempt {attempt + 1})")
                return client
            except Exception as e:
                error_str = str(e).lower()
                is_retryable = (
                    "connection" in error_str or
                    "timeout" in error_str or
                    "refused" in error_str or
                    "unreachable" in error_str
                )

                if not is_retryable:
                    logger.error(f"Non-retryable Redis error: {e}")
                    raise RuntimeError(f"Failed to connect to Redis: {str(e)}")

                if attempt == max_retries:
                    logger.error(f"Max retries ({max_retries}) reached for Redis connection")
                    raise RuntimeError(f"Failed to connect to Redis after {max_retries} attempts: {str(e)}")

                delay = base_delay * (2 ** attempt) + random.uniform(0.5, 1.5)
                delay = min(delay, 30)  # Cap at 30 seconds

                logger.warning(f"Redis connection failed (attempt {attempt + 1}/{max_retries + 1}), retrying in {delay:.2f}s: {e}")
                time.sleep(delay)

    def _read_file_content_with_retry(self, file_path: str, max_retries: int = 3) -> str:
        """Read content from file (PDF or text) with retry mechanism"""
        base_delay = 1.0

        for attempt in range(max_retries + 1):
            try:
                return self._read_file_content(file_path)
            except Exception as e:
                error_str = str(e).lower()
                is_retryable = (
                    "permission denied" in error_str or
                    "being used by another process" in error_str or
                    "i/o error" in error_str or
                    "timeout" in error_str or
                    "temporarily unavailable" in error_str
                )

                if not is_retryable:
                    logger.error(f"Non-retryable file reading error: {e}")
                    raise RuntimeError(f"Failed to read file {file_path}: {str(e)}")

                if attempt == max_retries:
                    logger.error(f"Max retries ({max_retries}) reached for reading file {file_path}")
                    raise RuntimeError(f"Failed to read file {file_path} after {max_retries} attempts: {str(e)}")

                delay = base_delay * (2 ** attempt) + random.uniform(0.2, 1.0)
                delay = min(delay, 10)  # Cap at 10 seconds

                logger.warning(f"File reading failed (attempt {attempt + 1}/{max_retries + 1}), retrying in {delay:.2f}s: {e}")
                time.sleep(delay)

        return ""

    def _read_file_content(self, file_path: str) -> str:
        """Read content from file (PDF or text)"""
        # Check if file is PDF by extension
        if file_path.lower().endswith('.pdf'):
            # Use PyMuPDF for better PDF reading
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(file_path)
                text = ""
                for page in doc:
                    text += page.get_text() + "\n"
                doc.close()
                logger.info(f"Successfully read PDF with PyMuPDF: {len(text)} characters")
                return text.strip()
            except ImportError:
                logger.error("PyMuPDF (fitz) not available, falling back to basic reading")
                # Fallback to PyPDF2 if available
                try:
                    from PyPDF2 import PdfReader
                    reader = PdfReader(file_path)
                    return "\n\n".join((p.extract_text() or "") for p in reader.pages)
                except Exception as e:
                    logger.error(f"PyPDF2 also failed: {e}")
                    raise RuntimeError(f"Failed to read PDF {file_path}: {str(e)}")
            except Exception as e:
                logger.error(f"Error reading PDF with PyMuPDF {file_path}: {e}")
                raise RuntimeError(f"Failed to read PDF {file_path}: {str(e)}")
        else:
            # Read as text file
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    logger.info(f"Successfully read text file: {len(content)} characters")
                    return content.strip()
            except Exception as e:
                logger.error(f"Error reading text file {file_path}: {e}")
                raise RuntimeError(f"Failed to read text file {file_path}: {str(e)}")

    def check_ai_availability(self) -> bool:
        """Check if AI engine is available"""
        try:
            from src.core.ai_engine import available
            return available()
        except Exception as e:
            logger.error(f"Error checking AI availability: {e}")
            return False

    def process_job_with_retry(self, job_data: Dict[str, Any], max_retries: int = 2) -> Dict[str, Any]:
        """Process individual job with retry mechanism"""
        base_delay = 5.0

        for attempt in range(max_retries + 1):
            try:
                return self.process_job(job_data)
            except Exception as e:
                error_str = str(e).lower()
                is_retryable = (
                    "ai services not available" in error_str or
                    "rate limit" in error_str or
                    "timeout" in error_str or
                    "connection" in error_str or
                    "temporarily unavailable" in error_str or
                    "resource exhausted" in error_str or
                    "database" in error_str or
                    "redis" in error_str
                )

                if not is_retryable:
                    logger.error(f"Non-retryable job processing error: {e}")
                    return self._create_error_result(job_data.get('job_id'), e, traceback.format_exc())

                if attempt == max_retries:
                    logger.error(f"Max retries ({max_retries}) reached for job {job_data.get('job_id')}")
                    return self._create_error_result(job_data.get('job_id'), e, f"Failed after {max_retries} retries")

                delay = base_delay * (2 ** attempt) + random.uniform(1.0, 3.0)
                delay = min(delay, 60)  # Cap at 60 seconds

                logger.warning(f"Job processing failed (attempt {attempt + 1}/{max_retries + 1}), retrying in {delay:.2f}s: {e}")
                time.sleep(delay)

    def _create_error_result(self, job_id: int, error: Exception, trace: str) -> Dict[str, Any]:
        """Create standardized error result"""
        if job_id:
            Job.update_status(job_id, "failed")

        return {
            "error": str(error),
            "traceback": trace,
            "processing_metadata": {
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "ai_engine_used": False,
                "worker_type": "simple_redis_worker",
                "retry_failed": True
            }
        }

    def process_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process individual job"""
        job_id = job_data.get('job_id')
        cv_id = job_data.get('cv_id')
        report_id = job_data.get('report_id')
        job_title = job_data.get('job_title')

        logger.info(f"Processing job {job_id} for CV {cv_id}, Report {report_id}, Title: {job_title}")

        # Update job status to processing
        Job.update_status(job_id, "processing")

        # Get documents from database
        cv_doc = Document.get_by_id(cv_id)
        report_doc = Document.get_by_id(report_id)

        if not cv_doc or not report_doc:
            raise ValueError(f"Documents not found: CV={cv_doc is not None}, Report={report_doc is not None}")

        logger.info(f"Retrieved CV: {cv_doc['filename']}, Report: {report_doc['filename']}")

        # Check AI availability
        ai_available = self.check_ai_availability()
        logger.info(f"AI Engine available: {ai_available}")

        if not ai_available:
            logger.error("AI Engine not available - cannot proceed with evaluation")
            raise RuntimeError("AI services not available. Please ensure Instructor, Google Generative AI, and GEMINI_API_KEY are properly configured.")

        # Read document content from files with retry
        logger.info("Reading CV content from file...")
        cv_text = self._read_file_content_with_retry(cv_doc['path'])
        logger.info(f"CV content length: {len(cv_text)} characters")

        logger.info("Reading report content from file...")
        report_text = self._read_file_content_with_retry(report_doc['path'])
        logger.info(f"Report content length: {len(report_text)} characters")

        # Evaluate CV (AI engine already has retry mechanism)
        logger.info("Starting CV evaluation...")
        cv_result = evaluate_cv(
            cv_text=cv_text,
            job_title=job_title
        )
        logger.info(f"CV evaluation completed: match_rate={cv_result.cv_match_rate}")

        # Evaluate Project (AI engine already has retry mechanism)
        logger.info("Starting project evaluation...")
        project_result = evaluate_project(
            report_text=report_text,
            case_brief_text=job_title  # Using job_title as case brief
        )
        logger.info(f"Project evaluation completed: score={project_result.project_score}")

        # Synthesize overall result (AI engine already has retry mechanism)
        logger.info("Starting synthesis...")
        overall_result = synthesize_overall(cv_result, project_result)
        logger.info("Synthesis completed")

        # Prepare final result
        final_result = {
            "cv_result": {
                "match_rate": cv_result.cv_match_rate,
                "feedback": cv_result.cv_feedback
            },
            "project_result": {
                "score": project_result.project_score,
                "feedback": project_result.project_feedback
            },
            "overall_result": {
                "summary": overall_result.overall_summary
            },
            "processing_metadata": {
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "ai_engine_used": ai_available,
                "worker_type": "simple_redis_worker"
            }
        }

        # Update job status to completed
        Job.update_status(job_id, "completed")

        logger.info(f"Job {job_id} completed successfully")
        return final_result

    def save_result(self, job_id: int, result: Dict[str, Any]):
        """Save job result to Redis"""
        result_key = f"{self.result_prefix}{job_id}"
        self.redis_client.setex(
            result_key,
            3600,  # Expire after 1 hour
            json.dumps(result)
        )
        logger.info(f"Result saved for job {job_id}")

    def run(self):
        """Main worker loop"""
        logger.info("Starting Simple Redis Worker...")

        while True:
            try:
                # Check Redis connection with retry
                try:
                    self.redis_client.ping()
                except Exception as e:
                    logger.error(f"Redis ping failed, attempting reconnection: {e}")
                    self.redis_client = self._create_redis_connection()

                # Try to get job from queue (blocking with timeout)
                job_data = self.redis_client.blpop(self.queue_name, timeout=5)

                if job_data:
                    queue_name, job_json = job_data
                    logger.info(f"Received job from queue: {queue_name}")

                    try:
                        # Parse job data
                        job_data = json.loads(job_json)
                        logger.info(f"Job data parsed: {job_data}")

                        # Process the job with retry mechanism
                        result = self.process_job_with_retry(job_data)

                        # Save result
                        self.save_result(job_data['job_id'], result)

                        if 'error' in result:
                            logger.error(f"Job {job_data['job_id']} failed after retries")
                        else:
                            logger.info(f"Job {job_data['job_id']} processed successfully")

                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON in job data: {e}")
                    except KeyError as e:
                        logger.error(f"Missing required field in job data: {e}")
                    except Exception as e:
                        logger.error(f"Unexpected error processing job: {e}")
                        logger.error(f"Traceback: {traceback.format_exc()}")
                else:
                    # No job received, continue loop
                    logger.debug("No jobs in queue, continuing...")

            except KeyboardInterrupt:
                logger.info("Worker stopped by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error in worker loop: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                time.sleep(5)

        logger.info("Worker shutdown complete")

def main():
    """Main entry point"""
    worker = SimpleWorker()
    worker.run()

if __name__ == "__main__":
    main()