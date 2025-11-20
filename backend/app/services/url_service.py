"""URL service for managing search URLs."""
import logging
from typing import Optional, List, Dict, Any
from pydantic import HttpUrl

from ..models import SearchURLModel
from ..repositories import URLRepository

logger = logging.getLogger(__name__)


class URLService:
    """Service for search URL operations."""

    def __init__(self):
        """Initialize URL service."""
        self.url_repo = URLRepository()

    async def get_url_by_id(self, url_id: str) -> Optional[Dict[str, Any]]:
        """
        Get URL by ID.

        Args:
            url_id: URL ID

        Returns:
            URL dict or None
        """
        return await self.url_repo.find_by_id(url_id)

    async def get_all_urls(
        self,
        enabled_only: bool = False,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """
        Get all URLs with pagination.

        Args:
            enabled_only: Only return enabled URLs
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Dict with URLs list and pagination info
        """
        skip = (page - 1) * page_size

        urls, total = await self.url_repo.get_all(
            enabled_only=enabled_only,
            skip=skip,
            limit=page_size,
        )

        total_pages = (total + page_size - 1) // page_size

        return {
            "urls": urls,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            },
        }

    async def get_enabled_urls(self) -> List[Dict[str, Any]]:
        """
        Get all enabled URLs.

        Returns:
            List of enabled URLs
        """
        return await self.url_repo.get_enabled_urls()

    async def create_url(
        self, url: HttpUrl, name: str, enabled: bool = True
    ) -> str:
        """
        Create a new search URL.

        Args:
            url: URL to add
            name: Friendly name for the URL
            enabled: Whether URL is enabled

        Returns:
            Created URL ID
        """
        search_url = SearchURLModel(
            url=url,
            name=name,
            enabled=enabled,
        )

        url_id = await self.url_repo.create(search_url)
        logger.info(f"Created search URL: {name} ({url})")

        return url_id

    async def update_url(
        self,
        url_id: str,
        name: Optional[str] = None,
        enabled: Optional[bool] = None,
    ) -> bool:
        """
        Update a search URL.

        Args:
            url_id: URL ID
            name: New name (optional)
            enabled: New enabled status (optional)

        Returns:
            True if updated, False otherwise
        """
        update_data: Dict[str, Any] = {}

        if name is not None:
            update_data["name"] = name

        if enabled is not None:
            update_data["enabled"] = enabled

        if not update_data:
            return False

        updated = await self.url_repo.update(url_id, update_data)

        if updated:
            logger.info(f"Updated URL {url_id}: {update_data}")

        return updated

    async def delete_url(self, url_id: str) -> bool:
        """
        Delete a search URL.

        Args:
            url_id: URL ID

        Returns:
            True if deleted, False otherwise
        """
        # Check if URL exists
        url = await self.url_repo.find_by_id(url_id)
        if not url:
            return False

        deleted = await self.url_repo.delete(url_id)

        if deleted:
            logger.info(f"Deleted URL: {url_id}")

        return deleted

    async def toggle_url(self, url_id: str) -> Optional[bool]:
        """
        Toggle URL enabled status.

        Args:
            url_id: URL ID

        Returns:
            New enabled status or None if not found
        """
        toggled = await self.url_repo.toggle_enabled(url_id)

        if toggled:
            url = await self.url_repo.find_by_id(url_id)
            if url:
                new_status = url.get("enabled", True)
                logger.info(f"Toggled URL {url_id} to {new_status}")
                return new_status

        return None

    async def get_url_stats(self) -> Dict[str, Any]:
        """
        Get URL statistics.

        Returns:
            Statistics dict
        """
        return await self.url_repo.get_stats()

    async def record_scrape_result(
        self,
        url_id: str,
        jobs_found: int = 0,
        error: Optional[str] = None,
    ) -> bool:
        """
        Record scrape result for a URL.

        Args:
            url_id: URL ID
            jobs_found: Number of jobs found
            error: Error message if scrape failed

        Returns:
            True if recorded, False otherwise
        """
        if error:
            return await self.url_repo.update_last_error(url_id, error)
        else:
            return await self.url_repo.increment_scrape_count(url_id, jobs_found)

    async def validate_url(self, url: str) -> bool:
        """
        Validate that a URL is a valid Upwork search URL.

        Args:
            url: URL to validate

        Returns:
            True if valid, False otherwise
        """
        # Basic validation
        if not url.startswith("https://www.upwork.com/"):
            return False

        # Check if it's a search URL
        valid_paths = ["/nx/search/jobs", "/search/jobs"]
        return any(path in url for path in valid_paths)
