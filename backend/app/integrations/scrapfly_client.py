"""Scrapfly client for web scraping."""
import asyncio
import logging
from typing import Optional, Dict, Any, List
from scrapfly import ScrapflyClient as ScrapflySDK, ScrapeConfig, ScrapeApiResponse

from ..config import settings

logger = logging.getLogger(__name__)


class ScrapflyClient:
    """Client for Scrapfly web scraping service."""

    def __init__(self):
        """Initialize Scrapfly client."""
        self._client: Optional[ScrapflySDK] = None
        self._semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_REQUESTS)

    async def initialize(self):
        """Initialize the Scrapfly SDK client."""
        if not self._client:
            self._client = ScrapflySDK(
                key=settings.SCRAPFLY_API_KEY,
                max_concurrency=settings.MAX_CONCURRENT_REQUESTS,
            )
            logger.info("Scrapfly client initialized")

    async def close(self):
        """Close the Scrapfly client."""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("Scrapfly client closed")

    async def scrape_url(
        self,
        url: str,
        render_js: bool = True,
        wait_for_selector: Optional[str] = None,
        retry_on_error: bool = True,
        max_retries: int = 3,
        asp: bool = True,
        **kwargs,
    ) -> Optional[ScrapeApiResponse]:
        """
        Scrape a URL using Scrapfly.

        Args:
            url: URL to scrape
            render_js: Whether to render JavaScript
            wait_for_selector: CSS selector to wait for before returning
            retry_on_error: Whether to retry on errors
            max_retries: Maximum number of retries
            asp: Enable Anti-Scraping Protection bypass
            **kwargs: Additional ScrapeConfig parameters

        Returns:
            ScrapeApiResponse or None if failed
        """
        if not self._client:
            await self.initialize()

        async with self._semaphore:
            scrape_config = ScrapeConfig(
                url=url,
                render_js=render_js,
                asp=asp,
                retry=retry_on_error,
                country=settings.SCRAPFLY_COUNTRY,
                **kwargs,
            )

            if wait_for_selector:
                scrape_config.wait_for_selector = wait_for_selector

            for attempt in range(max_retries):
                try:
                    logger.debug(f"Scraping URL: {url} (attempt {attempt + 1}/{max_retries})")
                    result = await self._client.async_scrape(scrape_config)
                    logger.info(f"Successfully scraped: {url}")
                    return result

                except Exception as e:
                    logger.error(f"Error scraping {url} (attempt {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    else:
                        logger.error(f"Failed to scrape {url} after {max_retries} attempts")
                        return None

    async def scrape_search_page(self, url: str) -> Optional[str]:
        """
        Scrape an Upwork search page.

        Args:
            url: Search page URL

        Returns:
            HTML content or None if failed
        """
        result = await self.scrape_url(
            url=url,
            render_js=True,
            wait_for_selector=settings.SEARCH_PAGE_WAIT_SELECTOR,
            asp=True,
        )

        if result and result.success:
            return result.content
        return None

    async def scrape_detail_page(self, url: str) -> Optional[str]:
        """
        Scrape an Upwork job detail page.

        Args:
            url: Job detail URL

        Returns:
            HTML content or None if failed
        """
        result = await self.scrape_url(
            url=url,
            render_js=True,
            wait_for_selector=settings.DETAIL_PAGE_WAIT_SELECTOR,
            asp=True,
        )

        if result and result.success:
            return result.content
        return None

    async def batch_scrape(
        self,
        urls: List[str],
        scrape_type: str = "search",
    ) -> Dict[str, Optional[str]]:
        """
        Scrape multiple URLs concurrently.

        Args:
            urls: List of URLs to scrape
            scrape_type: Type of scraping ("search" or "detail")

        Returns:
            Dictionary mapping URLs to their HTML content
        """
        if scrape_type == "detail":
            scrape_func = self.scrape_detail_page
        else:
            scrape_func = self.scrape_search_page

        tasks = [scrape_func(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            url: (result if not isinstance(result, Exception) else None)
            for url, result in zip(urls, results)
        }

    async def get_account_info(self) -> Optional[Dict[str, Any]]:
        """
        Get Scrapfly account information.

        Returns:
            Account info dict or None if failed
        """
        if not self._client:
            await self.initialize()

        try:
            account = await self._client.account()
            return {
                "subscription": account.subscription,
                "requests_used": account.requests_used,
                "requests_limit": account.requests_limit,
                "requests_remaining": account.requests_limit - account.requests_used,
            }
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return None
