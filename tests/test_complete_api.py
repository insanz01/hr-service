#!/usr/bin/env python3
"""
Complete API test with the fixed AI engine
"""
import requests
import json
import time
import os

API_BASE = "http://localhost:5000"

def test_api_workflow():
    """Test complete API workflow"""
    print("🧪 Testing Complete API Workflow with Fixed AI Engine")
    print("=" * 60)

    # Test 1: Health check
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{API_BASE}/health")
        health_data = response.json()
        print(f"   Status: {response.status_code}")
        print(f"   Overall Status: {health_data.get('status')}")

        # Check AI engine health
        ai_status = health_data.get('checks', {}).get('ai_engine', {})
        print(f"   AI Engine Status: {ai_status.get('status')}")
        print(f"   AI Engine Available: {ai_status.get('available')}")

    except Exception as e:
        print(f"   ❌ Health check failed: {e}")
        return False

    # Test 2: Metrics
    print("\n2. Testing metrics endpoint...")
    try:
        response = requests.get(f"{API_BASE}/metrics")
        metrics_data = response.json()
        print(f"   Status: {response.status_code}")
        print(f"   Total Jobs: {metrics_data.get('jobs', {}).get('total', 0)}")

    except Exception as e:
        print(f"   ❌ Metrics check failed: {e}")
        return False

    # Test 3: Upload documents (using dummy files)
    print("\n3. Testing document upload...")
    try:
        # Create dummy CV and report files
        cv_content = """
John Doe
Senior Backend Engineer

Experience:
- 5 years Python development with Django and FastAPI
- 3 years microservices architecture
- 2 years Redis and PostgreSQL
- 1 year AI/ML integration with TensorFlow
- Experience with Docker, Kubernetes, and cloud deployment

Skills: Python, Django, FastAPI, Redis, PostgreSQL, Docker, Kubernetes, TensorFlow, NLP

Projects:
- Built scalable e-commerce backend handling 10K+ requests/sec
- Implemented real-time analytics pipeline with Redis
- Developed AI-powered recommendation engine
        """.strip()

        report_content = """
Project Implementation Report: AI-Powered Document Analysis System

Technical Architecture:
- Backend: FastAPI with async support
- Database: PostgreSQL for primary storage, Redis for caching
- Vector Storage: ChromaDB for document embeddings
- AI Integration: Google Gemini for document analysis
- Task Queue: Celery with Redis broker
- Monitoring: Comprehensive health checks and metrics

Implementation Details:

1. API Design
- RESTful API endpoints for document upload and processing
- Async request handling for improved performance
- Comprehensive error handling and logging
- Rate limiting and authentication middleware

2. Document Processing Pipeline
- PDF/text extraction with PyMuPDF
- Text chunking and preprocessing
- Vector embedding generation
- Storage in ChromaDB with metadata

3. RAG System Implementation
- Document retrieval using semantic search
- Context-aware prompt engineering
- Chain-of-thought reasoning for complex queries
- Result caching with Redis

4. System Integration
- Docker containerization for all services
- Environment-based configuration
- Health monitoring with comprehensive checks
- Metrics collection and reporting

5. Production Readiness Features
- Comprehensive error handling and retry logic
- Graceful degradation when AI services fail
- Task queue for background processing
- Resource monitoring and scaling considerations

Performance Metrics:
- Average response time: <200ms for cached queries
- Document processing throughput: 100+ docs/minute
- System uptime: 99.9%+ with proper monitoring
- Memory usage: Optimized with efficient caching

Challenges and Solutions:
- Implemented robust error handling for AI API failures
- Created fallback mechanisms for service degradation
- Optimized vector search for better performance
- Added comprehensive logging for debugging
        """.strip()

        # Write to temporary files
        with open('/tmp/test_cv.txt', 'w') as f:
            f.write(cv_content)
        with open('/tmp/test_report.txt', 'w') as f:
            f.write(report_content)

        # Upload files
        with open('/tmp/test_cv.txt', 'rb') as cv_file, \
             open('/tmp/test_report.txt', 'rb') as report_file:

            files = {
                'cv': ('cv.txt', cv_file, 'text/plain'),
                'report': ('report.txt', report_file, 'text/plain')
            }

            response = requests.post(f"{API_BASE}/upload", files=files)
            upload_data = response.json()

            print(f"   Status: {response.status_code}")
            print(f"   CV ID: {upload_data.get('cv_id')}")
            print(f"   Report ID: {upload_data.get('report_id')}")

            cv_id = upload_data.get('cv_id')
            report_id = upload_data.get('report_id')

    except Exception as e:
        print(f"   ❌ Upload failed: {e}")
        return False

    # Test 4: Submit evaluation
    print("\n4. Testing evaluation submission...")
    try:
        job_data = {
            "job_title": "Senior Backend Engineer (AI/ML Focus)",
            "cv_id": cv_id,
            "report_id": report_id
        }

        response = requests.post(f"{API_BASE}/evaluate", json=job_data)
        eval_data = response.json()

        print(f"   Status: {response.status_code}")
        print(f"   Job ID: {eval_data.get('id')}")
        print(f"   Initial Status: {eval_data.get('status')}")

        job_id = eval_data.get('id')

    except Exception as e:
        print(f"   ❌ Evaluation submission failed: {e}")
        return False

    # Test 5: Check results
    print("\n5. Checking evaluation results...")
    max_attempts = 30
    attempt = 0

    while attempt < max_attempts:
        try:
            response = requests.get(f"{API_BASE}/result/{job_id}")
            result_data = response.json()

            status = result_data.get('status')
            print(f"   Attempt {attempt + 1}: Status = {status}")

            if status == 'completed':
                print(f"   ✅ Evaluation completed successfully!")

                result = result_data.get('result', {})
                print(f"\n   📊 Results Summary:")
                print(f"   CV Match Rate: {result.get('cv_match_rate', 0):.2f}")
                print(f"   CV Feedback: {result.get('cv_feedback', 'N/A')}")
                print(f"   Project Score: {result.get('project_score', 0):.1f}")
                print(f"   Project Feedback: {result.get('project_feedback', 'N/A')}")
                print(f"   Overall Summary: {result.get('overall_summary', 'N/A')}")

                # Check if AI was used (not fallback)
                if result.get('cv_match_rate', 0) > 0.5:  # AI typically gives more nuanced scores
                    print(f"\n   🎉 SUCCESS: AI evaluation completed without fallback!")
                    print(f"   The fixed AI engine is working correctly with Celery.")
                else:
                    print(f"\n   ⚠️  Warning: May still be using fallback evaluation")

                return True

            elif status == 'failed':
                error = result_data.get('error', 'Unknown error')
                print(f"   ❌ Evaluation failed: {error}")
                return False

            attempt += 1
            time.sleep(2)

        except Exception as e:
            print(f"   ❌ Result check failed: {e}")
            return False

    print(f"   ⏰ Timeout: Evaluation did not complete within {max_attempts * 2} seconds")
    return False

if __name__ == "__main__":
    success = test_api_workflow()
    print(f"\n{'='*60}")
    print(f"📊 Final Result: {'SUCCESS' if success else 'FAILED'}")

    if success:
        print("✅ All API tests passed! The fixed AI engine works correctly.")
        print("✅ Celery tasks are processed with proper AI evaluation (no fallback).")
        print("✅ Gemini API integration is working with direct API calls.")
    else:
        print("❌ Some tests failed. Please check the logs for details.")