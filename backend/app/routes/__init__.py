"""API route modules."""
from .job_routes import router as job_router
from .url_routes import router as url_router
from .scraping_routes import router as scraping_router
from .health_routes import router as health_router

__all__ = [
    "job_router",
    "url_router",
    "scraping_router",
    "health_router",
]
