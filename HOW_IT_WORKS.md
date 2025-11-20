# How It Works: Upwork Scraper System

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Data Flow](#data-flow)
4. [Key Components](#key-components)
5. [Scraping Process](#scraping-process)
6. [Data Extraction](#data-extraction)
7. [API Endpoints](#api-endpoints)
8. [Real-time Updates](#real-time-updates)
9. [Configuration](#configuration)

---

## System Overview

The Upwork Scraper is a production-ready system that:
- **Scrapes job postings** from Upwork search pages and detail pages
- **Extracts structured data** from complex HTML and JavaScript-rendered content
- **Stores job data** in MongoDB with full relationship tracking (jobs, clients, skills)
- **Provides REST API** for managing URLs, jobs, and scraping operations
- **Streams real-time progress** via Server-Sent Events (SSE)
- **Validates data quality** at multiple levels

### Technology Stack
- **Backend Framework**: FastAPI (async Python web framework)
- **Database**: MongoDB (document-oriented NoSQL)
- **Web Scraping**: Scrapfly API (bypasses anti-bot measures)
- **Data Extraction**: Custom `upwork_extractor` library
- **Architecture**: Hexagonal (Ports & Adapters)

---

## Architecture

The system follows **Hexagonal Architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                        API Layer                             │
│  (FastAPI Controllers - HTTP Interface)                      │
│  - job_controller.py                                         │
│  - url_controller.py                                         │
│  - scraping_controller.py                                    │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                   Application Layer                          │
│  (Business Logic & Use Cases)                                │
│  - ScrapingOrchestrationService                             │
│  - URLManagementService                                      │
│  - JobQueryService                                           │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                     Domain Layer                             │
│  (Core Business Models & Abstract Interfaces)                │
│  - JobModel, ClientModel, SkillModel                        │
│  - AbstractJobRepository, AbstractScrapingAdapter           │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                 Infrastructure Layer                         │
│  (Concrete Implementations)                                  │
│  - MongoJobRepository (MongoDB adapter)                     │
│  - ScrapflyClient (Web scraping adapter)                    │
│  - UpworkExtractorAdapter (Data extraction adapter)         │
└─────────────────────────────────────────────────────────────┘
```

### Why Hexagonal Architecture?

1. **Testability**: Core business logic has no dependencies on external systems
2. **Flexibility**: Easy to swap MongoDB for PostgreSQL or Scrapfly for another service
3. **Maintainability**: Changes in infrastructure don't affect business logic
4. **Clear Dependencies**: Dependencies point inward (infrastructure depends on domain, not vice versa)

---

## Data Flow

### Complete Scraping Flow

```
1. User Request (API)
   POST /api/scraping/search/start
   ↓
2. ScrapingOrchestrationService
   - Creates ScrapeRunModel
   - Stores in MongoDB
   - Launches background task
   ↓
3. For each SearchURL:
   a) ScrapflyClient.fetch()
      - Fetches HTML with proxy rotation
      - Handles JS rendering
      - Returns HTML content
   ↓
   b) UpworkExtractorAdapter.extract_search_job_summaries()
      - Parses __NUXT_DATA__ JSON
      - Extracts job summaries
      - Returns structured data
   ↓
   c) MongoJobRepository.add()
      - Stores/updates jobs in DB
      - Links to skills & clients
      - Tracks pipeline status
   ↓
   d) SSEManager.send_progress()
      - Streams progress to connected clients
      - Real-time updates
   ↓
4. Complete
   - Updates ScrapeRunModel status
   - Sends completion event via SSE
```

### Detail Enrichment Flow

```
1. Find jobs needing enrichment
   - JobRepository.find_jobs_needing_detail()
   - Status: 'discovered' → 'scraping_detail'
   ↓
2. For each job:
   a) Fetch detail page HTML (ScrapflyClient)
   ↓
   b) Extract complete data (UpworkExtractorAdapter)
      - Parse __NUXT_DATA__
      - Extract from HTML elements
      - Validate with Schema.org
   ↓
   c) Store enriched data
      - Upsert ClientModel
      - Upsert SkillModels
      - Update JobModel
      - Status: 'scraping_detail' → 'enriched'
   ↓
3. Track in transaction
   - All updates atomic per job
   - Rollback on failure
```

---

## Key Components

### 1. ScrapingOrchestrationService

**Purpose**: Coordinates the entire scraping workflow

**Key Methods**:
```python
async def start_search_scrape(command: StartSearchScrapeCommand)
    # Initiates search page scraping
    # - Validates no concurrent runs
    # - Creates ScrapeRunModel
    # - Launches background task

async def start_detail_scrape_batch(command: StartDetailScrapeCommand)
    # Batch enriches job details
    # - Finds jobs needing enrichment
    # - Scrapes details in parallel
    # - Updates jobs transactionally

async def _process_single_job_detail(job_uid, job_url, scrape_run_id)
    # Scrapes one job detail page
    # - Fetches HTML
    # - Extracts data
    # - Stores in DB
```

**Responsibilities**:
- Concurrency control (prevent duplicate runs)
- Error handling and retry logic
- Progress tracking via SSE
- Transaction management

### 2. ScrapflyClient

**Purpose**: Handles web scraping with anti-bot bypass

**Features**:
- **API Key Rotation**: Automatically switches keys when rate-limited
- **Intelligent Retries**: Exponential backoff with retry budget
- **File-based Caching**: Avoids redundant scrapes
- **Large Object Handling**: Auto-downloads clob/blob responses
- **Content Validation**: Detects CAPTCHA/blocks

**Key Method**:
```python
async def fetch(
    url: str,
    render_js: bool = True,
    country: str = "us",
    asp: bool = True,
    rendering_wait_ms: int = 3000,
    ...
) -> Dict[str, Any]:
    # Returns: {"success": True, "html": "...", "metadata": {...}}
```

### 3. UpworkExtractorAdapter

**Purpose**: Wrapper around the standalone `upwork_extractor` library

**Core Extraction Flow**:
```python
# 1. Initialize with HTML
extractor = UpworkDataExtractor(html_content, config)

# 2. Extract data (automatic source priority)
job_data = extractor.extract()

# 3. Returns UpworkJobData (Pydantic model) with:
- title, description, uid
- budget, duration, experience_level
- client info, activity metrics
- skills, qualifications
- data_quality report
```

**Extraction Strategy** (in upwork_extractor library):
1. **NUXT_DATA__ parsing** (primary source - most reliable)
2. **HTML element extraction** (fallback/enrichment)
3. **Schema.org validation** (quality check)

### 4. MongoDB Repositories

**Pattern**: Each domain model has a dedicated repository

```python
# Example: MongoJobRepository
class MongoJobRepository(AbstractJobRepository):
    async def get_by_uid(self, uid: str) -> Optional[JobModel]
    async def add(self, job_model: JobModel) -> str
    async def update(self, uid: str, updates: Dict) -> JobModel
    async def find_jobs_needing_detail(self, limit: int) -> List[JobModel]
```

**Features**:
- Automatic index management
- Transaction support
- Aggregation pipelines for statistics
- Reference resolution (skills, clients)

### 5. SSEManager

**Purpose**: Real-time progress streaming via Server-Sent Events

**How it works**:
```python
# 1. Client connects to SSE endpoint
GET /api/scraping/status/{run_id}/stream

# 2. Server establishes SSE connection
async def event_generator():
    queue = await sse_manager.connect(run_id)
    while True:
        update = await queue.get()
        yield f"data: {json.dumps(update)}\n\n"

# 3. Service sends updates
await sse_manager.send_progress(run_id, {
    "status": "scraping_search_page",
    "current_page": 2,
    "jobs_found": 50
})

# 4. Client receives real-time updates
EventSource automatically reconnects on disconnect
```

---

## Scraping Process

### Search Page Scraping (2-Phase)

#### Phase 1: URL Discovery
```python
# 1. Get enabled URLs
urls = await url_repo.list_for_scraping(min_interval_minutes=1440)

# 2. For each URL, scrape all pages
for url_model in urls:
    page = 1
    has_more = True

    while has_more:
        # Fetch page
        html = await scrapfly_client.fetch(
            url=f"{url}?page={page}",
            render_js=True,
            asp=True
        )

        # Extract jobs
        jobs = await extractor.extract_search_job_summaries(html)

        # Store in DB
        for job in jobs:
            await job_repo.add(job)  # Status: 'discovered'

        page += 1
        has_more = len(jobs) >= 50  # Heuristic for pagination
```

#### Phase 2: Detail Enrichment
```python
# 1. Find jobs needing enrichment
jobs = await job_repo.find_jobs_needing_detail(
    limit=50,
    max_retries=3
)

# 2. Scrape each job's detail page
for job in jobs:
    # Update status
    await job_repo.update(job.uid, {"status": "scraping_detail"})

    # Fetch detail page
    html = await scrapfly_client.fetch(
        url=f"https://www.upwork.com/jobs/~{job.ciphertext}",
        render_js=True
    )

    # Extract complete data
    extracted = await extractor.extract_job_detail(html)

    # Store enriched data
    await job_repo.update(job.uid, extracted)
    await job_repo.update(job.uid, {"status": "enriched"})
```

### Concurrency & Rate Limiting

```python
# Controlled parallelism
MAX_CONCURRENT_REQUESTS = 5
semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

async def scrape_with_semaphore(job):
    async with semaphore:
        return await scrape_single_job(job)

# Process all jobs in parallel (but max 5 at once)
results = await asyncio.gather(*[
    scrape_with_semaphore(job) for job in jobs
])
```

---

## Data Extraction

### The `upwork_extractor` Library

This is a **standalone extraction library** with zero coupling to the scraper backend.

#### Key Classes

**1. UpworkDataExtractor** (Orchestrator)
```python
extractor = UpworkDataExtractor(html_content, config)
job_data = extractor.extract()  # Returns UpworkJobData
```

**2. NuxtParser** (Primary Source)
```python
# Extracts from __NUXT_DATA__ JSON
# - Resolves integer references recursively
# - Finds root data object
# - Populates job, client, skills, activity
```

**3. HtmlParser** (Fallback/Enrichment)
```python
# Extracts from HTML elements using robust selectors
# - data-qa attributes (most stable)
# - Semantic selectors
# - Regex patterns for text extraction
```

**4. SchemaParser** (Validation)
```python
# Parses Schema.org JSON-LD
# - Validates extracted data
# - Detects mismatches
# - Logs quality issues
```

#### Extraction Priority

```
1. NUXT_DATA__ (highest priority)
   ↓ (if missing/incomplete)
2. HTML Elements (fallback)
   ↓ (always runs)
3. Schema.org (validation only)
```

#### Data Quality Tracking

Every extraction produces a `DataQuality` report:
```json
{
  "warnings": ["NUXT client object not found"],
  "validation_issues": [
    {
      "field_name": "hourly_rate",
      "reason": "Min > Max",
      "severity": "warning"
    }
  ],
  "source_coverage": {
    "title": "nuxt",
    "description": "html",
    "budget": "nuxt"
  },
  "schema_mismatches": [],
  "summary": {
    "total_warnings": 1,
    "error_count": 0,
    "fields_extracted": 45
  }
}
```

---

## API Endpoints

### URL Management

```http
GET    /api/urls              # List all search URLs
POST   /api/urls              # Add new search URL
GET    /api/urls/{id}         # Get specific URL
PATCH  /api/urls/{id}         # Update URL
DELETE /api/urls/{id}         # Delete URL
PUT    /api/urls/{id}/toggle  # Enable/disable URL
GET    /api/urls/stats/summary # URL statistics
```

### Job Queries

```http
GET /api/jobs                    # Paginated job list
GET /api/jobs/{uid}              # Single job details
GET /api/jobs/search?q=python    # Search jobs
GET /api/jobs/recent/discovered  # Recent jobs
GET /api/jobs/pending/enrichment # Jobs needing detail scrape
GET /api/jobs/stats              # Job statistics
```

### Scraping Operations

```http
POST /api/scraping/search/start
{
  "url_ids": ["uuid-1", "uuid-2"],  # Optional: specific URLs
  "triggered_by": "api"
}
# Returns: {"run_id": "...", "status": "running"}

POST /api/scraping/detail/start
{
  "job_uids": ["~0123...", "~0456..."],  # Optional: specific jobs
  "limit": 50,
  "triggered_by": "api"
}

POST /api/scraping/detail/{job_uid}
# Scrape single job detail

GET /api/scraping/status/{run_id}/stream
# SSE endpoint for real-time progress

GET /api/scraping/runs
# List recent scrape runs

GET /api/scraping/runs/{run_id}
# Get run details
```

---

## Real-time Updates

### Server-Sent Events (SSE)

**Client Connection**:
```javascript
const eventSource = new EventSource(
  '/api/scraping/status/run-123/stream'
);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === 'progress') {
    console.log(`Page ${data.current_page}: ${data.jobs_found} jobs`);
  }

  if (data.type === 'completion') {
    console.log(`Complete! ${data.jobs_new} new jobs`);
    eventSource.close();
  }
};
```

**Server Events**:
```json
// Progress update
{
  "type": "progress",
  "run_id": "run-123",
  "status": "scraping_search_page",
  "current_url_name": "Python Jobs",
  "current_page": 3,
  "total_pages": 10,
  "jobs_found_in_url": 150,
  "timestamp": "2025-01-20T10:30:45Z"
}

// Completion
{
  "type": "completion",
  "run_id": "run-123",
  "status": "completed",
  "results": {
    "jobs_found": 500,
    "jobs_new": 120,
    "jobs_updated": 380
  },
  "timestamp": "2025-01-20T10:35:00Z"
}
```

**Heartbeats**: Server sends heartbeat every 30s to keep connection alive

---

## Configuration

### Environment Variables (.env)

```bash
# MongoDB
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=upwork_stable

# Scrapfly (supports multiple keys for rotation)
SCRAPFLY_API_KEY=key1,key2,key3
SCRAPFLY_COUNTRY=us
SCRAPFLY_RENDERING_WAIT=3000

# Scraping
MAX_RETRIES=3
RETRY_DELAY=2
MAX_CONCURRENT_REQUESTS=5

# Caching
ENABLE_CACHE=True
CACHE_EXPIRY_MINUTES=1440
```

### Extraction Configuration

```python
from upwork_extractor import ExtractionConfig, ValidationLevel

config = ExtractionConfig(
    validation_level=ValidationLevel.STRICT,  # strict/normal/permissive
    extract_schema_org=True,
    extract_similar_jobs=True,
    preserve_skill_hierarchy=True,
    critical_fields=["title", "description", "uid"]
)
```

---

## Advanced Features

### 1. Transaction Management

All database updates for a single job are atomic:
```python
async def run_in_transaction(operations_callback):
    async with await client.start_session() as session:
        async with session.start_transaction():
            await operations_callback(session)
            # Auto-commit or rollback
```

### 2. Intelligent Caching

- **File-based cache** with SHA256 URL hashing
- **TTL support** (default 24 hours)
- **Cache validation** (content verification)

### 3. Error Handling & Retry

- **Exponential backoff**: 2s → 4s → 8s → 16s
- **Retry budget**: Max 3 attempts
- **Circuit breaker**: Stops retry on non-retryable errors
- **Graceful degradation**: NUXT fails → HTML fallback

### 4. Data Validation

**Multiple levels**:
1. **Pydantic validation**: Type checking, enums, constraints
2. **Custom validators**: UID format, date formats, ranges
3. **Schema.org validation**: Cross-check with official markup
4. **Business rules**: Budget consistency, proposal ranges

---

## Summary

This Upwork scraper is a **production-grade system** with:

✅ **Robust scraping** via Scrapfly with anti-bot bypass
✅ **Intelligent extraction** from multiple data sources
✅ **Clean architecture** for maintainability
✅ **Real-time updates** via SSE
✅ **Transaction support** for data integrity
✅ **Comprehensive validation** at every level
✅ **Error recovery** with retry logic
✅ **Scalability** with async operations and connection pooling

The system can handle thousands of jobs per hour while maintaining data quality and providing real-time visibility into the scraping process.
