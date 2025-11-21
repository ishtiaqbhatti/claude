"""API schemas (DTOs)."""
from .job import *
from .url import *
from .scraping import *

__all__ = [
    # Job schemas
    "JobResponse",
    "JobListResponse",
    "JobSearchQuery",
    "JobDetailResponse",
    "JobStatsResponse",
    # URL schemas
    "URLCreate",
    "URLUpdate",
    "URLResponse",
    "URLListResponse",
    "URLStatsResponse",
    # Scraping schemas
    "StartSearchScrapeRequest",
    "StartDetailScrapeRequest",
    "ScrapeRunResponse",
]
