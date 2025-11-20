"""Scrape run repository for database operations."""
from datetime import UTC, datetime
from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorClientSession

from ..config import DatabaseManager
from ..models import ScrapeRunModel, ScrapeErrorLog


class ScrapeRunRepository:
    """Repository for scrape run operations."""

    def __init__(self):
        self.collection_name = "scrape_runs"

    @property
    def collection(self):
        """Get scrape_runs collection."""
        return DatabaseManager.get_collection(self.collection_name)

    async def find_by_run_id(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Find scrape run by run_id."""
        return await self.collection.find_one({"run_id": run_id})

    async def exists(self, run_id: str) -> bool:
        """Check if scrape run exists."""
        count = await self.collection.count_documents({"run_id": run_id}, limit=1)
        return count > 0

    async def create(
        self,
        scrape_run: ScrapeRunModel,
        session: Optional[AsyncIOMotorClientSession] = None,
    ) -> str:
        """Create a new scrape run."""
        run_dict = scrape_run.model_dump(by_alias=True, exclude={"id"})
        result = await self.collection.insert_one(run_dict, session=session)
        return str(result.inserted_id)

    async def update(
        self,
        run_id: str,
        update_data: Dict[str, Any],
        session: Optional[AsyncIOMotorClientSession] = None,
    ) -> bool:
        """Update scrape run by run_id."""
        result = await self.collection.update_one(
            {"run_id": run_id}, {"$set": update_data}, session=session
        )
        return result.modified_count > 0

    async def update_status(
        self,
        run_id: str,
        status: str,
        session: Optional[AsyncIOMotorClientSession] = None,
    ) -> bool:
        """Update scrape run status."""
        update_data = {"status": status}

        # If completing, set completion time
        if status in ["completed", "failed"]:
            run = await self.find_by_run_id(run_id)
            if run:
                started_at = run.get("started_at")
                if started_at:
                    completed_at = datetime.now(UTC)
                    duration = (completed_at - started_at).total_seconds()
                    update_data["completed_at"] = completed_at
                    update_data["duration_seconds"] = duration

        return await self.update(run_id, update_data, session=session)

    async def update_progress(
        self,
        run_id: str,
        progress_percentage: float,
        session: Optional[AsyncIOMotorClientSession] = None,
    ) -> bool:
        """Update scrape run progress."""
        return await self.update(
            run_id, {"progress_percentage": progress_percentage}, session=session
        )

    async def increment_counters(
        self,
        run_id: str,
        jobs_found: int = 0,
        jobs_new: int = 0,
        jobs_updated: int = 0,
        jobs_failed: int = 0,
        session: Optional[AsyncIOMotorClientSession] = None,
    ) -> bool:
        """Increment result counters."""
        update_data: Dict[str, Any] = {"$inc": {}}

        if jobs_found > 0:
            update_data["$inc"]["jobs_found"] = jobs_found
        if jobs_new > 0:
            update_data["$inc"]["jobs_new"] = jobs_new
        if jobs_updated > 0:
            update_data["$inc"]["jobs_updated"] = jobs_updated
        if jobs_failed > 0:
            update_data["$inc"]["jobs_failed"] = jobs_failed

        if not update_data["$inc"]:
            return False

        result = await self.collection.update_one(
            {"run_id": run_id}, update_data, session=session
        )
        return result.modified_count > 0

    async def add_error(
        self,
        run_id: str,
        error: ScrapeErrorLog,
        session: Optional[AsyncIOMotorClientSession] = None,
    ) -> bool:
        """Add an error to scrape run."""
        error_dict = error.model_dump()
        result = await self.collection.update_one(
            {"run_id": run_id}, {"$push": {"errors": error_dict}}, session=session
        )
        return result.modified_count > 0

    async def update_result_for_url(
        self,
        run_id: str,
        url_id: str,
        result_data: Dict[str, Any],
        session: Optional[AsyncIOMotorClientSession] = None,
    ) -> bool:
        """Update results for a specific URL."""
        update_data = {f"results_by_url.{url_id}": result_data}
        result = await self.collection.update_one(
            {"run_id": run_id}, {"$set": update_data}, session=session
        )
        return result.modified_count > 0

    async def get_recent_runs(
        self,
        run_type: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Get recent scrape runs."""
        filters: Dict[str, Any] = {}
        if run_type:
            filters["run_type"] = run_type

        cursor = (
            self.collection.find(filters)
            .sort("started_at", -1)
            .limit(limit)
        )
        return await cursor.to_list(length=limit)

    async def get_active_runs(self) -> List[Dict[str, Any]]:
        """Get currently active scrape runs."""
        cursor = self.collection.find({"status": {"$in": ["pending", "running"]}})
        return await cursor.to_list(length=None)

    async def get_stats(
        self, run_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get scrape run statistics."""
        match_stage: Dict[str, Any] = {}
        if run_type:
            match_stage = {"$match": {"run_type": run_type}}

        pipeline = []
        if match_stage:
            pipeline.append(match_stage)

        pipeline.append({
            "$group": {
                "_id": "$status",
                "count": {"$sum": 1},
                "avg_duration": {"$avg": "$duration_seconds"},
                "total_jobs_found": {"$sum": "$jobs_found"},
                "total_jobs_new": {"$sum": "$jobs_new"},
                "total_jobs_updated": {"$sum": "$jobs_updated"},
                "total_jobs_failed": {"$sum": "$jobs_failed"},
            }
        })

        cursor = self.collection.aggregate(pipeline)
        results = await cursor.to_list(length=None)

        stats = {
            "total_runs": 0,
            "by_status": {},
            "totals": {
                "jobs_found": 0,
                "jobs_new": 0,
                "jobs_updated": 0,
                "jobs_failed": 0,
            },
        }

        for result in results:
            status = result["_id"]
            count = result["count"]
            stats["by_status"][status] = {
                "count": count,
                "avg_duration": result.get("avg_duration", 0.0),
                "jobs_found": result.get("total_jobs_found", 0),
                "jobs_new": result.get("total_jobs_new", 0),
                "jobs_updated": result.get("total_jobs_updated", 0),
                "jobs_failed": result.get("total_jobs_failed", 0),
            }
            stats["total_runs"] += count
            stats["totals"]["jobs_found"] += result.get("total_jobs_found", 0)
            stats["totals"]["jobs_new"] += result.get("total_jobs_new", 0)
            stats["totals"]["jobs_updated"] += result.get("total_jobs_updated", 0)
            stats["totals"]["jobs_failed"] += result.get("total_jobs_failed", 0)

        return stats

    async def delete_old_runs(
        self,
        days: int = 30,
        session: Optional[AsyncIOMotorClientSession] = None,
    ) -> int:
        """Delete scrape runs older than specified days."""
        cutoff_date = datetime.now(UTC).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        cutoff_date = cutoff_date.replace(day=cutoff_date.day - days)

        result = await self.collection.delete_many(
            {"started_at": {"$lt": cutoff_date}}, session=session
        )
        return result.deleted_count
