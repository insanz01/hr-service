# Docker Setup with SimpleWorker

## Architecture Overview

This HR Service now uses **SimpleWorker** instead of Celery for background processing:

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Flask API  │───▶│   Redis     │───▶│ SimpleWorker │
│   (Port 5000)│    │   Queue     │    │  (AI Jobs)   │
└─────────────┘    └─────────────┘    └─────────────┘
```

## Quick Start with Docker Compose

### 1. Start All Services
```bash
# Build and start Redis + API + Workers
docker-compose up -d --build

# Check status
docker-compose ps
```

### 2. Services Overview

- **Redis** (Port 6379): Queue and result storage
- **API** (Port 5000): Flask REST API server
- **Workers** (2 instances): SimpleWorker processing AI evaluation jobs

### 3. Verify Setup
```bash
# Check API health
curl http://localhost:5000/health

# Check logs
docker-compose logs -f api
docker-compose logs -f worker
```

## Development Workflow

### Using Dockerfile.dev (Recommended for Development)
```bash
# Build development image
docker build -f Dockerfile.dev -t hr-api-dev .

# Run API server with hot reload
docker run -p 5000:5000 --env-file .env hr-api-dev

# Run worker in separate terminal
docker run --env-file .env hr-api-dev python src/workers/simple_worker.py
```

### Manual Docker Commands
```bash
# Build production image
docker build -t hr-api:latest .

# Run Redis
docker run -d --name hr-redis -p 6379:6379 redis:7-alpine

# Run API
docker run -d --name hr-api -p 5000:5000 \
  --env REDIS_URL=redis://hr-redis:6379/0 \
  --env GEMINI_API_KEY=your_api_key \
  hr-api:latest

# Run Worker
docker run -d --name hr-worker \
  --env REDIS_URL=redis://hr-redis:6379/0 \
  --env GEMINI_API_KEY=your_api_key \
  hr-api:latest python src/workers/simple_worker.py
```

## Environment Variables

Required for both API and Worker:

```bash
# Redis Configuration
REDIS_URL=redis://redis:6379/0

# AI Configuration
GEMINI_API_KEY=your_gemini_api_key

# Application Configuration
PYTHONPATH=/app
PYTHONUNBUFFERED=1
FLASK_ENV=development
LOG_LEVEL=INFO
```

## Monitoring & Debugging

### Check Worker Status
```bash
# View worker logs
docker-compose logs worker

# Check Redis queue
docker exec hr-redis redis-cli LLEN evaluation_queue

# Check Redis results
docker exec hr-redis redis-cli KEYS "job_result:*"
```

### API Testing
```bash
# Upload documents
curl -X POST -F "cv=@test_cv.txt" -F "report=@test_cv.txt" \
  http://localhost:5000/upload

# Submit evaluation
curl -X POST -H "Content-Type: application/json" \
  -d '{"job_title": "Senior Software Engineer", "cv_id": 1, "report_id": 2}' \
  http://localhost:5000/evaluate

# Check results
curl http://localhost:5000/result/1
```

## Scaling Workers

```bash
# Scale to 4 worker instances
docker-compose up -d --scale worker=4

# Check running instances
docker-compose ps
```

## Differences from Celery Setup

| Feature | Old (Celery) | New (SimpleWorker) |
|---------|---------------|-------------------|
| Queue Backend | Redis + Celery | Redis only |
| Worker Process | Celery Worker | Simple Python Process |
| Configuration | Complex broker setup | Simple Redis URL |
| Monitoring | Flower UI | Redis CLI / Logs |
| Dependencies | celery[redis] | redis |
| Startup Time | Slower | Faster |
| Debugging | Harder | Easier (direct logs) |

## Troubleshooting

### Worker Not Processing Jobs
```bash
# Check if worker is running
docker-compose logs worker

# Check Redis connection
docker exec hr-redis redis-cli ping

# Check queue status
docker exec hr-redis redis-cli LLEN evaluation_queue
```

### API Cannot Connect to Redis
```bash
# Check Redis container
docker-compose ps redis

# Test API to Redis connection
docker exec hr-api python -c "import redis; r=redis.from_url('redis://redis:6379/0'); print(r.ping())"
```

### Jobs Stuck in "Processing"
```bash
# Restart workers
docker-compose restart worker

# Clear stuck jobs (if needed)
docker exec hr-redis redis-cli DEL evaluation_queue
```

## Production Deployment

For production, use the production Dockerfile:

```bash
# Build production image
docker build -f Dockerfile -t hr-api:prod .

# Use production environment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Next Steps

1. Set up proper environment variables in `.env` file
2. Configure Redis persistence for production
3. Set up monitoring and alerting
4. Configure health checks and auto-restart policies
5. Review security settings (non-root user, resource limits)