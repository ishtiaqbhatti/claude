"""Rate limiting middleware."""
import time
import logging
from collections import defaultdict
from typing import Dict, Tuple
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..config import settings

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware with sliding window algorithm.

    Limits:
    - 100 requests per minute per IP
    - 1000 requests per hour per IP
    """

    def __init__(self, app):
        super().__init__(app)
        # Store: {ip: [(timestamp, count)]}
        self.request_counts: Dict[str, list] = defaultdict(list)
        self.last_cleanup = time.time()

        # Rate limits
        self.minute_limit = 100  # requests per minute
        self.hour_limit = 1000   # requests per hour

        # Windows in seconds
        self.minute_window = 60
        self.hour_window = 3600

        # Cleanup interval (every 10 minutes)
        self.cleanup_interval = 600

    def _cleanup_old_entries(self):
        """Remove old entries to prevent memory growth."""
        now = time.time()

        # Only cleanup every 10 minutes
        if now - self.last_cleanup < self.cleanup_interval:
            return

        cutoff = now - self.hour_window
        for ip in list(self.request_counts.keys()):
            # Remove entries older than 1 hour
            self.request_counts[ip] = [
                entry for entry in self.request_counts[ip]
                if entry[0] > cutoff
            ]
            # Remove IP if no entries
            if not self.request_counts[ip]:
                del self.request_counts[ip]

        self.last_cleanup = now
        logger.debug(f"Rate limit cleanup: {len(self.request_counts)} IPs tracked")

    def _check_rate_limit(self, ip: str) -> Tuple[bool, str]:
        """
        Check if request exceeds rate limit.

        Returns:
            (is_allowed, error_message)
        """
        now = time.time()

        # Get requests in the last minute and hour
        minute_cutoff = now - self.minute_window
        hour_cutoff = now - self.hour_window

        requests = self.request_counts[ip]

        # Count requests in windows
        minute_count = sum(1 for ts, _ in requests if ts > minute_cutoff)
        hour_count = sum(1 for ts, _ in requests if ts > hour_cutoff)

        # Check limits
        if minute_count >= self.minute_limit:
            return False, f"Rate limit exceeded: {self.minute_limit} requests per minute"
        if hour_count >= self.hour_limit:
            return False, f"Rate limit exceeded: {self.hour_limit} requests per hour"

        return True, ""

    async def dispatch(self, request: Request, call_next):
        """Rate limit requests by IP address."""
        # Skip rate limiting for health checks
        if request.url.path.startswith("/api/health"):
            return await call_next(request)

        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Periodic cleanup
        self._cleanup_old_entries()

        # Check rate limit
        is_allowed, error_msg = self._check_rate_limit(client_ip)

        if not is_allowed:
            logger.warning(f"Rate limit exceeded for {client_ip}: {request.url.path}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": error_msg,
                    "retry_after": 60,  # seconds
                },
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(self.minute_limit),
                    "X-RateLimit-Remaining": "0",
                },
            )

        # Record request
        now = time.time()
        self.request_counts[client_ip].append((now, 1))

        # Calculate remaining requests
        minute_cutoff = now - self.minute_window
        minute_count = sum(1 for ts, _ in self.request_counts[client_ip] if ts > minute_cutoff)
        remaining = max(0, self.minute_limit - minute_count)

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.minute_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(now + self.minute_window))

        return response
