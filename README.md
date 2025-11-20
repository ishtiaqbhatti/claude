File Summary
Purpose
This file contains a packed representation of the entire repository's contents. It is designed to be easily consumable by AI systems for analysis, code review, or other automated processes.

File Format
The content is organized as follows:

This summary section
Repository information
Directory structure
Multiple file entries, each consisting of: a. A header with the file path (## File: path/to/file) b. The full contents of the file in a code block
Usage Guidelines
This file should be treated as read-only. Any changes should be made to the original repository files, not this packed version.
When processing this file, use the file path to distinguish between different files in the repository.
Be aware that this file may contain sensitive information. Handle it with the same level of security as you would the original repository.
Notes
Some files may have been excluded based on .gitignore rules and Repomix's configuration.
Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files.
Additional Info
Directory Structure
src/
  upwork_scraper/
    api/
      controllers/
        __init__.py
        job_controller.py
        scraping_controller.py
        url_controller.py
      __init__.py
      dependencies.py
      main.py
    application/
      __init__.py
      dtos.py
      services.py
    domain/
      models/
        __init__.py
        client.py
        job.py
        scrape_run.py
        skill.py
        url.py
      __init__.py
      exceptions.py
      repositories.py
    infrastructure/
      database/
        repositories/
          __init__.py
          mongo_client_repository.py
          mongo_job_repository.py
          mongo_scrape_run_repository.py
          mongo_skill_repository.py
          mongo_url_repository.py
        __init__.py
        connection.py
      scraping/
        __init__.py
        scrapfly_client.py
        upwork_extractor_client.py
      sse/
        __init__.py
        sse_manager.py
      __init__.py
    __init__.py
    config.py
upwork_extractor/
  models/
    __init__.py
    activity.py
    client.py
    enums.py
    job.py
    quality.py
    skills.py
  parsers/
    __init__.py
    html_parser.py
    nuxt_parser.py
    schema_parser.py
    selectors.py
  utils/
    __init__.py
    date_utils.py
    text_utils.py
    validation.py
  __init__.py
  config.py
  exceptions.py
  extractor.py
  main.py
  mappers.py
  pyproject.toml
.env.example
pyproject.toml
README.md
Files
File: src/upwork_scraper/api/controllers/init.py
"""
API Controllers (Routers) for the FastAPI application.
"""
File: src/upwork_scraper/api/controllers/job_controller.py
"""
Job controller for accessing and managing job data.
This controller is lean and delegates all logic to the application services.
"""
import logging
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Dict, Any

from src.upwork_scraper.application import dtos
from src.upwork_scraper.application.services import JobQueryService
from src.upwork_scraper.api.dependencies import get_job_query_service
from src.upwork_scraper.domain.exceptions import EntityNotFoundError, RepositoryError
from src.upwork_scraper.domain.models import job as domain_job_models

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "",
    response_model=dtos.PaginatedJobsResponseDTO,
    summary="Get paginated list of jobs"
)
async def get_jobs(
    query: dtos.GetJobsQuery = Depends(),
    job_query_service: JobQueryService = Depends(get_job_query_service),
):
    """
    Retrieves a paginated list of jobs from the database, with optional
    filtering by status and enrichment status, and customizable sorting.
    """
    try:
        return await job_query_service.get_jobs_paginated(query)
    except RepositoryError as e:
        logger.error(f"Repository error while fetching jobs: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {str(e)}")
    except Exception as e:
        logger.exception("An unexpected error occurred while fetching jobs:")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")


@router.get(
    "/stats",
    response_model=Dict[str, Any],
    summary="Get overall job statistics"
)
async def get_job_statistics(
    job_query_service: JobQueryService = Depends(get_job_query_service),
):
    """
    Retrieves aggregated statistics about the jobs in the database,
    including total count, enriched count, and daily discoveries.
    """
    try:
        return await job_query_service.get_job_statistics()
    except RepositoryError as e:
        logger.error(f"Repository error while fetching job statistics: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {str(e)}")
    except Exception as e:
        logger.exception("An unexpected error occurred while fetching job statistics:")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")


@router.get(
    "/{job_uid}",
    response_model=domain_job_models.JobModel,
    summary="Get a specific job by UID"
)
async def get_job(
    job_uid: str,
    job_query_service: JobQueryService = Depends(get_job_query_service),
):
    """
    Retrieves details for a single job using its unique identifier (UID).
    """
    try:
        return await job_query_service.get_job_by_uid(job_uid)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RepositoryError as e:
        logger.error(f"Repository error while fetching job '{job_uid}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {str(e)}")
    except Exception as e:
        logger.exception(f"An unexpected error occurred while fetching job '{job_uid}':")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")


@router.get(
    "/search",
    response_model=dtos.PaginatedJobsResponseDTO,
    summary="Search jobs by keywords"
)
async def search_jobs(
    query: dtos.SearchJobsQuery = Depends(),
    job_query_service: JobQueryService = Depends(get_job_query_service),
):
    """
    Searches for jobs by keywords in their title or plain text description.
    Results are paginated.
    """
    try:
        return await job_query_service.search_jobs_paginated(query)
    except RepositoryError as e:
        logger.error(f"Repository error while searching jobs for '{query.q}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {str(e)}")
    except Exception as e:
        logger.exception(f"An unexpected error occurred while searching jobs for '{query.q}':")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")


@router.get(
    "/recent/discovered",
    response_model=List[domain_job_models.JobModel],
    summary="Get recently discovered jobs"
)
async def get_recent_jobs(
    query: dtos.GetRecentJobsQuery = Depends(),
    job_query_service: JobQueryService = Depends(get_job_query_service),
):
    """
    Retrieves a list of the most recently discovered jobs, ordered by their
    discovery timestamp.
    """
    try:
        return await job_query_service.get_recent_jobs(limit=query.limit)
    except RepositoryError as e:
        logger.error(f"Repository error while fetching recent jobs: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {str(e)}")
    except Exception as e:
        logger.exception("An unexpected error occurred while fetching recent jobs:")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")


@router.get(
    "/pending/enrichment",
    response_model=List[domain_job_models.JobModel],
    summary="Get jobs pending detail enrichment"
)
async def get_jobs_pending_enrichment(
    query: dtos.GetJobsPendingEnrichmentQuery = Depends(),
    job_query_service: JobQueryService = Depends(get_job_query_service),
):
    """
    Retrieves a list of jobs that have been discovered but not yet fully
    enriched with detail page data. These are typically prioritized for
    detail scraping.
    """
    try:
        return await job_query_service.get_jobs_pending_enrichment(limit=query.limit)
    except RepositoryError as e:
        logger.error(f"Repository error while fetching jobs pending enrichment: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {str(e)}")
    except Exception as e:
        logger.exception("An unexpected error occurred while fetching jobs pending enrichment:")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")
File: src/upwork_scraper/api/controllers/scraping_controller.py
"""
Scraping controller for triggering and monitoring scraping operations.
This controller is lean and delegates all logic to the application services.
"""
import logging
import asyncio
import json
from datetime import datetime, UTC
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, status
from fastapi.responses import StreamingResponse

from src.upwork_scraper.application import dtos
from src.upwork_scraper.application.services import ScrapingOrchestrationService, ScrapeRunQueryService
from src.upwork_scraper.api.dependencies import get_scraping_orchestration_service, get_scrape_run_query_service, get_sse_manager
from src.upwork_scraper.infrastructure.sse.sse_manager import SSEManager
from src.upwork_scraper.domain.exceptions import DomainError, EntityNotFoundError, ScrapeAlreadyInProgressError, RepositoryError, ScrapingError
from src.upwork_scraper.domain.models import scrape_run as domain_scrape_run_models
from src.upwork_scraper.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/search/start",
    response_model=dtos.ScrapeRunResultDTO,
    summary="Start scraping search URLs"
)
async def start_search_scraping(
    command: dtos.StartSearchScrapeCommand,
    scraping_service: ScrapingOrchestrationService = Depends(get_scraping_orchestration_service),
):
    """
    Initiates the scraping process for search result URLs.
    
    If `url_ids` are provided, only those specific URLs will be scraped.
    If `url_ids` is empty or not provided, all currently enabled and ready search URLs
    will be scraped.
    The scraping runs in the background, and its progress can be monitored
    via the SSE endpoint (`/api/scraping/status/{run_id}/stream`).
    """
    try:
        return await scraping_service.start_search_scrape(command)
    except ScrapeAlreadyInProgressError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except DomainError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except (RepositoryError, ScrapingError) as e:
        logger.error(f"Error initiating search scraping: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Scraping or storage error: {str(e)}")
    except Exception as e:
        logger.exception("An unexpected error occurred while starting search scraping:")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")


@router.post(
    "/detail/start",
    response_model=dtos.ScrapeRunResultDTO,
    summary="Start scraping job details"
)
async def start_detail_scraping(
    command: dtos.StartDetailScrapeCommand,
    scraping_service: ScrapingOrchestrationService = Depends(get_scraping_orchestration_service),
):
    """
    Initiates the scraping process for individual job detail pages.
    
    If `job_uids` are provided, only those specific jobs will have their details scraped.
    If `job_uids` is empty or not provided, the system will identify and scrape a `limit`
    number of jobs that are marked as 'discovered' but not yet 'enriched'.
    The scraping runs in the background and can be monitored via the SSE endpoint.
    """
    try:
        return await scraping_service.start_detail_scrape_batch(command)
    except ScrapeAlreadyInProgressError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except DomainError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except (RepositoryError, ScrapingError) as e:
        logger.error(f"Error initiating detail scraping: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Scraping or storage error: {str(e)}")
    except Exception as e:
        logger.exception("An unexpected error occurred while starting detail scraping:")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")


@router.post(
    "/detail/{job_uid}",
    response_model=dtos.SingleScrapeResultDTO,
    summary="Scrape details for a single job"
)
async def scrape_single_job_detail(
    job_uid: str,
    background_tasks: BackgroundTasks,
    scraping_service: ScrapingOrchestrationService = Depends(get_scraping_orchestration_service),
):
    """
    Triggers the scraping and enrichment process for a single job's detail page.
    This runs in the background. To monitor progress, use the job's UID as the `run_id`
    in the `/api/scraping/status/{run_id}/stream` endpoint.
    """
    try:
        # Use job_uid as the run_id for single scrapes for easy tracking
        stream_run_id = job_uid

        async def run_scraping_task():
            result_dto = await scraping_service._process_single_job_detail(
                job_uid=job_uid, job_url=None, scrape_run_id=stream_run_id
            )
            await scraping_service.sse_manager.send_completion(stream_run_id, result_dto.model_dump())

        background_tasks.add_task(run_scraping_task)
        logger.info(f"Single job detail scraping initiated for job {job_uid}.")

        return dtos.SingleScrapeResultDTO(
            job_uid=job_uid,
            status="started",
            final_status="scraping_detail",
            stream_run_id=stream_run_id,
        )
    except EntityNotFoundError as e: # This might be raised if the job doesn't exist before starting
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (RepositoryError, ScrapingError) as e:
        logger.error(f"Error initiating single job detail scraping for '{job_uid}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Scraping or storage error: {str(e)}")
    except Exception as e:
        logger.exception(f"An unexpected error occurred while starting single job detail scraping for '{job_uid}':")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")


@router.get(
    "/status/{run_id}/stream",
    summary="Stream real-time scraping status",
    response_class=StreamingResponse
)
async def stream_scraping_status(
    run_id: str,
    sse_manager: SSEManager = Depends(get_sse_manager),
    run_query_service: ScrapeRunQueryService = Depends(get_scrape_run_query_service),
):
    """
    Establishes a Server-Sent Events (SSE) connection to stream real-time
    progress and status updates for a specific scraping run identified by `run_id`.
    Clients should reconnect if the connection is lost.
    """
    async def event_generator():
        # First, check if the run is already completed in the database
        try:
            run_from_db = await run_query_service.get_scrape_run_by_id(run_id)
            if run_from_db.status in ["completed", "failed", "completed_with_errors"]:
                logger.info(f"SSE client connected to completed run {run_id}. Sending final status and closing.")
                final_state = {
                    "type": "completion",
                    "run_id": run_id,
                    "status": run_from_db.status,
                    "results": run_from_db.model_dump(mode='json')
                }
                yield f"data: {json.dumps(final_state)}\n\n"
                return # End the generator
        except EntityNotFoundError:
            # If the run is not in DB yet, it might be a single job scrape using job_uid
            pass
        except Exception:
            # If DB check fails, proceed to live stream but log error
            logger.exception(f"Error checking initial run status for {run_id} from DB.")
        
        # If not completed, connect to the live stream
        queue = await sse_manager.connect(run_id)

        try:
            # Send initial state from memory if available
            initial_state = sse_manager.run_status.get(run_id)
            if initial_state:
                yield f"data: {json.dumps(initial_state)}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'connected', 'run_id': run_id, 'timestamp': datetime.now(UTC).isoformat()})}\n\n"

            while True:
                try:
                    update = await asyncio.wait_for(queue.get(), timeout=settings.SSE_HEARTBEAT_INTERVAL)
                    yield f"data: {json.dumps(update)}\n\n"
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'type': 'heartbeat', 'run_id': run_id, 'timestamp': datetime.now(UTC).isoformat()})}\n\n"
                except asyncio.CancelledError:
                    logger.info(f"SSE client disconnected from run {run_id}")
                    break
        finally:
            sse_manager.disconnect(run_id)
            logger.info(f"SSE event generator for run {run_id} finished.")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get(
    "/runs",
    response_model=dtos.ScrapeRunListResponseDTO,
    summary="Get recent scrape runs"
)
async def get_scrape_runs(
    query: dtos.GetScrapeRunsQuery = Depends(),
    run_query_service: ScrapeRunQueryService = Depends(get_scrape_run_query_service),
):
    """
    Retrieves a list of recent scraping runs, with options to filter by run type
    and status.
    """
    try:
        runs = await run_query_service.list_scrape_runs(query)
        return dtos.ScrapeRunListResponseDTO(
            runs=[run.model_dump(mode='json') for run in runs],
            count=len(runs)
        )
    except RepositoryError as e:
        logger.error(f"Repository error while retrieving scrape runs: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {str(e)}")
    except Exception as e:
        logger.exception("An unexpected error occurred while retrieving scrape runs:")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")


@router.get(
    "/runs/{run_id}",
    response_model=domain_scrape_run_models.ScrapeRunModel,
    summary="Get details of a specific scrape run"
)
async def get_scrape_run(
    run_id: str,
    run_query_service: ScrapeRunQueryService = Depends(get_scrape_run_query_service),
):
    """
    Retrieves detailed information about a specific scraping run using its `run_id`.
    """
    try:
        return await run_query_service.get_scrape_run_by_id(run_id)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RepositoryError as e:
        logger.error(f"Repository error while retrieving scrape run '{run_id}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {str(e)}")
    except Exception as e:
        logger.exception(f"An unexpected error occurred while retrieving scrape run '{run_id}':")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")
File: src/upwork_scraper/api/controllers/url_controller.py
"""
URL controller for managing search URLs.
This controller is lean and delegates all logic to the URLManagementService.
"""
import logging
from fastapi import APIRouter, HTTPException, Query, Depends, Response, status
from typing import List, Optional, Dict, Any

from src.upwork_scraper.application import dtos
from src.upwork_scraper.application.services import URLManagementService
from src.upwork_scraper.api.dependencies import get_url_management_service
from src.upwork_scraper.domain.exceptions import EntityNotFoundError, RepositoryError, DomainError
from src.upwork_scraper.domain.models import url as domain_url_models

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "",
    response_model=List[domain_url_models.SearchURLModel],
    summary="Get all search URLs"
)
async def get_urls(
    enabled_only: bool = Query(False, description="If true, only returns URLs that are enabled for scraping."),
    category: Optional[str] = Query(None, description="Filters URLs by a specific category."),
    url_service: URLManagementService = Depends(get_url_management_service),
):
    """
    Retrieves a list of all configured search URLs, with optional filtering
    by their enabled status and category.
    """
    try:
        return await url_service.list_urls(enabled_only=enabled_only, category=category)
    except RepositoryError as e:
        logger.error(f"Repository error while fetching URLs: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {str(e)}")
    except Exception as e:
        logger.exception("An unexpected error occurred while fetching URLs:")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")


@router.get(
    "/{url_id}",
    response_model=domain_url_models.SearchURLModel,
    summary="Get a specific search URL by ID"
)
async def get_url(
    url_id: str,
    url_service: URLManagementService = Depends(get_url_management_service),
):
    """
    Retrieves details for a single search URL using its unique identifier (ID).
    """
    try:
        return await url_service.get_url(url_id)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RepositoryError as e:
        logger.error(f"Repository error while fetching URL '{url_id}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {str(e)}")
    except Exception as e:
        logger.exception(f"An unexpected error occurred while fetching URL '{url_id}':")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")


@router.post(
    "",
    response_model=domain_url_models.SearchURLModel,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new search URL"
)
async def create_url(
    command: dtos.CreateURLCommand,
    url_service: URLManagementService = Depends(get_url_management_service),
):
    """
    Creates a new search URL entry in the database.
    Requires the actual URL, a name, and optional category and description.
    """
    try:
        return await url_service.create_url(command)
    except RepositoryError as e:
        logger.error(f"Repository error while creating URL: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {str(e)}")
    except Exception as e:
        logger.exception("An unexpected error occurred while creating URL:")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")


@router.patch(
    "/{url_id}",
    response_model=domain_url_models.SearchURLModel,
    summary="Partially update a search URL"
)
async def update_url(
    url_id: str,
    command: dtos.UpdateURLCommand,
    url_service: URLManagementService = Depends(get_url_management_service),
):
    """
    Partially updates an existing search URL's properties, such as its name, category,
    description, or enabled status.
    """
    try:
        return await url_service.update_url(url_id, command)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DomainError as e: # Catch empty update command
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RepositoryError as e:
        logger.error(f"Repository error while updating URL '{url_id}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {str(e)}")
    except Exception as e:
        logger.exception(f"An unexpected error occurred while updating URL '{url_id}':")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")


@router.put(
    "/{url_id}/toggle",
    response_model=domain_url_models.SearchURLModel,
    summary="Toggle enabled status of a search URL"
)
async def toggle_url(
    url_id: str,
    url_service: URLManagementService = Depends(get_url_management_service),
):
    """
    Toggles the `enabled` status of a specific search URL. If it was enabled,
    it becomes disabled, and vice-versa.
    """
    try:
        return await url_service.toggle_url_status(url_id)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RepositoryError as e:
        logger.error(f"Repository error while toggling URL '{url_id}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {str(e)}")
    except Exception as e:
        logger.exception(f"An unexpected error occurred while toggling URL '{url_id}':")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")


@router.delete(
    "/{url_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a search URL"
)
async def delete_url(
    url_id: str,
    url_service: URLManagementService = Depends(get_url_management_service),
):
    """
    Deletes a search URL from the system using its unique identifier.
    """
    try:
        await url_service.delete_url(url_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT) # Return response with no body
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RepositoryError as e:
        logger.error(f"Repository error while deleting URL '{url_id}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {str(e)}")
    except Exception as e:
        logger.exception(f"An unexpected error occurred while deleting URL '{url_id}':")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")


@router.get(
    "/stats/summary",
    response_model=Dict[str, Any],
    summary="Get statistics about search URLs"
)
async def get_url_statistics(
    url_service: URLManagementService = Depends(get_url_management_service),
):
    """
    Retrieves aggregated statistics regarding all configured search URLs,
    such as total count, enabled/disabled counts, and total jobs found.
    """
    try:
        return await url_service.get_url_statistics()
    except RepositoryError as e:
        logger.error(f"Repository error while fetching URL statistics: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {str(e)}")
    except Exception as e:
        logger.exception("An unexpected error occurred while fetching URL statistics:")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")
File: src/upwork_scraper/api/init.py
"""
API Layer for the Upwork Scraper.
Contains FastAPI controllers, dependencies, and the main application entrypoint.
"""
File: src/upwork_scraper/api/dependencies.py
"""
FastAPI Dependencies for dependency injection.
This is where we instantiate our services and repositories so they can
be injected into the API controllers.
"""
from functools import lru_cache

# Import repositories
from src.upwork_scraper.infrastructure.database.repositories.mongo_job_repository import MongoJobRepository
from src.upwork_scraper.infrastructure.database.repositories.mongo_url_repository import MongoUrlRepository
from src.upwork_scraper.infrastructure.database.repositories.mongo_client_repository import MongoClientRepository
from src.upwork_scraper.infrastructure.database.repositories.mongo_skill_repository import MongoSkillRepository
from src.upwork_scraper.infrastructure.database.repositories.mongo_scrape_run_repository import MongoScrapeRunRepository

# Import adapters and managers
from src.upwork_scraper.infrastructure.scraping.scrapfly_client import ScrapflyClient
from src.upwork_scraper.infrastructure.scraping.upwork_extractor_client import UpworkExtractorAdapter
from src.upwork_scraper.infrastructure.sse.sse_manager import SSEManager

# Import application services
from src.upwork_scraper.application.services import (
    ScrapingOrchestrationService,
    URLManagementService,
    JobQueryService,
    ScrapeRunQueryService,
)

# Use lru_cache to create singleton instances of each dependency
# This is a simple and effective way to manage singletons in FastAPI

@lru_cache()
def get_job_repository() -> MongoJobRepository:
    return MongoJobRepository()

@lru_cache()
def get_url_repository() -> MongoUrlRepository:
    return MongoUrlRepository()

@lru_cache()
def get_client_repository() -> MongoClientRepository:
    return MongoClientRepository()

@lru_cache()
def get_skill_repository() -> MongoSkillRepository:
    return MongoSkillRepository()

@lru_cache()
def get_scrape_run_repository() -> MongoScrapeRunRepository:
    return MongoScrapeRunRepository()

@lru_cache()
def get_scrapfly_adapter() -> ScrapflyClient:
    return ScrapflyClient()

@lru_cache()
def get_upwork_extractor_adapter() -> UpworkExtractorAdapter:
    return UpworkExtractorAdapter()

@lru_cache()
def get_sse_manager() -> SSEManager:
    return SSEManager()


# --- Application Service Dependencies ---

@lru_cache()
def get_scraping_orchestration_service() -> ScrapingOrchestrationService:
    return ScrapingOrchestrationService(
        job_repo=get_job_repository(),
        url_repo=get_url_repository(),
        client_repo=get_client_repository(),
        skill_repo=get_skill_repository(),
        run_repo=get_scrape_run_repository(),
        scrapfly_adapter=get_scrapfly_adapter(),
        extractor_adapter=get_upwork_extractor_adapter(),
        sse_manager=get_sse_manager(),
    )

@lru_cache()
def get_url_management_service() -> URLManagementService:
    return URLManagementService(url_repo=get_url_repository())

@lru_cache()
def get_job_query_service() -> JobQueryService:
    return JobQueryService(job_repo=get_job_repository())

@lru_cache()
def get_scrape_run_query_service() -> ScrapeRunQueryService:
    return ScrapeRunQueryService(run_repo=get_scrape_run_repository())
File: src/upwork_scraper/api/main.py
"""
Main FastAPI application for the Upwork Scraper Backend.
Initializes the application, sets up middleware, routers, and lifecycle events.
"""
import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.upwork_scraper.config import settings
from src.upwork_scraper.infrastructure.database.connection import DatabaseConnectionManager
from src.upwork_scraper.domain.exceptions import DomainError, EntityNotFoundError, ScrapeAlreadyInProgressError
from src.upwork_scraper.infrastructure.sse.sse_manager import SSEManager
from src.upwork_scraper.infrastructure.scraping.scrapfly_client import ScrapflyClient

from .controllers import (
    url_controller,
    job_controller,
    scraping_controller
)

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def sse_cleanup_task():
    """Background task to periodically clean up stale SSE run statuses from memory."""
    sse_manager = SSEManager()
    while True:
        await asyncio.sleep(settings.SSE_STATUS_CLEANUP_INTERVAL_SECONDS)
        await sse_manager.cleanup_stale_status()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles application startup and shutdown events."""
    logger.info("Starting Upwork Scraper API...")
    
    # --- Startup ---
    try:
        await DatabaseConnectionManager.connect()
        logger.info("Connected to MongoDB successfully.")
    except Exception as e:
        logger.critical(f"CRITICAL: Failed to connect to MongoDB during startup: {e}. API will be unhealthy.", exc_info=True)
        # Allow startup to continue, but health checks will fail.
    
    # Start the SSE cleanup background task
    cleanup_task = asyncio.create_task(sse_cleanup_task())
    logger.info("Started SSE status cleanup background task.")

    yield  # Application runs

    # --- Shutdown ---
    logger.info("Shutting down Upwork Scraper API...")
    cleanup_task.cancel() # Stop the background task
    await DatabaseConnectionManager.disconnect()
    logger.info("Disconnected from MongoDB.")


# Create FastAPI app instance
app = FastAPI(
    title="Upwork Scraper API",
    description="API for Upwork job scraping, data management, and monitoring, built with a Hexagonal Architecture.",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(url_controller.router, prefix="/api/urls", tags=["URLs"])
app.include_router(job_controller.router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(scraping_controller.router, prefix="/api/scraping", tags=["Scraping"])

# --- Global Exception Handlers ---

@app.exception_handler(EntityNotFoundError)
async def entity_not_found_exception_handler(request: Request, exc: EntityNotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"message": str(exc)},
    )

@app.exception_handler(ScrapeAlreadyInProgressError)
async def scrape_in_progress_exception_handler(request: Request, exc: ScrapeAlreadyInProgressError):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"message": str(exc), "run_id": exc.run_id},
    )

@app.exception_handler(DomainError)
async def domain_error_exception_handler(request: Request, exc: DomainError):
    # Catches general business logic errors (e.g., bad input to a service)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"message": f"A business rule was violated: {exc}"},
    )

# --- Root and Health Endpoints ---
@app.get("/", summary="Root endpoint for the API")
async def root():
    """Provides basic information about the Upwork Scraper API."""
    return {
        "name": "Upwork Scraper API",
        "version": app.version,
        "status": "running",
        "documentation": "/docs"
    }

@app.get("/health/live", status_code=status.HTTP_200_OK, tags=["Health"])
async def liveness_check():
    """Liveness probe: Checks if the application process is running."""
    return {"status": "alive"}

@app.get("/health/ready", tags=["Health"])
async def readiness_check():
    """
    Readiness probe: Checks if the application is ready to accept traffic.
    Verifies critical dependencies like the database connection.
    """
    try:
        db = await DatabaseConnectionManager.get_database()
        await db.command('ping')
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        logger.critical(f"Readiness check failed: Database is not connected. Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "not_ready", "database": "disconnected", "error": str(e)},
        )

@app.get("/status", tags=["Health"])
async def comprehensive_status_check():
    """
    Performs a comprehensive status check on all dependencies for diagnostics.
    This is not intended to be used as a liveness/readiness probe.
    """
    health_status = {"status": "healthy", "checks": {}}
    
    # Check MongoDB connection and counts
    try:
        db_health = await DatabaseConnectionManager.health_check()
        health_status["checks"]["database"] = db_health
        if db_health["status"] != "connected":
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = {"status": "error", "error": str(e)}

    # Check Scrapfly API status
    try:
        scrapfly_client = ScrapflyClient()
        scrapfly_health = await scrapfly_client.get_account_info()
        health_status["checks"]["scrapfly_api"] = scrapfly_health
        if not scrapfly_health.get("success"):
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["scrapfly_api"] = {"status": "error", "error": str(e)}

    if health_status["status"] == "unhealthy":
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=health_status)
    
    return health_status


if __name__ == "__main__":
    import uvicorn
    # Correct path for running directly
    uvicorn.run(
        "src.upwork_scraper.api.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
File: src/upwork_scraper/application/init.py
"""
Application layer for the Upwork Scraper.
Contains use cases and data transfer objects (DTOs).
"""
File: src/upwork_scraper/application/dtos.py
"""
Data Transfer Objects (DTOs) for the Application Layer.
These Pydantic models define the input (Commands) and output (Results)
structures for the application services/use cases.
"""
from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Dict, Any

# --- Commands (Inputs to Application Services) ---

class CreateURLCommand(BaseModel):
    url: HttpUrl = Field(..., description="The Upwork search URL to store.")
    name: str = Field(..., min_length=3, description="A human-readable name for this search URL.")
    category: Optional[str] = Field(None, description="An optional category or tag to organize URLs.")
    description: Optional[str] = Field(None, description="A brief description of what this search is for.")

class UpdateURLCommand(BaseModel):
    name: Optional[str] = Field(None, min_length=3, description="New human-readable name for the URL.")
    category: Optional[str] = Field(None, description="New category or tag for the URL.")
    description: Optional[str] = Field(None, description="New description for the URL.")
    enabled: Optional[bool] = Field(None, description="Set to true to enable scraping, false to disable.")

class GetJobsQuery(BaseModel):
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(50, ge=1, le=100, description="Items per page")
    status: Optional[str] = Field(None, description="Filter by job status (e.g., 'discovered', 'enriched')")
    enriched: Optional[bool] = Field(None, description="Filter by enrichment status (true/false)")
    sort_by: str = Field("created_at", description="Field to sort by")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="Sort order ('asc' or 'desc')")

class SearchJobsQuery(BaseModel):
    q: str = Field(..., min_length=2, description="Search query string for job title or description")
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(50, ge=1, le=100, description="Items per page")

class GetRecentJobsQuery(BaseModel):
    limit: int = Field(20, ge=1, le=100)

class GetJobsPendingEnrichmentQuery(BaseModel):
    limit: int = Field(50, ge=1, le=100)

class StartSearchScrapeCommand(BaseModel):
    url_ids: Optional[List[str]] = Field(None, description="List of specific URL IDs to scrape. If None, all enabled URLs will be scraped.")
    triggered_by: str = Field("api", description="How the scraping run was triggered (e.g., 'api', 'scheduled').")

class StartDetailScrapeCommand(BaseModel):
    job_uids: Optional[List[str]] = Field(None, description="List of specific job UIDs to scrape. If None, jobs needing enrichment will be selected.")
    limit: int = Field(50, ge=1, le=100, description="Maximum number of jobs to scrape if UIDs are not provided.")
    triggered_by: str = Field("api", description="How the scraping run was triggered (e.g., 'api', 'scheduled').")

class GetScrapeRunsQuery(BaseModel):
    run_type: Optional[str] = Field(None, pattern="^(search|detail)$", description="Filter by run type ('search' or 'detail')")
    status: Optional[str] = Field(None, description="Filter by run status ('pending', 'running', 'completed', 'failed', 'completed_with_errors')")
    limit: int = Field(20, ge=1, le=100, description="Maximum number of runs to retrieve")

# --- Results (Outputs from Application Services) ---

class JobResponseDTO(BaseModel):
    # This will be a subset/full representation of src.upwork_scraper.domain.models.job.JobModel
    # For simplicity, we can use Dict[str, Any] or define a more specific DTO here if needed.
    # But usually, the domain model can be returned directly by application services.
    pass # Will be defined more concretely by the service, possibly returning domain.models.job.JobModel

class PaginatedJobsResponseDTO(BaseModel):
    jobs: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int

class UrlResponseDTO(BaseModel):
    pass # Will be defined more concretely by the service, returning domain.models.url.SearchURLModel

class UrlListResponseDTO(BaseModel):
    urls: List[Dict[str, Any]] # Using Dict[str, Any] for flexibility, can be List[UrlResponseDTO]

class ScrapeRunResponseDTO(BaseModel):
    pass # Will be defined more concretely by the service, returning domain.models.scrape_run.ScrapeRunModel

class ScrapeRunListResponseDTO(BaseModel):
    runs: List[Dict[str, Any]]
    count: int

class StatsResponseDTO(BaseModel):
    # Flexible DTO for various statistics
    pass # Will be defined more concretely by the service, returning Dict[str, Any]

class SingleScrapeResultDTO(BaseModel):
    job_uid: str
    status: str
    final_status: str
    error: Optional[str] = None
    stream_run_id: str = Field(..., description="The ID to use for SSE streaming for this single job scrape.")
File: src/upwork_scraper/application/services.py
"""
Application Services (Use Cases) for the Upwork Scraper.
These orchestrate domain models and repositories to perform business logic.
"""
import asyncio
import logging
import hashlib
from datetime import datetime, UTC
from typing import List, Dict, Any, Optional, Tuple
from pydantic import HttpUrl # Added HttpUrl
from bs4 import BeautifulSoup # Added BeautifulSoup
import random # Added random
import json # Ensure json is imported

from upwork_extractor.utils.text_utils import clean_number, normalize_whitespace # Added clean_number, normalize_whitespace
from upwork_extractor.utils.date_utils import parse_date_flexible, parse_duration_to_weeks # Added date utilities

from src.upwork_scraper.config import settings
from src.upwork_scraper.domain.exceptions import (
    DomainError, RepositoryError, EntityNotFoundError,
    ScrapingError, ScrapeAlreadyInProgressError,
    UpworkExtractionError, UpworkExtractionValidationError
)
from src.upwork_scraper.domain.models import (
    job, url, client, scrape_run,
)
from src.upwork_scraper.domain.repositories import (
    AbstractJobRepository,
    AbstractUrlRepository,
    AbstractClientRepository,
    AbstractSkillRepository,
    AbstractScrapeRunRepository,
    AbstractScrapingAdapter,
    AbstractUpworkExtractorAdapter,
)
from src.upwork_scraper.application import dtos
from src.upwork_scraper.infrastructure.sse.sse_manager import SSEManager

from tenacity import retry, stop_after_attempt, retry_if_exception_type, wait_exponential, before_sleep_log

logger = logging.getLogger(__name__)

# Define a retry strategy for critical internal database updates
# This ensures that even if a scrape fails, we try to record its failure state
RETRY_CRITICAL_DB_UPDATE = retry(
    stop=stop_after_attempt(settings.MAX_RETRIES + 1),
    wait=wait_exponential(multiplier=1, min=2, max=settings.RETRY_DELAY * 2),
    retry=retry_if_exception_type(RepositoryError),
    before_sleep=before_sleep_log(logger, logging.WARNING, exc_info=True),
    reraise=True
)

class ScrapingOrchestrationService:
    """
    Manages the overall scraping workflow, initiating and coordinating
    search and detail scraping operations.
    """
    def __init__(
        self,
        job_repo: AbstractJobRepository,
        url_repo: AbstractUrlRepository,
        client_repo: AbstractClientRepository,
        skill_repo: AbstractSkillRepository,
        run_repo: AbstractScrapeRunRepository,
        scrapfly_adapter: AbstractScrapingAdapter,
        extractor_adapter: AbstractUpworkExtractorAdapter,
        sse_manager: SSEManager,
    ):
        self.job_repo = job_repo
        self.url_repo = url_repo
        self.client_repo = client_repo
        self.skill_repo = skill_repo
        self.run_repo = run_repo
        self.scrapfly_adapter = scrapfly_adapter
        self.extractor_adapter = extractor_adapter
        self.sse_manager = sse_manager

    async def _update_job_status_on_failure(self, job_uid: str, final_status: job.JobStatus, error_message: str):
        """Helper to update job status and error info, with retries."""
        @RETRY_CRITICAL_DB_UPDATE
        async def _attempt_update():
            await self.job_repo.update(
                uid=job_uid,
                updates={
                    "status": final_status.value,
                    "pipeline.optimization_error": error_message,
                    "updated_at": datetime.now(UTC),
                }
            )
        try:
            await _attempt_update()
        except RepositoryError:
            logger.critical(f"CRITICAL: Failed to update job {job_uid} status to {final_status.value} even after retries.")

    async def _process_single_search_page(
        self,
        page_url: str,
        search_url_model: url.SearchURLModel,
        scrape_run: scrape_run.ScrapeRunModel,
        progress_callback: Optional[callable] = None,
    ) -> Dict[str, Any]:
        """
        Fetches and processes a single search result page.
        Returns a dict of counts (jobs_found, jobs_new, jobs_updated).
        """
        page_results = {
            "jobs_found": 0,
            "jobs_new": 0,
            "jobs_updated": 0,
            "errors": [],
            "status": "success",
        }
        
        try:
            scrape_response = await self.scrapfly_adapter.fetch(
                url=page_url,
                country=settings.SCRAPFLY_COUNTRY,
                render_js=True,
                asp=True,
                rendering_wait_ms=settings.SCRAPFLY_RENDERING_WAIT,
                tags=["search_page", search_url_model.id],
                correlation_id=scrape_run.run_id,
            )

            html_content = scrape_response.get("html", "")
            if not html_content:
                raise ScrapingError("Scrapfly returned empty HTML content for search page.")
            
            job_summaries_data = await self.extractor_adapter.extract_search_job_summaries(html_content)
            
            new_count, updated_count = await self._store_search_job_summaries(
                job_summaries_data, scrape_run.run_id
            )

            page_results["jobs_found"] = len(job_summaries_data)
            page_results["jobs_new"] = new_count
            page_results["jobs_updated"] = updated_count

        except (ScrapingError, UpworkExtractionError, UpworkExtractionValidationError, RepositoryError) as e:
            logger.error(f"Error processing search page {page_url} for URL '{search_url_model.name}': {e}", exc_info=True)
            page_results["errors"].append(
                scrape_run.ScrapeErrorLog(message=str(e), item_id=search_url_model.id, details={"page_url": page_url})
            )
            page_results["status"] = "failed"
        except Exception as e:
            logger.exception(f"Unexpected error processing search page {page_url} for URL '{search_url_model.name}':")
            page_results["errors"].append(
                scrape_run.ScrapeErrorLog(message=f"Unexpected error: {str(e)}", item_id=search_url_model.id, details={"page_url": page_url})
            )
            page_results["status"] = "failed"
        
        return page_results

    async def _store_search_job_summaries(self, job_summaries: List[Dict[str, Any]], run_id: str) -> Tuple[int, int]:
        """
        Stores or updates job summaries from search results in the database.
        This operation for a batch of jobs will be transactional.
        """
        new_jobs_count = 0
        updated_jobs_count = 0

        async def _transaction_logic(session: Any): # session type is AsyncIOMotorClientSession
            nonlocal new_jobs_count, updated_jobs_count
            for job_entry in job_summaries:
                job_uid = str(job_entry.get("uid", ""))
                if not job_uid:
                    logger.warning(f"Skipping search job entry with no UID: {job_entry}")
                    continue

                # Prepare skills for upsert and get their ObjectIds
                search_skills_info = [] # Will be a list of SkillInfo
                skill_obj_ids = [] # Will be a list of ObjectId strings
                for attr in job_entry.get("attrs", []):
                    skill_name = attr.get("prefLabel") or attr.get("prettyName")
                    if skill_name:
                        skill_info_item = job.SkillInfo(
                            uid=str(attr.get("uid")) if attr.get("uid") else hashlib.sha256(skill_name.lower().encode("utf-8")).hexdigest(),
                            name=skill_name,
                            category="highlighted" if attr.get("highlighted") else "attribute"
                        )
                        search_skills_info.append(skill_info_item)
                        obj_id = await self.skill_repo.upsert(skill_info_item, increment_job_count=True, session=session)
                        if obj_id:
                            skill_obj_ids.append(obj_id)

                # Map search entry to job model dict
                job_model_dict_partial = self._map_search_entry_to_job_model_dict(job_entry, run_id, skill_obj_ids, search_skills_info)
                
                existing_job = await self.job_repo.get_by_uid(job_uid) # Check if exists before update
                
                if not existing_job:
                    # Insert new job
                    new_job = job.JobModel(**job_model_dict_partial)
                    await self.job_repo.add(new_job, session=session)
                    new_jobs_count += 1
                else:
                    # Update existing job (only if status isn't DELETED/PRIVATE_JOB)
                    if existing_job.status in [job.JobStatus.DELETED, job.JobStatus.PRIVATE_JOB]:
                        logger.info(f"Skipping update for job {job_uid} as it's marked {existing_job.status.value}. Found again in search.")
                        continue

                    # Compare relevant fields to decide if update is needed
                    # This is a simplified comparison, can be made more granular
                    # For search results, we primarily update if content/title/terms/skills changed
                    
                    has_changed = (
                        existing_job.title != job_model_dict_partial.get("title") or
                        existing_job.content.description_plain != job_model_dict_partial.get("content", {}).get("description_plain") or
                        existing_job.terms.model_dump(exclude_none=True) != job_model_dict_partial.get("terms") or
                        set(existing_job.content.skill_ids) != set(skill_obj_ids)
                    )

                    if has_changed:
                        update_payload = {
                            "title": job_model_dict_partial.get("title"),
                            "url": job_model_dict_partial.get("url"),
                            "ciphertext": job_model_dict_partial.get("ciphertext"),
                            "content.description": job_model_dict_partial.get("content", {}).get("description"),
                            "content.description_plain": job_model_dict_partial.get("content", {}).get("description_plain"),
                            "content.skill_ids": skill_obj_ids,
                            "content.skills": search_skills_info,
                            "terms": job_model_dict_partial.get("terms"),
                            "published_on": job_model_dict_partial.get("published_on"),
                            "renewed_on": job_model_dict_partial.get("renewed_on"),
                            "created_on": job_model_dict_partial.get("created_on"),
                            "source_data.search": job_model_dict_partial.get("source_data", {}).get("search"),
                            "updated_at": datetime.now(UTC),
                            "status": job.JobStatus.DISCOVERED.value # Reset to discovered if it was a failed state
                        }
                        await self.job_repo.update(job_uid, update_payload, session=session)
                        updated_jobs_count += 1

        # Use transaction for atomic writes
        from src.upwork_scraper.infrastructure.database.connection import DatabaseConnectionManager
        db_manager = DatabaseConnectionManager()
        try:
            await db_manager.run_in_transaction(_transaction_logic)
        except RepositoryError as e:
            logger.error(f"Transaction failed while storing search job summaries for run {run_id}: {e}", exc_info=True)
            raise ScrapingError(f"Failed to store search job summaries transactionally: {e}")

        logger.debug(f"Summary for run {run_id}: Stored {new_jobs_count} new jobs, updated {updated_jobs_count} existing jobs from search.")
        return new_jobs_count, updated_jobs_count

    def _map_search_entry_to_job_model_dict(self, job_entry: Dict[str, Any], run_id: str, skill_obj_ids: List[str], search_skills_info: List[job.SkillInfo]) -> Dict[str, Any]:
        """
        Maps a raw search job entry to a JobModel dictionary for database storage.
        """
        job_uid = str(job_entry.get("uid", ""))
        job_type_raw = job_entry.get("type") # 1 for hourly, 0 for fixed
        budget_type_str = "hourly" if job_type_raw == 1 else "fixed" # Nuxt type 1 is hourly
        
        budget_min: Optional[float] = None
        budget_max: Optional[float] = None
        budget_available = False

        if budget_type_str == "hourly":
            hourly_budget = job_entry.get("hourlyBudget")
            if isinstance(hourly_budget, dict):
                min_val = clean_number(hourly_budget.get("min"))
                max_val = clean_number(hourly_budget.get("max"))
                if min_val is not None and min_val > 0:
                    budget_min = min_val
                    budget_available = True
                if max_val is not None and max_val > 0:
                    budget_max = max_val
                    budget_available = True
        else: # Fixed price
            amount_data = job_entry.get("amount")
            if isinstance(amount_data, dict):
                amount = clean_number(amount_data.get("amount"))
                if amount is not None and amount > 0:
                    budget_min = amount
                    budget_max = amount
                    budget_available = True
        
        duration_label = job_entry.get("durationLabel")
        duration_label_str = str(duration_label) if duration_label else None
        duration_weeks_val = parse_duration_to_weeks(duration_label_str)

        tier_text = job_entry.get("tierText")
        contractor_tier = self._decode_tier(tier_text) if tier_text else None

        published_on_iso, _ = parse_date_flexible(job_entry.get("publishedOn"))
        created_on_iso, _ = parse_date_flexible(job_entry.get("createdOn"))
        renewed_on_iso, _ = parse_date_flexible(job_entry.get("renewedOn"))
        
        description_raw = job_entry.get("description", "")
        description_plain = normalize_whitespace(BeautifulSoup(description_raw, 'lxml').get_text(separator=' ', strip=True))

        relevance_encoded = job_entry.get("relevanceEncoded")
        search_position = self._extract_search_position(relevance_encoded)

        budget_model = job.BudgetModel(
            available=budget_available,
            type=budget_type_str,
            min=budget_min,
            max=budget_max,
            currency="USD"
        )
        duration_model = job.DurationModel(
            label=duration_label_str,
            min_weeks=duration_weeks_val,
            max_weeks=duration_weeks_val # For search, we typically have a single value or estimate
        )
        terms_model = job.TermsModel(
            budget=budget_model,
            duration=duration_model,
            contractor_tier=contractor_tier,
            engagement=self._decode_engagement(job_entry.get("engagement")),
            project_type=job.ProjectType.from_nuxt_type(budget_type_str).value if job.ProjectType.from_nuxt_type(budget_type_str) else None
        )
        content_model = job.ContentModel(
            description=description_raw,
            description_plain=description_plain,
            skill_ids=skill_obj_ids,
            skills=search_skills_info
        )
        pipeline_model = job.PipelineModel(
            source="search",
            is_enriched=False,
            discovered_at=datetime.now(UTC),
            last_optimization_attempt=datetime.now(UTC),
            optimization_retries=0
        )
        source_data_model = job.SourceDataModel(
            search={
                "ciphertext": job_entry.get("ciphertext"),
                "tier_text": tier_text,
                "published_on_raw": job_entry.get("publishedOn"),
                "created_on_raw": job_entry.get("createdOn"),
                "renewed_on_raw": job_entry.get("renewedOn"),
                "relevance_encoded": relevance_encoded,
                "search_position": search_position,
                "raw_job_entry": job_entry,
            }
        )
        
        job_model = job.JobModel(
            uid=job_uid,
            title=normalize_whitespace(BeautifulSoup(job_entry.get("title", "Untitled"), 'lxml').get_text(separator=' ', strip=True)),
            url=HttpUrl(f"{settings.UPWORK_BASE_URL}/jobs/~{job_entry.get('ciphertext')}") if job_entry.get("ciphertext") else None,
            status=job.JobStatus.DISCOVERED,
            run_id=run_id,
            ciphertext=job_entry.get("ciphertext"),

            content=content_model,
            terms=terms_model,

            published_on=published_on_iso,
            created_on=created_on_iso,
            renewed_on=renewed_on_iso,
            was_renewed=job_entry.get("renewedOn") is not None,

            pipeline=pipeline_model,
            source_data=source_data_model,

            updated_at=datetime.now(UTC),
        )

        return job_model.model_dump(by_alias=True, exclude_none=True)

    def _decode_engagement(self, engagement_key: Optional[str]) -> Optional[str]:
        """Decode Upwork's internal engagement keys to human-readable values"""
        if not engagement_key:
            return None

        engagement_map = {
            "usnuxt_Engagement_421.partTime": "Part Time",
            "usnuxt_Engagement_421.fullTime": "Full Time",
            "usnuxt_Engagement_421.notSure": "Not Sure",
        }
        return engagement_map.get(engagement_key, engagement_key)

    def _decode_tier(self, tier_key: Optional[str]) -> Optional[str]:
        """Decode Upwork's internal tier keys to human-readable values"""
        if not tier_key:
            return None

        tier_map = {
            "jsn_Intermediate_206": "Intermediate",
            "jsn_Expert_207": "Expert",
            "jsn_EntryLevel_205": "Entry Level",
            "IntermediateLevel": "Intermediate", # From Extractor output
            "ExpertLevel": "Expert",             # From Extractor output
            "EntryLevel": "Entry Level",         # From Extractor output
        }
        return tier_map.get(tier_key, tier_key)
    
    def _extract_search_position(self, relevance_encoded: Optional[str]) -> Optional[int]:
        """Extract position from relevanceEncoded JSON string."""
        if not relevance_encoded:
            return None
        try:
            data = json.loads(relevance_encoded)
            return data.get("position")
        except json.JSONDecodeError:
            logger.warning(f"Failed to decode relevanceEncoded JSON: {relevance_encoded[:100]}...")
            return None

    async def _scrape_single_url(
        self,
        search_url_model: url.SearchURLModel,
        scrape_run: scrape_run.ScrapeRunModel,
        progress_callback: Optional[callable] = None,
    ) -> Dict[str, Any]:
        """
        Scrapes a single search URL and all its paginated results.
        Updates the URL's scrape history.
        """
        base_url = str(search_url_model.url)
        logger.info(f"Starting to scrape search URL: '{base_url}' (ID: {search_url_model.id})")

        results = {
            "url_id": search_url_model.id,
            "url": base_url,
            "pages_scraped": 0,
            "jobs_found": 0,
            "jobs_new": 0,
            "jobs_updated": 0,
            "errors": [],
            "status": "completed",
        }

        page = 1
        has_more_pages = True
        
        # New: Use pagination data from NUXT, if available, otherwise fallback to heuristics
        total_pages_from_nuxt: Optional[int] = None
        
        while has_more_pages:
            current_page_url = self._build_page_url(base_url, page)
            if progress_callback:
                await progress_callback({
                    "run_id": scrape_run.run_id,
                    "status": "scraping_search_page",
                    "current_url_id": search_url_model.id,
                    "current_url_name": search_url_model.name,
                    "current_page": page,
                    "total_pages": total_pages_from_nuxt, # Provide total pages if known
                    "jobs_found_in_url": results["jobs_found"]
                })
            
            try:
                logger.info(f"Scraping page {page} for URL '{search_url_model.name}': {current_page_url}")

                scrape_response = await self.scrapfly_adapter.fetch(
                    url=current_page_url,
                    country=settings.SCRAPFLY_COUNTRY,
                    render_js=True,
                    asp=True,
                    rendering_wait_ms=settings.SCRAPFLY_RENDERING_WAIT,
                    tags=["search_page", search_url_model.id],
                    correlation_id=scrape_run.run_id,
                )

                html_content = scrape_response.get("html", "")
                if not html_content:
                    raise ScrapingError("Scrapfly returned empty HTML content for search page.")

                # Extract job summaries and pagination data
                job_summaries_data = await self.extractor_adapter.extract_search_job_summaries(html_content)
                pagination_data = await self.extractor_adapter.extract_pagination_data(html_content)

                if pagination_data:
                    total_pages_from_nuxt = pagination_data.get('total_pages')
                    # Use has_next_page if provided, otherwise infer from job count
                    has_more_pages_from_nuxt = pagination_data.get('current_page') < pagination_data.get('total_pages') if pagination_data.get('total_pages') else True
                    has_more_pages = has_more_pages_from_nuxt and len(job_summaries_data) > 0 # Also ensure jobs were found

                if not job_summaries_data:
                    logger.info(f"No jobs found on page {page} for '{search_url_model.name}', stopping pagination.")
                    has_more_pages = False # Explicitly stop if no jobs
                
                # Store jobs in database
                new_count, updated_count = await self._store_search_job_summaries(
                    job_summaries_data, scrape_run.run_id
                )

                results["jobs_found"] += len(job_summaries_data)
                results["jobs_new"] += new_count
                results["jobs_updated"] += updated_count
                results["pages_scraped"] += 1

                logger.info(f"Page {page} for '{search_url_model.name}': Found {len(job_summaries_data)} jobs "
                            f"({new_count} new, {updated_count} updated).")

                # If no NUXT pagination data, use heuristic
                if total_pages_from_nuxt is None:
                    has_more_pages = len(job_summaries_data) >= settings.UPWORK_SEARCH_PAGE_JOB_COUNT
                
                # Introduce randomized delay between pages
                if has_more_pages:
                    await asyncio.sleep(settings.RETRY_DELAY + random.uniform(0.5, 1.5))
                page += 1

            except (ScrapingError, UpworkExtractionError, UpworkExtractionValidationError) as e:
                error_log_entry = scrape_run.ScrapeErrorLog(
                    message=str(e),
                    item_id=search_url_model.id,
                    details={"page_url": current_page_url, "page": page}
                )
                logger.error(f"Error during search scraping of page {page} for '{search_url_model.name}': {e}", exc_info=True)
                results["errors"].append(error_log_entry)
                results["status"] = "failed"
                has_more_pages = False # Break on error
            except Exception as e:
                error_log_entry = scrape_run.ScrapeErrorLog(
                    message=f"Unexpected error: {str(e)}",
                    item_id=search_url_model.id,
                    details={"page_url": current_page_url, "page": page}
                )
                logger.exception(f"Unexpected error during search scraping of page {page} for '{search_url_model.name}':")
                results["errors"].append(error_log_entry)
                results["status"] = "failed"
                has_more_pages = False # Break on error

        # Update URL scrape history via URL repo
        url_update_payload = {
            "last_scraped_at": datetime.now(UTC) if results["status"] == "completed" else search_url_model.last_scraped_at,
            "last_scrape_job_count": results["jobs_found"] if results["status"] == "completed" else search_url_model.last_scrape_job_count,
            "total_scrape_count": search_url_model.total_scrape_count + 1,
            "total_jobs_found": search_url_model.total_jobs_found + results["jobs_found"],
            "last_error": results["errors"][0].message if results["errors"] else None,
            "last_error_at": results["errors"][0].timestamp if results["errors"] else None,
            "error_count": search_url_model.error_count + (1 if results["errors"] else 0),
            "updated_at": datetime.now(UTC),
        }
        await self.url_repo.update(search_url_model.id, url_update_payload)

        logger.info(f"Completed scraping URL '{base_url}': {results['jobs_found']} jobs found. (ID: {search_url_model.id})")
        return results

    async def start_search_scrape(self, command: dtos.StartSearchScrapeCommand) -> dtos.ScrapeRunResultDTO:
        """
        Initiates the scraping process for search result URLs.
        Prevents duplicate concurrent runs.
        """
        # Concurrency control
        active_runs_count = await self.run_repo.count_active_runs("search")
        if active_runs_count > 0: # Simply check if any active run exists
            raise ScrapeAlreadyInProgressError(
                run_id="multiple active runs",
                run_type="search",
                message="A search scraping task is already running. Please wait for it to complete."
            )

        urls_to_scrape_models: List[url.SearchURLModel]
        if command.url_ids:
            urls_to_scrape_models = []
            for url_id in command.url_ids:
                url_model = await self.url_repo.get_by_id(url_id)
                if url_model and url_model.enabled:
                    urls_to_scrape_models.append(url_model)
                else:
                    logger.warning(f"URL ID '{url_id}' not found or not enabled. Skipping.")
            if not urls_to_scrape_models:
                raise DomainError("No valid or enabled URLs to scrape from the provided IDs.")
        else:
            urls_to_scrape_models = await self.url_repo.list_for_scraping(
                min_scrape_interval_minutes=settings.CACHE_EXPIRY_MINUTES # Use cache expiry as min interval
            )

        if not urls_to_scrape_models:
            raise DomainError("No enabled URLs configured or ready for scraping.")

        current_url_ids = [url_model.id for url_model in urls_to_scrape_models]

        new_scrape_run = scrape_run.ScrapeRunModel(
            run_type="search",
            search_urls=current_url_ids,
            status="running",
            triggered_by=command.triggered_by,
            jobs_found=0, # Will be updated later
        )
        run_id = await self.run_repo.add(new_scrape_run)
        new_scrape_run.run_id = run_id # Ensure run_id is set if repo returned it

        async def _execute_search_scrape_task():
            await self._execute_search_scrape(urls_to_scrape_models, new_scrape_run, self.sse_manager.send_scraping_progress)

        asyncio.create_task(_execute_search_scrape_task()) # Run in background

        logger.info(f"Search scraping initiated for {len(current_url_ids)} URLs. Run ID: {run_id}")
        return dtos.ScrapeRunResultDTO(
            run_id=run_id,
            status="running",
            message=f"Search scraping started for {len(current_url_ids)} URLs."
        )

    async def _execute_search_scrape(
        self,
        url_models: List[url.SearchURLModel],
        scrape_run_model: scrape_run.ScrapeRunModel,
        progress_callback: Optional[callable] = None,
    ):
        """Internal task to execute scraping for multiple URLs concurrently."""
        start_time = datetime.now(UTC)
        total_jobs_found = 0
        total_jobs_new = 0
        total_jobs_updated = 0
        total_urls_failed = 0
        results_by_url: Dict[str, Dict[str, Any]] = {}
        
        semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_REQUESTS)

        async def scrape_single_url_task_with_semaphore(url_model: url.SearchURLModel):
            async with semaphore:
                # Use BaseException to catch CancelledError for proper shutdown
                try:
                    result_for_url = await self._scrape_single_url(url_model, scrape_run_model, progress_callback)
                    return url_model.id, result_for_url
                except BaseException as e: # Catch BaseException to log cancellation
                    error_msg = f"Task for URL '{url_model.id}' ({url_model.url}) was terminated: {type(e).__name__} - {e}"
                    logger.critical(error_msg, exc_info=True)
                    return url_model.id, {
                        "url_id": url_model.id, "url": str(url_model.url),
                        "pages_scraped": 0, "jobs_found": 0, "jobs_new": 0, "jobs_updated": 0,
                        "errors": [scrape_run.ScrapeErrorLog(message=error_msg, item_id=url_model.id, timestamp=datetime.now(UTC))]
                    }
        
        tasks = [scrape_single_url_task_with_semaphore(url_model) for url_model in url_models]
        all_url_results = await asyncio.gather(*tasks, return_exceptions=False) # return_exceptions=False to raise BaseException

        for url_id, result in all_url_results:
            total_jobs_found += result["jobs_found"]
            total_jobs_new += result["jobs_new"]
            total_jobs_updated += result["jobs_updated"]
            if result["errors"]:
                total_urls_failed += 1
                # Append individual error logs to the main run errors
                scrape_run_model.errors.extend(result["errors"])
            results_by_url[url_id] = result
        
        # Final update of the scrape run model
        duration = (datetime.now(UTC) - start_time).total_seconds()
        scrape_run_model.status = "completed" if total_urls_failed == 0 else "completed_with_errors"
        scrape_run_model.jobs_found = total_jobs_found
        scrape_run_model.jobs_new = total_jobs_new
        scrape_run_model.jobs_updated = total_jobs_updated
        scrape_run_model.jobs_failed = total_urls_failed
        scrape_run_model.completed_at = datetime.now(UTC)
        scrape_run_model.duration_seconds = duration
        scrape_run_model.progress_percentage = 100.0
        scrape_run_model.results_by_url = results_by_url

        try:
            await self.run_repo.update(scrape_run_model.run_id, scrape_run_model.model_dump(by_alias=True))
        except RepositoryError as e:
            logger.critical(f"CRITICAL: Failed to update final scrape run record {scrape_run_model.run_id}: {e}", exc_info=True)

        if progress_callback:
            await progress_callback({
                "run_id": scrape_run_model.run_id,
                "status": scrape_run_model.status,
                "progress_percentage": 100,
                "results": {
                    "jobs_found": total_jobs_found,
                    "jobs_new": total_jobs_new,
                    "jobs_updated": total_jobs_updated,
                    "jobs_failed": total_urls_failed
                }
            })
        
        logger.info(f"Search scraping batch completed. Total URLs: {len(url_models)}, "
                   f"Total Jobs Found: {total_jobs_found}, "
                   f"New Jobs: {total_jobs_new}, Updated Jobs: {total_jobs_updated}, "
                   f"Failed URLs: {total_urls_failed}. "
                   f"Duration: {duration:.1f}s. Run ID: {scrape_run_model.run_id}")

    async def _process_single_job_detail(
        self,
        job_uid: str,
        job_url: Optional[str],
        scrape_run_id: str, # For detail batches, this is the run_id of the batch
    ) -> dtos.SingleScrapeResultDTO:
        """
        Scrapes, extracts, and enriches a single job detail page.
        """
        # Initialize with default failure status
        result_dto = dtos.SingleScrapeResultDTO(
            job_uid=job_uid,
            status="failed",
            final_status=job.JobStatus.DETAIL_FAILED.value,
            stream_run_id=scrape_run_id, # Use batch run_id for batch tasks
        )
        
        try:
            current_job_doc = await self.job_repo.get_by_uid(job_uid)
            if not current_job_doc:
                raise EntityNotFoundError(entity_name="Job", identifier=job_uid)
            
            effective_job_url = job_url or str(current_job_doc.url)
            if not effective_job_url:
                ciphertext = current_job_doc.ciphertext
                if ciphertext:
                    effective_job_url = f"{settings.UPWORK_BASE_URL}/jobs/~{ciphertext}"
                else:
                    raise DomainError(f"Job URL or ciphertext not found for job {job_uid}. Cannot scrape.")

            logger.info(f"Starting detail scrape for job {job_uid} at {effective_job_url}")

            # Update job status to indicate scraping in progress
            current_retries = current_job_doc.pipeline.optimization_retries
            await self.job_repo.update(
                uid=job_uid,
                updates={
                    "status": job.JobStatus.SCRAPING_DETAIL.value,
                    "pipeline.last_optimization_attempt": datetime.now(UTC),
                    "pipeline.optimization_retries": current_retries + 1,
                    "updated_at": datetime.now(UTC),
                }
            )

            scrape_response = await self.scrapfly_adapter.fetch(
                url=effective_job_url,
                country=settings.SCRAPFLY_COUNTRY,
                render_js=True,
                asp=True,
                rendering_wait_ms=settings.SCRAPFLY_RENDERING_WAIT,
                tags=["detail_page", job_uid],
                correlation_id=scrape_run_id,
            )
            
            # Check for specific HTTP status codes if present in metadata from Scrapfly
            status_code_from_metadata = scrape_response.get("metadata", {}).get("status_code")
            if status_code_from_metadata == 403:
                result_dto.final_status = job.JobStatus.PRIVATE_JOB.value
                raise ScrapingError(f"Job {job_uid} is private (403 Forbidden).")
            elif status_code_from_metadata == 404:
                result_dto.final_status = job.JobStatus.DELETED.value
                raise ScrapingError(f"Job {job_uid} not found (404 Not Found) - likely deleted or invalid.")
            
            html_content = scrape_response.get("html", "")
            if not html_content:
                raise ScrapingError("Scrapfly returned empty HTML content for detail page.")

            extracted_data_dict = await self.extractor_adapter.extract_job_detail(html_content)

            # Store extracted data in DB using repository
            enrich_result = await self._store_enriched_job_data(
                job_uid=job_uid,
                extracted_data=extracted_data_dict,
                raw_html=html_content,
                session=None # This single job scrape might not be in a batch transaction
            )

            if not enrich_result["success"]:
                raise ScrapingError(f"Failed to enrich job {job_uid} in database: {enrich_result.get('error')}")

            await self.job_repo.update(
                uid=job_uid,
                updates={
                    "status": job.JobStatus.ENRICHED.value,
                    "pipeline.is_enriched": True,
                    "pipeline.detail_scraped_at": datetime.now(UTC),
                    "pipeline.optimization_error": None,
                    "updated_at": datetime.now(UTC),
                }
            )
            
            logger.info(f"Successfully enriched job {job_uid}")
            result_dto.status = "success"
            result_dto.final_status = job.JobStatus.ENRICHED.value
            return result_dto

        except EntityNotFoundError:
            await self._update_job_status_on_failure(job_uid, job.JobStatus.DETAIL_FAILED, f"Job not found: {job_uid}")
            raise
        except (ScrapingError, UpworkExtractionError, UpworkExtractionValidationError) as e:
            error_message = str(e)
            await self._update_job_status_on_failure(job_uid, result_dto.final_status, error_message)
            result_dto.error = error_message
            return result_dto
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            logger.exception(f"An unexpected error occurred during detail scraping for job {job_uid}:")
            await self._update_job_status_on_failure(job_uid, job.JobStatus.DETAIL_FAILED, error_message)
            result_dto.error = error_message
            return result_dto

    async def _store_enriched_job_data(
        self,
        job_uid: str,
        extracted_data: Dict[str, Any], # Normalized dict from UpworkExtractor
        raw_html: str,
        session: Optional[Any] = None # For transactional context
    ) -> Dict[str, Any]:
        """
        Stores client and skill data, then updates the job record with enriched details.
        All operations in this method will run transactionally if a session is provided.
        """
        try:
            # 1. Process Client (upsert)
            client_id_str: Optional[str] = None
            client_info_data = extracted_data.get("client")
            if client_info_data:
                client_model = client.ClientModel(
                    client_key=self._generate_client_key_from_client_info(client_info_data),
                    **client_info_data # Assume client_info_data maps directly
                )
                client_id_str = await self.client_repo.upsert(client_model, job_uid, session=session)
                if not client_id_str:
                    logger.warning(f"Could not link job {job_uid} to client. Client upsert failed or returned no ID.")
            
            # 2. Process Skills (upsert from Extractor's Skill models)
            detail_skill_obj_ids = []
            skills_list = extracted_data.get("skills_list", [])
            if skills_list:
                for skill_data in skills_list:
                    # Convert to our domain SkillInfo model for upsert
                    skill_info_item = job.SkillInfo(
                        uid=skill_data.get("uid", hashlib.sha256(skill_data.get("name", "").lower().encode("utf-8")).hexdigest()),
                        name=skill_data.get("name"),
                        category=skill_data.get("category"),
                    )
                    obj_id = await self.skill_repo.upsert(skill_info_item, increment_job_count=False, session=session)
                    if obj_id:
                        detail_skill_obj_ids.append(obj_id)

            # 3. Prepare Job Update Payload
            # This extracted_data is already flattened and normalized by the extractor
            job_update_payload_dict = {
                "client_id": client_id_str,
                "content": {
                    "description": extracted_data.get("job_description"), # Extractor provides full description
                    "description_plain": normalize_whitespace(BeautifulSoup(extracted_data.get("job_description", ""), 'lxml').get_text(separator=' ', strip=True)),
                    "skill_ids": detail_skill_obj_ids,
                    "skills": [job.SkillInfo(**s) for s in skills_list if s] # Re-map to our SkillInfo
                },
                "terms": {
                    "budget": {
                        "available": extracted_data.get("budget_amount") is not None or (extracted_data.get("hourly_min") is not None or extracted_data.get("hourly_max") is not None),
                        "type": extracted_data.get("budget_type"),
                        "min": extracted_data.get("hourly_min") if extracted_data.get("hourly_min") is not None else extracted_data.get("budget_amount"),
                        "max": extracted_data.get("hourly_max") if extracted_data.get("hourly_max") is not None else extracted_data.get("budget_amount"),
                        "currency": extracted_data.get("budget_currency") or "USD",
                    },
                    "duration": {
                        "label": extracted_data.get("duration_label"),
                        "min_weeks": extracted_data.get("duration_weeks"),
                        "max_weeks": extracted_data.get("duration_weeks"),
                    },
                    "contractor_tier": extracted_data.get("experience_level"),
                    "engagement": extracted_data.get("workload"),
                    "project_type": extracted_data.get("project_type"),
                },
                "activity": {
                    "last_buyer_activity": parse_date_flexible(extracted_data.get("last_buyer_activity"))[0],
                    "activity_text": extracted_data.get("last_buyer_activity_raw"),
                    "total_applicants": extracted_data.get("proposals_max"),
                    "proposals_min": extracted_data.get("proposals_min"),
                    "proposals_max": extracted_data.get("proposals_max"),
                    "total_hired": extracted_data.get("total_hired_count"),
                    "total_invited_to_interview": extracted_data.get("interviewing_count"),
                    "unanswered_invites": extracted_data.get("unanswered_invites_count"),
                    "invitations_sent": extracted_data.get("invites_sent_count"),
                    # hours_since_last_buyer_activity will need separate calculation if not in raw data
                },
                "client_qualifications": {
                    "min_english_skill_level": extracted_data.get("qualifications", {}).get("preferred_english_skill"),
                    "min_hours_week": extracted_data.get("qualifications", {}).get("min_hours_week"),
                    "is_rising_talent_ok": extracted_data.get("qualifications", {}).get("rising_talent_only"),
                    "requires_portfolio": extracted_data.get("qualifications", {}).get("should_have_portfolio"),
                    "is_local_market_only": extracted_data.get("qualifications", {}).get("local_market"),
                    "location_check_required": extracted_data.get("qualifications", {}).get("location_check_required"),
                    "allowed_countries": extracted_data.get("qualifications", {}).get("allowed_countries"),
                    "languages_required": extracted_data.get("qualifications", {}).get("languages_required"),
                },
                "similar_job_ciphertexts": [
                    sim_job.get("ciphertext") for sim_job in extracted_data.get("similar_jobs_list", []) if sim_job.get("ciphertext")
                ],
                "category_info": {
                    "primary": extracted_data.get("category_group"),
                    "secondary": extracted_data.get("category_name"),
                    "occupation": extracted_data.get("skill_ontology", {}).get("occupation_name"),
                },
                "published_on": parse_date_flexible(extracted_data.get("posted_date"))[0],
                "created_on": parse_date_flexible(extracted_data.get("created_date"))[0],
                "renewed_on": parse_date_flexible(extracted_data.get("renewed_on"))[0] if extracted_data.get("was_renewed") else None,
                "was_renewed": extracted_data.get("was_renewed"),
                "positions_to_hire": extracted_data.get("number_of_positions"),

                "pipeline.source": extracted_data.get("data_source"),
                "pipeline.is_enriched": True,
                "pipeline.detail_scraped_at": datetime.now(UTC),
                "pipeline.optimization_retries": 0,
                "pipeline.optimization_error": None,
                
                "source_data.detail_extracted": extracted_data, # Store the full normalized dict
                "source_data.detail_html_ref": self._save_raw_html_to_file(job_uid, raw_html), # Save HTML to file and get ref
                
                "updated_at": datetime.now(UTC),
                "status": job.JobStatus.ENRICHED.value
            }

            if session: # If in a transaction, update with session
                update_successful = await self.job_repo.update(job_uid, job_update_payload_dict, session=session)
            else: # Otherwise, directly update
                update_successful = await self.job_repo.update(job_uid, job_update_payload_dict)

            if not update_successful:
                raise RepositoryError(f"Job {job_uid} not found for enrichment or no changes were made.")

            return {"success": True, "job_uid": job_uid}

        except (RepositoryError, DomainError) as e:
            logger.error(f"Storage error during enrichment of job {job_uid}: {e}", exc_info=True)
            return {"success": False, "job_uid": job_uid, "error": str(e)}
        except Exception as e:
            logger.exception(f"An unexpected error occurred during _store_enriched_job_data for job {job_uid}:")
            return {"success": False, "job_uid": job_uid, "error": f"An unexpected error occurred: {str(e)}"}

    def _save_raw_html_to_file(self, job_uid: str, html_content: str) -> str:
        """
        Saves raw HTML content to a file and returns its path.
        In a real production system, this would upload to S3 or GridFS.
        """
        html_dir = settings.CACHE_DIR / "raw_html"
        html_dir.mkdir(parents=True, exist_ok=True)
        file_path = html_dir / f"{job_uid}.html"
        try:
            # Using synchronous file write for simplicity, can be aiofiles
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            logger.debug(f"Saved raw HTML for {job_uid} to {file_path}")
            return str(file_path)
        except Exception as e:
            logger.error(f"Failed to save raw HTML for {job_uid} to file: {e}")
            return f"Error saving HTML: {e}" # Return error message as ref

    async def start_detail_scrape_batch(self, command: dtos.StartDetailScrapeCommand) -> dtos.ScrapeRunResultDTO:
        """
        Initiates the scraping process for individual job detail pages in a batch.
        Prevents duplicate concurrent runs.
        """
        active_runs_count = await self.run_repo.count_active_runs("detail")
        if active_runs_count > 0:
            raise ScrapeAlreadyInProgressError(
                run_id="multiple active runs",
                run_type="detail",
                message="A detail scraping task is already running. Please wait for it to complete."
            )
        
        job_uids_to_scrape: List[str]
        if command.job_uids:
            # Validate UIDs if provided
            jobs_found = []
            for uid in command.job_uids:
                job_model = await self.job_repo.get_by_uid(uid)
                if job_model: # Only add if job exists
                    jobs_found.append(uid)
                else:
                    logger.warning(f"Job UID '{uid}' not found for detail scraping. Skipping.")
            if not jobs_found:
                raise DomainError("No valid jobs found from the provided UIDs for detail scraping.")
            job_uids_to_scrape = jobs_found
        else:
            jobs_needing_detail_models = await self.job_repo.find_jobs_needing_detail(
                limit=command.limit, max_retries=settings.MAX_RETRIES
            )
            job_uids_to_scrape = [job_model.uid for job_model in jobs_needing_detail_models]
            
        if not job_uids_to_scrape:
            raise DomainError("No jobs found needing detail scraping or retry.")

        new_scrape_run = scrape_run.ScrapeRunModel(
            run_type="detail",
            job_uids=job_uids_to_scrape,
            status="running",
            triggered_by=command.triggered_by,
            jobs_found=len(job_uids_to_scrape)
        )
        run_id = await self.run_repo.add(new_scrape_run)
        new_scrape_run.run_id = run_id

        async def _execute_detail_scrape_batch_task():
            await self._execute_detail_scrape_batch(job_uids_to_scrape, new_scrape_run, self.sse_manager.send_scraping_progress)
        
        asyncio.create_task(_execute_detail_scrape_batch_task())

        logger.info(f"Detail scraping initiated for {len(job_uids_to_scrape)} jobs. Run ID: {run_id}")
        return dtos.ScrapeRunResultDTO(
            run_id=run_id,
            status="running",
            message=f"Detail scraping started for {len(job_uids_to_scrape)} jobs."
        )

    async def _execute_detail_scrape_batch(
        self,
        job_uids: List[str],
        scrape_run_model: scrape_run.ScrapeRunModel,
        progress_callback: Optional[callable] = None,
    ):
        """Internal task to execute detail scraping for multiple jobs concurrently."""
        start_time = datetime.now(UTC)
        successful_count = 0
        failed_count = 0
        
        semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_REQUESTS)
        
        async def process_single_job_with_semaphore(uid: str):
            async with semaphore:
                # This ensures each job's scraping and DB updates for its result are atomic
                from src.upwork_scraper.infrastructure.database.connection import DatabaseConnectionManager
                db_manager = DatabaseConnectionManager()
                
                single_job_result_dto: Optional[dtos.SingleScrapeResultDTO] = None

                async def _transaction_for_single_job(session: Any):
                    nonlocal single_job_result_dto
                    # Pass the session explicitly to _process_single_job_detail
                    single_job_result_dto = await self._process_single_job_detail_transactional(
                        job_uid=uid,
                        job_url=None, # Will be fetched from DB
                        scrape_run_id=scrape_run_model.run_id,
                        session=session # Pass session to inner calls
                    )
                    if single_job_result_dto.status == "failed":
                        # If the detail scrape failed (and DB status update failed too),
                        # then we need to log it here but allow the transaction to commit if other parts worked.
                        # However, for a single job failure, it's simpler to just raise and roll back the whole job's processing.
                        # The _process_single_job_detail_transactional would only raise on *transactional* error,
                        # not on scrape/extraction failures that it handled internally.
                        pass # The internal process_single_job_detail_transactional handles its own DB updates for failure

                try:
                    await db_manager.run_in_transaction(_transaction_for_single_job)
                    # If transaction commits, use the result
                    if single_job_result_dto and single_job_result_dto.status == "success":
                        return uid, single_job_result_dto
                    else:
                         # If transaction committed but result was still failed, something went wrong in status update logic
                         error_msg = single_job_result_dto.error if single_job_result_dto else "Unknown transactional failure"
                         raise ScrapingError(f"Job {uid} transactional processing failed: {error_msg}")
                except (RepositoryError, DomainError, Exception) as e:
                    # Catch transactional errors or other unexpected errors during the single job process
                    logger.error(f"Job {uid} processing failed within transaction for batch {scrape_run_model.run_id}: {e}", exc_info=True)
                    return uid, dtos.SingleScrapeResultDTO(
                        job_uid=uid,
                        status="failed",
                        final_status=job.JobStatus.DETAIL_FAILED.value,
                        error=str(e),
                        stream_run_id=scrape_run_model.run_id,
                    )
        
        all_job_results = await asyncio.gather(*[process_single_job_with_semaphore(uid) for uid in job_uids], return_exceptions=False)

        for uid, result_dto in all_job_results:
            if result_dto.status == "success":
                successful_count += 1
            else:
                failed_count += 1
                if result_dto.error:
                    scrape_run_model.errors.append(
                        scrape_run.ScrapeErrorLog(message=result_dto.error, item_id=uid, timestamp=datetime.now(UTC))
                    )
        
        # Final update of the scrape run model
        duration = (datetime.now(UTC) - start_time).total_seconds()
        scrape_run_model.status = "completed" if failed_count == 0 else "completed_with_errors"
        scrape_run_model.jobs_new = successful_count # For detail scrapes, 'new' refers to successfully enriched
        scrape_run_model.jobs_failed = failed_count
        scrape_run_model.completed_at = datetime.now(UTC)
        scrape_run_model.duration_seconds = duration
        scrape_run_model.progress_percentage = 100.0

        try:
            await self.run_repo.update(scrape_run_model.run_id, scrape_run_model.model_dump(by_alias=True))
        except RepositoryError as e:
            logger.critical(f"CRITICAL: Failed to update final scrape run record {scrape_run_model.run_id}: {e}", exc_info=True)

        if progress_callback:
            await progress_callback({
                "run_id": scrape_run_model.run_id,
                "status": scrape_run_model.status,
                "progress_percentage": 100,
                "jobs_found": len(job_uids),
                "jobs_new": successful_count,
                "jobs_failed": failed_count,
            })
        
        logger.info(f"Detail scraping batch completed. Total: {len(job_uids)}, "
                   f"Successful: {successful_count}, Failed: {failed_count}. "
                   f"Duration: {duration:.1f}s. Run ID: {scrape_run_model.run_id}")

    async def _process_single_job_detail_transactional(
        self,
        job_uid: str,
        job_url: Optional[str],
        scrape_run_id: str,
        session: Any # Must receive a session for transactional context
    ) -> dtos.SingleScrapeResultDTO:
        """
        Scrapes a single job detail page, ensuring all DB updates for *this job* are transactional.
        This is called from within a larger transaction for batch processing.
        """
        # Initialize with default failure status
        result_dto = dtos.SingleScrapeResultDTO(
            job_uid=job_uid,
            status="failed",
            final_status=job.JobStatus.DETAIL_FAILED.value,
            stream_run_id=scrape_run_id,
        )
        
        try:
            current_job_doc = await self.job_repo.get_by_uid(job_uid)
            if not current_job_doc:
                raise EntityNotFoundError(entity_name="Job", identifier=job_uid)
            
            effective_job_url = job_url or str(current_job_doc.url)
            if not effective_job_url:
                ciphertext = current_job_doc.ciphertext
                if ciphertext:
                    effective_job_url = f"{settings.UPWORK_BASE_URL}/jobs/~{ciphertext}"
                else:
                    raise DomainError(f"Job URL or ciphertext not found for job {job_uid}. Cannot scrape.")

            logger.info(f"Starting detail scrape for job {job_uid} at {effective_job_url}")

            # Update job status to indicate scraping in progress
            current_retries = current_job_doc.pipeline.optimization_retries
            await self.job_repo.update(
                uid=job_uid,
                updates={
                    "status": job.JobStatus.SCRAPING_DETAIL.value,
                    "pipeline.last_optimization_attempt": datetime.now(UTC),
                    "pipeline.optimization_retries": current_retries + 1,
                    "updated_at": datetime.now(UTC),
                },
                session=session # Pass session
            )

            scrape_response = await self.scrapfly_adapter.fetch(
                url=effective_job_url,
                country=settings.SCRAPFLY_COUNTRY,
                render_js=True,
                asp=True,
                rendering_wait_ms=settings.SCRAPFLY_RENDERING_WAIT,
                tags=["detail_page", job_uid],
                correlation_id=scrape_run_id,
            )
            
            status_code_from_metadata = scrape_response.get("metadata", {}).get("status_code")
            if status_code_from_metadata == 403:
                result_dto.final_status = job.JobStatus.PRIVATE_JOB.value
                raise ScrapingError(f"Job {job_uid} is private (403 Forbidden).")
            elif status_code_from_metadata == 404:
                result_dto.final_status = job.JobStatus.DELETED.value
                raise ScrapingError(f"Job {job_uid} not found (404 Not Found) - likely deleted or invalid.")
            
            html_content = scrape_response.get("html", "")
            if not html_content:
                raise ScrapingError("Scrapfly returned empty HTML content for detail page.")

            extracted_data_dict = await self.extractor_adapter.extract_job_detail(html_content)

            # Store extracted data in DB using repository
            enrich_result = await self._store_enriched_job_data(
                job_uid=job_uid,
                extracted_data=extracted_data_dict,
                raw_html=html_content,
                session=session # Pass session
            )

            if not enrich_result["success"]:
                raise ScrapingError(f"Failed to enrich job {job_uid} in database: {enrich_result.get('error')}")

            await self.job_repo.update(
                uid=job_uid,
                updates={
                    "status": job.JobStatus.ENRICHED.value,
                    "pipeline.is_enriched": True,
                    "pipeline.detail_scraped_at": datetime.now(UTC),
                    "pipeline.optimization_error": None,
                    "updated_at": datetime.now(UTC),
                },
                session=session # Pass session
            )
            
            logger.info(f"Successfully enriched job {job_uid}")
            result_dto.status = "success"
            result_dto.final_status = job.JobStatus.ENRICHED.value
            return result_dto

        except EntityNotFoundError:
            await self._update_job_status_on_failure(job_uid, job.JobStatus.DETAIL_FAILED, f"Job not found: {job_uid}")
            raise # Re-raise to trigger transaction rollback if this is an unrecoverable error
        except (ScrapingError, UpworkExtractionError, UpworkExtractionValidationError) as e:
            error_message = str(e)
            await self._update_job_status_on_failure(job_uid, result_dto.final_status, error_message)
            result_dto.error = error_message
            # Do NOT re-raise. The single job update for its failure state committed.
            # The parent batch transaction should continue.
            return result_dto
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            logger.exception(f"An unexpected error occurred during detail scraping for job {job_uid}:")
            await self._update_job_status_on_failure(job_uid, job.JobStatus.DETAIL_FAILED, error_message)
            result_dto.error = error_message
            raise # Re-raise to trigger transaction rollback for unexpected errors

class URLManagementService:
    """
    Manages CRUD operations and statistics for search URLs.
    """
    def __init__(self, url_repo: AbstractUrlRepository):
        self.url_repo = url_repo

    async def create_url(self, command: dtos.CreateURLCommand) -> url.SearchURLModel:
        new_url = url.SearchURLModel(**command.model_dump())
        await self.url_repo.add(new_url)
        return new_url

    async def get_url(self, url_id: str) -> url.SearchURLModel:
        found_url = await self.url_repo.get_by_id(url_id)
        if not found_url:
            raise EntityNotFoundError("SearchURL", url_id)
        return found_url

    async def list_urls(self, enabled_only: bool = False, category: Optional[str] = None) -> List[url.SearchURLModel]:
        return await self.url_repo.list_all(enabled_only=enabled_only, category=category)

    async def update_url(self, url_id: str, command: dtos.UpdateURLCommand) -> url.SearchURLModel:
        updates = command.model_dump(exclude_unset=True)
        if not updates:
            raise DomainError("No update fields provided for URL.")
        
        updated_url = await self.url_repo.update(url_id, updates)
        if not updated_url:
            raise EntityNotFoundError("SearchURL", url_id)
        return updated_url

    async def toggle_url_status(self, url_id: str) -> url.SearchURLModel:
        existing_url = await self.url_repo.get_by_id(url_id)
        if not existing_url:
            raise EntityNotFoundError("SearchURL", url_id)
        
        new_status = not existing_url.enabled
        updated_url = await self.url_repo.update(url_id, {"enabled": new_status, "updated_at": datetime.now(UTC)})
        if not updated_url:
            raise RepositoryError(f"Failed to toggle URL {url_id} status.") # Should not happen if found
        return updated_url

    async def delete_url(self, url_id: str) -> None:
        deleted = await self.url_repo.delete(url_id)
        if not deleted:
            raise EntityNotFoundError("SearchURL", url_id)

    async def get_url_statistics(self) -> Dict[str, Any]:
        return await self.url_repo.get_statistics()

class JobQueryService:
    """
    Provides query operations for job data.
    """
    def __init__(self, job_repo: AbstractJobRepository):
        self.job_repo = job_repo

    async def get_jobs_paginated(self, query: dtos.GetJobsQuery) -> dtos.PaginatedJobsResponseDTO:
        filters = {}
        if query.status:
            filters["status"] = query.status
        if query.enriched is not None:
            filters["pipeline.is_enriched"] = query.enriched
        
        sort_direction = -1 if query.sort_order == "desc" else 1
        skip = (query.page - 1) * query.page_size

        jobs, total = await self.job_repo.list_paginated(
            filters=filters,
            skip=skip,
            limit=query.page_size,
            sort_by=query.sort_by,
            sort_order=sort_direction
        )
        total_pages = (total + query.page_size - 1) // query.page_size

        return dtos.PaginatedJobsResponseDTO(
            jobs=[job_model.model_dump(by_alias=True) for job_model in jobs],
            total=total,
            page=query.page,
            page_size=query.page_size,
            total_pages=total_pages
        )

    async def search_jobs_paginated(self, query: dtos.SearchJobsQuery) -> dtos.PaginatedJobsResponseDTO:
        filters = {
            "$or": [
                {"title": {"$regex": query.q, "$options": "i"}},
                {"content.description_plain": {"$regex": query.q, "$options": "i"}}
            ]
        }
        skip = (query.page - 1) * query.page_size

        jobs, total = await self.job_repo.list_paginated(
            filters=filters,
            skip=skip,
            limit=query.page_size,
            sort_by="created_at", # Default sort for search
            sort_order=-1
        )
        total_pages = (total + query.page_size - 1) // query.page_size

        return dtos.PaginatedJobsResponseDTO(
            jobs=[job_model.model_dump(by_alias=True) for job_model in jobs],
            total=total,
            page=query.page,
            page_size=query.page_size,
            total_pages=total_pages
        )

    async def get_job_by_uid(self, job_uid: str) -> job.JobModel:
        found_job = await self.job_repo.get_by_uid(job_uid)
        if not found_job:
            raise EntityNotFoundError("Job", job_uid)
        return found_job

    async def get_recent_jobs(self, limit: int) -> List[job.JobModel]:
        jobs, _ = await self.job_repo.list_paginated(
            filters={},
            skip=0,
            limit=limit,
            sort_by="pipeline.discovered_at",
            sort_order=-1
        )
        return jobs

    async def get_jobs_pending_enrichment(self, limit: int) -> List[job.JobModel]:
        return await self.job_repo.find_jobs_needing_detail(limit=limit, max_retries=settings.MAX_RETRIES)

    async def get_job_statistics(self) -> Dict[str, Any]:
        return await self.job_repo.get_statistics()

class ScrapeRunQueryService:
    """
    Provides query operations for scrape run data.
    """
    def __init__(self, run_repo: AbstractScrapeRunRepository):
        self.run_repo = run_repo

    async def get_scrape_run_by_id(self, run_id: str) -> scrape_run.ScrapeRunModel:
        found_run = await self.run_repo.get_by_run_id(run_id)
        if not found_run:
            raise EntityNotFoundError("ScrapeRun", run_id)
        return found_run

    async def list_scrape_runs(self, query: dtos.GetScrapeRunsQuery) -> List[scrape_run.ScrapeRunModel]:
        return await self.run_repo.list_recent(run_type=query.run_type, status=query.status, limit=query.limit)
File: src/upwork_scraper/domain/models/init.py
"""
Export all domain model classes
"""
# Alphabetically sorted exports
from .client import ClientModel, ClientStatsModel
from .job import (
    ActivityModel,
    BudgetModel,
    ContentModel,
    DurationModel,
    JobModel,
    JobStatus,
    PipelineModel,
    QualificationsModel,
    SkillInfo,
    SourceDataModel,
)
from .scrape_run import ScrapeErrorLog, ScrapeRunModel
from .skill import SkillModel, SkillStatsModel
from .url import SearchURLModel

__all__ = [
    # Client Models
    "ClientModel",
    "ClientStatsModel",
    # Job Models
    "ActivityModel",
    "BudgetModel",
    "ContentModel",
    "DurationModel",
    "JobModel",
    "JobStatus",
    "PipelineModel",
    "QualificationsModel",
    "SkillInfo",
    "SourceDataModel",
    # Scrape Run Models
    "ScrapeErrorLog",
    "ScrapeRunModel",
    # Skill Models
    "SkillModel",
    "SkillStatsModel",
    # URL Models
    "SearchURLModel",
]
File: src/upwork_scraper/domain/models/client.py
"""
Client model for Upwork client/buyer data
"""
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ClientStatsModel(BaseModel):
    """Statistics about a client's hiring history and spending"""
    total_assignments: Optional[int] = Field(None, description="Total number of contracts/assignments")
    active_assignments_count: Optional[int] = Field(None, description="Number of contracts currently active")
    hours_count: Optional[float] = Field(None, description="Total hours tracked across all contracts")
    feedback_count: Optional[int] = Field(None, description="Number of feedback entries/reviews given")
    score: Optional[float] = Field(None, ge=0.0, le=5.0, description="Client's average feedback score (0-5)")
    total_jobs_with_hires: Optional[int] = Field(None, description="Total jobs where client successfully hired")
    total_charges: Optional[Dict[str, Any]] = Field(None, description="Total amount spent, with currency")
    jobs_posted_count: Optional[int] = Field(None, description="Total jobs posted by client")
    jobs_open_count: Optional[int] = Field(None, description="Number of currently open jobs by client")
    avg_hourly_jobs_rate: Optional[float] = Field(None, description="Average hourly rate client paid")


class ClientModel(BaseModel):
    """Schema for a single Client/Buyer document stored in MongoDB"""

    id: Optional[str] = Field(None, alias="_id", description="MongoDB ObjectId (auto-generated)") # Allow _id mapping
    # Unique identifier for deduplication purposes, derived from client info
    client_key: str = Field(..., description="Unique deduplication key for the client")

    # Company and location
    company: Optional[Dict[str, Any]] = Field(None, description="Company details like name, industry, size, contract date")
    location: Optional[Dict[str, Any]] = Field(None, description="Geographical location of the client (country, city, timezone)")
    verification: Optional[Dict[str, Any]] = Field(None, description="Payment verification status and enterprise flag")

    # Aggregated statistics
    stats: ClientStatsModel = Field(default_factory=ClientStatsModel, description="Detailed client hiring statistics")
    open_jobs: List[Dict[str, Any]] = Field(default_factory=list, description="List of currently open jobs by this client (summary data)")
    job_uids: List[str] = Field(default_factory=list, description="List of UIDs of all jobs associated with this client")

    # Timestamps
    first_seen_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="When client was first encountered")
    last_activity_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Client's last observed activity")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="When client document was created")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Last update to client document")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
        arbitrary_types_allowed = True
        populate_by_name = True # Allow mapping _id to id
File: src/upwork_scraper/domain/models/job.py
"""
Job model for Upwork job data
"""
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum


class JobStatus(str, Enum):
    """Enum for job processing status"""
    DISCOVERED = "discovered" # Job found in search results
    SCRAPING_DETAIL = "scraping_detail" # Detail page currently being scraped
    ENRICHED = "enriched" # Detail page successfully scraped and data enriched
    PRIVATE_JOB = "private_job" # Job is marked as private/unavailable (e.g., 403 Forbidden) (corrected casing)
    DETAIL_FAILED = "detail_failed" # Scraping detail page failed due to network/Scrapfly issue
    EXTRACTION_FAILED = "extraction_failed" # Data extraction from detail page HTML failed
    AWAITING_INTELLIGENCE_CALC = "awaiting_intelligence_calc" # Enriched, pending further processing/ranking
    COMPLETED = "completed" # Fully processed and ready
    DELETED = "deleted" # Job was found but no longer exists (e.g., 404 Not Found)


class BudgetModel(BaseModel):
    """Job budget information"""
    available: bool = Field(False, description="Whether budget information is available")
    type: Optional[str] = Field(None, description="Budget type: fixed or hourly")
    min: Optional[float] = Field(None, description="Minimum amount or hourly rate")
    max: Optional[float] = Field(None, description="Maximum amount or hourly rate")
    currency: Optional[str] = Field("USD", description="Currency code (ISO 4217)")


class DurationModel(BaseModel):
    """Job duration information"""
    label: Optional[str] = Field(None, description="Human-readable duration label (e.g., '1 to 3 months')")
    min_weeks: Optional[int] = Field(None, description="Minimum duration in weeks")
    max_weeks: Optional[int] = Field(None, description="Maximum duration in weeks")


class SkillInfo(BaseModel):
    """Individual skill information with UID and name as seen in Upwork data"""
    uid: str = Field(..., description="Skill UID from Upwork (or generated hash)")
    name: str = Field(..., description="Skill name")
    category: Optional[str] = Field(None, description="Skill category (e.g., 'mandatory', 'nice_to_have', 'attribute')")


class TermsModel(BaseModel):
    """Job terms and requirements"""
    budget: BudgetModel = Field(default_factory=BudgetModel)
    duration: Optional[DurationModel] = Field(default_factory=DurationModel, description="Duration details")
    contractor_tier: Optional[str] = Field(None, description="Required experience level (e.g., 'Expert', 'Intermediate')")
    engagement: Optional[str] = Field(None, description="Engagement type (e.g., 'Full Time', 'Part Time', 'Not Sure')")
    project_type: Optional[str] = Field(None, description="Project type (e.g., 'one_time', 'ongoing', 'contract_to_hire')")


class ContentModel(BaseModel):
    """Job content and description"""
    description: Optional[str] = Field(None, description="Full job description (can contain HTML)")
    description_plain: Optional[str] = Field(None, description="Cleaned plain text description")
    skill_ids: List[str] = Field(default_factory=list, description="List of MongoDB ObjectIds linking to SkillModel documents")
    skills: List[SkillInfo] = Field(default_factory=list, description="List of raw skill info from Upwork data (for quick reference)")


class SourceDataModel(BaseModel):
    """Raw and processed source data from scraping stages"""
    search: Optional[Dict[str, Any]] = Field(None, description="Raw data from the initial search page scrape")
    detail_html_ref: Optional[str] = Field(None, description="Reference (e.g., file path or S3 URL) to the raw HTML content") # Replaced detail_raw_html
    # detail_nuxt: Optional[Dict[str, Any]] = Field(None, description="Parsed __NUXT_DATA__ JSON from detail page") # Removed to reduce bloat
    # detail_json_ld: Optional[Dict[str, Any]] = Field(None, description="Parsed Schema.org JSON-LD from detail page") # Removed to reduce bloat
    detail_extracted: Optional[Dict[str, Any]] = Field(None, description="Normalized structured data from UpworkDataExtractor")


class PipelineModel(BaseModel):
    """Pipeline processing metadata for a job"""
    source: str = Field(default="search", description="Initial data source that led to job creation")
    is_enriched: bool = Field(default=False, description="True if full job details have been scraped and enriched")
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Timestamp when job was first discovered")
    detail_scraped_at: Optional[datetime] = Field(None, description="Timestamp when full job details were successfully scraped")
    last_optimization_attempt: Optional[datetime] = Field(None, description="Last timestamp an attempt was made to scrape detail page")
    optimization_retries: int = Field(default=0, description="Number of detail scraping retries attempted for this job")
    optimization_error: Optional[str] = Field(None, description="Last error message from a detail scraping attempt")


class ActivityModel(BaseModel):
    """Job activity metrics from Upwork"""
    last_buyer_activity: Optional[datetime] = Field(None, description="Timestamp of client's last activity")
    hours_since_last_buyer_activity: Optional[float] = Field(None, description="Calculated hours since last buyer activity")
    activity_text: Optional[str] = Field(None, description="Raw text describing client activity (e.g., '10 hours ago')")
    total_applicants: Optional[int] = Field(None, description="Total number of proposals/applicants (usually max of range)")
    proposals_min: Optional[int] = Field(None, description="Minimum proposals in reported range")
    proposals_max: Optional[int] = Field(None, description="Maximum proposals in reported range")
    total_hired: Optional[int] = Field(None, description="Number of freelancers hired for this job")
    total_invited_to_interview: Optional[int] = Field(None, description="Number of freelancers invited to interview")
    unanswered_invites: Optional[int] = Field(None, description="Number of unanswered invites sent")
    invitations_sent: Optional[int] = Field(None, description="Total invitations sent by client for this job")


class QualificationsModel(BaseModel):
    """Client qualifications and specific job requirements"""
    min_job_success_score: Optional[int] = Field(None, ge=0, le=100, description="Minimum job success score required")
    min_english_skill_level: Optional[int] = Field(None, ge=0, le=5, description="Minimum English skill level (0-5)")
    min_odesk_hours: Optional[int] = Field(None, ge=0, description="Minimum Odesk/Upwork hours required")
    min_hours_week: Optional[int] = Field(None, ge=0, description="Minimum hours per week required from freelancer")
    is_rising_talent_ok: Optional[bool] = Field(None, description="Whether Rising Talent freelancers are accepted")
    requires_portfolio: Optional[bool] = Field(None, description="Whether a portfolio is required")
    is_local_market_only: Optional[bool] = Field(None, description="Whether job is restricted to local market")
    allowed_countries: Optional[List[str]] = Field(None, description="List of allowed countries for applicants")
    languages_required: Optional[List[Dict[str, Any]]] = Field(None, description="Required languages and proficiency levels")


class JobModel(BaseModel):
    """Complete schema for a single Upwork job document stored in MongoDB"""

    id: Optional[str] = Field(None, alias="_id", description="MongoDB ObjectId (auto-generated)") # Allow _id mapping
    # Core identifiers
    uid: str = Field(..., description="Unique job identifier from Upwork (e.g., ~021989059411821975576)")
    title: str = Field(..., description="Job title")
    url: Optional[HttpUrl] = Field(None, description="Direct URL to the job posting on Upwork")
    status: JobStatus = Field(default=JobStatus.DISCOVERED, description="Current processing status of the job")
    run_id: Optional[str] = Field(None, description="ID of the scraper run that first found this job")
    ciphertext: Optional[str] = Field(None, description="Encrypted job identifier used in Upwork URLs")

    # Core job content
    content: ContentModel = Field(default_factory=ContentModel)
    terms: TermsModel = Field(default_factory=TermsModel)

    # Relationships
    client_id: Optional[str] = Field(None, description="MongoDB ObjectId of the associated ClientModel document")
    similar_job_ciphertexts: List[str] = Field(default_factory=list, description="Ciphertexts of similar jobs found on Upwork")

    # Metadata
    category_info: Optional[Dict[str, Any]] = Field(None, description="Category and subcategory information")
    activity: ActivityModel = Field(default_factory=ActivityModel, description="Client activity and job proposal metrics")
    client_qualifications: QualificationsModel = Field(default_factory=QualificationsModel, description="Qualifications set by the client for applicants")
    positions_to_hire: Optional[int] = Field(None, description="Number of positions the client intends to hire")
    was_renewed: Optional[bool] = Field(None, description="Whether the job posting was renewed on Upwork")

    # Job posting timestamps
    created_on: Optional[datetime] = Field(None, description="When job was created on Upwork (Upwork's internal creation date)")
    published_on: Optional[datetime] = Field(None, description="When job was published on Upwork (Upwork's visible posted date)")
    renewed_on: Optional[datetime] = Field(None, description="When job was explicitly renewed on Upwork")

    # Pipeline tracking
    pipeline: PipelineModel = Field(default_factory=PipelineModel)

    # Source data (raw and extracted for debugging/auditing)
    source_data: SourceDataModel = Field(default_factory=SourceDataModel)

    # Timestamps (for database record management)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="When this job document was created in the database")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Last timestamp this job document was updated in the database")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
        arbitrary_types_allowed = True
        use_enum_values = True
        populate_by_name = True # Allow mapping '_id' field from MongoDB to 'id' attribute
File: src/upwork_scraper/domain/models/scrape_run.py
"""
Scrape run model for tracking scraping operations
"""
from datetime import UTC, datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ScrapeErrorLog(BaseModel):
    """Structured log for errors encountered during a scrape run."""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC), description="When the error occurred")
    message: str = Field(..., description="Error message")
    item_id: Optional[str] = Field(None, description="ID of the item that failed (e.g., URL ID or Job UID)")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class ScrapeRunModel(BaseModel):
    """Schema for tracking a scraping run/operation"""
File: src/upwork_scraper/domain/models/skill.py
"""
Skill model for Upwork skill data
"""
from datetime import UTC, datetime
from typing import Optional
from pydantic import BaseModel, Field


class SkillStatsModel(BaseModel):
    """Statistics about a skill's usage and relevance"""
    job_count: int = Field(default=0, description="Total number of jobs requiring this skill")
    search_highlight_count: int = Field(default=0, description="Times skill was highlighted in search results")
    relevance_mandatory_count: int = Field(default=0, description="Times skill was marked as mandatory")


class SkillModel(BaseModel):
    """Schema for a single Skill document stored in MongoDB"""

    id: Optional[str] = Field(None, alias="_id", description="MongoDB ObjectId (auto-generated)") # Allow _id mapping
    # Core identifiers
    uid: str = Field(..., description="Unique skill identifier (Upwork UID or generated hash)")
    name: str = Field(..., description="Canonical name of the skill (lowercase)")
    pref_label: Optional[str] = Field(None, description="Preferred display label for the skill")
    pretty_name: Optional[str] = Field(None, description="Nicely formatted name for display")
    parent_skill_uid: Optional[str] = Field(None, description="UID of the parent skill if hierarchical")

    # Source information
    free_text_value: Optional[str] = Field(None, description="Original free-text value if user-defined (for `is_free_text` skills)")
    source_type: str = Field(default="attribute", description="Source of skill (e.g., 'attribute', 'ontology', 'free_text', 'search_highlight')")
    is_free_text: bool = Field(default=False, description="True if skill was extracted as free-text by client")

    # Usage statistics
    stats: SkillStatsModel = Field(default_factory=SkillStatsModel, description="Usage statistics for the skill")

    # Timestamps
    first_seen_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="When skill was first encountered across jobs")
    last_seen_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="When skill was last seen in a job posting")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="When skill document was created in DB")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Last update to skill document in DB")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
        arbitrary_types_allowed = True
        populate_by_name = True # Allow mapping '_id' field from MongoDB to 'id' attribute
File: src/upwork_scraper/domain/models/url.py
"""
Search URL model for managing Upwork search URLs
"""
from datetime import UTC, datetime
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl
import uuid


class SearchURLModel(BaseModel):
    """Schema for a search URL document stored in MongoDB"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the URL")
    url: HttpUrl = Field(..., description="The Upwork search URL to scrape")
    name: str = Field(..., description="Human-readable name for this search URL")

    # Management fields
    enabled: bool = Field(default=True, description="Whether this URL is active for scraping")
    category: Optional[str] = Field(None, description="Category/tag to organize URLs")
    description: Optional[str] = Field(None, description="Optional description of what this search is for")

    # Scraping history
    last_scraped_at: Optional[datetime] = Field(None, description="Timestamp of last successful scrape")
    last_scrape_job_count: Optional[int] = Field(None, description="Number of jobs found in last successful scrape")
    total_scrape_count: int = Field(default=0, description="Total number of times this URL has been scraped")
    total_jobs_found: int = Field(default=0, description="Total jobs found from this URL across all scrapes")

    # Error tracking
    last_error: Optional[str] = Field(None, description="Last error message if scraping failed")
    last_error_at: Optional[datetime] = Field(None, description="Timestamp of last error")
    error_count: int = Field(default=0, description="Total number of scraping errors encountered")

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="When URL was added to the system")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Last update to URL document")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
        arbitrary_types_allowed = True
        populate_by_name = True # Allow mapping '_id' field from MongoDB to 'id' attribute
File: src/upwork_scraper/domain/init.py
"""
Domain layer for the Upwork Scraper application.
Contains core business logic: models, interfaces (ports), and domain exceptions.
"""
File: src/upwork_scraper/domain/exceptions.py
"""
Custom exception hierarchy for the backend application's domain layer.
Provides granular error handling for different failure scenarios.
"""
from typing import Any, Optional

class DomainError(Exception):
    """Base exception for all domain-specific errors."""
    pass

class RepositoryError(DomainError):
    """Raised when an error occurs during repository operations (e.g., database issues)."""
    pass

class EntityNotFoundError(DomainError):
    """Raised when a requested entity (e.g., Job, URL) is not found."""
    def __init__(self, entity_name: str, identifier: str):
        self.entity_name = entity_name
        self.identifier = identifier
        super().__init__(f"{entity_name} with identifier '{identifier}' not found.")

class DuplicateEntityError(DomainError):
    """Raised when an attempt is made to create an entity that already exists."""
    def __init__(self, entity_name: str, identifier: str, message: Optional[str] = None):
        self.entity_name = entity_name
        self.identifier = identifier
        super().__init__(message or f"{entity_name} with identifier '{identifier}' already exists.")

class DataValidationError(DomainError):
    """Raised when extracted data fails validation rules before storage/processing."""
    pass

class ScrapingError(DomainError):
    """Base exception for all scraping-related errors within the application layer."""
    pass

class ScrapflyError(ScrapingError):
    """Raised when an error occurs during interaction with the Scrapfly API."""
    def __init__(self, message: str, status_code: Optional[int] = None, error_code: Optional[str] = None, details: Optional[Any] = None, retryable: bool = False):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code
        self.details = details
        self.retryable = retryable

class ScrapflyConcurrencyLimitError(ScrapflyError):
    """Raised when Scrapfly returns a 429 Too Many Requests due to concurrency limits."""
    def __init__(self, message: str = "Scrapfly concurrency limit reached.", details: Optional[Any] = None):
        super().__init__(message, status_code=429, error_code="TOO_MANY_REQUESTS", details=details, retryable=True)

class ScrapflyRequestFailedError(ScrapflyError):
    """Raised when Scrapfly returns a 422 Request Failed."""
    def __init__(self, message: str, status_code: int = 422, error_code: Optional[str] = None, details: Optional[Any] = None, retryable: bool = False):
        super().__init__(message, status_code=status_code, error_code=error_code, details=details, retryable=retryable)

class ScrapeAlreadyInProgressError(DomainError):
    """Raised when a scrape operation is requested but an identical one is already running."""
    def __init__(self, run_id: str, run_type: str, message: Optional[str] = None):
        self.run_id = run_id
        self.run_type = run_type
        super().__init__(message or f"A '{run_type}' scrape is already in progress with run_id: {run_id}")

class UpworkExtractionError(ScrapingError):
    """Raised when data extraction from HTML content fails using the UpworkExtractor library."""
    pass

class UpworkExtractionValidationError(ScrapingError):
    """Raised when extracted data fails validation rules from UpworkExtractor library."""
    pass
File: src/upwork_scraper/domain/repositories.py
"""
Abstract Repository Interfaces (Ports) for the Domain Layer.
These define the contracts for interacting with persistence and other external systems.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Any, Dict, Tuple

from src.upwork_scraper.domain.models import job, url, scrape_run, client, skill

class AbstractJobRepository(ABC):
    """Abstract repository for JobModel."""
    @abstractmethod
    async def get_by_uid(self, uid: str) -> Optional[job.JobModel]:
        raise NotImplementedError

    @abstractmethod
    async def add(self, job_model: job.JobModel, session: Optional[Any] = None) -> str:
        raise NotImplementedError
    
    @abstractmethod
    async def update(self, uid: str, updates: Dict[str, Any], session: Optional[Any] = None) -> Optional[job.JobModel]:
        raise NotImplementedError

    @abstractmethod
    async def list_paginated(
        self,
        filters: Dict[str, Any],
        skip: int,
        limit: int,
        sort_by: str,
        sort_order: int
    ) -> Tuple[List[job.JobModel], int]:
        raise NotImplementedError
    
    @abstractmethod
    async def count(self, filters: Dict[str, Any]) -> int:
        raise NotImplementedError

    @abstractmethod
    async def get_statistics(self) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def find_jobs_needing_detail(self, limit: int, max_retries: int) -> List[job.JobModel]:
        raise NotImplementedError

class AbstractUrlRepository(ABC):
    """Abstract repository for SearchURLModel."""
    @abstractmethod
    async def get_by_id(self, url_id: str) -> Optional[url.SearchURLModel]:
        raise NotImplementedError

    @abstractmethod
    async def add(self, url_model: url.SearchURLModel, session: Optional[Any] = None) -> str:
        raise NotImplementedError

    @abstractmethod
    async def update(self, url_id: str, updates: Dict[str, Any], session: Optional[Any] = None) -> Optional[url.SearchURLModel]:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, url_id: str, session: Optional[Any] = None) -> bool:
        raise NotImplementedError
    
    @abstractmethod
    async def list_all(self, enabled_only: bool = False, category: Optional[str] = None) -> List[url.SearchURLModel]:
        raise NotImplementedError

    @abstractmethod
    async def list_for_scraping(self, min_scrape_interval_minutes: int) -> List[url.SearchURLModel]:
        raise NotImplementedError

    @abstractmethod
    async def get_statistics(self) -> Dict[str, Any]:
        raise NotImplementedError

class AbstractClientRepository(ABC):
    """Abstract repository for ClientModel."""
    @abstractmethod
    async def get_by_client_key(self, client_key: str) -> Optional[client.ClientModel]:
        raise NotImplementedError

    @abstractmethod
    async def upsert(self, client_model: client.ClientModel, job_uid: Optional[str], session: Optional[Any] = None) -> str:
        """Inserts or updates a client and returns its MongoDB ObjectId."""
        raise NotImplementedError
    
    @abstractmethod
    async def count(self) -> int:
        raise NotImplementedError

class AbstractSkillRepository(ABC):
    """Abstract repository for SkillModel."""
    @abstractmethod
    async def get_by_uid(self, uid: str) -> Optional[skill.SkillModel]:
        raise NotImplementedError
    
    @abstractmethod
    async def upsert(self, skill_info: job.SkillInfo, increment_job_count: bool = True, session: Optional[Any] = None) -> str:
        """Inserts or updates a skill and returns its MongoDB ObjectId."""
        raise NotImplementedError

    @abstractmethod
    async def count(self) -> int:
        raise NotImplementedError

class AbstractScrapeRunRepository(ABC):
    """Abstract repository for ScrapeRunModel."""
    @abstractmethod
    async def get_by_run_id(self, run_id: str) -> Optional[scrape_run.ScrapeRunModel]:
        raise NotImplementedError

    @abstractmethod
    async def add(self, run_model: scrape_run.ScrapeRunModel, session: Optional[Any] = None) -> str:
        raise NotImplementedError
    
    @abstractmethod
    async def update(self, run_id: str, updates: Dict[str, Any], session: Optional[Any] = None) -> Optional[scrape_run.ScrapeRunModel]:
        raise NotImplementedError

    @abstractmethod
    async def list_recent(self, run_type: Optional[str] = None, status: Optional[str] = None, limit: int = 20) -> List[scrape_run.ScrapeRunModel]:
        raise NotImplementedError
    
    @abstractmethod
    async def count_active_runs(self, run_type: str) -> int:
        raise NotImplementedError

class AbstractScrapingAdapter(ABC):
    """Abstract interface for a web scraping API client (e.g., Scrapfly)."""
    @abstractmethod
    async def fetch(self, url: str, render_js: bool, country: str, proxy_pool: str, asp: bool, timeout_ms: int,
                    rendering_wait_ms: Optional[int] = None, wait_for_selector: Optional[str] = None,
                    headers: Optional[Dict[str, str]] = None, tags: Optional[List[str]] = None,
                    correlation_id: Optional[str] = None, max_retries: Optional[int] = None) -> Dict[str, Any]:
        """Fetches a URL and returns content and metadata."""
        raise NotImplementedError

class AbstractUpworkExtractorAdapter(ABC):
    """Abstract interface for the Upwork data extraction library."""
    @abstractmethod
    async def extract_job_detail(self, html_content: str) -> Dict[str, Any]:
        """Extracts structured job detail data from HTML."""
        raise NotImplementedError

    @abstractmethod
    async def extract_search_job_summaries(self, html_content: str) -> List[Dict[str, Any]]:
        """Extracts job summaries from search results HTML."""
        raise NotImplementedError
    
    @abstractmethod
    async def extract_pagination_data(self, html_content: str) -> Optional[Dict[str, Any]]:
        """Extracts pagination metadata from search results HTML."""
        raise NotImplementedError
File: src/upwork_scraper/infrastructure/database/repositories/init.py
"""
Concrete implementations of domain repository interfaces using MongoDB.
"""
File: src/upwork_scraper/infrastructure/database/repositories/mongo_client_repository.py
"""
MongoDB implementation of the AbstractClientRepository.
"""
import logging
import hashlib
from datetime import datetime, UTC
from typing import Any, Dict, Optional

from pymongo import ReturnDocument, DuplicateKeyError

from src.upwork_scraper.config import settings
from src.upwork_scraper.domain.models import client as domain_client_models
from src.upwork_scraper.domain.repositories import AbstractClientRepository
from src.upwork_scraper.domain.exceptions import RepositoryError, DuplicateEntityError
from src.upwork_scraper.infrastructure.database.connection import DatabaseConnectionManager

from upwork_extractor.models.client import ClientInfo # For client key generation
from upwork_extractor.utils.text_utils import normalize_whitespace

logger = logging.getLogger(__name__)


class MongoClientRepository(AbstractClientRepository):
    """
    MongoDB implementation of the AbstractClientRepository.
    Handles persistence of client data.
    """
    def __init__(self):
        self.db_manager = DatabaseConnectionManager()
        self.collection_name = settings.COLLECTION_CLIENTS

    async def get_by_client_key(self, client_key: str) -> Optional[domain_client_models.ClientModel]:
        """Retrieves a client by its unique client_key."""
        try:
            doc = await self.db_manager.find_one(self.collection_name, {"client_key": client_key})
            if doc:
                return domain_client_models.ClientModel(**doc)
            return None
        except Exception as e:
            raise RepositoryError(f"Failed to get client by key {client_key}: {e}") from e

    async def upsert(self, client_model: domain_client_models.ClientModel, job_uid: Optional[str], session: Optional[Any] = None) -> str:
        """
        Inserts or updates a client document.
        If job_uid is provided, it's added to the client's associated jobs.
        """
        client_key = client_model.client_key
        if not client_key:
            raise RepositoryError("ClientModel must have a client_key for upsert operation.")

        # Convert Pydantic model to dictionary, handling aliases and excluding unset
        client_doc_partial = client_model.model_dump(by_alias=False, exclude_unset=True)
        # Remove _id / id from the update payload if present, as it's for lookup
        client_doc_partial.pop("id", None)
        client_doc_partial.pop("_id", None)


        # Specific logic for updating lists/sub-documents
        update_op: Dict[str, Any] = {
            "$set": {
                **client_doc_partial, # Flatten top-level fields
                "updated_at": datetime.now(UTC),
            },
            "$setOnInsert": {
                "client_key": client_key,
                "first_seen_at": datetime.now(UTC),
                "created_at": datetime.now(UTC),
            },
        }
        
        # Handle nested fields for $set
        if client_model.company:
            update_op["$set"]["company"] = client_model.company
        if client_model.location:
            update_op["$set"]["location"] = client_model.location
        if client_model.verification:
            update_op["$set"]["verification"] = client_model.verification
        if client_model.stats:
            update_op["$set"]["stats"] = client_model.stats.model_dump(by_alias=True)

        if job_uid:
            update_op.setdefault("$addToSet", {})["job_uids"] = job_uid
        
        if client_model.open_jobs:
            # $addToSet prevents duplicates. For open_jobs, we expect summary dicts.
            # Using $each for multiple items.
            update_op.setdefault("$addToSet", {})["open_jobs"] = {"$each": client_model.open_jobs}


        try:
            result_doc = await self.db_manager.get_collection(self.collection_name).find_one_and_update(
                {"client_key": client_key},
                update_op,
                upsert=True,
                return_document=ReturnDocument.AFTER,
                session=session # Pass session for transactions
            )
            return str(result_doc["_id"]) if result_doc else None
        except DuplicateKeyError as e:
            raise DuplicateEntityError("Client", client_key, message=f"Client with key {client_key} already exists: {e}") from e
        except Exception as e:
            logger.error(f"Failed to upsert client {client_key}: {e}", exc_info=True)
            raise RepositoryError(f"Failed to upsert client: {e}") from e

    async def count(self) -> int:
        """Returns the total count of client documents."""
        try:
            return await self.db_manager.count_documents(self.collection_name)
        except Exception as e:
            raise RepositoryError(f"Failed to count clients: {e}") from e

    def _generate_client_key_from_client_info(self, client_info: ClientInfo) -> Optional[str]:
        """
        Generate a consistent hash key from Extractor's ClientInfo model for deduplication.
        Uses key components that are typically stable.
        """
        components = []
        
        if client_info.company and client_info.company.name:
            components.append(normalize_whitespace(client_info.company.name).lower())
        if client_info.location and client_info.location.country:
            components.append(normalize_whitespace(client_info.location.country).lower())
        components.append("1" if client_info.payment_verified else "0") # Payment verification is a strong identifier
        
        # Add total spent and client score if available, these often identify stable clients
        if client_info.stats:
            if client_info.stats.total_spent is not None:
                components.append(f"spent_{client_info.stats.total_spent:.2f}")
            if client_info.stats.client_score is not None:
                components.append(f"score_{client_info.stats.client_score:.2f}")

        if len(components) < 2: # Require at least a company name or country + payment_verified for reasonable key
            logger.warning(f"Client key generation from sparse data. Client: {client_info.model_dump_json(exclude_none=True)}")
            try:
                # Fallback to hash of entire model if critical parts are missing, but this is less stable
                raw_str = client_info.model_dump_json(exclude_none=True, sort_keys=True)
                return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()
            except Exception:
                logger.error("Failed to generate fallback client key from full model.")
                return None

        combined = "|".join(sorted(components)) # Sort components for consistent hash
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()
File: src/upwork_scraper/infrastructure/database/repositories/mongo_job_repository.py
"""
MongoDB implementation of the AbstractJobRepository.
"""
import logging
from datetime import datetime, UTC
from typing import Any, Dict, List, Optional, Tuple

from pymongo import ReturnDocument

from src.upwork_scraper.config import settings
from src.upwork_scraper.domain.models import job as domain_job_models
from src.upwork_scraper.domain.repositories import AbstractJobRepository
from src.upwork_scraper.domain.exceptions import RepositoryError, DuplicateEntityError
from src.upwork_scraper.infrastructure.database.connection import DatabaseConnectionManager

logger = logging.getLogger(__name__)


class MongoJobRepository(AbstractJobRepository):
    """
    MongoDB implementation of the AbstractJobRepository.
    Handles persistence and retrieval of job data.
    """
    def __init__(self):
        self.db_manager = DatabaseConnectionManager()
        self.collection_name = settings.COLLECTION_JOBS

    async def get_by_uid(self, uid: str) -> Optional[domain_job_models.JobModel]:
        """Retrieves a job by its unique Upwork UID."""
        try:
            doc = await self.db_manager.find_one(self.collection_name, {"uid": uid})
            if doc:
                return domain_job_models.JobModel(**doc)
            return None
        except Exception as e:
            raise RepositoryError(f"Failed to get job by UID {uid}: {e}") from e

    async def add(self, job_model: domain_job_models.JobModel, session: Optional[Any] = None) -> str:
        """Adds a new job document to the database."""
        try:
            job_dict = job_model.model_dump(by_alias=True, exclude_none=True)
            inserted_id = await self.db_manager.insert_one(self.collection_name, job_dict, session=session)
            return inserted_id
        except DuplicateEntityError:
            raise # Re-raise if specific duplicate error is needed upstream
        except Exception as e:
            raise RepositoryError(f"Failed to add job {job_model.uid}: {e}") from e
    
    async def update(self, uid: str, updates: Dict[str, Any], session: Optional[Any] = None) -> Optional[domain_job_models.JobModel]:
        """
        Updates an existing job document by UID.
        Returns the updated job model or None if not found.
        """
        try:
            # Ensure updated_at is always set
            updates["updated_at"] = datetime.now(UTC)
            
            # MongoDB $set expects nested fields like "content.description"
            # Pydantic model_dump_json gives flat dict with dot notation in keys, which is suitable for $set
            # We need to ensure updates here directly support MongoDB dot notation for nested fields.
            # Convert job.SkillInfo and other Pydantic models in updates to dicts for MongoDB
            processed_updates = {}
            for key, value in updates.items():
                if isinstance(value, domain_job_models.ContentModel):
                    processed_updates[key] = value.model_dump(by_alias=True, exclude_none=True)
                elif isinstance(value, List) and all(isinstance(item, domain_job_models.SkillInfo) for item in value):
                    processed_updates[key] = [item.model_dump(by_alias=True, exclude_none=True) for item in value]
                elif isinstance(value, dict):
                    # Check for nested pydantic models in dict, e.g., 'terms'
                    # This requires deep inspection, or a convention that update payloads are already flattened/dict-ized
                    processed_updates[key] = value
                else:
                    processed_updates[key] = value

            result = await self.db_manager.get_collection(self.collection_name).find_one_and_update(
                {"uid": uid},
                {"$set": processed_updates},
                return_document=ReturnDocument.AFTER,
                session=session # Pass session for transactions
            )
            if result:
                return domain_job_models.JobModel(**result)
            return None
        except Exception as e:
            raise RepositoryError(f"Failed to update job {uid}: {e}") from e

    async def list_paginated(
        self,
        filters: Dict[str, Any],
        skip: int,
        limit: int,
        sort_by: str,
        sort_order: int
    ) -> Tuple[List[domain_job_models.JobModel], int]:
        """
        Retrieves a paginated list of jobs and their total count using an aggregation pipeline.
        """
        pipeline = [
            {"$match": filters},
            {
                "$facet": {
                    "metadata": [{"$count": "total"}],
                    "data": [
                        {"$sort": {sort_by: sort_order}},
                        {"$skip": skip},
                        {"$limit": limit}
                    ]
                }
            }
        ]
        
        try:
            result = await self.db_manager.aggregate(self.collection_name, pipeline)
            
            if not result or not result[0]['data']:
                return [], 0
            
            total = result[0]['metadata'][0]['total'] if result[0]['metadata'] else 0
            jobs_data = result[0]['data']
            
            return [domain_job_models.JobModel(**doc) for doc in jobs_data], total
        except Exception as e:
            raise RepositoryError(f"Failed to list paginated jobs with filters {filters}: {e}") from e
    
    async def count(self, filters: Dict[str, Any]) -> int:
        """Returns the count of jobs matching the given filters."""
        try:
            return await self.db_manager.count_documents(self.collection_name, filters)
        except Exception as e:
            raise RepositoryError(f"Failed to count jobs with filters {filters}: {e}") from e

    async def get_statistics(self) -> Dict[str, Any]:
        """Get aggregated statistics about job documents."""
        try:
            total_jobs = await self.count({})
            enriched_jobs = await self.count({"pipeline.is_enriched": True})
            discovered_today = await self.count({
                "created_at": {"$gte": datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)}
            })
            private_jobs = await self.count({"status": domain_job_models.JobStatus.PRIVATE_JOB.value})
            deleted_jobs = await self.count({"status": domain_job_models.JobStatus.DELETED.value})

            return {
                "total": total_jobs,
                "enriched": enriched_jobs,
                "discovered_today": discovered_today,
                "pending_enrichment": total_jobs - enriched_jobs - private_jobs - deleted_jobs,
                "private_jobs": private_jobs,
                "deleted_jobs": deleted_jobs,
            }
        except Exception as e:
            raise RepositoryError(f"Failed to get job statistics: {e}") from e

    async def find_jobs_needing_detail(self, limit: int, max_retries: int) -> List[domain_job_models.JobModel]:
        """
        Finds jobs that need detail enrichment and haven't exceeded the retry limit.
        """
        try:
            filters = {
                "status": {"$in": [domain_job_models.JobStatus.DISCOVERED.value, domain_job_models.JobStatus.DETAIL_FAILED.value, domain_job_models.JobStatus.EXTRACTION_FAILED.value]},
                "pipeline.is_enriched": False,
                "pipeline.optimization_retries": {"$lt": max_retries}
            }
            jobs_docs = await self.db_manager.find_many(
                self.collection_name,
                filters,
                limit=limit,
                sort=[("created_at", 1)]  # Process oldest discovered/failed first
            )
            return [domain_job_models.JobModel(**doc) for doc in jobs_docs]
        except Exception as e:
            raise RepositoryError(f"Failed to find jobs needing detail enrichment: {e}") from e
File: src/upwork_scraper/infrastructure/database/repositories/mongo_scrape_run_repository.py
"""
MongoDB implementation of the AbstractScrapeRunRepository.
"""
import logging
from typing import Any, Dict, Optional



from src.upwork_scraper.config import settings
from src.upwork_scraper.domain.models import scrape_run as domain_scrape_run_models
from src.upwork_scraper.domain.repositories import AbstractScrapeRunRepository
from src.upwork_scraper.domain.exceptions import RepositoryError, DuplicateEntityError
from src.upwork_scraper.infrastructure.database.connection import DatabaseConnectionManager

logger = logging.getLogger(__name__)


class MongoScrapeRunRepository(AbstractScrapeRunRepository):
    """
    MongoDB implementation of the AbstractScrapeRunRepository.
    Handles persistence and retrieval of scrape run data.
    """
    def __init__(self):
        self.db_manager = DatabaseConnectionManager()
        self.collection_name = settings.COLLECTION_SCRAPE_RUNS

    async def get_by_run_id(self, run_id: str) -> Optional[domain_scrape_run_models.ScrapeRunModel]:
        """Retrieves a scrape run by its unique run_id."""
        try:
            doc = await self.db_manager.find_one(self.collection_name, {"run_id": run_id})
            if doc:
                return domain_scrape_run_models.ScrapeRunModel(**doc)
            return None
        except Exception as e:
            raise RepositoryError(f"Failed to get scrape run by ID {run_id}: {e}") from e

    async def add(self, run_model: domain_scrape_run_models.ScrapeRunModel, session: Optional[Any] = None) -> str:
        """Adds a new scrape run document to the database."""
        try:
            run_dict = run_model.model_dump(by_alias=True, exclude_none=True)
            inserted_id = await self.db_manager.insert_one(self.collection_name, run_dict, session=session)
            # Ensure run_id is passed if not already part of the model _id handling
            if "_id" in run_dict and inserted_id:
                return str(inserted_id)
            return run_model.run_id
        except DuplicateEntityError:
            raise # Re-raise if specific duplicate error is needed upstream
        except Exception as e:
            raise RepositoryError(f"Failed to add scrape run {run_model.run_id}: {e}") from e
    
    async def update(self, run_id: str, updates: Dict[str, Any], session: Optional[Any] = None) -> Optional[domain_scrape_run_models.ScrapeRunModel]:
        """
        Updates an existing scrape run document by run_id.
        Returns the updated run model or None if not found.
        """
File: src/upwork_scraper/infrastructure/database/repositories/mongo_skill_repository.py
"""
MongoDB implementation of the AbstractSkillRepository.
"""
import logging
import hashlib
from datetime import datetime, UTC
from typing import Any, Optional

from pymongo import ReturnDocument, DuplicateKeyError

from src.upwork_scraper.config import settings
from src.upwork_scraper.domain.models import skill as domain_skill_models, job as domain_job_models
from src.upwork_scraper.domain.repositories import AbstractSkillRepository
from src.upwork_scraper.domain.exceptions import RepositoryError, DuplicateEntityError
from src.upwork_scraper.infrastructure.database.connection import DatabaseConnectionManager
from upwork_extractor.utils.text_utils import normalize_whitespace

logger = logging.getLogger(__name__)


class MongoSkillRepository(AbstractSkillRepository):
    """
    MongoDB implementation of the AbstractSkillRepository.
    Handles persistence of skill data.
    """
    def __init__(self):
        self.db_manager = DatabaseConnectionManager()
        self.collection_name = settings.COLLECTION_SKILLS

    async def get_by_uid(self, uid: str) -> Optional[domain_skill_models.SkillModel]:
        """Retrieves a skill by its unique UID."""
        try:
            doc = await self.db_manager.find_one(self.collection_name, {"uid": uid})
            if doc:
                return domain_skill_models.SkillModel(**doc)
            return None
        except Exception as e:
            raise RepositoryError(f"Failed to get skill by UID {uid}: {e}") from e
    
    async def upsert(self, skill_info: domain_job_models.SkillInfo, increment_job_count: bool = True, session: Optional[Any] = None) -> str:
        """
        Inserts or updates a skill document based on SkillInfo.
        Returns the MongoDB ObjectId of the upserted document.
        """
        if not skill_info.name:
            raise RepositoryError("Skill name cannot be empty for upsert operation.")
        
        # Determine UID - use provided UID or generate from name as a fallback
        skill_uid = skill_info.uid or self._generate_skill_uid(skill_info.name)

        update_payload = {
            "name": skill_info.name.lower(),
            "pretty_name": skill_info.name,
            "pref_label": skill_info.name, # Default, can be overridden
            "source_type": skill_info.category or "derived_attribute",
            "last_seen_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }

        increment_fields = {}
        if increment_job_count:
            increment_fields["stats.job_count"] = 1
        if skill_info.category == "highlighted":
            increment_fields["stats.search_highlight_count"] = 1
        if skill_info.category == "mandatory":
            increment_fields["stats.relevance_mandatory_count"] = 1
        
        update_op = {
            "$set": update_payload,
            "$setOnInsert": {
                "uid": skill_uid,
                "created_at": datetime.now(UTC),
                "first_seen_at": datetime.now(UTC),
                "is_free_text": False, # Assume not free text unless specified
            }
        }
        if increment_fields:
            update_op["$inc"] = increment_fields

        try:
            result_doc = await self.db_manager.get_collection(self.collection_name).find_one_and_update(
                {"uid": skill_uid},
                update_op,
                upsert=True,
                return_document=ReturnDocument.AFTER,
                session=session
            )
            return str(result_doc["_id"]) if result_doc else None
        except DuplicateKeyError as e:
            # This can happen in a race condition if another process inserts the same skill.
            # We can gracefully handle this by fetching the existing document.
            logger.warning(f"Duplicate key on skill upsert for UID {skill_uid}. Fetching existing document.")
            existing_doc = await self.get_by_uid(skill_uid)
            if existing_doc:
                return existing_doc.id
            raise DuplicateEntityError("Skill", skill_uid, message=f"Skill with UID {skill_uid} already exists: {e}") from e
        except Exception as e:
            logger.error(f"Failed to upsert skill '{skill_info.name}' (UID: {skill_uid}): {e}", exc_info=True)
            raise RepositoryError(f"Failed to upsert skill: {e}") from e

    async def count(self) -> int:
        """Returns the total count of skill documents."""
        try:
            return await self.db_manager.count_documents(self.collection_name)
        except Exception as e:
            raise RepositoryError(f"Failed to count skills: {e}") from e
    
    def _generate_skill_uid(self, skill_name: str) -> str:
        """Generate a consistent UID for skills based on normalized name."""
        canonical = normalize_whitespace(skill_name).lower().replace(" ", "_").replace("-", "_")
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
File: src/upwork_scraper/infrastructure/database/repositories/mongo_url_repository.py
"""
MongoDB implementation of the AbstractUrlRepository.
"""
import logging
from datetime import datetime, UTC, timedelta
from typing import Any, Dict, List, Optional

from pymongo import ReturnDocument

from src.upwork_scraper.config import settings
from src.upwork_scraper.domain.models import url as domain_url_models
from src.upwork_scraper.domain.repositories import AbstractUrlRepository
from src.upwork_scraper.domain.exceptions import RepositoryError, DuplicateEntityError
from src.upwork_scraper.infrastructure.database.connection import DatabaseConnectionManager

logger = logging.getLogger(__name__)


class MongoUrlRepository(AbstractUrlRepository):
    """
    MongoDB implementation of the AbstractUrlRepository.
    Handles persistence and retrieval of search URL data.
    """
    def __init__(self):
        self.db_manager = DatabaseConnectionManager()
        self.collection_name = settings.COLLECTION_SEARCH_URLS

    async def get_by_id(self, url_id: str) -> Optional[domain_url_models.SearchURLModel]:
        """Retrieves a search URL by its unique ID."""
        try:
            doc = await self.db_manager.find_one(self.collection_name, {"id": url_id})
            if doc:
                return domain_url_models.SearchURLModel(**doc)
            return None
        except Exception as e:
            raise RepositoryError(f"Failed to get URL by ID {url_id}: {e}") from e

    async def add(self, url_model: domain_url_models.SearchURLModel, session: Optional[Any] = None) -> str:
        """Adds a new search URL document."""
        try:
            url_dict = url_model.model_dump(by_alias=True, exclude_none=True)
            inserted_id = await self.db_manager.insert_one(self.collection_name, url_dict, session=session)
            return inserted_id
        except DuplicateEntityError:
            raise
        except Exception as e:
            raise RepositoryError(f"Failed to add URL {url_model.id}: {e}") from e

    async def update(self, url_id: str, updates: Dict[str, Any], session: Optional[Any] = None) -> Optional[domain_url_models.SearchURLModel]:
        """Updates an existing search URL document."""
        try:
            updates["updated_at"] = datetime.now(UTC)
            result = await self.db_manager.get_collection(self.collection_name).find_one_and_update(
                {"id": url_id},
                {"$set": updates},
                return_document=ReturnDocument.AFTER,
                session=session
            )
            if result:
                return domain_url_models.SearchURLModel(**result)
            return None
        except Exception as e:
            raise RepositoryError(f"Failed to update URL {url_id}: {e}") from e

    async def delete(self, url_id: str, session: Optional[Any] = None) -> bool:
        """Deletes a search URL document."""
        try:
            return await self.db_manager.delete_one(self.collection_name, {"id": url_id}, session=session)
        except Exception as e:
            raise RepositoryError(f"Failed to delete URL {url_id}: {e}") from e
    
    async def list_all(self, enabled_only: bool = False, category: Optional[str] = None) -> List[domain_url_models.SearchURLModel]:
        """Lists all search URLs with optional filtering."""
        try:
            filters = {}
            if enabled_only:
                filters["enabled"] = True
            if category:
                filters["category"] = category
            
            url_docs = await self.db_manager.find_many(
                self.collection_name,
                filters,
                sort=[("created_at", -1)]
            )
            return [domain_url_models.SearchURLModel(**doc) for doc in url_docs]
        except Exception as e:
            raise RepositoryError(f"Failed to list all URLs: {e}") from e

    async def list_for_scraping(self, min_scrape_interval_minutes: int) -> List[domain_url_models.SearchURLModel]:
        """Gets all enabled URLs that are ready for scraping based on an interval."""
        try:
            now = datetime.now(UTC)
            threshold_time = now - timedelta(minutes=min_scrape_interval_minutes)
            
            filters = {
                "enabled": True,
                "$or": [
                    {"last_scraped_at": {"$exists": False}},
                    {"last_scraped_at": {"$lte": threshold_time}}
                ]
            }
            
            url_docs = await self.db_manager.find_many(
                self.collection_name,
                filters,
                sort=[("last_scraped_at", 1)] # Prioritize oldest scrapes
            )
            return [domain_url_models.SearchURLModel(**doc) for doc in url_docs]
        except Exception as e:
            raise RepositoryError(f"Failed to list URLs for scraping: {e}") from e

    async def get_statistics(self) -> Dict[str, Any]:
        """Gets aggregated statistics about all search URLs."""
        try:
            all_urls = await self.list_all()
            enabled_count = sum(1 for url in all_urls if url.enabled)
            total_jobs = sum(url.total_jobs_found for url in all_urls)
            total_scrapes = sum(url.total_scrape_count for url in all_urls)
            urls_with_errors = sum(1 for url in all_urls if url.last_error)
            
            categories_counts = {}
            for url in all_urls:
                if url.category:
                    categories_counts[url.category] = categories_counts.get(url.category, 0) + 1

            return {
                "total_urls": len(all_urls),
                "enabled_urls": enabled_count,
                "disabled_urls": len(all_urls) - enabled_count,
                "total_jobs_found_across_all_urls": total_jobs,
                "total_successful_scrapes": total_scrapes,
                "urls_with_errors": urls_with_errors,
                "categories_summary": categories_counts
            }
        except Exception as e:
            raise RepositoryError(f"Failed to get URL statistics: {e}") from e
File: src/upwork_scraper/infrastructure/database/init.py
"""
MongoDB database connection and repository implementations.
"""
File: src/upwork_scraper/infrastructure/database/connection.py
"""
MongoDB database connection and management (Asynchronous with Motor)
Implements connection pooling, index creation, and transaction management.
"""
import logging
from typing import Optional, Dict, Any, List, Callable, Awaitable, Tuple
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection, AsyncIOMotorClientSession
from pymongo import ASCENDING, DESCENDING, IndexModel
from pymongo.errors import ConnectionFailure, DuplicateKeyError, BulkWriteError

from src.upwork_scraper.config import settings
from src.upwork_scraper.domain.exceptions import RepositoryError # Use domain exception

logger = logging.getLogger(__name__)


class DatabaseConnectionManager:
    """
    MongoDB database connection manager (Asynchronous with Motor).
    Handles connection lifecycle, index creation, and transaction management.
    Designed as a class-based singleton.
    """

    _client: Optional[AsyncIOMotorClient] = None
    _database: Optional[AsyncIOMotorDatabase] = None

    @classmethod
    async def connect(cls) -> None:
        """
        Establish asynchronous connection to MongoDB.
        Configures connection pooling and creates indexes.
        Idempotent: will only connect if not already connected.
        """
        if cls._client and cls._database:
            logger.info("MongoDB client already connected.")
            return

        try:
            # Configure connection pooling explicitly for robustness
            cls._client = AsyncIOMotorClient(
                settings.MONGODB_URI,
                maxPoolSize=100,      # Max connections in pool
                minPoolSize=10,       # Min connections in pool
                maxIdleTimeMS=30000,  # Max time a connection can remain idle in the pool
                serverSelectionTimeoutMS=5000 # Timeout for server selection
            )
            cls._database = cls._client[settings.DATABASE_NAME]

            # Test connection by pinging the database
            await cls._client.admin.command('ping')
            logger.info(f"Connected to MongoDB at {settings.MONGODB_URI}")

            # Create indexes for performance
            await cls._create_indexes()

        except ConnectionFailure as e:
            logger.critical(f"Failed to connect to MongoDB: {e}", exc_info=True)
            raise RepositoryError(f"Failed to connect to MongoDB: {e}") from e
        except Exception as e:
            logger.critical(f"An unexpected error occurred during MongoDB connection: {e}", exc_info=True)
            raise RepositoryError(f"An unexpected error occurred during MongoDB connection: {e}") from e


    @classmethod
    async def disconnect(cls) -> None:
        """Close MongoDB connection gracefully."""
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._database = None
            logger.info("Disconnected from MongoDB")

    @classmethod
    async def get_database(cls) -> AsyncIOMotorDatabase:
        """
        Get database instance, establishing connection if not already established.
        This enables lazy initialization and makes the class more resilient.
        """
        if not cls._database:
            await cls.connect()
        if not cls._database: # Final check after attempted connection
            raise RepositoryError("Database connection could not be established.")
        return cls._database

    @classmethod
    async def get_collection(cls, collection_name: str) -> AsyncIOMotorCollection:
        """Get an asynchronous collection by name."""
        db = await cls.get_database() # Await the potentially connecting method
        return db[collection_name]

    @classmethod
    async def _create_indexes(cls) -> None:
        """
        Create database indexes for performance.
        Ensures common query fields are indexed for faster lookups.
        """
        db = await cls.get_database() # Ensure DB is connected

        # Jobs collection indexes
        jobs = db[settings.COLLECTION_JOBS]
        await jobs.create_indexes([
            IndexModel([("uid", ASCENDING)], unique=True, name="uid_unique"),
            IndexModel([("status", ASCENDING)], name="status_idx"),
            IndexModel([("created_at", DESCENDING)], name="created_at_idx"),
            IndexModel([("client_id", ASCENDING)], name="client_id_idx"),
            IndexModel([("pipeline.discovered_at", DESCENDING)], name="discovered_at_idx"),
            IndexModel([("pipeline.is_enriched", ASCENDING)], name="is_enriched_idx"),
            # Combined text index for title and description for search
            IndexModel(
                [("title", "text"), ("content.description_plain", "text")],
                name="job_text_search_idx",
                default_language="english",
                weights={"title": 5, "content.description_plain": 1}
            ),
            IndexModel([("content.skill_ids", ASCENDING)], name="skill_ids_idx", sparse=True),
        ])

        # Clients collection indexes
        clients = db[settings.COLLECTION_CLIENTS]
        await clients.create_indexes([
            IndexModel([("client_key", ASCENDING)], unique=True, name="client_key_unique"),
            IndexModel([("created_at", DESCENDING)], name="created_at_idx"),
            IndexModel([("stats.total_charges.amount", DESCENDING)], name="client_total_spent_idx", sparse=True),
            IndexModel([("stats.score", DESCENDING)], name="client_score_idx", sparse=True),
        ])

        # Skills collection indexes
        skills = db[settings.COLLECTION_SKILLS]
        await skills.create_indexes([
            IndexModel([("uid", ASCENDING)], unique=True, name="uid_unique"),
            IndexModel([("name", ASCENDING)], name="name_idx"),
            IndexModel([("stats.job_count", DESCENDING)], name="job_count_idx"),
        ])

        # Search URLs collection indexes
        search_urls = db[settings.COLLECTION_SEARCH_URLS]
        await search_urls.create_indexes([
            IndexModel([("id", ASCENDING)], unique=True, name="id_unique"),
            IndexModel([("enabled", ASCENDING)], name="enabled_idx"),
            IndexModel([("category", ASCENDING)], name="category_idx"),
            IndexModel([("created_at", DESCENDING)], name="created_at_idx"),
        ])

        # Scrape runs collection indexes
        scrape_runs = db[settings.COLLECTION_SCRAPE_RUNS]
        await scrape_runs.create_indexes([
            IndexModel([("run_id", ASCENDING)], unique=True, name="run_id_unique"),
            IndexModel([("status", ASCENDING)], name="status_idx"),
            IndexModel([("started_at", DESCENDING)], name="started_at_idx"),
            IndexModel([("run_type", ASCENDING)], name="run_type_idx"),
        ])

        logger.info("Database indexes created successfully")

    @classmethod
    async def health_check(cls) -> Dict[str, Any]:
        """Check database health asynchronously."""
        try:
            if not cls._client:
                return {"status": "disconnected"}

            await cls._client.admin.command('ping') # Perform a simple operation to check connection

            db = await cls.get_database() # Ensure connection is established
            stats = {
                "status": "connected",
                "database": settings.DATABASE_NAME,
                "collections": {
                    "jobs": await db[settings.COLLECTION_JOBS].count_documents({}),
                    "clients": await db[settings.COLLECTION_CLIENTS].count_documents({}),
                    "skills": await db[settings.COLLECTION_SKILLS].count_documents({}),
                    "search_urls": await db[settings.COLLECTION_SEARCH_URLS].count_documents({}),
                    "scrape_runs": await db[settings.COLLECTION_SCRAPE_RUNS].count_documents({}),
                }
            }
            return stats

        except Exception as e:
            logger.error(f"MongoDB health check failed: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}

    @classmethod
    async def run_in_transaction(cls, operations_callback: Callable[[AsyncIOMotorClientSession], Awaitable[Any]]) -> Any:
        """
        Executes a series of database operations within a MongoDB transaction.
        
        Args:
            operations_callback: An async callable that accepts an AsyncIOMotorClientSession
                                 and performs the transactional database operations.
        
        Returns:
            The result of the operations_callback.
            
        Raises:
            RepositoryError: If the transaction fails or MongoDB is not connected.
        """
        if not cls._client:
            await cls.connect() # Ensure client is connected
        if not cls._client:
            raise RepositoryError("MongoDB client not connected for transaction.")

        async with await cls._client.start_session() as session:
            async with session.start_transaction():
                try:
                    result = await operations_callback(session)
                    return result
                except Exception as e:
                    logger.error(f"MongoDB transaction failed, rolling back: {e}", exc_info=True)
                    # The 'async with session.start_transaction()' handles the abort
                    raise RepositoryError(f"MongoDB transaction failed: {e}") from e

    @classmethod
    async def insert_one(cls, collection_name: str, document: Dict[str, Any], session: Optional[AsyncIOMotorClientSession] = None) -> str:
        """Insert a single document asynchronously."""
        collection = await cls.get_collection(collection_name)
        try:
            result = await collection.insert_one(document, session=session)
            logger.debug(f"Inserted document into {collection_name} with ID: {result.inserted_id}")
            return str(result.inserted_id)
        except DuplicateKeyError as e:
            logger.warning(f"Duplicate key error when inserting into {collection_name}. Doc: {document.get('uid') or document.get('id') or document.get('client_key')}. Error: {e}")
            raise RepositoryError(f"Duplicate key error: {e}") from e
        except Exception as e:
            logger.error(f"Error inserting into {collection_name}: {e}", exc_info=True)
            raise RepositoryError(f"Error inserting document: {e}") from e

    @classmethod
    async def insert_many(cls, collection_name: str, documents: List[Dict[str, Any]], session: Optional[AsyncIOMotorClientSession] = None) -> List[str]:
        """Insert multiple documents asynchronously."""
        if not documents:
            return []
        collection = await cls.get_collection(collection_name)
        try:
            # ordered=False allows partial success but requires handling BulkWriteError for details
            result = await collection.insert_many(documents, ordered=False, session=session)
            logger.debug(f"Inserted {len(result.inserted_ids)} documents into {collection_name}.")
            return [str(id) for id in result.inserted_ids]
        except BulkWriteError as e: # Catch BulkWriteError for more detailed error handling
            write_errors = e.details.get('writeErrors', [])
            error_msg = f"{len(write_errors)} documents failed during bulk insert into {collection_name}."
            logger.warning(f"{error_msg} Details: {write_errors}", exc_info=True)
            # Re-raise with custom exception, potentially including more details
            raise RepositoryError(error_msg, details=write_errors) from e
        except Exception as e:
            logger.error(f"Error inserting many into {collection_name}: {e}", exc_info=True)
            raise RepositoryError(f"Error inserting documents: {e}") from e

    @classmethod
    async def find_one(cls, collection_name: str, filter: Dict[str, Any], session: Optional[AsyncIOMotorClientSession] = None) -> Optional[Dict[str, Any]]:
        """Find a single document asynchronously."""
        collection = await cls.get_collection(collection_name)
        try:
            return await collection.find_one(filter, session=session)
        except Exception as e:
            logger.error(f"Error finding one in {collection_name} with filter {filter}: {e}", exc_info=True)
            raise RepositoryError(f"Error finding document: {e}") from e


    @classmethod
    async def find_many(cls, collection_name: str, filter: Dict[str, Any] = None,
                 skip: int = 0, limit: int = 0, sort: Optional[List[Tuple[str, Any]]] = None, session: Optional[AsyncIOMotorClientSession] = None) -> List[Dict[str, Any]]:
        """Find multiple documents asynchronously."""
        collection = await cls.get_collection(collection_name)
        try:
            cursor = collection.find(filter or {}, session=session)

            if sort:
                cursor = cursor.sort(sort)
            if skip:
                cursor = cursor.skip(skip)
            if limit > 0: # Only apply limit if greater than 0
                cursor = cursor.limit(limit)

            return await cursor.to_list(length=limit if limit > 0 else None)
        except Exception as e:
            logger.error(f"Error finding many in {collection_name} with filter {filter}: {e}", exc_info=True)
            raise RepositoryError(f"Error finding documents: {e}") from e


    @classmethod
    async def update_one(cls, collection_name: str, filter: Dict[str, Any],
                  update: Dict[str, Any], upsert: bool = False, session: Optional[AsyncIOMotorClientSession] = None) -> bool:
        """Update a single document asynchronously."""
        collection = await cls.get_collection(collection_name)
        try:
            result = await collection.update_one(filter, {"$set": update}, upsert=upsert, session=session)
            logger.debug(f"Updated document in {collection_name} with filter {filter}. Matched: {result.matched_count}, Modified: {result.modified_count}, Upserted: {result.upserted_id}")
            return result.modified_count > 0 or result.upserted_id is not None
        except Exception as e:
            logger.error(f"Error updating one in {collection_name} with filter {filter} and update {update}: {e}", exc_info=True)
            raise RepositoryError(f"Error updating document: {e}") from e


    @classmethod
    async def update_many(cls, collection_name: str, filter: Dict[str, Any],
                   update: Dict[str, Any], session: Optional[AsyncIOMotorClientSession] = None) -> int:
        """Update multiple documents asynchronously."""
        collection = await cls.get_collection(collection_name)
        try:
            result = await collection.update_many(filter, {"$set": update}, session=session)
            logger.debug(f"Updated {result.modified_count} documents in {collection_name} with filter {filter}.")
            return result.modified_count
        except Exception as e:
            logger.error(f"Error updating many in {collection_name} with filter {filter} and update {update}: {e}", exc_info=True)
            raise RepositoryError(f"Error updating documents: {e}") from e


    @classmethod
    async def delete_one(cls, collection_name: str, filter: Dict[str, Any], session: Optional[AsyncIOMotorClientSession] = None) -> bool:
        """Delete a single document asynchronously."""
        collection = await cls.get_collection(collection_name)
        try:
            result = await collection.delete_one(filter, session=session)
            logger.debug(f"Deleted {result.deleted_count} document from {collection_name} with filter {filter}.")
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting one from {collection_name} with filter {filter}: {e}", exc_info=True)
            raise RepositoryError(f"Error deleting document: {e}") from e


    @classmethod
    async def delete_many(cls, collection_name: str, filter: Dict[str, Any], session: Optional[AsyncIOMotorClientSession] = None) -> int:
        """Delete multiple documents asynchronously."""
        collection = await cls.get_collection(collection_name)
        try:
            result = await collection.delete_many(filter, session=session)
            logger.debug(f"Deleted {result.deleted_count} documents from {collection_name} with filter {filter}.")
            return result.deleted_count
        except Exception as e:
            logger.error(f"Error deleting many from {collection_name} with filter {filter}: {e}", exc_info=True)
            raise RepositoryError(f"Error deleting documents: {e}") from e


    @classmethod
    async def count_documents(cls, collection_name: str, filter: Dict[str, Any] = None, session: Optional[AsyncIOMotorClientSession] = None) -> int:
        """Count documents matching filter asynchronously."""
        collection = await cls.get_collection(collection_name)
        try:
            return await collection.count_documents(filter or {}, session=session)
        except Exception as e:
            logger.error(f"Error counting documents in {collection_name} with filter {filter}: {e}", exc_info=True)
            raise RepositoryError(f"Error counting documents: {e}") from e


    @classmethod
    async def aggregate(cls, collection_name: str, pipeline: List[Dict[str, Any]], session: Optional[AsyncIOMotorClientSession] = None) -> List[Dict[str, Any]]:
        """Run an aggregation pipeline asynchronously."""
        collection = await cls.get_collection(collection_name)
        try:
            return await collection.aggregate(pipeline, session=session).to_list(length=None)
        except Exception as e:
            logger.error(f"Error running aggregation on {collection_name} with pipeline {pipeline}: {e}", exc_info=True)
            raise RepositoryError(f"Error during aggregation: {e}") from e
File: src/upwork_scraper/infrastructure/scraping/init.py
"""
Adapters for external scraping services and libraries.
"""
File: src/upwork_scraper/infrastructure/scraping/scrapfly_client.py
"""
Scrapfly API Client - Rebuilt for robustness and flexibility.
Handles web scraping with proxy rotation, ASP, intelligent retries, and file-based caching.
"""
import hashlib
import json
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx
import tenacity
from tenacity import retry_if_exception_type

from src.upwork_scraper.config import settings
from src.upwork_scraper.domain.exceptions import ScrapflyError, ScrapflyConcurrencyLimitError, ScrapflyRequestFailedError
from src.upwork_scraper.domain.repositories import AbstractScrapingAdapter

logger = logging.getLogger(__name__)


class ApiKeyState:
    """Helper class to manage the state of an individual API key."""
    def __init__(self, key: str):
        self.key = key
        self.status: str = "available" # available, rate_limited, exhausted
        self.cooldown_until: Optional[datetime] = None

    def is_available(self) -> bool:
        if self.status == "available":
            return True
        if self.status == "rate_limited" and self.cooldown_until:
            if datetime.now(UTC) > self.cooldown_until:
                self.status = "available"
                self.cooldown_until = None
                logger.info(f"API key ...{self.key[-4:]} cooldown has ended. Status set to 'available'.")
                return True
        return False

    def set_rate_limited(self, cooldown_seconds: int = 60):
        self.status = "rate_limited"
        self.cooldown_until = datetime.now(UTC) + timedelta(seconds=cooldown_seconds)
        logger.warning(f"API key ...{self.key[-4:]} is rate-limited. Cooling down for {cooldown_seconds} seconds.")


class ScrapflyClient(AbstractScrapingAdapter):
    """
    Scrapfly API Client with intelligent retries, key rotation, and caching.
    Implements the AbstractScrapingAdapter interface.
    """
    _instance: Optional["ScrapflyClient"] = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ScrapflyClient, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # This check prevents re-initialization on subsequent calls
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self.api_url: str = settings.SCRAPFLY_API_URL
        api_keys_str = settings.SCRAPFLY_API_KEY
        
        if not api_keys_str:
            logger.critical("SCRAPFLY_API_KEY is not configured. Scraping will fail.")
            raise ValueError("SCRAPFLY_API_KEY is not configured in settings.")

        self.api_keys: List[ApiKeyState] = [ApiKeyState(k.strip()) for k in api_keys_str.split(',') if k.strip()]
        self.proxy_pools: List[str] = settings.SCRAPFLY_PROXY_POOLS
        self.default_country: str = settings.SCRAPFLY_COUNTRY
        self.default_timeout_ms: int = settings.SCRAPFLY_TIMEOUT
        self.default_rendering_wait_ms: int = settings.SCRAPFLY_RENDERING_WAIT

        # Local file-based cache
        self.cache_dir = settings.CACHE_DIR / "scrapfly_cache"
        self.enable_cache = settings.ENABLE_CACHE
        self.cache_expiry_minutes = settings.CACHE_EXPIRY_MINUTES

        if self.enable_cache:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Local file-based cache enabled at: {self.cache_dir}")
        else:
            logger.info("Local file-based cache disabled.")
        
        self._current_key_index = 0
        self._initialized = True

    def _get_next_api_key(self) -> ApiKeyState:
        """
        Gets the next available API key in a round-robin fashion, skipping keys on cooldown.
        """
        if not self.api_keys:
            raise ValueError("No API keys configured.")
        
        # Try to find an available key, cycling through the list at most once
        for _ in range(len(self.api_keys)):
            key_state = self.api_keys[self._current_key_index]
            self._current_key_index = (self._current_key_index + 1) % len(self.api_keys)
            if key_state.is_available():
                return key_state
        
        # If all keys are on cooldown, raise an exception
        raise ScrapflyError("All Scrapfly API keys are currently rate-limited or exhausted.", retryable=True)

    async def fetch(
        self,
        url: str,
        render_js: bool = True,
        country: Optional[str] = None,
        proxy_pool: Optional[str] = None,
        asp: bool = True,
        timeout_ms: Optional[int] = None,
        use_cache: Optional[bool] = None,
        rendering_wait_ms: Optional[int] = None,
        wait_for_selector: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        tags: Optional[List[str]] = None,
        correlation_id: Optional[str] = None,
        max_retries: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Fetches a URL with caching, intelligent key rotation, and configurable retries.
        """
        resolved_use_cache = use_cache if use_cache is not None else self.enable_cache

        # Check local cache first
        if resolved_use_cache:
            cached = self._get_from_cache(url)
            if cached:
                logger.debug(f"✅ Local cache hit for {url}")
                return cached

        # Define the retryer dynamically based on per-request or global settings
        actual_max_retries = max_retries if max_retries is not None else settings.MAX_RETRIES
        
        # Custom retry condition: only retry if the exception is marked as retryable
        def is_retryable(e: BaseException) -> bool:
            return isinstance(e, (httpx.RequestError, httpx.TimeoutException)) or \
                   (isinstance(e, ScrapflyError) and e.retryable)

        retryer = tenacity.AsyncRetrying(
            wait=tenacity.wait_exponential(multiplier=1, min=2, max=settings.RETRY_DELAY * 2),
            stop=tenacity.stop_after_attempt(actual_max_retries + 1),
            retry=retry_if_exception_type(Exception) if is_retryable else False, # Simplified to check inside function
            reraise=True
        )
        
        try:
            result = await retryer.call(
                self._execute_fetch,
                url=url,
                render_js=render_js,
                country=country,
                proxy_pool=proxy_pool,
                asp=asp,
                timeout_ms=timeout_ms,
                rendering_wait_ms=rendering_wait_ms,
                wait_for_selector=wait_for_selector,
                headers=headers,
                tags=tags,
                correlation_id=correlation_id,
            )
        except tenacity.RetryError as e:
            # Reraise the last underlying exception for the caller to handle
            raise e.last_attempt.result() from e

        # Success - validate and cache
        if result["success"]:
            if self._is_valid_upwork_content(result.get("html", "")):
                if resolved_use_cache:
                    self._set_to_cache(url, result)
                logger.info(f"✅ Successfully scraped {url}")
                return result
            else:
                error_msg = "Invalid Upwork content received (possible CAPTCHA or block)."
                logger.warning(f"❌ {error_msg} for {url}. Content: {result.get('html', '')[:200]}")
                # Treat as a definitive failure for content validation, not retryable
                raise ScrapflyError(error_msg, status_code=result.get("status_code", 200), details=result, retryable=False)
        
        # This part should ideally not be reached if exceptions are raised correctly
        error_msg = result.get("error", "Unknown scraping failure after fetch.")
        raise ScrapflyError(error_msg, status_code=result.get("status_code"), details=result, retryable=False)

    async def _execute_fetch(
        self,
        url: str,
        render_js: bool,
        country: Optional[str],
        proxy_pool: Optional[str],
        asp: bool,
        timeout_ms: Optional[int],
        rendering_wait_ms: Optional[int],
        wait_for_selector: Optional[str],
        headers: Optional[Dict[str, str]],
        tags: Optional[List[str]],
        correlation_id: Optional[str],
    ) -> Dict[str, Any]:
        """
        Internal method to execute a single fetch attempt. Called by tenacity.
        """
        api_key_state = self._get_next_api_key()
        api_key = api_key_state.key
        
        logger.info(f"Attempting scrape for {url} with key ...{api_key[-4:]}")

        try:
            return await self._fetch_with_key(
                url=url,
                api_key=api_key,
                render_js=render_js,
                country=country or self.default_country,
                proxy_pool=proxy_pool or (self.proxy_pools[0] if self.proxy_pools else "public_datacenter_pool"),
                asp=asp,
                timeout_ms=timeout_ms or self.default_timeout_ms,
                rendering_wait_ms=rendering_wait_ms or self.default_rendering_wait_ms,
                wait_for_selector=wait_for_selector,
                headers=headers,
                tags=tags,
                correlation_id=correlation_id,
            )
        except ScrapflyConcurrencyLimitError as e:
            api_key_state.set_rate_limited()
            raise e # Re-raise to trigger retry with a different key
        except ScrapflyError as e:
            # If the error is retryable, tenacity will handle it. If not, it will fail fast.
            raise e
    
    async def _fetch_with_key(
        self,
        url: str,
        api_key: str,
        render_js: bool,
        country: str,
        proxy_pool: str,
        asp: bool,
        timeout_ms: int,
        rendering_wait_ms: Optional[int],
        wait_for_selector: Optional[str],
        headers: Optional[Dict[str, str]],
        tags: Optional[List[str]],
        correlation_id: Optional[str],
    ) -> Dict[str, Any]:
        """
        Internal method to fetch with a specific API key using httpx (async).
        Raises specific ScrapflyError on non-successful responses.
        """
        # Build query parameters as a list of tuples for flexibility
        params_list: List[Tuple[str, str]] = [
            ("key", api_key),
            ("url", url),
            ("country", country),
            ("proxy_pool", proxy_pool),
            ("render_js", str(render_js).lower()),
            ("asp", str(asp).lower()),
            ("retry", "true"),
        ]

        if rendering_wait_ms is not None:
            params_list.append(("rendering_wait", str(rendering_wait_ms)))
        elif render_js:
            params_list.append(("rendering_wait", str(self.default_rendering_wait_ms)))

        if wait_for_selector:
            params_list.append(("wait_for_selector", wait_for_selector))

        if headers:
            for key, value in headers.items():
                params_list.append((f"headers[{key}]", value))

        if tags:
            for tag in tags:
                params_list.append(("tags[]", tag))

        if correlation_id:
            params_list.append(("correlation_id", correlation_id))

        request_headers = {
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
        }
        
        httpx_timeout_s = max(timeout_ms / 1000, 155) + 10 # Add buffer

        try:
            async with httpx.AsyncClient(timeout=httpx_timeout_s) as client:
                response = await client.get(self.api_url, params=params_list, headers=request_headers)

            # Handle non-200 HTTP status from Scrapfly API
            if response.status_code != 200:
                error_text = response.text[:500]
                error_code = response.headers.get("X-Scrapfly-Reject-Code", "UNKNOWN")
                error_desc = response.headers.get("X-Scrapfly-Reject-Description", "")
                is_retryable = response.headers.get("X-Scrapfly-Reject-Retryable", "false") == "true"
                
                log_level = logger.warning if is_retryable else logger.error
                log_level(
                    f"❌ Scrapfly API HTTP {response.status_code} for {url}\n"
                    f"   Error Code: {error_code}\n   Description: {error_desc}\n   Retryable: {is_retryable}\n   Details: {error_text}"
                )
                
                # Raise specific exceptions
                if response.status_code == 429:
                    raise ScrapflyConcurrencyLimitError(
                        message=f"Scrapfly API returned HTTP {response.status_code}",
                        details={"error_description": error_desc, "response_body": error_text}
                    )
                else:
                    raise ScrapflyRequestFailedError(
                        message=f"Scrapfly API returned HTTP {response.status_code}",
                        status_code=response.status_code,
                        error_code=error_code,
                        details={"error_description": error_desc, "response_body": error_text},
                        retryable=is_retryable
                    )

            response_data = response.json()
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON response from Scrapfly for {url}: {e}")
            raise ScrapflyError("Invalid JSON response from Scrapfly", details={"raw_response": response.text[:500]}, retryable=True) from e
        except httpx.TimeoutException as e:
            logger.error(f"⏱️ Request timeout for {url}: {e}")
            raise ScrapflyError("Request timeout", status_code=408, retryable=True) from e
        except httpx.RequestError as e:
            logger.error(f"❌ Network error for {url}: {e}")
            raise ScrapflyError(f"Network error: {str(e)}", retryable=True) from e

        result_content = response_data.get("result", {})
        html_content = result_content.get("content", "")
        content_format = result_content.get("format", "")

        # Handle large objects by downloading them automatically
        if content_format in ["clob", "blob"]:
            download_url = html_content
            logger.warning(f"⚠️ Large object detected for {url}. Automatically downloading from: {download_url}")
            try:
                # Use httpx to download the content, must be authenticated
                async with httpx.AsyncClient() as download_client:
                    auth_download_url = f"{download_url}&key={api_key}"
                    content_response = await download_client.get(auth_download_url, timeout=180) # Longer timeout for large files
                    content_response.raise_for_status()
                    html_content = content_response.text
                    logger.info(f"✅ Successfully downloaded large object content for {url}")
            except httpx.RequestError as e:
                raise ScrapflyError(f"Failed to download large object content from {download_url}", details={"error": str(e)}, retryable=True) from e

        metadata = {
            "status_code": result_content.get("status_code"),
            "duration": result_content.get("duration"),
            "cost": result_content.get("cost"),
            "url_final": result_content.get("url"),
            "format": content_format,
            "api_cost": response.headers.get("X-Scrapfly-Api-Cost"),
            "remaining_credit": response.headers.get("X-Scrapfly-Remaining-Api-Credit"),
            "account_concurrent_usage": response.headers.get("X-Scrapfly-Account-Concurrent-Usage"),
            "remaining_concurrent": response.headers.get("X-Scrapfly-Account-Remaining-Concurrent-Usage"),
            "context": response_data.get("context", {}),
            "config": response_data.get("config", {}),
        }

        return {"success": True, "html": html_content, "metadata": metadata, "url": url}
    
    # ... Other methods like _is_valid_upwork_content, caching, and health check remain largely the same,
    # but I will include them for completeness.

    def _is_valid_upwork_content(self, html: str) -> bool:
        """
        Validate Upwork page content to detect blocks, CAPTCHAs, or unexpected content.
        """
        if not html or len(html) < 500:
            return False
        
        if html.startswith("[LARGE_OBJECT:"):
            return True

        html_lower = html.lower()

        upwork_markers = ["window.__nuxt__", "__nuxt_data__", "upwork.com", "<h1 data-qa=", "client-activity"]
        block_indicators = ["captcha", "recaptcha", "cloudflare", "access denied", "please verify you are a human"]

        has_upwork_marker = any(marker in html_lower for marker in upwork_markers)
        has_block_indicator = any(indicator in html_lower for indicator in block_indicators)

        if has_block_indicator:
            logger.warning("⚠️ Block indicator detected in content.")
            return False
        if not has_upwork_marker:
            logger.warning("⚠️ No strong Upwork markers found in content. Potentially generic page or block.")
            return False
        return True

    def _get_cache_path(self, url: str) -> Path:
        """Generate cache file path from URL hash."""
        url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{url_hash}.json"

    def _get_from_cache(self, url: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached result if valid and not expired."""
        if not self.enable_cache:
            return None
        cache_path = self._get_cache_path(url)
        if not cache_path.exists():
            return None
        try:
            with open(cache_path, encoding="utf-8") as f:
                cached_data = json.load(f)
            cached_time = datetime.fromisoformat(cached_data["timestamp"])
            if datetime.now(UTC) - cached_time < timedelta(minutes=self.cache_expiry_minutes):
                return cached_data["result"]
            else:
                cache_path.unlink(missing_ok=True)
                return None
        except Exception as e:
            logger.warning(f"Invalid cache file for {url}: {e}, removing...")
            cache_path.unlink(missing_ok=True)
            return None

    def _set_to_cache(self, url: str, result: Dict[str, Any]) -> None:
        """Save result to cache."""
        if not self.enable_cache:
            return
        try:
            cache_path = self._get_cache_path(url)
            cache_data = {"timestamp": datetime.now(UTC).isoformat(), "result": result, "url": url}
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to write cache for {url}: {e}")

    async def get_account_info(self) -> Dict[str, Any]:
        """Get Scrapfly account information (credits, concurrency) for the first API key."""
        if not self.api_keys:
            return {"success": False, "error": "No API keys configured", "status": "unhealthy"}
        try:
            api_key = self.api_keys[0].key
            result = await self._fetch_with_key(
                url="https://httpbin.dev/get",
                api_key=api_key,
                render_js=False,
                asp=False,
                timeout_ms=10000,
                country='us',
                proxy_pool='public_datacenter_pool',
                rendering_wait_ms=None, wait_for_selector=None, headers=None, tags=None, correlation_id=None,
            )
            if result["success"]:
                metadata = result.get("metadata", {})
                return {
                    "success": True,
                    "api_key_used_suffix": api_key[-4:],
                    "remaining_credit": metadata.get("remaining_credit"),
                    "concurrent_usage": metadata.get("account_concurrent_usage"),
                    "remaining_concurrent": metadata.get("remaining_concurrent"),
                    "status": "healthy"
                }
            else:
                return {"success": False, "error": result.get("error"), "status": "unhealthy"}
        except ScrapflyError as e:
            return {"success": False, "error": str(e), "status_code": e.status_code, "status": "unhealthy"}
        except Exception as e:
            logger.exception("Failed to get Scrapfly account info:")
            return {"success": False, "error": f"Unexpected error: {str(e)}", "status": "unhealthy"}
File: src/upwork_scraper/infrastructure/scraping/upwork_extractor_client.py
"""
Adapter for the standalone `upwork_extractor` library.
This class wraps the library's synchronous calls in an async interface
to be used by the application services.
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple

from upwork_extractor import (
    UpworkDataExtractor,
    ExtractionConfig,
    ValidationLevel,
    ExtractionError,
    NuxtParsingError,
    ValidationError as ExtractorValidationError,
    CriticalDataMissingError,
)
from src.upwork_scraper.domain.repositories import AbstractUpworkExtractorAdapter
from src.upwork_scraper.domain.exceptions import UpworkExtractionError, UpworkExtractionValidationError

logger = logging.getLogger(__name__)


class UpworkExtractorAdapter(AbstractUpworkExtractorAdapter):
    """
    Adapter for the Upwork data extraction library.
    Runs the synchronous extractor in a thread pool to avoid blocking the event loop.
    """
    def __init__(self):
        # Configure the extractor for permissive validation, as we want to get as much data as possible
        # and handle validation issues at the application level if needed.
        self.config = ExtractionConfig(validation_level=ValidationLevel.NORMAL)
        logger.info("UpworkExtractorAdapter initialized with NORMAL validation level.")

    def _run_extraction_sync(self, html_content: str) -> Dict[str, Any]:
        """Synchronous wrapper to run the extractor and get normalized data."""
        try:
            extractor = UpworkDataExtractor(html_content, self.config)
            job_data = extractor.extract()
            # Use the external mapper to get the normalized dictionary
            from upwork_extractor.mappers import job_data_to_normalized_dict
            return job_data_to_normalized_dict(job_data)
        except (CriticalDataMissingError, ExtractorValidationError) as e:
            logger.error(f"Upwork extractor validation failed: {e}", exc_info=True)
            raise UpworkExtractionValidationError(f"Extractor validation failed: {e}") from e
        except (ExtractionError, NuxtParsingError) as e:
            logger.error(f"Upwork extractor failed: {e}", exc_info=True)
            raise UpworkExtractionError(f"Extractor failed: {e}") from e
        except Exception as e:
            logger.exception("An unexpected error occurred in the Upwork extractor library:")
            raise UpworkExtractionError(f"An unexpected extractor error occurred: {e}") from e

    async def extract_job_detail(self, html_content: str) -> Dict[str, Any]:
        """Asynchronously extracts structured job detail data from HTML."""
        return await asyncio.to_thread(self._run_extraction_sync, html_content)

    def _run_search_extraction_sync(self, html_content: str) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """Synchronous wrapper to extract job summaries and pagination from a search page."""
        try:
            extractor = UpworkDataExtractor(html_content, self.config)
            # This is a bit of a workaround, as the extractor is designed for detail pages.
            # We need to access its internal NuxtParser to get search-specific data.
            # This indicates a potential improvement for the extractor library itself to have a dedicated search page mode.
            if not extractor.nuxt_available:
                raise UpworkExtractionError("NUXT data not found on search page, cannot extract job summaries.")
            
            job_summaries = extractor.nuxt_parser.extract_search_job_summaries()
            pagination_data = extractor.nuxt_parser.find_pagination_data()
            return job_summaries, pagination_data
        except (ExtractionError, NuxtParsingError) as e:
            logger.error(f"Upwork search extractor failed: {e}", exc_info=True)
            raise UpworkExtractionError(f"Search extractor failed: {e}") from e
        except Exception as e:
            logger.exception("An unexpected error occurred in the Upwork search extractor:")
            raise UpworkExtractionError(f"An unexpected search extractor error occurred: {e}") from e

    async def extract_search_job_summaries(self, html_content: str) -> List[Dict[str, Any]]:
        """Asynchronously extracts job summaries from search results HTML."""
        summaries, _ = await asyncio.to_thread(self._run_search_extraction_sync, html_content)
        return summaries
    
    async def extract_pagination_data(self, html_content: str) -> Optional[Dict[str, Any]]:
        """Asynchronously extracts pagination metadata from search results HTML."""
        _, pagination = await asyncio.to_thread(self._run_search_extraction_sync, html_content)
        return pagination
File: src/upwork_scraper/infrastructure/sse/init.py
"""
Server-Sent Events (SSE) management infrastructure.
"""
File: src/upwork_scraper/infrastructure/sse/sse_manager.py
"""
SSE (Server-Sent Events) manager for real-time progress updates.
Singleton pattern to manage state across the application.
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, UTC

logger = logging.getLogger(__name__)


class SSEManager:
    """Manager for Server-Sent Events connections, implemented as a singleton."""
    _instance: Optional["SSEManager"] = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SSEManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # Prevent re-initialization
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        # Store active connections by run_id, using a standard dict for explicit control
        self.connections: Dict[str, asyncio.Queue] = {}
        # Store latest status for each run_id for new connections
        self.run_status: Dict[str, Dict[str, Any]] = {}
        self._initialized = True
        logger.info("SSEManager initialized.")

    async def connect(self, run_id: str) -> asyncio.Queue:
        """
        Establishes a new SSE connection for a given run_id.
        Returns the asyncio.Queue associated with this run_id.
        """
        if run_id not in self.connections:
            self.connections[run_id] = asyncio.Queue()
        queue = self.connections[run_id]
        logger.info(f"SSE client connected for run {run_id}.")
        return queue

    def disconnect(self, run_id: str):
        """Removes an SSE connection for a given run_id."""
        if run_id in self.connections:
            del self.connections[run_id]
            logger.info(f"SSE client disconnected and connection for run {run_id} cleaned up.")
        # The run_status is cleaned up by a periodic task, not on disconnect.

    async def send_update(self, run_id: str, data: Dict[str, Any]):
        """
        Sends a generic update to a specific run's connection.
        Also updates the stored latest status for the run.
        """
        self.run_status[run_id] = data # Store latest status
        
        # Send to connected client if any
        if run_id in self.connections:
            queue = self.connections[run_id]
            try:
                # Use put_nowait inside an async function as it's non-blocking for a queue with no size limit
                # If the queue were bounded, await queue.put() would be necessary.
                queue.put_nowait(data)
                logger.debug(f"Sent SSE update for run {run_id}: Type={data.get('type', 'unknown')}, Status={data.get('status', 'unknown')}")
            except asyncio.QueueFull:
                logger.warning(f"SSE queue for run {run_id} is full. Dropping update.")
            except Exception as e:
                logger.error(f"Failed to put message on SSE queue for run {run_id}: {e}")
        else:
            logger.debug(f"No active SSE connection for run {run_id}, stored status only.")

    async def send_scraping_progress(self, run_id: str, progress_data: Dict[str, Any]):
        """Sends a scraping progress update."""
        update = {
            "type": "progress",
            "run_id": run_id,
            "timestamp": datetime.now(UTC).isoformat(),
            **progress_data
        }
        await self.send_update(run_id, update)

    async def send_completion(self, run_id: str, results: Dict[str, Any]):
        """Sends a completion notification for a scrape run."""
        update = {
            "type": "completion",
            "run_id": run_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "status": results.get("final_status", "completed"),
            **results
        }
        await self.send_update(run_id, update)

    async def send_error(self, run_id: str, error: str, status_code: int = None, details: Any = None):
        """Sends an error notification for a scrape run."""
        update = {
            "type": "error",
            "run_id": run_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "status": "failed",
            "error": error,
            "status_code": status_code,
            "details": details
        }
        await self.send_update(run_id, update)

    def get_active_connections_count(self) -> int:
        """Returns the number of active SSE connections."""
        return len(self.connections)

    async def cleanup_stale_status(self, max_age_seconds: int = 3600):
        """
        Cleans up stale run status data from memory for runs that completed
        long ago and no longer have active connections.
        """
        now = datetime.now(UTC)
        stale_run_ids = []
        for run_id, status_data in list(self.run_status.items()):
            # Only consider cleaning up if no client is actively connected
            if run_id not in self.connections:
                status = status_data.get('status', 'unknown')
                timestamp_str = status_data.get('timestamp')
                
                # Check if the run is in a final state and its last update is old
                if timestamp_str and status in ["completed", "failed", "completed_with_errors"]:
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str)
                        if (now - timestamp).total_seconds() > max_age_seconds:
                            stale_run_ids.append(run_id)
                    except ValueError:
                        # If timestamp format is bad, it's stale
                        stale_run_ids.append(run_id)
        
        if stale_run_ids:
            for run_id in stale_run_ids:
                if run_id in self.run_status: # Check again in case it was re-activated
                    del self.run_status[run_id]
            logger.info(f"Cleaned up stale in-memory status for {len(stale_run_ids)} runs.")
File: src/upwork_scraper/infrastructure/init.py
"""
Infrastructure layer for the Upwork Scraper.
Contains concrete implementations (adapters) for repositories, API clients, etc.
"""
File: src/upwork_scraper/init.py
"""
Main Upwork Scraper Application Package.
"""
File: src/upwork_scraper/config.py
"""
Application settings and configuration
"""
from pydantic import Field # Import Field for validation
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from pathlib import Path

class Settings(BaseSettings):
    """Application settings"""

    # MongoDB Configuration
    MONGODB_URI: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "upwork_stable"

    # Scrapfly Configuration
    SCRAPFLY_API_KEY: str = Field(..., min_length=1, description="Scrapfly API key(s), comma-separated if multiple.")
    SCRAPFLY_API_URL: str = "https://api.scrapfly.io/scrape"
    SCRAPFLY_PROXY_POOLS: List[str] = ["public_datacenter_pool"]
    SCRAPFLY_COUNTRY: str = "us" # Default country for scraping (ISO 3166-1 alpha-2 code)
    SCRAPFLY_TIMEOUT: int = 155000 # Milliseconds, Scrapfly API default is 155 seconds
    SCRAPFLY_RENDERING_WAIT: int = 3000 # Milliseconds, wait time after page load for JS rendering

    # API Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False # Secure default: False. Enable debug mode for FastAPI. SHOULD BE FALSE IN PRODUCTION.

    # CORS Configuration
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Paths (relative to BASE_DIR, which is src/upwork_scraper)
    BASE_DIR: Path = Path(__file__).resolve().parent
    CACHE_DIR: Path = BASE_DIR / "cache"
    LOG_DIR: Path = BASE_DIR / "logs"

    # Caching
    ENABLE_CACHE: bool = True # Global toggle for Scrapfly client-side caching
    CACHE_EXPIRY_MINUTES: int = 1440 # Cache expiry in minutes (24 hours)

    # Logging
    LOG_LEVEL: str = "INFO" # Default logging level

    # SSE Configuration
    SSE_HEARTBEAT_INTERVAL: int = 30 # Seconds between SSE heartbeats
    SSE_RETRY_TIMEOUT: int = 3000 # Milliseconds, client reconnection timeout
    SSE_STATUS_CLEANUP_INTERVAL_SECONDS: int = 3600 # How often to cleanup stale SSE run_status in memory

    # Scraping Configuration
    MAX_RETRIES: int = 3 # Max retries for a single Scrapfly fetch attempt (after initial failure)
    RETRY_DELAY: int = 2 # Seconds, delay between retries
    MAX_CONCURRENT_REQUESTS: int = 5 # Max concurrent HTTP requests/tasks in scraping services

    # Upwork Specifics
    UPWORK_BASE_URL: str = "https://www.upwork.com"
    UPWORK_SEARCH_PAGE_JOB_COUNT: int = 50 # Expected number of jobs per page on Upwork search results

    # MongoDB Collection Names
    COLLECTION_JOBS: str = "jobs"
    COLLECTION_CLIENTS: str = "clients"
    COLLECTION_SKILLS: str = "skills"
    COLLECTION_SEARCH_URLS: str = "search_urls"
    COLLECTION_SCRAPE_RUNS: str = "scrape_runs"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False) # Changed to case_sensitive=False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories if they don't exist
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.LOG_DIR.mkdir(parents=True, exist_ok=True)

# Create settings instance
settings = Settings()
File: upwork_extractor/models/init.py
"""
Data models for Upwork job extraction.
Provides Pydantic models with strict validation for all extracted data.
"""

# Alphabetically sorted exports for better readability and maintainability
from .activity import ActivityMetrics, ProposalRange
from .client import ClientInfo, ClientStats, Company, Location
from .enums import BudgetType, DataSource, ExperienceLevel, ProjectType, SkillCategory
from .job import (
    Annotations,
    Budget,
    Category,
    JobDetails,
    JobSlug,
    Qualifications,
    UpworkJobData,
)
from .quality import DataQuality, SchemaOrgMismatch, ValidationIssue
from .skills import Skill, SkillGroup, SkillOntology

__all__ = [
    # Activity Models
    "ActivityMetrics",
    "ProposalRange",
    # Client Models
    "ClientInfo",
    "ClientStats",
    "Company",
    "Location",
    # Enums
    "BudgetType",
    "DataSource",
    "ExperienceLevel",
    "ProjectType",
    "SkillCategory",
    # Job Models
    "Annotations",
    "Budget",
    "Category",
    "JobDetails",
    "JobSlug",
    "Qualifications",
    "UpworkJobData",
    # Quality Models
    "DataQuality",
    "SchemaOrgMismatch",
    "ValidationIssue",
    # Skill Models
    "Skill",
    "SkillGroup",
    "SkillOntology",
]
File: upwork_extractor/models/activity.py
"""
Job activity metrics models.
"""

from typing import Optional
from pydantic import BaseModel, Field


class ProposalRange(BaseModel):
    """Range for proposal counts."""
    
    min: Optional[float] = Field(None, description="Minimum proposals")
    max: Optional[float] = Field(None, description="Maximum proposals")
    
    # Removed custom validator as text_utils now returns None instead of float('inf')


class ActivityMetrics(BaseModel):
    """
    Job posting activity metrics.
    
    Tracks proposals, interviews, invites, and client activity.
    """
    
    proposals: Optional[ProposalRange] = Field(None, description="Proposal count range")
    proposals_text: Optional[str] = Field(None, description="Original proposals text (e.g., '10 to 15')")
    
    interviewing: Optional[int] = Field(None, description="Number of freelancers interviewing")
    invites_sent: Optional[int] = Field(None, description="Number of invites sent by client")
    unanswered_invites: Optional[int] = Field(None, description="Number of unanswered invites")
    
    total_hired: Optional[int] = Field(None, description="Total hired from this job")
    last_buyer_activity: Optional[str] = Field(None, description="Last activity timestamp (ISO 8601 UTC)")
    last_buyer_activity_raw: Optional[str] = Field(None, description="Raw last activity text")
    
    last_viewed: Optional[str] = Field(None, description="Last viewed timestamp or relative time")
File: upwork_extractor/models/client.py
"""
Client/buyer information models.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime


class Location(BaseModel):
    """Client's geographical location."""
    
    country: Optional[str] = Field(None, description="Country name")
    city: Optional[str] = Field(None, description="City name")
    timezone: Optional[str] = Field(None, description="Timezone string (e.g., 'America/Chicago')")
    timezone_offset_ms: Optional[int] = Field(None, description="Timezone offset from UTC in milliseconds")
    local_time: Optional[str] = Field(None, description="Local time string from HTML")


class Company(BaseModel):
    """Client's company information."""
    
    name: Optional[str] = Field(None, description="Company name")
    industry: Optional[str] = Field(None, description="Industry sector")
    size: Optional[str] = Field(None, description="Company size")
    contract_date: Optional[str] = Field(None, description="Upwork member since date (ISO 8601 UTC)")
    contract_date_raw: Optional[str] = Field(None, description="Raw date string")


class ClientStats(BaseModel):
    """Detailed statistics about client's activity on Upwork."""
    
    total_spent: Optional[float] = Field(None, description="Total amount spent on Upwork")
    total_hires: Optional[int] = Field(None, description="Total number of hires")
    active_hires: Optional[int] = Field(None, description="Currently active contracts")
    total_assignments: Optional[int] = Field(None, description="Total contracts ever created")
    hours_count: Optional[int] = Field(None, description="Total hours tracked")
    feedback_count: Optional[int] = Field(None, description="Number of reviews given")
    client_score: Optional[float] = Field(None, description="Client rating (0-5)")
    jobs_posted_count: Optional[int] = Field(None, description="Total jobs posted")
    jobs_open_count: Optional[int] = Field(None, description="Currently open jobs")
    avg_hourly_rate: Optional[float] = Field(None, description="Average hourly rate paid")


class ClientInfo(BaseModel):
    """
    Comprehensive client/buyer information.
    
    Combines location, company, and statistics into unified model.
    """
    
    location: Location = Field(default_factory=Location)
    company: Company = Field(default_factory=Company)
    stats: ClientStats = Field(default_factory=ClientStats)
    
    payment_verified: bool = Field(False, description="Payment method verification status")
    
    # Legacy flat fields for backward compatibility
    member_since: Optional[str] = Field(None, description="Member since date (ISO 8601 UTC)")
    member_since_raw: Optional[str] = Field(None, description="Raw member since text")
    
    # Other jobs by this client (summary data from NUXT / HTML)
    open_jobs: List[Dict[str, Any]] = Field(default_factory=list, description="Other open jobs by this client (summary data)")
    
    @validator('member_since')
    @classmethod
    def validate_member_since_iso(cls, v: Optional[str]) -> Optional[str]:
        """Validates ISO 8601 format for member_since."""
        if not v:
            return None
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00') if v.endswith('Z') else v)
            return v
        except ValueError as e:
            # Log the error but don't raise if this is just a warning in permissive mode
            # This validator is part of the extractor, which has its own config for validation level.
            # So, it's fine to raise here, and the extractor's main logic will catch it.
            raise ValueError(f"Invalid ISO 8601 datetime for member_since: {v}") from e
File: upwork_extractor/models/enums.py
"""
Enumeration types used throughout the extraction system.
"""

from enum import Enum
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ExperienceLevel(str, Enum):
    """Freelancer experience level required for the job."""
    
    ENTRY = "entry"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"
    
    @classmethod
    def from_tier(cls, tier: Optional[int]) -> Optional['ExperienceLevel']:
        """
        Maps Upwork's integer tier (1-3) to experience level.
        
        Args:
            tier: Integer tier from NUXT data (1=entry, 2=intermediate, 3=expert)
            
        Returns:
            ExperienceLevel enum or None if tier is invalid
        """
        mapping = {1: cls.ENTRY, 2: cls.INTERMEDIATE, 3: cls.EXPERT}
        result = mapping.get(tier)
        
        if tier is not None and result is None:
            logger.warning(f"Unknown experience tier: {tier}")
        
        return result
    
    @classmethod
    def from_text(cls, text: Optional[str]) -> Optional['ExperienceLevel']:
        """Maps text description to experience level."""
        if not text:
            return None
        
        text_lower = text.lower()
        if 'entry' in text_lower or 'beginner' in text_lower:
            return cls.ENTRY
        elif 'intermediate' in text_lower or 'moderate' in text_lower:
            return cls.INTERMEDIATE
        elif 'expert' in text_lower or 'advanced' in text_lower:
            return cls.EXPERT
        
        return None


class DataSource(str, Enum):
    """Indicates the primary source(s) from which data was extracted."""
    
    NUXT_DATA = "nuxt_data"
    HTML_ELEMENTS = "html_elements"
    SCHEMA_ORG = "schema_org"
    HYBRID = "hybrid" # Combination of NUXT and HTML
    SEARCH_PAGE_SUMMARY = "search_page_summary" # For initial job discovery from search results


class SkillCategory(str, Enum):
    """Categorizes different types of skills and requirements."""
    
    MANDATORY = "mandatory"
    NICE_TO_HAVE = "nice_to_have"
    TOOL = "tool"
    DELIVERABLE = "deliverable"
    OTHER = "other"
    
    # Categories seen in NUXT 'relevance' field
    ATTRIBUTE = "attribute"
    ONTOLOGY = "ontology"
    FREE_TEXT = "free_text"
    SEARCH_HIGHLIGHT = "search_highlight" # Added for skills directly from search highlights
    
    @classmethod
    def from_relevance(cls, relevance: Optional[str]) -> 'SkillCategory':
        """Maps NUXT relevance string to category."""
        if not relevance:
            return cls.OTHER
        
        relevance_lower = relevance.lower()
        if 'mandatory' in relevance_lower or 'required' in relevance_lower:
            return cls.MANDATORY
        elif 'nice' in relevance_lower or 'preferred' in relevance_lower:
            return cls.NICE_TO_HAVE
        elif 'tool' in relevance_lower:
            return cls.TOOL
        elif 'attribute' in relevance_lower:
            return cls.ATTRIBUTE
        elif 'ontology' in relevance_lower:
            return cls.ONTOLOGY
        elif 'free_text' in relevance_lower:
            return cls.FREE_TEXT
        elif 'highlighted' in relevance_lower: # From search results
            return cls.SEARCH_HIGHLIGHT
        
        return cls.OTHER


class ProjectType(str, Enum):
    """Type of project engagement."""
    
    ONE_TIME = "one_time"
    ONGOING = "ongoing"
    CONTRACT_TO_HIRE = "contract_to_hire"
    
    @classmethod
    def from_nuxt_type(cls, nuxt_type: Optional[str]) -> Optional['ProjectType']:
        """Maps NUXT type string to ProjectType enum."""
        if not nuxt_type:
            return None
        
        mapping = {
            'EMPLOYMENT_PROJECT': cls.ONE_TIME,
            'CONTRACTOR': cls.ONGOING,
            'TEMPORARY': cls.ONE_TIME,
            'EMPLOYMENT_ONGOING': cls.ONGOING,
            'CONTRACT_TO_HIRE': cls.CONTRACT_TO_HIRE,
            'DIRECT': cls.ONE_TIME,
            'EMPLOYMENT': cls.ONGOING, # Upwork sometimes treats "EMPLOYMENT" as ongoing
            'HOURLY': cls.ONGOING, # Added based on context of `type` from search results for hourly
            'FIXED': cls.ONE_TIME, # Added based on context of `type` from search results for fixed
        }
        
        result = mapping.get(nuxt_type)
        if result is None:
            logger.warning(f"Unknown NUXT project type: {nuxt_type}")
        
        return result


class BudgetType(str, Enum):
    """Budget configuration type."""
    
    MANUAL = "manual"
    DEFAULT = "default"
    SKIP = "skip"
    HOURLY = "hourly"
    FIXED = "fixed"
    NOT_PROVIDED = "not_provided" # Explicitly for cases where no budget is given
File: upwork_extractor/models/job.py
"""
Main job posting models.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field, HttpUrl, validator, root_validator
from .enums import ExperienceLevel, DataSource, ProjectType, BudgetType
from .skills import Skill, SkillOntology
from .client import ClientInfo
from .activity import ActivityMetrics
from ..utils.validation import validate_uid


class Budget(BaseModel):
    """Job budget details including fixed amount and hourly rate range."""
    
    amount: Optional[float] = Field(None, description="Fixed budget amount")
    currency_code: Optional[str] = Field(None, min_length=3, max_length=3, description="ISO currency code")
    
    hourly_min: Optional[float] = Field(None, description="Minimum hourly rate")
    hourly_max: Optional[float] = Field(None, description="Maximum hourly rate")
    
    budget_type: Optional[BudgetType] = Field(None, description="Budget configuration type")
    weekly_retainer: Optional[float] = Field(None, description="Weekly retainer amount")
    
    @root_validator(skip_on_failure=True)
    @classmethod
    def validate_hourly_range(cls, values):
        """Ensures hourly_min <= hourly_max."""
        min_val = values.get('hourly_min')
        max_val = values.get('hourly_max')
        
        # Only swap if both exist and min > max
        if min_val is not None and max_val is not None and min_val > max_val:
            values['hourly_min'], values['hourly_max'] = max_val, min_val
        
        return values
    
    class Config:
        use_enum_values = True


class Category(BaseModel):
    """Job category classification."""
    
    name: Optional[str] = Field(None, description="Category name")
    url_slug: Optional[str] = Field(None, description="URL slug for category")
    group_name: Optional[str] = Field(None, description="Parent category group")
    group_url_slug: Optional[str] = Field(None, description="Parent group URL slug")


class Qualifications(BaseModel):
    """Freelancer qualifications and requirements."""
    
    min_hours_week: Optional[int] = Field(None, description="Minimum hours per week")
    location_check_required: bool = Field(False, description="Whether location check is required")
    preferred_english_skill: Optional[int] = Field(None, description="Preferred English proficiency level (0-5)")
    rising_talent_only: bool = Field(False, description="Only accept Rising Talent")
    should_have_portfolio: bool = Field(False, description="Portfolio required")
    local_market: bool = Field(False, description="Local market preference")
    allowed_countries: Optional[List[str]] = Field(None, description="List of allowed countries for the job")
    languages_required: Optional[List[Dict[str, Any]]] = Field(None, description="Required languages and proficiency levels")


class Annotations(BaseModel):
    """Job posting annotations and metadata from posting flow."""
    
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="Custom posting fields")
    tags: List[str] = Field(default_factory=list, description="Job tags")
    site_source: Optional[str] = Field(None, description="Source site (e.g., 'desktop_rjp')")
    sourcing_update_count: Optional[int] = Field(None, description="Number of sourcing updates")
    sourcing_update_forbidden: bool = Field(False, description="Whether sourcing updates are forbidden")
    job_type_code: Optional[str] = Field(None, description="Internal job type code")
    original_prompt: Optional[str] = Field(None, description="Original client text before AI enhancement")
    browser: Optional[str] = Field(None, description="Browser used for posting")
    device: Optional[str] = Field(None, description="Device used for posting")
    flow_type: Optional[str] = Field(None, description="Posting flow type")


class JobSlug(BaseModel):
    """Canonical job slug information."""
    
    id: Optional[str] = Field(None, description="Slug ID")
    type: Optional[str] = Field(None, description="Slug type")
    name: Optional[str] = Field(None, description="Display name")
    slug: Optional[str] = Field(None, description="URL slug")
    modifier: Optional[str] = Field(None, description="Slug modifier")


class JobDetails(BaseModel):
    """Detailed job posting attributes."""
    
    experience_level: Optional[ExperienceLevel] = Field(None, description="Required experience level")
    duration: Optional[str] = Field(None, description="Project duration (e.g., '1-3 months')")
    duration_weeks: Optional[int] = Field(None, description="Duration in weeks")
    workload: Optional[str] = Field(None, description="Expected workload (e.g., 'Less than 30 hrs/week')")
    project_type: Optional[ProjectType] = Field(None, description="Project type")
    
    budget: Budget = Field(default_factory=Budget, description="Budget information")
    
    posted_date: Optional[str] = Field(None, description="Posted date (ISO 8601 UTC)")
    posted_date_raw: Optional[str] = Field(None, description="Raw posted date text")
    
    created_date: Optional[str] = Field(None, description="Created date (ISO 8601 UTC)")
    created_date_raw: Optional[str] = Field(None, description="Raw created date")
    
    start_date: Optional[str] = Field(None, description="Project start date")
    delivery_date: Optional[str] = Field(None, description="Expected delivery date")
    deadline: Optional[str] = Field(None, description="Application deadline")
    
    remote_job: bool = Field(False, description="Remote work allowed")
    
    category: Optional[Category] = Field(None, description="Job category")
    # Removed Optional from these fields as they have default_factory
    qualifications: Qualifications = Field(default_factory=Qualifications, description="Freelancer qualifications") 
    annotations: Annotations = Field(default_factory=Annotations, description="Job annotations and metadata")
    job_slug: JobSlug = Field(default_factory=JobSlug, description="Canonical slug information")
    
    # Additional metadata
    was_renewed: bool = Field(False, description="Whether job was renewed")
    hide_budget: bool = Field(False, description="Whether client hid budget")
    number_of_positions: Optional[int] = Field(None, description="Number of positions to hire")
    is_contract_to_hire: bool = Field(False, description="Contract-to-hire opportunity")
    not_sure_duration: bool = Field(False, description="Client uncertain about duration")
    not_sure_experience_level: bool = Field(False, description="Client uncertain about experience level")
    not_sure_freelancers_to_hire: bool = Field(False, description="Client uncertain about number to hire")
    
    @validator('posted_date', 'created_date', pre=True)
    @classmethod
    def validate_iso_date(cls, v: Optional[str]) -> Optional[str]:
        """Validates ISO 8601 datetime format."""
        if not v:
            return None
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00') if v.endswith('Z') else v)
            return v
        except ValueError as e:
            raise ValueError(f"Invalid ISO 8601 datetime: {v}") from e
    
    class Config:
        use_enum_values = True


class UpworkJobData(BaseModel):
    """
    Main model representing a complete Upwork job posting.
    
    Combines all extracted data with quality tracking and metadata.
    Optimized for database storage with normalized structure.
    """
    
    # Core fields (CRITICAL - must exist)
    title: str = Field(..., description="Job title")
    description: str = Field(..., description="Job description")
    
    # Identifiers
    uid: Optional[str] = Field(None, description="Unique job ID (e.g., ~021989059411821975576)")
    ciphertext: Optional[str] = Field(None, description="Encrypted job identifier")
    url: Optional[HttpUrl] = Field(None, description="Job posting URL")
    
    # Status
    status: Optional[int] = Field(None, description="Job status code")
    access: Optional[int] = Field(None, description="Access level code")
    
    # Nested details
    job_details: JobDetails = Field(default_factory=JobDetails, description="Detailed job attributes")
    
    # Skills (both flat and hierarchical)
    skills: List[Skill] = Field(default_factory=list, description="Flat list of all skills")
    deliverables: List[str] = Field(default_factory=list, description="Explicit deliverables from client")
    skill_ontology: Optional[SkillOntology] = Field(default_factory=SkillOntology, description="Hierarchical skills ontology")
    
    # Client & Activity
    client: ClientInfo = Field(default_factory=ClientInfo, description="Client information")
    activity: ActivityMetrics = Field(default_factory=ActivityMetrics, description="Job activity metrics")
    
    # Related jobs
    other_jobs_by_client: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Other open jobs by this client (excluding current) - summary dicts"
    )
    similar_jobs: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Similar job postings - summary dicts"
    )
    
    # Metadata
    data_source: DataSource = Field(..., description="Primary data source")
    data_quality: Optional[Dict[str, Any]] = Field(None, description="Data quality report")
    
    extracted_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec='seconds') + 'Z',
        description="Extraction timestamp (ISO 8601 UTC)"
    )
    
    @validator('uid')
    @classmethod
    def validate_uid_format_custom(cls, v: Optional[str]) -> Optional[str]:
        """Validates Upwork UID format (~021989059411821975576) using `utils.validation.validate_uid`."""
        if v:
            # `validate_uid` will raise ValueError if invalid in strict mode
            validate_uid(v, strict=True)
        return v
    

    
    class Config:
        use_enum_values = True
        arbitrary_types_allowed = True
        validate_assignment = True
    
    # Removed to_normalized_dict method as per architectural audit
File: upwork_extractor/models/quality.py
"""
Data quality tracking and validation models.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone


@dataclass
class ValidationIssue:
    """Represents a single validation issue encountered during extraction."""
    
    field_name: str
    value: Any
    reason: str
    severity: str  # 'error', 'warning', 'info'
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec='seconds') + 'Z')
    
    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.field_name}: {self.reason} (value: {self.value})"


@dataclass
class SchemaOrgMismatch:
    """Represents a mismatch between Schema.org and extracted data."""
    
    field_name: str
    schema_value: Any
    extracted_value: Any
    source: str  # 'nuxt' or 'html'
    
    def __str__(self) -> str:
        return (
            f"Schema.org mismatch in '{self.field_name}': "
            f"Schema={self.schema_value}, {self.source}={self.extracted_value}"
        )


@dataclass
class DataQuality:
    """
    Comprehensive data quality tracking for extraction process.
    
    Tracks warnings, validation issues, source coverage, and schema mismatches.
    Provides methods to add issues and generate quality reports.
    """
    
    # Correctly uses default_factory for mutable defaults
    warnings: List[str] = field(default_factory=list)
    validation_issues: List[ValidationIssue] = field(default_factory=list)
    source_coverage: Dict[str, str] = field(default_factory=dict) # Tracks which source (nuxt, html) provided a field
    schema_mismatches: List[SchemaOrgMismatch] = field(default_factory=list)
    extraction_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_warning(self, message: str, field_name: Optional[str] = None):
        """
        Adds a unique warning message.
        
        Args:
            message: Warning message
            field_name: Optional field name for context
        """
        msg = f"[{field_name}] {message}" if field_name else message
        if msg not in self.warnings:
            self.warnings.append(msg)
    
    def add_validation_issue(
        self,
        field_name: str,
        value: Any,
        reason: str,
        severity: str = "warning"
    ):
        """
        Adds a validation issue.
        
        Args:
            field_name: Name of the field with issue
            value: The problematic value
            reason: Description of the issue
            severity: 'error', 'warning', or 'info'
        """
        issue = ValidationIssue(
            field_name=field_name,
            value=str(value) if value is not None else None,
            reason=reason,
            severity=severity
        )
        self.validation_issues.append(issue)
    
    def add_schema_mismatch(
        self,
        field_name: str,
        schema_value: Any,
        extracted_value: Any,
        source: str
    ):
        """
        Records a mismatch between Schema.org and extracted data.
        
        Args:
            field_name: Field with mismatch
            schema_value: Value from Schema.org JSON-LD
            extracted_value: Value from NUXT/HTML extraction
            source: Source of extracted value ('nuxt' or 'html')
        """
        mismatch = SchemaOrgMismatch(
            field_name=field_name,
            schema_value=schema_value,
            extracted_value=extracted_value,
            source=source
        )
        self.schema_mismatches.append(mismatch)
    
    def set_source(self, field_name: str, source: str):
        """Records which source provided a specific field."""
        self.source_coverage[field_name] = source
    
    def has_errors(self) -> bool:
        """Returns True if any validation issues have 'error' severity."""
        return any(issue.severity == 'error' for issue in self.validation_issues)
    
    def has_warnings(self) -> bool:
        """Returns True if there are any warnings or warning-level issues."""
        return len(self.warnings) > 0 or any(
            issue.severity == 'warning' for issue in self.validation_issues
        )
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Generates a summary of data quality metrics.
        
        Returns:
            Dictionary with quality statistics
        """
        return {
            'total_warnings': len(self.warnings),
            'total_validation_issues': len(self.validation_issues),
            'error_count': sum(1 for i in self.validation_issues if i.severity == 'error'),
            'warning_count': sum(1 for i in self.validation_issues if i.severity == 'warning'),
            'schema_mismatches': len(self.schema_mismatches),
            'fields_extracted': len(self.source_coverage),
            'has_errors': self.has_errors(),
            'has_warnings': self.has_warnings(),
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Converts DataQuality to dictionary for serialization."""
        return {
            'warnings': self.warnings,
            'validation_issues': [
                {
                    'field_name': issue.field_name,
                    'value': issue.value,
                    'reason': issue.reason,
                    'severity': issue.severity,
                    'timestamp': issue.timestamp,
                }
                for issue in self.validation_issues
            ],
            'source_coverage': self.source_coverage,
            'schema_mismatches': [
                {
                    'field_name': mismatch.field_name,
                    'schema_value': mismatch.schema_value,
                    'extracted_value': mismatch.extracted_value,
                    'source': mismatch.source,
                }
                for mismatch in self.schema_mismatches
            ],
            'extraction_metadata': self.extraction_metadata,
            'summary': self.get_summary(),
        }
File: upwork_extractor/models/skills.py
"""
Skills and ontology models.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, validator
from .enums import SkillCategory


class Skill(BaseModel):
    """
    Represents a single skill with category and optional metadata.
    
    Stored in flat list for easy searching while maintaining hierarchy reference.
    """
    
    name: str = Field(..., description="Skill name")
    category: Optional[SkillCategory] = Field(None, description="Skill category/relevance")
    uid: Optional[str] = Field(None, description="Upwork skill UID")
    parent_group: Optional[str] = Field(None, description="Name of the parent skill group if hierarchical")
    ontology_id: Optional[str] = Field(None, description="Ontology identifier (could be different from UID)")
    
    @validator('name')
    @classmethod
    def clean_name(cls, v: str) -> str:
        """Validates and cleans skill name."""
        if not v or not v.strip():
            raise ValueError("Skill name cannot be empty")
        return v.strip()
    
    class Config:
        use_enum_values = True


class SkillGroup(BaseModel):
    """
    Represents a hierarchical skill group (e.g., 'Web Design Skills').
    
    Used to preserve parent-child relationships from ontology data.
    """
    
    name: str = Field(..., description="Group name")
    group_id: Optional[str] = Field(None, description="Internal group ID")
    uid: Optional[str] = Field(None, description="Upwork UID for the group")
    skills: List[Skill] = Field(default_factory=list, description="Skills in this group")
    
    class Config:
        use_enum_values = True


class SkillOntology(BaseModel):
    """
    Complete skills ontology data from NUXT 'sands' object.
    
    Preserves both flat skill list and hierarchical structure.
    """
    
    occupation_id: Optional[str] = Field(None, description="Occupation ontology ID")
    occupation_name: Optional[str] = Field(None, description="Occupation name")
    occupation_uid: Optional[str] = Field(None, description="Occupation UID")
    
    skill_groups: List[SkillGroup] = Field(
        default_factory=list,
        description="Hierarchical skill groups"
    )
    
    additional_skills: List[Skill] = Field(
        default_factory=list,
        description="Additional skills not in groups"
    )
    
    class Config:
        use_enum_values = True
File: upwork_extractor/parsers/init.py
"""
Parser modules for different data sources.

Organized parsers:
- nuxt_parser: Extracts data from __NUXT_DATA__ JSON
- html_parser: Extracts data from HTML elements
- schema_parser: Extracts and validates Schema.org JSON-LD
"""

from .html_parser import HtmlParser
from .nuxt_parser import NuxtParser
from .schema_parser import SchemaParser

__all__ = [
    "NuxtParser",
    "HtmlParser",
    "SchemaParser",
]
File: upwork_extractor/parsers/html_parser.py
"""
HTML parser with robust selectors.

Extracts job data from HTML elements as fallback or enrichment for NUXT data.
Uses semantic selectors and data attributes for stability.
[Tech Debt] This HTML parser is inherently brittle and dependent on Upwork's current
HTML structure. It should be treated as a fallback/enrichment source and
requires constant monitoring and maintenance. Data should be prioritized from NUXT.
"""

import re
import logging
from typing import Optional, List, Dict, Any
from bs4 import BeautifulSoup, Tag

from ..models import (
    UpworkJobData,
    ExperienceLevel,
    Skill,
    SkillCategory,
    ProposalRange,
    ProjectType, # Added ProjectType
)
from ..models.quality import DataQuality
from ..utils.text_utils import get_text_safe, clean_number, parse_proposals_text, normalize_whitespace
from ..utils.date_utils import parse_date_flexible
from .selectors import (
    HTML_JOB_TITLE_SELECTORS,
    HTML_JOB_DESCRIPTION_SELECTORS,
    DELIVERABLES_LIST_SELECTOR,
    HTML_FEATURES_LIST_SELECTORS,
    PATTERN_EXPERIENCE_LEVEL,
    PATTERN_DURATION,
    PATTERN_HOURLY,
    REMOTE_JOB_PATTERNS,
    HTML_POSTED_DATE_SELECTORS,
    HTML_SKILLS_SECTION_SELECTOR,
    HTML_SKILL_BADGE_PATTERN,
    HTML_CLIENT_SECTION_SELECTORS,
    HTML_CLIENT_LOCATION_SELECTOR,
    HTML_CLIENT_SPEND_SELECTOR,
    HTML_CLIENT_HIRES_SELECTOR,
    PATTERN_HIRES,
    HTML_CLIENT_CONTRACT_DATE_SELECTORS,
    PATTERN_MEMBER_SINCE,
    HTML_CLIENT_COMPANY_SELECTOR,
    HTML_ACTIVITY_ITEM_SELECTORS,
    PATTERN_PROPOSALS,
    PATTERN_INTERVIEWING,
    PATTERN_INVITES_SENT,
    PATTERN_UNANSWERED,
    HTML_OTHER_JOBS_LIST_SELECTOR,
    HTML_SIMILAR_JOBS_SELECTORS,
    META_URL_SELECTORS,
)

logger = logging.getLogger(__name__)


class HtmlParser:
    """
    Parses HTML elements for job data extraction.
    
    Serves as fallback when NUXT data is unavailable and enrichment source
    for fields that HTML provides more detail on.
    """
    
    def __init__(self, soup: BeautifulSoup, data_quality: DataQuality):
        """
        Initialize HTML parser.
        
        Args:
            soup: BeautifulSoup instance of HTML
            data_quality: DataQuality tracker
        """
        self.soup = soup
        self.data_quality = data_quality
        
        # Cache frequently accessed elements (not strictly needed with specific selectors, but good practice)
        self._cache: Dict[str, Any] = {}
    
    def _find_first_element(self, selectors: List[Dict]) -> Optional[Tag]:
        """Helper to find the first element matching any of the provided selectors."""
        for selector in selectors:
            elem = self.soup.find(**selector)
            if elem:
                return elem
        return None
    
    def populate_job_data(self, data: UpworkJobData):
        """
        Populates UpworkJobData from HTML elements.
        
        Only populates fields that are empty (NUXT takes priority).
        """
        # Core job info
        self._populate_title(data)
        self._populate_url(data)
        self._populate_description(data)
        
        # Job details
        self._populate_features(data)
        self._populate_posted_date(data)
        
        # Skills
        self._populate_skills(data)
        
        # Client info
        self._populate_client(data)
        
        # Activity
        self._populate_activity(data)
        
        # Related jobs
        self._populate_other_jobs(data)
        self._populate_similar_jobs(data)
    
    def _populate_title(self, data: UpworkJobData):
        """Extracts job title from HTML."""
        if data.title and data.title.strip():
            return  # Already have title from NUXT or other source

        elem = self._find_first_element(HTML_JOB_TITLE_SELECTORS)
        if elem:
            text = normalize_whitespace(get_text_safe(elem))
            if text:
                data.title = text
                self.data_quality.set_source('title', 'html')
                logger.debug(f"Extracted title from HTML: '{text}'")
                return
        
        self.data_quality.add_warning("Job title not found in HTML", 'title')
    
    def _populate_url(self, data: UpworkJobData):
        """Extracts job URL from meta tags."""
        if data.url:
            return
        
        for selector in META_URL_SELECTORS:
            elem = self.soup.find(**selector)
            if elem:
                url = elem.get('content') or elem.get('href')
                if url:
                    data.url = url
                    self.data_quality.set_source('url', 'html')
                    return
    
    def _populate_description(self, data: UpworkJobData):
        """Extracts description and deliverables."""
        current_description = data.description
        
        desc_section = self._find_first_element(HTML_JOB_DESCRIPTION_SELECTORS)
        if desc_section:
            # Check for a "Read more" button / truncated description
            full_desc_div = desc_section.find('div', {'class': 'up-expandable-text-content'})
            if full_desc_div:
                description = get_text_safe(full_desc_div)
            else:
                description = get_text_safe(desc_section)
            
            description = normalize_whitespace(description)

            if description and (not current_description or len(description) > len(current_description)):
                data.description = description
                self.data_quality.set_source('description', 'html')
                current_description = description # Update for subsequent checks
            
            # Always try to extract deliverables regardless of description source
            self._extract_deliverables_from_section(desc_section, data)
            
            if data.description: # If description was found via HTML, we're done here
                return
        
        if not data.description:
            self.data_quality.add_warning("Job description not found in HTML", 'description')
    
    def _extract_deliverables_from_section(self, section: Tag, data: UpworkJobData) -> List[str]:
        """Extracts deliverables from description section."""
        deliverables_ul = section.find(**DELIVERABLES_LIST_SELECTOR)
        if not deliverables_ul:
            return []
        
        deliverables = []
        for li in deliverables_ul.find_all('li'):
            text = normalize_whitespace(get_text_safe(li))
            if text and text not in data.deliverables: # Avoid duplicates
                deliverables.append(text)
                # Add as skill with DELIVERABLE category
                if text.lower() not in {s.name.lower() for s in data.skills}:
                    data.skills.append(Skill(name=text, category=SkillCategory.DELIVERABLE))
        
        if deliverables:
            data.deliverables.extend(deliverables)
            self.data_quality.set_source('deliverables', 'html')
        
        return deliverables
    
    def _populate_features(self, data: UpworkJobData):
        """Extracts job features (experience, duration, budget, etc.)."""
        features_section = self._find_first_element(HTML_FEATURES_LIST_SELECTORS)
        if not features_section:
            self.data_quality.add_warning("Features section not found in HTML", 'features')
            return
        
        for item_li in features_section.find_all('li'):
            value_elem = item_li.find('strong')
            if not value_elem:
                continue
            
            value_text = normalize_whitespace(get_text_safe(value_elem))
            
            # Get description/label
            desc_elem = item_li.find('div', {'class': 'description'}) or item_li.find('small')
            label_text = normalize_whitespace(get_text_safe(desc_elem)).lower() if desc_elem else ""
            
            # Experience level
            if not data.job_details.experience_level and PATTERN_EXPERIENCE_LEVEL.search(label_text):
                level = ExperienceLevel.from_text(value_text)
                if level:
                    data.job_details.experience_level = level
                    self.data_quality.set_source('experience_level', 'html')
            
            # Duration
            if not data.job_details.duration and PATTERN_DURATION.search(label_text):
                data.job_details.duration = value_text
                self.data_quality.set_source('duration', 'html')
            
            # Workload
            # Look for "Hours per week" or similar labels
            if not data.job_details.workload and (PATTERN_HOURLY.search(value_text) or 'hrs/week' in label_text):
                data.job_details.workload = value_text
                self.data_quality.set_source('workload', 'html')
            
            # Hourly rate (only if not already set by NUXT)
            if data.job_details.budget.hourly_min is None and '$' in value_text: # Simple check for currency symbol
                amounts_raw = [s.get_text(strip=True) for s in item_li.find_all('strong') if '$' in s.get_text(strip=True)]
                amounts = [clean_number(ar) for ar in amounts_raw if clean_number(ar) is not None]
                
                if len(amounts) >= 2:
                    data.job_details.budget.hourly_min = amounts[0]
                    data.job_details.budget.hourly_max = amounts[1]
                    self.data_quality.set_source('hourly_rate', 'html')
                elif len(amounts) == 1:
                    data.job_details.budget.hourly_min = amounts[0]
                    data.job_details.budget.hourly_max = amounts[0]
                    self.data_quality.set_source('hourly_rate', 'html')
            
            # Remote job indicator
            if not data.job_details.remote_job:
                for pattern in REMOTE_JOB_PATTERNS:
                    if pattern.search(value_text):
                        data.job_details.remote_job = True
                        self.data_quality.set_source('remote_job', 'html')
                        break
            
            # Project type from text
            if not data.job_details.project_type:
                value_lower = value_text.lower()
                if 'one-time project' in value_lower:
                    data.job_details.project_type = ProjectType.ONE_TIME
                    self.data_quality.set_source('project_type', 'html')
                elif 'long-term project' in value_lower or 'ongoing project' in value_lower:
                    data.job_details.project_type = ProjectType.ONGOING
                    self.data_quality.set_source('project_type', 'html')
    
    def _populate_posted_date(self, data: UpworkJobData):
        """Extracts posted date."""
        if data.job_details.posted_date:
            return
        
        posted_elem = self._find_first_element(HTML_POSTED_DATE_SELECTORS)
        if posted_elem:
            text = normalize_whitespace(get_text_safe(posted_elem))
            text = re.sub(r'posted\s+', '', text, flags=re.I).strip()
            
            iso_date, raw_text = parse_date_flexible(text)
            data.job_details.posted_date = iso_date
            data.job_details.posted_date_raw = raw_text or text
            if iso_date:
                self.data_quality.set_source('posted_date', 'html')
            else:
                self.data_quality.add_warning(f"Could not parse HTML posted date: '{text}'", 'posted_date')
    
    def _populate_skills(self, data: UpworkJobData):
        """Extracts skills with categorization."""
        skills_section = self._find_first_element([HTML_SKILLS_SECTION_SELECTOR])
        if not skills_section:
            return
        
        seen_names = {s.name.lower() for s in data.skills}
        skills_to_add = []
        
        # Find skill groups (e.g., "Skills and Expertise", "Optional Skills")
        for group_div in skills_section.find_all('div', {'class': 'span-md-12'}):
            header = group_div.find('strong')
            if not header:
                continue
            
            category_text = normalize_whitespace(get_text_safe(header)).lower()
            category = SkillCategory.OTHER
            
            if 'mandatory' in category_text or 'required' in category_text:
                category = SkillCategory.MANDATORY
            elif 'nice-to-have' in category or 'preferred' in category_text:
                category = SkillCategory.NICE_TO_HAVE
            elif 'tool' in category_text:
                category = SkillCategory.TOOL
            
            # Find skills in this group (badges)
            skills_list = group_div.find('div', {'class': 'skills-list'})
            if skills_list:
                for badge in skills_list.find_all(['span', 'div'], class_=HTML_SKILL_BADGE_PATTERN):
                    name = normalize_whitespace(get_text_safe(badge))
                    if name and name.lower() not in seen_names:
                        skills_to_add.append(Skill(name=name, category=category))
                        seen_names.add(name.lower())
        
        if skills_to_add:
            data.skills.extend(skills_to_add)
            self.data_quality.set_source('skills', 'html')
    
    def _populate_client(self, data: UpworkJobData):
        """Extracts client information."""
        client_section = self._find_first_element(HTML_CLIENT_SECTION_SELECTORS)
        if not client_section:
            self.data_quality.add_warning("Client section not found in HTML", 'client')
            return
        
        # Location
        loc_elem = client_section.find(**HTML_CLIENT_LOCATION_SELECTOR)
        if loc_elem:
            country_elem = loc_elem.find('strong')
            if country_elem and not data.client.location.country:
                data.client.location.country = normalize_whitespace(get_text_safe(country_elem))
            
            time_div = loc_elem.find('div', {'class': 'text-body-sm'})
            if time_div:
                nowrap_spans = time_div.find_all('span', {'class': 'nowrap'})
                if nowrap_spans:
                    if len(nowrap_spans) >= 1 and not data.client.location.city:
                        data.client.location.city = normalize_whitespace(get_text_safe(nowrap_spans[0]))
                    if len(nowrap_spans) > 1 and not data.client.location.local_time:
                        data.client.location.local_time = normalize_whitespace(get_text_safe(nowrap_spans[1]))
            
            if data.client.location.country or data.client.location.city:
                self.data_quality.set_source('client_location', 'html')
        
        # Total spent
        spend_elem = client_section.find(**HTML_CLIENT_SPEND_SELECTOR)
        if spend_elem and data.client.stats.total_spent is None:
            text = normalize_whitespace(get_text_safe(spend_elem))
            amount = clean_number(re.sub(r'spent\s*', '', text, flags=re.I))
            if amount is not None:
                data.client.stats.total_spent = amount
                self.data_quality.set_source('client_total_spent', 'html')
        
        # Hires
        hires_elem = client_section.find(**HTML_CLIENT_HIRES_SELECTOR)
        if hires_elem and data.client.stats.total_hires is None:
            text = normalize_whitespace(get_text_safe(hires_elem))
            match = PATTERN_HIRES.search(text)
            if match:
                data.client.stats.total_hires = int(match.group(1))
                if match.group(2):
                    data.client.stats.active_hires = int(match.group(2))
                else:
                    data.client.stats.active_hires = 0
                self.data_quality.set_source('client_hires', 'html')
        
        # Member since
        member_elem = self._find_first_element(HTML_CLIENT_CONTRACT_DATE_SELECTORS)
        if member_elem and not data.client.member_since:
            text = normalize_whitespace(get_text_safe(member_elem))
            text = PATTERN_MEMBER_SINCE.sub('', text).strip()
            
            iso_date, raw_text = parse_date_flexible(text)
            data.client.member_since = iso_date
            data.client.member_since_raw = raw_text or text
            if iso_date:
                self.data_quality.set_source('client_member_since', 'html')
        
        # Company
        company_elem = client_section.find(**HTML_CLIENT_COMPANY_SELECTOR)
        if company_elem and not data.client.company.name:
            data.client.company.name = normalize_whitespace(get_text_safe(company_elem))
            self.data_quality.set_source('client_company', 'html')
    
    def _populate_activity(self, data: UpworkJobData):
        """Extracts activity metrics."""
        activity_items = self._find_first_element(HTML_ACTIVITY_ITEM_SELECTORS) # This should be the parent UL/DIV
        if not activity_items:
            return
        
        # Loop through actual list items within the container
        for item in activity_items.find_all('li', class_=re.compile(r'(?:ca-item|list-item)')):
            title_elem = item.find('strong') or item.find('b')
            value_elem = item.find('span', {'class': 'text-muted'}) or item.find('div')
            
            if not (title_elem and value_elem):
                continue
            
            title_text = normalize_whitespace(get_text_safe(title_elem)).lower()
            value_text = normalize_whitespace(get_text_safe(value_elem))
            
            # Proposals
            if PATTERN_PROPOSALS.search(title_text):
                min_val, max_val, original = parse_proposals_text(value_text)
                if min_val is not None and max_val is not None:
                    # Only override if HTML has a more informative range or NUXT data is missing
                    should_override = (
                        not data.activity.proposals or
                        (data.activity.proposals.min == data.activity.proposals.max and min_val != max_val) # HTML has range, NUXT had exact
                        # Or if HTML range is more precise/different and not infinity
                        or (data.activity.proposals.max is not None and max_val is None) # NUXT had a max, HTML has unbounded
                        or (data.activity.proposals.max is None and max_val is not None) # NUXT had unbounded, HTML has a max
                    )
                    
                    if should_override:
                        data.activity.proposals = ProposalRange(min=min_val, max=max_val)
                        data.activity.proposals_text = original or value_text
                        self.data_quality.set_source('activity_proposals', 'html')
            
            # Interviewing
            elif PATTERN_INTERVIEWING.search(title_text) and data.activity.interviewing is None:
                count = clean_number(value_text)
                if count is not None:
                    data.activity.interviewing = int(count)
                    self.data_quality.set_source('activity_interviewing', 'html')
            
            # Invites sent
            elif PATTERN_INVITES_SENT.search(title_text) and data.activity.invites_sent is None:
                count = clean_number(value_text)
                if count is not None:
                    data.activity.invites_sent = int(count)
                    self.data_quality.set_source('activity_invites_sent', 'html')
            
            # Unanswered invites
            elif PATTERN_UNANSWERED.search(title_text) and data.activity.unanswered_invites is None:
                count = clean_number(value_text)
                if count is not None:
                    data.activity.unanswered_invites = int(count)
                    self.data_quality.set_source('activity_unanswered_invites', 'html')
    
    def _populate_other_jobs(self, data: UpworkJobData):
        """Extracts other jobs by client."""
        if data.other_jobs_by_client:
            return  # Already have from NUXT or set to not extract
        
        other_jobs_list = self._find_first_element([HTML_OTHER_JOBS_LIST_SELECTOR])
        if not other_jobs_list:
            return
        
        current_uid = data.uid.replace('~', '') if data.uid else None # Remove ~ for comparison
        
        for job_item in other_jobs_list.find_all('li'):
            link = job_item.find('a')
            if not link:
                continue
            
            job_url = link.get('href', '')
            job_title = normalize_whitespace(get_text_safe(link))
            
            # Extract UID from URL to check if it's current job
            uid_match = re.search(r'~(\d{19,20})', job_url) # Adjusted UID pattern
            job_uid = uid_match.group(1) if uid_match else None # Get just the digits

            # Check for self-reference
            if job_uid and job_uid == current_uid:
                continue
            
            type_span = job_item.find('span', {'class': 'type'})
            job_type = normalize_whitespace(get_text_safe(type_span)) if type_span else None
            
            data.other_jobs_by_client.append({
                'title': job_title,
                'url': job_url,
                'uid': f"~{job_uid}" if job_uid else None, # Re-add ~ for consistency
                'type': job_type,
            })
        
        if data.other_jobs_by_client:
            self.data_quality.set_source('other_jobs_by_client', 'html')
    
    def _populate_similar_jobs(self, data: UpworkJobData):
        """Extracts similar jobs."""
        if data.similar_jobs:
            return # Already have from NUXT or set to not extract
        
        # Similar jobs are often in cards/sections
        for job_section_selector in HTML_SIMILAR_JOBS_SELECTORS:
            for job_section in self.soup.find_all(**job_section_selector):
                title_link = job_section.find('a', {'data-test': 'job-title'})
                if not title_link:
                    continue
                
                # Extract skills
                skill_badges = job_section.find_all('span', {'class': 'air3-badge'})
                skills = [normalize_whitespace(get_text_safe(badge)) for badge in skill_badges if get_text_safe(badge)]
                
                # Posted date
                posted_elem = job_section.find('small', {'class': 'text-light-on-muted'})
                posted_text = normalize_whitespace(get_text_safe(posted_elem)) if posted_elem else None
                
                # Job type (hourly/fixed) - often in a small tag near budget
                type_elem = job_section.find('small', text=re.compile(r'(Hourly|Fixed-price)', re.IGNORECASE))
                job_type = normalize_whitespace(get_text_safe(type_elem)) if type_elem else None
                
                data.similar_jobs.append({
                    'title': normalize_whitespace(get_text_safe(title_link)),
                    'url': title_link.get('href'),
                    'posted_text': posted_text,
                    'job_type': job_type,
                    'skills': skills,
                })
        
        if data.similar_jobs:
            self.data_quality.set_source('similar_jobs', 'html')
File: upwork_extractor/parsers/nuxt_parser.py
"""
NUXT data parser with complete reference resolution.

Extracts and resolves all data from __NUXT_DATA__ JSON array.
Handles integer references and nested structures properly.
"""

import logging
from typing import Optional, List, Dict, Any
from bs4 import BeautifulSoup
import json

from ..models import (
    UpworkJobData,
    ExperienceLevel,
    Skill,
    SkillCategory,
    SkillOntology,
    SkillGroup,
    ProjectType,
    BudgetType,
    Category,
    Qualifications,
    Annotations,
    JobSlug,
    Location,
    Company,
    ClientStats,
    ProposalRange,
)
from ..models.quality import DataQuality
from ..utils.text_utils import get_nested_safe, clean_number, normalize_whitespace
from ..utils.date_utils import parse_date_flexible, parse_duration_to_weeks
from src.upwork_scraper.config import settings # Import settings for UPWORK_BASE_URL (corrected path)

logger = logging.getLogger(__name__)


class NuxtParser:
    """
    Parses __NUXT_DATA__ script tag with proper reference resolution.
    
    NUXT data is stored as an array where integer values are references to other
    array indices. This parser recursively resolves all references to build complete
    data structures.
    """
    
    def __init__(self, nuxt_array: List[Any], data_quality: DataQuality):
        """
        Initialize parser with NUXT array.
        
        Args:
            nuxt_array: Parsed NUXT_DATA__ JSON array
            data_quality: DataQuality tracker
        """
        self.array = nuxt_array
        self.data_quality = data_quality
        self._resolution_cache: Dict[int, Any] = {}  # Cache for resolved objects
    
    def _resolve_references(self, data_to_resolve: Any, visited: Optional[set] = None) -> Any:
        """
        Recursively resolves integer references in NUXT data.
        
        Handles:
        - Dictionaries: resolves all values
        - Lists: resolves all items
        - Integers: looks up in main array and resolves recursively
        - Other types: returns as-is
        
        Args:
            data_to_resolve: Data to resolve (dict, list, int, or primitive)
            visited: Set of visited object IDs to prevent circular references
            
        Returns:
            Fully resolved data structure
        """
        if visited is None:
            visited = set()
        
        # Handle dictionaries
        if isinstance(data_to_resolve, dict):
            obj_id = id(data_to_resolve)
            if obj_id in visited:
                return data_to_resolve  # Circular reference detected
            visited.add(obj_id)
            
            resolved_dict = {}
            for k, v in data_to_resolve.items():
                resolved_dict[k] = self._resolve_references(v, visited)
            return resolved_dict
        
        # Handle lists
        if isinstance(data_to_resolve, list):
            obj_id = id(data_to_resolve)
            if obj_id in visited:
                return data_to_resolve
            visited.add(obj_id)
            
            return [self._resolve_references(item, visited) for item in data_to_resolve]
        
        # Handle integer references
        if isinstance(data_to_resolve, int):
            # If it's a negative integer, it's not a valid reference, return as-is
            if data_to_resolve < 0:
                # logger.warning(f"Invalid NUXT array index (negative): {data_to_resolve}") # Too noisy
                return data_to_resolve

            # Check cache first
            if data_to_resolve in self._resolution_cache:
                return self._resolution_cache[data_to_resolve]
            
            # Validate index
            if 0 <= data_to_resolve < len(self.array):
                resolved_value_at_index = self.array[data_to_resolve]
                
                # If the value at the index is a primitive, return it directly
                if isinstance(resolved_value_at_index, (int, str, bool, type(None), float)):
                    self._resolution_cache[data_to_resolve] = resolved_value_at_index
                    return resolved_value_at_index

                # Otherwise, resolve recursively
                resolved = self._resolve_references(resolved_value_at_index, visited)
                # Cache the result
                self._resolution_cache[data_to_resolve] = resolved
                return resolved
            else:
                logger.warning(f"Invalid NUXT array index: {data_to_resolve}")
                return data_to_resolve
        
        # Return primitives as-is
        return data_to_resolve
    
    def find_root_data_object(self) -> Optional[Dict]:
        """
        Finds the root data object containing job, buyer, etc.
        
        Searches the NUXT array for an object that has characteristic keys
        indicating it's the main data container for a job detail page.
        """
        # Look for the characteristic root object
        # The structure can be complex, often `{"data":<ref>, "state":<ref>}` or directly contains keys.
        # From the provided example for detail page: `{"data":2,"state":4,"once":10,...}` where `2` points to `{"$RW9Kc6PidP":3}`.
        # So we need to find the object that contains keys like `job`, `buyer`, `sands`, etc.
        
        for item in self.array:
            if isinstance(item, dict):
                resolved_item = self._resolve_references(item) # Resolve the top-level item
                
                # Common pattern 1: The item itself contains direct job/buyer info
                if 'job' in resolved_item and 'buyer' in resolved_item and 'sands' in resolved_item:
                    logger.debug(f"Found root NUXT data (direct keys): {json.dumps(resolved_item, indent=2)[:500]}...")
                    return resolved_item
                
                # Common pattern 2: Main data is nested under 'data' key or similar, which is a dict itself
                # Example: `{"data": {"NuxtLayoutVisitorV2:0": {...actual_data...}}, ...}`
                # Example: `{"data": {"$RW9Kc6PidP": {...actual_data...}}, ...}`
                main_data_container = resolved_item.get('data')
                if isinstance(main_data_container, dict):
                    for k, v in main_data_container.items():
                        # Look for specific generated keys from Nuxt
                        if k.endswith('PidP') and isinstance(v, dict) and 'job' in v and 'buyer' in v:
                            logger.debug(f"Found root NUXT data (nested via PID key): {json.dumps(v, indent=2)[:500]}...")
                            return v
                        # Or other common Nuxt layout keys
                        if k.startswith('NuxtLayoutVisitorV2') and isinstance(v, dict) and 'job' in v and 'buyer' in v:
                            logger.debug(f"Found root NUXT data (nested via NuxtLayoutVisitorV2): {json.dumps(v, indent=2)[:500]}...")
                            return v
                
                # Common pattern 3: Main data is under `state` and then `jobDetails`
                state_data_container = resolved_item.get('state')
                if isinstance(state_data_container, dict):
                    job_details_data = state_data_container.get('jobDetails')
                    if isinstance(job_details_data, dict) and 'job' in job_details_data and 'buyer' in job_details_data:
                         logger.debug(f"Found root NUXT data (nested via state.jobDetails): {json.dumps(job_details_data, indent=2)[:500]}...")
                         return job_details_data

        logger.warning("Root NUXT data object not found by any characteristic patterns. Attempting deep signature search.")
        # Fallback: Deep search by signature if direct paths fail, with a strong signature.
        return self._find_object_by_signature(
            signature_keys=['uid', 'title', 'description', 'ciphertext', 'contractorTier'],
            max_depth=5 # Increase depth for more exhaustive search
        )
    
    def find_job_data(self) -> Optional[Dict]:
        """
        Finds and resolves main job data object.
        
        Returns:
            Resolved job data dictionary
        """
        root = self.find_root_data_object()
        if root and 'job' in root:
            resolved_job_obj = self._resolve_references(root['job'])
            if isinstance(resolved_job_obj, dict):
                return resolved_job_obj
            logger.warning("Resolved 'job' reference is not a dictionary.")

        # Fallback: if root itself looks like a jobDetails object (e.g., in `jobDetails` context)
        if root and 'status' in root and 'title' in root and 'description' in root and 'ciphertext' in root:
            logger.debug("Root object itself appears to be the job data object.")
            return root
        
        logger.warning("Job data object not found in NUXT root. Attempting signature search.")
        return self._find_object_by_signature(
            signature_keys=['title', 'description', 'uid', 'ciphertext', 'contractorTier'],
            type_indicator='JobPosting'
        )
    
    def find_client_data(self) -> Optional[Dict]:
        """
        Finds and resolves client/buyer data object.
        
        Returns:
            Resolved client data dictionary
        """
        root = self.find_root_data_object()
        if root and 'buyer' in root:
            resolved_client_obj = self._resolve_references(root['buyer'])
            if isinstance(resolved_client_obj, dict):
                return resolved_client_obj
            logger.warning("Resolved 'buyer' reference is not a dictionary.")

        logger.warning("Client data object not found in NUXT root. Attempting signature search.")
        return self._find_object_by_signature(
            signature_keys=['totalCharges', 'isPaymentMethodVerified', 'location', 'stats', 'company'],
            type_indicator='Organization'
        )
    
    def find_skills_ontology(self) -> Optional[Dict]:
        """
        Finds and resolves skills ontology (sands object).
        
        Returns:
            Resolved sands data dictionary
        """
        root = self.find_root_data_object()
        if root and 'sands' in root:
            resolved_sands_obj = self._resolve_references(root['sands'])
            if isinstance(resolved_sands_obj, dict):
                return resolved_sands_obj
            logger.warning("Resolved 'sands' reference is not a dictionary.")
        
        logger.warning("Skills ontology (sands) object not found in NUXT root. Attempting signature search.")
        return self._find_object_by_signature(
            signature_keys=['occupation', 'ontologySkills', 'additionalSkills']
        )
    
    def find_seo_data(self) -> Optional[Dict]:
        """
        Finds SEO metadata.
        
        Returns:
            Resolved SEO data dictionary
        """
        root = self.find_root_data_object()
        if root and 'seo' in root:
            resolved_seo_obj = self._resolve_references(root['seo'])
            if isinstance(resolved_seo_obj, dict):
                return resolved_seo_obj
            logger.warning("Resolved 'seo' reference is not a dictionary.")
        
        logger.warning("SEO data object not found in NUXT root. Attempting signature search.")
        return self._find_object_by_signature(
            signature_keys=['title', 'description', 'url'],
        )
    
    def find_job_slug(self) -> Optional[Dict]:
        """
        Finds canonical job slug data.
        
        Returns:
            Resolved job slug dictionary
        """
        root = self.find_root_data_object()
        if root and 'jobSlug' in root:
            resolved_slug_obj = self._resolve_references(root['jobSlug'])
            if isinstance(resolved_slug_obj, dict):
                return resolved_slug_obj
            logger.warning("Resolved 'jobSlug' reference is not a dictionary.")
        
        return None
    
    def find_other_jobs(self) -> Optional[List[Dict]]:
        """
        Finds other jobs by client.
        
        Returns:
            List of resolved job dictionaries
        """
        root = self.find_root_data_object()
        if root and 'openJobs' in root:
            resolved_open_jobs = self._resolve_references(root['openJobs'])
            if isinstance(resolved_open_jobs, list):
                return resolved_open_jobs
            logger.warning("Resolved 'openJobs' reference is not a list.")
        
        return None
    
    def find_similar_jobs(self) -> Optional[List[Dict]]:
        """
        Finds similar jobs.
        
        Returns:
            List of resolved job dictionaries
        """
        root = self.find_root_data_object()
        if root and 'similarJobs' in root:
            resolved_similar_jobs = self._resolve_references(root['similarJobs'])
            if isinstance(resolved_similar_jobs, list):
                return resolved_similar_jobs
            logger.warning("Resolved 'similarJobs' reference is not a list.")
        
        return None

    def find_pagination_data(self) -> Optional[Dict]:
        """
        Finds and resolves pagination data for search results.
        
        Returns:
            Resolved pagination data dictionary or None.
        """
        root = self.find_root_data_object()
        if root and 'state' in root:
            state_data = self._resolve_references(root['state'])
            jobs_search_data = state_data.get('jobsSearch')
            if jobs_search_data and 'paging' in jobs_search_data:
                paging_data = self._resolve_references(jobs_search_data['paging'])
                return {
                    "total_pages": get_nested_safe(paging_data, 'pagesTotal'),
                    "current_page": get_nested_safe(paging_data, 'page'),
                    "total_jobs": get_nested_safe(paging_data, 'total'),
                    "jobs_per_page": get_nested_safe(paging_data, 'perPage'),
                }
        return None
    
    def _find_object_by_signature(
        self,
        signature_keys: List[str],
        type_indicator: Optional[str] = None,
        max_depth: int = 3
    ) -> Optional[Dict]:
        """
        Finds object by matching signature keys and optionally @type.
        Performs a limited-depth BFS search on the NUXT array.
        
        Args:
            signature_keys: Keys that must exist in object
            type_indicator: Optional @type value to match
            max_depth: Maximum recursion depth for the search
            
        Returns:
            First matching resolved object or None
        """
        if not signature_keys:
            return None
        
        # Using a queue for BFS-like traversal
        queue = [(item, 0) for item in self.array if isinstance(item, dict)]
        seen_ids = set(id(item) for item in queue) # Track IDs of processed dicts
        
        while queue:
            current_item, current_depth = queue.pop(0)
            
            if current_depth > max_depth:
                continue
            
            resolved_item = self._resolve_references(current_item) # Resolve current item fully
            
            # Check if this resolved_item matches the signature
            if isinstance(resolved_item, dict) and all(k in resolved_item for k in signature_keys):
                if not type_indicator or resolved_item.get('@type') == type_indicator:
                    logger.debug(f"Found object by signature at depth {current_depth}: {json.dumps(resolved_item, indent=2)[:500]}...")
                    return resolved_item
            
            # Add nested dictionaries/lists to the queue for further exploration
            if current_depth < max_depth:
                for value in resolved_item.values() if isinstance(resolved_item, dict) else (resolved_item if isinstance(resolved_item, list) else []):
                    if isinstance(value, dict) and id(value) not in seen_ids:
                        queue.append((value, current_depth + 1))
                        seen_ids.add(id(value))
                    elif isinstance(value, list):
                        for sub_value in value:
                            if isinstance(sub_value, dict) and id(sub_value) not in seen_ids:
                                queue.append((sub_value, current_depth + 1))
                                seen_ids.add(id(sub_value))
        
        logger.debug(f"No object found by signature {signature_keys} (type: {type_indicator}) up to depth {max_depth}.")
        return None
    
    def populate_job_data(self, job_obj: Dict, data: UpworkJobData):
        """
        Populates UpworkJobData from resolved NUXT job object.
        
        Args:
            job_obj: Resolved job data dictionary
            data: UpworkJobData instance to populate
        """
        # Core fields
        logger.debug(f"Attempting to populate title from NUXT. Current title: '{data.title}', job_obj title: '{job_obj.get('title')}'")
        if not data.title and job_obj.get('title'):
            data.title = normalize_whitespace(BeautifulSoup(str(job_obj['title']), 'lxml').get_text(strip=True)) # Clean HTML from title if present
            self.data_quality.set_source('title', 'nuxt')
        
        if not data.description and job_obj.get('description'):
            # Description might be HTML
            desc_text = normalize_whitespace(BeautifulSoup(str(job_obj['description']), 'lxml').get_text(separator='\n', strip=True))
            if desc_text:
                data.description = desc_text
                self.data_quality.set_source('description', 'nuxt')
        
        # Identifiers
        if not data.uid and job_obj.get('uid'):
            raw_uid = str(job_obj['uid'])
            if not raw_uid.startswith('~'):
                raw_uid = '~' + raw_uid
            data.uid = raw_uid
            self.data_quality.set_source('uid', 'nuxt')
        
        if not data.ciphertext and job_obj.get('ciphertext'):
            data.ciphertext = job_obj['ciphertext']
            self.data_quality.set_source('ciphertext', 'nuxt')
        
        if data.url is None and job_obj.get('ciphertext'): # Construct URL from ciphertext
            data.url = f"{settings.UPWORK_BASE_URL}/jobs/~{job_obj['ciphertext']}"
            self.data_quality.set_source('url', 'nuxt_derived')
        elif data.url is None and job_obj.get('url'): # Fallback to URL directly if present
             data.url = job_obj['url']
             self.data_quality.set_source('url', 'nuxt')

        if data.status is None and job_obj.get('status') is not None:
            status_value = get_nested_safe(job_obj, 'status', 'data')
            if isinstance(status_value, int):
                data.status = status_value
                self.data_quality.set_source('status', 'nuxt')
        
        if data.access is None and job_obj.get('access') is not None:
            access_value = get_nested_safe(job_obj, 'access', 'data')
            if isinstance(access_value, int):
                data.access = access_value
                self.data_quality.set_source('access', 'nuxt')
        
        # Dates
        self._populate_dates(job_obj, data)
        
        # Experience level
        if not data.job_details.experience_level:
            # Check `contractorTier` which is often a direct int (1, 2, 3)
            tier_obj = job_obj.get('contractorTier')
            tier = get_nested_safe(tier_obj, 'data') if isinstance(tier_obj, dict) else tier_obj

            if tier is not None:
                data.job_details.experience_level = ExperienceLevel.from_tier(tier)
                if data.job_details.experience_level:
                    self.data_quality.set_source('experience_level', 'nuxt')
                else:
                    self.data_quality.add_validation_issue(
                        'experience_level',
                        tier,
                        f"Unknown tier value: {tier}",
                        'warning'
                    )
            # Fallback to `tierText` if present, which might be a string like "IntermediateLevel"
            elif job_obj.get('tierText') and not data.job_details.experience_level:
                data.job_details.experience_level = ExperienceLevel.from_text(job_obj['tierText'])
                if data.job_details.experience_level:
                    self.data_quality.set_source('experience_level', 'nuxt_tierText')


        # Duration
        if not data.job_details.duration:
            data.job_details.duration = job_obj.get('durationLabel') or job_obj.get('engagementDuration')
            if data.job_details.duration:
                data.job_details.duration = normalize_whitespace(data.job_details.duration)
                self.data_quality.set_source('duration', 'nuxt')
                # Parse duration to weeks
                data.job_details.duration_weeks = parse_duration_to_weeks(data.job_details.duration)
        
        # Workload
        if not data.job_details.workload:
            # workload often comes from `engagement` in search results, or `workload` on detail page
            raw_workload = job_obj.get('workload') or job_obj.get('engagement')
            if raw_workload:
                # Upwork sometimes has values like "usnuxt_Engagement_421.partTime" that needs decoding
                if isinstance(raw_workload, str) and "usnuxt_Engagement" in raw_workload:
                    if "partTime" in raw_workload:
                        data.job_details.workload = "Part Time"
                    elif "fullTime" in raw_workload:
                        data.job_details.workload = "Full Time"
                    elif "notSure" in raw_workload:
                        data.job_details.workload = "Not Sure"
                    else:
                        data.job_details.workload = normalize_whitespace(raw_workload)
                else:
                    data.job_details.workload = normalize_whitespace(str(raw_workload))
                self.data_quality.set_source('workload', 'nuxt')
        
        # Project type
        if not data.job_details.project_type:
            # Check `project_type` directly or from `type` field
            raw_type = job_obj.get('project_type') or job_obj.get('type')
            if isinstance(job_obj.get('segmentationData'), list) and job_obj.get('segmentationData'):
                raw_type = job_obj['segmentationData'][0].get('type') # Use type from segmentationData if present

            if raw_type:
                data.job_details.project_type = ProjectType.from_nuxt_type(str(raw_type))
                if data.job_details.project_type:
                    self.data_quality.set_source('project_type', 'nuxt')
        
        # Budget
        self._populate_budget(job_obj, data)
        
        # Remote job
        if not data.job_details.remote_job:
            location_type = get_nested_safe(job_obj, 'jobLocationType') or \
                          get_nested_safe(job_obj, 'qualifications', 'jobLocationType')
            if location_type and (str(location_type).upper() == 'TELECOMMUTE' or 'remote' in str(location_type).lower()):
                data.job_details.remote_job = True
                self.data_quality.set_source('remote_job', 'nuxt')
        
        # Additional flags
        if not data.job_details.was_renewed:
            data.job_details.was_renewed = job_obj.get('wasRenewed', False)
        
        if not data.job_details.hide_budget:
            data.job_details.hide_budget = job_obj.get('hideBudget', False)
        
        if data.job_details.number_of_positions is None:
            data.job_details.number_of_positions = clean_number(job_obj.get('numberOfPositionsToHire'))
        
        if not data.job_details.is_contract_to_hire:
            data.job_details.is_contract_to_hire = job_obj.get('isContractToHire', False)
        
        if not data.job_details.not_sure_duration:
            data.job_details.not_sure_duration = job_obj.get('notSureProjectDuration', False)
        
        if not data.job_details.not_sure_experience_level:
            data.job_details.not_sure_experience_level = job_obj.get('notSureExperienceLevel', False)
        
        if not data.job_details.not_sure_freelancers_to_hire:
            data.job_details.not_sure_freelancers_to_hire = job_obj.get('notSureFreelancersToHire', False)
        
        # Category
        self._populate_category(job_obj, data)
        
        # Qualifications
        self._populate_qualifications(job_obj, data)
        
        # Annotations
        self._populate_annotations(job_obj, data)
        
        # Skills (from job object's direct `attrs` or `ontologySkills`)
        self._populate_skills_from_job(job_obj, data)
        
        # Activity
        if 'clientActivity' in job_obj:
            self.populate_activity_data(job_obj['clientActivity'], data)
        elif 'activity' in job_obj: # If activity is directly at top level
            self.populate_activity_data(job_obj['activity'], data)
    
    def _populate_dates(self, job_obj: Dict, data: UpworkJobData):
        """Populates all date fields."""
        # Posted date
        if not data.job_details.posted_date:
            posted = job_obj.get('postedOn') or job_obj.get('publishTime')
            if posted:
                iso_date, raw_text = parse_date_flexible(str(posted))
                data.job_details.posted_date = iso_date
                data.job_details.posted_date_raw = raw_text or str(posted)
                if iso_date:
                    self.data_quality.set_source('posted_date', 'nuxt')
                else:
                    self.data_quality.add_validation_issue(
                        'posted_date',
                        posted,
                        "Could not parse to ISO 8601",
                        'warning'
                    )
        
        # Created date
        if not data.job_details.created_date:
            created = job_obj.get('createdOn')
            if created:
                iso_date, raw_text = parse_date_flexible(str(created))
                data.job_details.created_date = iso_date
                data.job_details.created_date_raw = raw_text or str(created)
                if iso_date:
                    self.data_quality.set_source('created_date', 'nuxt')
        
        # Start date
        if not data.job_details.start_date:
            start = job_obj.get('startDate')
            if start:
                iso_date, _ = parse_date_flexible(str(start))
                data.job_details.start_date = iso_date
                self.data_quality.set_source('start_date', 'nuxt')
        
        # Delivery date
        if not data.job_details.delivery_date:
            delivery = job_obj.get('deliveryDate')
            if delivery:
                iso_date, _ = parse_date_flexible(str(delivery))
                data.job_details.delivery_date = iso_date
                self.data_quality.set_source('delivery_date', 'nuxt')
        
        # Deadline
        if not data.job_details.deadline:
            deadline = job_obj.get('deadline')
            if deadline:
                iso_date, _ = parse_date_flexible(str(deadline))
                data.job_details.deadline = iso_date
                self.data_quality.set_source('deadline', 'nuxt')
    
    def _populate_budget(self, job_obj: Dict, data: UpworkJobData):
        """Populates budget information."""
        # Fixed amount
        if data.job_details.budget.amount is None:
            # Check `amount` first, then `budget.amount`
            amount = clean_number(job_obj.get('amount', {}).get('amount')) or \
                     clean_number(get_nested_safe(job_obj, 'budget', 'amount'))
            if amount is not None:
                data.job_details.budget.amount = amount
                self.data_quality.set_source('budget_amount', 'nuxt')
        
        # Currency
        if not data.job_details.budget.currency_code:
            currency = job_obj.get('amount', {}).get('currencyCode') or \
                       get_nested_safe(job_obj, 'budget', 'currencyCode')
            if currency:
                data.job_details.budget.currency_code = currency
                self.data_quality.set_source('budget_currency', 'nuxt')
        
        # Hourly rate
        if data.job_details.budget.hourly_min is None:
            min_rate = clean_number(get_nested_safe(job_obj, 'hourlyBudget', 'min')) or \
                       clean_number(get_nested_safe(job_obj, 'extendedBudgetInfo', 'hourlyBudgetMin'))
            max_rate = clean_number(get_nested_safe(job_obj, 'hourlyBudget', 'max')) or \
                       clean_number(get_nested_safe(job_obj, 'extendedBudgetInfo', 'hourlyBudgetMax'))
            
            # Fallback to baseSalary (Schema.org format sometimes embedded in NUXT)
            if min_rate is None and max_rate is None:
                min_rate = clean_number(get_nested_safe(job_obj, 'baseSalary', 'value', 'minValue'))
                max_rate = clean_number(get_nested_safe(job_obj, 'baseSalary', 'value', 'maxValue'))
            
            if min_rate is not None or max_rate is not None:
                data.job_details.budget.hourly_min = min_rate
                data.job_details.budget.hourly_max = max_rate
                self.data_quality.set_source('hourly_rate', 'nuxt')
        
        # Budget type
        if not data.job_details.budget.budget_type:
            budget_type = get_nested_safe(job_obj, 'extendedBudgetInfo', 'hourlyBudgetType') or \
                          job_obj.get('type') # 'type' from search results might be 'hourly' or 'fixed'
            if budget_type:
                try:
                    # Convert to ProjectType first, then to BudgetType
                    project_type_enum = ProjectType.from_nuxt_type(str(budget_type))
                    if project_type_enum == ProjectType.ONGOING:
                        data.job_details.budget.budget_type = BudgetType.HOURLY
                    elif project_type_enum == ProjectType.ONE_TIME:
                        data.job_details.budget.budget_type = BudgetType.FIXED
                    else:
                         # Attempt direct conversion if not a known ProjectType
                         data.job_details.budget.budget_type = BudgetType(str(budget_type).lower())

                    self.data_quality.set_source('budget_type', 'nuxt')
                except ValueError:
                    logger.debug(f"Unknown budget type: {budget_type}")
            # If no budget info, set as NOT_PROVIDED
            if not data.job_details.budget.budget_type and data.job_details.budget.amount is None and \
               data.job_details.budget.hourly_min is None and data.job_details.budget.hourly_max is None:
                data.job_details.budget.budget_type = BudgetType.NOT_PROVIDED
                self.data_quality.set_source('budget_type', 'derived_default')

        # Weekly retainer
        if data.job_details.budget.weekly_retainer is None:
            retainer = clean_number(job_obj.get('weeklyBudget', {}).get('amount')) # Often found in 'weeklyBudget.amount'
            if retainer is not None:
                data.job_details.budget.weekly_retainer = retainer
                self.data_quality.set_source('weekly_retainer', 'nuxt')
        
        # Flag if both fixed and hourly exist (for quality tracking)
        if data.job_details.budget.amount is not None and \
           (data.job_details.budget.hourly_min is not None or data.job_details.budget.hourly_max is not None):
            self.data_quality.add_warning(
                "Job has both fixed budget and hourly rate",
                'budget'
            )
    
    def _populate_category(self, job_obj: Dict, data: UpworkJobData):
        """Populates category information."""
        if data.job_details.category is None:
            category_obj = job_obj.get('category')
            category_group_obj = job_obj.get('categoryGroup')
            
            if category_obj or category_group_obj:
                data.job_details.category = Category(
                    name=normalize_whitespace(get_nested_safe(category_obj, 'name')) if get_nested_safe(category_obj, 'name') else None,
                    url_slug=normalize_whitespace(get_nested_safe(category_obj, 'urlName') or get_nested_safe(category_obj, 'urlSlug')) if (get_nested_safe(category_obj, 'urlName') or get_nested_safe(category_obj, 'urlSlug')) else None,
                    group_name=normalize_whitespace(get_nested_safe(category_group_obj, 'name')) if get_nested_safe(category_group_obj, 'name') else None,
                    group_url_slug=normalize_whitespace(get_nested_safe(category_group_obj, 'urlName') or get_nested_safe(category_group_obj, 'urlSlug')) if (get_nested_safe(category_group_obj, 'urlName') or get_nested_safe(category_group_obj, 'urlSlug')) else None,
                )
                self.data_quality.set_source('category', 'nuxt')
    
    def _populate_qualifications(self, job_obj: Dict, data: UpworkJobData):
        """Populates qualifications/requirements."""
        # Only populate if job_details.qualifications (created by default_factory) is essentially empty
        if not data.job_details.qualifications.min_hours_week and not data.job_details.qualifications.preferred_english_skill and not data.job_details.qualifications.allowed_countries:
            qual_obj = job_obj.get('qualifications')
            if qual_obj:
                min_hours_week = clean_number(get_nested_safe(qual_obj, 'minHoursWeek'))
                location_check_required = get_nested_safe(qual_obj, 'locationCheckRequired')
                preferred_english_skill = clean_number(get_nested_safe(qual_obj, 'prefEnglishSkill'))
                rising_talent_only = get_nested_safe(qual_obj, 'risingTalent')
                should_have_portfolio = get_nested_safe(qual_obj, 'shouldHavePortfolio')
                local_market = get_nested_safe(qual_obj, 'localMarket')
                
                # Upwork also has `countries` and `languages` within qualifications
                allowed_countries_raw = get_nested_safe(qual_obj, 'countries')
                allowed_countries = [c for c in allowed_countries_raw if c] if isinstance(allowed_countries_raw, list) else None

                languages_required_raw = get_nested_safe(qual_obj, 'languages')
                languages_required = [lang for lang in languages_required_raw if lang] if isinstance(languages_required_raw, list) else None


                data.job_details.qualifications = Qualifications(
                    min_hours_week=int(min_hours_week) if min_hours_week is not None else None,
                    location_check_required=bool(location_check_required) if isinstance(location_check_required, (bool, int)) else False,
                    preferred_english_skill=int(preferred_english_skill) if preferred_english_skill is not None else None,
                    rising_talent_only=bool(rising_talent_only) if isinstance(rising_talent_only, (bool, int)) else False,
                    should_have_portfolio=bool(should_have_portfolio) if isinstance(should_have_portfolio, (bool, int)) else False,
                    local_market=bool(local_market) if isinstance(local_market, (bool, int)) else False,
                    allowed_countries=allowed_countries,
                    languages_required=languages_required,
                )
                self.data_quality.set_source('qualifications', 'nuxt')
    
    def _populate_annotations(self, job_obj: Dict, data: UpworkJobData):
        """Populates annotations and metadata."""
        # Only populate if job_details.annotations (created by default_factory) is essentially empty
        if not data.job_details.annotations.custom_fields and not data.job_details.annotations.tags and not data.job_details.annotations.site_source:
            annotations_obj = job_obj.get('annotations')
            
            # Segmentation data also contains annotations
            seg_data = job_obj.get('segmentationData')
            if isinstance(seg_data, list) and seg_data:
                seg_data = seg_data[0] # Assume the first element is the relevant dictionary
            elif not isinstance(seg_data, dict):
                seg_data = {} # Default to empty dict if not found or wrong type

            if isinstance(annotations_obj, dict) or seg_data:
                custom_fields = annotations_obj.get('customFields', {}) if isinstance(annotations_obj, dict) else {}
                tags = annotations_obj.get('tags', []) if isinstance(annotations_obj, dict) else []

                data.job_details.annotations = Annotations(
                    custom_fields=custom_fields,
                    tags=[t for t in tags if t] if tags else [], # Filter out None/empty tags
                    site_source=normalize_whitespace(seg_data.get('siteSource')) if seg_data.get('siteSource') else None,
                    sourcing_update_count=clean_number(seg_data.get('sourcingUpdateCount')),
                    sourcing_update_forbidden=seg_data.get('sourcingUpdateForbidden', False),
                    job_type_code=normalize_whitespace(seg_data.get('type')) if seg_data.get('type') else None,
                    original_prompt=normalize_whitespace(seg_data.get('generate_prompt')) if seg_data.get('generate_prompt') else None,
                    browser=normalize_whitespace(seg_data.get('browser')) if seg_data.get('browser') else None,
                    device=normalize_whitespace(seg_data.get('device')) if seg_data.get('device') else None,
                    flow_type=normalize_whitespace(seg_data.get('flowType')) if seg_data.get('flowType') else None,
                )
                self.data_quality.set_source('annotations', 'nuxt')
    
    def _populate_skills_from_job(self, job_obj: Dict, data: UpworkJobData):
        """Populates skills from job object (flat list)."""
        seen_names = {s.name.lower() for s in data.skills}
        skills_to_add = []
        
        # Check multiple possible skill field paths
        skill_field_paths = [
            ['ontologySkills'],
            ['skills'], # Often a direct list of skill objects
            ['additionalSkills'],
            ['attrs'] # From search page data, also present in detail NUXT sometimes
        ]
        
        for path in skill_field_paths:
            skill_list = get_nested_safe(job_obj, *path)
            if isinstance(skill_list, list):
                for skill_obj in skill_list:
                    if isinstance(skill_obj, dict):
                        name = normalize_whitespace(skill_obj.get('prefLabel') or skill_obj.get('prettyName') or skill_obj.get('name'))
                        if name and name.lower() not in seen_names:
                            category = SkillCategory.from_relevance(skill_obj.get('relevance'))
                            skills_to_add.append(Skill(
                                name=name,
                                category=category,
                                uid=skill_obj.get('uid'),
                                ontology_id=skill_obj.get('id'), # Ontology ID might be different from UID
                                parent_group=normalize_whitespace(skill_obj.get('parentSkillUid')) if skill_obj.get('parentSkillUid') else None # If hierarchical attribute
                            ))
                            seen_names.add(name.lower())
        
        if skills_to_add:
            data.skills.extend(skills_to_add)
            self.data_quality.set_source('skills', 'nuxt')
    
    def populate_skills_ontology(self, sands_obj: Dict, data: UpworkJobData):
        """
        Populates hierarchical skills ontology.
        
        Extracts both flat list and hierarchical structure.
        """
        if not sands_obj:
            return
        
        ontology = SkillOntology()
        
        # Occupation info
        occupation = sands_obj.get('occupation', {})
        if occupation:
            ontology.occupation_id = normalize_whitespace(occupation.get('ontologyId') or occupation.get('id')) if (occupation.get('ontologyId') or occupation.get('id')) else None
            ontology.occupation_name = normalize_whitespace(occupation.get('prefLabel') or occupation.get('name')) if (occupation.get('prefLabel') or occupation.get('name')) else None
            ontology.occupation_uid = normalize_whitespace(occupation.get('uid')) if occupation.get('uid') else None
        
        # Skill groups (hierarchical)
        ontology_skills_groups_raw = sands_obj.get('ontologySkills', []) # This might be the top-level groups
        seen_names = {s.name.lower() for s in data.skills} # Ensure uniqueness against already populated skills
        
        for group_obj in ontology_skills_groups_raw:
            if not isinstance(group_obj, dict):
                continue
            
            group_name = normalize_whitespace(group_obj.get('name', ''))
            if not group_name:
                continue # Skip if group name is empty

            skill_group = SkillGroup(
                name=group_name,
                group_id=normalize_whitespace(group_obj.get('id')) if group_obj.get('id') else None,
                uid=normalize_whitespace(group_obj.get('uid')) if group_obj.get('uid') else None,
            )
            
            children = group_obj.get('children', [])
            for child_obj in children:
                if isinstance(child_obj, dict):
                    name = normalize_whitespace(child_obj.get('name') or child_obj.get('prefLabel'))
                    if name:
                        category = SkillCategory.from_relevance(child_obj.get('relevance'))
                        skill = Skill(
                            name=name,
                            category=category,
                            uid=child_obj.get('uid'),
                            ontology_id=child_obj.get('id'),
                            parent_group=skill_group.name,
                        )
                        skill_group.skills.append(skill)
                        
                        # Add to flat list if not already present
                        if name.lower() not in seen_names:
                            data.skills.append(skill)
                            seen_names.add(name.lower())
            
            if skill_group.skills:
                ontology.skill_groups.append(skill_group)
        
        # Additional skills (not in groups)
        additional = sands_obj.get('additionalSkills', [])
        for skill_obj in additional:
            if isinstance(skill_obj, dict):
                name = normalize_whitespace(skill_obj.get('name') or skill_obj.get('prefLabel'))
                if name:
                    category = SkillCategory.from_relevance(skill_obj.get('relevance'))
                    skill = Skill(
                        name=name,
                        category=category,
                        uid=skill_obj.get('uid'),
                        ontology_id=skill_obj.get('id'),
                    )
                    ontology.additional_skills.append(skill)
                    
                    # Add to flat list
                    if name.lower() not in seen_names:
                        data.skills.append(skill)
                        seen_names.add(name.lower())
        
        data.skill_ontology = ontology
        self.data_quality.set_source('skill_ontology', 'nuxt')
    
    def populate_client_data(self, client_obj: Dict, data: UpworkJobData):
        """Populates client information."""
        if not client_obj:
            return
        
        # Location
        location_obj = client_obj.get('location', {})
        if location_obj:
            data.client.location = Location(
                country=normalize_whitespace(get_nested_safe(location_obj, 'address', 'addressCountry') or location_obj.get('country')) if (get_nested_safe(location_obj, 'address', 'addressCountry') or location_obj.get('country')) else None,
                city=normalize_whitespace(get_nested_safe(location_obj, 'address', 'addressLocality') or location_obj.get('city')) if (get_nested_safe(location_obj, 'address', 'addressLocality') or location_obj.get('city')) else None,
                timezone=normalize_whitespace(location_obj.get('countryTimezone') or location_obj.get('timezone')) if (location_obj.get('countryTimezone') or location_obj.get('timezone')) else None,
                timezone_offset_ms=clean_number(location_obj.get('offsetFromUtcMillis')),
            )
            self.data_quality.set_source('client_location', 'nuxt')
        
        # Company
        company_obj = client_obj.get('company', {})
        if company_obj:
            contract_date = company_obj.get('contractDate')
            iso_date, raw_text = parse_date_flexible(str(contract_date)) if contract_date else (None, None)
            
            data.client.company = Company(
                name=normalize_whitespace(str(company_obj.get('name'))) if company_obj.get('name') is not None else None,
                contract_date=iso_date,
                contract_date_raw=raw_text or str(contract_date) if contract_date else None,
            )
            
            # Also set legacy field
            data.client.member_since = iso_date
            data.client.member_since_raw = raw_text or str(contract_date) if contract_date else None
            
            profile = company_obj.get('profile', {})
            if profile:
                data.client.company.industry = normalize_whitespace(profile.get('industry')) if profile.get('industry') else None
                data.client.company.size = normalize_whitespace(profile.get('size')) if profile.get('size') else None
            
            self.data_quality.set_source('client_company', 'nuxt')
        
        # Stats
        stats_obj = client_obj.get('stats', {})
        if stats_obj:
            total_charges = get_nested_safe(stats_obj, 'totalCharges', 'amount')
            
            data.client.stats = ClientStats(
                total_spent=clean_number(total_charges),
                total_hires=clean_number(get_nested_safe(stats_obj, 'totalJobsWithHires')),
                active_hires=clean_number(get_nested_safe(stats_obj, 'activeAssignmentsCount')),
                total_assignments=clean_number(get_nested_safe(stats_obj, 'totalAssignments')),
                hours_count=clean_number(get_nested_safe(stats_obj, 'hoursCount')),
                feedback_count=clean_number(get_nested_safe(stats_obj, 'feedbackCount')),
                client_score=clean_number(get_nested_safe(stats_obj, 'score')),
                jobs_posted_count=clean_number(get_nested_safe(stats_obj, 'jobs', 'postedCount')), # Nested path
                jobs_open_count=clean_number(get_nested_safe(stats_obj, 'jobs', 'openCount')), # Nested path
                avg_hourly_rate=clean_number(get_nested_safe(stats_obj, 'avgHourlyJobsRate')), # Nested path
            )
            self.data_quality.set_source('client_stats', 'nuxt')
        
        # Jobs info (if not already captured in stats)
        # This block might be redundant if stats_obj captures it well, but keeps it safe
        jobs_obj = client_obj.get('jobs', {})
        if jobs_obj:
            if data.client.stats.jobs_posted_count is None:
                data.client.stats.jobs_posted_count = clean_number(jobs_obj.get('postedCount'))
            if data.client.stats.jobs_open_count is None:
                data.client.stats.jobs_open_count = clean_number(jobs_obj.get('openCount'))
        
        # Payment verified
        is_verified = client_obj.get('isPaymentMethodVerified')
        if isinstance(is_verified, bool):
            data.client.payment_verified = is_verified
            self.data_quality.set_source('client_payment_verified', 'nuxt')
        elif isinstance(is_verified, dict) and 'data' in is_verified: # Sometimes nested
            data.client.payment_verified = bool(is_verified['data'])
            self.data_quality.set_source('client_payment_verified', 'nuxt')
        
        # Average hourly rate (if not already captured in stats)
        if data.client.stats.avg_hourly_rate is None:
            avg_rate = clean_number(client_obj.get('avgHourlyJobsRate'))
            if avg_rate is not None:
                data.client.stats.avg_hourly_rate = avg_rate
                self.data_quality.set_source('client_avg_hourly_rate', 'nuxt')

        # Open Jobs by Client (from NUXT directly)
        if not data.client.open_jobs and 'openJobs' in client_obj and isinstance(client_obj['openJobs'], list):
            data.client.open_jobs = client_obj['openJobs']
            self.data_quality.set_source('client_open_jobs', 'nuxt')
    
    def populate_activity_data(self, activity_obj: Dict, data: UpworkJobData):
        """Populates activity metrics."""
        if not activity_obj:
            return
        
        # Proposals
        # Nuxt can provide totalApplicants (exact number) or a range like proposals.max / proposals.min
        proposals_max_val = clean_number(activity_obj.get('totalApplicants')) or \
                            clean_number(get_nested_safe(activity_obj, 'proposals', 'max'))
        proposals_min_val = clean_number(get_nested_safe(activity_obj, 'proposals', 'min'))

        if proposals_max_val is not None:
            data.activity.proposals = ProposalRange(
                min=proposals_min_val if proposals_min_val is not None else proposals_max_val,
                max=proposals_max_val
            )
            # Default text if only max is available
            if proposals_min_val is None or proposals_min_val == proposals_max_val:
                data.activity.proposals_text = f"{int(proposals_max_val)} proposals"
            else:
                data.activity.proposals_text = f"{int(proposals_min_val)} to {int(proposals_max_val)} proposals"
            self.data_quality.set_source('activity_proposals', 'nuxt')
        
        # Interviewing
        interviewing = clean_number(activity_obj.get('totalInvitedToInterview')) or \
                       clean_number(activity_obj.get('interviewing')) # Can be either key
        if interviewing is not None:
            data.activity.interviewing = int(interviewing)
            self.data_quality.set_source('activity_interviewing', 'nuxt')
        
        # Invites sent
        invites = clean_number(activity_obj.get('invitationsSent')) or \
                  clean_number(activity_obj.get('invites_sent')) # Can be either key
        if invites is not None:
            data.activity.invites_sent = int(invites)
            self.data_quality.set_source('activity_invites_sent', 'nuxt')
        
        # Unanswered invites
        unanswered = clean_number(activity_obj.get('unansweredInvites')) or \
                     clean_number(activity_obj.get('unanswered_invites')) # Can be either key
        if unanswered is not None:
            data.activity.unanswered_invites = int(unanswered)
            self.data_quality.set_source('activity_unanswered_invites', 'nuxt')
        
        # Total hired
        hired = clean_number(activity_obj.get('totalHired'))
        if hired is not None:
            data.activity.total_hired = int(hired)
            self.data_quality.set_source('activity_total_hired', 'nuxt')
        
        # Last buyer activity
        last_activity = activity_obj.get('lastBuyerActivity') or activity_obj.get('last_buyer_activity')
        if last_activity:
            iso_date, raw_text = parse_date_flexible(str(last_activity))
            data.activity.last_buyer_activity = iso_date
            data.activity.last_buyer_activity_raw = raw_text or str(last_activity)
            self.data_quality.set_source('activity_last_buyer_activity', 'nuxt')

        # Last viewed
        last_viewed = activity_obj.get('lastViewed') or activity_obj.get('last_viewed')
        if last_viewed:
            data.activity.last_viewed = normalize_whitespace(str(last_viewed)) # Store raw string as it might be relative "a few minutes ago"
            self.data_quality.set_source('activity_last_viewed', 'nuxt')

    
    def populate_job_slug(self, slug_obj: Dict, data: UpworkJobData):
        """Populates job slug data."""
        if not slug_obj:
            return
        
        # Only populate if job_details.job_slug is still default_factory created (empty)
        if not data.job_details.job_slug.id and not data.job_details.job_slug.name:
            data.job_details.job_slug = JobSlug(
                id=normalize_whitespace(slug_obj.get('id')) if slug_obj.get('id') else None,
                type=normalize_whitespace(slug_obj.get('type')) if slug_obj.get('type') else None,
                name=normalize_whitespace(slug_obj.get('name')) if slug_obj.get('name') else None,
                slug=normalize_whitespace(slug_obj.get('slug')) if slug_obj.get('slug') else None,
                modifier=normalize_whitespace(slug_obj.get('modifier')) if slug_obj.get('modifier') else None,
            )
            self.data_quality.set_source('job_slug', 'nuxt')

    def extract_search_job_summaries(self) -> List[Dict[str, Any]]:
        """
        Extracts a list of job summaries from a search results page's NUXT data.
        This method assumes `self.array` contains the NUXT data for a search page.
        """
        jobs_raw_data = None
        
        # Navigate to state.jobsSearch.jobs in the NUXT data structure (common for search pages)
        state = self.array[0].get('state', {}) if self.array and isinstance(self.array[0], dict) else {}
        jobs_search = state.get('jobsSearch', {})
        jobs_raw_data = jobs_search.get('jobs', [])

        if jobs_raw_data:
            logger.debug(f"Extracted {len(jobs_raw_data)} jobs from NUXT data for search.")
            formatted_jobs: List[Dict[str, Any]] = []
            for raw_job in jobs_raw_data:
                # Minimal formatting as detailed parsing happens in StorageService from UpworkJobData
                # This primarily extracts what's easily available on the search result.
                # All values are normalized before returning
                formatted_jobs.append({
                    "uid": str(raw_job.get("uid", "")),
                    "title": normalize_whitespace(BeautifulSoup(raw_job.get("title", ""), 'lxml').get_text(strip=True)),
                    "description": normalize_whitespace(BeautifulSoup(raw_job.get("description", ""), 'lxml').get_text(strip=True)),
                    "ciphertext": raw_job.get('ciphertext'),
                    "url": f"{settings.UPWORK_BASE_URL}/jobs/~{raw_job.get('ciphertext')}" if raw_job.get('ciphertext') else None,
                    "type": raw_job.get("type"), # Fixed/Hourly identifier (integer)
                    "hourlyBudget": raw_job.get("hourlyBudget", {}),
                    "amount": raw_job.get("amount", {}), # Fixed price amount
                    "durationLabel": raw_job.get("durationLabel"),
                    "engagement": raw_job.get("engagement"),
                    "tierText": raw_job.get("tierText"),
                    "createdOn": raw_job.get("createdOn"),
                    "publishedOn": raw_job.get("publishedOn"),
                    "renewedOn": raw_job.get("renewedOn"),
                    "attrs": raw_job.get("attrs", []), # Skills from search page
                    "relevanceEncoded": raw_job.get("relevanceEncoded")
                })
            return formatted_jobs
        else:
            logger.warning("No job list found in NUXT data structure for search page.")
            return []
File: upwork_extractor/parsers/schema_parser.py
"""
Schema.org JSON-LD parser for validation.

Extracts structured data from Schema.org markup and validates against extracted data.
"""

import json
import logging
from typing import Optional, Dict, Any, List
from bs4 import BeautifulSoup
from difflib import SequenceMatcher # Import for improved text similarity

from ..models.quality import DataQuality, SchemaOrgMismatch
from ..utils.text_utils import get_nested_safe, normalize_whitespace
from ..utils.date_utils import parse_date_flexible
from ..utils.validation import sanitize_html
from .selectors import SCHEMA_SCRIPT_SELECTOR

logger = logging.getLogger(__name__)


class SchemaParser:
    """
    Parses Schema.org JobPosting JSON-LD for validation.
    
    Used as validation source to detect mismatches with NUXT/HTML data.
    """
    
    def __init__(self, soup: BeautifulSoup, data_quality: DataQuality):
        """
        Initialize schema parser.
        
        Args:
            soup: BeautifulSoup instance of HTML
            data_quality: DataQuality tracker
        """
        self.soup = soup
        self.data_quality = data_quality
        self.schema_data: Optional[Dict[str, Any]] = None
    
    def extract_schema_data(self) -> Optional[Dict[str, Any]]:
        """
        Extracts and parses Schema.org JSON-LD.
        
        Handles single object, list of objects, and @graph structures.
        
        Returns:
            Parsed schema dictionary or None if not found/invalid
        """
        try:
            # Find all script tags with type="application/ld+json"
            script_tags = self.soup.find_all(**SCHEMA_SCRIPT_SELECTOR)
            
            for script in script_tags:
                if not script.string:
                    continue
                
                try:
                    data = json.loads(script.string)
                    
                    potential_nodes = []
                    if isinstance(data, list):
                        potential_nodes.extend(data)
                    elif isinstance(data, dict):
                        if data.get('@graph'):
                            potential_nodes.extend(data['@graph'])
                        else:
                            potential_nodes.append(data)
                    
                    for item in potential_nodes:
                        if isinstance(item, dict) and item.get('@type') == 'JobPosting':
                            self.schema_data = item
                            logger.info("Successfully extracted Schema.org JobPosting data")
                            return item
                    
                except json.JSONDecodeError as e:
                    logger.debug(f"Failed to parse JSON-LD script: {e}")
                    continue
            
            logger.warning("No Schema.org JobPosting found in HTML")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting Schema.org data: {e}", exc_info=True)
            self.data_quality.add_warning(
                f"Schema.org extraction failed: {str(e)}",
                "schema_org"
            )
            return None
    
    def validate_against_extracted(
        self,
        extracted_data: Dict[str, Any],
        source: str = "nuxt"
    ) -> List[SchemaOrgMismatch]: # Return list of SchemaOrgMismatch objects
        """
        Validates extracted data against Schema.org data.
        
        Detects mismatches and records them in data_quality.
        
        Args:
            extracted_data: Data extracted from NUXT or HTML (should be normalized dict)
            source: Source name ('nuxt' or 'html')
            
        Returns:
            List of SchemaOrgMismatch objects
        """
        if not self.schema_data:
            logger.debug("No Schema.org data available for validation")
            return []
        
        mismatches: List[SchemaOrgMismatch] = []
        
        # Validate title
        schema_title = normalize_whitespace(self.schema_data.get('title', ''))
        extracted_title = normalize_whitespace(extracted_data.get('job_title', ''))
        if schema_title and extracted_title and schema_title != extracted_title:
            mismatch = SchemaOrgMismatch('title', schema_title, extracted_title, source)
            self.data_quality.add_schema_mismatch(**mismatch.__dict__) # Use dict to unpack dataclass
            mismatches.append(mismatch)
        
        # Validate description (compare plain text)
        schema_desc = sanitize_html(self.schema_data.get('description', ''))
        extracted_desc = sanitize_html(extracted_data.get('job_description', ''))
        if schema_desc and extracted_desc:
            if not self._texts_similar(schema_desc, extracted_desc, threshold=0.9):
                mismatch = SchemaOrgMismatch(
                    'description',
                    schema_desc[:100] + '...',
                    extracted_desc[:100] + '...',
                    source
                )
                self.data_quality.add_schema_mismatch(**mismatch.__dict__)
                mismatches.append(mismatch)
        
        # Validate posted date
        schema_posted_raw = self.schema_data.get('datePosted')
        extracted_posted_raw = extracted_data.get('posted_date')
        if schema_posted_raw and extracted_posted_raw:
            schema_iso, _ = parse_date_flexible(schema_posted_raw)
            # Extracted data should already be ISO
            extracted_iso = extracted_posted_raw 
            
            if schema_iso and extracted_iso and schema_iso != extracted_iso:
                mismatch = SchemaOrgMismatch('posted_date', schema_iso, extracted_iso, source)
                self.data_quality.add_schema_mismatch(**mismatch.__dict__)
                mismatches.append(mismatch)
        
        # Validate budget (hourly rate)
        schema_salary = get_nested_safe(
            self.schema_data,
            'baseSalary',
            'value'
        )
        if schema_salary:
            schema_min = get_nested_safe(schema_salary, 'minValue')
            schema_max = get_nested_safe(schema_salary, 'maxValue')
            schema_currency = self.schema_data.get('baseSalary', {}).get('currency')
            
            # Use normalized keys for extracted data
            extracted_min = extracted_data.get('hourly_min')
            extracted_max = extracted_data.get('hourly_max')
            extracted_currency = extracted_data.get('budget_currency')
            
            if schema_min is not None and extracted_min is not None and float(schema_min) != float(extracted_min):
                mismatch = SchemaOrgMismatch('hourly_rate_min', schema_min, extracted_min, source)
                self.data_quality.add_schema_mismatch(**mismatch.__dict__)
                mismatches.append(mismatch)
            
            if schema_max is not None and extracted_max is not None and float(schema_max) != float(extracted_max):
                mismatch = SchemaOrgMismatch('hourly_rate_max', schema_max, extracted_max, source)
                self.data_quality.add_schema_mismatch(**mismatch.__dict__)
                mismatches.append(mismatch)
            
            if schema_currency and extracted_currency and normalize_whitespace(schema_currency) != normalize_whitespace(extracted_currency):
                mismatch = SchemaOrgMismatch('currency_code', schema_currency, extracted_currency, source)
                self.data_quality.add_schema_mismatch(**mismatch.__dict__)
                mismatches.append(mismatch)
        
        # Validate employment type (informational, not strict equality)
        schema_employment = self.schema_data.get('employmentType')
        extracted_project_type = extracted_data.get('project_type')
        
        if schema_employment and extracted_project_type:
            # Schema.org often uses ["FULL_TIME", "PART_TIME"], extracted uses "one_time", "ongoing"
            # This is more of a semantic comparison, not direct string equality
            schema_types_str = schema_employment if isinstance(schema_employment, str) else ", ".join(schema_employment)
            schema_types_lower = schema_types_str.lower()
            
            # Basic mapping logic for comparison (can be expanded)
            is_schema_fixed = "fixed" in schema_types_lower or "one_time" in schema_types_lower
            is_schema_hourly = "hourly" in schema_types_lower or "full_time" in schema_types_lower or "part_time" in schema_types_lower or "ongoing" in schema_types_lower

            is_extracted_fixed = extracted_project_type == "one_time"
            is_extracted_hourly = extracted_project_type == "ongoing"

            if (is_schema_fixed != is_extracted_fixed) or (is_schema_hourly != is_extracted_hourly):
                mismatch = SchemaOrgMismatch(
                    'employment_type',
                    schema_types_str,
                    extracted_project_type,
                    source
                )
                self.data_quality.add_schema_mismatch(**mismatch.__dict__)
                mismatches.append(mismatch)
        
        if mismatches:
            logger.warning(f"Found {len(mismatches)} Schema.org validation mismatches.")
        else:
            logger.info("Schema.org validation passed - no mismatches found.")
        
        return mismatches
    
    def _texts_similar(self, text1: str, text2: str, threshold: float = 0.9) -> bool:
        """
        Checks if two texts are similar using difflib's SequenceMatcher after normalization.
        
        Args:
            text1: First text
            text2: Second text
            threshold: Similarity threshold (0-1)
            
        Returns:
            True if texts are similar enough
        """
        if not text1 or not text2:
            return False
        
        text1_norm = normalize_whitespace(text1).lower()
        text2_norm = normalize_whitespace(text2).lower()
        
        if not text1_norm or not text2_norm:
            return False

        ratio = SequenceMatcher(None, text1_norm, text2_norm).ratio()
        
        return ratio >= threshold
    
    def get_schema_summary(self) -> Optional[Dict[str, Any]]:
        """
        Returns summary of Schema.org data for reporting.
        
        Returns:
            Dictionary with key schema fields
        """
        if not self.schema_data:
            return None
        
        return {
            'type': self.schema_data.get('@type'),
            'title': self.schema_data.get('title'),
            'url': self.schema_data.get('url'),
            'date_posted': self.schema_data.get('datePosted'),
            'employment_type': self.schema_data.get('employmentType'),
            'has_salary_info': 'baseSalary' in self.schema_data,
            'job_location_city': get_nested_safe(self.schema_data, 'jobLocation', 'address', 'addressLocality'),
            'job_location_country': get_nested_safe(self.schema_data, 'jobLocation', 'address', 'addressCountry')
        }
File: upwork_extractor/parsers/selectors.py
"""
HTML selectors constants.

Centralized selectors for robust HTML parsing.
Uses data attributes and semantic selectors over fragile class names.
All auto-generated data-v-* selectors have been removed as they are brittle.
"""

import re

# ============================================================================
# JOB CORE INFORMATION
# ============================================================================

HTML_JOB_TITLE_SELECTORS = [
    # Primary: Data attribute selectors (most stable)
    {'name': 'h1', 'attrs': {'data-qa': 'job-title'}},
    {'name': 'h1', 'attrs': {'data-test': 'job-title'}},
    {'name': 'h2', 'attrs': {'data-qa': 'job-title'}},
    
    # Secondary: Semantic selectors (often stable)
    {'name': 'h1', 'class_': re.compile(r'\bh[1-6]\b')},
    {'name': 'strong', 'class_': re.compile(r'\bh[1-6]\b')}, # Sometimes titles are strong tags
    
    # Fallback: Any h1 in a relevant context (less specific)
    {'name': 'h1', 'class_': 'h4'}, # General class for title-like elements
]

HTML_JOB_DESCRIPTION_SELECTORS = [
    {'attrs': {'data-test': 'Description'}},
    {'attrs': {'data-qa': 'job-description'}},
    {'name': 'section', 'attrs': {'aria-label': re.compile(r'description', re.I)}},
    {'class_': 'job-description-content'}, # Common content container
    {'class_': 'description'}, # Another common class
    {'id': 'job-description-section'}, # ID selector
]

# ============================================================================
# JOB DETAILS & FEATURES (Experience, Duration, Budget, Workload)
# ============================================================================

HTML_FEATURES_LIST_SELECTORS = [
    {'name': 'ul', 'class_': 'features'}, # Old structure, list of features
    {'name': 'section', 'attrs': {'data-qa': re.compile(r'job.*details', re.I)}}, # Generic section
    {'name': 'div', 'class_': 'job-details-overview'}, # Common container for job overview
    {'name': 'ul', 'class_': 'list-unstyled cfe-ui-job-features-list'}, # Current list structure
    {'class_': 'up-card-section', 'attrs': {'data-test': 'job-details-card'}}, # Another common card
]

HTML_POSTED_DATE_SELECTORS = [ # Can be in a span, small, or div
    {'class_': 'posted-on-line'},
    {'name': 'small', 'class_': 'text-light-on-muted'}, # Common for smaller text dates
    {'name': 'span', 'attrs': {'data-qa': 'posted-date'}}, # data-qa selector
    {'name': 'div', 'class_': 'up-card-section-info'}, # Sometimes part of a larger info block
]


# ============================================================================
# SKILLS
# ============================================================================

HTML_SKILLS_SECTION_SELECTOR = {'name': 'section', 'class_': re.compile(r'skills-section|job-skills', re.I)} # General sections for skills
HTML_SKILL_BADGE_PATTERN = re.compile(r'(?:air3-badge|skill-badge|tag-badge)', re.I) # Class for skill badges


# ============================================================================
# CLIENT INFORMATION
# ============================================================================

HTML_CLIENT_SECTION_SELECTORS = [ # Using a list of potential selectors for robustness
    {'class_': 'cfe-about-client-v2'}, # Common client section class
    {'class_': 'up-card-section', 'attrs': {'data-test': 'client-info'}}, # Another common card structure
    {'name': 'section', 'attrs': {'aria-label': re.compile(r'about the client', re.I)}},
    {'name': 'div', 'attrs': {'data-qa': 'client-profile'}}, # Generic client profile container
]

HTML_CLIENT_LOCATION_SELECTOR = {'attrs': {'data-qa': 'client-location'}}
HTML_CLIENT_SPEND_SELECTOR = {'attrs': {'data-qa': 'client-spend'}}
HTML_CLIENT_HIRES_SELECTOR = {'attrs': {'data-qa': 'client-hires'}}
HTML_CLIENT_CONTRACT_DATE_SELECTORS = [ # Can be in small or span
    {'attrs': {'data-qa': 'client-contract-date'}},
    {'name': 'small', 'string': re.compile(r'Member since', re.I)},
]
HTML_CLIENT_COMPANY_SELECTOR = {'attrs': {'data-qa': 'client-company-profile'}} # Link to company profile


# ============================================================================
# ACTIVITY METRICS
# ============================================================================

HTML_ACTIVITY_SECTION_SELECTOR = {'class_': re.compile(r'client-activity')} # Generic for activity block
HTML_ACTIVITY_ITEM_SELECTORS = [ # List of selectors for the container of activity items
    {'class_': re.compile(r'(?:ca-items-list|list-unstyled cfe-ui-job-activity-list)', re.I)}, # Common list of items
    {'name': 'div', 'attrs': {'data-test': 'proposals-section'}}, # Specific section for proposals
]


# ============================================================================
# RELATED JOBS (Other jobs by client, Similar jobs)
# ============================================================================

HTML_OTHER_JOBS_LIST_SELECTOR = {'name': 'ul', 'id': 'otherOpenJobs'} # ID might change, prefer data-qa/data-test
HTML_SIMILAR_JOBS_SELECTORS = [ # List of selectors for individual similar job cards
    {'name': 'section', 'class_': 'job-tile'},
    {'attrs': {'data-test': 'job-tile'}},
    {'class_': 'air3-job-tile'},
]


# ============================================================================
# META TAGS
# ============================================================================

META_URL_SELECTORS = [
    {'name': 'meta', 'attrs': {'property': 'og:url'}},
    {'name': 'link', 'attrs': {'rel': 'canonical'}},
]

META_DESCRIPTION_SELECTOR = {'name': 'meta', 'attrs': {'name': 'description'}}


# ============================================================================
# SCHEMA.ORG JSON-LD
# ============================================================================

SCHEMA_SCRIPT_SELECTOR = {
    'name': 'script',
    'attrs': {'type': 'application/ld+json'}
}


# ============================================================================
# NUXT DATA
# ============================================================================

NUXT_DATA_SCRIPT_SELECTOR = {
    'name': 'script',
    'attrs': {'id': '__NUXT_DATA__'}
}


# ============================================================================
# HELPER PATTERNS (RegEx)
# ============================================================================

# Text patterns for extracting specific data
PATTERN_PROPOSALS = re.compile(r'proposal', re.I)
PATTERN_INTERVIEWING = re.compile(r'interview', re.I)
PATTERN_INVITES_SENT = re.compile(r'invite.*sent', re.I)
PATTERN_UNANSWERED = re.compile(r'unanswered', re.I)

PATTERN_EXPERIENCE_LEVEL = re.compile(r'experience', re.I)
PATTERN_DURATION = re.compile(r'duration', re.I)
PATTERN_HOURLY = re.compile(r'hour(?:ly)?|hrs?/week', re.I)

PATTERN_MEMBER_SINCE = re.compile(r'member\s+since', re.I)
PATTERN_HIRES = re.compile(r'(\d+)\s*hires?(?:,\s*(\d+)\s*active)?', re.I)


# ============================================================================
# CONSTANTS
# ============================================================================

DELIVERABLES_LIST_SELECTOR = {'attrs': {'data-test': 'deliverables'}}

# Remote job indicators
REMOTE_JOB_PATTERNS = [
    re.compile(r'remote', re.I),
    re.compile(r'worldwide', re.I),
    re.compile(r'telecommute', re.I),
]
File: upwork_extractor/utils/init.py
"""
Utility functions for data extraction and processing.

Organized into focused modules:
- text_utils: Text cleaning, number parsing
- date_utils: Date/time parsing and formatting
- validation: Data validation helpers
"""

from .date_utils import (
    ensure_utc_iso,
    format_duration,
    parse_date_flexible,
    parse_duration_to_weeks,
    parse_relative_date,
)
from .text_utils import (
    clean_number,
    extract_skills_from_text,
    get_nested_safe,
    get_text_safe,
    normalize_whitespace,
    parse_proposals_text,
    truncate_text,
)
from .validation import (
    sanitize_html,
    validate_currency_code,
    validate_date_iso,
    validate_range,
    validate_uid,
    validate_url,
)

__all__ = [
    # Date utilities
    "ensure_utc_iso",
    "format_duration",
    "parse_date_flexible",
    "parse_duration_to_weeks",
    "parse_relative_date",
    # Text utilities
    "clean_number",
    "extract_skills_from_text",
    "get_nested_safe",
    "get_text_safe",
    "normalize_whitespace",
    "parse_proposals_text",
    "truncate_text",
    # Validation
    "sanitize_html",
    "validate_currency_code",
    "validate_date_iso",
    "validate_range",
    "validate_uid",
    "validate_url",
]
File: upwork_extractor/utils/date_utils.py
"""
Date and time parsing utilities.

Handles various date formats including ISO 8601, relative dates, and common formats.
"""

import re
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import logging
from dateutil.relativedelta import relativedelta # Import for accurate month/year calculations

logger = logging.getLogger(__name__)

# Precompiled regex patterns for relative dates
RELATIVE_PATTERNS = [
    (re.compile(r'(\d+)\s*min(?:ute)?s?\s*ago'), lambda n: timedelta(minutes=n)),
    (re.compile(r'(\d+)\s*hour?s?\s*ago'), lambda n: timedelta(hours=n)),
    (re.compile(r'(\d+)\s*day?s?\s*ago'), lambda n: timedelta(days=n)),
    (re.compile(r'(\d+)\s*week?s?\s*ago'), lambda n: timedelta(weeks=n)),
    # Using relativedelta for more accurate month/year handling
    (re.compile(r'(\d+)\s*month?s?\s*ago'), lambda n: relativedelta(months=n)),
    (re.compile(r'(\d+)\s*year?s?\s*ago'), lambda n: relativedelta(years=n)),
    (re.compile(r'a\s+minute\s+ago'), lambda _: timedelta(minutes=1)),
    (re.compile(r'an?\s+hour\s+ago'), lambda _: timedelta(hours=1)),
    (re.compile(r'a\s+day\s+ago'), lambda _: timedelta(days=1)),
    (re.compile(r'a\s+week\s+ago'), lambda _: timedelta(weeks=1)),
    (re.compile(r'a\s+month\s+ago'), lambda _: relativedelta(months=1)),
    (re.compile(r'a\s+year\s+ago'), lambda _: relativedelta(years=1)),
    (re.compile(r'just\s+now'), lambda _: timedelta(seconds=0)),
    (re.compile(r'yesterday'), lambda _: timedelta(days=1)),
]

# Common date format strings
DATE_FORMATS = [
    '%Y-%m-%d',                    # 2024-03-20
    '%Y-%m-%dT%H:%M:%S.%fZ',       # 2024-03-20T10:30:45.123Z
    '%Y-%m-%dT%H:%M:%S%z',         # 2024-03-20T10:30:45+0000
    '%Y-%m-%dT%H:%M:%S.%f%z',      # 2024-03-20T10:30:45.123+0000
    '%B %d, %Y',                   # March 20, 2024
    '%b %d, %Y',                   # Mar 20, 2024
    '%m/%d/%Y',                    # 03/20/2024
    '%d/%m/%Y',                    # 20/03/2024
    '%Y/%m/%d',                    # 2024/03/20
    '%d %B %Y',                    # 20 March 2024
    '%d %b %Y',                    # 20 Mar 2024
    '%Y-%m-%d %H:%M:%S',           # 2024-03-20 10:30:45 (Assume UTC if no timezone)
    '%Y-%m-%d %H:%M',              # 2024-03-20 10:30 (Assume UTC)
]


def ensure_utc_iso(dt: datetime) -> str:
    """
    Ensures datetime is UTC and returns ISO 8601 string with 'Z' suffix.
    
    Args:
        dt: Datetime object (aware or naive)
        
    Returns:
        ISO 8601 string with 'Z' suffix (e.g., "2024-03-20T10:30:45Z")
    """
    # If naive, assume UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    # If aware but not UTC, convert to UTC
    elif dt.tzinfo != timezone.utc:
        dt = dt.astimezone(timezone.utc)
    
    # Format as ISO with seconds precision and 'Z' suffix
    return dt.isoformat(timespec='seconds').replace('+00:00', 'Z')


def parse_relative_date(text: str) -> Optional[str]:
    """
    Parses relative date text into UTC ISO 8601 timestamp.
    
    Args:
        text: Relative date text (e.g., "5 minutes ago", "yesterday")
        
    Returns:
        ISO 8601 timestamp or None if not a relative date
        
    Examples:
        >>> parse_relative_date("5 minutes ago")
        "2024-03-20T10:25:00Z"  # (if current time is 10:30)
        >>> parse_relative_date("just now")
        "2024-03-20T10:30:00Z"
    """
    if not text:
        return None
    
    text_lower = text.lower().strip()
    now = datetime.now(timezone.utc)
    
    for pattern, delta_fn in RELATIVE_PATTERNS:
        match = pattern.search(text_lower)
        if match:
            try:
                # Extract number if present (group 1), otherwise use default (1)
                n = int(match.group(1)) if match.lastindex and match.lastindex >= 1 and match.group(1).isdigit() else 1
                delta = delta_fn(n)
                
                # relativedelta works directly with datetime objects
                if isinstance(delta, relativedelta):
                    past_time = now - delta
                else: # timedelta objects
                    past_time = now - delta

                return ensure_utc_iso(past_time)
            except (ValueError, IndexError) as e:
                logger.debug(f"Error parsing relative date '{text}': {e}")
                continue
    
    return None


def parse_date_flexible(text: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Parses date/time string into UTC ISO 8601 format.
    
    Handles:
    1. ISO 8601 formats (with/without timezone)
    2. Relative dates ("5 minutes ago")
    3. Common explicit formats ("March 20, 2024")
    
    Returns both parsed ISO date and original raw text for dual storage.
    
    Args:
        text: Date string in any supported format
        
    Returns:
        Tuple of (iso_date_str, raw_text)
        - iso_date_str: Parsed ISO 8601 UTC timestamp with 'Z' suffix, or None
        - raw_text: Original text if parsing failed, otherwise None
        
    Examples:
        >>> parse_date_flexible("2024-03-20T10:30:45.123Z")
        ("2024-03-20T10:30:45Z", None)
        >>> parse_date_flexible("5 minutes ago")
        ("2024-03-20T10:25:00Z", "5 minutes ago")
        >>> parse_date_flexible("March 20, 2024")
        ("2024-03-20T00:00:00Z", None)
    """
    if not text:
        return None, None
    
    text = text.strip()
    
    # 1. Try ISO 8601 format first (most common in NUXT data)
    try:
        # Handle 'Z' suffix by converting to +00:00
        iso_text = text.replace('Z', '+00:00') if text.endswith('Z') else text
        dt = datetime.fromisoformat(iso_text)
        return ensure_utc_iso(dt), None
    except ValueError:
        pass
    
    # 2. Try relative dates
    relative_iso = parse_relative_date(text)
    if relative_iso:
        return relative_iso, text  # Keep raw text for relative dates
    
    # 3. Try common explicit date formats
    for fmt in DATE_FORMATS:
        try:
            dt = datetime.strptime(text, fmt)
            # Assume parsed naive datetimes are UTC
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return ensure_utc_iso(dt), None
        except ValueError:
            continue
    
    # 4. Try parsing just the date part if time parsing fails
    date_only_match = re.match(r'(\d{4}-\d{2}-\d{2})', text)
    if date_only_match:
        try:
            dt = datetime.strptime(date_only_match.group(1), '%Y-%m-%d')
            dt = dt.replace(tzinfo=timezone.utc)
            return ensure_utc_iso(dt), text  # Keep raw text as it had extra info
        except ValueError:
            pass
    
    logger.warning(f"Failed to parse date: '{text}'. Returning raw string.") # Changed to WARNING
    return None, text  # Return raw text if all parsing attempts fail


def format_duration(weeks: Optional[int]) -> Optional[str]:
    """
    Formats duration in weeks to human-readable string.
    
    Args:
        weeks: Duration in weeks
        
    Returns:
        Formatted string (e.g., "1-3 months", "3-6 months")
        
    Examples:
        >>> format_duration(9)
        "1-3 months"
        >>> format_duration(24)
        "3-6 months"
    """
    if weeks is None:
        return None
    
    if weeks < 4:
        return "Less than 1 month"
    elif weeks <= 12:
        return "1-3 months"
    elif weeks <= 24:
        return "3-6 months"
    else:
        return "More than 6 months"


def parse_duration_to_weeks(duration_text: Optional[str]) -> Optional[int]:
    """
    Parses duration text to approximate weeks.
    
    Args:
        duration_text: Duration string (e.g., "1-3 months", "Less than 1 month")
        
    Returns:
        Approximate duration in weeks
        
    Examples:
        >>> parse_duration_to_weeks("1-3 months")
        9
        >>> parse_duration_to_weeks("More than 6 months")
        26
    """
    if not duration_text:
        return None
    
    text_lower = duration_text.lower()
    
    if 'less than 1 month' in text_lower or 'less than a month' in text_lower:
        return 2
    elif '1-3 months' in text_lower or '1 to 3 months' in text_lower:
        return 9  # Middle of range: 2 months * 4.5 weeks
    elif '3-6 months' in text_lower or '3 to 6 months' in text_lower:
        return 19  # Middle of range: 4.5 months * 4.3 weeks
    elif 'more than 6 months' in text_lower:
        return 26  # 6+ months (approx)
    
    # Try to extract numbers
    match_range = re.search(r'(\d+)\s*(?:to|-)\s*(\d+)\s*(week|month)', text_lower)
    if match_range:
        min_val = int(match_range.group(1))
        max_val = int(match_range.group(2))
        unit = match_range.group(3)
        
        avg = (min_val + max_val) / 2
        if unit == 'week':
            return int(avg)
        elif unit == 'month':
            return int(avg * (365.25 / 12 / 7)) # More accurate weeks per month
            
    match_single = re.search(r'(\d+)\s*(week|month)', text_lower)
    if match_single:
        val = int(match_single.group(1))
        unit = match_single.group(2)
        if unit == 'week':
            return val
        elif unit == 'month':
            return int(val * (365.25 / 12 / 7)) # More accurate weeks per month
    
    return None
File: upwork_extractor/utils/text_utils.py
"""
Text processing and number extraction utilities.
"""

import re
from typing import Optional, Union, Tuple, Any
from bs4 import Tag
import logging

logger = logging.getLogger(__name__)

# Precompiled regex patterns for performance
CURRENCY_PATTERN = re.compile(r'[$,% ]')
NUMBER_PATTERN = re.compile(r'[-+]?\d*\.?\d+') # For general numbers


def get_text_safe(element: Optional[Union[Tag, str]]) -> str:
    """
    Safely extracts text from HTML element or string.
    
    Args:
        element: BeautifulSoup Tag, string, or None
        
    Returns:
        Cleaned text string, empty string if None
    """
    if element is None:
        return ''
    
    if isinstance(element, str):
        return element.strip()
    
    if hasattr(element, 'get_text'):
        return element.get_text(strip=True)
    
    return str(element).strip()


def get_nested_safe(data_obj: Any, *keys: Union[str, int]) -> Any:
    """
    Safely accesses nested dictionary/list values.
    
    Traverses nested structures without raising KeyError or IndexError.
    
    Args:
        data_obj: Dictionary, list, or any object
        *keys: Path to nested value (strings for dict keys, ints for list indices)
        
    Returns:
        Value at nested path, or None if path doesn't exist
        
    Example:
        >>> data = {'job': {'budget': {'amount': 100}}}
        >>> get_nested_safe(data, 'job', 'budget', 'amount')
        100
        >>> get_nested_safe(data, 'job', 'invalid', 'path')
        None
    """
    temp_obj = data_obj
    
    for key in keys:
        if isinstance(temp_obj, dict) and key in temp_obj:
            temp_obj = temp_obj[key]
        elif isinstance(temp_obj, list) and isinstance(key, int) and 0 <= key < len(temp_obj):
            temp_obj = temp_obj[key]
        else:
            return None
    
    return temp_obj


def clean_number(text: Optional[Union[str, int, float]]) -> Optional[float]:
    """
    Extracts and converts numeric value from text.
    
    Handles:
    - Currency symbols ($, €, £, etc.)
    - Thousands separators (commas)
    - Percentage signs
    - Whitespace
    
    Args:
        text: String, number, or None
        
    Returns:
        Float value or None if conversion fails
        
    Examples:
        >>> clean_number("$1,234.56")
        1234.56
        >>> clean_number("50%")
        50.0
        >>> clean_number("invalid")
        None
    """
    if text is None:
        return None
    
    if isinstance(text, (int, float)):
        return float(text)
    
    text_str = str(text).strip()
    if not text_str:
        return None
    
    # Remove currency symbols, commas, percent signs, and spaces
    cleaned = CURRENCY_PATTERN.sub('', text_str)
    
    # Check for empty string after cleaning
    if not cleaned or cleaned in ('.', '-', '+'):
        return None
    
    try:
        # Use NUMBER_PATTERN to find the actual number part in case of extra text
        match = NUMBER_PATTERN.search(cleaned)
        if match:
            return float(match.group(0))
        return None # No number found
    except (ValueError, TypeError):
        logger.debug(f"Failed to convert '{text_str}' to number")
        return None


def parse_proposals_text(text: Optional[str]) -> Tuple[Optional[float], Optional[float], Optional[str]]:
    """
    Parses proposal count text into min/max range.
    
    Handles formats:
    - "10 to 15" -> (10, 15)
    - "5-10" -> (5, 10)
    - "Less than 5" -> (0, 4)
    - "More than 10" -> (11, None) # Changed float('inf') to None for JSON compliance
    - "50+" -> (50, None) # Changed float('inf') to None for JSON compliance
    - "10" -> (10, 10)
    
    Args:
        text: Proposal count text
        
    Returns:
        Tuple of (min, max, original_text)
        min and max are None if parsing fails
        
    Examples:
        >>> parse_proposals_text("10 to 15")
        (10.0, 15.0, "10 to 15")
        >>> parse_proposals_text("Less than 5")
        (0.0, 4.0, "Less than 5")
        >>> parse_proposals_text("50+")
        (50.0, None, "50+")
    """
    if not text:
        return None, None, None
    
    text = text.strip()
    original_text = text
    text_lower = text.lower()
    
    # Precompiled patterns with handlers
    patterns = [
        # "10 to 15" or "10-15"
        (re.compile(r'(\d+)\s*(?:to|-)\s*(\d+)\s*proposals?'), 
         lambda m: (float(m.group(1)), float(m.group(2)))),
        
        # "Less than 5 proposals"
        (re.compile(r'less\s+than\s+(\d+)\s*proposals?'), 
         lambda m: (0.0, float(m.group(1)) - 1)),
        
        # "More than 10 proposals" (returns None for max)
        (re.compile(r'more\s+than\s+(\d+)\s*proposals?'), 
         lambda m: (float(m.group(1)) + 1, None)),
        
        # "50+ proposals" (returns None for max)
        (re.compile(r'^(\d+)\+\s*proposals?$'), 
         lambda m: (float(m.group(1)), None)),
        
        # Just a number "10 proposals"
        (re.compile(r'^(\d+)\s*proposals?$'), 
         lambda m: (float(m.group(1)), float(m.group(1)))),

        # Fallback for just "Less than 5" or "50+" without "proposals"
        (re.compile(r'less\s+than\s+(\d+)'),
         lambda m: (0.0, float(m.group(1)) - 1)),
        (re.compile(r'^(\d+)\+$'),
         lambda m: (float(m.group(1)), None)),
        (re.compile(r'^(\d+)$'),
         lambda m: (float(m.group(1)), float(m.group(1)))),
    ]
    
    for pattern, handler in patterns:
        match = pattern.search(text_lower)
        if match:
            try:
                min_val, max_val = handler(match)
                return min_val, max_val, original_text
            except (ValueError, IndexError) as e:
                logger.debug(f"Error parsing proposals '{text}': {e}")
                continue
    
    logger.debug(f"Unknown proposals text format: '{original_text}'")
    return None, None, original_text


_KNOWN_SKILLS: Optional[set] = None

def _load_known_skills() -> set:
    """
    Loads a predefined list of common tech skills.
    In a real application, this would load from a file or a database.
    For this example, we'll hardcode a small list.
    """
    global _KNOWN_SKILLS
    if _KNOWN_SKILLS is None:
        # Example hardcoded list. In production, load from a data file.
        _KNOWN_SKILLS = {
            "python", "javascript", "react", "node.js", "java", "c++", "c#", "php", "go", "ruby",
            "aws", "azure", "gcp", "docker", "kubernetes", "sql", "nosql", "mongodb", "postgresql",
            "html", "css", "vue.js", "angular", "django", "flask", "spring", "machine learning",
            "ai", "data science", "devops", "cloud computing", "api integration", "web scraping",
            "selenium", "scrapy", "beautifulsoup", "nlp", "computer vision", "ui/ux", "figma",
            "photoshop", "illustrator", "excel", "google sheets", "automation", "zapier", "n8n",
            "rest api", "graphql", "frontend", "backend", "full stack", "mobile development",
            "ios", "android", "unity", "game development", "blockchain", "ethereum", "solidity",
            "testing", "qa", "agile", "scrum", "project management", "technical writing",
            "customer service", "sales", "marketing", "digital marketing", "seo", "sem",
            "social media", "content creation", "copywriting", "business analysis",
            "financial modeling", "accounting", "bookkeeping", "hr", "recruiting",
            "microsoft office", "google workspace", "excel automation", "google apps script",
            "data entry", "virtual assistant", "research", "lead generation",
            "cybersecurity", "network administration", "system administration", "devops engineering",
            "cloud engineering", "erp", "crm", "sap", "salesforce", "api", "etl", "data analysis",
            "data visualization", "tableau", "power bi", "power automate", "power apps",
            "make.com", "monday.com", "notion", "slack", "stripe", "openai", "chatgpt", "midjourney",
            "stable diffusion", "ai agent", "langchain", "llama", "hugging face", "mql5", "ninjatrader",
            "trading automation", "algorithm development", "software development", "web development",
            "mobile development", "data engineering", "database management", "business intelligence",
            "data warehousing", "etl pipelines", "data governance", "data quality", "data modeling",
            "statistical analysis", "predictive modeling", "r", "sas", "spss", "jupyter", "pandas",
            "numpy", "scikit-learn", "tensorflow", "pytorch", "keras", "deep learning", "computer vision",
            "natural language processing", "time series analysis", "big data", "hadoop", "spark", "kafka",
            "data lakes", "data warehouses", "cloud data platforms", "snowflake", "databricks",
            "aws redshift", "google bigquery", "azure synapse", "data privacy", "gdpr", "ccpa",
            "hipaa", "soc 2", "iso 27001", "security audits", "penetration testing", "vulnerability assessment",
            "security incident response", "identity and access management", "active directory",
            "network security", "firewalls", "vpn", "intrusion detection", "endpoint security",
            "threat intelligence", "risk management", "compliance", "regulatory affairs",
            "legal research", "contract review", "litigation support", "patent law", "trademark law",
            "employment law", "corporate law", "tax law", "immigration law", "international law",
            "legal translation", "legal writing", "legal document drafting", "legal technology",
            "legal operations", "project management professional", "pmp", "agile scrum master",
            "safe agile", "lean manufacturing", "six sigma", "process improvement", "business process automation",
            "robotic process automation", "rpa", "uipath", "automation anywhere", "blue prism",
            "business intelligence development", "data warehouse development", "etl development",
            "ssis", "ssas", "ssrs", "power query", "power pivot", "dax", "mdx", "sql server",
            "oracle", "mysql", "mariadb", "sqlite", "nosql databases", "cassandra", "couchbase",
            "redis", "elasticsearch", "solr", "cloud databases", "dynamodb", "cosmos db",
            "aurora", "documentdb", "document database", "graph database", "neo4j", "arangodb",
            "timeseries database", "influxdb", "grafana", "prometheus", "kubernetes administration",
            "docker swarm", "jenkins", "gitlab ci", "github actions", "circleci", "travis ci",
            "azure devops", "aws codepipeline", "google cloud build", "ansible", "puppet", "chef",
            "terraform", "cloudformation", "pulumi", "ci/cd", "continuous integration", "continuous delivery",
            "infrastructure as code", "iac", "containerization", "virtualization", "vmware", "kvm",
            "hyper-v", "cloud architecture", "solution architecture", "enterprise architecture",
            "technical leadership", "mentoring", "coaching", "training", "documentation",
            "confluence", "jira", "asana", "trello", "monday.com", "slack automation",
            "google chat", "microsoft teams", "zoom api", "webex api", "twilio", "nexmo", "sendgrid",
            "mailchimp", "activecampaign", "hubspot", "salesforce crm", "microsoft dynamics",
            "zoho crm", "freshsales", "intercom", "drift", "zendesk", "freshdesk", "gainsight",
            "customer success management", "onboarding", "retention", "churn reduction",
            "customer engagement", "customer journey mapping", "voice of customer", "cx", "ux research",
            "usability testing", "a/b testing", "conversion rate optimization", "cro", "google analytics",
            "google tag manager", "google data studio", "looker studio", "tableau public",
            "power bi desktop", "domo", "qlik sense", "sisense", "periscope data", "mode analytics",
            "mixpanel", "amplitude", "segment", "rudderstack", "customer data platform", "cdp",
            "marketing automation platforms", "crm platforms", ""
        }
    return _KNOWN_SKILLS

def extract_skills_from_text(text: str, min_word_length: int = 2, min_ngram_length: int = 1, max_ngram_length: int = 3) -> list:
    """
    Extracts potential skill keywords and n-grams from text by matching against a known list.
    Prioritizes longer matches.

    Args:
        text: Text to extract skills from
        min_word_length: Minimum word length for consideration if not part of a known skill
        min_ngram_length: Minimum number of words in a skill phrase
        max_ngram_length: Maximum number of words in a skill phrase
        
    Returns:
        List of potential skill keywords
    """
    if not text:
        return []

    # Load known skills once
    known_skills = _load_known_skills()
    text_lower = normalize_whitespace(text).lower()
    
    found_skills = set()

    # Try matching known n-grams (multi-word skills) first, from longest to shortest
    for n in range(max_ngram_length, min_ngram_length - 1, -1):
        words = text_lower.split()
        for i in range(len(words) - n + 1):
            ngram = " ".join(words[i : i + n])
            if ngram in known_skills:
                found_skills.add(ngram)
    
    # Add any remaining single words that are in known skills and not part of an already found n-gram
    remaining_words = set(re.findall(r'\b[a-z0-9][a-z0-9+#.\-]*\b', text_lower))
    for skill_word in remaining_words:
        if skill_word in known_skills and all(skill_word not in fs for fs in found_skills):
            found_skills.add(skill_word)

    return list(found_skills)


def truncate_text(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """
    Truncates text to maximum length with suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to append if truncated
        
    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)].rstrip() + suffix


def normalize_whitespace(text: str) -> str:
    """
    Normalizes whitespace in text.
    
    Replaces multiple spaces/newlines with single space, and strips.
    
    Args:
        text: Text to normalize
        
    Returns:
        Normalized text
    """
    if not text:
        return ""
    
    # Replace multiple whitespace with single space
    return re.sub(r'\s+', ' ', text).strip()
File: upwork_extractor/utils/validation.py
"""
Data validation utilities.

Strict validation functions for critical data fields.
"""

import re
from typing import Optional
from urllib.parse import urlparse
import logging
from datetime import datetime
from bs4 import BeautifulSoup # Import for sanitize_html

logger = logging.getLogger(__name__)

# Validation patterns
# Upwork UID format: ~ followed by 19 or 20 digits (e.g., ~021989059411821975576)
UID_PATTERN = re.compile(r'^~\d{19,20}$')
CURRENCY_CODE_PATTERN = re.compile(r'^[A-Z]{3}$')


def validate_uid(uid: Optional[str], strict: bool = True) -> bool:
    """
    Validates Upwork job UID format.
    
    Expected format: ~ followed by 19 or 20 digits.
    
    Args:
        uid: UID string to validate
        strict: If True, raise ValueError on invalid format
        
    Returns:
        True if valid, False otherwise (in non-strict mode)
        
    Raises:
        ValueError: If strict=True and UID is invalid
        
    Examples:
        >>> validate_uid("~021989059411821975576")
        True
        >>> validate_uid("invalid", strict=False)
        False
    """
    if not uid:
        if strict:
            raise ValueError("UID cannot be empty")
        return False
    
    if not UID_PATTERN.match(uid):
        message = f"Invalid UID format: '{uid}' (expected format: ~ followed by 19-20 digits)"
        if strict:
            raise ValueError(message)
        logger.warning(message)
        return False
    
    return True


def validate_url(url: Optional[str], strict: bool = True) -> bool:
    """
    Validates URL format and optionally checks if it's an Upwork URL.
    
    Args:
        url: URL string to validate
        strict: If True, raise ValueError on invalid format
        
    Returns:
        True if valid, False otherwise (in non-strict mode)
        
    Raises:
        ValueError: If strict=True and URL is invalid
    """
    if not url:
        if strict:
            raise ValueError("URL cannot be empty")
        return False
    
    try:
        parsed = urlparse(url)
        
        # Check for scheme and netloc
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"Invalid URL format: '{url}' (missing scheme or netloc)")
        
        # Only accept http/https schemes
        if parsed.scheme.lower() not in ['http', 'https']:
            raise ValueError(f"Invalid URL scheme: '{parsed.scheme}' for URL '{url}' (must be http or https)")

        # Optionally check if it's an Upwork URL (as a warning, not strict failure)
        if 'upwork.com' not in parsed.netloc.lower():
            logger.warning(f"URL is not from upwork.com: '{url}'")
        
        return True
        
    except Exception as e:
        message = f"URL validation failed: '{url}' - {str(e)}"
        if strict:
            raise ValueError(message) from e
        logger.warning(message)
        return False


def validate_currency_code(code: Optional[str], strict: bool = True) -> bool:
    """
    Validates ISO 4217 currency code format.
    
    Args:
        code: Currency code (e.g., "USD", "EUR")
        strict: If True, raise ValueError on invalid format
        
    Returns:
        True if valid format, False otherwise
        
    Raises:
        ValueError: If strict=True and code is invalid
        
    Examples:
        >>> validate_currency_code("USD")
        True
        >>> validate_currency_code("us", strict=False)
        False
    """
    if not code:
        if strict:
            raise ValueError("Currency code cannot be empty")
        return False
    
    if not CURRENCY_CODE_PATTERN.match(code):
        message = f"Invalid currency code: '{code}' (expected 3 uppercase letters)"
        if strict:
            raise ValueError(message)
        logger.warning(message)
        return False
    
    return True


def validate_date_iso(date_str: Optional[str], strict: bool = True) -> bool:
    """
    Validates ISO 8601 date format.
    
    Args:
        date_str: Date string to validate
        strict: If True, raise ValueError on invalid format
        
    Returns:
        True if valid, False otherwise
        
    Raises:
        ValueError: If strict=True and date is invalid
    """
    if not date_str:
        if strict:
            raise ValueError("Date string cannot be empty")
        return False
    
    try:
        # Handle 'Z' suffix
        iso_str = date_str.replace('Z', '+00:00') if date_str.endswith('Z') else date_str
        datetime.fromisoformat(iso_str)
        return True
    except ValueError as e:
        message = f"Invalid ISO 8601 date: '{date_str}'"
        if strict:
            raise ValueError(message) from e
        logger.warning(message)
        return False


def validate_range(min_val: Optional[float], max_val: Optional[float], strict: bool = True) -> bool:
    """
    Validates that min <= max in a numerical range.
    
    Args:
        min_val: Minimum value
        max_val: Maximum value
        strict: If True, raise ValueError on invalid range
        
    Returns:
        True if valid range, False otherwise
        
    Raises:
        ValueError: If strict=True and range is invalid
    """
    # If one is None, it's considered valid unless both are non-None and min > max
    if min_val is None or max_val is None:
        return True
    
    if min_val > max_val:
        message = f"Invalid range: min ({min_val}) > max ({max_val})"
        if strict:
            raise ValueError(message)
        logger.warning(message)
        return False
    
    return True


def sanitize_html(html_text: str) -> str:
    """
    Removes HTML tags and returns plain text.
    Uses BeautifulSoup for robust HTML parsing.
    
    Args:
        html_text: HTML string
        
    Returns:
        Plain text without HTML tags
    """
    if not html_text:
        return ""
    
    # Use 'lxml' parser for BeautifulSoup for robustness and speed
    soup = BeautifulSoup(html_text, 'lxml')
    return soup.get_text(separator=' ', strip=True)
File: upwork_extractor/init.py
"""
Upwork Job Data Extractor Package

A robust, production-ready system for extracting structured data from Upwork job postings.
Handles both NUXT data (primary source) and HTML fallback with strict validation.

Main Entry Point:
    from upwork_extractor import UpworkDataExtractor
    
    extractor = UpworkDataExtractor(html_content)
    job_data = extractor.extract()
"""

import logging

# Core exports for easy imports
from .extractor import UpworkDataExtractor
from .models import (
    UpworkJobData,
    ExperienceLevel,
    DataSource,
    DataQuality,
    SkillCategory,
)
from .config import ExtractionConfig, ValidationLevel
from .exceptions import (
    ExtractionError,
    NuxtParsingError,
    ValidationError,
    CriticalDataMissingError,
    HTMLParsingError,
    SchemaValidationError,
)
from .mappers import job_data_to_normalized_dict # New export

# Package metadata
__version__ = "2.0.0"
__author__ = "Upwork Extractor Team"
__license__ = "MIT"

# Configure package-level logger (no handlers, let application configure)
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

__all__ = [
    "UpworkDataExtractor",
    "UpworkJobData",
    "ExperienceLevel",
    "DataSource",
    "DataQuality",
    "SkillCategory",
    "ExtractionConfig",
    "ValidationLevel",
    "ExtractionError",
    "NuxtParsingError",
    "ValidationError",
    "CriticalDataMissingError",
    "HTMLParsingError",
    "SchemaValidationError",
    "job_data_to_normalized_dict", # Export new mapper
]
File: upwork_extractor/config.py
"""
Configuration classes for the extractor.
Allows customization of extraction behavior, validation rules, and output format.
"""

from dataclasses import dataclass, field
from typing import List
from enum import Enum


class ValidationLevel(str, Enum):
    """Validation strictness levels."""
    STRICT = "strict"  # Raise exceptions on validation failures
    NORMAL = "normal"  # Log warnings but continue
    PERMISSIVE = "permissive"  # Silently continue


@dataclass
class ExtractionConfig:
    """
    Configuration for data extraction behavior.
    
    Attributes:
        validation_level: Strictness of data validation
        extract_schema_org: Whether to parse Schema.org JSON-LD for validation
        extract_similar_jobs: Include similar job postings
        extract_other_client_jobs: Include other jobs by same client
        filter_current_job_from_other_jobs: Remove current job from "other jobs" list
        preserve_skill_hierarchy: Keep parent-child skill relationships
        store_raw_dates: Store original date strings alongside parsed ISO dates
        critical_fields: Fields that must exist for extraction to succeed (by UpworkJobData attribute path)
        important_fields: Fields that trigger warnings if missing but don't fail extraction
    """
    
    validation_level: ValidationLevel = ValidationLevel.STRICT
    extract_schema_org: bool = True
    extract_similar_jobs: bool = True
    extract_other_client_jobs: bool = True
    filter_current_job_from_other_jobs: bool = True
    preserve_skill_hierarchy: bool = True
    store_raw_dates: bool = True # Flag to decide if raw dates should be stored alongside parsed ISO dates

    # Critical fields that must exist for extraction to succeed
    # These are paths to attributes in the UpworkJobData model
    critical_fields: List[str] = field(default_factory=lambda: ["title", "description", "uid", "job_details.posted_date"])
    
    # Optional fields that trigger warnings if missing but don't fail extraction
    important_fields: List[str] = field(default_factory=lambda: [
        "url", "job_details.experience_level", "job_details.budget.hourly_min",
        "job_details.category.name", "client.location.country", "client.stats.total_spent",
        "activity.proposals.max"
    ])


# Default configuration instance
DEFAULT_CONFIG = ExtractionConfig()
File: upwork_extractor/exceptions.py
"""
Custom exceptions for the Upwork extractor package.
Provides granular error handling for different failure scenarios.
"""
from typing import Any, List, Optional

class ExtractionError(Exception):
    """Base exception for all extraction-related errors."""
    pass


class NuxtParsingError(ExtractionError):
    """Raised when NUXT_DATA__ JSON parsing fails."""
    
    def __init__(self, message: str, raw_content: str = None):
        super().__init__(message)
        self.raw_content = raw_content


class HTMLParsingError(ExtractionError):
    """Raised when HTML parsing encounters critical errors."""
    pass


class ValidationError(ExtractionError):
    """Raised when data validation fails (strict mode)."""
    
    def __init__(self, field_name: str, value, reason: str):
        self.field_name = field_name
        self.value = value
        self.reason = reason
        super().__init__(f"Validation failed for '{field_name}': {reason} (value: {value})")


class CriticalDataMissingError(ExtractionError):
    """Raised when critical fields (title, description) are missing."""
    
    def __init__(self, missing_fields: List[str]):
        self.missing_fields = missing_fields
        super().__init__(f"Critical fields missing: {', '.join(missing_fields)}")


class SchemaValidationError(ExtractionError):
    """Raised when Schema.org JSON-LD validation detects mismatches."""
    
    def __init__(self, field_name: str, expected: Any, actual: Any, source: str, message: Optional[str] = None):
        self.field_name = field_name
        self.expected = expected
        self.actual = actual
        self.source = source
        if message:
            super().__init__(message)
        else:
            super().__init__(
                f"Schema validation mismatch in '{field_name}': "
                f"expected {expected}, got {actual} from {source}"
            )
File: upwork_extractor/extractor.py
"""
Main extractor orchestration.

Coordinates NUXT, HTML, and Schema.org parsers to extract complete job data.
Implements hybrid extraction strategy with validation and quality tracking.
"""

import json
import logging
from typing import Optional, Any
from bs4 import BeautifulSoup

from .models import UpworkJobData, DataSource
from .models.quality import DataQuality
from .models.enums import ProjectType # Added import
from .parsers import NuxtParser, HtmlParser, SchemaParser, selectors
from .config import ExtractionConfig, DEFAULT_CONFIG, ValidationLevel
from .exceptions import (
    NuxtParsingError,
    HTMLParsingError,
    ValidationError,
    CriticalDataMissingError,
    SchemaValidationError,
)
from .mappers import job_data_to_normalized_dict # Added import
from .utils.text_utils import get_nested_safe # For checking nested critical fields

logger = logging.getLogger(__name__)


class UpworkDataExtractor:
    """
    Main extraction orchestrator for Upwork job data.
    
    Coordinates multiple data sources (NUXT, HTML, Schema.org) with priority-based
    merging and comprehensive validation.
    
    Usage:
        extractor = UpworkDataExtractor(html_content, config)
        job_data = extractor.extract()
    """
    
    def __init__(
        self,
        html_content: str,
        config: Optional[ExtractionConfig] = None
    ):
        """
        Initialize extractor with HTML content.
        
        Args:
            html_content: Raw HTML content from Upwork job page
            config: Optional extraction configuration (uses defaults if None)
        """
        self.html_content = html_content
        self.config = config or DEFAULT_CONFIG
        self.data_quality = DataQuality()
        
        # Validate config field paths upfront
        self._validate_config_field_paths()

        # Parse HTML once
        try:
            self.soup = BeautifulSoup(html_content, 'lxml') # Use lxml for better performance and robustness
        except Exception as e:
            raise HTMLParsingError(f"Failed to parse HTML: {str(e)}") from e
        
        # Initialize parsers (will be populated during extraction)
        self.nuxt_parser: Optional[NuxtParser] = None
        self.html_parser: Optional[HtmlParser] = None
        self.schema_parser: Optional[SchemaParser] = None
        
        # Track data sources used
        self.nuxt_available = False
        self.schema_available = False
        
        logger.info("UpworkDataExtractor initialized")

    def _validate_config_field_paths(self):
        """
        Ensures all field paths in the config's critical_fields and important_fields
        are valid attributes of the UpworkJobData model.
        """
        # Create a dummy UpworkJobData instance to introspect paths
        # This assumes the base model can be initialized, even with dummy data.
        dummy_job_data = UpworkJobData(title="dummy", description="dummy", data_source=DataSource.NUXT_DATA)

        all_field_paths = self.config.critical_fields + self.config.important_fields
        for path_str in all_field_paths:
            current_obj: Any = dummy_job_data
            path_parts = path_str.split('.')
            is_valid_path = True
            for part in path_parts:
                if isinstance(current_obj, UpworkJobData.__class__): # If it's the class itself
                    # Check if 'part' is a field in the model, or a nested model
                    if part not in current_obj.model_fields:
                        is_valid_path = False
                        break
                    # For nested models, get their type to continue validation
                    field_info = current_obj.model_fields[part]
                    if hasattr(field_info.annotation, '__origin__') and field_info.annotation.__origin__ in (list, dict, Optional):
                        # For complex types, we just check existence and assume validity down the line.
                        # Can be improved by introspecting the generic arguments if needed.
                        pass
                    else:
                        current_obj = field_info.annotation # Move to the nested model type for next part
                elif isinstance(current_obj, type(None)): # Reached a None in the path
                    is_valid_path = False
                    break
                elif hasattr(current_obj, part): # If it's an instance of a model
                    current_obj = getattr(current_obj, part)
                else:
                    is_valid_path = False
                    break
            
            if not is_valid_path:
                raise ValueError(
                    f"Invalid field path in ExtractionConfig: '{path_str}'. "
                    f"Please check the path against the UpworkJobData model structure."
                )
        logger.debug("ExtractionConfig field paths validated successfully.")
    
    def extract(self) -> UpworkJobData:
        """
        Performs complete data extraction.
        
        Extraction strategy:
        1. Parse NUXT_DATA__ (primary source)
        2. Parse HTML elements (fallback/enrichment)
        3. Parse Schema.org JSON-LD (validation)
        4. Validate and merge data
        5. Return complete UpworkJobData
        
        Returns:
            UpworkJobData instance with all extracted data
            
        Raises:
            CriticalDataMissingError: If critical fields are missing (strict mode)
            ValidationError: If validation fails (strict mode)
            ExtractionError: For other critical failures
        """
        logger.info("Starting data extraction")
        
        # Step 1: Extract NUXT data (primary source)
        job_data = self._extract_from_nuxt()
        
        # Step 2: Enrich/fallback with HTML data
        self._enrich_from_html(job_data)
        
        # Step 3: Extract and validate with Schema.org
        if self.config.extract_schema_org:
            self._validate_with_schema(job_data)
        
        # Step 4: Determine primary data source
        job_data.data_source = self._determine_data_source()
        
        # Step 5: Final validation
        self._validate_final_data(job_data)
        
        # Step 6: Convert DataQuality to dict for serialization
        job_data.data_quality = self.data_quality.to_dict()
        
        logger.info(f"Extraction complete. Source: {job_data.data_source}, "
                   f"Quality: {self.data_quality.get_summary()}")
        
        return job_data
    
    def _extract_from_nuxt(self) -> UpworkJobData:
        """
        Extracts data from NUXT_DATA__ script tag.
        
        Returns:
            UpworkJobData instance with NUXT data (may be incomplete)
        """
        # Initialize with minimal data
        job_data = UpworkJobData(
            title="",  # Initialize with empty string
            description="",  # Initialize with empty string
            data_source=DataSource.NUXT_DATA # Will be updated later
        )
        
        try:
            # Find NUXT_DATA__ script tag
            nuxt_script = self.soup.find(**selectors.NUXT_DATA_SCRIPT_SELECTOR)
            
            if not nuxt_script or not nuxt_script.string:
                logger.warning("NUXT_DATA__ script tag not found")
                self.data_quality.add_warning(
                    "NUXT_DATA__ not found, using HTML-only extraction",
                    'nuxt_data'
                )
                return job_data
            
            # Parse JSON
            try:
                nuxt_array = json.loads(nuxt_script.string)
                if not isinstance(nuxt_array, list): # Root is usually a list, but can be a dict in some cases
                    # If it's not a list, it might be the top-level state object directly
                    if isinstance(nuxt_array, dict) and ('state' in nuxt_array or 'data' in nuxt_array):
                        logger.debug("NUXT_DATA__ is a dictionary, attempting to process as a list containing it.")
                        # Wrap in a list to satisfy NuxtParser's constructor expecting a list
                        nuxt_array = [nuxt_array]
                    else:
                        raise ValueError("NUXT_DATA__ is not a list or recognizable dictionary structure.")
                
                logger.info(f"Parsed NUXT_DATA__ array with {len(nuxt_array)} items (or derived length)")
                logger.debug(f"Raw NUXT array sample: {json.dumps(nuxt_array, indent=2)[:1000]}...") # Log first 1000 chars
                self.nuxt_available = True
                
            except json.JSONDecodeError as e:
                raise NuxtParsingError(
                    f"Failed to parse NUXT_DATA__ JSON: {str(e)}",
                    nuxt_script.string[:500] if nuxt_script.string else None
                ) from e
            except ValueError as e:
                raise NuxtParsingError(
                    f"Invalid NUXT_DATA__ structure: {str(e)}",
                    nuxt_script.string[:500] if nuxt_script.string else None
                ) from e

            # Initialize NUXT parser
            self.nuxt_parser = NuxtParser(nuxt_array, self.data_quality)
            
            # Extract core structures
            job_obj = self.nuxt_parser.find_job_data()
            client_obj = self.nuxt_parser.find_client_data()
            sands_obj = self.nuxt_parser.find_skills_ontology()
            seo_obj = self.nuxt_parser.find_seo_data()
            slug_obj = self.nuxt_parser.find_job_slug()
            
            # Populate data from NUXT objects
            if job_obj:
                self.nuxt_parser.populate_job_data(job_obj, job_data)
                logger.debug("Populated job data from NUXT")
            else:
                logger.warning("Job data object not found in NUXT")
                self.data_quality.add_warning("Job object not found in NUXT", 'nuxt_job')
            
            if client_obj:
                self.nuxt_parser.populate_client_data(client_obj, job_data)
                logger.debug("Populated client data from NUXT")
            else:
                logger.warning("Client data object not found in NUXT")
                self.data_quality.add_warning("Client object not found in NUXT", 'nuxt_client')
            
            if sands_obj and self.config.preserve_skill_hierarchy:
                self.nuxt_parser.populate_skills_ontology(sands_obj, job_data)
                logger.debug("Populated skills ontology from NUXT")
            else:
                if self.config.preserve_skill_hierarchy:
                    self.data_quality.add_warning("Skills ontology (sands) object not found in NUXT", 'nuxt_skills_ontology')
            
            if seo_obj:
                # SEO data can provide URL and validate title/description
                if not job_data.url and seo_obj.get('url'):
                    job_data.url = seo_obj['url']
                    self.data_quality.set_source('url', 'nuxt_seo')
            
            if slug_obj:
                self.nuxt_parser.populate_job_slug(slug_obj, job_data)
            
            # Extract related jobs if configured
            if self.config.extract_other_client_jobs:
                other_jobs = self.nuxt_parser.find_other_jobs()
                if other_jobs:
                    # Filter out current job if configured
                    if self.config.filter_current_job_from_other_jobs and job_data.uid:
                        current_uid_clean = job_data.uid.replace('~', '')
                        other_jobs = [
                            job for job in other_jobs
                            if str(job.get('uid', '')).replace('~', '') != current_uid_clean
                        ]
                    job_data.other_jobs_by_client = other_jobs
                    self.data_quality.set_source('other_jobs', 'nuxt')
            
            if self.config.extract_similar_jobs:
                similar_jobs = self.nuxt_parser.find_similar_jobs()
                if similar_jobs:
                    job_data.similar_jobs = similar_jobs
                    self.data_quality.set_source('similar_jobs', 'nuxt')
            
        except NuxtParsingError:
            # Re-raise NUXT parsing errors
            raise
        except Exception as e:
            # Log unexpected errors but continue with HTML extraction
            logger.error(f"Unexpected error during NUXT extraction: {e}", exc_info=True)
            self.data_quality.add_warning(
                f"NUXT extraction failed: {str(e)}",
                'nuxt_extraction'
            )
        
        return job_data
    
    def _enrich_from_html(self, job_data: UpworkJobData):
        """
        Enriches data with HTML extraction.
        
        Args:
            job_data: UpworkJobData instance to enrich
        """
        try:
            self.html_parser = HtmlParser(self.soup, self.data_quality)
            self.html_parser.populate_job_data(job_data)
            logger.debug("Enriched data from HTML")
            
        except Exception as e:
            logger.error(f"HTML extraction failed: {e}", exc_info=True)
            self.data_quality.add_warning(
                f"HTML extraction failed: {str(e)}",
                'html_extraction'
            )
            
            # In strict mode, if HTML is the *only* source and it fails, raise.
            # Otherwise, just log a warning and continue.
            if self.config.validation_level == ValidationLevel.STRICT and not self.nuxt_available:
                raise HTMLParsingError(f"HTML extraction failed and NUXT data was unavailable: {str(e)}") from e
    
    def _validate_with_schema(self, job_data: UpworkJobData):
        """
        Validates extracted data against Schema.org JSON-LD.
        
        Args:
            job_data: UpworkJobData instance to validate
        """
        try:
            self.schema_parser = SchemaParser(self.soup, self.data_quality)
            schema_data = self.schema_parser.extract_schema_data()
            
            if schema_data:
                self.schema_available = True
                
                # Convert job_data to dict for validation
                # Use a specific mapper for Schema validation as it's the target structure
                # The .to_normalized_dict is now an external mapper function
                extracted_dict = job_data_to_normalized_dict(job_data)
                
                # Validate against NUXT/HTML data
                source = 'nuxt' if self.nuxt_available else 'html'
                mismatches = self.schema_parser.validate_against_extracted(
                    extracted_dict,
                    source
                )
                
                if mismatches:
                    logger.warning(f"Found {len(mismatches)} Schema.org validation mismatches")
                    if self.config.validation_level == ValidationLevel.STRICT:
                        # Aggregate error messages for the SchemaValidationError exception
                        error_details = [f"{m.field_name}: Schema='{m.schema_value}', Extracted='{m.extracted_value}' (Source: {m.source})" for m in mismatches]
                        raise SchemaValidationError(
                            field_name="multiple_fields",
                            expected="matches Schema.org",
                            actual="mismatches found",
                            source=source,
                            message=f"Schema.org validation detected {len(mismatches)} mismatches. Details: {'; '.join(error_details)}"
                        )
                else:
                    logger.info("Schema.org validation passed")
                
                # Store schema summary in metadata
                self.data_quality.extraction_metadata['schema_summary'] = \
                    self.schema_parser.get_schema_summary()
            
        except SchemaValidationError:
            raise # Re-raise if strict
        except Exception as e:
            logger.warning(f"Schema.org validation failed: {e}", exc_info=True)
            self.data_quality.add_warning(
                f"Schema.org validation failed: {str(e)}",
                'schema_validation'
            )
    
    def _determine_data_source(self) -> DataSource:
        """
        Determines primary data source used.
        
        Returns:
            DataSource enum value
        """
        if self.nuxt_available and self.html_parser and self.data_quality.source_coverage:
            # Check if HTML actually contributed anything
            html_contributed = any(source == 'html' for source in self.data_quality.source_coverage.values())
            if html_contributed:
                return DataSource.HYBRID
            else:
                return DataSource.NUXT_DATA # NUXT was primary, HTML didn't add new info
        elif self.nuxt_available:
            return DataSource.NUXT_DATA
        elif self.html_parser and self.data_quality.source_coverage:
            # Check if HTML parser actually found any data
            html_contributed = any(source == 'html' for source in self.data_quality.source_coverage.values())
            if html_contributed:
                return DataSource.HTML_ELEMENTS
            else:
                # This case indicates HTML parser ran but found nothing.
                # It means the page was likely empty or not a job page
                logger.warning("HTML parser found no relevant data.")
                return DataSource.HTML_ELEMENTS # Still consider HTML as attempt source
        else:
            return DataSource.HTML_ELEMENTS  # Default fallback if no data found/parsers ran
    
    def _validate_final_data(self, job_data: UpworkJobData):
        """
        Performs final validation on extracted data.
        
        Args:
            job_data: UpworkJobData instance to validate
            
        Raises:
            CriticalDataMissingError: If critical fields are missing (strict mode)
            ValidationError: If validation fails (strict mode)
        """
        # Check critical fields
        missing_critical = []
        for field_path in self.config.critical_fields:
            # Use get_nested_safe to check for deeply nested fields
            field_value = get_nested_safe(job_data, *field_path.split('.'))
            if field_value is None or (isinstance(field_value, (str, list, dict)) and not field_value): # Also check for empty lists/dicts
                missing_critical.append(field_path)
        
        if missing_critical:
            message = f"Critical fields missing: {', '.join(missing_critical)}"
            
            if self.config.validation_level == ValidationLevel.STRICT:
                raise CriticalDataMissingError(missing_critical)
            elif self.config.validation_level == ValidationLevel.NORMAL:
                logger.error(message)
                self.data_quality.add_validation_issue(
                    'critical_fields',
                    missing_critical,
                    message,
                    'error'
                )
            else:  # PERMISSIVE
                logger.warning(message)
                self.data_quality.add_warning(message, 'critical_fields')
        
        # Check important fields
        missing_important = []
        for field_path in self.config.important_fields:
            field_value = get_nested_safe(job_data, *field_path.split('.'))
            if field_value is None or (isinstance(field_value, (str, list, dict)) and not field_value):
                missing_important.append(field_path)
        
        if missing_important:
            message = f"Important fields missing: {', '.join(missing_important)}"
            logger.warning(message)
            self.data_quality.add_warning(message, 'important_fields')
        
        # Validate data integrity (Pydantic's internal validation handles basic types/enums)
        # This is for cross-field or more complex business logic checks
        self._validate_data_integrity(job_data)
        
        # Check for errors in strict mode
        if self.config.validation_level == ValidationLevel.STRICT:
            if self.data_quality.has_errors():
                # Aggregate error messages for the ValidationError exception
                error_details = [f"{i.field_name}: {i.reason} (value: {i.value})" 
                                 for i in self.data_quality.validation_issues if i.severity == 'error']
                raise ValidationError(
                    'data_validation',
                    None,
                    f"Validation errors found: {len(error_details)}. Details: {'; '.join(error_details)}"
                )
        
        # Log summary
        summary = self.data_quality.get_summary()
        logger.info(
            f"Validation complete - "
            f"Errors: {summary['error_count']}, "
            f"Warnings: {summary['warning_count']}, "
            f"Fields extracted: {summary['fields_extracted']}"
        )
    
    def _validate_data_integrity(self, job_data: UpworkJobData):
        """
        Validates data integrity (ranges, formats, etc.).
        This extends Pydantic's own validators with custom logic.
        
        Args:
            job_data: UpworkJobData instance to validate
        """
        # Pydantic's validators (like @validator('uid')) are already called on model creation.
        # This function adds additional cross-field or custom logic.
        
        # Validate hourly rate range
        budget = job_data.job_details.budget
        if budget.hourly_min is not None and budget.hourly_max is not None:
            if budget.hourly_min > budget.hourly_max:
                self.data_quality.add_validation_issue(
                    'hourly_rate',
                    f"{budget.hourly_min}-{budget.hourly_max}",
                    "Min hourly rate is greater than max",
                    'warning'
                )
        
        # Validate proposal range
        activity_proposals = job_data.activity.proposals
        if activity_proposals:
            if activity_proposals.min is not None and activity_proposals.max is not None:
                if activity_proposals.min > activity_proposals.max:
                    self.data_quality.add_validation_issue(
                        'proposals',
                        f"{activity_proposals.min}-{activity_proposals.max}",
                        "Min proposals is greater than max",
                        'warning'
                    )
        
        # Check for both fixed and hourly budget (flag as quality issue)
        if budget.amount is not None and \
           (budget.hourly_min is not None or budget.hourly_max is not None):
            self.data_quality.add_validation_issue(
                'budget',
                'mixed',
                "Job has both fixed budget and hourly rate",
                'info'
            )

        # Validate budget amount based on project type
        if job_data.job_details.project_type == ProjectType.ONE_TIME: # Fixed cost
            if budget.amount is None or budget.amount <= 0:
                self.data_quality.add_validation_issue(
                    'budget_amount',
                    budget.amount,
                    "Fixed-cost project must have a positive budget amount",
                    'warning' if self.config.validation_level == ValidationLevel.NORMAL else 'info'
                )
        elif job_data.job_details.project_type == ProjectType.ONGOING: # Hourly
            # For hourly projects, `amount` should typically be 0 or None, not a large value
            if budget.amount is not None and budget.amount > 0:
                self.data_quality.add_validation_issue(
                    'budget_amount',
                    budget.amount,
                    "Hourly project has a fixed budget amount specified (unexpected)",
                    'warning' if self.config.validation_level == ValidationLevel.NORMAL else 'info'
                )
File: upwork_extractor/main.py
"""
CLI entry point for Upwork data extractor.

Provides command-line interface for extracting job data from HTML files.
"""

import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Optional

from . import __version__
from .extractor import UpworkDataExtractor
from .config import ExtractionConfig, ValidationLevel
from .exceptions import (
    ExtractionError,
    CriticalDataMissingError,
    ValidationError,
    NuxtParsingError,
    HTMLParsingError,
    SchemaValidationError,
)
from .mappers import job_data_to_normalized_dict


# Configure logging
def setup_logging(verbose: bool = False, log_file: Optional[str] = None):
    """
    Sets up logging configuration.
    
    Args:
        verbose: Enable verbose (DEBUG) logging
        log_file: Optional log file path
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    # Format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Handlers
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
    
    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=handlers
    )
    
    # Set level for the upwork_extractor package
    logging.getLogger('upwork_extractor').setLevel(level)


def print_summary(job_data):
    """
    Prints extraction summary to console.
    
    Args:
        job_data: UpworkJobData instance
    """
    print(f"\n{'='*70}")
    print(f"{'UPWORK JOB DATA EXTRACTION REPORT':^70}")
    print(f"{'='*70}")
    
    # Core info
    print(f"\nJob Title: {job_data.title}")
    print(f"Job UID: {job_data.uid or 'N/A'}")
    print(f"Job URL: {job_data.url or 'N/A'}")
    
    # Job details
    print(f"\nExperience Level: {job_data.job_details.experience_level.value if job_data.job_details.experience_level else 'N/A'}")
    print(f"Project Type: {job_data.job_details.project_type.value if job_data.job_details.project_type else 'N/A'}")
    print(f"Duration: {job_data.job_details.duration or 'N/A'} ({job_data.job_details.duration_weeks or '?'} weeks)")
    print(f"Workload: {job_data.job_details.workload or 'N/A'}")
    print(f"Posted: {job_data.job_details.posted_date or job_data.job_details.posted_date_raw or 'N/A'}")
    print(f"Remote Job: {'Yes' if job_data.job_details.remote_job else 'No'}")
    
    # Budget
    budget = job_data.job_details.budget
    if budget.amount:
        print(f"Fixed Budget: {budget.currency_code or ''} {budget.amount}")
    if budget.hourly_min is not None or budget.hourly_max is not None:
        min_rate = budget.hourly_min if budget.hourly_min is not None and budget.hourly_min != float('inf') else '?'
        max_rate = budget.hourly_max if budget.hourly_max is not None and budget.hourly_max != float('inf') else '?'
        currency = budget.currency_code or 'USD'
        print(f"Hourly Rate: {currency} {min_rate} - {max_rate}")
    if budget.weekly_retainer is not None:
        print(f"Weekly Retainer: {budget.currency_code or 'USD'} {budget.weekly_retainer}")
    print(f"Budget Type: {budget.budget_type.value if budget.budget_type else 'N/A'}")
    
    # Skills
    print(f"\nSkills ({len(job_data.skills)}):")
    if job_data.skills:
        # Group by category
        by_category = {}
        for skill in job_data.skills:
            cat = skill.category.value if skill.category else 'other'
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(skill.name)
        
        for category, skills in sorted(by_category.items()):
            print(f"  {category.upper()}: {', '.join(skills[:5])}")
            if len(skills) > 5:
                print(f"    ... and {len(skills) - 5} more")
    
    # Client
    client = job_data.client
    print("\nClient Information:")
    print(f"  Location: {client.location.city or ''}, {client.location.country or 'N/A'} (Local Time: {client.location.local_time or 'N/A'})")
    print(f"  Company: {client.company.name or 'N/A'} (Industry: {client.company.industry or 'N/A'}, Size: {client.company.size or 'N/A'})")
    print(f"  Member Since: {client.member_since or client.member_since_raw or 'N/A'}")
    print(f"  Total Spent: {client.stats.total_spent or 'N/A'}")
    print(f"  Total Hires: {client.stats.total_hires or 'N/A'} ({client.stats.active_hires or '0'} active)")
    print(f"  Payment Verified: {'Yes' if client.payment_verified else 'No'}")
    
    # Activity
    activity = job_data.activity
    print("\nActivity Metrics:")
    if activity.proposals:
        min_p = int(activity.proposals.min) if activity.proposals.min is not None and activity.proposals.min != float('inf') else '?'
        max_p = int(activity.proposals.max) if activity.proposals.max is not None and activity.proposals.max != float('inf') else '?'
        print(f"  Proposals: {min_p} - {max_p} ({activity.proposals_text or 'N/A'})")
    print(f"  Interviewing: {activity.interviewing or 0}")
    print(f"  Invites Sent: {activity.invites_sent or 0}")
    print(f"  Unanswered Invites: {activity.unanswered_invites or 0}")
    print(f"  Last Buyer Activity: {activity.last_buyer_activity or activity.last_buyer_activity_raw or 'N/A'}")
    
    # Metadata
    print(f"\n{'~'*70}")
    print(f"Data Source: {job_data.data_source.value}")
    print(f"Extracted At: {job_data.extracted_at}")
    
    # Data Quality
    if job_data.data_quality:
        quality = job_data.data_quality
        summary = quality.get('summary', {})
        
        print("\nData Quality:")
        print(f"  Fields Extracted: {summary.get('fields_extracted', 0)}")
        print(f"  Warnings: {summary.get('total_warnings', 0)}")
        print(f"  Errors: {summary.get('error_count', 0)}")
        print(f"  Schema Mismatches: {summary.get('schema_mismatches', 0)}")
        
        # Show warnings if any
        if quality.get('warnings'):
            print("\n  ⚠️  Warnings:")
            for warning in quality['warnings'][:5]:  # Show first 5
                print(f"    • {warning}")
            if len(quality['warnings']) > 5:
                print(f"    ... and {len(quality['warnings']) - 5} more")
        
        # Show errors if any
        if quality.get('validation_issues'):
            errors = [i for i in quality['validation_issues'] if i['severity'] == 'error']
            if errors:
                print("\n  ❌ Errors:")
                for error in errors[:3]:
                    print(f"    • {error['field_name']}: {error['reason']} (Value: {error['value']})")
                if len(errors) > 3:
                    print(f"    ... and {len(errors) - 3} more")
        
        if quality.get('schema_mismatches'):
            schema_mismatches = quality['schema_mismatches']
            if schema_mismatches:
                print("\n  ⚠️ Schema.org Mismatches:")
                for mismatch in schema_mismatches[:3]:
                    print(f"    • {mismatch['field_name']}: Schema='{mismatch['schema_value']}', Extracted='{mismatch['extracted_value']}' (Source: {mismatch['source']})")
                if len(schema_mismatches) > 3:
                    print(f"    ... and {len(schema_mismatches) - 3} more")
    
    print(f"\n{'='*70}\n")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Extract structured data from Upwork job posting HTML',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic extraction
  python -m upwork_extractor.main job.html
  
  # Save to specific output file
  python -m upwork_extractor.main job.html -o output.json
  
  # Verbose logging with database-normalized output
  python -m upwork_extractor.main job.html -v --normalized
  
  # Permissive validation (continue on errors)
  python -m upwork_extractor.main job.html --validation permissive
        """
    )
    
    # Arguments
    parser.add_argument(
        'html_file',
        type=str,
        help='Path to Upwork job HTML file'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        default='upwork_job_data.json',
        help='Output JSON file path (default: upwork_job_data.json)'
    )
    
    parser.add_argument(
        '--normalized',
        action='store_true',
        help='Output database-normalized format (flat structure)'
    )
    
    parser.add_argument(
        '--validation',
        type=str,
        choices=['strict', 'normal', 'permissive'],
        default='strict',
        help='Validation level (default: strict)'
    )
    
    parser.add_argument(
        '--no-schema',
        action='store_true',
        help='Skip Schema.org validation'
    )
    
    parser.add_argument(
        '--no-similar-jobs',
        action='store_true',
        help='Skip extracting similar jobs'
    )
    
    parser.add_argument(
        '--no-other-jobs',
        action='store_true',
        help='Skip extracting other client jobs'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--log-file',
        type=str,
        help='Write logs to file'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version=f'Upwork Extractor v{__version__}'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose, args.log_file)
    logger = logging.getLogger(__name__)
    
    logger.info(f"Upwork Data Extractor v{__version__}")
    logger.info(f"Processing: {args.html_file}")
    
    # Validate input file
    html_path = Path(args.html_file)
    if not html_path.exists():
        print(f"❌ Error: HTML file not found: {args.html_file}", file=sys.stderr)
        sys.exit(1)
    
    # Read HTML content
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        logger.info(f"Read {len(html_content)} bytes from {args.html_file}")
    except Exception as e:
        print(f"❌ Error reading file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Configure extraction
    config = ExtractionConfig(
        validation_level=ValidationLevel(args.validation),
        extract_schema_org=not args.no_schema,
        extract_similar_jobs=not args.no_similar_jobs,
        extract_other_client_jobs=not args.no_other_jobs,
    )
    
    # Extract data
    try:
        print("Extracting data... ", end="", flush=True)
        extractor = UpworkDataExtractor(html_content, config)
        job_data = extractor.extract()
        print("Done.")
        
        logger.info("✅ Extraction successful")
        
        # Print summary
        print_summary(job_data)
        
        # Prepare output
        if args.normalized:
            # Use the new mapper function
            output_data = job_data_to_normalized_dict(job_data)
        else:
            output_data = job_data.model_dump(by_alias=True, exclude_none=False) # Use model_dump
        
        # Write to file
        output_path = Path(args.output)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False, default=str) # default=str to handle datetime objects
        
        print(f"✅ Data saved to: {output_path}")
        print(f"📊 Output format: {'Normalized (database-ready)' if args.normalized else 'Standard'}")
        
        # Exit code based on data quality
        if job_data.data_quality:
            summary = job_data.data_quality.get('summary', {})
            if summary.get('error_count', 0) > 0:
                logger.warning("Extraction completed with errors. Exiting with code 2.")
                sys.exit(2)
            elif summary.get('warning_count', 0) > 0 or summary.get('schema_mismatches', 0) > 0:
                logger.info("Extraction completed with warnings. Exiting with code 0.")
                sys.exit(0) # Not an error, but worth noting
        
        sys.exit(0)
        
    except CriticalDataMissingError as e:
        print(f"\n❌ Critical data missing: {e}", file=sys.stderr)
        logger.error(f"Critical data missing: {e}")
        sys.exit(3)
        
    except ValidationError as e:
        print(f"\n❌ Validation failed: {e}", file=sys.stderr)
        logger.error(f"Validation failed: {e}")
        sys.exit(4)
    
    except NuxtParsingError as e:
        print(f"\n❌ NUXT Parsing Error: {e}", file=sys.stderr)
        logger.error(f"NUXT Parsing Error: {e}", exc_info=True)
        sys.exit(5)

    except HTMLParsingError as e:
        print(f"\n❌ HTML Parsing Error: {e}", file=sys.stderr)
        logger.error(f"HTML Parsing Error: {e}", exc_info=True)
        sys.exit(6)

    except SchemaValidationError as e:
        print(f"\n❌ Schema.org Validation Error: {e}", file=sys.stderr)
        logger.error(f"Schema.org Validation Error: {e}", exc_info=True)
        sys.exit(7)
        
    except ExtractionError as e:
        print(f"\n❌ General Extraction error: {e}", file=sys.stderr)
        logger.error(f"General Extraction error: {e}", exc_info=True)
        sys.exit(8) # Catch other specific ExtractionError types
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}", file=sys.stderr)
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(99)


if __name__ == '__main__':
    main()
File: upwork_extractor/mappers.py
"""
Mapper functions for converting UpworkJobData to various normalized formats.
This module helps to separate transformation logic from the core data models.
"""

from typing import Any, Dict
from .models import UpworkJobData

def job_data_to_normalized_dict(job_data: UpworkJobData) -> Dict[str, Any]:
    """
    Converts a UpworkJobData model instance into a flattened, database-friendly
    normalized dictionary structure.

    Args:
        job_data: The UpworkJobData model instance to convert.

    Returns:
        A dictionary representing the flattened job data.
    """
    # Use model_dump to get a dictionary representation, excluding None values
    # and converting by alias if specified in the models.
    data = job_data.model_dump(exclude_none=True, by_alias=True)

    # Helper for safe nested dict access
    def get_nested_val(d: Dict[str, Any], *keys: str) -> Any:
        temp_obj = d
        for key in keys:
            if isinstance(temp_obj, dict) and key in temp_obj:
                temp_obj = temp_obj.get(key)
            else:
                return None
        return temp_obj

    normalized = {
        # Job core
        'job_uid': data.get('uid'),
        'job_title': data.get('title'),
        'job_description': data.get('description'),
        'job_url': str(data.get('url')) if data.get('url') else None,
        'job_ciphertext': data.get('ciphertext'),
        'job_status_code': data.get('status'),
        'job_access_code': data.get('access'),
        
        # Job details
        'experience_level': get_nested_val(data, 'job_details', 'experience_level'),
        'duration_label': get_nested_val(data, 'job_details', 'duration'),
        'duration_weeks': get_nested_val(data, 'job_details', 'duration_weeks'),
        'workload': get_nested_val(data, 'job_details', 'workload'),
        'project_type': get_nested_val(data, 'job_details', 'project_type'),
        'posted_date': get_nested_val(data, 'job_details', 'posted_date'),
        'created_date': get_nested_val(data, 'job_details', 'created_date'),
        'start_date': get_nested_val(data, 'job_details', 'start_date'),
        'delivery_date': get_nested_val(data, 'job_details', 'delivery_date'),
        'deadline': get_nested_val(data, 'job_details', 'deadline'),
        'remote_job': get_nested_val(data, 'job_details', 'remote_job'),
        'was_renewed': get_nested_val(data, 'job_details', 'was_renewed'),
        'hide_budget': get_nested_val(data, 'job_details', 'hide_budget'),
        'number_of_positions': get_nested_val(data, 'job_details', 'number_of_positions'),
        'is_contract_to_hire': get_nested_val(data, 'job_details', 'is_contract_to_hire'),
        
        # Budget
        'budget_amount': get_nested_val(data, 'job_details', 'budget', 'amount'),
        'budget_currency': get_nested_val(data, 'job_details', 'budget', 'currency_code'),
        'hourly_min': get_nested_val(data, 'job_details', 'budget', 'hourly_min'),
        'hourly_max': get_nested_val(data, 'job_details', 'budget', 'hourly_max'),
        'budget_type': get_nested_val(data, 'job_details', 'budget', 'budget_type'),
        'weekly_retainer': get_nested_val(data, 'job_details', 'budget', 'weekly_retainer'),
        
        # Category
        'category_name': get_nested_val(data, 'job_details', 'category', 'name'),
        'category_slug': get_nested_val(data, 'job_details', 'category', 'url_slug'),
        'category_group': get_nested_val(data, 'job_details', 'category', 'group_name'),
        'category_group_slug': get_nested_val(data, 'job_details', 'category', 'group_url_slug'),
        
        # Client
        'client_location_country': get_nested_val(data, 'client', 'location', 'country'),
        'client_location_city': get_nested_val(data, 'client', 'location', 'city'),
        'client_location_timezone': get_nested_val(data, 'client', 'location', 'timezone'),
        'client_total_spent': get_nested_val(data, 'client', 'stats', 'total_spent'),
        'client_total_hires': get_nested_val(data, 'client', 'stats', 'total_hires'),
        'client_active_hires': get_nested_val(data, 'client', 'stats', 'active_hires'),
        'client_payment_verified': get_nested_val(data, 'client', 'payment_verified'),
        'client_member_since': get_nested_val(data, 'client', 'member_since'),
        'client_company_name': get_nested_val(data, 'client', 'company', 'name'),
        'client_company_industry': get_nested_val(data, 'client', 'company', 'industry'),
        'client_company_size': get_nested_val(data, 'client', 'company', 'size'),

        # Activity
        'proposals_min': get_nested_val(data, 'activity', 'proposals', 'min'),
        'proposals_max': get_nested_val(data, 'activity', 'proposals', 'max'),
        'proposals_text': get_nested_val(data, 'activity', 'proposals_text'),
        'interviewing_count': get_nested_val(data, 'activity', 'interviewing'),
        'invites_sent_count': get_nested_val(data, 'activity', 'invites_sent'),
        'unanswered_invites_count': get_nested_val(data, 'activity', 'unanswered_invites'),
        'total_hired_count': get_nested_val(data, 'activity', 'total_hired'),
        'last_buyer_activity': get_nested_val(data, 'activity', 'last_buyer_activity'),
        
        # Metadata
        'data_source': data.get('data_source'),
        'extracted_at': data.get('extracted_at'),
        
        # Complex/Nested fields kept as (semi-)structured JSON
        'skills_list': [s for s in data.get('skills', [])],
        'deliverables_list': data.get('deliverables', []),
        'skill_ontology': data.get('skill_ontology') if data.get('skill_ontology') else None,
        'qualifications': get_nested_val(data, 'job_details', 'qualifications') if get_nested_val(data, 'job_details', 'qualifications') else None,
        'annotations': get_nested_val(data, 'job_details', 'annotations') if get_nested_val(data, 'job_details', 'annotations') else None,
        'job_slug_info': get_nested_val(data, 'job_details', 'job_slug') if get_nested_val(data, 'job_details', 'job_slug') else None,
        'other_jobs_by_client_list': data.get('other_jobs_by_client', []),
        'similar_jobs_list': data.get('similar_jobs', []),
        'data_quality_report': data.get('data_quality'),
    }
    
    return normalized
File: upwork_extractor/pyproject.toml
[tool.poetry]
name = "upwork_extractor"
version = "0.1.0"
description = ""
authors = ["Your Name <you@example.com>"]
packages = [{ include = "upwork_extractor" }]

[tool.poetry.dependencies]
python = "^3.11"
beautifulsoup4 = "^4.12.3"
lxml = "^5.2.2"
pydantic = "^2.8.2"
python-dateutil = "^2.9.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
File: .env.example
# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=upwork_stable

# Scrapfly Configuration
# Can be a single key or a comma-separated list for key rotation.
SCRAPFLY_API_KEY=your_scrapfly_api_key_here 
SCRAPFLY_API_URL=https://api.scrapfly.io/scrape
SCRAPFLY_PROXY_POOLS=["public_datacenter_pool"]
SCRAPFLY_COUNTRY=us # Default country for scraping
SCRAPFLY_TIMEOUT=155000 # Milliseconds, 155 seconds default for Scrapfly
SCRAPFLY_RENDERING_WAIT=3000 # Milliseconds

# API Configuration
HOST=0.0.0.0
PORT=8000
# Set to True for development only. SHOULD BE FALSE IN PRODUCTION.
DEBUG=False

# CORS Configuration
# Comma-separated list of allowed origins. No trailing slashes.
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Caching
ENABLE_CACHE=True
CACHE_DIR=./cache
CACHE_EXPIRY_MINUTES=1440 # 24 hours

# Logging
LOG_DIR=./logs
LOG_LEVEL=INFO

# SSE Configuration
SSE_HEARTBEAT_INTERVAL=30
SSE_RETRY_TIMEOUT=3000
SSE_STATUS_CLEANUP_INTERVAL_SECONDS=3600 # How often to cleanup stale SSE run_status in memory

# Scraping Configuration
MAX_RETRIES=3 # Max attempts for internal retries (e.g. on detail page fetch failures)
RETRY_DELAY=2 # Seconds, for delays between attempts
MAX_CONCURRENT_REQUESTS=5 # For parallel scraping operations

# Upwork Specifics
UPWORK_BASE_URL=https://www.upwork.com
UPWORK_SEARCH_PAGE_JOB_COUNT=50 # Heuristic for pagination (jobs per page)
File: pyproject.toml
[tool.poetry]
name = "upwork_scraper"
version = "0.1.0"
description = "A backend application for scraping Upwork job postings, built with FastAPI and MongoDB."
authors = ["Your Name <you@example.com>"]
readme = "README.md"

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.111.0"
uvicorn = {extras = ["standard"], version = "^0.30.1"}
motor = "^3.3.2"
pydantic = "^2.8.2"
pydantic-settings = "^2.3.4"
beautifulsoup4 = "^4.12.3"
lxml = "^5.2.2"
scrapfly-sdk = "^0.8.23"
python-dotenv = "^1.0.1"
httpx = "^0.27.0"
sse-starlette = "^2.1.0"
python-dateutil = "^2.9.0"
tenacity = "^8.4.1"
aiofiles = "^24.1.0"
# Explicitly pinned sub-dependencies for uvicorn[standard] for reproducibility
# These versions should be checked with `pip freeze` after `poetry install uvicorn[standard]`
httptools = "^0.6.1"
uvloop = "^0.19.0"
websockets = "^12.0"
# The upwork_extractor is a local package
upwork_extractor = { path = "./upwork_extractor", develop = true }

[tool.poetry.group.dev.dependencies]
pytest = "^8.2.2"
pytest-asyncio = "^0.23.6"
black = "^24.4.2"
isort = "^5.13.2"
flake8 = "^7.1.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
File: README.md
# Upwork Scraper Backend

This project is a FastAPI-based backend application designed for scraping Upwork job postings, managing the scraped data in MongoDB, and providing real-time status updates via Server-Sent Events (SSE). It follows a Hexagonal Architecture for modularity, testability, and maintainability.

## Architecture Overview

The application is structured into distinct layers:

-   **Domain Layer:** Contains the core business entities (Pydantic models for Job, Client, Skill, etc.) and abstract repository interfaces (ports) that define how the application interacts with data.
-   **Application Layer:** Implements the business logic (use cases/services) that orchestrates domain entities and uses the repository interfaces. It is agnostic to infrastructure details.
-   **Infrastructure Layer:** Provides concrete implementations (adapters) for the repository interfaces (e.g., MongoDB repositories), external API clients (Scrapfly, Upwork Extractor), and other external concerns.
-   **API Layer:** The FastAPI controllers that expose the application's functionality via RESTful endpoints, handling HTTP requests and responses.

## Getting Started

### Prerequisites

-   Python 3.11+
-   MongoDB instance (local or remote)
-   Scrapfly API Key

### 1. Clone the repository
