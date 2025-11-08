# HR Service - Local Development Setup Guide

## 🚀 Cara Proper Menjalankan Aplikasi di Local

Ada **3 cara** untuk menjalankan aplikasi ini di local. Pilih yang paling sesuai dengan kebutuhan Anda.

---

## 📋 Prasyarat (Requirements)

### Software yang harus diinstall:
- **Python 3.11+** (direkomendasikan 3.11)
- **Redis Server** (untuk background job processing)
- **Git** (untuk clone repository)

### API Key yang dibutuhkan:
- **Google Gemini API Key** - Dapatkan dari [Google AI Studio](https://makersuite.google.com/app/apikey)

---

## 🔧 **Cara 1: Docker (Recommended untuk Production-like)**

Cara ini paling mudah dan recommended karena semua dependencies sudah terbundle.

### 1. Start Redis dan API
```bash
# Jalankan semua services (Redis + API + Worker)
docker-compose up -d

# Atau jalankan dengan logs untuk debugging
docker-compose up
```

### 2. Setup API Key
```bash
# Edit docker-compose.yml dan ganti API key
# line 36 & 67: GANTI AIzaSyCRtkNwIKFirwnxziwijEx-3lVUOVknjaY
# dengan API key Anda sendiri
```

### 3. Test aplikasi
```bash
# Test health check
curl http://localhost:5000/health

# Test root endpoint
curl http://localhost:5000/
```

### 4. Stop aplikasi
```bash
docker-compose down
```

**🔍 Monitoring Docker:**
```bash
# Lihat logs semua services
docker-compose logs -f

# Lihat logs API saja
docker-compose logs -f api

# Lihat logs worker saja
docker-compose logs -f worker
```

---

## 💻 **Cara 2: Local Python Development**

Cara ini untuk development dengan fitur auto-reload saat code berubah.

### 1. Install Redis
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install redis-server

# MacOS (dengan Homebrew)
brew install redis

# Start Redis
sudo systemctl start redis-server  # Linux
brew services start redis           # MacOS
```

### 2. Setup Python Environment
```bash
# Clone repository (jika belum)
git clone <repository-url>
cd hr-service

# Buat virtual environment
python -m venv venv

# Aktifkan virtual environment
source venv/bin/activate  # Linux/Mac
# atau
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Setup Environment Variables
```bash
# Buat file .env
cat > .env << 'EOF'
# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Google Gemini API Key - GANTI DENGAN API KEY ANDA
GEMINI_API_KEY=your_api_key_here

# Development Settings
FLASK_ENV=development
PYTHONPATH=$(pwd)
PYTHONUNBUFFERED=1
LOG_LEVEL=DEBUG
EOF

# Set API key Anda
export GEMINI_API_KEY="your_actual_api_key_here"
```

### 4. Start Worker (Terminal 1)
```bash
source venv/bin/activate
export GEMINI_API_KEY="your_actual_api_key_here"

# Start worker process
python src/workers/simple_worker.py
```

### 5. Start API Server (Terminal 2)
```bash
source venv/bin/activate
export GEMINI_API_KEY="your_actual_api_key_here"

# Start Flask development server dengan auto-reload
python main.py
```

---

## 🚀 **Cara 3: Hybrid Development**

Cara ini kombinasi Redis di Docker dan Python development di local.

### 1. Start Redis dengan Docker
```bash
# Jalankan Redis saja
docker-compose up redis -d
```

### 2. Setup Python Environment
```bash
# Langkah 2-4 dari Cara 2 di atas
```

### 3. Aplikasi akan terhubung ke Redis di Docker
Aplikasi Python local akan otomatis terhubung ke Redis yang berjalan di Docker.

---

## 🧪 Testing Aplikasi

### 1. Basic Health Check
```bash
curl http://localhost:5000/health
```

### 2. Upload Documents
```bash
# Upload CV dan Report
curl -X POST http://localhost:5000/upload \
  -F "cv=@path/to/cv.pdf" \
  -F "report=@path/to/report.pdf"
```

### 3. Evaluate CV
```bash
# Ganti cv_id dan report_id dari hasil upload
curl -X POST http://localhost:5000/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "job_title": "Software Engineer",
    "cv_id": 1,
    "report_id": 1
  }'
```

### 4. Get Result
```bash
# Ganti job_id dari hasil evaluate
curl http://localhost:5000/result/1
```

---

## 🐛 Troubleshooting

### **Problem: Redis Connection Error**
```bash
# Cek Redis running
redis-cli ping

# Start Redis manual
redis-server

# Cek port 6379
netstat -tlnp | grep 6379
```

### **Problem: API Key Error**
```bash
# Verifikasi API key ter-set
echo $GEMINI_API_KEY

# Test API key
curl -H "Content-Type: application/json" \
     -d '{"contents":[{"parts":[{"text":"Hello"}]}]}' \
     "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=$GEMINI_API_KEY"
```

### **Problem: Dependencies Error**
```bash
# Reinstall dependencies
pip uninstall -r requirements.txt -y
pip install -r requirements.txt

# Update specific packages
pip install --upgrade chromadb numpy
```

### **Problem: Port Already in Use**
```bash
# Kill process di port 5000
sudo lsof -ti:5000 | xargs kill -9

# Atau gunakan port lain
python -c "from main import app; app.run(port=5001)"
```

---

## 📁 Project Structure

```
hr-service/
├── main.py                 # Main Flask application
├── src/
│   ├── core/              # AI & RAG engines
│   ├── models/            # Database models
│   ├── workers/           # Background workers
│   └── monitoring/        # Health monitoring
├── uploads/               # File uploads directory
├── logs/                  # Application logs
├── requirements.txt       # Python dependencies
├── docker-compose.yml     # Docker configuration
├── Dockerfile            # Docker image config
└── .env                  # Environment variables
```

---

## 🎯 Development Tips

### **Hot Reload Development**
```bash
# Untuk development dengan auto-reload
export FLASK_ENV=development
python main.py
```

### **Debug Mode**
```bash
# Enable debug mode
export FLASK_DEBUG=1
python main.py
```

### **Database Reset**
```bash
# Hapus database untuk fresh start
rm -f database.db
python -c "from src.models.database import init_db; init_db()"
```

### **Logs Monitoring**
```bash
# Monitor logs real-time
tail -f logs/app.log
tail -f logs/celery.log
```

---

## 🔐 Security Notes

- **Jangan commit API key** ke version control
- **Gunakan environment variables** untuk sensitive data
- **API hanya untuk development**, tidak untuk production tanpa proper security setup

---

## ✅ Recommendation

Untuk **development**: Gunakan **Cara 2** (Local Python Development) untuk fitur hot-reload dan debugging yang lebih mudah.

Untuk **production-like testing**: Gunakan **Cara 1** (Docker) untuk environment yang mendekati production.

Happy coding! 🎉