import asyncio
from typing import List
from src.crawler.companies import (
    parse_remote_jobs_brazil_repo,
    detect_careers_page,
    normalize_url,
)
from src.crawler.scraper import (
    fetch_page,
    fetch_page_async,
    detect_ats_system,
    extract_job_postings,
)
from src.crawler.jobs_manager import load_jobs, save_jobs, merge_jobs
from src.config import JOBS_FILE
from src.types import JobPosting
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_crawler() -> int:
    """
    Main crawler orchestrator.

    Returns:
        Number of new jobs found
    """
    logger.info("Starting crawler...")

    # Step 1: Parse companies list
    logger.info("Fetching companies list from lerrua/remote-jobs-brazil...")
    companies = parse_remote_jobs_brazil_repo()
    logger.info(f"Found {len(companies)} companies")

    # Step 2: Crawl each company
    all_jobs = []
    for idx, company in enumerate(companies):
        logger.info(f"[{idx+1}/{len(companies)}] Crawling {company['name']}")
        try:
            jobs = await crawl_company(company)
            all_jobs.extend(jobs)
            logger.info(f"  Found {len(jobs)} jobs")
        except Exception as e:
            logger.warning(f"  Error crawling {company['name']}: {e}")
            continue

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

async def crawl_company(company: dict) -> List[JobPosting]:
    """
    Crawl a single company to find job postings.

    Args:
        company: Dict with 'name' and 'url'

    Returns:
        List of JobPosting objects found
    """
    jobs = []
    base_url = company["url"]
    company_name = company["name"]

    # Step 1: Generate possible careers page URLs
    possible_urls = detect_careers_page(base_url)

    # Step 2: Try to fetch each possible URL
    for career_url in possible_urls:
        try:
            logger.debug(f"  Trying {career_url}")
            html = await fetch_page_async(career_url, use_javascript=False)

            # Detect ATS
            ats = detect_ats_system(html)
            if ats:
                logger.debug(f"  Detected ATS: {ats}")

            # Extract jobs
            extracted = extract_job_postings(html, company_name, base_url, career_url)
            if extracted:
                logger.debug(f"  Found {len(extracted)} jobs on {career_url}")
                jobs.extend(extracted)
                break  # Found jobs on this page, stop trying other URLs

        except Exception as e:
            logger.debug(f"  Failed to fetch {career_url}: {e}")
            continue

    return jobs

def main():
    """Synchronous entry point for CLI"""
    new_jobs = asyncio.run(run_crawler())
    print(f"\nCrawler completed. Found {new_jobs} new jobs.")
    return 0

if __name__ == "__main__":
    exit(main())
