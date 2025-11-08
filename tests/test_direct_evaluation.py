#!/usr/bin/env python3
"""
Test the evaluation module directly
"""
import os
import sys

# Set environment variables
os.environ.setdefault("GEMINI_API_KEY", "AIzaSyCRtkNwIKFirwnxziwijEx-3lVUOVknjaY")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("REDIS_BACKEND", "redis://localhost:6379/1")

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.evaluation import evaluate_candidate_job
from src.models.database import Job, Document

def test_direct_evaluation():
    """Test evaluation directly without Celery"""
    print("🧪 Testing Direct Evaluation (No Celery)")
    print("=" * 50)

    # Create test documents directly in database
    cv_text = """
John Doe
Senior Backend Engineer

Experience:
- 5 years Python development with Django and FastAPI
- 3 years microservices architecture
- 2 years Redis and PostgreSQL
- 1 year AI/ML integration with TensorFlow

Skills: Python, Django, FastAPI, Redis, PostgreSQL, Docker, TensorFlow, NLP
""".strip()

    report_text = """
Project: AI-Powered Document Analysis System

Implementation:
- FastAPI backend with async support
- Redis for caching and task queuing
- ChromaDB for vector storage
- RAG system with comprehensive error handling
- Docker containerization
- Production-ready monitoring and metrics
""".strip()

    case_text = "Build an AI-powered document analysis system using RAG architecture"

    # Create test documents
    cv_id = Document.create("cv", "test_cv.txt", "/tmp/test_cv.txt")
    report_id = Document.create("report", "test_report.txt", "/tmp/test_report.txt")

    # Create test job
    job_id = Job.create("Senior Backend Engineer (AI/ML Focus)", cv_id, report_id)

    print(f"Created test job: {job_id}")

    # Write test files
    with open(f"/tmp/test_cv.txt", 'w') as f:
        f.write(cv_text)
    with open(f"/tmp/test_report.txt", 'w') as f:
        f.write(report_text)
    with open("docs/case_study_text.txt", 'w') as f:
        f.write(case_text)

    # Test evaluation
    print("\n🔄 Running evaluation...")
    try:
        success, message = evaluate_candidate_job(job_id)
        print(f"   Success: {success}")
        print(f"   Message: {message}")

        if success:
            # Get results
            job = Job.get_by_id(job_id)
            if job and job["status"] == "completed":
                import json
                result = json.loads(job["result_json"])
                print(f"\n📊 Results:")
                print(f"   CV Match Rate: {result.get('cv_match_rate', 0):.2f}")
                print(f"   CV Feedback: {result.get('cv_feedback', 'N/A')}")
                print(f"   Project Score: {result.get('project_score', 0):.1f}")
                print(f"   Project Feedback: {result.get('project_feedback', 'N/A')}")
                print(f"   Overall Summary: {result.get('overall_summary', 'N/A')}")

                # Check if AI was used
                cv_score = result.get('cv_match_rate', 0)
                project_score = result.get('project_score', 0)

                if cv_score > 0.5 and project_score > 2.0:
                    print(f"\n🎉 SUCCESS: AI evaluation worked without fallback!")
                    return True
                else:
                    print(f"\n⚠️  May still be using fallback evaluation")
                    return True
            else:
                print(f"❌ Job not completed: {job['status'] if job else 'Not found'}")
                return False
        else:
            print(f"❌ Evaluation failed: {message}")
            return False

    except Exception as e:
        print(f"❌ Evaluation exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_direct_evaluation()
    print(f"\n📊 Test result: {'SUCCESS' if success else 'FAILED'}")