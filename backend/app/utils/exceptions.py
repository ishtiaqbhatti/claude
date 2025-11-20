"""Custom exceptions for the scraper application."""


class ScraperException(Exception):
    """Base exception for scraper application."""

    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ScrapingException(ScraperException):
    """Exception raised during web scraping."""

    pass


class ExtractionException(ScraperException):
    """Exception raised during data extraction."""

    pass


class DatabaseException(ScraperException):
    """Exception raised during database operations."""

    pass


class ValidationException(ScraperException):
    """Exception raised during validation."""

    pass


class ConfigurationException(ScraperException):
    """Exception raised for configuration errors."""

    pass


class RateLimitException(ScraperException):
    """Exception raised when rate limit is exceeded."""

    def __init__(self, message: str, retry_after: int = None, details: dict = None):
        super().__init__(message, details)
        self.retry_after = retry_after


class AuthenticationException(ScraperException):
    """Exception raised for authentication errors."""

    pass


class JobNotFoundException(ScraperException):
    """Exception raised when a job is not found."""

    def __init__(self, job_uid: str):
        self.job_uid = job_uid
        super().__init__(f"Job {job_uid} not found", {"job_uid": job_uid})


class URLNotFoundException(ScraperException):
    """Exception raised when a URL is not found."""

    def __init__(self, url_id: str):
        self.url_id = url_id
        super().__init__(f"URL {url_id} not found", {"url_id": url_id})
