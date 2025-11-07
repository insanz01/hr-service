#!/usr/bin/env python3
"""
Test multiple evaluation scenarios
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import workers
from models import Job, Document

def run_evaluation(cv_file, report_file, job_title, scenario_name):
    """Run evaluation for specific scenario"""
    print(f"\n🎯 Testing Scenario: {scenario_name}")
    print(f"CV: {cv_file}")
    print(f"Report: {report_file}")
    print(f"Job Title: {job_title}")
    print("-" * 50)

    try:
        # Upload documents
        cv_path = f"samples/pdfs/{cv_file}"
        report_path = f"samples/pdfs/{report_file}"

        if not os.path.exists(cv_path):
            print(f"❌ CV file not found: {cv_path}")
            return None

        if not os.path.exists(report_path):
            print(f"❌ Report file not found: {report_path}")
            return None

        # Create document records
        cv_id = Document.create('cv', cv_file, cv_path)
        report_id = Document.create('report', report_file, report_path)

        # Create job
        job_id = Job.create(job_title, cv_id, report_id)

        # Extract text
        cv_text = workers._read_pdf_text(cv_path)
        report_text = workers._read_pdf_text(report_path)

        print(f"✅ CV Text Length: {len(cv_text)} characters")
        print(f"✅ Report Text Length: {len(report_text)} characters")

        # Mock evaluation based on content length and file type
        if "excellent" in cv_file:
            cv_match_rate = min(0.95, max(0.8, len(cv_text) / 5000.0))
            cv_feedback = "Excellent CV with strong technical background and extensive experience."
        elif "good" in cv_file:
            cv_match_rate = min(0.75, max(0.6, len(cv_text) / 5000.0))
            cv_feedback = "Good CV with solid technical skills and relevant experience."
        else:  # basic
            cv_match_rate = min(0.6, max(0.4, len(cv_text) / 5000.0))
            cv_feedback = "Basic CV showing entry to mid-level experience."

        if "excellent" in report_file:
            project_score = min(5.0, max(4.5, len(report_text) / 2000.0))
            project_feedback = "Excellent project implementation with advanced features and clean code."
        elif "good" in report_file:
            project_score = min(4.5, max(3.5, len(report_text) / 2000.0))
            project_feedback = "Good project implementation with solid technical approach."
        else:  # basic
            project_score = min(3.5, max(2.5, len(report_text) / 2000.0))
            project_feedback = "Basic project implementation with room for improvement."

        # Generate overall summary
        if cv_match_rate >= 0.8 and project_score >= 4.5:
            overall = "Strong candidate with excellent technical skills and project quality. Highly recommended."
        elif cv_match_rate >= 0.6 and project_score >= 3.5:
            overall = "Good candidate with solid technical background. Recommended for consideration."
        else:
            overall = "Entry-level candidate showing potential. Consider for junior positions with additional training."

        result = {
            'cv_match_rate': round(cv_match_rate, 2),
            'cv_feedback': cv_feedback,
            'project_score': round(project_score, 1),
            'project_feedback': project_feedback,
            'overall_summary': overall
        }

        # Update job status
        Job.update_status(job_id, 'completed', result_json=json.dumps(result))

        print(f"✅ Evaluation Results:")
        print(f"   CV Match Rate: {result['cv_match_rate']}")
        print(f"   Project Score: {result['project_score']}")
        print(f"   Overall Summary: {result['overall_summary']}")

        return {
            'job_id': job_id,
            'cv_id': cv_id,
            'report_id': report_id,
            'result': result
        }

    except Exception as e:
        print(f"❌ Scenario failed: {e}")
        return None

def main():
    """Test all scenarios"""
    print("🧪 Testing Multiple HR Evaluation Scenarios")
    print("=" * 60)

    scenarios = [
        {
            'cv': 'cv_1_john_doe.pdf',
            'report': 'project_report_1_excellent.pdf',
            'job_title': 'Senior Backend Engineer',
            'name': 'Excellent Candidate + Excellent Project'
        },
        {
            'cv': 'cv_2_sarah_wilson.pdf',
            'report': 'project_report_2_good.pdf',
            'job_title': 'Backend Developer',
            'name': 'Good Candidate + Good Project'
        },
        {
            'cv': 'cv_3_mike_chen.pdf',
            'report': 'project_report_3_basic.pdf',
            'job_title': 'Junior Backend Developer',
            'name': 'Basic Candidate + Basic Project'
        }
    ]

    results = []
    for scenario in scenarios:
        result = run_evaluation(
            cv_file=scenario['cv'],
            report_file=scenario['report'],
            job_title=scenario['job_title'],
            scenario_name=scenario['name']
        )
        if result:
            results.append(result)

    print(f"\n" + "=" * 60)
    print("📊 Scenario Test Summary:")
    print(f"✅ Successful Scenarios: {len(results)}/{len(scenarios)}")

    if results:
        print("\n🎯 Evaluation Results Summary:")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['result']['overall_summary']}")
            print(f"   CV Match: {result['result']['cv_match_rate']}, Project Score: {result['result']['project_score']}")

    print(f"\n🔗 API Test Results:")
    for result in results:
        import requests
        response = requests.get(f"http://localhost:5000/result/{result['job_id']}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Job {result['job_id']}: {data['status']} - CV: {data['result']['cv_match_rate']}")
        else:
            print(f"❌ Job {result['job_id']}: API Error")

    return len(results) == len(scenarios)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)