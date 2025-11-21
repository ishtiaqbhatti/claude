"""Scraping service for orchestrating web scraping operations."""
import asyncio
import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from collections.abc import AsyncIterator
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from ..config import DatabaseManager, settings
from ..models import JobModel, JobStatus, ClientModel, SkillModel, ScrapeRunModel, ScrapeErrorLog, PipelineModel
from ..repositories import (
    JobRepository,
    ClientRepository,
    SkillRepository,
    URLRepository,
    ScrapeRunRepository,
)
from ..integrations import ScrapflyClient, UpworkExtractorClient
from ..infrastructure.sse_manager import sse_manager

logger = logging.getLogger(__name__)


class ScrapingService:
    """Service for orchestrating scraping operations."""

    def __init__(self):
        """Initialize scraping service."""
        self.job_repo = JobRepository()
        self.client_repo = ClientRepository()
        self.skill_repo = SkillRepository()
        self.url_repo = URLRepository()
        self.scrape_run_repo = ScrapeRunRepository()
        self.scrapfly = ScrapflyClient()
        self.extractor = UpworkExtractorClient()

    async def initialize(self):
        """Initialize external clients."""
        await self.scrapfly.initialize()

    async def cleanup(self):
        """Cleanup resources."""
        await self.scrapfly.close()

    async def start_search_scrape(
        self,
        url_ids: Optional[List[str]] = None,
        triggered_by: str = "api",
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Start search scraping process with SSE updates.

        Args:
            url_ids: Optional list of URL IDs to scrape (None = all enabled)
            triggered_by: Source that triggered the scrape

        Yields:
            SSE events with progress updates
        """
        # Create scrape run
        scrape_run = ScrapeRunModel(
            run_type="search",
            triggered_by=triggered_by,
        )
        await self.scrape_run_repo.create(scrape_run)

        yield {
            "event": "run_started",
            "data": {
                "run_id": scrape_run.run_id,
                "run_type": "search",
                "status": "running",
            },
        }

        try:
            # Update status to running
            await self.scrape_run_repo.update_status(scrape_run.run_id, "running")

            # Get URLs to scrape
            if url_ids:
                urls = await self.url_repo.find_by_ids(url_ids)
            else:
                urls, _ = await self.url_repo.get_all(enabled_only=True)

            if not urls:
                await self.scrape_run_repo.update_status(scrape_run.run_id, "completed")
                yield {
                    "event": "run_completed",
                    "data": {"run_id": scrape_run.run_id, "message": "No URLs to scrape"},
                }
                return

            total_urls = len(urls)

            # Process each URL
            for idx, url_doc in enumerate(urls):
                url_id = url_doc["id"]
                url = str(url_doc["url"])

                yield {
                    "event": "url_started",
                    "data": {"url_id": url_id, "url": url, "progress": idx / total_urls},
                }

                try:
                    # Send progress via SSEManager
                    await sse_manager.send_scraping_progress(
                        run_id=scrape_run.run_id,
                        progress_percentage=(idx / total_urls) * 100,
                        current_item=url,
                        total_items=total_urls,
                        processed_items=idx,
                        status_message=f"Scraping search page: {url_doc.get('name', url)}",
                    )

                    # Scrape search page with retry
                    html_content = await self._scrape_with_retry(url, "search")

                    if not html_content:
                        error = ScrapeErrorLog(
                            message="Failed to scrape URL",
                            item_id=url_id,
                        )
                        await self.scrape_run_repo.add_error(scrape_run.run_id, error)
                        await self.url_repo.update_last_error(url_id, "Failed to scrape")
                        await sse_manager.send_error(
                            run_id=scrape_run.run_id,
                            error=f"Failed to scrape URL: {url}",
                        )
                        continue

                    # Archive raw HTML
                    self._save_raw_html_to_file(html_content, url_id, "search")

                    # Extract jobs
                    jobs_data = self.extractor.extract_search_results(html_content)

                    # Process jobs
                    jobs_new = 0
                    jobs_updated = 0

                    for job_data in jobs_data:
                        try:
                            result = await self._process_search_job(job_data, scrape_run.run_id)
                            if result == "new":
                                jobs_new += 1
                            elif result == "updated":
                                jobs_updated += 1
                        except Exception as e:
                            logger.error(f"Error processing job {job_data.get('uid')}: {e}")

                    # Update stats
                    await self.scrape_run_repo.increment_counters(
                        scrape_run.run_id,
                        jobs_found=len(jobs_data),
                        jobs_new=jobs_new,
                        jobs_updated=jobs_updated,
                    )
                    await self.url_repo.increment_scrape_count(url_id, len(jobs_data))

                    yield {
                        "event": "url_completed",
                        "data": {
                            "url_id": url_id,
                            "jobs_found": len(jobs_data),
                            "jobs_new": jobs_new,
                            "jobs_updated": jobs_updated,
                        },
                    }

                except Exception as e:
                    logger.error(f"Error scraping URL {url}: {e}")
                    error = ScrapeErrorLog(
                        message=str(e),
                        item_id=url_id,
                    )
                    await self.scrape_run_repo.add_error(scrape_run.run_id, error)

                # Update progress
                progress = (idx + 1) / total_urls * 100
                await self.scrape_run_repo.update_progress(scrape_run.run_id, progress)

            # Complete run
            await self.scrape_run_repo.update_status(scrape_run.run_id, "completed")

            # Get final stats
            final_run = await self.scrape_run_repo.find_by_run_id(scrape_run.run_id)

            # Send completion via SSEManager
            await sse_manager.send_completion(
                run_id=scrape_run.run_id,
                results={
                    "jobs_found": final_run.get("jobs_found", 0),
                    "jobs_new": final_run.get("jobs_new", 0),
                    "jobs_updated": final_run.get("jobs_updated", 0),
                },
                status="completed"
            )

            yield {
                "event": "run_completed",
                "data": {
                    "run_id": scrape_run.run_id,
                    "status": "completed",
                    "jobs_found": final_run.get("jobs_found", 0),
                    "jobs_new": final_run.get("jobs_new", 0),
                    "jobs_updated": final_run.get("jobs_updated", 0),
                },
            }

        except Exception as e:
            logger.error(f"Error in search scrape: {e}")
            await self.scrape_run_repo.update_status(scrape_run.run_id, "failed")
            yield {
                "event": "run_failed",
                "data": {"run_id": scrape_run.run_id, "error": str(e)},
            }

    async def start_detail_scrape(
        self,
        job_uids: Optional[List[str]] = None,
        limit: int = 50,
        triggered_by: str = "api",
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Start detail scraping process with SSE updates.

        Args:
            job_uids: Optional list of job UIDs to scrape (None = discovered jobs)
            limit: Maximum number of jobs to scrape
            triggered_by: Source that triggered the scrape

        Yields:
            SSE events with progress updates
        """
        # Create scrape run
        scrape_run = ScrapeRunModel(
            run_type="detail",
            triggered_by=triggered_by,
        )
        await self.scrape_run_repo.create(scrape_run)

        yield {
            "event": "run_started",
            "data": {
                "run_id": scrape_run.run_id,
                "run_type": "detail",
                "status": "running",
            },
        }

        try:
            # Update status to running
            await self.scrape_run_repo.update_status(scrape_run.run_id, "running")

            # Get jobs to scrape
            if job_uids:
                jobs = await self.job_repo.find_by_uids(job_uids)
            else:
                jobs = await self.job_repo.get_discovered_jobs(limit)

            if not jobs:
                await self.scrape_run_repo.update_status(scrape_run.run_id, "completed")
                yield {
                    "event": "run_completed",
                    "data": {"run_id": scrape_run.run_id, "message": "No jobs to scrape"},
                }
                return

            total_jobs = len(jobs)

            # Process each job
            for idx, job_doc in enumerate(jobs):
                job_uid = job_doc["uid"]
                job_url = str(job_doc.get("url", ""))

                if not job_url:
                    logger.warning(f"Job {job_uid} has no URL")
                    continue

                yield {
                    "event": "job_started",
                    "data": {"job_uid": job_uid, "progress": idx / total_jobs},
                }

                try:
                    # Send progress via SSEManager
                    await sse_manager.send_scraping_progress(
                        run_id=scrape_run.run_id,
                        progress_percentage=(idx / total_jobs) * 100,
                        current_item=job_uid,
                        total_items=total_jobs,
                        processed_items=idx,
                        status_message=f"Scraping job detail: {job_uid}",
                    )

                    # Update status to scraping
                    await self.job_repo.update_status(job_uid, JobStatus.SCRAPING_DETAIL)

                    # Scrape detail page with retry
                    html_content = await self._scrape_with_retry(job_url, "detail")

                    if not html_content:
                        await self.job_repo.update_status(job_uid, JobStatus.DETAIL_FAILED)
                        error = ScrapeErrorLog(
                            message="Failed to scrape job detail",
                            item_id=job_uid,
                        )
                        await self.scrape_run_repo.add_error(scrape_run.run_id, error)
                        await self.scrape_run_repo.increment_counters(scrape_run.run_id, jobs_failed=1)
                        await sse_manager.send_error(
                            run_id=scrape_run.run_id,
                            error=f"Failed to scrape job: {job_uid}",
                        )
                        continue

                    # Archive raw HTML
                    self._save_raw_html_to_file(html_content, job_uid, "detail")

                    # Extract job detail
                    job_detail = self.extractor.extract_job_detail(html_content)

                    if not job_detail:
                        await self.job_repo.update_status(job_uid, JobStatus.EXTRACTION_FAILED)
                        error = ScrapeErrorLog(
                            message="Failed to extract job detail",
                            item_id=job_uid,
                        )
                        await self.scrape_run_repo.add_error(scrape_run.run_id, error)
                        await self.scrape_run_repo.increment_counters(scrape_run.run_id, jobs_failed=1)
                        continue

                    # Update job with detail
                    await self._update_job_with_detail(job_uid, job_detail, scrape_run.run_id)

                    await self.scrape_run_repo.increment_counters(
                        scrape_run.run_id,
                        jobs_updated=1,
                    )

                    yield {
                        "event": "job_completed",
                        "data": {"job_uid": job_uid},
                    }

                except Exception as e:
                    logger.error(f"Error scraping job {job_uid}: {e}")
                    await self.job_repo.update_status(job_uid, JobStatus.DETAIL_FAILED)
                    error = ScrapeErrorLog(
                        message=str(e),
                        item_id=job_uid,
                    )
                    await self.scrape_run_repo.add_error(scrape_run.run_id, error)
                    await self.scrape_run_repo.increment_counters(scrape_run.run_id, jobs_failed=1)

                # Update progress
                progress = (idx + 1) / total_jobs * 100
                await self.scrape_run_repo.update_progress(scrape_run.run_id, progress)

            # Complete run
            await self.scrape_run_repo.update_status(scrape_run.run_id, "completed")

            # Get final stats
            final_run = await self.scrape_run_repo.find_by_run_id(scrape_run.run_id)

            # Send completion via SSEManager
            await sse_manager.send_completion(
                run_id=scrape_run.run_id,
                results={
                    "jobs_updated": final_run.get("jobs_updated", 0),
                    "jobs_failed": final_run.get("jobs_failed", 0),
                },
                status="completed"
            )

            yield {
                "event": "run_completed",
                "data": {
                    "run_id": scrape_run.run_id,
                    "status": "completed",
                    "jobs_updated": final_run.get("jobs_updated", 0),
                    "jobs_failed": final_run.get("jobs_failed", 0),
                },
            }

        except Exception as e:
            logger.error(f"Error in detail scrape: {e}")
            await self.scrape_run_repo.update_status(scrape_run.run_id, "failed")
            await sse_manager.send_error(
                run_id=scrape_run.run_id,
                error=str(e),
            )
            yield {
                "event": "run_failed",
                "data": {"run_id": scrape_run.run_id, "error": str(e)},
            }

    async def _process_search_job(
        self, job_data: Dict[str, Any], run_id: str
    ) -> str:
        """
        Process a job from search results.

        Returns:
            "new" if job was created, "updated" if job was updated, "skipped" if skipped
        """
        job_uid = job_data["uid"]

        # Check if job exists
        existing_job = await self.job_repo.find_by_uid(job_uid)

        if existing_job:
            # Update existing job
            update_data = {
                "title": job_data["title"],
                "updated_at": datetime.now(UTC),
            }
            await self.job_repo.update(job_uid, update_data)
            return "updated"
        else:
            # Create new job
            job = JobModel(
                uid=job_uid,
                title=job_data["title"],
                url=job_data.get("url"),
                status=JobStatus.DISCOVERED,
                ciphertext=job_data.get("ciphertext"),
                budget=job_data.get("budget", {}),
                content=job_data.get("content", {}),
                published_on=job_data.get("published_on"),
                created_on=job_data.get("created_on"),
                run_id=run_id,
                pipeline=PipelineModel(
                    source="search",
                    discovered_at=datetime.now(UTC),
                ),
            )
            await self.job_repo.create(job)
            return "new"

    async def _update_job_with_detail(
        self, job_uid: str, job_detail: Dict[str, Any], run_id: str
    ):
        """Update job with detail page data."""
        # Process client
        client_id = None
        if job_detail.get("client"):
            client_data = job_detail["client"]
            client_key = f"{client_data.get('country')}_{client_data.get('company', 'unknown')}"

            client = ClientModel(
                client_key=client_key,
                country=client_data.get("country"),
                city=client_data.get("city"),
                company=client_data.get("company"),
                total_spent=client_data.get("total_spent"),
                total_hires=client_data.get("total_hires"),
                active_contracts=client_data.get("active_contracts"),
                payment_verified=client_data.get("payment_verified", False),
                rating=client_data.get("rating"),
                reviews_count=client_data.get("reviews_count"),
            )
            client_id = await self.client_repo.upsert(client)

        # Process skills
        for skill_data in job_detail.get("content", {}).get("skills", []):
            skill = SkillModel(
                uid=skill_data["uid"],
                name=skill_data["name"],
                pretty_name=skill_data["name"],
            )
            await self.skill_repo.upsert(skill)
            await self.skill_repo.increment_job_count(skill_data["uid"])

        # Update job
        update_data = {
            "content": job_detail.get("content", {}),
            "budget": job_detail.get("budget", {}),
            "client_id": client_id,
            "experience_level": job_detail.get("experience_level"),
            "duration": job_detail.get("duration"),
            "workload": job_detail.get("workload"),
            "project_type": job_detail.get("project_type"),
            "category_name": job_detail.get("category_name"),
            "published_on": job_detail.get("published_on"),
            "created_on": job_detail.get("created_on"),
            "renewed_on": job_detail.get("renewed_on"),
            "was_renewed": job_detail.get("was_renewed", False),
            "pipeline.detail_scraped_at": datetime.now(UTC),
            "status": JobStatus.ENRICHED.value,
        }

        await self.job_repo.update(job_uid, update_data)
        await self.job_repo.mark_as_enriched(job_uid)

    # ==================== Helper Methods ====================

    def _save_raw_html_to_file(
        self,
        html_content: str,
        job_uid: str,
        page_type: str = "detail"
    ) -> Optional[Path]:
        """
        Save raw HTML to file for debugging and analysis.

        Args:
            html_content: Raw HTML content
            job_uid: Job UID (used for filename)
            page_type: Type of page (search, detail, etc.)

        Returns:
            Path to saved file or None if failed
        """
        try:
            # Create directory structure: cache/html/YYYY-MM-DD/page_type/
            date_str = datetime.now(UTC).strftime("%Y-%m-%d")
            html_dir = settings.CACHE_DIR / "html" / date_str / page_type
            html_dir.mkdir(parents=True, exist_ok=True)

            # Clean job_uid for filename (remove special chars)
            clean_uid = re.sub(r'[^\w\-]', '_', job_uid)
            timestamp = datetime.now(UTC).strftime("%H%M%S")
            filename = f"{clean_uid}_{timestamp}.html"
            file_path = html_dir / filename

            # Write HTML to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            logger.debug(f"Saved raw HTML to {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"Error saving raw HTML for {job_uid}: {e}")
            return None

    def _decode_engagement(self, engagement_value: Optional[str]) -> Optional[str]:
        """
        Decode Upwork engagement type from encoded value.

        Args:
            engagement_value: Raw engagement value from Upwork

        Returns:
            Decoded engagement type or None
        """
        if not engagement_value:
            return None

        # Common Upwork engagement mappings
        engagement_map = {
            "1": "One-time project",
            "2": "Ongoing project",
            "3": "Complex project",
            "4": "Not sure",
        }

        # Try direct mapping
        if engagement_value in engagement_map:
            return engagement_map[engagement_value]

        # Try pattern matching for encoded values
        if "ongoing" in engagement_value.lower():
            return "Ongoing project"
        elif "one" in engagement_value.lower() or "single" in engagement_value.lower():
            return "One-time project"
        elif "complex" in engagement_value.lower():
            return "Complex project"

        # Return as-is if no match
        logger.debug(f"Unknown engagement value: {engagement_value}")
        return engagement_value

    def _decode_tier(self, tier_value: Optional[str]) -> Optional[str]:
        """
        Decode Upwork client tier from encoded value.

        Args:
            tier_value: Raw tier value from Upwork

        Returns:
            Decoded tier name or None
        """
        if not tier_value:
            return None

        # Common Upwork tier mappings
        tier_map = {
            "1": "Basic",
            "2": "Plus",
            "3": "Enterprise",
            "UNSET": "No tier",
            "PAYMENT_UNVERIFIED": "Payment unverified",
        }

        # Try direct mapping
        tier_upper = tier_value.upper()
        if tier_upper in tier_map:
            return tier_map[tier_upper]

        # Pattern matching
        if "plus" in tier_value.lower():
            return "Plus"
        elif "enterprise" in tier_value.lower():
            return "Enterprise"
        elif "basic" in tier_value.lower():
            return "Basic"

        # Return as-is if no match
        logger.debug(f"Unknown tier value: {tier_value}")
        return tier_value

    def _extract_search_position(
        self, job_data: Dict[str, Any], search_context: Optional[Dict[str, Any]] = None
    ) -> Optional[int]:
        """
        Extract job's search position/ranking from search results.

        Args:
            job_data: Job data dictionary
            search_context: Optional context with page number and position

        Returns:
            Search position (1-based) or None
        """
        # If explicit position provided in job data
        if "search_position" in job_data:
            return job_data["search_position"]

        # Calculate from search context
        if search_context:
            page = search_context.get("page", 1)
            position_in_page = search_context.get("position_in_page", 0)
            jobs_per_page = search_context.get("jobs_per_page", 50)

            # Calculate absolute position
            return (page - 1) * jobs_per_page + position_in_page + 1

        # Try to extract from job data metadata
        if "metadata" in job_data:
            metadata = job_data["metadata"]
            if isinstance(metadata, dict) and "position" in metadata:
                return metadata["position"]

        return None

    # ==================== Retry Decorators ====================

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((asyncio.TimeoutError, ConnectionError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    async def _scrape_with_retry(self, url: str, scrape_type: str = "search") -> Optional[str]:
        """
        Scrape URL with automatic retry on transient failures.

        Args:
            url: URL to scrape
            scrape_type: Type of scraping (search or detail)

        Returns:
            HTML content or None if failed
        """
        if scrape_type == "detail":
            return await self.scrapfly.scrape_detail_page(url)
        else:
            return await self.scrapfly.scrape_search_page(url)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((ConnectionError, asyncio.TimeoutError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    async def _db_operation_with_retry(self, operation_func, *args, **kwargs):
        """
        Execute database operation with automatic retry.

        Args:
            operation_func: Async function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Result of the operation
        """
        return await operation_func(*args, **kwargs)
