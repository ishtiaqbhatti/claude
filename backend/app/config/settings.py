"""Application settings and configuration."""
from pathlib import Path
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # Application
    APP_NAME: str = "Upwork Scraper API"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # MongoDB
    MONGODB_URI: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "upwork_stable"

    # Collections
    COLLECTION_JOBS: str = "jobs"
    COLLECTION_CLIENTS: str = "clients"
    COLLECTION_SKILLS: str = "skills"
    COLLECTION_SEARCH_URLS: str = "search_urls"
    COLLECTION_SCRAPE_RUNS: str = "scrape_runs"

    # Scrapfly
    SCRAPFLY_API_KEY: str = Field(..., min_length=1)
    SCRAPFLY_API_URL: str = "https://api.scrapfly.io/scrape"
    SCRAPFLY_PROXY_POOLS: List[str] = ["public_datacenter_pool"]
    SCRAPFLY_COUNTRY: str = "us"
    SCRAPFLY_TIMEOUT: int = 155000
    SCRAPFLY_RENDERING_WAIT: int = 3000

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    CACHE_DIR: Path = BASE_DIR / "cache"
    LOG_DIR: Path = BASE_DIR / "logs"

    # Caching
    ENABLE_CACHE: bool = True
    CACHE_EXPIRY_MINUTES: int = 1440

    # Logging
    LOG_LEVEL: str = "INFO"

    # SSE
    SSE_HEARTBEAT_INTERVAL: int = 30
    SSE_RETRY_TIMEOUT: int = 3000
    SSE_STATUS_CLEANUP_INTERVAL_SECONDS: int = 3600

    # Scraping
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 2
    MAX_CONCURRENT_REQUESTS: int = 5

    # Upwork
    UPWORK_BASE_URL: str = "https://www.upwork.com"
    UPWORK_SEARCH_PAGE_JOB_COUNT: int = 50

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.LOG_DIR.mkdir(parents=True, exist_ok=True)


# Singleton instance
settings = Settings()
