"""Search URL API routes."""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import HttpUrl

from ..services import URLService
from ..schemas.url import URLCreate, URLUpdate, URLListResponse, URLStatsResponse

router = APIRouter(prefix="/api/urls", tags=["urls"])

# Initialize service
url_service = URLService()


@router.get("/", response_model=URLListResponse)
async def get_all_urls(
    enabled_only: bool = Query(False, description="Only return enabled URLs"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
):
    """
    Get all search URLs with pagination.
    """
    result = await url_service.get_all_urls(
        enabled_only=enabled_only,
        page=page,
        page_size=page_size,
    )

    return URLListResponse(
        urls=result["urls"],
        total=result["pagination"]["total"],
        page=result["pagination"]["page"],
        page_size=result["pagination"]["page_size"],
        total_pages=result["pagination"]["total_pages"],
    )


@router.get("/enabled")
async def get_enabled_urls():
    """
    Get all enabled search URLs.
    """
    urls = await url_service.get_enabled_urls()

    return {
        "urls": urls,
        "count": len(urls),
    }


@router.get("/stats", response_model=URLStatsResponse)
async def get_url_stats():
    """
    Get URL statistics.
    """
    stats = await url_service.get_url_stats()
    return URLStatsResponse(**stats)


@router.get("/{url_id}")
async def get_url(url_id: str):
    """
    Get URL by ID.
    """
    url = await url_service.get_url_by_id(url_id)

    if not url:
        raise HTTPException(status_code=404, detail=f"URL {url_id} not found")

    return url


@router.post("/")
async def create_url(url_data: URLCreate):
    """
    Create a new search URL.
    """
    # Validate URL
    is_valid = await url_service.validate_url(str(url_data.url))
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail="Invalid Upwork search URL. Must be a valid Upwork search page URL.",
        )

    url_id = await url_service.create_url(
        url=url_data.url,
        name=url_data.name,
        enabled=url_data.enabled,
    )

    return {
        "success": True,
        "url_id": url_id,
        "message": "Search URL created successfully",
    }


@router.patch("/{url_id}")
async def update_url(url_id: str, url_data: URLUpdate):
    """
    Update a search URL.
    """
    updated = await url_service.update_url(
        url_id=url_id,
        name=url_data.name,
        enabled=url_data.enabled,
    )

    if not updated:
        raise HTTPException(status_code=404, detail=f"URL {url_id} not found")

    return {
        "success": True,
        "url_id": url_id,
        "message": "URL updated successfully",
    }


@router.delete("/{url_id}")
async def delete_url(url_id: str):
    """
    Delete a search URL.
    """
    deleted = await url_service.delete_url(url_id)

    if not deleted:
        raise HTTPException(status_code=404, detail=f"URL {url_id} not found")

    return {
        "success": True,
        "message": f"URL {url_id} deleted successfully",
    }


@router.post("/{url_id}/toggle")
async def toggle_url(url_id: str):
    """
    Toggle URL enabled status.
    """
    new_status = await url_service.toggle_url(url_id)

    if new_status is None:
        raise HTTPException(status_code=404, detail=f"URL {url_id} not found")

    return {
        "success": True,
        "url_id": url_id,
        "enabled": new_status,
    }
