"""Job service for job queries and management."""
import logging
from typing import Optional, List, Dict, Any
from pymongo import DESCENDING

from ..models import JobStatus
from ..repositories import JobRepository, ClientRepository, SkillRepository

logger = logging.getLogger(__name__)


class JobService:
    """Service for job operations."""

    def __init__(self):
        """Initialize job service."""
        self.job_repo = JobRepository()
        self.client_repo = ClientRepository()
        self.skill_repo = SkillRepository()

    async def get_job_by_uid(self, uid: str) -> Optional[Dict[str, Any]]:
        """
        Get job by UID with enriched data.

        Args:
            uid: Job UID

        Returns:
            Job dict with client and skills data or None
        """
        job = await self.job_repo.find_by_uid(uid)
        if not job:
            return None

        # Enrich with client data
        if job.get("client_id"):
            client = await self.client_repo.find_by_id(job["client_id"])
            if client:
                job["client"] = client

        # Enrich with skill data
        skill_ids = job.get("content", {}).get("skill_ids", [])
        if skill_ids:
            skills = await self.skill_repo.find_by_uids(skill_ids)
            job["content"]["skills"] = skills

        return job

    async def search_jobs(
        self,
        query: Optional[str] = None,
        status: Optional[str] = None,
        client_id: Optional[str] = None,
        skill_ids: Optional[List[str]] = None,
        budget_min: Optional[float] = None,
        budget_max: Optional[float] = None,
        page: int = 1,
        page_size: int = 50,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Dict[str, Any]:
        """
        Search jobs with filters and pagination.

        Args:
            query: Search query
            status: Job status filter
            client_id: Client ID filter
            skill_ids: List of skill IDs
            budget_min: Minimum budget
            budget_max: Maximum budget
            page: Page number (1-indexed)
            page_size: Items per page
            sort_by: Field to sort by
            sort_order: Sort order ("asc" or "desc")

        Returns:
            Dict with jobs list and pagination info
        """
        # Convert status string to enum
        status_enum = None
        if status:
            try:
                status_enum = JobStatus(status)
            except ValueError:
                logger.warning(f"Invalid status: {status}")

        # Calculate skip
        skip = (page - 1) * page_size

        # Sort order
        sort_direction = DESCENDING if sort_order == "desc" else 1

        # Search jobs
        jobs, total = await self.job_repo.search(
            query=query,
            status=status_enum,
            client_id=client_id,
            skill_ids=skill_ids,
            budget_min=budget_min,
            budget_max=budget_max,
            skip=skip,
            limit=page_size,
            sort_by=sort_by,
            sort_order=sort_direction,
        )

        # Calculate pagination
        total_pages = (total + page_size - 1) // page_size

        return {
            "jobs": jobs,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            },
        }

    async def get_jobs_by_status(
        self, status: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get jobs by status.

        Args:
            status: Job status
            limit: Maximum number of jobs

        Returns:
            List of jobs
        """
        try:
            status_enum = JobStatus(status)
        except ValueError:
            logger.error(f"Invalid status: {status}")
            return []

        # For discovered jobs, use specialized method
        if status_enum == JobStatus.DISCOVERED:
            return await self.job_repo.get_discovered_jobs(limit)

        # Otherwise search by status
        jobs, _ = await self.job_repo.search(
            status=status_enum,
            limit=limit,
        )
        return jobs

    async def get_job_stats(self) -> Dict[str, Any]:
        """
        Get job statistics.

        Returns:
            Statistics dict
        """
        stats = await self.job_repo.get_stats()
        return stats

    async def delete_job(self, uid: str) -> bool:
        """
        Delete a job by UID.

        Args:
            uid: Job UID

        Returns:
            True if deleted, False otherwise
        """
        # Check if job exists
        job = await self.job_repo.find_by_uid(uid)
        if not job:
            return False

        # Delete job
        deleted = await self.job_repo.delete(uid)

        if deleted:
            logger.info(f"Deleted job: {uid}")

        return deleted

    async def update_job_status(self, uid: str, status: str) -> bool:
        """
        Update job status.

        Args:
            uid: Job UID
            status: New status

        Returns:
            True if updated, False otherwise
        """
        try:
            status_enum = JobStatus(status)
        except ValueError:
            logger.error(f"Invalid status: {status}")
            return False

        return await self.job_repo.update_status(uid, status_enum)

    async def get_jobs_for_enrichment(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get jobs ready for enrichment.

        Args:
            limit: Maximum number of jobs

        Returns:
            List of jobs
        """
        return await self.job_repo.get_jobs_for_enrichment(limit)

    async def bulk_update_status(
        self, uids: List[str], status: str
    ) -> int:
        """
        Bulk update job statuses.

        Args:
            uids: List of job UIDs
            status: New status

        Returns:
            Number of jobs updated
        """
        try:
            status_enum = JobStatus(status)
        except ValueError:
            logger.error(f"Invalid status: {status}")
            return 0

        count = await self.job_repo.bulk_update_status(uids, status_enum)
        logger.info(f"Updated {count} jobs to status {status}")
        return count

    async def get_related_jobs(
        self, uid: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get related jobs based on skills and category.

        Args:
            uid: Job UID
            limit: Maximum number of related jobs

        Returns:
            List of related jobs
        """
        # Get source job
        job = await self.job_repo.find_by_uid(uid)
        if not job:
            return []

        # Get skill IDs
        skill_ids = job.get("content", {}).get("skill_ids", [])
        if not skill_ids:
            return []

        # Search for jobs with similar skills
        jobs, _ = await self.job_repo.search(
            skill_ids=skill_ids,
            limit=limit + 1,  # +1 to exclude source job
        )

        # Filter out source job
        related_jobs = [j for j in jobs if j["uid"] != uid][:limit]

        return related_jobs

    async def get_recent_discovered_jobs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get recently discovered jobs ordered by discovery time.

        Args:
            limit: Maximum number of jobs

        Returns:
            List of recently discovered jobs
        """
        from pymongo import DESCENDING

        jobs, _ = await self.job_repo.search(
            status=JobStatus.DISCOVERED,
            limit=limit,
            sort_by="pipeline.discovered_at",
            sort_order=DESCENDING,
        )
        return jobs
