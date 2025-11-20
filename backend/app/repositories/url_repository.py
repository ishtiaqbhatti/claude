"""Search URL repository for database operations."""
from datetime import UTC, datetime
from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorClientSession

from ..config import DatabaseManager
from ..models import SearchURLModel


class URLRepository:
    """Repository for search URL operations."""

    def __init__(self):
        self.collection_name = "search_urls"

    @property
    def collection(self):
        """Get search_urls collection."""
        return DatabaseManager.get_collection(self.collection_name)

    async def find_by_id(self, url_id: str) -> Optional[Dict[str, Any]]:
        """Find URL by ID."""
        return await self.collection.find_one({"id": url_id})

    async def find_by_ids(self, url_ids: List[str]) -> List[Dict[str, Any]]:
        """Find URLs by IDs."""
        cursor = self.collection.find({"id": {"$in": url_ids}})
        return await cursor.to_list(length=None)

    async def exists(self, url_id: str) -> bool:
        """Check if URL exists."""
        count = await self.collection.count_documents({"id": url_id}, limit=1)
        return count > 0

    async def create(
        self, url: SearchURLModel, session: Optional[AsyncIOMotorClientSession] = None
    ) -> str:
        """Create a new search URL."""
        url_dict = url.model_dump(by_alias=True, exclude={"_id"})
        result = await self.collection.insert_one(url_dict, session=session)
        return str(result.inserted_id)

    async def update(
        self,
        url_id: str,
        update_data: Dict[str, Any],
        session: Optional[AsyncIOMotorClientSession] = None,
    ) -> bool:
        """Update URL by ID."""
        update_data["updated_at"] = datetime.now(UTC)
        result = await self.collection.update_one(
            {"id": url_id}, {"$set": update_data}, session=session
        )
        return result.modified_count > 0

    async def delete(
        self, url_id: str, session: Optional[AsyncIOMotorClientSession] = None
    ) -> bool:
        """Delete URL by ID."""
        result = await self.collection.delete_one({"id": url_id}, session=session)
        return result.deleted_count > 0

    async def get_all(
        self, enabled_only: bool = False, skip: int = 0, limit: int = 100
    ) -> tuple[List[Dict[str, Any]], int]:
        """Get all URLs with pagination."""
        filters: Dict[str, Any] = {}
        if enabled_only:
            filters["enabled"] = True

        total = await self.collection.count_documents(filters)
        cursor = self.collection.find(filters).skip(skip).limit(limit)
        urls = await cursor.to_list(length=limit)

        return urls, total

    async def get_enabled_urls(self) -> List[Dict[str, Any]]:
        """Get all enabled URLs."""
        cursor = self.collection.find({"enabled": True})
        return await cursor.to_list(length=None)

    async def list_for_scraping(
        self, min_scrape_interval_minutes: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Get URLs that are ready for scraping based on last scrape time.

        Args:
            min_scrape_interval_minutes: Minimum minutes between scrapes

        Returns:
            List of URLs that haven't been scraped recently
        """
        from datetime import timedelta

        cutoff_time = datetime.now(UTC) - timedelta(minutes=min_scrape_interval_minutes)

        filters = {
            "enabled": True,
            "$or": [
                {"last_scraped_at": {"$exists": False}},
                {"last_scraped_at": None},
                {"last_scraped_at": {"$lt": cutoff_time}}
            ]
        }

        cursor = self.collection.find(filters)
        return await cursor.to_list(length=None)

    async def toggle_enabled(
        self, url_id: str, session: Optional[AsyncIOMotorClientSession] = None
    ) -> bool:
        """Toggle enabled status."""
        url = await self.find_by_id(url_id)
        if not url:
            return False

        new_status = not url.get("enabled", True)
        return await self.update(url_id, {"enabled": new_status}, session=session)

    async def increment_scrape_count(
        self,
        url_id: str,
        jobs_found: int = 0,
        session: Optional[AsyncIOMotorClientSession] = None,
    ) -> bool:
        """Increment scrape count and update stats."""
        update_data = {
            "$inc": {
                "total_scrapes": 1,
                "total_jobs_found": jobs_found,
            },
            "$set": {
                "last_scraped_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
            },
        }

        result = await self.collection.update_one(
            {"id": url_id}, update_data, session=session
        )
        return result.modified_count > 0

    async def update_last_error(
        self,
        url_id: str,
        error_message: str,
        session: Optional[AsyncIOMotorClientSession] = None,
    ) -> bool:
        """Update last error for URL."""
        update_data = {
            "last_error": error_message,
            "last_error_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }
        result = await self.collection.update_one(
            {"id": url_id}, {"$set": update_data}, session=session
        )
        return result.modified_count > 0

    async def get_stats(self) -> Dict[str, Any]:
        """Get URL statistics."""
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_urls": {"$sum": 1},
                    "enabled_urls": {
                        "$sum": {"$cond": [{"$eq": ["$enabled", True]}, 1, 0]}
                    },
                    "total_scrapes": {"$sum": "$total_scrapes"},
                    "total_jobs_found": {"$sum": "$total_jobs_found"},
                }
            }
        ]

        cursor = self.collection.aggregate(pipeline)
        results = await cursor.to_list(length=1)

        if results:
            result = results[0]
            return {
                "total_urls": result.get("total_urls", 0),
                "enabled_urls": result.get("enabled_urls", 0),
                "total_scrapes": result.get("total_scrapes", 0),
                "total_jobs_found": result.get("total_jobs_found", 0),
            }

        return {
            "total_urls": 0,
            "enabled_urls": 0,
            "total_scrapes": 0,
            "total_jobs_found": 0,
        }
