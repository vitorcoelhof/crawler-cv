"""
InfoJobs scraper - Brazil's largest job board
Responsibly scrapes InfoJobs job listings
"""
import requests
from typing import List
from src.types import JobPosting
from datetime import date
import uuid
import logging
from bs4 import BeautifulSoup
import time

logger = logging.getLogger(__name__)

# InfoJobs has a public search endpoint
INFOJOBS_API = "https://www.infojobs.com.br/api/search"

def search_infojobs(keywords: List[str] = None, max_results: int = 50) -> List[JobPosting]:
    """
    Search InfoJobs for remote jobs.

    Uses publicly available search without authentication.

    Args:
        keywords: Skills to search for
        max_results: Maximum results to fetch

    Returns:
        List of JobPosting objects
    """
    if not keywords:
        keywords = ["Python", "Data Engineer"]

    jobs = []

    try:
        logger.info(f"Searching InfoJobs for: {', '.join(keywords[:3])}")

        # Prepare search parameters
        query = " ".join(keywords)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept-Language": "pt-BR,pt;q=0.9"
        }

        # InfoJobs search endpoint
        url = "https://www.infojobs.com.br/vagas-de-emprego.aspx"

        params = {
            "q": query,
            "localizacao": "remoto",
            "pagina": 1
        }

        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()

        # Parse HTML
        soup = BeautifulSoup(response.content, "html.parser")

        # InfoJobs job listing selector (may need adjustment based on current HTML structure)
        job_elements = soup.find_all("article", class_="job")

        if not job_elements:
            # Fallback selector
            job_elements = soup.find_all("div", class_="vaga")

        logger.info(f"Found {len(job_elements)} job listings on InfoJobs")

        for elem in job_elements[:max_results]:
            try:
                job = _parse_infojobs_job(elem)
                if job:
                    jobs.append(job)

                # Be respectful with delays
                time.sleep(0.5)

            except Exception as e:
                logger.debug(f"Error parsing InfoJobs job: {e}")
                continue

        logger.info(f"Extracted {len(jobs)} jobs from InfoJobs")

    except requests.RequestException as e:
        logger.warning(f"InfoJobs request failed: {e}")
        return []
    except Exception as e:
        logger.error(f"Error scraping InfoJobs: {e}")
        return []

    return jobs

def _parse_infojobs_job(element) -> JobPosting:
    """Parse individual InfoJobs job element"""
    try:
        # These selectors may need updating based on InfoJobs' current HTML
        title_elem = element.find("h2") or element.find("h3")
        company_elem = element.find("span", class_="empresa")
        description_elem = element.find("p", class_="descricao")
        link_elem = element.find("a")

        if not title_elem:
            return None

        title = title_elem.get_text(strip=True)
        company = company_elem.get_text(strip=True) if company_elem else "Unknown"
        description = description_elem.get_text(strip=True) if description_elem else ""
        link = link_elem.get("href", "") if link_elem else ""

        full_text = f"{title} {description}"
        skills = _extract_skills(full_text)
        senioridade = _detect_senioridade(full_text)

        job = JobPosting(
            id=str(uuid.uuid4()),
            empresa=company,
            titulo=title,
            descricao=description[:500] if description else "",
            requisitos=description,
            skills_detectadas=skills,
            senioridade=senioridade,
            localizacao="Remoto - Brasil",
            link=f"https://www.infojobs.com.br{link}" if link.startswith("/") else link,
            data_coleta=date.today().isoformat(),
            url_empresa="https://www.infojobs.com.br",
        )

        return job

    except Exception as e:
        logger.debug(f"Error parsing InfoJobs job: {e}")
        return None

def _extract_skills(text: str) -> List[str]:
    """Extract known skills from text"""
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
