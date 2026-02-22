"""
RemoteOK API integration - Public jobs API for remote positions
Site: https://remoteok.io
API: https://remoteok.io/api
No authentication required
"""
import requests
from typing import List
from src.types import JobPosting
from datetime import date
import uuid
import logging

logger = logging.getLogger(__name__)

REMOTEOK_API_URL = "https://remoteok.io/api"

def search_remoteok_jobs(keywords: List[str] = None, max_results: int = 100) -> List[JobPosting]:
    """
    Search RemoteOK for remote jobs.

    Args:
        keywords: Skills to search for
        max_results: Maximum results to fetch

    Returns:
        List of JobPosting objects
    """
    if not keywords:
        keywords = ["Python", "Data Engineer", "Backend"]

    jobs = []

    try:
        logger.info(f"Searching RemoteOK API for: {', '.join(keywords[:3])}")

        # RemoteOK returns all jobs by default
        # We filter by search terms in post-processing
        response = requests.get(REMOTEOK_API_URL, timeout=10)
        response.raise_for_status()

        data = response.json()
        logger.info(f"RemoteOK returned {len(data)} total jobs")

        # Filter by keywords
        keyword_lower = [k.lower() for k in keywords]
        count = 0

        for item in data:
            if count >= max_results:
                break

            try:
                # Check if job matches keywords
                title_lower = str(item.get("title", "")).lower()
                tags_lower = [t.lower() for t in item.get("tags", [])]
                description_lower = str(item.get("description", "")).lower()

                matches_keywords = any(
                    kw in title_lower or
                    kw in " ".join(tags_lower) or
                    kw in description_lower
                    for kw in keyword_lower
                )

                if not matches_keywords:
                    continue

                # Extract job details
                job = _parse_remoteok_job(item)
                if job:
                    jobs.append(job)
                    count += 1

            except Exception as e:
                logger.debug(f"Error parsing RemoteOK job: {e}")
                continue

        logger.info(f"Found {len(jobs)} matching jobs from RemoteOK")

    except requests.RequestException as e:
        logger.warning(f"RemoteOK API request failed: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error querying RemoteOK: {e}")
        return []

    return jobs


def _parse_remoteok_job(data: dict) -> JobPosting:
    """Convert RemoteOK API response to JobPosting."""

    try:
        # Extract skills from title and description
        title = data.get("title", "")
        description = data.get("description", "")
        tags = data.get("tags", [])

        full_text = f"{title} {description} {' '.join(tags)}"
        skills = _extract_skills(full_text)
        senioridade = _detect_senioridade(full_text)

        # Get company name (RemoteOK uses 'company' or extracts from title)
        company = data.get("company", "Unknown")
        if not company or company == "Unknown":
            # Try to extract from title
            company = title.split(" at ")[-1] if " at " in title else "Unknown"

        job = JobPosting(
            id=str(uuid.uuid4()),
            empresa=company,
            titulo=title,
            descricao=description[:500] if description else "",
            requisitos=description if description else "",
            skills_detectadas=skills,
            senioridade=senioridade,
            localizacao=data.get("location", "Remote"),
            link=data.get("url", ""),
            data_coleta=date.today().isoformat(),
            url_empresa=data.get("company_url", ""),
            salario_min=data.get("salary_min"),
            salario_max=data.get("salary_max"),
        )

        return job

    except Exception as e:
        logger.debug(f"Error parsing RemoteOK job details: {e}")
        return None


def _extract_skills(text: str) -> List[str]:
    """Extract known skills from text."""
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
        "DevOps", "Cloud", "Microservices", "API", "Database",
    ]

    text_lower = text.lower()
    found_skills = [skill for skill in known_skills if skill.lower() in text_lower]
    return list(set(found_skills))  # Remove duplicates


def _detect_senioridade(text: str) -> str:
    """Detect seniority level from text."""
    text_lower = text.lower()

    if any(word in text_lower for word in ["senior", "staff", "lead", "principal", "sr."]):
        return "Senior"
    elif any(word in text_lower for word in ["mid-level", "pleno", "mid", "intermediate", "mid-senior"]):
        return "Pleno"
    elif any(word in text_lower for word in ["junior", "entry", "trainee", "jr.", "estagiario", "entry-level"]):
        return "Junior"

    return "Pleno"  # Default
