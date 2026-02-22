"""
Dynamic Gupy scraper - discovers and scrapes ALL active Gupy companies
Instead of hardcoded URLs, this discovers companies from Gupy's job listings
"""
import requests
from typing import List, Set
from src.types import JobPosting
from datetime import date
import uuid
import logging
from bs4 import BeautifulSoup
import time

logger = logging.getLogger(__name__)

# Gupy's main job search API endpoint
GUPY_SEARCH_API = "https://api.gupy.io/api/careers/public"
GUPY_BASE_URL = "https://gupy.io"

def discover_gupy_companies() -> Set[str]:
    """
    Discover all companies currently using Gupy.

    This queries Gupy's API to get active companies instead of using hardcoded list.

    Returns:
        Set of company domain names using Gupy
    """
    companies = set()

    try:
        logger.info("Discovering active Gupy companies...")

        # Gupy API endpoint that returns job openings across all companies
        url = "https://api.gupy.io/api/careers"

        params = {
            "offset": 0,
            "limit": 100,
            "sort": "publishedDate,desc"
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        if "data" in data:
            for job in data["data"]:
                if "company" in job and "name" in job["company"]:
                    company_name = job["company"]["name"]
                    companies.add(company_name)

        logger.info(f"Discovered {len(companies)} active Gupy companies")

    except Exception as e:
        logger.warning(f"Failed to discover Gupy companies: {e}")

    return companies

def search_gupy_jobs_api(keywords: List[str] = None, max_results: int = 100) -> List[JobPosting]:
    """
    Search for jobs via Gupy's public API.
    This is more reliable than scraping individual company pages.

    Args:
        keywords: Skills to search for
        max_results: Maximum jobs to return

    Returns:
        List of JobPosting objects
    """
    if not keywords:
        keywords = ["Python", "Data", "Engineer"]

    jobs = []

    try:
        logger.info(f"Searching Gupy API for: {', '.join(keywords[:3])}")

        # Gupy's API endpoint for job search
        url = "https://api.gupy.io/api/careers"

        params = {
            "offset": 0,
            "limit": min(max_results, 100),
            "sort": "publishedDate,desc"
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        logger.info(f"Gupy API returned {len(data.get('data', []))} jobs")

        keyword_lower = [k.lower() for k in keywords]
        count = 0

        for item in data.get("data", []):
            if count >= max_results:
                break

            try:
                # Filter by keywords
                title = item.get("name", "").lower()
                description = item.get("description", "").lower()

                matches = any(kw in title or kw in description for kw in keyword_lower)

                if not matches:
                    continue

                job = _parse_gupy_api_job(item)
                if job:
                    jobs.append(job)
                    count += 1

                # Be respectful to the API
                time.sleep(0.1)

            except Exception as e:
                logger.debug(f"Error parsing Gupy job: {e}")
                continue

        logger.info(f"Found {len(jobs)} matching jobs from Gupy API")

    except requests.RequestException as e:
        logger.warning(f"Gupy API request failed: {e}")
        return []
    except Exception as e:
        logger.error(f"Error searching Gupy: {e}")
        return []

    return jobs

def _parse_gupy_api_job(data: dict) -> JobPosting:
    """Parse Gupy API job response"""
    try:
        title = data.get("name", "")
        description = data.get("description", "")
        company_data = data.get("company", {})
        company_name = company_data.get("name", "Unknown")

        full_text = f"{title} {description}"
        skills = _extract_skills(full_text)
        senioridade = _detect_senioridade(full_text)

        job = JobPosting(
            id=str(uuid.uuid4()),
            empresa=company_name,
            titulo=title,
            descricao=description[:500] if description else "",
            requisitos=description if description else "",
            skills_detectadas=skills,
            senioridade=senioridade,
            localizacao=data.get("location", {}).get("name", "Remoto - Brasil"),
            link=data.get("url", ""),
            data_coleta=date.today().isoformat(),
            url_empresa=data.get("company", {}).get("website", ""),
        )

        return job

    except Exception as e:
        logger.debug(f"Error parsing Gupy job: {e}")
        return None

def _extract_skills(text: str) -> List[str]:
    """Extract known skills from text"""
    known_skills = [
        "Python", "JavaScript", "TypeScript", "Java", "C#", "PHP",
        "Django", "FastAPI", "Flask", "Node.js", "React", "Vue",
        "AWS", "Docker", "Kubernetes", "PostgreSQL", "MongoDB",
        "Git", "REST API", "GraphQL", "SQL", "Linux",
        "Go", "Rust", "Ruby", "Rails", "Laravel",
        "Airflow", "PySpark", "Spark", "Databricks",
        "Pandas", "NumPy", "Scikit-learn", "TensorFlow", "PyTorch",
        "Machine Learning", "Deep Learning", "Data Science",
        "Data Engineer", "Backend", "Frontend", "Full Stack",
    ]

    text_lower = text.lower()
    found_skills = [skill for skill in known_skills if skill.lower() in text_lower]
    return list(set(found_skills))

def _detect_senioridade(text: str) -> str:
    """Detect seniority level"""
    text_lower = text.lower()

    if any(word in text_lower for word in ["senior", "staff", "lead", "principal", "sr."]):
        return "Senior"
    elif any(word in text_lower for word in ["mid-level", "pleno", "mid", "intermediate"]):
        return "Pleno"
    elif any(word in text_lower for word in ["junior", "entry", "trainee", "jr.", "estagiario"]):
        return "Junior"

    return "Pleno"
