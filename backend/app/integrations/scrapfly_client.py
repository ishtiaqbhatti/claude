"""Scrapfly client for web scraping."""
import asyncio
import hashlib
import json
import logging
from datetime import datetime, timedelta, UTC
from pathlib import Path
from typing import Optional, Dict, Any, List
from scrapfly import ScrapflyClient as ScrapflySDK, ScrapeConfig, ScrapeApiResponse

from ..config import settings

logger = logging.getLogger(__name__)


class APIKeyManager:
    """Manages API key rotation and rate limit tracking."""

    def __init__(self, api_keys: List[str]):
        """Initialize with list of API keys."""
        self.api_keys = api_keys if isinstance(api_keys, list) else [api_keys]
        self.current_index = 0
        self.key_cooldowns: Dict[str, datetime] = {}
        self.key_usage: Dict[str, int] = {key: 0 for key in self.api_keys}

    def get_next_key(self) -> str:
        """Get next available API key (round-robin with cooldown check)."""
        now = datetime.now(UTC)

        # Try each key starting from current index
        for _ in range(len(self.api_keys)):
            key = self.api_keys[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.api_keys)

            # Check if key is in cooldown
            if key in self.key_cooldowns:
                if now < self.key_cooldowns[key]:
                    continue  # Skip this key, it's in cooldown
                else:
                    # Cooldown expired, remove it
                    del self.key_cooldowns[key]

            # Key is available
            self.key_usage[key] = self.key_usage.get(key, 0) + 1
            return key

        # All keys in cooldown, return first key anyway
        logger.warning("All API keys in cooldown, using first key")
        return self.api_keys[0]

    def mark_rate_limited(self, key: str, cooldown_minutes: int = 60):
        """Mark a key as rate-limited with cooldown period."""
        self.key_cooldowns[key] = datetime.now(UTC) + timedelta(minutes=cooldown_minutes)
        logger.warning(f"API key marked as rate-limited until {self.key_cooldowns[key]}")

    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics for all keys."""
        return {
            "total_keys": len(self.api_keys),
            "keys_in_cooldown": len(self.key_cooldowns),
            "usage_per_key": self.key_usage.copy(),
            "cooldown_status": {
                key: cooldown.isoformat()
                for key, cooldown in self.key_cooldowns.items()
            }
        }


class CacheManager:
    """Manages file-based caching for scraped content."""

    def __init__(self, cache_dir: Path, expiry_minutes: int = 1440):
        """Initialize cache manager."""
        self.cache_dir = cache_dir
        self.expiry_minutes = expiry_minutes
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.hits = 0
        self.misses = 0

    def _get_cache_key(self, url: str, params: Dict[str, Any]) -> str:
        """Generate SHA256 cache key from URL and parameters."""
        cache_string = f"{url}:{json.dumps(params, sort_keys=True)}"
        return hashlib.sha256(cache_string.encode()).hexdigest()

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get file path for cache key."""
        # Organize cache files in subdirectories by first 2 chars
        subdir = cache_key[:2]
        cache_subdir = self.cache_dir / subdir
        cache_subdir.mkdir(exist_ok=True)
        return cache_subdir / f"{cache_key}.json"

    def get(self, url: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get cached content if available and not expired."""
        if not settings.ENABLE_CACHE:
            return None

        cache_key = self._get_cache_key(url, params)
        cache_path = self._get_cache_path(cache_key)

        if not cache_path.exists():
            self.misses += 1
            return None

        try:
            with open(cache_path, 'r') as f:
                cached_data = json.load(f)

            # Check expiry
            cached_at = datetime.fromisoformat(cached_data['cached_at'])
            expiry_time = cached_at + timedelta(minutes=self.expiry_minutes)

            if datetime.now(UTC) > expiry_time:
                # Cache expired
                cache_path.unlink()
                self.misses += 1
                return None

            self.hits += 1
            logger.debug(f"Cache hit for {url[:50]}...")
            return cached_data['content']

        except Exception as e:
            logger.error(f"Error reading cache: {e}")
            self.misses += 1
            return None

    def set(self, url: str, params: Dict[str, Any], content: Dict[str, Any]):
        """Cache content for URL and parameters."""
        if not settings.ENABLE_CACHE:
            return

        cache_key = self._get_cache_key(url, params)
        cache_path = self._get_cache_path(cache_key)

        try:
            cached_data = {
                'url': url,
                'params': params,
                'content': content,
                'cached_at': datetime.now(UTC).isoformat(),
            }

            with open(cache_path, 'w') as f:
                json.dump(cached_data, f)

            logger.debug(f"Cached content for {url[:50]}...")

        except Exception as e:
            logger.error(f"Error writing cache: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

        # Count cache files
        cache_files = list(self.cache_dir.rglob("*.json"))

        return {
            "enabled": settings.ENABLE_CACHE,
            "cache_dir": str(self.cache_dir),
            "expiry_minutes": self.expiry_minutes,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(hit_rate, 2),
            "total_cached_files": len(cache_files),
        }


class ContentValidator:
    """Validates scraped content for quality and blocks."""

    # Common CAPTCHA indicators
    CAPTCHA_INDICATORS = [
        "captcha",
        "recaptcha",
        "hcaptcha",
        "cloudflare",
        "challenge",
        "unusual traffic",
        "verify you are human",
        "security check",
    ]

    # Common block indicators
    BLOCK_INDICATORS = [
        "access denied",
        "403 forbidden",
        "blocked",
        "rate limit",
        "too many requests",
        "suspended",
    ]

    @staticmethod
    def validate_content(html: str, url: str) -> Dict[str, Any]:
        """
        Validate scraped content.

        Returns:
            Dict with validation results including any issues found
        """
        html_lower = html.lower()
        issues = []

        # Check for CAPTCHA
        for indicator in ContentValidator.CAPTCHA_INDICATORS:
            if indicator in html_lower:
                issues.append({
                    "type": "captcha",
                    "indicator": indicator,
                    "severity": "high"
                })
                break

        # Check for blocks
        for indicator in ContentValidator.BLOCK_INDICATORS:
            if indicator in html_lower:
                issues.append({
                    "type": "blocked",
                    "indicator": indicator,
                    "severity": "high"
                })
                break

        # Check content length
        if len(html) < 1000:
            issues.append({
                "type": "content_too_short",
                "length": len(html),
                "severity": "medium"
            })

        # Check for empty body
        if "<body" in html_lower and "</body>" in html_lower:
            body_start = html_lower.find("<body")
            body_end = html_lower.find("</body>")
            body_content = html[body_start:body_end]
            if len(body_content.strip()) < 500:
                issues.append({
                    "type": "empty_body",
                    "severity": "medium"
                })

        validation_result = {
            "valid": len(issues) == 0,
            "issues": issues,
            "content_length": len(html),
            "url": url,
        }

        if issues:
            logger.warning(f"Content validation issues for {url}: {issues}")

        return validation_result


class ScrapflyClient:
    """Client for Scrapfly web scraping service with advanced features."""

    def __init__(self):
        """Initialize Scrapfly client."""
        self._client: Optional[ScrapflySDK] = None
        self._semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_REQUESTS)

        # Initialize managers
        api_keys = settings.SCRAPFLY_API_KEY.split(',') if ',' in settings.SCRAPFLY_API_KEY else [settings.SCRAPFLY_API_KEY]
        self.api_key_manager = APIKeyManager(api_keys)
        self.cache_manager = CacheManager(settings.CACHE_DIR, settings.CACHE_EXPIRY_MINUTES)
        self.validator = ContentValidator()

    async def initialize(self):
        """Initialize the Scrapfly SDK client."""
        if not self._client:
            # Use first API key for initialization (will rotate on requests)
            initial_key = self.api_key_manager.get_next_key()
            self._client = ScrapflySDK(
                key=initial_key,
                max_concurrency=settings.MAX_CONCURRENT_REQUESTS,
            )
            logger.info(f"Scrapfly client initialized with {len(self.api_key_manager.api_keys)} API key(s)")

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
        Scrape a URL using Scrapfly with caching and validation.

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

        # Check cache first
        cache_params = {
            "render_js": render_js,
            "asp": asp,
            "country": settings.SCRAPFLY_COUNTRY,
            **kwargs
        }
        cached_result = self.cache_manager.get(url, cache_params)
        if cached_result:
            logger.info(f"Returning cached content for {url}")
            # Reconstruct ScrapeApiResponse-like dict
            return type('CachedResponse', (), cached_result)()

        current_key = None
        async with self._semaphore:
            for attempt in range(max_retries):
                try:
                    # Get next available API key
                    current_key = self.api_key_manager.get_next_key()

                    # Update client with current key
                    self._client.config.key = current_key

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

                    logger.debug(f"Scraping URL: {url} (attempt {attempt + 1}/{max_retries})")
                    result = await self._client.async_scrape(scrape_config)

                    # Validate content
                    validation = self.validator.validate_content(result.content, url)

                    if not validation['valid']:
                        # Check if validation issue is severe
                        severe_issues = [i for i in validation['issues'] if i['severity'] == 'high']
                        if severe_issues:
                            logger.error(f"Content validation failed for {url}: {severe_issues}")

                            # If CAPTCHA or block detected, mark key as rate-limited
                            issue_types = [i['type'] for i in severe_issues]
                            if 'captcha' in issue_types or 'blocked' in issue_types:
                                self.api_key_manager.mark_rate_limited(current_key, cooldown_minutes=30)

                            if attempt < max_retries - 1:
                                await asyncio.sleep(2 ** attempt)
                                continue
                            return None

                    # Cache successful result
                    cache_content = {
                        'content': result.content,
                        'success': result.success,
                        'status_code': result.status_code if hasattr(result, 'status_code') else 200,
                    }
                    self.cache_manager.set(url, cache_params, cache_content)

                    logger.info(f"Successfully scraped: {url}")
                    return result

                except Exception as e:
                    error_str = str(e).lower()

                    # Check for rate limiting
                    if '429' in error_str or 'rate limit' in error_str:
                        if current_key:
                            self.api_key_manager.mark_rate_limited(current_key)

                    logger.error(f"Error scraping {url} (attempt {attempt + 1}/{max_retries}): {e}")

                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    else:
                        logger.error(f"Failed to scrape {url} after {max_retries} attempts")
                        return None

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
        Get comprehensive Scrapfly account information and client stats.

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
                "api_key_stats": self.api_key_manager.get_stats(),
                "cache_stats": self.cache_manager.get_stats(),
            }
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return None

    def get_client_stats(self) -> Dict[str, Any]:
        """
        Get client statistics without making API calls.

        Returns:
            Dict with cache and API key stats
        """
        return {
            "api_keys": self.api_key_manager.get_stats(),
            "cache": self.cache_manager.get_stats(),
        }
