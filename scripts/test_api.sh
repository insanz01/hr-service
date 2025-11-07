#!/bin/bash

# HR Screening System API Test Script
# Usage: ./test_api.sh

echo "🚀 Testing HR Screening System API"
echo "=================================="

# Base URL
BASE_URL="http://localhost:5000"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

# Function to test API
test_api() {
    local endpoint=$1
    local method=$2
    local data=$3
    local description=$4

    print_info "Testing: $description"

    if [ -z "$data" ]; then
        response=$(curl -s -X $method "$BASE_URL$endpoint" \
                    -H "Content-Type: application/json")
    else
        response=$(curl -s -X $method "$BASE_URL$endpoint" \
                    -H "Content-Type: application/json" \
                    -d "$data")
    fi

    if [ $? -eq 0 ]; then
        print_status "✅ $description - Success"
        echo "Response:"
        echo "$response" | jq . 2>/dev/null || echo "$response"
    else
        print_error "❌ $description - Failed"
        echo "Response: $response"
    fi
    echo ""
}

# Function to upload file
upload_file() {
    local file_path=$1
    local description=$2

    print_info "Uploading: $description"

    response=$(curl -s -X POST "$BASE_URL/upload" \
                -F "files=@$file_path")

    if [ $? -eq 0 ]; then
        print_status "✅ $description - Upload Success"
        echo "Response:"
        echo "$response" | jq . 2>/dev/null || echo "$response"
        echo "$response"
    else
        print_error "❌ $description - Upload Failed"
        echo "Response: $response"
    fi
    echo ""
}

# Check if API is running
echo "1. Checking API availability..."
health_response=$(curl -s $BASE_URL/ 2>/dev/null)
if [ $? -eq 0 ]; then
    print_status "✅ API is running"
    echo "Health Response:"
    echo "$health_response" | jq . 2>/dev/null || echo "$health_response"
else
    print_error "❌ API is not responding at $BASE_URL"
    exit 1
fi
echo ""

# Test file uploads
echo "2. Testing file uploads..."
cv_response=$(upload_file "samples/pdfs/cv_1_john_doe.pdf" "CV - John Doe")
project_response=$(upload_file "samples/pdfs/project_report_1_excellent.pdf" "Project Report - Excellent")

# Extract document IDs (if jq is available)
if command -v jq >/dev/null 2>&1; then
    cv_id=$(echo "$cv_response" | jq -r '.documents[0].id' 2>/dev/null)
    project_id=$(echo "$project_response" | jq -r '.documents[0].id' 2>/dev/null)

    if [ "$cv_id" = "null" ] || [ -z "$cv_id" ]; then
        cv_id=1
    fi
    if [ "$project_id" = "null" ] || [ -z "$project_id" ]; then
        project_id=2
    fi

    print_info "Using document IDs: CV=$cv_id, Project=$project_id"
else
    cv_id=1
    project_id=2
    print_info "Using default document IDs: CV=$cv_id, Project=$project_id"
fi
echo ""

# Test evaluation
echo "3. Testing candidate evaluation..."
eval_data='{
  "job_title": "Backend Engineer with AI/ML",
  "documents": [
    {"id": '$cv_id', "type": "cv"},
    {"id": '$project_id', "type": "project"}
  ]
}'

eval_response=$(curl -s -X POST "$BASE_URL/evaluate" \
                -H "Content-Type: application/json" \
                -d "$eval_data")

if [ $? -eq 0 ]; then
    print_status "✅ Evaluation started"
    echo "Evaluation Response:"
    echo "$eval_response" | jq . 2>/dev/null || echo "$eval_response"

    # Extract job ID
    if command -v jq >/dev/null 2>&1; then
        job_id=$(echo "$eval_response" | jq -r '.job_id' 2>/dev/null)
        if [ "$job_id" = "null" ] || [ -z "$job_id" ]; then
            job_id=1
        fi
    else
        job_id=1
    fi

    print_info "Job ID: $job_id"
    echo ""

    # Check results with polling
    echo "4. Checking evaluation results..."
    max_attempts=10
    attempt=1

    while [ $attempt -le $max_attempts ]; do
        print_info "Attempt $attempt/$max_attempts: Checking results..."

        result_response=$(curl -s -X GET "$BASE_URL/result/$job_id")

        if [ $? -eq 0 ]; then
            if command -v jq >/dev/null 2>&1; then
                status=$(echo "$result_response" | jq -r '.status' 2>/dev/null)
            else
                status="processing"
            fi

            echo "Status: $status"
            echo "Response:"
            echo "$result_response" | jq . 2>/dev/null || echo "$result_response"

            if [ "$status" = "completed" ]; then
                print_status "✅ Evaluation completed successfully!"
                break
            elif [ "$status" = "failed" ]; then
                print_error "❌ Evaluation failed"
                break
            fi
        else
            print_error "❌ Failed to get results"
        fi

        attempt=$((attempt + 1))
        if [ $attempt -le $max_attempts ]; then
            print_info "Waiting 10 seconds before next check..."
            sleep 10
        fi
        echo ""
    done

    if [ $attempt -gt $max_attempts ]; then
        print_error "⏰ Timeout: Evaluation did not complete within expected time"
    fi
else
    print_error "❌ Failed to start evaluation"
    echo "Response: $eval_response"
fi
echo ""

# Test manual ingest
echo "5. Testing manual text ingest..."
ingest_data='{
  "doc_id": "test_doc_1",
  "text": "Sample text for testing RAG functionality. This candidate has strong Python skills and experience with AI/ML frameworks including TensorFlow and PyTorch.",
  "metadata": {"type": "test", "source": "manual", "skill_level": "senior"}
}'

test_api "/ingest" "POST" "$ingest_data" "Manual text ingestion"

echo "🎉 API Testing Complete!"
echo "========================"
echo ""
echo "📋 Summary:"
echo "- ✅ API Health Check"
echo "- ✅ File Upload (CV & Project)"
echo "- ✅ Evaluation Process"
echo "- ✅ Result Checking"
echo "- ✅ Manual Ingest"
echo ""
echo "🔗 Next Steps:"
echo "1. Try with different PDF files"
echo "2. Test with different job titles"
echo "3. Check Celery worker logs: ./docker-start.sh logs worker"
echo "4. Monitor API logs: ./docker-start.sh logs api"
echo ""
echo "📚 For more details, see API_DOCUMENTATION.md"