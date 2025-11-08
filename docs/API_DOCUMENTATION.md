# HR Screening System API Documentation

## 🚀 Overview

HR Screening System adalah aplikasi berbasis Flask dengan Celery untuk background processing yang digunakan untuk mengevaluasi CV dan project report kandidat menggunakan AI dan RAG (Retrieval-Augmented Generation).

## 🌐 Base Configuration

- **Base URL**: `http://localhost:5000`
- **Content-Type**: `application/json` (kecuali untuk upload file)
- **Timeout**: 30000ms (30 detik untuk AI processing)
- **Port**: 5000

## 📋 Available Endpoints

### 1. Health Check

**Endpoint**: `GET /`

**Deskripsi**: Mengecek status API dan melihat endpoint yang tersedia

**Request**:
```bash
curl -X GET http://localhost:5000/ \
  -H "Content-Type: application/json"
```

**Response**:
```json
{
  "endpoints": {
    "evaluate": "/evaluate",
    "ingest": "/ingest",
    "result": "/result/<id>",
    "upload": "/upload"
  },
  "message": "HR Service",
  "version": "1.2.0"
}
```

### 2. Upload Documents

**Endpoint**: `POST /upload`

**Deskripsi**: Mengupload file CV atau project report dalam format PDF

**Request**:
```bash
curl -X POST http://localhost:5000/upload \
  -H "Content-Type: multipart/form-data" \
  -F "files=@cv_1_john_doe.pdf" \
  -F "files=@project_report_1_excellent.pdf"
```

**Headers**:
- `Content-Type: multipart/form-data`

**Body**:
- `files`: File PDF (banyak file dapat diupload sekaligus)

**Response**:
```json
{
  "message": "Files uploaded successfully",
  "documents": [
    {
      "id": 1,
      "filename": "cv_1_john_doe.pdf",
      "type": "cv",
      "status": "uploaded"
    },
    {
      "id": 2,
      "filename": "project_report_1_excellent.pdf",
      "type": "project",
      "status": "uploaded"
    }
  ]
}
```

### 3. Manual Ingest Text

**Endpoint**: `POST /ingest`

**Deskripsi**: Memasukkan teks manual ke dalam RAG system

**Request**:
```bash
curl -X POST http://localhost:5000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "test_doc_1",
    "text": "Sample text for testing RAG functionality",
    "metadata": {"type": "test", "source": "manual"}
  }'
```

**Headers**:
- `Content-Type: application/json`

**Body**:
```json
{
  "doc_id": "string",
  "text": "string",
  "metadata": {
    "type": "string",
    "source": "string"
  }
}
```

**Response**:
```json
{
  "message": "Text ingested successfully",
  "doc_id": "test_doc_1"
}
```

### 4. Evaluate Candidates

**Endpoint**: `POST /evaluate`

**Deskripsi**: Mengevaluasi CV dan project report kandidat menggunakan AI

**Request**:
```bash
curl -X POST http://localhost:5000/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "job_title": "Backend Engineer with AI/ML",
    "documents": [
      {"id": 1, "type": "cv"},
      {"id": 2, "type": "project"}
    ]
  }'
```

**Headers**:
- `Content-Type: application/json`

**Body**:
```json
{
  "job_title": "Backend Engineer with AI/ML",
  "documents": [
    {
      "id": 1,
      "type": "cv"
    },
    {
      "id": 2,
      "type": "project"
    }
  ]
}
```

**Response**:
```json
{
  "job_id": 1,
  "status": "processing",
  "message": "Evaluation started. Use /result/1 to check progress."
}
```

### 5. Get Evaluation Results

**Endpoint**: `GET /result/<job_id>`

**Deskripsi**: Mendapatkan hasil evaluasi kandidat

**Request**:
```bash
curl -X GET http://localhost:5000/result/1 \
  -H "Content-Type: application/json"
```

**Headers**:
- `Content-Type: application/json`

**Path Parameters**:
- `job_id`: ID dari job evaluasi

**Response (Processing)**:
```json
{
  "job_id": 1,
  "status": "processing",
  "progress": 50,
  "message": "Analyzing CV..."
}
```

**Response (Completed)**:
```json
{
  "job_id": 1,
  "status": "completed",
  "result": {
    "overall_score": 85,
    "cv_evaluation": {
      "score": 88,
      "strengths": ["Strong Python skills", "AI/ML experience"],
      "weaknesses": ["Limited cloud experience"],
      "recommendation": "Highly recommended"
    },
    "project_evaluation": {
      "score": 82,
      "technical_skills": ["Backend development", "Database design"],
      "project_quality": "Good",
      "recommendation": "Recommended"
    },
    "final_recommendation": "Strong candidate for Backend Engineer with AI/ML position"
  }
}
```

## 🎯 Postman/Insomnia Setup

### Environment Variables

```json
{
  "base_url": "http://localhost:5000",
  "job_title": "Backend Engineer with AI/ML"
}
```

### Collection Structure

1. **Health Check**
   - Method: `GET`
   - URL: `{{base_url}}/`

2. **Upload CV**
   - Method: `POST`
   - URL: `{{base_url}}/upload`
   - Body: `form-data`
   - Key: `files` | Type: `File` | Value: pilih PDF CV

3. **Upload Project Report**
   - Method: `POST`
   - URL: `{{base_url}}/upload`
   - Body: `form-data`
   - Key: `files` | Type: `File` | Value: pilih PDF Project

4. **Evaluate Candidate**
   - Method: `POST`
   - URL: `{{base_url}}/evaluate`
   - Body: `raw JSON`
   ```json
   {
     "job_title": "{{job_title}}",
     "documents": [
       {"id": 1, "type": "cv"},
       {"id": 2, "type": "project"}
     ]
   }
   ```

5. **Check Results**
   - Method: `GET`
   - URL: `{{base_url}}/result/1`

## 📁 Test Files Available

### CV Samples
- `cv_1_john_doe.pdf` - CV Backend Engineer dengan AI experience
- `cv_2_sarah_wilson.pdf` - CV Senior Backend Developer
- `cv_3_mike_chen.pdf` - CV Full Stack dengan fokus Backend

### Project Report Samples
- `project_report_1_excellent.pdf` - Project AI/ML implementation (Excellent)
- `project_report_2_good.pdf` - Backend system design (Good)
- `project_report_3_basic.pdf` - Simple web application (Basic)

## ⚡ Quick Test Script

```bash
#!/bin/bash

# Base URL
BASE_URL="http://localhost:5000"

echo "🚀 Testing HR Screening System API"
echo "=================================="

# 1. Health Check
echo "1. Checking API health..."
curl -s $BASE_URL/ | jq .

# 2. Upload CV
echo -e "\n2. Uploading CV..."
CV_RESPONSE=$(curl -s -X POST $BASE_URL/upload \
  -F "files=@samples/pdfs/cv_1_john_doe.pdf")
echo $CV_RESPONSE | jq .

# 3. Upload Project Report
echo -e "\n3. Uploading Project Report..."
PROJECT_RESPONSE=$(curl -s -X POST $BASE_URL/upload \
  -F "files=@samples/pdfs/project_report_1_excellent.pdf")
echo $PROJECT_RESPONSE | jq .

# 4. Start Evaluation
echo -e "\n4. Starting evaluation..."
EVAL_RESPONSE=$(curl -s -X POST $BASE_URL/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "job_title": "Backend Engineer with AI/ML",
    "documents": [
      {"id": 1, "type": "cv"},
      {"id": 2, "type": "project"}
    ]
  }')
echo $EVAL_RESPONSE | jq .

# Extract Job ID
JOB_ID=$(echo $EVAL_RESPONSE | jq -r '.job_id')

# 5. Check Results (polling)
echo -e "\n5. Checking results..."
for i in {1..10}; do
  RESULT=$(curl -s -X GET $BASE_URL/result/$JOB_ID)
  STATUS=$(echo $RESULT | jq -r '.status')

  echo "Attempt $i: Status = $STATUS"
  echo $RESULT | jq .

  if [ "$STATUS" = "completed" ]; then
    echo "✅ Evaluation completed!"
    break
  fi

  sleep 5
done
```

## 🔧 Error Handling

### Common Error Responses

#### 400 Bad Request
```json
{
  "error": "Missing required field: job_title",
  "status": "error"
}
```

#### 404 Not Found
```json
{
  "error": "Job with ID 999 not found",
  "status": "error"
}
```

#### 500 Internal Server Error
```json
{
  "error": "Failed to process PDF file",
  "status": "error",
  "details": "PyMuPDF not available"
}
```

## 🎭 AI Evaluation Process

### Scoring Parameters
- **Backend Skills (50%)**: Python, Database, API, System Design
- **AI/ML Skills (30%)**: Machine Learning, Data Processing, AI Frameworks
- **Experience (15%)**: Years of experience, Project complexity
- **Achievements (5%)**: Certifications, Awards, Open source

### Evaluation Steps
1. **Text Extraction**: Menggunakan PyMuPDF dengan fallback ke pdfplumber
2. **Content Analysis**: AI analysis dengan Google Gemini atau fallback keyword-based
3. **Scoring**: Automatic scoring berdasarkan job requirements
4. **Recommendation**: Final recommendation dengan detail analysis

## 📊 Monitoring & Debugging

### Check Docker Status
```bash
./docker-start.sh status
```

### View Logs
```bash
./docker-start.sh logs api
./docker-start.sh logs worker
```

### Check Celery Tasks
```bash
docker exec hr-service-worker-1 celery -A celery_app inspect active
docker exec hr-service-worker-1 celery -A celery_app inspect registered
```

## 🎉 Success Indicators

✅ **API is working**: Health check returns 200
✅ **File upload successful**: Documents return with IDs
✅ **Evaluation starts**: Job ID returned from evaluate endpoint
✅ **Background processing**: Celery workers show ready status
✅ **Results available**: /result endpoint returns completed evaluation

---

**Dibuat untuk HR Screening System v1.2.0**
**Last Updated**: 7 November 2025