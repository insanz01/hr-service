# Project Cleanup & Organization Guide

## 🎯 Objective

Membersihkan dan mengorganisir struktur proyek HR Screening System untuk better maintainability dan clarity.

## 📋 Cleanup Recommendations

### 1. 🗑️ Remove Duplicate/Redundant Files

#### **Duplicate Worker Scripts:**
```bash
# Files to consider removing:
- celery_worker.py          # Redundant dengan start_worker.py
- celery_app.py             # Bisa digabung dengan tasks.py
- start_services.sh         # Redundant dengan docker-start.sh
- run.sh                   # Redundant dengan docker-start.sh
```

#### **Duplicate Documentation:**
```bash
# Consider consolidating:
- README_DOCKER.md          # Could merge into main README
- README_RUN.md            # Could merge into main README
- setup_ai.md              # Could merge into main README
```

### 2. 📁 Reorganize File Structure

#### **Proposed New Structure:**
```
hr-service/
├── 📁 src/                    # Main application code
│   ├── 📁 api/               # API layer
│   │   ├── __init__.py
│   │   ├── routes.py         # From main.py routes
│   │   └── utils.py          # API utilities
│   ├── 📁 core/              # Core business logic
│   │   ├── __init__.py
│   │   ├── evaluation.py     # From workers.py logic
│   │   ├── rag_engine.py     # From rag.py
│   │   └── ai_engine.py      # From llm.py
│   ├── 📁 models/            # Data models
│   │   ├── __init__.py
│   │   ├── database.py       # From models.py
│   │   └── schemas.py        # Pydantic schemas
│   ├── 📁 workers/           # Background processing
│   │   ├── __init__.py
│   │   ├── tasks.py          # From tasks.py
│   │   └── celery_app.py     # From celery_app.py
│   └── 📁 utils/             # Utilities
│       ├── __init__.py
│       ├── pdf_processor.py  # PDF processing logic
│       └── config.py         # Configuration
├── 📁 tests/                 # Test files
│   ├── __init__.py
│   ├── test_api.py
│   ├── test_evaluation.py
│   └── test_integration.py
├── 📁 docs/                  # Documentation
│   ├── README.md
│   ├── API.md
│   ├── DEPLOYMENT.md
│   └── DEVELOPMENT.md
├── 📁 scripts/               # Utility scripts
│   ├── start.sh
│   ├── test.sh
│   └── setup.sh
├── 📁 samples/               # Sample data
│   ├── cvs/
│   ├── projects/
│   └── case_study/
├── 📁 uploads/               # Runtime uploads
├── 📁 logs/                  # Logs
├── 📁 static/                # Static assets
├── 📁 templates/             # Templates
├── main.py                   # Application entry point
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
├── .env.example
└── README.md
```

### 3. 🔧 Specific Actions

#### **A. Remove Redundant Files:**
```bash
# Remove duplicate scripts
rm celery_worker.py
rm start_services.sh
rm run.sh

# Remove duplicate READMEs (after consolidation)
rm README_DOCKER.md
rm README_RUN.md
rm setup_ai.md
```

#### **B. Consolidate Core Files:**
```python
# Merge celery_app.py into tasks.py
# Extract routes from main.py into api/routes.py
# Extract business logic from workers.py into core/evaluation.py
```

#### **C. Create Proper Package Structure:**
```bash
# Create proper __init__.py files
touch src/__init__.py
touch src/api/__init__.py
touch src/core/__init__.py
# ... etc
```

### 4. 📝 File Content Cleanup

#### **Consolidate README.md:**
```markdown
# HR Screening System

## 🚀 Quick Start
## 🐳 Docker Deployment
## 🤖 AI Setup
## 📡 API Documentation
## 🧪 Testing
## 📚 Development Guide
```

#### **Clean Up Main.py:**
```python
# Keep only:
# - App initialization
# - Basic imports
# - Entry point

# Move to src/api/routes.py:
# - All route definitions
# - Request handling logic
```

#### **Organize Workers.py:**
```python
# Move to src/core/evaluation.py:
# - Evaluation logic
# - AI integration calls

# Move to src/workers/tasks.py:
# - Celery task definitions
# - Background job processing
```

### 5. 🎯 Implementation Steps

#### **Step 1: Backup**
```bash
# Create backup before cleanup
cp -r /path/to/hr-service /path/to/hr-service-backup
```

#### **Step 2: Create New Structure**
```bash
# Create new directories
mkdir -p src/{api,core,models,workers,utils}
mkdir -p tests docs scripts

# Create __init__.py files
touch src/__init__.py src/api/__init__.py src/core/__init__.py
touch src/models/__init__.py src/workers/__init__.py src/utils/__init__.py
```

#### **Step 3: Move and Refactor Files**
```bash
# Move files to new structure
mv rag.py src/core/rag_engine.py
mv llm.py src/core/ai_engine.py
mv models.py src/models/database.py
mv tasks.py src/workers/
mv celery_app.py src/workers/

# Move test files
mv test_*.py tests/
mv test_*.sh scripts/
```

#### **Step 4: Update Imports**
```python
# Update all import statements
# From: import rag
# To: from src.core.rag_engine import ingest_text, query

# From: import models
# To: from src.models.database import Document, Job
```

#### **Step 5: Update Docker Files**
```dockerfile
# Update Dockerfile WORKDIR
WORKDIR /app

# Update Python path
ENV PYTHONPATH=/app/src
```

#### **Step 6: Update Configuration**
```python
# Update imports in main.py
from src.api.routes import app
from src.workers.celery_app import celery
```

### 6. 🧪 Validation

#### **Test After Cleanup:**
```bash
# Test basic functionality
python main.py

# Test Docker build
docker-compose build

# Test API endpoints
./scripts/test.sh

# Run tests
python -m pytest tests/
```

### 7. 📋 Cleanup Checklist

- [ ] Remove duplicate files
- [ ] Create new directory structure
- [ ] Move files to appropriate locations
- [ ] Update all import statements
- [ ] Consolidate documentation
- [ ] Update Docker configuration
- [ ] Test basic functionality
- [ ] Test Docker deployment
- [ ] Run automated tests
- [ ] Update README with new structure

## 🎯 Benefits of Cleanup

### **Before Cleanup:**
- 79+ files in root directory
- Duplicate functionality
- Unclear separation of concerns
- Difficult to maintain

### **After Cleanup:**
- Clear package structure
- Separation of concerns
- Better maintainability
- Easier testing
- Cleaner documentation

## 🚀 Migration Plan

### **Phase 1: Preparation**
1. Create backup
2. Document current structure
3. Plan new structure

### **Phase 2: Implementation**
1. Create new directories
2. Move files incrementally
3. Update imports
4. Test each component

### **Phase 3: Validation**
1. Run full test suite
2. Test Docker deployment
3. Validate API functionality
4. Performance testing

### **Phase 4: Documentation**
1. Update README
2. Update API documentation
3. Create developer guide
4. Update deployment guide

---

**⚠️ Important**: Always backup before making structural changes to the project!

**This cleanup guide provides a systematic approach to organizing the HR Screening System project for better maintainability and clarity.**