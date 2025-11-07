# HR Screening System - Project Structure Documentation

## 📁 Project Overview

HR Screening System adalah aplikasi berbasis Flask dengan Celery untuk background processing yang menggunakan RAG (Retrieval-Augmented Generation) dan AI untuk mengevaluasi CV dan project report kandidat Backend Engineer dengan AI/ML capabilities.

## 🏗️ Project Architecture

```
hr-service/
├── 📁 Core Application Files
├── 📁 Configuration & Deployment
├── 📁 Documentation
├── 📁 Sample Data
├── 📁 Runtime Data
└── 📁 Test Files
```

---

## 📂 Detailed Structure

### 🐍 **Core Application Files** (`/`)

| File | Fungsi | Deskripsi |
|------|--------|-----------|
| `main.py` | 🌐 Flask API | Main application dengan REST endpoints |
| `workers.py` | ⚙️ Background Processing | Celery workers untuk evaluation tasks |
| `tasks.py` | 📋 Task Definitions | Definisi Celery tasks |
| `models.py` | 🗄️ Data Models | SQLAlchemy models untuk database |
| `database.py` | 🗄️ Database Setup | Database initialization dan connection |
| `rag.py` | 🧠 RAG System | ChromaDB integration untuk vector search |
| `llm.py` | 🤖 AI Integration | Google Gemini API dengan fallback |
| `celery_app.py` | ⚙️ Celery Config | Celery application configuration |
| `start_worker.py` | 🚀 Worker Launcher | Script untuk memulai Celery workers |

---

### 🐳 **Configuration & Deployment** (`/`)

| File | Fungsi | Deskripsi |
|------|--------|-----------|
| `Dockerfile` | 🐳 Production Build | Multi-stage Docker build untuk production |
| `Dockerfile.dev` | 🐳 Development Build | Dockerfile untuk development dengan hot-reload |
| `docker-compose.yml` | 🐳 Orchestration | Multi-service container orchestration |
| `.dockerignore` | 🐳 Build Optimization | Exclude files dari Docker build context |
| `docker-start.sh` | 🚀 Docker Manager | Script untuk mengelola Docker services |
| `requirements.txt` | 📦 Dependencies | Python dependencies dengan version pinning |
| `.env.example` | 🔧 Environment Template | Template untuk environment variables |

---

### 📚 **Documentation** (`/docs/`)

| File | Fungsi | Deskripsi |
|------|--------|-----------|
| `case_study_text.txt` | 📋 Job Requirements | Case study brief untuk Backend Engineer + AI role |
| `case study brief.md` | 📋 Job Requirements (Markdown) | Versi markdown dari case study |
| `extraction case study.md` | 📋 Extraction Guidelines | Guidelines untuk text extraction |
| `Case Study Brief - Backend.pdf` | 📋 Job Requirements (PDF) | Versi PDF dari case study |

---

### 📊 **Documentation Files** (`/`)

| File | Fungsi | Deskripsi |
|------|--------|-----------|
| `README.md` | 📖 Main Documentation | Project overview dan setup instructions |
| `README_DOCKER.md` | 🐳 Docker Guide | Docker-specific setup and deployment |
| `README_RUN.md` | 🚀 Run Instructions | Step-by-step running instructions |
| `API_DOCUMENTATION.md` | 📡 API Reference | Complete API documentation dengan examples |
| `DOCKER_OPTIMIZATION.md` | ⚡ Performance Guide | Docker optimization strategies |
| `setup_ai.md` | 🤖 AI Setup | AI/ML configuration guide |

---

### 📁 **Sample Data** (`/samples/`)

#### **Raw Markdown Files** (`/samples/raw/`)
```
raw/
├── cv_1_john_doe.md          # CV Backend Engineer dengan AI experience
├── cv_2_sarah_wilson.md       # CV Senior Backend Developer
├── cv_3_mike_chen.md          # CV Full Stack dengan fokus Backend
├── project_report_1_excellent.md  # Project AI/ML implementation (Excellent)
├── project_report_2_good.md       # Backend system design (Good)
└── project_report_3_basic.md      # Simple web application (Basic)
```

#### **PDF Files** (`/samples/pdfs/`)
```
pdfs/
├── cv_1_john_doe.pdf          # CV 1 - PDF version
├── cv_2_sarah_wilson.pdf       # CV 2 - PDF version
├── cv_3_mike_chen.pdf          # CV 3 - PDF version
├── project_report_1_excellent.pdf  # Project 1 - PDF version
├── project_report_2_good.pdf       # Project 2 - PDF version
└── project_report_3_basic.pdf      # Project 3 - PDF version
```

#### **HTML Files** (`/samples/html/`)
```
html/
├── cv_1_john_doe.html         # CV 1 - HTML version
├── cv_2_sarah_wilson.html      # CV 2 - HTML version
├── cv_3_mike_chen.html         # CV 3 - HTML version
├── project_report_1_excellent.html  # Project 1 - HTML version
├── project_report_2_good.html       # Project 2 - HTML version
└── project_report_3_basic.html      # Project 3 - HTML version
```

---

### 📂 **Runtime Data** (`/uploads/`)

```
uploads/
├── 📁 chroma/                 # ChromaDB vector database storage
│   └── {uuid}/               # ChromaDB data files
│       ├── data_level0.bin   # Vector embeddings
│       ├── header.bin        # Database metadata
│       ├── length.bin        # Data length info
│       └── link_lists.bin    # Index structures
├── 📄 Uploaded Files         # User uploaded CVs and projects
│   ├── cv_*.pdf              # Uploaded CV files
│   ├── cv_*.txt              # Extracted text from CVs
│   ├── report_*.pdf          # Uploaded project files
│   └── report_*.txt          # Extracted text from projects
└── 📄 .gitkeep               # Keep directory in git
```

---

### 📂 **Logs & Monitoring** (`/logs/`)

```
logs/
├── app.log                   # Main application logs
├── celery.log                # Celery worker logs
├── celery_new.log           # Updated Celery logs
├── celery_new_reader.log    # Celery reader logs
├── celery_proper.log        # Proper Celery logs
├── flask.log                # Flask-specific logs
└── .gitkeep                 # Keep directory in git
```

---

### ⚙️ **Process Management** (`/pids/`)

```
pids/
└── redis.pid                 # Redis process ID file
```

---

### 🎨 **Frontend Assets** (`/static/` & `/templates/`)

```
static/
├── css/                      # CSS stylesheets
└── js/                       # JavaScript files

templates/                     # Jinja2 templates (empty currently)
```

---

### 🧪 **Test Files** (`/`)

| File | Fungsi | Deskripsi |
|------|--------|-----------|
| `test_api.sh` | 🧪 API Testing | Automated API testing script |
| `test_evaluation.py` | 🧪 Evaluation Testing | Test evaluation logic |
| `test_scenarios.py` | 🧪 Scenario Testing | End-to-end test scenarios |

---

### 🚀 **Utility Scripts** (`/`)

| File | Fungsi | Deskripsi |
|------|--------|-----------|
| `run.sh` | 🚀 Quick Start | Quick start script |
| `start_services.sh` | 🚀 Services Manager | Script untuk memulai services |
| `celery_worker.py` | ⚙️ Worker Script | Alternative Celery worker script |

---

## 🔄 **Data Flow Architecture**

```
📱 Client Request
    ↓
🌐 Flask API (main.py)
    ↓
📋 Task Queue (Celery)
    ↓
⚙️ Background Worker (workers.py)
    ↓
🧠 RAG System (rag.py)
    ↓
🤖 AI Evaluation (llm.py)
    ↓
🗄️ Database (models.py + database.py)
    ↓
📤 JSON Response
```

## 🎯 **Key Components**

### **1. API Layer** (`main.py`)
- REST endpoints untuk upload, evaluation, dan results
- File upload handling dengan PDF text extraction
- Request validation dan error handling

### **2. Background Processing** (`workers.py`, `tasks.py`)
- Celery-based asynchronous processing
- PDF parsing dan text extraction
- AI evaluation dengan RAG integration

### **3. RAG System** (`rag.py`)
- ChromaDB vector database
- Document ingestion dan indexing
- Semantic search untuk context retrieval

### **4. AI Integration** (`llm.py`)
- Google Gemini API integration
- Fallback evaluation algorithms
- Structured scoring system

### **5. Data Layer** (`models.py`, `database.py`)
- SQLite database dengan SQLAlchemy ORM
- Job status tracking
- Result storage and retrieval

## 🎯 **Configuration Files**

### **Environment Variables** (`.env`)
```env
REDIS_URL=redis://localhost:6379/0
GEMINI_API_KEY=your_gemini_api_key
PYTHONPATH=/app
FLASK_ENV=development
LOG_LEVEL=INFO
```

### **Requirements** (`requirements.txt`)
- Flask framework dan CORS
- Celery dengan Redis broker
- ChromaDB untuk vector storage
- Google Generative AI
- PyMuPDF untuk PDF processing

## 🐳 **Docker Configuration**

### **Multi-Stage Build**
- **Base Stage**: System dependencies dan Python packages
- **Production Stage**: Optimized runtime image
- **Development Build**: Hot-reload dan development tools

### **Service Orchestration**
- **API Service**: Flask application
- **Worker Service**: Celery workers (2 instances)
- **Redis**: Message broker dan caching
- **Optional**: Flower monitoring, Beat scheduler

---

## 📊 **File Organization Principles**

### **✅ Well Organized:**
- ✅ Separation of concerns (API, workers, models, RAG)
- ✅ Clear documentation structure
- ✅ Sample data in multiple formats
- ✅ Comprehensive test coverage
- ✅ Docker optimization

### **🔄 Areas for Improvement:**
- 📝 Could consolidate duplicate worker scripts
- 📝 Could organize frontend assets better
- 📝 Could add more test coverage
- 📝 Could implement better error logging

---

## 🚀 **Getting Started**

1. **Clone Repository**
   ```bash
   git clone <repository_url>
   cd hr-service
   ```

2. **Environment Setup**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Docker Deployment**
   ```bash
   ./docker-start.sh init
   ./docker-start.sh start
   ```

4. **Test API**
   ```bash
   ./test_api.sh
   ```

---

## 📚 **Documentation Links**

- [Main README](README.md)
- [API Documentation](API_DOCUMENTATION.md)
- [Docker Guide](README_DOCKER.md)
- [Docker Optimization](DOCKER_OPTIMIZATION.md)
- [AI Setup Guide](setup_ai.md)

---

**Project Structure Last Updated**: 7 November 2025
**Version**: 1.2.0
**Status**: Production Ready 🚀