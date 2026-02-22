from src.crawler.adzuna import search_jobs_adzuna
from src.crawler.jobs_manager import load_jobs, save_jobs, merge_jobs
from src.config import JOBS_FILE
from src.types import ResumeProfile
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_crawler(skills: list = None) -> int:
    """
    Main crawler orchestrator using Adzuna API.

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

    # Step 1: Try to search jobs via Adzuna API
    logger.info(f"Searching for jobs with skills: {', '.join(skills[:5])}...")
    all_jobs = search_jobs_adzuna(skills, location="Brazil", max_results=100)
    logger.info(f"Found {len(all_jobs)} jobs from Adzuna API")

    if not all_jobs:
        logger.warning("Adzuna API failed or returned no results.")
        logger.info("To use Adzuna API with your own credentials:")
        logger.info("  1. Sign up at https://www.adzuna.com/api for free")
        logger.info("  2. Add your app_id and app_key to .env or hardcode in adzuna.py")
        logger.info("  3. For now, using existing jobs database...")
        return 0

    # Step 2: Load existing jobs and merge
    logger.info("Merging with existing jobs...")
    existing_jobs = load_jobs(str(JOBS_FILE))
    merged_jobs = merge_jobs(existing_jobs, all_jobs)

    new_count = len(merged_jobs) - len(existing_jobs)
    logger.info(f"New jobs: {new_count}, Total: {len(merged_jobs)}")

    # Step 3: Save
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
