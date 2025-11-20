"""Client repository for database operations."""
from datetime import UTC, datetime
from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorClientSession

from ..config import DatabaseManager
from ..models import ClientModel


class ClientRepository:
    """Repository for client operations."""

    def __init__(self):
        self.collection_name = "clients"

    @property
    def collection(self):
        """Get clients collection."""
        return DatabaseManager.get_collection(self.collection_name)

    async def find_by_key(self, client_key: str) -> Optional[Dict[str, Any]]:
        """Find client by unique key."""
        return await self.collection.find_one({"client_key": client_key})

    async def find_by_id(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Find client by ID."""
        return await self.collection.find_one({"_id": client_id})

    async def exists(self, client_key: str) -> bool:
        """Check if client exists."""
        count = await self.collection.count_documents({"client_key": client_key}, limit=1)
        return count > 0

    async def create(
        self, client: ClientModel, session: Optional[AsyncIOMotorClientSession] = None
    ) -> str:
        """Create a new client."""
        client_dict = client.model_dump(by_alias=True, exclude={"id"})
        result = await self.collection.insert_one(client_dict, session=session)
        return str(result.inserted_id)

    async def upsert(
        self, client: ClientModel, session: Optional[AsyncIOMotorClientSession] = None
    ) -> str:
        """Create or update client."""
        client_dict = client.model_dump(by_alias=True, exclude={"id"})
        client_dict["updated_at"] = datetime.now(UTC)

        result = await self.collection.update_one(
            {"client_key": client.client_key},
            {"$set": client_dict, "$setOnInsert": {"created_at": datetime.now(UTC)}},
            upsert=True,
            session=session,
        )

        if result.upserted_id:
            return str(result.upserted_id)

        # Get existing document ID
        doc = await self.find_by_key(client.client_key)
        return str(doc["_id"]) if doc else ""

    async def update(
        self,
        client_key: str,
        update_data: Dict[str, Any],
        session: Optional[AsyncIOMotorClientSession] = None,
    ) -> bool:
        """Update client by key."""
        update_data["updated_at"] = datetime.now(UTC)
        result = await self.collection.update_one(
            {"client_key": client_key}, {"$set": update_data}, session=session
        )
        return result.modified_count > 0

    async def increment_job_count(
        self,
        client_key: str,
        session: Optional[AsyncIOMotorClientSession] = None,
    ) -> bool:
        """Increment total jobs count."""
        result = await self.collection.update_one(
            {"client_key": client_key},
            {
                "$inc": {"total_jobs": 1},
                "$set": {"updated_at": datetime.now(UTC)},
            },
            session=session,
        )
        return result.modified_count > 0

    async def get_all(
        self, skip: int = 0, limit: int = 50
    ) -> tuple[List[Dict[str, Any]], int]:
        """Get all clients with pagination."""
        total = await self.collection.count_documents({})
        cursor = self.collection.find({}).skip(skip).limit(limit)
        clients = await cursor.to_list(length=limit)
        return clients, total

    async def search(
        self,
        query: Optional[str] = None,
        country: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[List[Dict[str, Any]], int]:
        """Search clients."""
        filters: Dict[str, Any] = {}

        if query:
            filters["$or"] = [
                {"company": {"$regex": query, "$options": "i"}},
                {"city": {"$regex": query, "$options": "i"}},
            ]

        if country:
            filters["country"] = country

        total = await self.collection.count_documents(filters)
        cursor = self.collection.find(filters).skip(skip).limit(limit)
        clients = await cursor.to_list(length=limit)

        return clients, total

    async def get_stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_clients": {"$sum": 1},
                    "verified_clients": {
                        "$sum": {"$cond": [{"$eq": ["$payment_verified", True]}, 1, 0]}
                    },
                    "avg_total_spent": {"$avg": "$total_spent"},
                    "avg_total_jobs": {"$avg": "$total_jobs"},
                }
            }
        ]

        cursor = self.collection.aggregate(pipeline)
        results = await cursor.to_list(length=1)

        if results:
            result = results[0]
            return {
                "total_clients": result.get("total_clients", 0),
                "verified_clients": result.get("verified_clients", 0),
                "avg_total_spent": result.get("avg_total_spent", 0.0),
                "avg_total_jobs": result.get("avg_total_jobs", 0),
            }

        return {
            "total_clients": 0,
            "verified_clients": 0,
            "avg_total_spent": 0.0,
            "avg_total_jobs": 0,
        }
