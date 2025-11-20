"""Job model."""
from datetime import UTC, datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl


class JobStatus(str, Enum):
    """Job processing status."""
    DISCOVERED = "discovered"
    SCRAPING_DETAIL = "scraping_detail"
    ENRICHED = "enriched"
    PRIVATE_JOB = "private_job"
    DETAIL_FAILED = "detail_failed"
    EXTRACTION_FAILED = "extraction_failed"
    DELETED = "deleted"


class BudgetModel(BaseModel):
    """Job budget information."""
    available: bool = False
    type: Optional[str] = None
    min: Optional[float] = None
    max: Optional[float] = None
    currency: Optional[str] = "USD"


class SkillInfo(BaseModel):
    """Skill reference information."""
    uid: str
    name: str
    category: Optional[str] = None


class ContentModel(BaseModel):
    """Job content."""
    description: Optional[str] = None
    description_plain: Optional[str] = None
    skill_ids: List[str] = Field(default_factory=list)
    skills: List[SkillInfo] = Field(default_factory=list)


class PipelineModel(BaseModel):
    """Job pipeline metadata."""
    source: str = "search"
    is_enriched: bool = False
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    detail_scraped_at: Optional[datetime] = None
    last_optimization_attempt: Optional[datetime] = None
    optimization_retries: int = 0
    optimization_error: Optional[str] = None


class JobModel(BaseModel):
    """Job database model."""
    # MongoDB ID
    id: Optional[str] = Field(None, alias="_id")

    # Core fields
    uid: str
    title: str
    url: Optional[HttpUrl] = None
    status: JobStatus = JobStatus.DISCOVERED
    run_id: Optional[str] = None
    ciphertext: Optional[str] = None

    # Content
    content: ContentModel = Field(default_factory=ContentModel)

    # Budget
    budget: BudgetModel = Field(default_factory=BudgetModel)

    # Relationships
    client_id: Optional[str] = None

    # Metadata
    experience_level: Optional[str] = None
    duration: Optional[str] = None
    workload: Optional[str] = None
    project_type: Optional[str] = None
    category_name: Optional[str] = None

    # Dates
    published_on: Optional[datetime] = None
    created_on: Optional[datetime] = None
    renewed_on: Optional[datetime] = None
    was_renewed: bool = False

    # Pipeline
    pipeline: PipelineModel = Field(default_factory=PipelineModel)

    # Source data (for debugging)
    source_data: Dict[str, Any] = Field(default_factory=dict)

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
        populate_by_name = True
        use_enum_values = True
