"""Job API routes."""
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from ..services import JobService
from ..schemas.job import JobSearchQuery, JobListResponse, JobDetailResponse, JobStatsResponse

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

# Initialize service
job_service = JobService()


@router.get("/", response_model=JobListResponse)
async def search_jobs(
    q: Optional[str] = Query(None, description="Search query"),
    status: Optional[str] = Query(None, description="Job status filter"),
    client_id: Optional[str] = Query(None, description="Client ID filter"),
    skill_ids: Optional[List[str]] = Query(None, description="Skill IDs filter"),
    budget_min: Optional[float] = Query(None, description="Minimum budget"),
    budget_max: Optional[float] = Query(None, description="Maximum budget"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
):
    """
    Search and filter jobs.

    Supports:
    - Full-text search in title and description
    - Status filtering
    - Client filtering
    - Skills filtering
    - Budget range filtering
    - Sorting and pagination
    """
    result = await job_service.search_jobs(
        query=q,
        status=status,
        client_id=client_id,
        skill_ids=skill_ids,
        budget_min=budget_min,
        budget_max=budget_max,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return JobListResponse(
        jobs=result["jobs"],
        total=result["pagination"]["total"],
        page=result["pagination"]["page"],
        page_size=result["pagination"]["page_size"],
        total_pages=result["pagination"]["total_pages"],
    )


@router.get("/stats", response_model=JobStatsResponse)
async def get_job_stats():
    """
    Get job statistics.

    Returns counts by status and total job count.
    """
    stats = await job_service.get_job_stats()
    return JobStatsResponse(**stats)


@router.get("/{uid}", response_model=JobDetailResponse)
async def get_job(uid: str):
    """
    Get job by UID.

    Returns complete job details including client and skills.
    """
    job = await job_service.get_job_by_uid(uid)

    if not job:
        raise HTTPException(status_code=404, detail=f"Job {uid} not found")

    return JobDetailResponse(job=job)


@router.get("/{uid}/related")
async def get_related_jobs(
    uid: str,
    limit: int = Query(10, ge=1, le=50, description="Maximum number of related jobs"),
):
    """
    Get related jobs based on skills and category.
    """
    related_jobs = await job_service.get_related_jobs(uid, limit)

    return {
        "uid": uid,
        "related_jobs": related_jobs,
        "count": len(related_jobs),
    }


@router.get("/recent/discovered")
async def get_recent_discovered_jobs(
    limit: int = Query(20, ge=1, le=100, description="Maximum number of jobs to return"),
):
    """
    Get recently discovered jobs ordered by discovery timestamp.
    """
    jobs = await job_service.get_recent_discovered_jobs(limit)

    return {
        "jobs": jobs,
        "count": len(jobs),
    }


@router.get("/pending/enrichment")
async def get_jobs_pending_enrichment(
    limit: int = Query(50, ge=1, le=200, description="Maximum number of jobs to return"),
):
    """
    Get jobs pending detail page enrichment.

    Returns jobs with status=DISCOVERED that are ready for detail scraping.
    """
    jobs = await job_service.get_jobs_for_enrichment(limit)

    return {
        "jobs": jobs,
        "count": len(jobs),
    }


@router.delete("/{uid}")
async def delete_job(uid: str):
    """
    Delete a job by UID.
    """
    deleted = await job_service.delete_job(uid)

    if not deleted:
        raise HTTPException(status_code=404, detail=f"Job {uid} not found")

    return {"success": True, "message": f"Job {uid} deleted"}


@router.patch("/{uid}/status")
async def update_job_status(uid: str, status: str):
    """
    Update job status.

    Valid statuses: discovered, scraping_detail, enriched, private_job, detail_failed, extraction_failed, deleted
    """
    updated = await job_service.update_job_status(uid, status)

    if not updated:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to update job {uid} status to {status}",
        )

    return {"success": True, "uid": uid, "status": status}


@router.post("/bulk/status")
async def bulk_update_status(uids: List[str], status: str):
    """
    Bulk update job statuses.
    """
    count = await job_service.bulk_update_status(uids, status)

    return {
        "success": True,
        "updated_count": count,
        "status": status,
    }
