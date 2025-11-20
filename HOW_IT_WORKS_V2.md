# How It Works: Upwork Scraper System v2.0

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Data Flow](#data-flow)
4. [Layer Breakdown](#layer-breakdown)
5. [Scraping Process](#scraping-process)
6. [API Endpoints](#api-endpoints)
7. [Real-time Updates](#real-time-updates)
8. [Database Schema](#database-schema)

---

## System Overview

The Upwork Scraper v2.0 is a refactored, production-ready system that:
- **Scrapes job postings** from Upwork search pages and detail pages
- **Extracts structured data** from complex HTML and JavaScript-rendered content
- **Stores job data** in MongoDB with full relationship tracking (jobs, clients, skills)
- **Provides REST API** for managing URLs, jobs, and scraping operations
- **Streams real-time progress** via Server-Sent Events (SSE)
- **Follows clean architecture** with clear separation of concerns

### Technology Stack
- **Backend Framework**: FastAPI (async Python web framework)
- **Database**: MongoDB with Motor (async driver)
- **Web Scraping**: Scrapfly SDK (bypasses anti-bot measures)
- **Data Extraction**: Custom `upwork_extractor` library
- **Architecture**: Layered architecture (Routes → Services → Repositories)
- **Validation**: Pydantic v2 for models and schemas

---

## Architecture

The system follows a **clean layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                      Routes Layer                            │
│  (API Controllers - HTTP Interface)                          │
│  FastAPI routers handle requests/responses                   │
│  Files: backend/app/routes/                                  │
│  - job_routes.py - Job CRUD operations                      │
│  - url_routes.py - URL management                           │
│  - scraping_routes.py - Scraping endpoints (SSE)            │
│  - health_routes.py - Health checks & monitoring            │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    Services Layer                            │
│  (Business Logic & Orchestration)                            │
│  Coordinates repositories and integrations                   │
│  Files: backend/app/services/                                │
│  - scraping_service.py - Scraping orchestration             │
│  - job_service.py - Job queries and management              │
│  - url_service.py - URL management logic                    │
└─────────┬──────────────────────────────────┬────────────────┘
          │                                  │
┌─────────▼──────────────┐      ┌───────────▼────────────────┐
│  Repositories Layer     │      │  Integrations Layer        │
│  (Data Access)          │      │  (External Services)       │
│  MongoDB operations     │      │  Third-party clients       │
│  backend/app/repos/     │      │  backend/app/integrations/ │
│  - job_repository       │      │  - scrapfly_client         │
│  - client_repository    │      │  - upwork_extractor_client │
│  - skill_repository     │      └────────────────────────────┘
│  - url_repository       │
│  - scrape_run_repository│
└─────────┬───────────────┘
          │
┌─────────▼────────────────────────────────────────────────────┐
│                      Models Layer                             │
│  (Database Models - Pydantic)                                 │
│  backend/app/models/                                          │
│  - job.py - JobModel, JobStatus, BudgetModel, ContentModel   │
│  - client.py - ClientModel                                    │
│  - skill.py - SkillModel                                      │
│  - url.py - SearchURLModel                                    │
│  - scrape_run.py - ScrapeRunModel, ScrapeErrorLog           │
└───────────────────────────────────────────────────────────────┘

Additional Layers:
┌─────────────────────────────────────────────────────────────┐
│  Schemas Layer (DTOs)                                        │
│  API request/response models (separate from DB models)       │
│  backend/app/schemas/                                        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Config Layer                                                │
│  Settings and database management                            │
│  backend/app/config/                                         │
│  - settings.py - Centralized Pydantic settings              │
│  - database.py - MongoDB connection & indexes               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Utils Layer                                                 │
│  Helpers, exceptions, logging                                │
│  backend/app/utils/                                          │
└─────────────────────────────────────────────────────────────┘
```

### Why This Architecture?

1. **Simplicity**: Conventional layered approach that most developers understand
2. **Maintainability**: Each layer has a single responsibility
3. **Testability**: Easy to mock dependencies and test each layer
4. **Scalability**: Clear boundaries make it easy to extract services
5. **Clarity**: Folder structure immediately shows system organization

---

## Data Flow

### Search Scraping Flow

```
1. Client Request
   POST /api/scraping/search/start
   Body: { "url_ids": ["..."], "triggered_by": "api" }
   ↓
2. Routes Layer (scraping_routes.py)
   - Validates request schema
   - Calls ScrapingService
   ↓
3. Services Layer (scraping_service.py)
   - Creates ScrapeRunModel
   - Saves to DB via ScrapeRunRepository
   - Starts SSE generator
   ↓
4. For each SearchURL:
   a) URL Repository fetches URLs
      ↓
   b) Scrapfly Client scrapes HTML
      - Handles JS rendering
      - Bypasses anti-bot measures
      ↓
   c) Upwork Extractor parses HTML
      - Extracts job summaries
      - Returns structured data
      ↓
   d) Job Repository saves jobs
      - Checks for duplicates
      - Creates or updates jobs
      ↓
   e) SSE yields progress event
      - Client receives real-time update
   ↓
5. Final Response
   SSE stream completes with stats
```

### Detail Scraping Flow

```
1. Client Request
   POST /api/scraping/detail/start
   Body: { "job_uids": null, "limit": 50 }
   ↓
2. Routes Layer (scraping_routes.py)
   - Validates request
   - Calls ScrapingService
   ↓
3. Services Layer (scraping_service.py)
   - Gets discovered jobs via JobRepository
   - Creates ScrapeRunModel
   ↓
4. For each Job:
   a) Scrapfly Client scrapes detail page
      ↓
   b) Upwork Extractor extracts full data
      - Job details
      - Client information
      - Skills list
      ↓
   c) Multi-repository transaction:
      - ClientRepository.upsert() - Save/update client
      - SkillRepository.upsert() - Save/update skills
      - JobRepository.update() - Enrich job data
      ↓
   d) Update job status to ENRICHED
      ↓
   e) SSE yields progress event
   ↓
5. Final Response
   SSE stream completes with enrichment stats
```

### Job Query Flow

```
1. Client Request
   GET /api/jobs?q=python&status=enriched&page=1&page_size=50
   ↓
2. Routes Layer (job_routes.py)
   - Validates query parameters
   - Calls JobService
   ↓
3. Services Layer (job_service.py)
   - Converts status string to enum
   - Calculates pagination
   - Calls JobRepository
   ↓
4. Repository Layer (job_repository.py)
   - Builds MongoDB filter
   - Executes aggregation pipeline
   - Returns jobs + total count
   ↓
5. Routes Layer formats response
   Returns JobListResponse with pagination
```

---

## Layer Breakdown

### 1. Routes Layer (`backend/app/routes/`)

**Purpose**: Handle HTTP requests and responses

**Files**:
- `job_routes.py` - Job CRUD, search, stats
- `url_routes.py` - URL management
- `scraping_routes.py` - Start scraping, SSE streaming
- `health_routes.py` - Health checks, monitoring

**Responsibilities**:
- Request validation (Pydantic schemas)
- Response formatting
- HTTP status codes
- Error handling

**Example**:
```python
@router.get("/api/jobs/{uid}")
async def get_job(uid: str):
    job = await job_service.get_job_by_uid(uid)
    if not job:
        raise HTTPException(status_code=404)
    return JobDetailResponse(job=job)
```

### 2. Services Layer (`backend/app/services/`)

**Purpose**: Business logic and orchestration

**Files**:
- `scraping_service.py` - Orchestrates scraping workflows
- `job_service.py` - Job queries and management
- `url_service.py` - URL management logic

**Responsibilities**:
- Coordinate multiple repositories
- Implement business rules
- Handle transactions
- Emit SSE events

**Example**:
```python
class ScrapingService:
    async def start_search_scrape(self, url_ids):
        # 1. Create scrape run
        scrape_run = ScrapeRunModel(run_type="search")
        await self.scrape_run_repo.create(scrape_run)

        # 2. Get URLs
        urls = await self.url_repo.find_by_ids(url_ids)

        # 3. Scrape each URL
        for url in urls:
            html = await self.scrapfly.scrape_search_page(url)
            jobs = self.extractor.extract_search_results(html)

            # 4. Save jobs
            for job_data in jobs:
                await self._process_search_job(job_data)

        # 5. Complete run
        await self.scrape_run_repo.update_status(scrape_run.run_id, "completed")
```

### 3. Repositories Layer (`backend/app/repositories/`)

**Purpose**: Data access and persistence

**Files**:
- `job_repository.py` - Job CRUD and queries
- `client_repository.py` - Client operations
- `skill_repository.py` - Skill operations
- `url_repository.py` - URL operations
- `scrape_run_repository.py` - Scrape run tracking

**Responsibilities**:
- MongoDB operations
- Query building
- Index usage
- Aggregation pipelines

**Example**:
```python
class JobRepository:
    async def search(self, query, status, skip, limit):
        filters = {}
        if query:
            filters["$or"] = [
                {"title": {"$regex": query, "$options": "i"}},
                {"content.description_plain": {"$regex": query, "$options": "i"}}
            ]
        if status:
            filters["status"] = status.value

        total = await self.collection.count_documents(filters)
        cursor = self.collection.find(filters).skip(skip).limit(limit)
        jobs = await cursor.to_list(length=limit)

        return jobs, total
```

### 4. Integrations Layer (`backend/app/integrations/`)

**Purpose**: External service clients

**Files**:
- `scrapfly_client.py` - Scrapfly SDK wrapper
- `upwork_extractor_client.py` - Data extraction wrapper

**Responsibilities**:
- API calls to external services
- Rate limiting
- Retry logic
- Error handling

**Example**:
```python
class ScrapflyClient:
    async def scrape_search_page(self, url):
        config = ScrapeConfig(
            url=url,
            render_js=True,
            asp=True,
            wait_for_selector="div[data-test='job-tile']"
        )
        result = await self._client.async_scrape(config)
        return result.content
```

### 5. Models Layer (`backend/app/models/`)

**Purpose**: Database models

**Files**: `job.py`, `client.py`, `skill.py`, `url.py`, `scrape_run.py`

**Key Models**:

**JobModel**:
```python
class JobModel(BaseModel):
    uid: str  # Unique identifier
    title: str
    url: Optional[HttpUrl]
    status: JobStatus  # discovered, scraping_detail, enriched
    content: ContentModel  # description, skills
    budget: BudgetModel  # type, min, max
    client_id: Optional[str]
    pipeline: PipelineModel  # discovered_at, detail_scraped_at
```

**ClientModel**:
```python
class ClientModel(BaseModel):
    client_key: str  # Unique deduplication key
    country: Optional[str]
    company: Optional[str]
    total_spent: Optional[float]
    payment_verified: bool
    total_jobs: int
```

**ScrapeRunModel**:
```python
class ScrapeRunModel(BaseModel):
    run_id: str
    run_type: str  # "search" or "detail"
    status: str  # pending, running, completed, failed
    jobs_found: int
    jobs_new: int
    jobs_updated: int
    errors: List[ScrapeErrorLog]
    progress_percentage: float
```

### 6. Schemas Layer (`backend/app/schemas/`)

**Purpose**: API request/response DTOs

**Why separate from models?**
- Database models may have fields not exposed in API
- API may need different validation rules
- Allows API evolution without changing DB schema

**Files**: `job.py`, `url.py`, `scraping.py`

**Example**:
```python
class JobSearchQuery(BaseModel):
    q: Optional[str]
    status: Optional[str]
    page: int = 1
    page_size: int = 50

class JobListResponse(BaseModel):
    jobs: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int
```

### 7. Config Layer (`backend/app/config/`)

**Purpose**: Configuration management

**Files**:
- `settings.py` - Centralized settings (Pydantic BaseSettings)
- `database.py` - MongoDB connection manager

**Settings Example**:
```python
class Settings(BaseSettings):
    MONGODB_URI: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "upwork_stable"
    SCRAPFLY_API_KEY: str
    MAX_CONCURRENT_REQUESTS: int = 5

    class Config:
        env_file = ".env"
```

**Database Manager**:
```python
class DatabaseManager:
    @classmethod
    async def connect(cls):
        cls._client = AsyncIOMotorClient(settings.MONGODB_URI)
        cls._db = cls._client[settings.DATABASE_NAME]
        await cls._create_indexes()

    @classmethod
    async def run_in_transaction(cls, operations_callback):
        async with session.start_transaction():
            return await operations_callback(session)
```

---

## Scraping Process

### Phase 1: Search Page Scraping

**Purpose**: Discover new jobs from search results

**Steps**:
1. **Fetch URLs**: Get enabled search URLs from database
2. **Scrape HTML**: Use Scrapfly to render JavaScript and fetch HTML
3. **Extract Jobs**: Parse HTML to extract job summaries
4. **Save Jobs**: Create new jobs with status=DISCOVERED
5. **Update Stats**: Track jobs found, new, updated

**Status Transitions**:
```
[New Job] → DISCOVERED
[Existing Job] → (status unchanged, update timestamp)
```

### Phase 2: Detail Page Scraping

**Purpose**: Enrich discovered jobs with full details

**Steps**:
1. **Find Jobs**: Get jobs with status=DISCOVERED
2. **Scrape Details**: Fetch and render detail pages
3. **Extract Data**: Parse full job details, client info, skills
4. **Upsert Relationships**:
   - Client → ClientRepository.upsert()
   - Skills → SkillRepository.upsert() + increment job_count
5. **Update Job**: Add detail data, set status=ENRICHED
6. **Handle Errors**: Set status=DETAIL_FAILED or EXTRACTION_FAILED

**Status Transitions**:
```
DISCOVERED → SCRAPING_DETAIL → ENRICHED
                             ↓
                    DETAIL_FAILED / EXTRACTION_FAILED
```

### Anti-Bot Bypass

**Scrapfly Features Used**:
- **ASP (Anti-Scraping Protection)**: Rotates proxies and headers
- **JavaScript Rendering**: Executes client-side code
- **Wait for Selector**: Ensures dynamic content loads
- **Retry Logic**: Exponential backoff on failures

---

## API Endpoints

### Jobs API

```
GET    /api/jobs                    # Search jobs
GET    /api/jobs/{uid}              # Get job details
GET    /api/jobs/{uid}/related      # Get related jobs
GET    /api/jobs/stats              # Job statistics
DELETE /api/jobs/{uid}              # Delete job
PATCH  /api/jobs/{uid}/status       # Update status
POST   /api/jobs/bulk/status        # Bulk update
```

### URLs API

```
GET    /api/urls                    # List URLs
GET    /api/urls/{id}               # Get URL
GET    /api/urls/enabled            # Get enabled URLs
GET    /api/urls/stats              # URL statistics
POST   /api/urls                    # Create URL
PATCH  /api/urls/{id}               # Update URL
DELETE /api/urls/{id}               # Delete URL
POST   /api/urls/{id}/toggle        # Toggle enabled
```

### Scraping API

```
POST   /api/scraping/search/start   # Start search scrape (SSE)
POST   /api/scraping/detail/start   # Start detail scrape (SSE)
GET    /api/scraping/runs/recent    # Recent runs
GET    /api/scraping/runs/{id}      # Run details
GET    /api/scraping/runs/stats     # Scraping stats
GET    /api/scraping/status/active  # Active runs
```

### Health API

```
GET    /api/health                  # Basic health check
GET    /api/health/ready            # Readiness probe
GET    /api/health/live             # Liveness probe
GET    /api/health/stats            # System statistics
GET    /api/health/config           # Configuration
```

---

## Real-time Updates

### Server-Sent Events (SSE)

**Endpoints**:
- `POST /api/scraping/search/start` - Search scraping stream
- `POST /api/scraping/detail/start` - Detail scraping stream

**Event Types**:

**Search Scraping**:
```javascript
// Run started
event: run_started
data: {"run_id": "...", "run_type": "search", "status": "running"}

// URL processing
event: url_started
data: {"url_id": "...", "url": "...", "progress": 0.25}

event: url_completed
data: {"url_id": "...", "jobs_found": 50, "jobs_new": 12, "jobs_updated": 38}

// Run completed
event: run_completed
data: {"run_id": "...", "status": "completed", "jobs_found": 200, "jobs_new": 45}
```

**Detail Scraping**:
```javascript
// Job processing
event: job_started
data: {"job_uid": "...", "progress": 0.5}

event: job_completed
data: {"job_uid": "..."}

// Run completed
event: run_completed
data: {"run_id": "...", "jobs_updated": 50, "jobs_failed": 2}
```

**Client Implementation**:
```javascript
const eventSource = new EventSource('/api/scraping/search/start');

eventSource.addEventListener('run_started', (e) => {
  const data = JSON.parse(e.data);
  console.log('Scraping started:', data.run_id);
});

eventSource.addEventListener('url_completed', (e) => {
  const data = JSON.parse(e.data);
  console.log('URL done:', data.jobs_found, 'jobs');
});

eventSource.addEventListener('run_completed', (e) => {
  const data = JSON.parse(e.data);
  console.log('Scraping complete:', data);
  eventSource.close();
});
```

---

## Database Schema

### Collections

**jobs**:
```javascript
{
  "_id": ObjectId,
  "uid": "1234567890abcdef",  // Upwork job ID
  "title": "Python Developer Needed",
  "url": "https://www.upwork.com/jobs/...",
  "status": "enriched",
  "run_id": "uuid",
  "ciphertext": "~abc123",
  "content": {
    "description": "<html>...",
    "description_plain": "We are looking for...",
    "skill_ids": ["python", "fastapi"],
    "skills": [
      {"uid": "python", "name": "Python", "category": "Web Development"}
    ]
  },
  "budget": {
    "available": true,
    "type": "hourly",
    "min": 50,
    "max": 100,
    "currency": "USD"
  },
  "client_id": ObjectId,
  "experience_level": "Expert",
  "duration": "More than 6 months",
  "pipeline": {
    "source": "search",
    "is_enriched": true,
    "discovered_at": ISODate,
    "detail_scraped_at": ISODate
  },
  "created_at": ISODate,
  "updated_at": ISODate
}
```

**Indexes**:
- `uid` (unique)
- `status`
- `client_id`
- `content.skill_ids`
- `created_at`

**clients**:
```javascript
{
  "_id": ObjectId,
  "client_key": "us_company_name",  // Deduplication key
  "country": "United States",
  "company": "Company Name",
  "total_spent": 50000.00,
  "payment_verified": true,
  "total_jobs": 15,
  "created_at": ISODate
}
```

**Indexes**:
- `client_key` (unique)

**skills**:
```javascript
{
  "_id": ObjectId,
  "uid": "python",
  "name": "Python",
  "pretty_name": "Python",
  "job_count": 1523,
  "first_seen_at": ISODate,
  "last_seen_at": ISODate
}
```

**Indexes**:
- `uid` (unique)
- `job_count`

**search_urls**:
```javascript
{
  "id": "uuid",
  "url": "https://www.upwork.com/nx/search/jobs/?q=python",
  "name": "Python Jobs",
  "enabled": true,
  "total_scrapes": 42,
  "total_jobs_found": 2100,
  "last_scraped_at": ISODate
}
```

**scrape_runs**:
```javascript
{
  "run_id": "uuid",
  "run_type": "search",
  "status": "completed",
  "triggered_by": "api",
  "jobs_found": 200,
  "jobs_new": 45,
  "jobs_updated": 155,
  "jobs_failed": 0,
  "progress_percentage": 100.0,
  "errors": [],
  "started_at": ISODate,
  "completed_at": ISODate,
  "duration_seconds": 125.5
}
```

---

## Key Improvements in v2.0

1. **Simpler Architecture**: Moved from Hexagonal to conventional layered architecture
2. **Better Organization**: Clear folder structure (routes, services, repositories)
3. **Separation of Concerns**: DTOs separate from database models
4. **Centralized Config**: Pydantic Settings for all configuration
5. **Database Management**: Dedicated DatabaseManager with connection pooling
6. **Error Handling**: Custom exceptions and comprehensive error tracking
7. **Monitoring**: Health checks and statistics endpoints
8. **Documentation**: Inline docstrings and comprehensive README

---

This architecture makes the codebase:
- **Easy to understand** for new developers
- **Easy to test** with clear dependency injection
- **Easy to maintain** with single-responsibility layers
- **Easy to extend** with new features and endpoints
