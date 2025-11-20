"""Search URL model."""
from datetime import UTC, datetime
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl
import uuid


class SearchURLModel(BaseModel):
    """Search URL database model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    url: HttpUrl
    name: str

    # Settings
    enabled: bool = True
    category: Optional[str] = None
    description: Optional[str] = None

    # Scraping history
    last_scraped_at: Optional[datetime] = None
    last_scrape_job_count: Optional[int] = None
    total_scrape_count: int = 0
    total_jobs_found: int = 0

    # Error tracking
    last_error: Optional[str] = None
    last_error_at: Optional[datetime] = None
    error_count: int = 0

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
        populate_by_name = True
