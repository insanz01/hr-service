# HR Screening System

🤖 **AI-Powered HR Screening System with RAG (Retrieval-Augmented Generation)**

A comprehensive Flask-based application that evaluates candidate CVs and project reports using AI and vector search for Backend Engineer positions with AI/ML capabilities.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Redis (for Celery)
- Google Gemini API Key (optional, has fallback)

### Docker Deployment (Recommended)

```bash
# Initialize and start services
./docker-start.sh init
./docker-start.sh start

# Check status
./docker-start.sh status

# Test API
curl http://localhost:5000/
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Start Redis
redis-server

# Start API
python main.py

# Start Celery workers
python start_worker.py
```

## 📡 API Documentation

### Base URL
```
http://localhost:5000
```

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check and API info |
| POST | `/upload` | Upload CV and project files |
| POST | `/evaluate` | Start evaluation process |
| GET | `/result/<id>` | Get evaluation results |
| POST | `/ingest` | Manual text ingestion |

### Quick Test

```bash
# Upload CV
curl -X POST http://localhost:5000/upload \
  -F "files=@samples/pdfs/cv_1_john_doe.pdf"

# Start Evaluation
curl -X POST http://localhost:5000/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "job_title": "Backend Engineer with AI/ML",
    "documents": [{"id": 1, "type": "cv"}]
  }'

# Check Results
curl -X GET http://localhost:5000/result/1
```

## 🏗️ Architecture

### System Components

```
📱 Client Request
    ↓
🌐 Flask API (REST endpoints)
    ↓
📋 Celery Queue (Background processing)
    ↓
⚙️ Worker (Evaluation logic)
    ↓
🧠 RAG System (ChromaDB + vector search)
    ↓
🤖 AI Engine (Gemini + fallback)
    ↓
🗄️ Database (SQLite)
    ↓
📤 JSON Response
```

### Technology Stack

- **Backend**: Flask, SQLAlchemy
- **Background Jobs**: Celery with Redis
- **AI/ML**: Google Gemini API, ChromaDB
- **Vector Search**: Sentence Transformers
- **PDF Processing**: PyMuPDF, pdfplumber
- **Database**: SQLite
- **Containerization**: Docker & Docker Compose

## 📁 Project Structure

```
hr-service/
├── 📁 src/                    # Main application code
│   ├── 📁 api/               # REST API layer
│   │   └── routes.py          # API endpoints
│   ├── 📁 core/              # Business logic
│   │   ├── rag_engine.py     # RAG system
│   │   ├── ai_engine.py      # AI integration
│   │   └── evaluation.py     # Evaluation logic
│   ├── 📁 models/            # Data models
│   │   └── database.py       # SQLAlchemy models
│   ├── 📁 workers/           # Background processing
│   │   ├── celery_app.py     # Celery config
│   │   └── tasks.py          # Celery tasks
│   └── 📁 utils/             # Utilities
│       └── database.py       # Database setup
├── 📁 samples/               # Sample data
│   ├── raw/                  # Markdown files
│   ├── pdfs/                 # PDF versions
│   └── html/                 # HTML versions
├── 📁 docs/                  # Documentation
├── 📁 uploads/               # Runtime uploads
├── 📁 logs/                  # Application logs
├── main.py                   # Application entry point
├── docker-compose.yml        # Docker orchestration
├── Dockerfile                # Production build
├── Dockerfile.dev            # Development build
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## 🎯 Features

### ✅ Core Functionality
- **Document Upload**: CV and project report processing
- **AI Evaluation**: Intelligent candidate assessment
- **RAG Integration**: Context-aware evaluation
- **Background Processing**: Asynchronous job handling
- **Multi-format Support**: PDF, text, HTML files
- **Vector Search**: Semantic document retrieval
- **Fallback Mechanisms**: Graceful degradation

### 🤖 AI Capabilities
- **Skill Extraction**: Automatic skill recognition
- **Experience Analysis**: Years and level assessment
- **Project Evaluation**: Technical implementation review
- **Scoring System**: Structured candidate ranking
- **Context Matching**: Job-specific evaluation

### 📊 Evaluation Process
1. **Text Extraction**: PDF → clean text
2. **RAG Retrieval**: Find similar documents
3. **AI Analysis**: Evaluate against requirements
4. **Scoring**: Structured assessment
5. **Synthesis**: Final recommendation

## 🛠️ Configuration

### Environment Variables

```env
# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_BACKEND=redis://localhost:6379/1

# AI Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Flask Configuration
FLASK_ENV=development
PYTHONPATH=/app/src
LOG_LEVEL=INFO
```

### Requirements

```txt
# Core Framework
Flask==2.3.3
Flask-CORS==4.0.0
Werkzeug==2.3.7

# PDF Processing
PyMuPDF==1.24.5

# Database & Storage
chromadb==0.4.22

# AI/ML Dependencies
instructor==1.3.5
google-generativeai==0.8.3

# Background Tasks
celery[redis]==5.3.6

# Data Validation
pydantic==2.9.2

# NumPy compatibility
numpy<2.0,>=1.24.0
```

## 🧪 Testing

### Automated Testing

```bash
# Run API tests
python tests/test_api.py

# Test evaluation process
python tests/test_evaluation.py

# Run complete test suite
python -m pytest tests/
```

### Manual Testing

```bash
# Use provided test script
./scripts/test_api.sh

# Test individual endpoints
curl -X GET http://localhost:5000/
curl -X POST http://localhost:5000/upload -F "files=@samples/pdfs/cv_1_john_doe.pdf"
```

## 🐳 Docker Deployment

### Multi-Stage Build

```dockerfile
# Base stage with dependencies
FROM python:3.11-slim as base
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim as production
COPY --from=base /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY . .
CMD ["python", "main.py"]
```

### Services

- **API Service**: Flask application (port 5000)
- **Worker Service**: Celery workers (2 instances)
- **Redis**: Message broker and caching (port 6379)
- **Optional**: Flower monitoring (port 5555)

## 📊 Performance

### Optimization Features
- **Multi-stage builds**: Reduced image size
- **Layer caching**: Faster rebuilds
- **Parallel processing**: Multiple workers
- **Vector search**: Efficient retrieval
- **Background jobs**: Non-blocking operations

### Benchmarks
- **Document processing**: < 2 seconds
- **AI evaluation**: 30-60 seconds
- **Vector search**: < 100ms
- **API response**: < 200ms

## 🔧 Development

### Setting Up Development Environment

```bash
# Clone repository
git clone <repository_url>
cd hr-service

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your configuration

# Start services
./docker-start.sh start
```

### Code Structure

- **API Layer**: `src/api/routes.py`
- **Business Logic**: `src/core/`
- **Data Models**: `src/models/`
- **Background Jobs**: `src/workers/`
- **Utilities**: `src/utils/`

### Adding New Features

1. Add API endpoints in `src/api/routes.py`
2. Implement business logic in `src/core/`
3. Create database models in `src/models/`
4. Add background jobs in `src/workers/`

## 🐛 Troubleshooting

### Common Issues

#### Docker Issues
```bash
# Check container status
./docker-start.sh status

# View logs
./docker-start.sh logs api
./docker-start.sh logs worker

# Rebuild containers
./docker-start.sh rebuild
```

#### Redis Connection
```bash
# Check Redis
redis-cli ping

# Restart Redis
docker-compose restart redis
```

#### AI Evaluation Issues
```bash
# Check API key
echo $GEMINI_API_KEY

# Test fallback mechanism
# System works without API key using keyword-based evaluation
```

#### Database Issues
```bash
# Check database file
ls -la database.db

# Reset database
rm database.db
# Application will recreate on startup
```

## 📚 Documentation

- [API Documentation](API_DOCUMENTATION.md) - Complete API reference
- [Project Structure](PROJECT_STRUCTURE.md) - Detailed file breakdown
- [Docker Guide](DOCKER_OPTIMIZATION.md) - Container deployment
- [Cleanup Guide](CLEANUP_GUIDE.md) - Organization recommendations

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make your changes
4. Add tests
5. Submit pull request

## 📄 License

This project is licensed under the MIT License.

## 🎯 Use Cases

### HR Departments
- **Resume Screening**: Automated CV evaluation
- **Technical Assessment**: Project review and scoring
- **Candidate Ranking**: Structured comparison

### Recruitment Agencies
- **Bulk Processing**: Multiple candidate evaluation
- **Custom Criteria**: Job-specific evaluation
- **Reporting**: Detailed assessment reports

### Companies
- **Internal Hiring**: Streamlined recruitment
- **Skill Assessment**: Technical capability evaluation
- **Talent Pipeline**: Candidate database management

---

**🚀 Ready for production deployment!**

For detailed technical documentation, see [API_DOCUMENTATION.md](API_DOCUMENTATION.md).

**Version**: 1.2.0
**Last Updated**: November 2025