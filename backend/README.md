# Upwork Scraper Backend

A modern, maintainable FastAPI-based backend for scraping and managing Upwork job listings.

## Architecture

This project follows a clean, layered architecture with clear separation of concerns:

```
backend/
├── app/
│   ├── config/          # Configuration management
│   ├── models/          # Database models (Pydantic)
│   ├── schemas/         # API request/response DTOs
│   ├── repositories/    # Data access layer
│   ├── services/        # Business logic layer
│   ├── routes/          # API endpoints (controllers)
│   ├── integrations/    # External service clients
│   ├── utils/           # Utilities and helpers
│   └── main.py          # Application entry point
├── requirements.txt     # Python dependencies
└── .env.example         # Environment variables template
```

## Features

- **2-Phase Scraping**: Search page discovery → Detail page enrichment
- **Real-time Updates**: Server-Sent Events (SSE) for live scraping progress
- **Anti-bot Bypass**: Scrapfly integration for reliable scraping
- **MongoDB Storage**: Async MongoDB with Motor driver
- **RESTful API**: Complete CRUD operations for jobs and URLs
- **Statistics**: Comprehensive stats and monitoring endpoints
- **Health Checks**: Kubernetes-ready health and readiness probes

## Getting Started

### Prerequisites

- Python 3.9+
- MongoDB 4.4+
- Scrapfly API key

### Installation

1. Clone the repository:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run the application:
```bash
python -m app.main
```

Or using uvicorn directly:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## API Endpoints

### Jobs

- `GET /api/jobs` - Search and filter jobs
- `GET /api/jobs/{uid}` - Get job details
- `GET /api/jobs/{uid}/related` - Get related jobs
- `GET /api/jobs/stats` - Get job statistics
- `DELETE /api/jobs/{uid}` - Delete job
- `PATCH /api/jobs/{uid}/status` - Update job status
- `POST /api/jobs/bulk/status` - Bulk update statuses

### Search URLs

- `GET /api/urls` - List search URLs
- `GET /api/urls/{id}` - Get URL details
- `GET /api/urls/enabled` - Get enabled URLs
- `GET /api/urls/stats` - Get URL statistics
- `POST /api/urls` - Create new URL
- `PATCH /api/urls/{id}` - Update URL
- `DELETE /api/urls/{id}` - Delete URL
- `POST /api/urls/{id}/toggle` - Toggle URL status

### Scraping

- `POST /api/scraping/search/start` - Start search scraping (SSE stream)
- `POST /api/scraping/detail/start` - Start detail scraping (SSE stream)
- `GET /api/scraping/runs/recent` - Get recent scrape runs
- `GET /api/scraping/runs/{id}` - Get scrape run details
- `GET /api/scraping/runs/stats` - Get scraping statistics
- `GET /api/scraping/status/active` - Get active scrape runs

### Health & Monitoring

- `GET /api/health` - Basic health check
- `GET /api/health/ready` - Readiness probe
- `GET /api/health/live` - Liveness probe
- `GET /api/health/stats` - System statistics
- `GET /api/health/config` - Current configuration

## Environment Variables

See `.env.example` for all available configuration options.

### Required Variables

- `MONGODB_URI` - MongoDB connection string
- `DATABASE_NAME` - Database name
- `SCRAPFLY_API_KEY` - Scrapfly API key

### Optional Variables

- `HOST` - Server host (default: 0.0.0.0)
- `PORT` - Server port (default: 8000)
- `DEBUG` - Debug mode (default: false)
- `LOG_LEVEL` - Logging level (default: INFO)
- `MAX_CONCURRENT_REQUESTS` - Max concurrent scrape requests (default: 5)

## Project Structure Explained

### Config Layer (`app/config/`)
- `settings.py` - Centralized settings using Pydantic
- `database.py` - MongoDB connection and index management

### Models Layer (`app/models/`)
- Database models using Pydantic
- Core entities: Job, Client, Skill, SearchURL, ScrapeRun

### Schemas Layer (`app/schemas/`)
- API request/response DTOs
- Separate from database models for clean API contracts

### Repositories Layer (`app/repositories/`)
- Data access layer
- All MongoDB operations
- Query builders and aggregations

### Services Layer (`app/services/`)
- Business logic orchestration
- Coordinates repositories and integrations
- Transaction management

### Routes Layer (`app/routes/`)
- API endpoint definitions
- Request validation
- Response formatting

### Integrations Layer (`app/integrations/`)
- External service clients
- Scrapfly for web scraping
- Upwork Extractor for data extraction

### Utils Layer (`app/utils/`)
- Custom exceptions
- Logging configuration
- Helper functions
- Validators

## Data Flow

### Search Scraping Flow
1. API receives request → `scraping_routes.py`
2. Service orchestrates → `scraping_service.py`
3. Scrapfly scrapes HTML → `scrapfly_client.py`
4. Extractor parses data → `upwork_extractor_client.py`
5. Repository saves → `job_repository.py`
6. SSE streams progress → Client

### Detail Scraping Flow
1. Service fetches discovered jobs → `job_repository.py`
2. Scrapfly scrapes detail pages → `scrapfly_client.py`
3. Extractor enriches data → `upwork_extractor_client.py`
4. Service updates jobs, clients, skills → Multiple repositories
5. Transaction ensures atomicity → `database.py`

## Development

### Code Style

This project uses:
- Black for code formatting
- Ruff for linting

Run formatters:
```bash
black app/
ruff check app/ --fix
```

### Testing

```bash
pytest
```

### Database Indexes

Indexes are automatically created on startup by `DatabaseManager`. See `backend/app/config/database.py:96`.

## Deployment

### Using Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app/ ./app/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables in Production

Never commit `.env` files. Use:
- Docker secrets
- Kubernetes ConfigMaps/Secrets
- Cloud provider secret management

## Monitoring

The API provides comprehensive monitoring endpoints:

- `/api/health/stats` - Complete system statistics
- `/api/health/ready` - Database connectivity check
- Structured logging for observability

## License

See LICENSE file for details.
