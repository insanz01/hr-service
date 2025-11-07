from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from datetime import datetime
import os
import threading
import queue
from werkzeug.utils import secure_filename
from database import init_db
from models import Document, Job
import rag
import llm
from tasks import process_uploaded_file_task, run_job_task

# Gunakan path relatif terhadap project root
UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
# Dokumen Case Study Brief (ground truth untuk project report)
CASE_STUDY_PATH = os.path.join(os.getcwd(), "docs", "case_study_text.txt")

app = Flask(__name__)
CORS(app)

# ========== Upload worker setup ==========
upload_queue = queue.Queue(maxsize=100)


def _read_pdf_text(path):
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
    try:
        text = _read_pdf_text(path)
        sidecar = f"{path}.txt"
        with open(sidecar, "w", encoding="utf-8") as f:
            f.write(text or "")
        # Ingest ke Chroma untuk RAG
        rag.ingest_text(
            f"doc:{doc_id}", text or "", metadata={"path": path, "doc_type": doc_type}
        )
    except Exception:
        pass


def _upload_worker():
    while True:
        task = upload_queue.get()
        try:
            _process_uploaded_file(task["doc_id"], task["path"], task["doc_type"])
        finally:
            upload_queue.task_done()


# Mulai worker thread
_upload_thread = threading.Thread(target=_upload_worker, daemon=True)
_upload_thread.start()


@app.route("/")
def home():
    return jsonify(
        {
            "message": "HR Service",
            "version": "1.2.0",
            "endpoints": {
                "upload": "/upload",
                "evaluate": "/evaluate",
                "result": "/result/<id>",
                "ingest": "/ingest",
            },
        }
    )


# ========= Ingest Endpoint (manual) =========
@app.route("/ingest", methods=["POST"])
def ingest_manual():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Body harus JSON"}), 400
        path = data.get("path")
        doc_type = data.get("doc_type", "system")
        title = data.get("title")
        if not path or not os.path.exists(path):
            return jsonify({"error": "path tidak valid"}), 400
        doc_id = rag.ingest_file(path, doc_type=doc_type, title=title)
        return jsonify({"id": doc_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ========= Upload Endpoint =========
@app.route("/upload", methods=["POST"])
def upload_documents():
    try:
        if "cv" not in request.files or "report" not in request.files:
            return jsonify({"error": "Form harus berisi file cv dan report"}), 400

        cv_file = request.files["cv"]
        report_file = request.files["report"]

        if cv_file.filename == "" or report_file.filename == "":
            return jsonify({"error": "Nama file tidak boleh kosong"}), 400

        cv_name = secure_filename(cv_file.filename)
        cv_path = os.path.join(
            UPLOAD_DIR, f"cv_{datetime.now().strftime('%Y%m%d%H%M%S')}_{cv_name}"
        )
        cv_file.save(cv_path)
        cv_id = Document.create("cv", cv_name, cv_path)
        try:
            # Kirim ke Celery worker
            process_uploaded_file_task.delay(cv_id, cv_path, "cv")
        except Exception:
            # Fallback ke queue lokal jika broker tidak tersedia
            upload_queue.put({"doc_id": cv_id, "path": cv_path, "doc_type": "cv"})

        report_name = secure_filename(report_file.filename)
        report_path = os.path.join(
            UPLOAD_DIR,
            f"report_{datetime.now().strftime('%Y%m%d%H%M%S')}_{report_name}",
        )
        report_file.save(report_path)
        report_id = Document.create("report", report_name, report_path)
        try:
            process_uploaded_file_task.delay(report_id, report_path, "report")
        except Exception:
            upload_queue.put(
                {"doc_id": report_id, "path": report_path, "doc_type": "report"}
            )

        return jsonify({"cv_id": cv_id, "report_id": report_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ========= Simple Evaluation Pipeline (Background) =========


def _load_case_study_text() -> str:
    try:
        with open(CASE_STUDY_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def _run_job(job_id):
    try:
        Job.update_status(job_id, "processing")
        job = Job.get_by_id(job_id)
        if not job:
            Job.update_status(job_id, "failed", error_message="Job tidak ditemukan")
            return

        cv_row = Document.get_by_id(job["cv_id"]) if job["cv_id"] else None
        report_row = Document.get_by_id(job["report_id"]) if job["report_id"] else None

        cv_sidecar = f"{cv_row['path']}.txt" if cv_row else None
        report_sidecar = f"{report_row['path']}.txt" if report_row else None

        if cv_sidecar and os.path.exists(cv_sidecar):
            with open(cv_sidecar, "r", encoding="utf-8") as f:
                cv_text = f.read()
        else:
            cv_text = _read_pdf_text(cv_row["path"]) if cv_row else ""

        if report_sidecar and os.path.exists(report_sidecar):
            with open(report_sidecar, "r", encoding="utf-8") as f:
                report_text = f.read()
        else:
            report_text = _read_pdf_text(report_row["path"]) if report_row else ""

        case_brief_text = _load_case_study_text()

        # RAG retrieval (opsional): ambil snippet terkait untuk prompt LLM
        cv_snippets = [
            d["document"] for d in rag.query(job["job_title"] or "", n_results=3)
        ]
        report_snippets = [
            d["document"]
            for d in rag.query(
                "project scoring prompt chaining RAG error handling", n_results=3
            )
        ]

        # Use LLM module with built-in fallback mechanism
        cv_res = llm.evaluate_cv(cv_text, job["job_title"] or "", cv_snippets)
        pr_res = llm.evaluate_project(report_text, case_brief_text, report_snippets)
        overall = llm.synthesize_overall(cv_res, pr_res)
        result = overall.dict()

        Job.update_status(job_id, "completed", result_json=json.dumps(result))
    except Exception as e:
        Job.update_status(job_id, "failed", error_message=str(e))


# ========= Evaluate Endpoint =========
@app.route("/evaluate", methods=["POST"])
def evaluate():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Body harus JSON"}), 400

        job_title = data.get("job_title")
        cv_id = data.get("cv_id")
        report_id = data.get("report_id")

        if not job_title or not cv_id or not report_id:
            return jsonify(
                {"error": "job_title, cv_id, dan report_id wajib diisi"}
            ), 400

        job_id = Job.create(job_title, cv_id, report_id)
        # Jalankan evaluasi via Celery; fallback ke thread lokal bila gagal
        try:
            run_job_task.delay(job_id)
        except Exception:
            t = threading.Thread(target=_run_job, args=(job_id,), daemon=True)
            t.start()

        return jsonify({"id": job_id, "status": "queued"}), 202
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ========= Result Endpoint =========
@app.route("/result/<int:job_id>", methods=["GET"])
def get_result(job_id):
    try:
        job = Job.get_by_id(job_id)
        if not job:
            return jsonify({"error": "Job tidak ditemukan"}), 404

        status = job["status"]
        if status in ["queued", "processing"]:
            return jsonify({"id": job_id, "status": status})
        elif status == "completed":
            result = json.loads(job["result_json"]) if job["result_json"] else {}
            return jsonify({"id": job_id, "status": status, "result": result})
        else:
            return jsonify(
                {
                    "id": job_id,
                    "status": status,
                    "error": job["error_message"] or "Unknown error",
                }
            ), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ========= Existing error handlers =========
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint tidak ditemukan"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Terjadi kesalahan internal"}), 500


if __name__ == "__main__":
    # Ingest Case Study Brief secara otomatis ke Chroma saat startup
    try:
        if os.path.exists(CASE_STUDY_PATH) and not rag.has_id("case_study_brief"):
            with open(CASE_STUDY_PATH, "r", encoding="utf-8") as f:
                rag.ingest_text(
                    "case_study_brief",
                    f.read(),
                    metadata={"doc_type": "case_brief", "path": CASE_STUDY_PATH},
                )
    except Exception:
        pass

    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000, use_reloader=False)
