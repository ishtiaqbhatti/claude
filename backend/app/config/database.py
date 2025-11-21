"""Database connection and management."""
import logging
from typing import Optional, Dict, Any, Callable, Awaitable
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING, IndexModel
from pymongo.errors import ConnectionFailure

from .settings import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """MongoDB database connection manager."""

    _client: Optional[AsyncIOMotorClient] = None
    _database: Optional[AsyncIOMotorDatabase] = None

    @classmethod
    async def connect(cls) -> None:
        """Establish connection to MongoDB."""
        if cls._client and cls._database:
            logger.info("MongoDB already connected")
            return

        try:
            cls._client = AsyncIOMotorClient(
                settings.MONGODB_URI,
                maxPoolSize=100,
                minPoolSize=10,
                maxIdleTimeMS=30000,
                serverSelectionTimeoutMS=5000
            )
            cls._database = cls._client[settings.DATABASE_NAME]

            # Test connection
            await cls._client.admin.command('ping')
            logger.info(f"Connected to MongoDB: {settings.DATABASE_NAME}")

            # Create indexes
            await cls._create_indexes()

        except ConnectionFailure as e:
            logger.critical(f"Failed to connect to MongoDB: {e}")
            raise
        except Exception as e:
            logger.critical(f"Unexpected error during MongoDB connection: {e}")
            raise

    @classmethod
    async def disconnect(cls) -> None:
        """Close MongoDB connection."""
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._database = None
            logger.info("Disconnected from MongoDB")

    @classmethod
    async def get_database(cls) -> AsyncIOMotorDatabase:
        """Get database instance."""
        if not cls._database:
            await cls.connect()
        if not cls._database:
            raise ConnectionError("Database connection not established")
        return cls._database

    @classmethod
    def get_collection(cls, collection_name: str):
        """Get collection instance synchronously."""
        if not cls._database:
            raise ConnectionError("Database not connected. Call connect() first.")
        return cls._database[collection_name]

    @classmethod
    async def _create_indexes(cls) -> None:
        """Create database indexes."""
        db = await cls.get_database()

        # Jobs collection
        jobs = db[settings.COLLECTION_JOBS]
        await jobs.create_indexes([
            IndexModel([("uid", ASCENDING)], unique=True, name="uid_unique"),
            IndexModel([("status", ASCENDING)], name="status_idx"),
            IndexModel([("created_at", DESCENDING)], name="created_at_idx"),
            IndexModel([("pipeline.discovered_at", DESCENDING)], name="discovered_at_idx"),
            IndexModel([("pipeline.is_enriched", ASCENDING)], name="is_enriched_idx"),
            IndexModel(
                [("title", "text"), ("content.description_plain", "text")],
                name="job_text_search_idx"
            ),
        ])

        # Clients collection
        clients = db[settings.COLLECTION_CLIENTS]
        await clients.create_indexes([
            IndexModel([("client_key", ASCENDING)], unique=True, name="client_key_unique"),
            IndexModel([("created_at", DESCENDING)], name="created_at_idx"),
        ])

        # Skills collection
        skills = db[settings.COLLECTION_SKILLS]
        await skills.create_indexes([
            IndexModel([("uid", ASCENDING)], unique=True, name="uid_unique"),
            IndexModel([("name", ASCENDING)], name="name_idx"),
            IndexModel([("stats.job_count", DESCENDING)], name="job_count_idx"),
        ])

        # Search URLs collection
        search_urls = db[settings.COLLECTION_SEARCH_URLS]
        await search_urls.create_indexes([
            IndexModel([("id", ASCENDING)], unique=True, name="id_unique"),
            IndexModel([("enabled", ASCENDING)], name="enabled_idx"),
        ])

        # Scrape runs collection
        scrape_runs = db[settings.COLLECTION_SCRAPE_RUNS]
        await scrape_runs.create_indexes([
            IndexModel([("run_id", ASCENDING)], unique=True, name="run_id_unique"),
            IndexModel([("status", ASCENDING)], name="status_idx"),
            IndexModel([("started_at", DESCENDING)], name="started_at_idx"),
        ])

        logger.info("Database indexes created successfully")

    @classmethod
    async def health_check(cls) -> Dict[str, Any]:
        """Check database health."""
        try:
            if not cls._client:
                return {"status": "disconnected"}

            await cls._client.admin.command('ping')
            db = await cls.get_database()

            return {
                "status": "connected",
                "database": settings.DATABASE_NAME,
                "collections": {
                    "jobs": await db[settings.COLLECTION_JOBS].count_documents({}),
                    "clients": await db[settings.COLLECTION_CLIENTS].count_documents({}),
                    "skills": await db[settings.COLLECTION_SKILLS].count_documents({}),
                    "urls": await db[settings.COLLECTION_SEARCH_URLS].count_documents({}),
                    "runs": await db[settings.COLLECTION_SCRAPE_RUNS].count_documents({}),
                }
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "error", "error": str(e)}

    @classmethod
    async def run_in_transaction(
        cls,
        operations_callback: Callable[[Any], Awaitable[Any]]
    ) -> Any:
        """Execute operations within a transaction."""
        if not cls._client:
            await cls.connect()
        if not cls._client:
            raise ConnectionError("MongoDB client not connected")

        async with await cls._client.start_session() as session:
            async with session.start_transaction():
                try:
                    result = await operations_callback(session)
                    return result
                except Exception as e:
                    logger.error(f"Transaction failed: {e}")
                    raise
