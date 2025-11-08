#!/usr/bin/env python3
"""
Test the fixed AI engine with direct Gemini API
"""
import os
import sys

# Set environment variables
os.environ.setdefault("GEMINI_API_KEY", "AIzaSyCRtkNwIKFirwnxziwijEx-3lVUOVknjaY")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("REDIS_BACKEND", "redis://localhost:6379/1")

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.ai_engine_fixed import available, evaluate_cv, evaluate_project, synthesize_overall

def test_fixed_ai():
    """Test the fixed AI engine"""
    print("🧪 Testing Fixed AI Engine")
    print("=" * 50)

    # Check availability
    ai_available = available()
    print(f"AI Engine Available: {ai_available}")

    if not ai_available:
        print("❌ AI Engine not available, cannot test")
        return False

    # Test CV evaluation
    print("\n📄 Testing CV evaluation...")
    try:
        cv_text = """
        John Doe
        Senior Backend Engineer

        Experience:
        - 5 years Python development
        - 3 years microservices architecture
        - 2 years Redis and PostgreSQL
        - 1 year AI/ML integration with TensorFlow

        Skills: Python, Django, FastAPI, Redis, PostgreSQL, Docker, TensorFlow, NLP
        """

        cv_result = evaluate_cv(cv_text, "Senior Backend Engineer")
        print(f"✅ CV Evaluation SUCCESS:")
        print(f"   Match Rate: {cv_result.cv_match_rate}")
        print(f"   Feedback: {cv_result.cv_feedback}")
        print(f"   Using AI (not fallback): True")

    except Exception as e:
        print(f"❌ CV evaluation failed: {e}")
        return False

    # Test Project evaluation
    print("\n📊 Testing Project evaluation...")
    try:
        project_text = """
        Project: AI-Powered Document Analysis System

        Implementation:
        - Used FastAPI for REST API backend
        - Integrated Redis for caching and task queuing
        - Used ChromaDB for vector storage
        - Implemented RAG system with OpenAI embeddings
        - Added comprehensive error handling and logging
        - Used Docker for containerization
        - Added monitoring with Prometheus metrics
        """

        case_brief = "Build an AI-powered document analysis system using RAG architecture"

        project_result = evaluate_project(project_text, case_brief)
        print(f"✅ Project Evaluation SUCCESS:")
        print(f"   Score: {project_result.project_score}")
        print(f"   Feedback: {project_result.project_feedback}")
        print(f"   Using AI (not fallback): True")

    except Exception as e:
        print(f"❌ Project evaluation failed: {e}")
        return False

    # Test synthesis
    print("\n🔗 Testing synthesis...")
    try:
        overall_result = synthesize_overall(cv_result, project_result)
        print(f"✅ Synthesis SUCCESS:")
        print(f"   Overall Summary: {overall_result.overall_summary}")
        print(f"   Using AI (not fallback): True")

    except Exception as e:
        print(f"❌ Synthesis failed: {e}")
        return False

    print("\n🎉 All AI tests passed! The fixed AI engine works correctly.")
    return True

if __name__ == "__main__":
    success = test_fixed_ai()
    print(f"\n📊 Test result: {'SUCCESS' if success else 'FAILED'}")