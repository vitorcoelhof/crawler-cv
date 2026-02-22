import requests
from typing import List
from src.types import JobPosting
from datetime import date
import uuid
from bs4 import BeautifulSoup

# Popular Brazilian companies using Gupy
GUPY_COMPANIES = [
    {"name": "PicPay", "url": "https://picpay.gupy.io/"},
    {"name": "Dock", "url": "https://dock.gupy.io/"},
    {"name": "Ioasys", "url": "https://ioasys.gupy.io/"},
    {"name": "Letras", "url": "https://letras.gupy.io/"},
    {"name": "Afya", "url": "https://afya.gupy.io/"},
    {"name": "ATTA", "url": "https://atta.gupy.io/"},
    {"name": "Alpargatas", "url": "https://alpargatas.gupy.io/"},
    {"name": "Hi Platform", "url": "https://hiplatform.gupy.io/"},
    {"name": "Acesso Digital", "url": "https://acessodigital.gupy.io/"},
    {"name": "Builders", "url": "https://builders.gupy.io/"},
]

def search_jobs_gupy() -> List[JobPosting]:
    """
    Scrape jobs from Gupy-based company career pages.

    Returns:
        List of JobPosting objects
    """
    jobs = []

    for company in GUPY_COMPANIES:
        try:
            company_jobs = _scrape_gupy_company(company["name"], company["url"])
            jobs.extend(company_jobs)
        except Exception as e:
            print(f"Error scraping {company['name']}: {e}")
            continue

    return jobs

def _scrape_gupy_company(company_name: str, gupy_url: str) -> List[JobPosting]:
    """
    Scrape jobs from a specific Gupy career page.

    Args:
        company_name: Name of the company
        gupy_url: URL of the company's Gupy page

    Returns:
        List of JobPosting objects
    """
    jobs = []

    try:
        # Try to fetch the page
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(gupy_url, headers=headers, timeout=10)
        response.raise_for_status()

        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.content, "html.parser")

        # Try to find job listings (Gupy uses various CSS classes)
        job_elements = soup.find_all("div", class_=["job-item", "job-card", "position", "opening"])

        if not job_elements:
            # Try alternative selectors
            job_elements = soup.find_all("article")

        for job_elem in job_elements[:10]:  # Limit to 10 per company
            try:
                # Extract job info
                title_elem = job_elem.find(["h2", "h3", "a"])
                title = title_elem.text.strip() if title_elem else None

                if not title:
                    continue

                # Try to find description
                desc_elem = job_elem.find("p")
                description = desc_elem.text.strip() if desc_elem else ""

                # Create JobPosting
                job = JobPosting(
                    id=str(uuid.uuid4()),
                    empresa=company_name,
                    titulo=title,
                    descricao=description[:500],
                    requisitos=description,
                    skills_detectadas=_extract_skills(title + " " + description),
                    senioridade=_detect_senioridade(title + " " + description),
                    localizacao="Remoto - Brasil",
                    link=gupy_url,
                    data_coleta=date.today().isoformat(),
                    url_empresa=gupy_url.replace("/careers", "").replace("/jobs", ""),
                )

                jobs.append(job)

            except Exception as e:
                print(f"Error parsing job from {company_name}: {e}")
                continue

    except requests.RequestException as e:
        print(f"Error fetching {gupy_url}: {e}")

    return jobs

def _extract_skills(text: str) -> List[str]:
    """Extract known skills from job description."""
    known_skills = [
        "Python", "JavaScript", "TypeScript", "Java", "C#", "PHP",
        "Django", "FastAPI", "Flask", "Node.js", "React", "Vue",
        "AWS", "Docker", "Kubernetes", "PostgreSQL", "MongoDB",
        "Git", "REST API", "GraphQL", "SQL", "Linux",
        "Go", "Rust", "Ruby", "Rails", "Laravel",
        "Airflow", "PySpark", "Spark", "Databricks",
    ]

    text_lower = text.lower()
    found_skills = [skill for skill in known_skills if skill.lower() in text_lower]
    return found_skills

def _detect_senioridade(text: str) -> str:
    """Detect seniority level from job description."""
    text_lower = text.lower()

    if any(word in text_lower for word in ["senior", "staff", "lead", "principal"]):
        return "Senior"
    elif any(word in text_lower for word in ["mid-level", "intermediate", "pleno"]):
        return "Pleno"
    elif any(word in text_lower for word in ["junior", "entry", "trainee"]):
        return "Junior"

    return "Pleno"
