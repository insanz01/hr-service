"""
Evaluation Module
Contains core evaluation logic moved from workers.py
"""

import json
import os
from datetime import datetime

# Import from restructured modules
from src.models.database import Job
from src.core.rag_engine import query
from src.core.ai_engine import evaluate_cv, evaluate_project, synthesize_overall

# Constants
CASE_STUDY_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'docs', 'case_study_text.txt')


def evaluate_candidate_job(job_id):
    """
    Core evaluation logic for candidate assessment
    """
    try:
        job = Job.get_by_id(job_id)
        if not job:
            return False, "Job not found"

        # Update status to processing
        Job.update_status(job_id, 'processing')

        # Parse job data
        documents = json.loads(job.documents or "[]")
        cv_text = ""
        report_text = ""

        # Extract text from uploaded documents
        for doc in documents:
            document = Job.get_document_by_id(doc["id"])
            if document:
                file_path = document.file_path
                if os.path.exists(file_path):
                    try:
                        with open(file_path.replace('.pdf', '.txt'), 'r', encoding='utf-8') as f:
                            text = f.read()
                        if doc["type"] == "cv":
                            cv_text = text
                        else:
                            report_text = text
                    except Exception:
                        pass

        # Ensure case study brief is available for context
        case_text = ""
        try:
            with open(CASE_STUDY_PATH, "r", encoding="utf-8") as f:
                case_text = f.read()
        except FileNotFoundError:
            case_text = ""

        # RAG retrieval: gunakan API rag.query yang tersedia
        try:
            cv_snippets = [d['document'] for d in query(job['job_title'] or '', n_results=3)]
        except Exception:
            cv_snippets = []
        try:
            report_snippets = [d['document'] for d in query('project scoring prompt chaining RAG error handling', n_results=3)]
        except Exception:
            report_snippets = []

        # LLM evaluation with built-in fallback mechanism
        try:
            cv_res = evaluate_cv(cv_text=cv_text, case_brief=case_text, context=cv_snippets)
            proj_res = evaluate_project(report_text=report_text, case_brief=case_text, context=report_snippets)
            overall_res = synthesize_overall(cv=cv_res, project=proj_res, case_brief=case_text)
            result = overall_res.dict()

            Job.update_status(job_id, 'completed', result_json=json.dumps(result))
            return True, "Evaluation completed successfully"

        except Exception as e:
            try:
                Job.update_status(job_id, 'failed', error_message=str(e))
            except Exception:
                pass
            return False, f"Evaluation failed: {str(e)}"

    except Exception as e:
        try:
            Job.update_status(job_id, 'failed', error_message=str(e))
        except Exception:
            pass
        return False, f"Process failed: {str(e)}"