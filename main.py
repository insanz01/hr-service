from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from datetime import datetime
import os
import threading
import queue
from werkzeug.utils import secure_filename

# Try to import core modules with error handling
try:
    from src.models.database import init_db, Document, Job
    from src.core.rag_engine import ingest_text, ingest_file, has_id, query
    from src.core.ai_engine import evaluate_cv, evaluate_project, synthesize_overall

    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Some dependencies are missing: {e}")
    print("Application will run in limited mode")
    DEPENDENCIES_AVAILABLE = False
    # Create dummy functions for graceful degradation
    init_db = lambda: None
    Document = type(
        "Document", (), {"create": lambda *a: None, "get_by_id": lambda *a: None}
    )
    Job = type(
        "Job",
        (),
        {
            "create": lambda *a, **k: None,
            "get_by_id": lambda *a: None,
            "update_status": lambda *a, **k: None,
            "count": lambda: 0,
        },
    )
    ingest_text = lambda *a, **k: None
    ingest_file = lambda *a, **k: None
    has_id = lambda *a: False
    query = lambda *a, **k: []
    evaluate_cv = lambda *a, **k: type("Result", (), {"dict": lambda: {}})()
    evaluate_project = lambda *a, **k: type("Result", (), {"dict": lambda: {}})()
    synthesize_overall = lambda *a, **k: type("Result", (), {"dict": lambda: {}})()

# Simple Redis-based worker instead of Celery
try:
    from src.workers.queue_manager import queue_manager

    QUEUE_MANAGER_AVAILABLE = True
except ImportError:
    print("Warning: Queue manager not available, falling back to local threading")
    QUEUE_MANAGER_AVAILABLE = False
    queue_manager = type(
        "QueueManager",
        (),
        {"submit_job": lambda *a, **k: False, "get_result": lambda *a, **k: None},
    )()

try:
    from src.monitoring.health import comprehensive_health_check, get_service_metrics

    MONITORING_AVAILABLE = True
except ImportError:
    print("Warning: Monitoring modules not available")
    MONITORING_AVAILABLE = False
    comprehensive_health_check = lambda: {
        "status": "unknown",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    get_service_metrics = lambda: {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "error": "Monitoring not available",
    }

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
        ingest_text(
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
                "health": "/health",
                "metrics": "/metrics",
            },
        }
    )


# ========= Ingest Endpoint (manual) =========
@app.route("/ingest", methods=["POST"])
def ingest_manual():
    start_time = datetime.utcnow()
    print(f"🔄 [INGEST] Starting ingest process at {start_time}")

    try:
        if not DEPENDENCIES_AVAILABLE:
            print("❌ [INGEST] Dependencies not available")
            return jsonify(
                {"error": "Service tidak tersedia - dependencies missing"}
            ), 503

        # Check if request is form-data (file upload) or JSON
        # More robust check for both content_type and files
        if request.files and len(request.files) > 0:
            print("📁 [INGEST] Processing file upload request")
            # Handle form-data with file upload
            if "document" not in request.files:
                print("❌ [INGEST] No 'document' file found in request")
                return jsonify({"error": "Form harus berisi file document"}), 400

            file = request.files["document"]
            if file.filename == "":
                print("❌ [INGEST] Empty filename provided")
                return jsonify({"error": "Nama file tidak boleh kosong"}), 400

            # Save uploaded file temporarily
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            temp_path = os.path.join(UPLOAD_DIR, f"temp_ingest_{timestamp}_{filename}")

            print(f"💾 [INGEST] Saving uploaded file: {filename} -> {temp_path}")
            file.save(temp_path)
            file_size = os.path.getsize(temp_path)
            print(f"📊 [INGEST] File saved successfully. Size: {file_size} bytes")

            # Get form fields
            doc_type = request.form.get("doc_type", "system")
            title = request.form.get("title", filename)
            print(f"📝 [INGEST] Document metadata - Type: {doc_type}, Title: {title}")

            # Ingest the uploaded file
            print(f"🚀 [INGEST] Starting ingestion process for {temp_path}")
            doc_id = ingest_file(temp_path, doc_type=doc_type, title=title)

            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds()
            print(f"✅ [INGEST] Ingestion completed successfully. Doc ID: {doc_id}")
            print(f"⏱️ [INGEST] Total processing time: {processing_time:.2f} seconds")

            return jsonify({"id": doc_id}), 201

        else:
            print("📄 [INGEST] Processing JSON request")
            # Handle JSON (original functionality)
            try:
                data = request.get_json(force=True, silent=True)
                print(f"📝 [INGEST] JSON data received: {data}")
            except Exception as e:
                print(f"❌ [INGEST] Error parsing JSON: {e}")
                data = None

            if not data:
                print("❌ [INGEST] No valid JSON data provided")
                return jsonify(
                    {
                        "error": "Invalid request format. Expected JSON or multipart/form-data with 'document' file",
                        "supported_formats": {
                            "json": "POST with Content-Type: application/json",
                            "form_data": "POST with Content-Type: multipart/form-data and file field 'document'",
                        },
                    }
                ), 400

            path = data.get("path")
            doc_type = data.get("doc_type", "system")
            title = data.get("title")

            print(f"📁 [INGEST] Processing file path: {path}")
            print(f"📝 [INGEST] Document metadata - Type: {doc_type}, Title: {title}")

            if not path or not os.path.exists(path):
                print(f"❌ [INGEST] Invalid path: {path}")
                return jsonify({"error": "path tidak valid"}), 400

            file_size = os.path.getsize(path) if os.path.exists(path) else 0
            print(f"📊 [INGEST] File size: {file_size} bytes")

            print(f"🚀 [INGEST] Starting ingestion process for {path}")
            doc_id = ingest_file(path, doc_type=doc_type, title=title)

            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds()
            print(f"✅ [INGEST] Ingestion completed successfully. Doc ID: {doc_id}")
            print(f"⏱️ [INGEST] Total processing time: {processing_time:.2f} seconds")

            return jsonify({"id": doc_id}), 201

    except Exception as e:
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()
        print(f"❌ [INGEST] Error occurred after {processing_time:.2f} seconds: {str(e)}")
        print(f"🔍 [INGEST] Error details: {type(e).__name__}")
        return jsonify({"error": str(e)}), 500


# ========= Upload Endpoint =========
@app.route("/upload", methods=["POST"])
def upload_documents():
    start_time = datetime.utcnow()
    print(f"🔄 [UPLOAD] Starting document upload process at {start_time}")

    try:
        if not DEPENDENCIES_AVAILABLE:
            print("❌ [UPLOAD] Dependencies not available")
            return jsonify(
                {"error": "Service tidak tersedia - dependencies missing"}
            ), 503

        # Validate required files
        missing_files = []
        if "cv" not in request.files:
            missing_files.append("cv")
        if "report" not in request.files:
            missing_files.append("report")

        if missing_files:
            print(f"❌ [UPLOAD] Missing required files: {missing_files}")
            return jsonify({"error": "Form harus berisi file cv dan report"}), 400

        cv_file = request.files["cv"]
        report_file = request.files["report"]

        print(f"📁 [UPLOAD] CV file detected: {cv_file.filename}")
        print(f"📁 [UPLOAD] Report file detected: {report_file.filename}")

        if cv_file.filename == "" or report_file.filename == "":
            print("❌ [UPLOAD] Empty filename provided")
            return jsonify({"error": "Nama file tidak boleh kosong"}), 400

        # Process CV file
        print("💼 [UPLOAD] Processing CV file...")
        cv_start_time = datetime.utcnow()
        cv_name = secure_filename(cv_file.filename)
        cv_timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        cv_path = os.path.join(UPLOAD_DIR, f"cv_{cv_timestamp}_{cv_name}")

        print(f"💾 [UPLOAD] Saving CV: {cv_name} -> {cv_path}")
        cv_file.save(cv_path)
        cv_file_size = os.path.getsize(cv_path)
        print(f"📊 [UPLOAD] CV saved successfully. Size: {cv_file_size} bytes")

        print("💾 [UPLOAD] Creating CV record in database...")
        cv_id = Document.create("cv", cv_name, cv_path)
        print(f"✅ [UPLOAD] CV record created with ID: {cv_id}")

        # Fallback ke queue lokal untuk file processing
        print("📤 [UPLOAD] Adding CV to processing queue...")
        upload_queue.put({"doc_id": cv_id, "path": cv_path, "doc_type": "cv"})

        cv_processing_time = (datetime.utcnow() - cv_start_time).total_seconds()
        print(f"⏱️ [UPLOAD] CV processing completed in {cv_processing_time:.2f} seconds")

        # Process Report file
        print("📄 [UPLOAD] Processing Report file...")
        report_start_time = datetime.utcnow()
        report_name = secure_filename(report_file.filename)
        report_timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        report_path = os.path.join(UPLOAD_DIR, f"report_{report_timestamp}_{report_name}")

        print(f"💾 [UPLOAD] Saving Report: {report_name} -> {report_path}")
        report_file.save(report_path)
        report_file_size = os.path.getsize(report_path)
        print(f"📊 [UPLOAD] Report saved successfully. Size: {report_file_size} bytes")

        print("💾 [UPLOAD] Creating Report record in database...")
        report_id = Document.create("report", report_name, report_path)
        print(f"✅ [UPLOAD] Report record created with ID: {report_id}")

        # Fallback ke queue lokal untuk file processing
        print("📤 [UPLOAD] Adding Report to processing queue...")
        upload_queue.put(
            {"doc_id": report_id, "path": report_path, "doc_type": "report"}
        )

        report_processing_time = (datetime.utcnow() - report_start_time).total_seconds()
        print(f"⏱️ [UPLOAD] Report processing completed in {report_processing_time:.2f} seconds")

        # Calculate total processing time
        total_processing_time = (datetime.utcnow() - start_time).total_seconds()
        print(f"📊 [UPLOAD] File sizes - CV: {cv_file_size} bytes, Report: {report_file_size} bytes")
        print(f"⏱️ [UPLOAD] Total upload processing time: {total_processing_time:.2f} seconds")

        # Return document IDs as per specification
        response_data = {"cv_id": cv_id, "report_id": report_id}
        print(f"✅ [UPLOAD] Upload completed successfully: {response_data}")
        return jsonify(response_data), 201

    except Exception as e:
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()
        print(f"❌ [UPLOAD] Error occurred after {processing_time:.2f} seconds: {str(e)}")
        print(f"🔍 [UPLOAD] Error details: {type(e).__name__}")
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

        # Convert sqlite3.Row to dict to avoid .get() method issues
        job_dict = dict(job)
        cv_row = Document.get_by_id(job_dict["cv_id"]) if job_dict["cv_id"] else None
        report_row = Document.get_by_id(job_dict["report_id"]) if job_dict["report_id"] else None

        # Convert Document rows to dict to avoid .get() method issues
        cv_dict = dict(cv_row) if cv_row else None
        report_dict = dict(report_row) if report_row else None

        cv_sidecar = f"{cv_dict['path']}.txt" if cv_dict else None
        report_sidecar = f"{report_dict['path']}.txt" if report_dict else None

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
            d["document"] for d in query(job["job_title"] or "", n_results=3)
        ]
        report_snippets = [
            d["document"]
            for d in query(
                "project scoring prompt chaining RAG error handling", n_results=3
            )
        ]

        # Use LLM module with built-in fallback mechanism
        cv_res = evaluate_cv(cv_text, job["job_title"] or "", cv_snippets)
        pr_res = evaluate_project(report_text, case_brief_text, report_snippets)
        overall = synthesize_overall(cv_res, pr_res)
        result = overall.dict()

        Job.update_status(job_id, "completed", result_json=json.dumps(result))
    except Exception as e:
        Job.update_status(job_id, "failed", error_message=str(e))


# ========= Evaluate Endpoint =========
@app.route("/evaluate", methods=["POST"])
def evaluate():
    start_time = datetime.utcnow()
    print(f"🔄 [EVALUATE] Starting evaluation process at {start_time}")

    try:
        if not DEPENDENCIES_AVAILABLE:
            print("❌ [EVALUATE] Dependencies not available")
            return jsonify(
                {"error": "Service tidak tersedia - dependencies missing"}
            ), 503

        data = request.get_json()
        if not data:
            print("❌ [EVALUATE] No JSON data provided in request body")
            return jsonify({"error": "Body harus JSON"}), 400

        job_title = data.get("job_title")
        cv_id = data.get("cv_id")
        report_id = data.get("report_id")

        print(f"📝 [EVALUATE] Evaluation request received:")
        print(f"   - Job Title: {job_title}")
        print(f"   - CV ID: {cv_id}")
        print(f"   - Report ID: {report_id}")

        if not job_title or not cv_id or not report_id:
            missing_fields = []
            if not job_title:
                missing_fields.append("job_title")
            if not cv_id:
                missing_fields.append("cv_id")
            if not report_id:
                missing_fields.append("report_id")

            print(f"❌ [EVALUATE] Missing required fields: {missing_fields}")
            return jsonify(
                {"error": "job_title, cv_id, dan report_id wajib diisi"}
            ), 400

        # Validate CV and Report documents exist
        print(f"🔍 [EVALUATE] Validating document existence...")
        cv_doc = Document.get_by_id(cv_id)
        report_doc = Document.get_by_id(report_id)

        if not cv_doc:
            print(f"❌ [EVALUATE] CV document with ID {cv_id} not found")
            return jsonify({"error": f"CV document with ID {cv_id} not found"}), 404

        if not report_doc:
            print(f"❌ [EVALUATE] Report document with ID {report_id} not found")
            return jsonify({"error": f"Report document with ID {report_id} not found"}), 404

        # Convert Document rows to dict to avoid .get() method issues
        cv_dict = dict(cv_doc)
        report_dict = dict(report_doc)

        print(f"✅ [EVALUATE] Documents validated:")
        print(f"   - CV: {cv_dict['filename']} ({cv_dict['path']})")
        print(f"   - Report: {report_dict['filename']} ({report_dict['path']})")

        print("💾 [EVALUATE] Creating job record in database...")
        job_id = Job.create(job_title, cv_id, report_id)
        print(f"✅ [EVALUATE] Job created with ID: {job_id}")

        # Jalankan evaluasi via Simple Redis Worker
        try:
            print("🚀 [EVALUATE] Attempting to submit job to Redis queue...")
            if QUEUE_MANAGER_AVAILABLE:
                print("📤 [EVALUATE] Queue manager is available, submitting to Redis...")
                success = queue_manager.submit_job(job_id, cv_id, report_id, job_title)
                if success:
                    print("✅ [EVALUATE] Job successfully submitted to Redis queue")
                    total_processing_time = (datetime.utcnow() - start_time).total_seconds()
                    print(f"⏱️ [EVALUATE] Total submission time: {total_processing_time:.2f} seconds")
                    return jsonify({"id": str(job_id), "status": "queued"}), 202
                else:
                    print("⚠️ [EVALUATE] Failed to submit to Redis queue, falling back to local thread")
            else:
                print("⚠️ [EVALUATE] Queue manager not available, using local thread fallback")

            # Fallback ke thread lokal bila gagal atau queue manager tidak tersedia
            print("🧵 [EVALUATE] Starting local processing thread...")
            t = threading.Thread(target=_run_job, args=(job_id,), daemon=True)
            t.start()
            print("✅ [EVALUATE] Local processing thread started successfully")

            total_processing_time = (datetime.utcnow() - start_time).total_seconds()
            print(f"⏱️ [EVALUATE] Total submission time (fallback): {total_processing_time:.2f} seconds")
            return jsonify({"id": str(job_id), "status": "queued"}), 202

        except Exception as e:
            print(f"⚠️ [EVALUATE] Error submitting to queue manager: {e}")
            print("🧵 [EVALUATE] Starting local processing thread as final fallback...")

            # Fallback ke thread lokal
            t = threading.Thread(target=_run_job, args=(job_id,), daemon=True)
            t.start()
            print("✅ [EVALUATE] Local processing thread started successfully")

            total_processing_time = (datetime.utcnow() - start_time).total_seconds()
            print(f"⏱️ [EVALUATE] Total submission time (final fallback): {total_processing_time:.2f} seconds")
            return jsonify({"id": str(job_id), "status": "queued"}), 202

    except Exception as e:
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()
        print(f"❌ [EVALUATE] Error occurred after {processing_time:.2f} seconds: {str(e)}")
        print(f"🔍 [EVALUATE] Error details: {type(e).__name__}")
        return jsonify({"error": str(e)}), 500


# ========= Health Check Endpoint =========
@app.route("/health", methods=["GET"])
def health_check():
    """Comprehensive health check endpoint"""
    try:
        if MONITORING_AVAILABLE:
            health_data = comprehensive_health_check()
            status_code = 200 if health_data["status"] == "healthy" else 503
            return jsonify(health_data), status_code
        else:
            return jsonify(
                {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "status": "unknown",
                    "message": "Health monitoring not available",
                    "dependencies_available": DEPENDENCIES_AVAILABLE,
                    "queue_manager_available": QUEUE_MANAGER_AVAILABLE,
                }
            ), 503
    except Exception as e:
        return jsonify(
            {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "status": "unhealthy",
                "error": str(e),
            }
        ), 503


# ========= Metrics Endpoint =========
@app.route("/metrics", methods=["GET"])
def metrics():
    """Service metrics endpoint"""
    try:
        if MONITORING_AVAILABLE:
            metrics_data = get_service_metrics()
            return jsonify(metrics_data), 200
        else:
            return jsonify(
                {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "message": "Metrics monitoring not available",
                    "dependencies_available": DEPENDENCIES_AVAILABLE,
                    "queue_manager_available": QUEUE_MANAGER_AVAILABLE,
                }
            ), 503
    except Exception as e:
        return jsonify(
            {"timestamp": datetime.utcnow().isoformat() + "Z", "error": str(e)}
        ), 500


# ========= Result Endpoint =========
@app.route("/result/<int:job_id>", methods=["GET"])
def get_result(job_id):
    start_time = datetime.utcnow()
    print(f"🔍 [RESULT] Starting result retrieval for job {job_id} at {start_time}")

    try:
        print(f"📋 [RESULT] Fetching job record from database...")
        job = Job.get_by_id(job_id)
        if not job:
            print(f"❌ [RESULT] Job {job_id} not found in database")
            return jsonify({"error": "Job tidak ditemukan"}), 404

        # Convert sqlite3.Row to dict to avoid .get() method issues
        job_dict = dict(job)
        status = job_dict["status"]
        print(f"📊 [RESULT] Job {job_id} status: {status}")
        print(f"📝 [RESULT] Job details: Title='{job_dict.get('job_title', 'N/A')}', CV_ID={job_dict.get('cv_id')}, Report_ID={job_dict.get('report_id')}")

        # Check if job is still queued/processing
        if status in ["queued", "processing"]:
            print(f"⏳ [RESULT] Job {job_id} is still {status}, checking Redis for results...")
            # Try to get result from Simple Redis Worker with proper timeout
            redis_start_time = datetime.utcnow()
            result = queue_manager.get_result(job_id, timeout=5)
            redis_query_time = (datetime.utcnow() - redis_start_time).total_seconds()

            print(f"🔎 [RESULT] Redis query completed in {redis_query_time:.2f} seconds")

            if result:
                print(f"✅ [RESULT] Result found in Redis for job {job_id}")

                # Result found in Redis, update job status
                if "error" in result:
                    print(f"❌ [RESULT] Error found in result for job {job_id}: {result['error']}")
                    Job.update_status(job_id, "failed", error_message=result["error"])
                    total_processing_time = (datetime.utcnow() - start_time).total_seconds()
                    print(f"⏱️ [RESULT] Total result retrieval time: {total_processing_time:.2f} seconds")

                    return jsonify(
                        {
                            "id": str(job_id),
                            "status": "failed",
                            "error": result["error"],
                        }
                    ), 500
                else:
                    print(f"🎉 [RESULT] Success result found for job {job_id}, updating database...")
                    # Success result found, update job status and result
                    Job.update_status(
                        job_id, "completed", result_json=json.dumps(result)
                    )

                    # Transform result to match specification format
                    transform_start_time = datetime.utcnow()
                    transformed_result = _transform_result_to_spec_format(result)
                    transform_time = (datetime.utcnow() - transform_start_time).total_seconds()
                    print(f"🔄 [RESULT] Result transformation completed in {transform_time:.2f} seconds")

                    total_processing_time = (datetime.utcnow() - start_time).total_seconds()
                    print(f"⏱️ [RESULT] Total result retrieval time: {total_processing_time:.2f} seconds")

                    return jsonify(
                        {
                            "id": str(job_id),
                            "status": "completed",
                            "result": transformed_result,
                        }
                    )
            else:
                print(f"⏳ [RESULT] No result found in Redis for job {job_id}, still processing...")
                total_processing_time = (datetime.utcnow() - start_time).total_seconds()
                print(f"⏱️ [RESULT] Total result retrieval time: {total_processing_time:.2f} seconds")
                return jsonify({"id": str(job_id), "status": status})

        elif status == "completed":
            print(f"✅ [RESULT] Job {job_id} is completed, retrieving result from database...")

            # Get result from database first
            if job_dict["result_json"]:
                print(f"💾 [RESULT] Found result in database for job {job_id}")
                db_start_time = datetime.utcnow()
                result = json.loads(job_dict["result_json"])
                db_query_time = (datetime.utcnow() - db_start_time).total_seconds()
                print(f"🔎 [RESULT] Database query completed in {db_query_time:.2f} seconds")
            else:
                print(f"⚠️ [RESULT] No result in database for job {job_id}, checking Redis...")
                # If result_json is empty, try to get from Redis (for SimpleWorker jobs)
                redis_start_time = datetime.utcnow()
                result = queue_manager.get_result(job_id, timeout=5)
                redis_query_time = (datetime.utcnow() - redis_start_time).total_seconds()
                print(f"🔎 [RESULT] Redis fallback query completed in {redis_query_time:.2f} seconds")

                if result:
                    print(f"📝 [RESULT] Found result in Redis, updating database...")
                    # Update database with result from Redis
                    Job.update_status(
                        job_id, "completed", result_json=json.dumps(result)
                    )
                else:
                    print(f"⚠️ [RESULT] No result found in Redis either, using empty result")

            # Transform result to match specification format
            print(f"🔄 [RESULT] Transforming result to specification format...")
            transform_start_time = datetime.utcnow()
            transformed_result = _transform_result_to_spec_format(result or {})
            transform_time = (datetime.utcnow() - transform_start_time).total_seconds()
            print(f"🔄 [RESULT] Result transformation completed in {transform_time:.2f} seconds")

            total_processing_time = (datetime.utcnow() - start_time).total_seconds()
            print(f"⏱️ [RESULT] Total result retrieval time: {total_processing_time:.2f} seconds")

            return jsonify(
                {"id": str(job_id), "status": status, "result": transformed_result}
            )
        else:
            # Failed job
            error_message = job_dict["error_message"] or "Unknown error"
            print(f"❌ [RESULT] Job {job_id} failed with error: {error_message}")
            total_processing_time = (datetime.utcnow() - start_time).total_seconds()
            print(f"⏱️ [RESULT] Total result retrieval time: {total_processing_time:.2f} seconds")

            return jsonify(
                {
                    "id": str(job_id),
                    "status": status,
                    "error": error_message,
                }
            ), 500

    except Exception as e:
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()
        print(f"❌ [RESULT] Error occurred after {processing_time:.2f} seconds: {str(e)}")
        print(f"🔍 [RESULT] Error details: {type(e).__name__}")
        return jsonify({"error": str(e)}), 500


def _transform_result_to_spec_format(result):
    """Transform internal result format to specification format"""
    try:
        # Extract data from the nested result structure from SimpleWorker
        cv_result = result.get("cv_result", {})
        project_result = result.get("project_result", {})
        overall_result = result.get("overall_result", {})

        # Extract from nested structure (SimpleWorker format)
        cv_match_rate = cv_result.get("match_rate", 0.0)
        cv_feedback = cv_result.get("feedback", "")
        project_score = project_result.get("score", 0.0)
        project_feedback = project_result.get("feedback", "")
        overall_summary = overall_result.get("summary", "")

        return {
            "cv_match_rate": cv_match_rate,
            "cv_feedback": cv_feedback,
            "project_score": project_score,
            "project_feedback": project_feedback,
            "overall_summary": overall_summary,
        }
    except Exception as e:
        # Log the error for debugging
        print(f"Error transforming result: {e}")
        # Fallback if transformation fails
        return {
            "cv_match_rate": 0.0,
            "cv_feedback": "Evaluation completed with limited data",
            "project_score": 0.0,
            "project_feedback": "Evaluation completed with limited data",
            "overall_summary": "Evaluation completed",
        }


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
        if os.path.exists(CASE_STUDY_PATH) and not has_id("case_study_brief"):
            with open(CASE_STUDY_PATH, "r", encoding="utf-8") as f:
                ingest_text(
                    "case_study_brief",
                    f.read(),
                    metadata={"doc_type": "case_brief", "path": CASE_STUDY_PATH},
                )
    except Exception:
        pass

    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000, use_reloader=False)
