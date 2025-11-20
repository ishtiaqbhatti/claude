"""Scraping API schemas."""
from typing import Optional, List
from pydantic import BaseModel, Field


class StartSearchScrapeRequest(BaseModel):
    """Start search scrape request."""
    url_ids: Optional[List[str]] = None
    triggered_by: str = "api"


class StartDetailScrapeRequest(BaseModel):
    """Start detail scrape request."""
    job_uids: Optional[List[str]] = None
    limit: int = Field(50, ge=1, le=100)
    triggered_by: str = "api"


class ScrapeRunResponse(BaseModel):
    """Scrape run response."""
    run_id: str
    status: str
    message: str
