"""
Playwright-based scraper for JavaScript-heavy sites
Handles InfoJobs and LinkedIn job boards
"""
import logging
from typing import List
from src.types import JobPosting
from datetime import date
import uuid

logger = logging.getLogger(__name__)

def search_infojobs_with_playwright(keywords: List[str] = None, max_jobs: int = 50) -> List[JobPosting]:
    """
    Search InfoJobs using Playwright (handles JavaScript rendering).

    Note: Requires Playwright to be installed and chromium browser downloaded.
    Install with: pip install playwright && playwright install chromium

    Args:
        keywords: Skills to search
        max_jobs: Maximum jobs to return

    Returns:
        List of JobPosting objects
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.warning("Playwright not installed. Install with: pip install playwright")
        return []

    if not keywords:
        keywords = ["Python", "Data Engineer"]

    jobs = []

    try:
        logger.info(f"Scraping InfoJobs with Playwright for: {', '.join(keywords[:3])}")

        with sync_playwright() as p:
            # Launch browser (headless = no UI)
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Set realistic headers
            page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept-Language": "pt-BR,pt;q=0.9"
            })

            # Navigate to InfoJobs
            search_query = " ".join(keywords)
            url = f"https://www.infojobs.com.br/vagas-de-emprego.aspx?q={search_query}&localizacao=remoto"

            logger.info(f"Loading {url}")
            page.goto(url, wait_until="networkidle", timeout=30000)

            # Wait for job listings to load (increased timeout for slower networks)
            try:
                page.wait_for_selector(".vaga, .job, [data-testid='jobCard'], .item-vaga, .job-card, article", timeout=15000)
            except Exception as e:
                logger.warning(f"Timeout waiting for selectors, continuing with available content: {e}")

            # Extract job listings - try multiple selector patterns
            job_elements = page.query_selector_all(".vaga, .job, [data-testid='jobCard'], .item-vaga, .job-card, article")

            # If still no elements, try a broader selector
            if not job_elements:
                logger.warning("No job elements found with standard selectors, trying broader search...")
                job_elements = page.query_selector_all("[class*='job'], [class*='vaga']")

            logger.info(f"Found {len(job_elements)} job elements")

            for idx, elem in enumerate(job_elements[:max_jobs]):
                try:
                    # Get element's HTML to understand structure (debug)
                    elem_html = elem.inner_html()[:200]

                    # Try multiple selector patterns for title
                    title_elem = elem.query_selector("h2, h3, h1, .titulo, [class*='title'], [class*='heading'], a")
                    title = title_elem.inner_text().strip() if title_elem else None

                    # Try to get any meaningful text from element
                    if not title:
                        title = elem.inner_text().strip().split("\n")[0]  # First line

                    # Get company - try multiple patterns
                    company_elem = elem.query_selector(".empresa, .company, [class*='empresa'], [class*='company'], span")
                    company = company_elem.inner_text().strip() if company_elem else "InfoJobs"

                    # Get the main link
                    link_elem = elem.query_selector("a")
                    link = link_elem.get_attribute("href") if link_elem else None

                    # Clean up title (remove extra whitespace and newlines)
                    if title:
                        title = " ".join(title.split())[:200]  # Limit to 200 chars

                    # Filter out false positives (footer text, banners, etc)
                    if title:
                        title_lower = title.lower()
                        # Skip if title is just repeated company name or common footer text
                        if (title_lower == company.lower() or
                            title_lower in ["achar vagas", "job", "vaga", "vagas", "find jobs",
                                          "procurar vagas", "search jobs", "o quê? onde?"]):
                            continue

                    # Process if we have meaningful title
                    if title and len(title) > 5:
                        # Ensure link is absolute (or use base URL)
                        if link:
                            if not link.startswith("http"):
                                link = f"https://www.infojobs.com.br{link}"
                        else:
                            link = f"https://www.infojobs.com.br/vagas-de-emprego.aspx"

                        job = JobPosting(
                            id=str(uuid.uuid4()),
                            empresa=company,
                            titulo=title,
                            descricao=title[:500],
                            requisitos="",
                            skills_detectadas=_extract_skills(title),
                            senioridade=_detect_senioridade(title),
                            localizacao="Remoto - Brasil",
                            link=link,
                            data_coleta=date.today().isoformat(),
                            url_empresa="https://www.infojobs.com.br",
                        )
                        jobs.append(job)
                        logger.info(f"InfoJobs: {company} - {title[:50]}")

                except Exception as e:
                    logger.debug(f"Error extracting job element {idx}: {e}")
                    continue

            browser.close()

        logger.info(f"Extracted {len(jobs)} jobs from InfoJobs")

    except Exception as e:
        logger.error(f"Playwright InfoJobs scraping failed: {e}")
        return []

    return jobs

def search_linkedin_with_playwright(keywords: List[str] = None, max_jobs: int = 50) -> List[JobPosting]:
    """
    Search LinkedIn using Playwright.

    Note: LinkedIn has strong anti-bot measures. This requires:
    - Valid LinkedIn account
    - Or LinkedIn API (requires business account)

    This is a placeholder showing the approach.

    Args:
        keywords: Skills to search
        max_jobs: Maximum jobs

    Returns:
        List of JobPosting objects
    """
    logger.warning("LinkedIn requires authentication. Use LinkedIn API instead (requires business account)")
    # LinkedIn is very restrictive. Recommended: use LinkedIn API or other sources
    return []

def _extract_skills(text: str) -> List[str]:
    """Extract skills from text"""
    known_skills = [
        "Python", "JavaScript", "TypeScript", "Java", "C#", "PHP",
        "Django", "FastAPI", "Flask", "Node.js", "React", "Vue",
        "AWS", "Docker", "Kubernetes", "PostgreSQL", "MongoDB",
        "Git", "REST API", "GraphQL", "SQL", "Linux",
        "Airflow", "PySpark", "Spark", "Databricks",
        "Machine Learning", "Data Science", "Data Engineer",
        "Backend", "Frontend", "Full Stack", "DevOps",
    ]

    text_lower = text.lower()
    found_skills = [skill for skill in known_skills if skill.lower() in text_lower]
    return list(set(found_skills))

def _detect_senioridade(text: str) -> str:
    """Detect seniority level"""
    text_lower = text.lower()

    if any(word in text_lower for word in ["senior", "staff", "lead", "principal"]):
        return "Senior"
    elif any(word in text_lower for word in ["mid", "pleno", "intermediate"]):
        return "Pleno"
    elif any(word in text_lower for word in ["junior", "entry", "trainee"]):
        return "Junior"

    return "Pleno"
