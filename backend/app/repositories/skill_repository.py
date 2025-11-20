"""Skill repository for database operations."""
from datetime import UTC, datetime
from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorClientSession

from ..config import DatabaseManager
from ..models import SkillModel


class SkillRepository:
    """Repository for skill operations."""

    def __init__(self):
        self.collection_name = "skills"

    @property
    def collection(self):
        """Get skills collection."""
        return DatabaseManager.get_collection(self.collection_name)

    async def find_by_uid(self, uid: str) -> Optional[Dict[str, Any]]:
        """Find skill by UID."""
        return await self.collection.find_one({"uid": uid})

    async def find_by_uids(self, uids: List[str]) -> List[Dict[str, Any]]:
        """Find skills by UIDs."""
        cursor = self.collection.find({"uid": {"$in": uids}})
        return await cursor.to_list(length=None)

    async def exists(self, uid: str) -> bool:
        """Check if skill exists."""
        count = await self.collection.count_documents({"uid": uid}, limit=1)
        return count > 0

    async def create(
        self, skill: SkillModel, session: Optional[AsyncIOMotorClientSession] = None
    ) -> str:
        """Create a new skill."""
        skill_dict = skill.model_dump(by_alias=True, exclude={"id"})
        result = await self.collection.insert_one(skill_dict, session=session)
        return str(result.inserted_id)

    async def upsert(
        self, skill: SkillModel, session: Optional[AsyncIOMotorClientSession] = None
    ) -> str:
        """Create or update skill."""
        skill_dict = skill.model_dump(by_alias=True, exclude={"id"})
        skill_dict["updated_at"] = datetime.now(UTC)
        skill_dict["last_seen_at"] = datetime.now(UTC)

        result = await self.collection.update_one(
            {"uid": skill.uid},
            {
                "$set": skill_dict,
                "$setOnInsert": {
                    "created_at": datetime.now(UTC),
                    "first_seen_at": datetime.now(UTC),
                },
            },
            upsert=True,
            session=session,
        )

        if result.upserted_id:
            return str(result.upserted_id)

        # Get existing document ID
        doc = await self.find_by_uid(skill.uid)
        return str(doc["_id"]) if doc else ""

    async def update(
        self,
        uid: str,
        update_data: Dict[str, Any],
        session: Optional[AsyncIOMotorClientSession] = None,
    ) -> bool:
        """Update skill by UID."""
        update_data["updated_at"] = datetime.now(UTC)
        result = await self.collection.update_one(
            {"uid": uid}, {"$set": update_data}, session=session
        )
        return result.modified_count > 0

    async def increment_job_count(
        self,
        uid: str,
        count: int = 1,
        session: Optional[AsyncIOMotorClientSession] = None,
    ) -> bool:
        """Increment job count for skill."""
        result = await self.collection.update_one(
            {"uid": uid},
            {
                "$inc": {"job_count": count},
                "$set": {
                    "updated_at": datetime.now(UTC),
                    "last_seen_at": datetime.now(UTC),
                },
            },
            session=session,
        )
        return result.modified_count > 0

    async def bulk_increment_job_count(
        self,
        uids: List[str],
        session: Optional[AsyncIOMotorClientSession] = None,
    ) -> int:
        """Bulk increment job count for multiple skills."""
        result = await self.collection.update_many(
            {"uid": {"$in": uids}},
            {
                "$inc": {"job_count": 1},
                "$set": {
                    "updated_at": datetime.now(UTC),
                    "last_seen_at": datetime.now(UTC),
                },
            },
            session=session,
        )
        return result.modified_count

    async def get_all(
        self, skip: int = 0, limit: int = 50
    ) -> tuple[List[Dict[str, Any]], int]:
        """Get all skills with pagination."""
        total = await self.collection.count_documents({})
        cursor = (
            self.collection.find({})
            .sort("job_count", -1)
            .skip(skip)
            .limit(limit)
        )
        skills = await cursor.to_list(length=limit)
        return skills, total

    async def search(
        self,
        query: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[List[Dict[str, Any]], int]:
        """Search skills by name."""
        filters: Dict[str, Any] = {}

        if query:
            filters["$or"] = [
                {"name": {"$regex": query, "$options": "i"}},
                {"pretty_name": {"$regex": query, "$options": "i"}},
            ]

        total = await self.collection.count_documents(filters)
        cursor = (
            self.collection.find(filters)
            .sort("job_count", -1)
            .skip(skip)
            .limit(limit)
        )
        skills = await cursor.to_list(length=limit)

        return skills, total

    async def get_top_skills(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get top skills by job count."""
        cursor = (
            self.collection.find({})
            .sort("job_count", -1)
            .limit(limit)
        )
        return await cursor.to_list(length=limit)

    async def get_stats(self) -> Dict[str, Any]:
        """Get skill statistics."""
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_skills": {"$sum": 1},
                    "total_jobs": {"$sum": "$job_count"},
                    "avg_jobs_per_skill": {"$avg": "$job_count"},
                }
            }
        ]

        cursor = self.collection.aggregate(pipeline)
        results = await cursor.to_list(length=1)

        if results:
            result = results[0]
            return {
                "total_skills": result.get("total_skills", 0),
                "total_jobs": result.get("total_jobs", 0),
                "avg_jobs_per_skill": result.get("avg_jobs_per_skill", 0.0),
            }

        return {
            "total_skills": 0,
            "total_jobs": 0,
            "avg_jobs_per_skill": 0.0,
        }
