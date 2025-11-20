"""Scrape run model."""
from datetime import UTC, datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import uuid


class ScrapeErrorLog(BaseModel):
    """Error log entry."""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    message: str
    item_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class ScrapeRunModel(BaseModel):
    """Scrape run database model."""
    id: Optional[str] = Field(None, alias="_id")
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Run info
    run_type: str  # "search" or "detail"
    status: str = "pending"  # pending, running, completed, failed
    triggered_by: str = "api"

    # Target items
    search_urls: List[str] = Field(default_factory=list)
    job_uids: List[str] = Field(default_factory=list)

    # Results
    jobs_found: int = 0
    jobs_new: int = 0
    jobs_updated: int = 0
    jobs_failed: int = 0

    # Progress
    progress_percentage: float = 0.0

    # Errors
    errors: List[ScrapeErrorLog] = Field(default_factory=list)

    # Results by URL/Job
    results_by_url: Dict[str, Any] = Field(default_factory=dict)

    # Timestamps
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
        populate_by_name = True
