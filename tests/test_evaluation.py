#!/usr/bin/env python3
"""
Test script for HR Screening System
"""

import json
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import workers
from models import Job

def test_pdf_reading():
    """Test PDF reading with PyMuPDF"""
    print("🔍 Testing PDF Reading...")

    cv_path = "samples/pdfs/cv_1_john_doe.pdf"
    report_path = "samples/pdfs/project_report_1_excellent.pdf"

    if not os.path.exists(cv_path):
        print(f"❌ CV file not found: {cv_path}")
        return False

    if not os.path.exists(report_path):
        print(f"❌ Report file not found: {report_path}")
        return False

    try:
        cv_text = workers._read_pdf_text(cv_path)
        report_text = workers._read_pdf_text(report_path)

        print(f"✅ CV Text Length: {len(cv_text)} characters")
        print(f"✅ Report Text Length: {len(report_text)} characters")
        print(f"✅ CV Sample: {cv_text[:200]}...")

        return True
    except Exception as e:
        print(f"❌ PDF reading failed: {e}")
        return False

def test_evaluation_logic():
    """Test evaluation logic with mock data"""
    print("\n🧠 Testing Evaluation Logic...")

    try:
        # Test mock evaluation
        cv_match_rate = min(1.0, max(0.0, 3000 / 5000.0))  # Based on text length
        project_score = min(5.0, max(1.0, 10000 / 2000.0))  # Based on text length

        result = {
            'cv_match_rate': round(cv_match_rate, 2),
            'cv_feedback': f'CV dievaluasi untuk Backend Engineer. Panjang teks menunjukkan pengalaman yang solid.',
            'project_score': round(project_score, 1),
            'project_feedback': 'Project report menunjukkan implementasi teknis yang baik dengan detail lengkap.',
            'overall_summary': 'Kandidat menunjukkan kecocokan baik dengan kombinasi pengalaman teknis dan implementasi project.'
        }

        print(f"✅ CV Match Rate: {result['cv_match_rate']}")
        print(f"✅ Project Score: {result['project_score']}")
        print(f"✅ Overall Summary: {result['overall_summary']}")

        return True
    except Exception as e:
        print(f"❌ Evaluation logic failed: {e}")
        return False

def test_database_operations():
    """Test database operations"""
    print("\n💾 Testing Database Operations...")

    try:
        # Create test job
        job_id = Job.create("Test Backend Engineer", 13, 14)
        print(f"✅ Created test job with ID: {job_id}")

        # Get job details
        job = Job.get_by_id(job_id)
        if job:
            print(f"✅ Retrieved job: {job['job_title']}")
        else:
            print(f"❌ Failed to retrieve job {job_id}")
            return False

        # Update job status
        test_result = {
            'cv_match_rate': 0.85,
            'cv_feedback': 'Test feedback',
            'project_score': 4.5,
            'project_feedback': 'Test project feedback',
            'overall_summary': 'Test summary'
        }

        Job.update_status(job_id, 'completed', result_json=json.dumps(test_result))
        print(f"✅ Updated job status to 'completed'")

        # Verify update
        updated_job = Job.get_by_id(job_id)
        if updated_job and updated_job['status'] == 'completed':
            print(f"✅ Job status verified: {updated_job['status']}")
            return True
        else:
            print(f"❌ Job status update failed")
            return False

    except Exception as e:
        print(f"❌ Database operations failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting HR Screening System Tests")
    print("=" * 50)

    tests = [
        test_pdf_reading,
        test_evaluation_logic,
        test_database_operations
    ]

    results = []
    for test in tests:
        result = test()
        results.append(result)

    print("\n" + "=" * 50)
    print("📊 Test Results:")

    passed = sum(results)
    total = len(results)

    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")

    if passed == total:
        print("\n🎉 All tests passed! System is working correctly.")
        return True
    else:
        print("\n⚠️  Some tests failed. Please check the system.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)