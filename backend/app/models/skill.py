"""Skill model."""
from datetime import UTC, datetime
from typing import Optional
from pydantic import BaseModel, Field


class SkillModel(BaseModel):
    """Skill database model."""
    id: Optional[str] = Field(None, alias="_id")
    uid: str
    name: str
    pretty_name: Optional[str] = None

    # Stats
    job_count: int = 0

    # Timestamps
    first_seen_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_seen_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
        populate_by_name = True
