# Drug Discovery AI Agent - Backend

A sophisticated, production-ready Flask-based backend for the Drug Discovery AI Agent, featuring advanced AI integration, comprehensive API endpoints, and enterprise-grade architecture.

## 🏗️ Architecture

The backend is organized into a modular, scalable architecture:

```
backend/
├── config/           # Configuration management
├── models/           # Pydantic data models and validation
├── services/         # Business logic services
├── api/             # API route handlers
├── middleware/      # Flask middleware (auth, rate limiting, logging)
├── database/        # Database models and connections
├── utils/           # Utility functions
├── tasks/           # Background task processing (Celery)
├── tests/           # Comprehensive test suite
└── docs/            # API documentation
```

## 🚀 Features

### Core Functionality
- **Multi-Agent AI Support**: Groq, Gemini, and LangChain agents
- **Comprehensive Data Sources**: PubMed, PDB, PubChem, NCBI, ChEMBL
- **Advanced RAG System**: FAISS/ChromaDB vector search
- **Real-time Processing**: Asynchronous task handling
- **Session Management**: User session tracking and memory

### Enterprise Features
- **Rate Limiting**: Configurable request limits per endpoint
- **Authentication**: JWT-based auth system (extensible)
- **Caching**: Redis-based response caching
- **Logging**: Structured logging with multiple handlers
- **Monitoring**: Health checks and metrics endpoints
- **Database**: SQLAlchemy ORM with migration support
- **API Documentation**: Auto-generated OpenAPI/Swagger docs

### Developer Experience
- **Type Safety**: Full Pydantic model validation
- **Testing**: Comprehensive pytest test suite
- **Docker Support**: Containerized deployment
- **Code Quality**: Black, flake8, mypy integration
- **Hot Reload**: Development server with auto-reload

## 📋 Prerequisites

- Python 3.11+
- Redis (for caching and background tasks)
- PostgreSQL (optional, for production database)

## 🛠️ Installation

### Local Development

1. **Clone and setup**:
```bash
cd app/backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Environment variables**:
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. **Database setup**:
```bash
# SQLite (default)
python -c "from database import db_manager; db_manager.engine.execute('SELECT 1')"
```

4. **Run the application**:
```bash
# Development
python app.py
```
## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Environment (development/production) | development |
| `GROQ_API_KEY` | Groq API key | - |
| `GEMINI_API_KEY` | Google Gemini API key | - |
| `DATABASE_URL` | Database connection URL | sqlite:///drug_discovery.db |
| `REDIS_URL` | Redis connection URL | redis://localhost:6379 |
| `SECRET_KEY` | Flask secret key | auto-generated |
| `LOG_LEVEL` | Logging level | INFO |

### Rate Limiting

Configure rate limits in `config/__init__.py`:

```python
rate_limit_config = RateLimitConfig(
    enabled=True,
    default_limits={
        "chat": 100,      # requests per hour
        "search": 500,
        "download": 50
    }
)
```

## 📚 API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/config` | System configuration |
| `POST` | `/api/chat` | Process chat messages |
| `GET` | `/api/agents` | List available agents |
| `POST` | `/api/rag` | Search RAG database |
| `POST` | `/api/compounds` | Search compounds |
| `POST` | `/api/papers` | Search research papers |
| `GET` | `/api/memory` | Get agent memory |

### Request/Response Examples

#### Chat Request
```json
{
  "message": "Find drugs for Alzheimer's disease",
  "agentType": "groq",
  "session_id": "optional-session-id"
}
```

#### Chat Response
```json
{
  "response": "Based on recent research...",
  "thought_process": [
    {
      "step": 1,
      "content": "Analyzing query for drug discovery research",
      "timestamp": "2024-01-01T10:00:00Z"
    }
  ],
  "actions": [
    {
      "tool": "PubMed API",
      "input": "Alzheimer's disease drugs",
      "result": "Found 1256 papers",
      "duration": 0.45,
      "success": true
    }
  ],
  "observations": [
    {
      "content": "Strong literature base available",
      "confidence": 0.95
    }
  ],
  "metadata": {
    "topic": "Alzheimer's disease",
    "pubmed_count": 1256,
    "pdb_count": 45,
    "processing_time": 2.34,
    "timestamp": "2024-01-01T10:00:02Z"
  },
  "status": "success"
}
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_api.py

# Run tests in verbose mode
pytest -v
```

## 📊 Monitoring

### Health Checks

```bash
# Overall health
curl http://localhost:5001/api/health

# Detailed metrics
curl http://localhost:5001/api/admin/stats
```

### Logging

Logs are structured and include:
- Request/response logging
- Error tracking
- Performance metrics
- Security events

## 🔒 Security

- **Input Validation**: All inputs validated with Pydantic
- **Rate Limiting**: Prevents abuse
- **CORS**: Configured for frontend origins
- **Security Headers**: XSS protection, content type sniffing prevention
- **API Keys**: Securely stored and validated

## 🚀 Deployment

### Production Checklist

- [ ] Set `FLASK_ENV=production`
- [ ] Configure production database
- [ ] Set up Redis for caching
- [ ] Configure reverse proxy (nginx)
- [ ] Set up SSL certificates
- [ ] Configure monitoring (Prometheus/Grafana)
- [ ] Set up log aggregation
- [ ] Configure backup strategy

### Docker Production

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  backend:
    image: drug-discovery-backend:latest
    environment:
      - FLASK_ENV=production
    secrets:
      - groq_api_key
      - gemini_api_key
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

### Code Quality

```bash
# Format code
black .

# Lint code
flake8 .

# Type check
mypy .

# Run pre-commit hooks
pre-commit run --all-files
```

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Issues**: GitHub Issues
- **Documentation**: `/docs` directory
- **API Docs**: `/api/docs` (when running)

## 🔄 Version History

- **v2.0.0**: Complete architecture overhaul
  - Modular design
  - Advanced AI integration
  - Production-ready features
  - Comprehensive testing

- **v1.0.0**: Initial release
  - Basic Flask API
  - Core AI functionality
  - Simple data integration