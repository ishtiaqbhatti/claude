"""Health check and monitoring routes."""
from datetime import datetime, UTC
from fastapi import APIRouter, HTTPException

from ..config import DatabaseManager, settings

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("/")
async def health_check():
    """
    Basic health check endpoint.

    Returns service status and timestamp.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "service": "upwork-scraper",
    }


@router.get("/ready")
async def readiness_check():
    """
    Readiness check - verifies service is ready to handle requests.

    Checks:
    - Database connectivity
    """
    checks = {
        "database": False,
    }

    # Check database
    try:
        db_healthy = await DatabaseManager.health_check()
        checks["database"] = db_healthy
    except Exception as e:
        checks["database"] = False
        checks["database_error"] = str(e)

    # Overall status
    is_ready = all(checks.values())

    if not is_ready:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "checks": checks,
            },
        )

    return {
        "status": "ready",
        "checks": checks,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/live")
async def liveness_check():
    """
    Liveness check - verifies service is alive.

    Simple check that always returns 200 if service is running.
    """
    return {
        "status": "alive",
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/stats")
async def get_system_stats():
    """
    Get system statistics.

    Returns:
    - Database stats
    - Job stats
    - URL stats
    - Scraping stats
    """
    from ..repositories import (
        JobRepository,
        URLRepository,
        ScrapeRunRepository,
        ClientRepository,
        SkillRepository,
    )

    job_repo = JobRepository()
    url_repo = URLRepository()
    scrape_repo = ScrapeRunRepository()
    client_repo = ClientRepository()
    skill_repo = SkillRepository()

    # Gather stats
    job_stats = await job_repo.get_stats()
    url_stats = await url_repo.get_stats()
    scrape_stats = await scrape_repo.get_stats()
    client_stats = await client_repo.get_stats()
    skill_stats = await skill_repo.get_stats()

    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "database": {
            "connected": await DatabaseManager.health_check(),
            "name": settings.DATABASE_NAME,
        },
        "jobs": job_stats,
        "urls": url_stats,
        "scraping": scrape_stats,
        "clients": client_stats,
        "skills": skill_stats,
    }


@router.get("/config")
async def get_config():
    """
    Get non-sensitive configuration.

    Returns current settings (excluding secrets).
    """
    return {
        "database": {
            "name": settings.DATABASE_NAME,
        },
        "scraping": {
            "max_concurrent_requests": settings.MAX_CONCURRENT_REQUESTS,
            "search_page_wait_selector": settings.SEARCH_PAGE_WAIT_SELECTOR,
            "detail_page_wait_selector": settings.DETAIL_PAGE_WAIT_SELECTOR,
            "country": settings.SCRAPFLY_COUNTRY,
        },
        "cache": {
            "enabled": settings.CACHE_ENABLED,
            "ttl_seconds": settings.CACHE_TTL_SECONDS,
            "directory": settings.CACHE_DIR,
        },
        "sse": {
            "retry_timeout": settings.SSE_RETRY_TIMEOUT,
            "keepalive_interval": settings.SSE_KEEPALIVE_INTERVAL,
        },
    }
