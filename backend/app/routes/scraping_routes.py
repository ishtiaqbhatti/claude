"""Scraping API routes."""
import json
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from ..services import ScrapingService
from ..schemas.scraping import (
    StartSearchScrapeRequest,
    StartDetailScrapeRequest,
    ScrapeRunResponse,
)

router = APIRouter(prefix="/api/scraping", tags=["scraping"])

# Initialize service
scraping_service = ScrapingService()


@router.on_event("startup")
async def startup_event():
    """Initialize scraping service on startup."""
    await scraping_service.initialize()


@router.on_event("shutdown")
async def shutdown_event():
    """Cleanup scraping service on shutdown."""
    await scraping_service.cleanup()


@router.post("/search/start")
async def start_search_scrape(request: StartSearchScrapeRequest):
    """
    Start search scraping process.

    Returns SSE stream with real-time updates.

    Events:
    - run_started: Scrape run has started
    - url_started: Processing URL
    - url_completed: URL processing completed
    - run_completed: Scrape run completed
    - run_failed: Scrape run failed
    """

    async def event_generator():
        """Generate SSE events."""
        async for event in scraping_service.start_search_scrape(
            url_ids=request.url_ids,
            triggered_by=request.triggered_by,
        ):
            # Format as SSE
            event_type = event.get("event", "message")
            event_data = event.get("data", {})

            yield f"event: {event_type}\n"
            yield f"data: {json.dumps(event_data)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/detail/start")
async def start_detail_scrape(request: StartDetailScrapeRequest):
    """
    Start detail scraping process.

    Returns SSE stream with real-time updates.

    Events:
    - run_started: Scrape run has started
    - job_started: Processing job
    - job_completed: Job processing completed
    - run_completed: Scrape run completed
    - run_failed: Scrape run failed
    """

    async def event_generator():
        """Generate SSE events."""
        async for event in scraping_service.start_detail_scrape(
            job_uids=request.job_uids,
            limit=request.limit,
            triggered_by=request.triggered_by,
        ):
            # Format as SSE
            event_type = event.get("event", "message")
            event_data = event.get("data", {})

            yield f"event: {event_type}\n"
            yield f"data: {json.dumps(event_data)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/detail/{job_uid}")
async def scrape_single_job(job_uid: str):
    """
    Scrape a single job detail page.

    Creates a dedicated scrape run for one job and returns the run ID
    for SSE streaming.
    """
    # Use the job_uid as the run_id for single scrapes
    run_id = f"single_{job_uid}"

    # Start detail scrape in background for this specific job
    from fastapi import BackgroundTasks
    background_tasks = BackgroundTasks()

    async def scrape_job():
        """Background task to scrape single job."""
        async for _ in scraping_service.start_detail_scrape(
            job_uids=[job_uid],
            limit=1,
            triggered_by="api_single",
        ):
            pass  # Events are handled by SSE stream

    background_tasks.add_task(scrape_job)

    return {
        "job_uid": job_uid,
        "run_id": run_id,
        "status": "started",
        "stream_url": f"/api/scraping/status/{run_id}/stream"
    }


@router.get("/status/{run_id}/stream")
async def stream_scraping_progress(run_id: str):
    """
    Stream real-time scraping progress via Server-Sent Events (SSE).

    Provides live updates for scraping operations including:
    - Progress percentages
    - Current item being processed
    - Completion status
    - Errors

    The stream will automatically close when the scraping is complete.

    Use with EventSource API in JavaScript:
    ```
    const eventSource = new EventSource('/api/scraping/status/{run_id}/stream');
    eventSource.addEventListener('progress', (e) => {
        const data = JSON.parse(e.data);
        console.log(data);
    });
    ```
    """
    from ..infrastructure import sse_manager

    # Check if run exists in database first
    from ..repositories import ScrapeRunRepository
    repo = ScrapeRunRepository()
    run = await repo.find_by_run_id(run_id)

    if run and run.get("status") in ["completed", "failed"]:
        # Run already completed, send final state and close
        async def completed_stream():
            yield f"event: complete\n"
            yield f"data: {json.dumps({'status': run['status'], 'run_id': run_id})}\n\n"

        return StreamingResponse(
            completed_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # Stream live events
    return StreamingResponse(
        sse_manager.stream_events(run_id, include_heartbeat=True),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/runs/recent")
async def get_recent_runs(
    run_type: Optional[str] = Query(None, description="Filter by run type (search/detail)"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of runs"),
):
    """
    Get recent scrape runs.
    """
    from ..repositories import ScrapeRunRepository

    repo = ScrapeRunRepository()
    runs = await repo.get_recent_runs(run_type=run_type, limit=limit)

    return {
        "runs": runs,
        "count": len(runs),
    }


@router.get("/runs/{run_id}")
async def get_scrape_run(run_id: str):
    """
    Get scrape run details by ID.
    """
    from ..repositories import ScrapeRunRepository

    repo = ScrapeRunRepository()
    run = await repo.find_by_run_id(run_id)

    if not run:
        raise HTTPException(status_code=404, detail=f"Scrape run {run_id} not found")

    return run


@router.get("/runs/stats")
async def get_scrape_stats(
    run_type: Optional[str] = Query(None, description="Filter by run type (search/detail)"),
):
    """
    Get scraping statistics.
    """
    from ..repositories import ScrapeRunRepository

    repo = ScrapeRunRepository()
    stats = await repo.get_stats(run_type=run_type)

    return stats


@router.get("/status/active")
async def get_active_runs():
    """
    Get currently active scrape runs.
    """
    from ..repositories import ScrapeRunRepository

    repo = ScrapeRunRepository()
    runs = await repo.get_active_runs()

    return {
        "runs": runs,
        "count": len(runs),
    }
