"""Client model."""
from datetime import UTC, datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ClientModel(BaseModel):
    """Client/buyer database model."""
    id: Optional[str] = Field(None, alias="_id")
    client_key: str

    # Location
    country: Optional[str] = None
    city: Optional[str] = None
    timezone: Optional[str] = None

    # Company
    company_name: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None

    # Stats
    total_spent: Optional[float] = None
    total_hires: Optional[int] = None
    active_hires: Optional[int] = None
    client_score: Optional[float] = None
    jobs_posted_count: Optional[int] = None
    payment_verified: bool = False

    # Relationships
    job_uids: List[str] = Field(default_factory=list)

    # Timestamps
    member_since: Optional[datetime] = None
    first_seen_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
        populate_by_name = True
