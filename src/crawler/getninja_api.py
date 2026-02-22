"""
GetNinja API integration - Brazilian freelance/PJ platform
Free to use, no authentication required
"""
import requests
from typing import List
from src.types import JobPosting
from datetime import date
import uuid
import logging

logger = logging.getLogger(__name__)

GETNINJA_API = "https://api.getninja.com.br"

def search_getninja(keywords: List[str] = None, max_jobs: int = 50) -> List[JobPosting]:
    """
    Search GetNinja for freelance/PJ opportunities.

    GetNinja is a large Brazilian platform for freelance and PJ work.
    API is public and doesn't require authentication.

    Args:
        keywords: Skills to search for
        max_jobs: Maximum jobs to return

    Returns:
        List of JobPosting objects
    """
    if not keywords:
        keywords = ["Python", "Data Engineer"]

    jobs = []

    try:
        logger.info(f"Searching GetNinja for: {', '.join(keywords[:3])}")

        # GetNinja API endpoint for project search
        url = f"{GETNINJA_API}/v1/projects/search"

        params = {
            "q": " ".join(keywords),
            "limit": min(max_jobs, 100),
            "offset": 0,
            "order": "recent"
        }

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/json"
        }

        response = requests.get(url, params=params, headers=headers, timeout=10)

        # GetNinja might return different status codes
        if response.status_code == 200:
            data = response.json()
            projects = data.get("data", data.get("projects", []))

            logger.info(f"GetNinja returned {len(projects)} projects")

            keyword_lower = [k.lower() for k in keywords]
            count = 0

            for project in projects:
                if count >= max_jobs:
                    break

                try:
                    # Filter by keywords
                    title = project.get("title", "").lower()
                    description = project.get("description", "").lower()

                    matches = any(kw in title or kw in description for kw in keyword_lower)

                    if not matches:
                        continue

                    job = _parse_getninja_project(project)
                    if job:
                        jobs.append(job)
                        count += 1

                except Exception as e:
                    logger.debug(f"Error parsing GetNinja project: {e}")
                    continue

            logger.info(f"Found {len(jobs)} matching projects from GetNinja")

        else:
            logger.warning(f"GetNinja API returned status {response.status_code}")

    except requests.RequestException as e:
        logger.warning(f"GetNinja API request failed: {e}")
        return []
    except Exception as e:
        logger.error(f"Error searching GetNinja: {e}")
        return []

    return jobs

def _parse_getninja_project(data: dict) -> JobPosting:
    """Parse GetNinja project response"""
    try:
        title = data.get("title", "")
        description = data.get("description", "")
        budget = data.get("budget", {})
        client = data.get("client", {})

        full_text = f"{title} {description}"
        skills = _extract_skills(full_text)
        senioridade = _detect_senioridade(full_text)

        # Format budget if available
        budget_str = ""
        if budget:
            min_budget = budget.get("min", 0)
            max_budget = budget.get("max", 0)
            if min_budget and max_budget:
                budget_str = f" | Budget: R$ {min_budget:,} - R$ {max_budget:,}"

        job = JobPosting(
            id=str(uuid.uuid4()),
            empresa=client.get("name", "GetNinja Client"),
            titulo=f"{title} (Freelance/PJ){budget_str}",
            descricao=description[:500] if description else "",
            requisitos=description,
            skills_detectadas=skills,
            senioridade=senioridade,
            localizacao="Remoto - Brasil",
            link=data.get("url", "https://www.getninja.com.br"),
            data_coleta=date.today().isoformat(),
            url_empresa="https://www.getninja.com.br",
            salario_min=budget.get("min") if budget else None,
            salario_max=budget.get("max") if budget else None,
        )

        return job

    except Exception as e:
        logger.debug(f"Error parsing GetNinja project: {e}")
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
        "Web Design", "UI/UX", "Mobile", "App",
    ]

    text_lower = text.lower()
    found_skills = [skill for skill in known_skills if skill.lower() in text_lower]
    return list(set(found_skills))

def _detect_senioridade(text: str) -> str:
    """Detect seniority level"""
    text_lower = text.lower()

    if any(word in text_lower for word in ["senior", "staff", "lead", "principal", "expert"]):
        return "Senior"
    elif any(word in text_lower for word in ["mid", "pleno", "intermediate", "experiente"]):
        return "Pleno"
    elif any(word in text_lower for word in ["junior", "entry", "trainee", "iniciante"]):
        return "Junior"

    return "Pleno"
