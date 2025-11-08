# HR Service - AI-Powered Candidate Screening System

Automated HR screening system that evaluates candidates based on CVs and project reports using AI/LLM technology with RAG (Retrieval-Augmented Generation).

## Overview

HR Service is a comprehensive web application that automates the initial screening process of job candidates by analyzing their CVs and project reports using advanced AI models. The system leverages Google Gemini AI through the Instructor library for structured evaluation and ChromaDB for efficient document retrieval.

## Key Features

- **AI-Powered Evaluation**: Uses Google Gemini AI to evaluate CVs and project reports
- **RAG Document Processing**: ChromaDB-based retrieval for case study and document context
- **Background Processing**: Redis-based queue system for scalable job processing
- **Comprehensive Scoring**: Multi-parameter evaluation with detailed feedback
- **RESTful API**: Clean, well-documented API endpoints
- **Docker Ready**: Fully containerized with multi-stage builds
- **Health Monitoring**: Built-in health checks for all system components

## Architecture & Design Choices

### 1. **Microservices Architecture**
- **API Service**: Handles HTTP requests and job submission
- **Worker Services**: Process evaluation jobs in parallel
- **Redis**: Acts as message queue and result cache
- **SQLite**: Lightweight database for job tracking

*Rationale*: Separates concerns, improves scalability and maintainability.

### 2. **AI Evaluation Pipeline**
- **Structured Output**: Uses Pydantic models for consistent AI responses
- **Fallback System**: Graceful degradation when AI services are unavailable
- **Multi-Parameter Scoring**: Technical, experience, and cultural fit evaluation

*Rationale*: Ensures consistent, reliable evaluation results and maintains system stability.

### 3. **Document Processing**
- **PDF Text Extraction**: PyMuPDF with PyPDF2 fallback
- **Content Ingestion**: ChromaDB for semantic search and retrieval
- **Metadata Storage**: Complete document tracking and versioning

*Rationale*: Provides efficient document search and maintains context for AI evaluation.

### 4. **Queue Management**
- **Simple Worker**: Primary background processing for development
- **Redis Integration**: Production-ready job queuing and result caching
- **Health Monitoring**: Real-time system status tracking

*Rationale*: Balances simplicity for development with scalability for production.

## Quick Start

### Using Docker (Recommended)

1. **Clone and Setup**:
   ```bash
   git clone <repository-url>
   cd hr-service
   cp .env.example .env
   ```

2. **Configure Environment**:
   ```bash
   # Edit .env file with your Gemini API key
   GEMINI_API_KEY="your_gemini_api_key_here"
   ```

3. **Run with Docker Compose**:
   ```bash
   docker-compose up -d
   ```

4. **Verify Installation**:
   ```bash
   curl http://localhost:5000/
   ```

### Local Development

1. **Install Dependencies**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Setup Environment**:
   ```bash
   export GEMINI_API_KEY="your_gemini_api_key_here"
   export REDIS_URL="redis://localhost:6379/0"
   ```

3. **Start Services**:
   ```bash
   # Start Redis (if not running)
   redis-server

   # Start Workers
   python start_worker.py

   # Start API Server
   python main.py
   ```

## API Documentation

### Core Endpoints

#### Document Upload
```bash
POST /upload
Content-Type: multipart/form-data

-F "cv=@cv.pdf"
-F "report=@project_report.pdf"
```
Returns: `{"cv_id": 1, "report_id": 2}`

#### Job Evaluation
```bash
POST /evaluate
Content-Type: application/json

{
  "job_title": "Senior Backend Engineer",
  "documents": [
    {"type": "cv", "id": 1},
    {"type": "project", "id": 2}
  ]
}
```
Returns: `{"job_id": 1, "status": "queued"}`

#### Result Retrieval
```bash
GET /result/1
```
Returns evaluation results when completed.

### Health Check
```bash
GET /health
```
Returns comprehensive system status including AI engine, database, RAG engine, Redis, and system resources.

## Evaluation Parameters

### CV Evaluation (Score: 1-5 each)
- **Technical Skills Match**: Backend, databases, APIs, cloud, AI/LLM exposure
- **Experience Level**: Years, project complexity
- **Relevant Achievements**: Impact, scale of work
- **Cultural Fit**: Communication, learning attitude

### Project Evaluation (Score: 1-5 each)
- **Correctness**: Meets requirements (prompt design, chaining, RAG, error handling)
- **Code Quality**: Clean, modular, testable code
- **Resilience**: Handles failures and retries effectively
- **Documentation**: Clear README and explanation of trade-offs
- **Creativity/Bonus**: Authentication, deployment, dashboards, etc.

## File Structure

```
hr-service/
├── src/
│   ├── api/
│   │   └── routes.py          # Flask API endpoints
│   ├── core/
│   │   ├── ai_engine.py      # AI evaluation logic
│   │   ├── rag_engine.py     # Document processing & RAG
│   │   └── evaluation.py    # Result synthesis
│   ├── models/
│   │   └── database.py       # Database models & operations
│   └── workers/
│       ├── tasks.py          # Celery job processing
│       ├── simple_worker.py # Local fallback worker
│       └── queue_manager.py  # Redis queue management
├── uploads/                 # File storage
├── main.py                  # Application entry point
├── requirements.txt          # Python dependencies
├── docker-compose.yml       # Docker orchestration
├── Dockerfile              # Container definitions
├── .env                    # Environment configuration
└── docs/                   # Documentation
```

## Configuration

### Environment Variables
- `GEMINI_API_KEY`: Required for AI evaluation
- `REDIS_URL`: Redis connection string (default: redis://localhost:6379/0)
- `REDIS_BACKEND`: Redis backend for Celery (default: redis://localhost:6379/1)

### Database Setup
The SQLite database is automatically initialized on first run. No manual setup required.

### Logging
- Comprehensive logging at multiple levels (INFO, DEBUG, ERROR)
- Structured logging with timestamps and process tracking
- Health monitoring and performance metrics

## Deployment Options

### Development
```bash
python main.py
```

### Production
```bash
gunicorn -w 4 -b :5000 main:app
```

### Docker Production
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hr-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: hr-service
  template:
    metadata:
      labels:
        app: hr-service
    spec:
      containers:
      - name: api
        image: hr-service:latest
        ports:
        - containerPort: 5000
        env:
        - name: GEMINI_API_KEY
          valueFrom:
            secretKeyRef:
              name: hr-secrets
              key: gemini-api-key
```

## Monitoring & Health

### Health Check Endpoint
```bash
curl http://localhost:5000/health
```

### System Metrics
- AI Engine availability and response time
- Database connection and record counts
- RAG Engine functionality
- Redis connectivity and memory usage
- System resource utilization

### Log Analysis
- Application logs: `docker logs hr_api`
- Worker logs: `docker logs hr-service-worker-1`
- Redis logs: `docker logs hr_redis`

## Performance Considerations

### Scaling
- **Horizontal Scaling**: Add more worker instances
- **Queue Management**: Redis cluster for high-throughput
- **Database**: PostgreSQL for production scale
- **Caching**: Redis for results and frequently accessed data

### Optimization
- **PDF Processing**: Async extraction for large documents
- **AI Requests**: Batching and retry logic
- **Memory Management**: Cleanup of processed documents
- **Connection Pooling**: Database connection pooling

## Security

### API Security
- Input validation on all endpoints
- File upload size restrictions
- SQL injection prevention
- CORS configuration for cross-origin requests

### Data Protection
- Local file storage with secure filenames
- Encrypted API key storage
- No sensitive data in logs
- Regular cleanup of temporary files

### Production Hardening
- HTTPS enforcement
- Rate limiting considerations
- Authentication & authorization
- Security headers implementation

## Troubleshooting

### Common Issues

1. **AI Service Unavailable**:
   - Check `GEMINI_API_KEY` environment variable
   - Verify internet connectivity
   - Check Gemini API quotas

2. **Redis Connection Failed**:
   - Verify Redis server is running
   - Check connection string in environment
   - Confirm network connectivity

3. **File Upload Issues**:
   - Check file permissions in uploads directory
   - Verify supported file formats (PDF preferred)
   - Check disk space availability

4. **Worker Not Processing**:
   - Check worker logs for errors
   - Verify Redis queue connectivity
   - Restart worker processes

### Debug Mode
Enable detailed logging by setting `DEBUG=True` in main.py.

## Development Guidelines

### Code Style
- Follow PEP 8 standards
- Use type hints where applicable
- Comprehensive docstrings
- Modular code organization

### Testing
- Unit tests for core functionality
- Integration tests for API endpoints
- Load testing for performance validation

### Contribution
- Fork and create feature branches
- Maintain backward compatibility
- Include tests for new features
- Update documentation

## Changelog

### Version 1.2.0
- Added comprehensive logging system
- Fixed ChromaDB compatibility issues
- Implemented Redis-based job processing
- Added health monitoring endpoints
- Disabled linter warnings for cleaner output

### Version 1.1.0
- Initial production-ready release
- Basic AI evaluation pipeline
- Docker containerization
- RESTful API implementation

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Support

For support and questions:
- Check troubleshooting section above
- Review API documentation
- Check system requirements and compatibility