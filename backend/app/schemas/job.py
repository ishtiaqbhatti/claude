"""Job API schemas."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class JobSearchQuery(BaseModel):
    """Job search query parameters."""
    q: Optional[str] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=100)
    status: Optional[str] = None
    enriched: Optional[bool] = None
    sort_by: str = "created_at"
    sort_order: str = Field("desc", pattern="^(asc|desc)$")


class JobResponse(BaseModel):
    """Job response schema."""
    uid: str
    title: str
    url: Optional[str] = None
    status: str
    description: Optional[str] = None
    budget: Optional[Dict[str, Any]] = None
    skills: List[Dict[str, str]] = []
    client_id: Optional[str] = None
    created_at: str
    updated_at: str


class JobListResponse(BaseModel):
    """Paginated job list response."""
    jobs: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int


class JobDetailResponse(BaseModel):
    """Detailed job response schema."""
    job: Dict[str, Any]


class JobStatsResponse(BaseModel):
    """Job statistics response schema."""
    total: int = 0
    by_status: Dict[str, int] = Field(default_factory=dict)
    enriched: int = 0
    discovered: int = 0
    failed: int = 0
