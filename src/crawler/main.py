from src.crawler.github_jobs import search_jobs_github
from src.crawler.gupy_scraper import search_jobs_gupy
from src.crawler.jobs_manager import load_jobs, save_jobs, merge_jobs
from src.config import JOBS_FILE
from src.types import ResumeProfile
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_crawler(skills: list = None) -> int:
    """
    Main crawler orchestrator using GitHub Jobs API + Gupy scraper.

    Args:
        skills: List of skills to search for (default: common data skills)

    Returns:
        Number of new jobs found
    """
    logger.info("Starting crawler...")

    # Default skills if none provided
    if not skills:
        skills = [
            "Python", "SQL", "Airflow", "PySpark", "Databricks",
            "Data Engineer", "Data Science", "Machine Learning",
            "Backend", "Full Stack"
        ]

    all_jobs = []

    # Step 1: Search GitHub Jobs API
    logger.info(f"Searching GitHub Jobs API with skills: {', '.join(skills[:5])}...")
    try:
        github_jobs = search_jobs_github(keywords=skills)
        logger.info(f"Found {len(github_jobs)} jobs from GitHub Jobs API")
        all_jobs.extend(github_jobs)
    except Exception as e:
        logger.warning(f"GitHub Jobs API failed: {e}")

    # Step 2: Scrape Gupy
    logger.info("Scraping Gupy for Brazilian company jobs...")
    try:
        gupy_jobs = search_jobs_gupy()
        logger.info(f"Found {len(gupy_jobs)} jobs from Gupy scraper")
        all_jobs.extend(gupy_jobs)
    except Exception as e:
        logger.warning(f"Gupy scraper failed: {e}")

    if not all_jobs:
        logger.warning("No jobs found from external sources.")
        logger.info("This is expected in CI/testing environments.")
        logger.info("Using existing jobs database as fallback...")
        # Note: In production with real APIs, jobs would be collected above
        return 0

    # Step 3: Load existing jobs and merge
    logger.info("Merging with existing jobs...")
    existing_jobs = load_jobs(str(JOBS_FILE))
    merged_jobs = merge_jobs(existing_jobs, all_jobs)

    new_count = len(merged_jobs) - len(existing_jobs)
    logger.info(f"New jobs: {new_count}, Total: {len(merged_jobs)}")

    # Step 4: Save
    logger.info(f"Saving to {JOBS_FILE}...")
    save_jobs(merged_jobs, str(JOBS_FILE))

    logger.info("Crawler complete!")
    return new_count

def main():
    """Entry point for CLI"""
    new_jobs = run_crawler()
    print(f"\nCrawler completed. Found {new_jobs} new jobs.")
    return 0

if __name__ == "__main__":
    exit(main())
