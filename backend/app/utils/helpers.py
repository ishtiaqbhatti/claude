"""General helper functions."""
import re
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any
from html import unescape


def generate_client_key(country: Optional[str], company: Optional[str]) -> str:
    """
    Generate a unique key for client deduplication.

    Args:
        country: Client country
        company: Company name

    Returns:
        Unique client key
    """
    country = (country or "unknown").lower().strip()
    company = (company or "unknown").lower().strip()

    # Create hash for very long company names
    if len(company) > 100:
        company_hash = hashlib.md5(company.encode()).hexdigest()[:16]
        return f"{country}_{company_hash}"

    return f"{country}_{company}"


def sanitize_html(html: str) -> str:
    """
    Sanitize HTML content.

    Args:
        html: HTML string

    Returns:
        Sanitized HTML
    """
    # Unescape HTML entities
    text = unescape(html)

    # Remove script and style tags
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)

    # Remove HTML comments
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)

    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def parse_budget(budget_str: Optional[str]) -> Dict[str, Any]:
    """
    Parse budget string into structured data.

    Args:
        budget_str: Budget string (e.g., "$100-$500", "$50/hr")

    Returns:
        Budget dict with type, min, max, currency
    """
    if not budget_str:
        return {
            "available": False,
            "type": None,
            "min": None,
            "max": None,
            "currency": "USD",
        }

    budget_str = budget_str.strip()

    # Check if hourly rate
    is_hourly = "/hr" in budget_str.lower() or "per hour" in budget_str.lower()
    budget_type = "hourly" if is_hourly else "fixed"

    # Extract numbers
    numbers = re.findall(r'\d+(?:,\d{3})*(?:\.\d{2})?', budget_str)
    numbers = [float(n.replace(',', '')) for n in numbers]

    if not numbers:
        return {
            "available": False,
            "type": budget_type,
            "min": None,
            "max": None,
            "currency": "USD",
        }

    # Determine min and max
    if len(numbers) == 1:
        min_budget = numbers[0]
        max_budget = numbers[0]
    else:
        min_budget = min(numbers)
        max_budget = max(numbers)

    return {
        "available": True,
        "type": budget_type,
        "min": min_budget,
        "max": max_budget,
        "currency": "USD",
    }


def format_datetime(dt: Optional[datetime], format_str: str = "%Y-%m-%d %H:%M:%S") -> Optional[str]:
    """
    Format datetime to string.

    Args:
        dt: Datetime object
        format_str: Format string

    Returns:
        Formatted datetime string or None
    """
    if dt is None:
        return None

    return dt.strftime(format_str)


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def extract_uid_from_url(url: str) -> Optional[str]:
    """
    Extract job UID from Upwork URL.

    Args:
        url: Upwork job URL

    Returns:
        Job UID or None
    """
    # Pattern: /jobs/~XXXXXXXXXXXXXXXXXXXX
    match = re.search(r'/jobs/~([a-f0-9]+)', url)
    if match:
        return match.group(1)

    return None


def clean_text(text: Optional[str]) -> Optional[str]:
    """
    Clean and normalize text.

    Args:
        text: Input text

    Returns:
        Cleaned text or None
    """
    if not text:
        return None

    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)

    # Remove leading/trailing whitespace
    text = text.strip()

    return text if text else None


def calculate_percentage(part: float, total: float) -> float:
    """
    Calculate percentage.

    Args:
        part: Part value
        total: Total value

    Returns:
        Percentage (0-100)
    """
    if total == 0:
        return 0.0

    return round((part / total) * 100, 2)


def chunks(lst: list, chunk_size: int):
    """
    Split list into chunks.

    Args:
        lst: Input list
        chunk_size: Size of each chunk

    Yields:
        Chunks of the list
    """
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]
