import os
import json
from typing import Optional

from PyPDF2 import PdfReader

import rag
import llm
from models import Document, Job


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(BASE_DIR, "docs")
CASE_STUDY_PATH = os.path.join(DOCS_DIR, "case_study_text.txt")


def _read_pdf_text(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    parts = []
    for page in reader.pages:
        text = page.extract_text() or ""
        parts.append(text)
    return "\n".join(parts).strip()


def process_uploaded_file(doc_id: int, path: str, doc_type: str) -> None:
    """Extract text from uploaded file and ingest into ChromaDB.

    Creates a sidecar .txt file next to the uploaded file for auditability.
    """
    if not os.path.exists(path):
        return

    text: Optional[str] = None
    _, ext = os.path.splitext(path.lower())
    try:
        if ext == ".pdf":
            text = _read_pdf_text(path)
        elif ext in (".txt", ".md"):
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        else:
            # Unsupported types: store minimal marker
            text = f"Unsupported file type {ext} for {path}"
    except Exception as e:
        text = f"Error reading file {path}: {e}"

    if not text:
        text = "(no text extracted)"

    # Write sidecar .txt
    sidecar_path = os.path.splitext(path)[0] + ".txt"
    try:
        with open(sidecar_path, "w", encoding="utf-8") as f:
            f.write(text)
    except Exception:
        pass

    # Ingest into RAG store menggunakan API rag.py yang tersedia
    try:
        rag.ingest_text(f"doc:{doc_id}", text, metadata={"path": path, "doc_type": doc_type})
    except Exception:
        # best-effort; jangan hentikan worker jika gagal ingest
        pass


def run_job(job_id: int) -> None:
    """Run end-to-end evaluation using LLM + RAG.

    Falls back to mock evaluation if LLM not available.
    """
    # Sinkron dengan main.py: update status dan ambil job
    try:
        Job.update_status(job_id, 'processing')
    except Exception:
        pass

    job = Job.get_by_id(job_id)
    if not job:
        try:
            Job.update_status(job_id, 'failed', error_message='Job tidak ditemukan')
        except Exception:
            pass
        return

    # Ambil dokumen dari DB
    cv_row = Document.get_by_id(job['cv_id']) if job['cv_id'] else None
    report_row = Document.get_by_id(job['report_id']) if job['report_id'] else None

    # Baca teks dari sidecar jika tersedia, fallback ke ekstraksi langsung
    cv_sidecar = f"{cv_row['path']}.txt" if cv_row else None
    report_sidecar = f"{report_row['path']}.txt" if report_row else None

    if cv_sidecar and os.path.exists(cv_sidecar):
        try:
            with open(cv_sidecar, 'r', encoding='utf-8') as f:
                cv_text = f.read()
        except Exception:
            cv_text = ''
    else:
        cv_text = _read_pdf_text(cv_row['path']) if cv_row else ''

    if report_sidecar and os.path.exists(report_sidecar):
        try:
            with open(report_sidecar, 'r', encoding='utf-8') as f:
                report_text = f.read()
        except Exception:
            report_text = ''
    else:
        report_text = _read_pdf_text(report_row['path']) if report_row else ''

    # Ensure case study brief is available for context
    case_text = ""
    try:
        with open(CASE_STUDY_PATH, "r", encoding="utf-8") as f:
            case_text = f.read()
    except FileNotFoundError:
        case_text = ""

    # RAG retrieval: gunakan API rag.query yang tersedia
    try:
        cv_snippets = [d['document'] for d in rag.query(job['job_title'] or '', n_results=3)]
    except Exception:
        cv_snippets = []
    try:
        report_snippets = [d['document'] for d in rag.query('project scoring prompt chaining RAG error handling', n_results=3)]
    except Exception:
        report_snippets = []

    # LLM evaluation
    try:
        if llm.available():
            cv_res = llm.evaluate_cv(cv_text=cv_text, case_brief=case_text, context=cv_snippets)
            proj_res = llm.evaluate_project(report_text=report_text, case_brief=case_text, context=report_snippets)
            overall_res = llm.synthesize_overall(cv=cv_res, project=proj_res, case_brief=case_text)
            result = overall_res.dict()
        else:
            # Fallback mock selaras dengan main.py
            cv_match_rate = min(1.0, max(0.0, len(cv_text) / 5000.0))
            cv_feedback = f"CV dievaluasi untuk '{job['job_title'] or ''}'. Panjang teks {len(cv_text)} karakter."
            project_score = min(5.0, max(1.0, len(report_text) / 1000.0))
            project_feedback = f"Project report dianalisis, panjang teks {len(report_text)} karakter."
            overall_summary = "Kandidat menunjukkan kecocokan sebagian, disarankan menambah pengalaman RAG dan error handling."
            result = {
                'cv_match_rate': round(cv_match_rate, 2),
                'cv_feedback': cv_feedback,
                'project_score': round(project_score, 1),
                'project_feedback': project_feedback,
                'overall_summary': overall_summary
            }

        Job.update_status(job_id, 'completed', result_json=json.dumps(result))
    except Exception as e:
        try:
            Job.update_status(job_id, 'failed', error_message=str(e))
        except Exception:
            pass