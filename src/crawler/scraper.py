import asyncio
from typing import List, Optional
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from src.types import JobPosting
from src.config import CRAWLER_TIMEOUT, USER_AGENT, RATE_LIMIT_DELAY
import time
import uuid
from datetime import date

async def fetch_page_async(url: str, use_javascript: bool = False) -> str:
    """
    Fetch page content. Use Playwright if JavaScript rendering is needed.

    Args:
        url: URL to fetch
        use_javascript: If True, use Playwright; else use requests

    Returns:
        HTML content
    """
    if use_javascript:
        return await _fetch_with_playwright(url)
    else:
        return _fetch_with_requests(url)

def _fetch_with_requests(url: str) -> str:
    """Fetch page with requests library (fast, for static HTML)"""
    try:
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(url, headers=headers, timeout=CRAWLER_TIMEOUT)
        response.raise_for_status()
        time.sleep(RATE_LIMIT_DELAY)
        return response.text
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to fetch {url}: {e}")

async def _fetch_with_playwright(url: str) -> str:
    """Fetch page with Playwright (slower, for JS-rendered sites)"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle", timeout=CRAWLER_TIMEOUT * 1000)
        content = await page.content()
        await browser.close()
        return content

def fetch_page(url: str) -> str:
    """Synchronous wrapper for fetch_page_async"""
    return asyncio.run(fetch_page_async(url, use_javascript=False))

def detect_ats_system(html: str) -> Optional[str]:
    """
    Detect if page uses a known ATS (Applicant Tracking System).

    Returns:
        ATS name (Greenhouse, Gupy, Lever, Workable, Kenoby) or None
    """
    ats_signatures = {
        "Greenhouse": ["boards.greenhouse.io", "greenhouse_config"],
        "Gupy": ["gupy", "GUPY_CONFIG"],
        "Lever": ["lever.co", "lever_config"],
        "Workable": ["workable.com", "workable_config"],
        "Kenoby": ["kenoby", "kenoby_config"],
    }

    for ats_name, signatures in ats_signatures.items():
        if any(sig.lower() in html.lower() for sig in signatures):
            return ats_name

    return None

def extract_job_postings(
    html: str,
    empresa: str,
    url_empresa: str,
    source_url: str
) -> List[JobPosting]:
    """
    Extract job postings from HTML using heuristics.
    This is a simplified implementation; may need refinement per site.

    Args:
        html: HTML content
        empresa: Company name
        url_empresa: Company base URL
        source_url: URL where this HTML came from

    Returns:
        List of extracted JobPosting objects
    """
    soup = BeautifulSoup(html, "html.parser")
    jobs = []

    # Common selectors for job postings
    job_selectors = [
        ("div.job", "h2,h3", "p"),  # Generic div.job
        ("article.job-posting", "h2", "p"),
        ("div[data-job-id]", "h2", "p"),
        ("li.job-listing", "h3", "span"),
    ]

    found = False
    for container_selector, title_selector, desc_selector in job_selectors:
        containers = soup.select(container_selector)
        if containers:
            found = True
            for container in containers:
                title_elem = container.select_one(title_selector)
                desc_elem = container.select_one(desc_selector)

                if title_elem:
                    title = title_elem.get_text(strip=True)
                    description = desc_elem.get_text(strip=True) if desc_elem else ""

                    job = JobPosting(
                        id=str(uuid.uuid4()),
                        empresa=empresa,
                        titulo=title,
                        descricao=description,
                        requisitos=description,  # Simplified
                        skills_detectadas=_extract_skills_from_text(description),
                        senioridade=_detect_senioridade(description),
                        localizacao="Remoto - Brasil",
                        link=source_url,
                        data_coleta=_get_today_iso(),
                        url_empresa=url_empresa,
                    )
                    jobs.append(job)

            if found:
                break

    return jobs

def _extract_skills_from_text(text: str) -> List[str]:
    """
    Heuristically extract skills from text.
    This is basic; could be improved with NLP.
    """
    known_skills = [
        "Python", "JavaScript", "TypeScript", "Java", "C#", "PHP",
        "Django", "FastAPI", "Flask", "Node.js", "React", "Vue",
        "AWS", "Docker", "Kubernetes", "PostgreSQL", "MongoDB",
        "Git", "REST API", "GraphQL", "SQL", "Linux",
        "Go", "Rust", "Ruby", "Rails", "Laravel",
    ]

    found_skills = [skill for skill in known_skills if skill.lower() in text.lower()]
    return found_skills

def _detect_senioridade(text: str) -> Optional[str]:
    """Detect seniority level from text"""
    text_lower = text.lower()

    if any(word in text_lower for word in ["senior", "staff", "lead", "principal"]):
        return "Senior"
    elif any(word in text_lower for word in ["mid-level", "pleno", "mid"]):
        return "Pleno"
    elif any(word in text_lower for word in ["junior", "entry", "trainee"]):
        return "Junior"

    return None

def _get_today_iso() -> str:
    """Return today's date in ISO format"""
    return date.today().isoformat()
