"""Upwork extractor client for data extraction."""
import logging
from typing import Optional, Dict, Any, List
from upwork_extractor import UpworkExtractor
from upwork_extractor.models import JobListing, JobDetail

logger = logging.getLogger(__name__)


class UpworkExtractorClient:
    """Client for Upwork data extraction."""

    def __init__(self):
        """Initialize Upwork extractor."""
        self.extractor = UpworkExtractor()

    def extract_search_results(self, html_content: str) -> List[Dict[str, Any]]:
        """
        Extract job listings from search page HTML.

        Args:
            html_content: HTML content of search page

        Returns:
            List of job dictionaries
        """
        try:
            jobs: List[JobListing] = self.extractor.extract_search_page(html_content)
            return [self._job_listing_to_dict(job) for job in jobs]
        except Exception as e:
            logger.error(f"Error extracting search results: {e}")
            return []

    def extract_job_detail(self, html_content: str) -> Optional[Dict[str, Any]]:
        """
        Extract job details from detail page HTML.

        Args:
            html_content: HTML content of job detail page

        Returns:
            Job detail dictionary or None if failed
        """
        try:
            job_detail: Optional[JobDetail] = self.extractor.extract_detail_page(html_content)
            if job_detail:
                return self._job_detail_to_dict(job_detail)
            return None
        except Exception as e:
            logger.error(f"Error extracting job detail: {e}")
            return None

    def _job_listing_to_dict(self, job: JobListing) -> Dict[str, Any]:
        """Convert JobListing to dictionary."""
        return {
            "uid": job.uid,
            "title": job.title,
            "url": str(job.url) if job.url else None,
            "ciphertext": job.ciphertext,
            "budget": {
                "available": job.budget_available if hasattr(job, 'budget_available') else False,
                "type": job.budget_type if hasattr(job, 'budget_type') else None,
                "min": job.budget_min if hasattr(job, 'budget_min') else None,
                "max": job.budget_max if hasattr(job, 'budget_max') else None,
                "currency": "USD",
            },
            "content": {
                "description": job.description if hasattr(job, 'description') else None,
                "description_plain": job.description_plain if hasattr(job, 'description_plain') else None,
                "skill_ids": [],
                "skills": [],
            },
            "published_on": job.published_on if hasattr(job, 'published_on') else None,
            "created_on": job.created_on if hasattr(job, 'created_on') else None,
        }

    def _job_detail_to_dict(self, job: JobDetail) -> Dict[str, Any]:
        """Convert JobDetail to dictionary."""
        # Extract skills
        skills = []
        skill_ids = []
        if hasattr(job, 'skills') and job.skills:
            for skill in job.skills:
                skill_uid = skill.get('uid') or skill.get('id', '')
                skill_name = skill.get('name', '')
                skill_ids.append(skill_uid)
                skills.append({
                    "uid": skill_uid,
                    "name": skill_name,
                    "category": skill.get('category'),
                })

        # Extract client info
        client_info = {}
        if hasattr(job, 'client') and job.client:
            client = job.client
            client_info = {
                "country": client.get('country'),
                "city": client.get('city'),
                "company": client.get('company'),
                "total_spent": client.get('total_spent'),
                "total_hires": client.get('total_hires'),
                "active_contracts": client.get('active_contracts'),
                "payment_verified": client.get('payment_verified', False),
                "rating": client.get('rating'),
                "reviews_count": client.get('reviews_count'),
            }

        return {
            "uid": job.uid,
            "title": job.title,
            "url": str(job.url) if job.url else None,
            "ciphertext": job.ciphertext if hasattr(job, 'ciphertext') else None,
            "content": {
                "description": job.description if hasattr(job, 'description') else None,
                "description_plain": job.description_plain if hasattr(job, 'description_plain') else None,
                "skill_ids": skill_ids,
                "skills": skills,
            },
            "budget": {
                "available": job.budget_available if hasattr(job, 'budget_available') else False,
                "type": job.budget_type if hasattr(job, 'budget_type') else None,
                "min": job.budget_min if hasattr(job, 'budget_min') else None,
                "max": job.budget_max if hasattr(job, 'budget_max') else None,
                "currency": "USD",
            },
            "client": client_info,
            "experience_level": job.experience_level if hasattr(job, 'experience_level') else None,
            "duration": job.duration if hasattr(job, 'duration') else None,
            "workload": job.workload if hasattr(job, 'workload') else None,
            "project_type": job.project_type if hasattr(job, 'project_type') else None,
            "category_name": job.category if hasattr(job, 'category') else None,
            "published_on": job.published_on if hasattr(job, 'published_on') else None,
            "created_on": job.created_on if hasattr(job, 'created_on') else None,
            "renewed_on": job.renewed_on if hasattr(job, 'renewed_on') else None,
            "was_renewed": job.was_renewed if hasattr(job, 'was_renewed') else False,
        }

    def extract_batch_search_results(
        self, html_contents: List[str]
    ) -> List[List[Dict[str, Any]]]:
        """
        Extract job listings from multiple search pages.

        Args:
            html_contents: List of HTML contents

        Returns:
            List of job listings for each page
        """
        return [self.extract_search_results(html) for html in html_contents]

    def extract_batch_job_details(
        self, html_contents: List[str]
    ) -> List[Optional[Dict[str, Any]]]:
        """
        Extract job details from multiple detail pages.

        Args:
            html_contents: List of HTML contents

        Returns:
            List of job details (None for failed extractions)
        """
        return [self.extract_job_detail(html) for html in html_contents]
