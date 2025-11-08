"""
Health Check Module
Provides comprehensive health monitoring for the HR service
"""

import os
import time
from datetime import datetime
from typing import Dict, Any

# Optional psutil import with fallback
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False

try:
    import redis
    from src.models.database import Job, Document
    from src.core.ai_engine import available as ai_available
    from src.core.rag_engine import test_rag_query
except ImportError:
    # Fallback for standalone testing
    ai_available = lambda: False
    test_rag_query = lambda: False


def check_redis_health() -> Dict[str, Any]:
    """Check Redis connection and basic functionality"""
    try:
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        client = redis.from_url(redis_url)

        # Test basic operations
        test_key = f"health_check_{int(time.time())}"
        client.set(test_key, "test", ex=10)
        value = client.get(test_key)
        client.delete(test_key)

        info = client.info()

        return {
            "status": "healthy" if value == b"test" else "unhealthy",
            "connected_clients": info.get("connected_clients", 0),
            "used_memory": info.get("used_memory_human", "0B"),
            "response_time_ms": round(client.ping() * 1000, 2)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


def check_database_health() -> Dict[str, Any]:
    """Check database connectivity and basic operations"""
    try:
        start_time = time.time()

        # Test database operations
        job_count = Job.count()
        document_count = Document.count()

        # Check recent jobs
        recent_jobs = Job.get_recent(limit=5)

        response_time = round((time.time() - start_time) * 1000, 2)

        return {
            "status": "healthy",
            "job_count": job_count,
            "document_count": document_count,
            "recent_jobs_count": len(recent_jobs),
            "response_time_ms": response_time
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


def check_ai_engine_health() -> Dict[str, Any]:
    """Check AI engine availability and basic functionality"""
    try:
        start_time = time.time()

        # Check AI availability
        available = ai_available()

        response_time = round((time.time() - start_time) * 1000, 2)

        return {
            "status": "healthy" if available else "unhealthy",
            "available": available,
            "response_time_ms": response_time
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "available": False
        }


def check_rag_engine_health() -> Dict[str, Any]:
    """Check RAG engine functionality"""
    try:
        start_time = time.time()

        # Test RAG query
        working = test_rag_query()

        response_time = round((time.time() - start_time) * 1000, 2)

        return {
            "status": "healthy" if working else "unhealthy",
            "functional": working,
            "response_time_ms": response_time
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "functional": False
        }


def check_system_resources() -> Dict[str, Any]:
    """Check system resource usage"""
    if not psutil:
        return {
            "status": "healthy",
            "cpu_percent": 0,
            "memory_percent": 0,
            "memory_available_gb": 0,
            "disk_percent": 0,
            "disk_free_gb": 0,
            "note": "psutil not available"
        }

    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return {
            "status": "healthy",
            "cpu_percent": round(cpu_percent, 2),
            "memory_percent": round(memory.percent, 2),
            "memory_available_gb": round(memory.available / (1024**3), 2),
            "disk_percent": round(disk.percent, 2),
            "disk_free_gb": round(disk.free / (1024**3), 2)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


def comprehensive_health_check() -> Dict[str, Any]:
    """Perform comprehensive health check"""
    timestamp = datetime.utcnow().isoformat() + "Z"

    checks = {
        "timestamp": timestamp,
        "status": "healthy",
        "checks": {
            "redis": check_redis_health(),
            "database": check_database_health(),
            "ai_engine": check_ai_engine_health(),
            "rag_engine": check_rag_engine_health(),
            "system_resources": check_system_resources()
        }
    }

    # Determine overall status
    for check_name, check_result in checks["checks"].items():
        if check_result.get("status") != "healthy":
            checks["status"] = "unhealthy"
            break

    return checks


def get_service_metrics() -> Dict[str, Any]:
    """Get detailed service metrics"""
    try:
        # Get job statistics
        total_jobs = Job.count()
        recent_jobs = Job.get_recent(limit=100)

        # Calculate job statistics
        completed_jobs = sum(1 for job in recent_jobs if job["status"] == "completed")
        failed_jobs = sum(1 for job in recent_jobs if job["status"] == "failed")
        processing_jobs = sum(1 for job in recent_jobs if job["status"] == "processing")

        # Document statistics
        total_documents = Document.count()

        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "jobs": {
                "total": total_jobs,
                "recent_completed": completed_jobs,
                "recent_failed": failed_jobs,
                "recent_processing": processing_jobs,
                "success_rate": round(completed_jobs / len(recent_jobs) * 100, 2) if recent_jobs else 0
            },
            "documents": {
                "total": total_documents
            },
            "system": check_system_resources()
        }
    except Exception as e:
        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": str(e)
        }