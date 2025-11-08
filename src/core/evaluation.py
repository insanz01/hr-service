"""
Evaluation Module
Contains core evaluation logic moved from workers.py
"""

import json
import os

# Import from restructured modules
from src.models.database import Job, Document
from src.core.rag_engine import query
from src.core.ai_engine import evaluate_cv, evaluate_project, synthesize_overall

# Constants
CASE_STUDY_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "docs", "case_study_text.txt"
)


def _read_pdf_text(path):
    """Read text from PDF or markdown file"""
    try:
        from PyPDF2 import PdfReader

        reader = PdfReader(path)
        return "\n\n".join((p.extract_text() or "") for p in reader.pages)
    except Exception:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return ""


def evaluate_candidate_job(job_id):
    """
    Core evaluation logic for candidate assessment
    """
    try:
        job = Job.get_by_id(job_id)
        if not job:
            return False, "Job not found"

        # Update status to processing
        Job.update_status(job_id, "processing")

        # Get CV and Report documents
        cv_text = ""
        report_text = ""

        # Get CV document
        if job["cv_id"]:
            cv_doc = Document.get_by_id(job["cv_id"])
            if cv_doc:
                cv_sidecar = f"{cv_doc['path']}.txt"
                if os.path.exists(cv_sidecar):
                    with open(cv_sidecar, "r", encoding="utf-8") as f:
                        cv_text = f.read()
                else:
                    cv_text = _read_pdf_text(cv_doc["path"])

        # Get Report document
        if job["report_id"]:
            report_doc = Document.get_by_id(job["report_id"])
            if report_doc:
                report_sidecar = f"{report_doc['path']}.txt"
                if os.path.exists(report_sidecar):
                    with open(report_sidecar, "r", encoding="utf-8") as f:
                        report_text = f.read()
                else:
                    report_text = _read_pdf_text(report_doc["path"])

        # Ensure case study brief is available for context
        case_text = ""
        try:
            with open(CASE_STUDY_PATH, "r", encoding="utf-8") as f:
                case_text = f.read()
        except FileNotFoundError:
            case_text = ""

        # RAG retrieval: gunakan API rag.query yang tersedia
        try:
            cv_snippets = [
                d["document"] for d in query(job["job_title"] or "", n_results=3)
            ]
        except Exception:
            cv_snippets = []
        try:
            report_snippets = [
                d["document"]
                for d in query(
                    "project scoring prompt chaining RAG error handling", n_results=3
                )
            ]
        except Exception:
            report_snippets = []

        # LLM evaluation with built-in fallback mechanism
        try:
            cv_res = evaluate_cv(
                cv_text=cv_text,
                job_title=job["job_title"],
                context_snippets=cv_snippets,
            )
            proj_res = evaluate_project(
                report_text=report_text,
                case_brief_text=case_text,
                context_snippets=report_snippets,
            )
            overall_res = synthesize_overall(cv=cv_res, pr=proj_res)
            result = overall_res.dict()

            Job.update_status(job_id, "completed", result_json=json.dumps(result))
            return True, "Evaluation completed successfully"

        except Exception as e:
            try:
                Job.update_status(job_id, "failed", error_message=str(e))
            except Exception:
                pass
            return False, f"Evaluation failed: {str(e)}"

    except Exception as e:
        try:
            Job.update_status(job_id, "failed", error_message=str(e))
        except Exception:
            pass
        return False, f"Process failed: {str(e)}"
