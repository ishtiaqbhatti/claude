"""Job repository for database operations."""
from datetime import UTC, datetime
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClientSession
from pymongo import ASCENDING, DESCENDING

from ..config import DatabaseManager
from ..models import JobModel, JobStatus


class JobRepository:
    """Repository for job operations."""

    def __init__(self):
        self.collection_name = "jobs"

    @property
    def collection(self):
        """Get jobs collection."""
        return DatabaseManager.get_collection(self.collection_name)

    async def find_by_uid(self, uid: str) -> Optional[Dict[str, Any]]:
        """Find job by UID."""
        return await self.collection.find_one({"uid": uid})

    async def find_by_uids(self, uids: List[str]) -> List[Dict[str, Any]]:
        """Find jobs by UIDs."""
        cursor = self.collection.find({"uid": {"$in": uids}})
        return await cursor.to_list(length=None)

    async def exists(self, uid: str) -> bool:
        """Check if job exists."""
        count = await self.collection.count_documents({"uid": uid}, limit=1)
        return count > 0

    async def create(
        self, job: JobModel, session: Optional[AsyncIOMotorClientSession] = None
    ) -> str:
        """Create a new job."""
        job_dict = job.model_dump(by_alias=True, exclude={"id"})
        result = await self.collection.insert_one(job_dict, session=session)
        return str(result.inserted_id)

    async def update(
        self,
        uid: str,
        update_data: Dict[str, Any],
        session: Optional[AsyncIOMotorClientSession] = None,
    ) -> bool:
        """Update job by UID."""
        update_data["updated_at"] = datetime.now(UTC)
        result = await self.collection.update_one(
            {"uid": uid}, {"$set": update_data}, session=session
        )
        return result.modified_count > 0

    async def update_status(
        self,
        uid: str,
        status: JobStatus,
        session: Optional[AsyncIOMotorClientSession] = None,
    ) -> bool:
        """Update job status."""
        return await self.update(uid, {"status": status.value}, session=session)

    async def delete(
        self, uid: str, session: Optional[AsyncIOMotorClientSession] = None
    ) -> bool:
        """Delete job by UID."""
        result = await self.collection.delete_one({"uid": uid}, session=session)
        return result.deleted_count > 0

    async def search(
        self,
        query: Optional[str] = None,
        status: Optional[JobStatus] = None,
        client_id: Optional[str] = None,
        skill_ids: Optional[List[str]] = None,
        budget_min: Optional[float] = None,
        budget_max: Optional[float] = None,
        skip: int = 0,
        limit: int = 50,
        sort_by: str = "created_at",
        sort_order: int = DESCENDING,
    ) -> tuple[List[Dict[str, Any]], int]:
        """Search jobs with filters."""
        # Build filter
        filters: Dict[str, Any] = {}

        if query:
            filters["$or"] = [
                {"title": {"$regex": query, "$options": "i"}},
                {"content.description_plain": {"$regex": query, "$options": "i"}},
            ]

        if status:
            filters["status"] = status.value

        if client_id:
            filters["client_id"] = client_id

        if skill_ids:
            filters["content.skill_ids"] = {"$in": skill_ids}

        if budget_min is not None or budget_max is not None:
            budget_filter: Dict[str, Any] = {}
            if budget_min is not None:
                budget_filter["$gte"] = budget_min
            if budget_max is not None:
                budget_filter["$lte"] = budget_max
            filters["budget.min"] = budget_filter

        # Get total count
        total = await self.collection.count_documents(filters)

        # Get paginated results
        cursor = (
            self.collection.find(filters)
            .sort(sort_by, sort_order)
            .skip(skip)
            .limit(limit)
        )
        jobs = await cursor.to_list(length=limit)

        return jobs, total

    async def get_discovered_jobs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get jobs in discovered status for detail scraping."""
        cursor = (
            self.collection.find({"status": JobStatus.DISCOVERED.value})
            .sort("created_at", ASCENDING)
            .limit(limit)
        )
        return await cursor.to_list(length=limit)

    async def get_jobs_for_enrichment(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get jobs ready for enrichment."""
        filters = {
            "status": JobStatus.SCRAPING_DETAIL.value,
            "pipeline.is_enriched": False,
        }
        cursor = (
            self.collection.find(filters)
            .sort("pipeline.discovered_at", ASCENDING)
            .limit(limit)
        )
        return await cursor.to_list(length=limit)

    async def count_by_status(self, status: JobStatus) -> int:
        """Count jobs by status."""
        return await self.collection.count_documents({"status": status.value})

    async def get_stats(self) -> Dict[str, Any]:
        """Get job statistics."""
        pipeline = [
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1},
                }
            }
        ]
        cursor = self.collection.aggregate(pipeline)
        results = await cursor.to_list(length=None)

        stats = {"total": 0, "by_status": {}}
        for result in results:
            status = result["_id"]
            count = result["count"]
            stats["by_status"][status] = count
            stats["total"] += count

        return stats

    async def bulk_update_status(
        self,
        uids: List[str],
        status: JobStatus,
        session: Optional[AsyncIOMotorClientSession] = None,
    ) -> int:
        """Bulk update job statuses."""
        result = await self.collection.update_many(
            {"uid": {"$in": uids}},
            {"$set": {"status": status.value, "updated_at": datetime.now(UTC)}},
            session=session,
        )
        return result.modified_count

    async def mark_as_enriched(
        self, uid: str, session: Optional[AsyncIOMotorClientSession] = None
    ) -> bool:
        """Mark job as enriched."""
        update_data = {
            "status": JobStatus.ENRICHED.value,
            "pipeline.is_enriched": True,
            "updated_at": datetime.now(UTC),
        }
        result = await self.collection.update_one(
            {"uid": uid}, {"$set": update_data}, session=session
        )
        return result.modified_count > 0
