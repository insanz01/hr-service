#!/usr/bin/env python3
"""
Queue Manager untuk Simple Redis Worker
Menghandle job submission dan result retrieval
"""

import os
import json
import redis
from typing import Dict, Any, Optional, List
from datetime import datetime

class SimpleQueueManager:
    def __init__(self):
        """Initialize queue manager dengan Redis connection"""
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self.redis_client = redis.from_url(self.redis_url, decode_responses=True)

        # Queue names
        self.queue_name = "evaluation_queue"
        self.result_prefix = "job_result:"

    def submit_job(self, job_id: int, cv_id: int, report_id: int, job_title: str) -> bool:
        """Submit job ke queue"""
        try:
            job_data = {
                "job_id": job_id,
                "cv_id": cv_id,
                "report_id": report_id,
                "job_title": job_title,
                "submitted_at": datetime.utcnow().isoformat(),
                "queue_type": "simple_redis_worker"
            }

            # Convert to JSON dan push ke queue
            job_json = json.dumps(job_data)
            self.redis_client.lpush(self.queue_name, job_json)

            print(f"✅ Job {job_id} submitted to queue successfully")
            return True

        except Exception as e:
            print(f"❌ Error submitting job {job_id}: {e}")
            return False

    def get_result(self, job_id: int, timeout: int = 300) -> Optional[Dict[str, Any]]:
        """Get job result dengan timeout"""
        result_key = f"{self.result_prefix}{job_id}"

        start_time = datetime.utcnow()

        while True:
            # Check if result exists
            result_json = self.redis_client.get(result_key)

            if result_json:
                try:
                    result = json.loads(result_json)
                    print(f"✅ Retrieved result for job {job_id}")
                    return result
                except json.JSONDecodeError as e:
                    print(f"❌ Error decoding result for job {job_id}: {e}")
                    return None

            # Check timeout
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            if elapsed > timeout:
                print(f"⏰ Timeout waiting for result of job {job_id} after {timeout}s")
                return None

            # Wait before checking again
            import time
            time.sleep(2)

    def get_queue_status(self) -> Dict[str, Any]:
        """Get queue status info"""
        try:
            queue_length = self.redis_client.llen(self.queue_name)

            # Get all result keys
            result_keys = self.redis_client.keys(f"{self.result_prefix}*")
            active_results = len(result_keys)

            return {
                "queue_length": queue_length,
                "active_results": active_results,
                "redis_url": self.redis_url,
                "queue_name": self.queue_name,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    def clear_queue(self) -> bool:
        """Clear all jobs from queue"""
        try:
            self.redis_client.delete(self.queue_name)
            print(f"✅ Queue {self.queue_name} cleared")
            return True
        except Exception as e:
            print(f"❌ Error clearing queue: {e}")
            return False

    def clear_results(self) -> bool:
        """Clear all results"""
        try:
            result_keys = self.redis_client.keys(f"{self.result_prefix}*")
            if result_keys:
                self.redis_client.delete(*result_keys)
                print(f"✅ Cleared {len(result_keys)} results")
            return True
        except Exception as e:
            print(f"❌ Error clearing results: {e}")
            return False

# Global instance
queue_manager = SimpleQueueManager()