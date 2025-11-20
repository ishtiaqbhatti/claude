"""API schemas (DTOs)."""
from .job import *
from .url import *
from .scraping import *

__all__ = [
    # Job schemas
    "JobResponse",
    "JobListResponse",
    "JobSearchQuery",
    # URL schemas
    "URLCreate",
    "URLUpdate",
    "URLResponse",
    # Scraping schemas
    "StartSearchScrapeRequest",
    "StartDetailScrapeRequest",
    "ScrapeRunResponse",
]
