"""Authentication middleware."""
import logging
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..config import settings

logger = logging.getLogger(__name__)


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Middleware to validate API keys for protected endpoints."""

    # Paths that don't require API key
    PUBLIC_PATHS = {
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/health",
        "/api/health/live",
        "/api/health/ready",
    }

    async def dispatch(self, request: Request, call_next):
        """Validate API key if authentication is enabled."""
        # Skip auth if disabled or public path
        if not settings.API_KEY_ENABLED or any(
            request.url.path.startswith(path) for path in self.PUBLIC_PATHS
        ):
            return await call_next(request)

        # Get API key from header
        api_key = request.headers.get("X-API-Key") or request.headers.get("Authorization", "").replace("Bearer ", "")

        # Validate API key
        if not api_key or api_key not in settings.API_KEYS:
            logger.warning(f"Unauthorized access attempt to {request.url.path}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid or missing API key"},
                headers={"WWW-Authenticate": "ApiKey"},
            )

        # API key is valid, proceed
        return await call_next(request)


def api_key_middleware():
    """Factory function to create API key middleware."""
    return APIKeyMiddleware
