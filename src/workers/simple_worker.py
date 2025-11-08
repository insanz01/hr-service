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
from datetime import datetime
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
        self.redis_client = redis.from_url(self.redis_url, decode_responses=True)

        # Queue names
        self.queue_name = "evaluation_queue"
        self.result_prefix = "job_result:"

        logger.info(f"Worker initialized with Redis: {self.redis_url}")

    def _read_file_content(self, file_path: str) -> str:
        """Read content from file (PDF or text)"""
        try:
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
                        return ""
                except Exception as e:
                    logger.error(f"Error reading PDF with PyMuPDF {file_path}: {e}")
                    return ""
            else:
                # Read as text file
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    logger.info(f"Successfully read text file: {len(content)} characters")
                    return content.strip()
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return ""

    def check_ai_availability(self) -> bool:
        """Check if AI engine is available"""
        try:
            from src.core.ai_engine import available
            return available()
        except Exception as e:
            logger.error(f"Error checking AI availability: {e}")
            return False

    def process_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process individual job"""
        job_id = job_data.get('job_id')
        cv_id = job_data.get('cv_id')
        report_id = job_data.get('report_id')
        job_title = job_data.get('job_title')

        logger.info(f"Processing job {job_id} for CV {cv_id}, Report {report_id}, Title: {job_title}")

        try:
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

            # Read document content from files
            logger.info("Reading CV content from file...")
            cv_text = self._read_file_content(cv_doc['path'])
            logger.info(f"CV content length: {len(cv_text)} characters")

            logger.info("Reading report content from file...")
            report_text = self._read_file_content(report_doc['path'])
            logger.info(f"Report content length: {len(report_text)} characters")

            # Evaluate CV
            logger.info("Starting CV evaluation...")
            cv_result = evaluate_cv(
                cv_text=cv_text,
                job_title=job_title
            )
            logger.info(f"CV evaluation completed: match_rate={cv_result.cv_match_rate}")

            # Evaluate Project
            logger.info("Starting project evaluation...")
            project_result = evaluate_project(
                report_text=report_text,
                case_brief_text=job_title  # Using job_title as case brief
            )
            logger.info(f"Project evaluation completed: score={project_result.project_score}")

            # Synthesize overall result
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
                    "processed_at": datetime.utcnow().isoformat(),
                    "ai_engine_used": ai_available,
                    "worker_type": "simple_redis_worker"
                }
            }

            # Update job status to completed
            Job.update_status(job_id, "completed")

            logger.info(f"Job {job_id} completed successfully")
            return final_result

        except Exception as e:
            logger.error(f"Error processing job {job_id}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")

            # Update job status to failed
            Job.update_status(job_id, "failed")

            return {
                "error": str(e),
                "traceback": traceback.format_exc(),
                "processing_metadata": {
                    "processed_at": datetime.utcnow().isoformat(),
                    "ai_engine_used": False,
                    "worker_type": "simple_redis_worker"
                }
            }

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
                # Check Redis connection
                self.redis_client.ping()

                # Try to get job from queue (blocking with timeout)
                job_data = self.redis_client.blpop(self.queue_name, timeout=5)

                if job_data:
                    queue_name, job_json = job_data
                    logger.info(f"Received job from queue: {queue_name}")

                    try:
                        # Parse job data
                        job_data = json.loads(job_json)
                        logger.info(f"Job data parsed: {job_data}")

                        # Process the job
                        result = self.process_job(job_data)

                        # Save result
                        self.save_result(job_data['job_id'], result)

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

            except redis.ConnectionError as e:
                logger.error(f"Redis connection error: {e}")
                logger.info("Waiting 5 seconds before retry...")
                time.sleep(5)
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