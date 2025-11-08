#!/usr/bin/env python3
"""
Test instructor integration with Gemini API
"""
import os
import sys

# Set environment variables
os.environ.setdefault("GEMINI_API_KEY", "AIzaSyCRtkNwIKFirwnxziwijEx-3lVUOVknjaY")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("REDIS_BACKEND", "redis://localhost:6379/1")

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.ai_engine import available, evaluate_cv, evaluate_project, synthesize_overall

def test_instructor_with_gemini():
    """Test instructor integration with Gemini"""
    print("🧪 Testing Instructor with Gemini API")
    print("=" * 50)

    # Check availability
    ai_available = available()
    print(f"AI Engine Available: {ai_available}")

    if not ai_available:
        print("❌ AI Engine not available, cannot test")
        return False

    # Test CV evaluation
    print("\n📄 Testing CV evaluation with instructor...")
    try:
        cv_text = """
        Jane Smith
        Senior AI/ML Engineer

        Experience:
        - 7 years building production ML systems
        - 5 years with deep learning frameworks (TensorFlow, PyTorch)
        - 3 years MLOps and model deployment
        - Expert in Python, FastAPI, Docker, Kubernetes
        - Experience with vector databases and RAG systems
        - Led team of 5 ML engineers

        Skills: Python, TensorFlow, PyTorch, FastAPI, Docker, Kubernetes,
        Vector Databases, RAG, LLMs, MLOps, CI/CD, AWS, GCP

        Projects:
        - Built recommendation system serving 10M+ users
        - Implemented real-time fraud detection system
        - Developed RAG-powered customer support chatbot
        """.strip()

        cv_result = evaluate_cv(cv_text, "Senior AI/ML Engineer")
        print(f"✅ CV Evaluation SUCCESS:")
        print(f"   Match Rate: {cv_result.cv_match_rate}")
        print(f"   Feedback: {cv_result.cv_feedback}")
        print(f"   Using instructor with Gemini: True")

    except Exception as e:
        print(f"❌ CV evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test Project evaluation
    print("\n📊 Testing Project evaluation with instructor...")
    try:
        project_text = """
        Project: Production-Grade RAG System for Enterprise Knowledge Management

        Architecture Overview:
        - Microservices architecture with FastAPI
        - Document processing pipeline with async operations
        - Vector storage using Weaviate with backup to PostgreSQL
        - LLM integration with multiple providers (OpenAI, Anthropic, Gemini)
        - Comprehensive caching strategy with Redis
        - Real-time search with Elasticsearch integration

        Technical Implementation:

        1. Document Processing:
        - Multi-format support (PDF, DOCX, TXT, HTML)
        - Intelligent chunking with semantic boundaries
        - Metadata extraction and indexing
        - Version control for document updates

        2. Vector Search:
        - Hybrid search (semantic + keyword)
        - Reranking for improved relevance
        - Faceted search and filtering
        - Real-time indexing updates

        3. LLM Integration:
        - Provider abstraction layer
        - Prompt engineering with templates
        - Response caching and optimization
        - Rate limiting and cost management

        4. Production Features:
        - Monitoring with Prometheus and Grafana
        - Distributed tracing with OpenTelemetry
        - Error handling and circuit breakers
        - Auto-scaling based on load

        Performance Metrics:
        - 99.9% uptime over 12 months
        - Average response time: 150ms
        - Handles 10K concurrent requests
        - Processes 100K documents/hour
        """.strip()

        case_brief = "Build enterprise-grade RAG system with multi-modal support, real-time processing, and production-ready scalability"

        project_result = evaluate_project(project_text, case_brief)
        print(f"✅ Project Evaluation SUCCESS:")
        print(f"   Score: {project_result.project_score}")
        print(f"   Feedback: {project_result.project_feedback}")
        print(f"   Using instructor with Gemini: True")

    except Exception as e:
        print(f"❌ Project evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test synthesis
    print("\n🔗 Testing synthesis with instructor...")
    try:
        overall_result = synthesize_overall(cv_result, project_result)
        print(f"✅ Synthesis SUCCESS:")
        print(f"   Overall Summary: {overall_result.overall_summary}")
        print(f"   Using instructor with Gemini: True")

    except Exception as e:
        print(f"❌ Synthesis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n🎉 All instructor tests passed! Gemini integration with instructor works correctly.")
    return True

if __name__ == "__main__":
    success = test_instructor_with_gemini()
    print(f"\n📊 Test result: {'SUCCESS' if success else 'FAILED'}")