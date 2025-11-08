"""
API Routes Module
Contains all Flask API endpoints for HR Screening System
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from datetime import datetime
import os
import threading
import queue
from werkzeug.utils import secure_filename

# Import from restructured modules
from src.models.database import Document, Job
from src.core.rag_engine import ingest_text, query, has_id, ingest_file
from src.core.ai_engine import evaluate_cv, evaluate_project, synthesize_overall
from src.workers.tasks import run_job_task

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
CASE_STUDY_PATH = os.path.join(os.getcwd(), "docs", "case_study_text.txt")

# Upload worker setup
upload_queue = queue.Queue(maxsize=100)


def _read_pdf_text(path):
    """Extract text from PDF file with fallback"""
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


def _process_uploaded_file(doc_id, path, doc_type):
    """Process uploaded file and ingest to RAG"""
    try:
        text = _read_pdf_text(path)
        sidecar = f"{path}.txt"
        with open(sidecar, "w", encoding="utf-8") as f:
            f.write(text or "")

        # Ingest ke Chroma untuk RAG
        ingest_text(
            f"doc:{doc_id}", text or "", metadata={"path": path, "doc_type": doc_type}
        )
    except Exception:
        pass


def _load_case_study_text():
    """Load case study brief text"""
    try:
        with open(CASE_STUDY_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


# ======== API Routes ========

@app.route("/")
def home():
    """Health check and API info"""
    return jsonify({
        "endpoints": {
            "evaluate": "/evaluate",
            "ingest": "/ingest",
            "result": "/result/<id>",
            "upload": "/upload"
        },
        "message": "HR Service",
        "version": "1.2.0"
    })


@app.route("/ingest", methods=["POST"])
def ingest_manual():
    """Manual text ingestion endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Body harus JSON"}), 400

        path = data.get("path")
        doc_type = data.get("doc_type", "system")
        title = data.get("title")

        if not path or not os.path.exists(path):
            return jsonify({"error": "path tidak valid"}), 400

        doc_id = ingest_file(path, doc_type=doc_type, title=title)
        return jsonify({"id": doc_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/upload", methods=["POST"])
def upload_documents():
    """Upload documents endpoint"""
    try:
        if "files" not in request.files:
            return jsonify({"error": "No files provided"}), 400

        files = request.files.getlist("files")
        if not files:
            return jsonify({"error": "No files selected"}), 400

        uploaded = []
        for file in files:
            if file.filename == "":
                continue

            # Save file
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            unique_name = f"{timestamp}_{filename}"
            save_path = os.path.join(UPLOAD_DIR, unique_name)
            file.save(save_path)

            # Determine document type
            doc_type = "cv" if "cv" in filename.lower() else "project"

            # Create database record
            doc_id = Document.create(
                doc_type=doc_type,
                filename=filename,
                path=save_path
            )
            uploaded.append({
                "id": doc_id,
                "filename": filename,
                "type": doc_type,
                "status": "uploaded"
            })

            # Process in background (optional: queue)
            try:
                _process_uploaded_file(doc_id, save_path, doc_type)
            except Exception:
                pass

        return jsonify({
            "message": "Files uploaded successfully",
            "documents": uploaded
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/evaluate", methods=["POST"])
def evaluate():
    """Start evaluation process"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON body required"}), 400

        job_title = data.get("job_title")
        documents = data.get("documents", [])

        if not job_title:
            return jsonify({"error": "job_title is required"}), 400
        if not documents:
            return jsonify({"error": "documents list is required"}), 400

        # Extract cv_id and report_id from documents list
        cv_id = None
        report_id = None

        for doc in documents:
            if doc.get('type') == 'cv':
                cv_id = doc.get('id')
            elif doc.get('type') == 'project':
                report_id = doc.get('id')

        if not cv_id or not report_id:
            return jsonify({"error": "Both CV and Project documents are required"}), 400

        # Create job with correct parameters
        job_id = Job.create(
            job_title=job_title,
            cv_id=cv_id,
            report_id=report_id
        )

        # Submit to Celery
        task = run_job_task.delay(job_id)

        return jsonify({
            "job_id": job_id,
            "status": "processing",
            "message": "Evaluation started. Use /result/{} to check progress.".format(job_id)
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/result/<int:job_id>", methods=["GET"])
def get_result(job_id):
    """Get evaluation results"""
    try:
        job = Job.get_by_id(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404

        if job.status == "completed":
            return jsonify({
                "job_id": job.id,
                "status": job.status,
                "result": json.loads(job.result_json or "{}")
            })
        elif job.status == "failed":
            return jsonify({
                "job_id": job.id,
                "status": job.status,
                "error": job.error_message
            }), 500
        else:
            return jsonify({
                "job_id": job.id,
                "status": job.status,
                "message": "Evaluation in progress..."
            })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ======== Background Processing (Legacy Support) ========

def upload_worker():
    """Background upload worker"""
    while True:
        try:
            doc_id, path, doc_type = upload_queue.get(timeout=1)
            _process_uploaded_file(doc_id, path, doc_type)
            upload_queue.task_done()
        except queue.Empty:
            continue


# Start upload worker thread
upload_thread = threading.Thread(target=upload_worker, daemon=True)
upload_thread.start()


# ======== Application Startup ========

def init_case_study():
    """Initialize case study brief in RAG"""
    try:
        if os.path.exists(CASE_STUDY_PATH) and not has_id("case_study_brief"):
            with open(CASE_STUDY_PATH, "r", encoding="utf-8") as f:
                ingest_text(
                    "case_study_brief",
                    f.read(),
                    metadata={"doc_type": "case_brief", "path": CASE_STUDY_PATH},
                )
    except Exception:
        pass


# Initialize case study on startup
init_case_study()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)