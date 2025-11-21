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
        db_health = await DatabaseManager.health_check()
        checks["database"] = db_health.get("status") == "connected"
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
            "max_retries": settings.MAX_RETRIES,
            "retry_delay": settings.RETRY_DELAY,
            "country": settings.SCRAPFLY_COUNTRY,
        },
        "cache": {
            "enabled": settings.ENABLE_CACHE,
            "expiry_minutes": settings.CACHE_EXPIRY_MINUTES,
            "directory": str(settings.CACHE_DIR),
        },
        "sse": {
            "heartbeat_interval": settings.SSE_HEARTBEAT_INTERVAL,
            "retry_timeout": settings.SSE_RETRY_TIMEOUT,
        },
    }


@router.get("/status")
async def get_comprehensive_status():
    """
    Comprehensive status endpoint with all system information.

    Includes:
    - Service health
    - Database connectivity
    - Scrapfly account info
    - Cache statistics
    - API key rotation status
    - SSE connection stats
    - Recent scraping activity
    """
    from ..repositories import (
        JobRepository,
        URLRepository,
        ScrapeRunRepository,
    )
    from ..integrations import ScrapflyClient
    from ..infrastructure.sse_manager import sse_manager

    status = {
        "timestamp": datetime.now(UTC).isoformat(),
        "service": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "healthy",
        },
    }

    # Database connectivity
    try:
        db_health = await DatabaseManager.health_check()
        status["database"] = {
            "connected": db_health.get("status") == "connected",
            "name": settings.DATABASE_NAME,
            "uri": settings.MONGODB_URI.split('@')[-1] if '@' in settings.MONGODB_URI else "local",
            "health": db_health,
        }
    except Exception as e:
        status["database"] = {
            "connected": False,
            "error": str(e),
        }
        status["service"]["status"] = "degraded"

    # Scrapfly client info
    try:
        scrapfly_client = ScrapflyClient()
        await scrapfly_client.initialize()

        # Get account info
        account_info = await scrapfly_client.get_account_info()
        client_stats = scrapfly_client.get_client_stats()

        status["scrapfly"] = {
            "connected": account_info is not None,
            "account": account_info if account_info else {"error": "Failed to fetch account info"},
            "client_stats": client_stats,
        }

        await scrapfly_client.close()

    except Exception as e:
        status["scrapfly"] = {
            "connected": False,
            "error": str(e),
        }
        status["service"]["status"] = "degraded"

    # SSE Manager stats
    try:
        status["sse"] = {
            "active_connections": sse_manager.get_active_connections_count(),
            "heartbeat_interval": settings.SSE_HEARTBEAT_INTERVAL,
        }
    except Exception as e:
        status["sse"] = {
            "error": str(e),
        }

    # Recent scraping activity
    try:
        scrape_repo = ScrapeRunRepository()
        recent_runs = await scrape_repo.get_recent_runs(limit=5)
        active_runs = await scrape_repo.get_active_runs()

        status["scraping"] = {
            "active_runs": len(active_runs),
            "recent_runs_count": len(recent_runs),
            "recent_runs": [
                {
                    "run_id": run["run_id"],
                    "run_type": run["run_type"],
                    "status": run["status"],
                    "started_at": run["started_at"].isoformat() if isinstance(run.get("started_at"), datetime) else run.get("started_at"),
                }
                for run in recent_runs
            ] if recent_runs else [],
        }
    except Exception as e:
        status["scraping"] = {
            "error": str(e),
        }

    # Job statistics
    try:
        job_repo = JobRepository()
        job_stats = await job_repo.get_stats()
        status["jobs"] = job_stats
    except Exception as e:
        status["jobs"] = {
            "error": str(e),
        }

    # URL statistics
    try:
        url_repo = URLRepository()
        url_stats = await url_repo.get_stats()
        status["urls"] = url_stats
    except Exception as e:
        status["urls"] = {
            "error": str(e),
        }

    return status
