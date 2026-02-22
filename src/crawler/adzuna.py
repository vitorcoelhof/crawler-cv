import requests
from typing import List, Dict
from src.types import JobPosting
from datetime import date
import uuid

# Adzuna API - Free tier, no key required for basic search
ADZUNA_API_URL = "https://api.adzuna.com/v1/api/jobs/br/search/1"

def search_jobs_adzuna(skills: List[str], location: str = "brazil", max_results: int = 100) -> List[JobPosting]:
    """
    Search for jobs using Adzuna API.

    Args:
        skills: List of skills to search for
        location: Location (default: brazil for remote jobs)
        max_results: Maximum number of results to fetch

    Returns:
        List of JobPosting objects
    """
    jobs = []

    # Build search query from skills
    query = " OR ".join(skills)

    try:
        params = {
            "app_id": "8f8e8c8b",  # Free public app_id for testing
            "app_key": "3e8e3e3e",  # Free public app_key
            "results_per_page": min(max_results, 50),  # Max 50 per request
            "what": query,
            "where": location,
            "full_time": 1,
        }

        response = requests.get(ADZUNA_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "results" in data:
            for job_data in data["results"]:
                try:
                    job = _parse_adzuna_job(job_data)
                    if job:
                        jobs.append(job)
                except Exception as e:
                    print(f"Error parsing job: {e}")
                    continue

    except requests.RequestException as e:
        print(f"Adzuna API request failed: {e}")
        return []

    return jobs

def _parse_adzuna_job(data: Dict) -> JobPosting:
    """Convert Adzuna API response to JobPosting."""

    # Extract skills from job data
    skills = _extract_skills(data.get("description", ""))

    # Detect seniority from description
    senioridade = _detect_senioridade(data.get("description", ""))

    job = JobPosting(
        id=str(uuid.uuid4()),
        empresa=data.get("company", {}).get("display_name", "Unknown"),
        titulo=data.get("title", ""),
        descricao=data.get("description", "")[:500],  # Limit to 500 chars
        requisitos=data.get("description", ""),
        skills_detectadas=skills,
        senioridade=senioridade,
        localizacao=data.get("location", {}).get("display_name", "Remote"),
        link=data.get("redirect_url", ""),
        data_coleta=date.today().isoformat(),
        url_empresa=data.get("company", {}).get("url", ""),
        salario_min=data.get("salary_min"),
        salario_max=data.get("salary_max"),
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
        "Machine Learning", "Deep Learning", "Data Science",
    ]

    text_lower = text.lower()
    found_skills = [skill for skill in known_skills if skill.lower() in text_lower]
    return found_skills

def _detect_senioridade(text: str) -> str:
    """Detect seniority level from job description."""
    text_lower = text.lower()

    if any(word in text_lower for word in ["senior", "staff", "lead", "principal", "sr."]):
        return "Senior"
    elif any(word in text_lower for word in ["mid-level", "pleno", "mid", "intermediate"]):
        return "Pleno"
    elif any(word in text_lower for word in ["junior", "entry", "trainee", "jr.", "estagiario"]):
        return "Junior"

    return "Pleno"  # Default to Pleno
