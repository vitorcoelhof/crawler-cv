import requests
from typing import List
from src.types import JobPosting
from datetime import date
import uuid
import json

# GitHub Jobs API (public, no auth required)
GITHUB_JOBS_API = "https://jobs.github.com/positions.json"

def search_jobs_github(keywords: List[str], location: str = "remote") -> List[JobPosting]:
    """
    Search for jobs using GitHub Jobs API.

    Args:
        keywords: List of keywords to search for
        location: Job location (default: remote)

    Returns:
        List of JobPosting objects
    """
    jobs = []

    try:
        # GitHub Jobs API accepts one keyword at a time
        for keyword in keywords[:3]:  # Limit to 3 keywords to avoid too many requests
            params = {
                "description": keyword,
                "location": location,
                "full_time": "true",
            }

            response = requests.get(GITHUB_JOBS_API, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            for job_data in data:
                try:
                    job = _parse_github_job(job_data)
                    if job and job.link not in [j.link for j in jobs]:  # Avoid duplicates
                        jobs.append(job)
                except Exception as e:
                    print(f"Error parsing GitHub job: {e}")
                    continue

    except requests.RequestException as e:
        print(f"GitHub Jobs API request failed: {e}")
        return []

    return jobs

def _parse_github_job(data: dict) -> JobPosting:
    """Convert GitHub Jobs API response to JobPosting."""

    # Extract skills from job data
    skills = _extract_skills(data.get("description", ""))

    # Detect seniority from description
    senioridade = _detect_senioridade(data.get("description", ""))

    job = JobPosting(
        id=data.get("id", str(uuid.uuid4())),
        empresa=data.get("company", "Unknown"),
        titulo=data.get("title", ""),
        descricao=data.get("description", "")[:500],
        requisitos=data.get("description", ""),
        skills_detectadas=skills,
        senioridade=senioridade,
        localizacao=data.get("location", "Remote"),
        link=data.get("url", ""),
        data_coleta=date.today().isoformat(),
        url_empresa=data.get("company_url", ""),
    )

    return job

def _extract_skills(text: str) -> List[str]:
    """Extract known skills from job description."""
    known_skills = [
        "Python", "JavaScript", "TypeScript", "Java", "C#", "PHP",
        "Django", "FastAPI", "Flask", "Node.js", "React", "Vue",
        "AWS", "Docker", "Kubernetes", "PostgreSQL", "MongoDB",
        "Git", "REST API", "GraphQL", "SQL", "Linux",
        "Go", "Rust", "Ruby", "Rails", "Laravel",
        "Airflow", "PySpark", "Spark", "Databricks", "Hadoop",
        "Pandas", "NumPy", "Scikit-learn", "TensorFlow", "PyTorch",
    ]

    text_lower = text.lower()
    found_skills = [skill for skill in known_skills if skill.lower() in text_lower]
    return found_skills

def _detect_senioridade(text: str) -> str:
    """Detect seniority level from job description."""
    text_lower = text.lower()

    if any(word in text_lower for word in ["senior", "staff", "lead", "principal", "sr."]):
        return "Senior"
    elif any(word in text_lower for word in ["mid-level", "intermediate", "pleno"]):
        return "Pleno"
    elif any(word in text_lower for word in ["junior", "entry", "trainee", "jr."]):
        return "Junior"

    return "Pleno"
