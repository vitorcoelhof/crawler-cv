"""
Multi-source job aggregator - combines jobs from multiple sources
RemoteOK + InfoJobs + GetNinja + LinkedIn + RSS feeds
"""
from typing import List
from src.types import JobPosting
from src.crawler.remoteok_api import search_remoteok_jobs
from src.crawler.infojobs_scraper import search_infojobs
import logging

logger = logging.getLogger(__name__)

def search_all_sources(keywords: List[str] = None, max_jobs_per_source: int = 50) -> List[JobPosting]:
    """
    Aggregate jobs from all available sources.

    Tries sources in order of reliability:
    1. RemoteOK API (most reliable, public, no blocking)
    2. InfoJobs (Brazilian, large database)
    3. GetNinja (Brazilian, freelance/PJ)
    4. LinkedIn (when available)
    5. RSS feeds (tech communities)

    Args:
        keywords: Skills to search for
        max_jobs_per_source: Max jobs from each source

    Returns:
        Combined list of JobPosting from all sources
    """
    if not keywords:
        keywords = [
            "Python", "SQL", "Airflow", "PySpark", "Databricks",
            "Data Engineer", "Data Science", "Machine Learning",
            "Backend", "Full Stack"
        ]

    all_jobs = []
    sources_status = {}

    # Source 1: RemoteOK API
    try:
        logger.info("Searching RemoteOK API...")
        remoteok_jobs = search_remoteok_jobs(keywords=keywords, max_results=max_jobs_per_source)
        all_jobs.extend(remoteok_jobs)
        sources_status["RemoteOK"] = f"✓ {len(remoteok_jobs)} jobs"
        logger.info(f"RemoteOK: {len(remoteok_jobs)} jobs")
    except Exception as e:
        sources_status["RemoteOK"] = f"✗ Failed: {str(e)[:50]}"
        logger.warning(f"RemoteOK failed: {e}")

    # Source 2: InfoJobs
    try:
        logger.info("Searching InfoJobs...")
        infojobs_jobs = search_infojobs(keywords=keywords, max_results=max_jobs_per_source)
        all_jobs.extend(infojobs_jobs)
        sources_status["InfoJobs"] = f"✓ {len(infojobs_jobs)} jobs"
        logger.info(f"InfoJobs: {len(infojobs_jobs)} jobs")
    except Exception as e:
        sources_status["InfoJobs"] = f"✗ Failed: {str(e)[:50]}"
        logger.warning(f"InfoJobs failed: {e}")

    # Source 3: GetNinja (placeholder - implement when needed)
    # try:
    #     logger.info("Searching GetNinja...")
    #     getninja_jobs = search_getninja(keywords=keywords)
    #     all_jobs.extend(getninja_jobs)
    #     logger.info(f"GetNinja: {len(getninja_jobs)} jobs")
    # except Exception as e:
    #     logger.warning(f"GetNinja failed: {e}")

    # Source 4: LinkedIn (requires authentication - placeholder)
    # try:
    #     logger.info("Searching LinkedIn...")
    #     linkedin_jobs = search_linkedin(keywords=keywords)
    #     all_jobs.extend(linkedin_jobs)
    #     logger.info(f"LinkedIn: {len(linkedin_jobs)} jobs")
    # except Exception as e:
    #     logger.warning(f"LinkedIn failed: {e}")

    # Source 5: RSS Feeds (placeholder - implement when needed)
    # try:
    #     logger.info("Searching RSS feeds...")
    #     rss_jobs = search_rss_feeds(keywords=keywords)
    #     all_jobs.extend(rss_jobs)
    #     logger.info(f"RSS Feeds: {len(rss_jobs)} jobs")
    # except Exception as e:
    #     logger.warning(f"RSS feeds failed: {e}")

    # Summary
    logger.info("\n=== Job Sources Summary ===")
    for source, status in sources_status.items():
        logger.info(f"{source}: {status}")
    logger.info(f"Total jobs from all sources: {len(all_jobs)}")

    return all_jobs
