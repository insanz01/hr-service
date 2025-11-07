import os
import json
from typing import Optional

# Try to import the best PDF libraries in order of preference
try:
    import fitz  # PyMuPDF - best choice
    _PDF_READER = 'pymupdf'
except ImportError:
    try:
        import pdfplumber
        _PDF_READER = 'pdfplumber'
    except ImportError:
        try:
            from pypdf import PdfReader
            _PDF_READER = 'pypdf'
        except ImportError:
            try:
                from PyPDF2 import PdfReader  # Fallback
                _PDF_READER = 'pypdf2'
            except ImportError:
                _PDF_READER = None

import rag
import llm
from models import Document, Job


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(BASE_DIR, "docs")
CASE_STUDY_PATH = os.path.join(DOCS_DIR, "case_study_text.txt")


def _read_pdf_text(pdf_path: str) -> str:
    """Extract text from PDF using the best available library.

    Tries libraries in order: PyMuPDF > pdfplumber > pypdf > PyPDF2
    Falls back to reading as plain text if PDF reading fails.
    """
    if not os.path.exists(pdf_path):
        return ""

    # Try PDF readers in order of preference
    if _PDF_READER == 'pymupdf':
        return _read_with_pymupdf(pdf_path)
    elif _PDF_READER == 'pdfplumber':
        return _read_with_pdfplumber(pdf_path)
    elif _PDF_READER in ('pypdf', 'pypdf2'):
        return _read_with_pypdf(pdf_path)
    else:
        # Fallback: try reading as plain text
        return _read_as_text(pdf_path)

def _read_with_pymupdf(pdf_path: str) -> str:
    """Extract text using PyMuPDF (fastest and most accurate)."""
    try:
        doc = fitz.open(pdf_path)
        text_parts = []
        for page in doc:
            text = page.get_text()
            if text.strip():
                text_parts.append(text)
        doc.close()
        return "\n".join(text_parts).strip()
    except Exception as e:
        print(f"PyMuPDF failed for {pdf_path}: {e}")
        return _read_as_text(pdf_path)

def _read_with_pdfplumber(pdf_path: str) -> str:
    """Extract text using pdfplumber (great for tables and forms)."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text_parts = []
            for page in pdf.pages:
                text = page.extract_text()
                if text and text.strip():
                    text_parts.append(text)
            return "\n".join(text_parts).strip()
    except Exception as e:
        print(f"pdfplumber failed for {pdf_path}: {e}")
        return _read_as_text(pdf_path)

def _read_with_pypdf(pdf_path: str) -> str:
    """Extract text using pypdf/PyPDF2."""
    try:
        reader = PdfReader(pdf_path)
        text_parts = []
        for page in reader.pages:
            text = page.extract_text() or ""
            if text.strip():
                text_parts.append(text)
        return "\n".join(text_parts).strip()
    except Exception as e:
        print(f"pypdf/PyPDF2 failed for {pdf_path}: {e}")
        return _read_as_text(pdf_path)

def _read_as_text(pdf_path: str) -> str:
    """Fallback: read file as plain text."""
    try:
        with open(pdf_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            # Clean up any PDF-like artifacts
            lines = content.split('\n')
            clean_lines = []
            for line in lines:
                # Skip PDF headers and artifacts
                if any(marker in line.lower() for marker in ['%%eof', 'pdf-', 'obj', 'endobj', 'stream', 'endstream']):
                    continue
                if line.strip() and len(line.strip()) > 1:
                    clean_lines.append(line.strip())
            return '\n'.join(clean_lines)
    except Exception as e:
        print(f"Failed to read {pdf_path} as text: {e}")
        return ""


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
    """Run end-to-end evaluation using LLM + RAG with built-in fallback mechanism."""
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

    # LLM evaluation with built-in fallback mechanism
    try:
        cv_res = llm.evaluate_cv(cv_text=cv_text, case_brief=case_text, context=cv_snippets)
        proj_res = llm.evaluate_project(report_text=report_text, case_brief=case_text, context=report_snippets)
        overall_res = llm.synthesize_overall(cv=cv_res, project=proj_res, case_brief=case_text)
        result = overall_res.dict()

        Job.update_status(job_id, 'completed', result_json=json.dumps(result))
    except Exception as e:
        try:
            Job.update_status(job_id, 'failed', error_message=str(e))
        except Exception:
            pass