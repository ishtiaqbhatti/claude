"""URL API schemas."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, HttpUrl, Field


class URLCreate(BaseModel):
    """Create URL request."""
    url: HttpUrl
    name: str = Field(..., min_length=3)
    category: Optional[str] = None
    description: Optional[str] = None


class URLUpdate(BaseModel):
    """Update URL request."""
    name: Optional[str] = Field(None, min_length=3)
    category: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None


class URLResponse(BaseModel):
    """URL response schema."""
    id: str
    url: str
    name: str
    enabled: bool
    category: Optional[str] = None
    total_jobs_found: int
    last_scraped_at: Optional[str] = None


class URLListResponse(BaseModel):
    """Paginated URL list response."""
    urls: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int


class URLStatsResponse(BaseModel):
    """URL statistics response schema."""
    total: int = 0
    enabled: int = 0
    disabled: int = 0
    total_jobs_found: int = 0
    total_scrapes: int = 0
