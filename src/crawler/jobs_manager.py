import json
from typing import List
from pathlib import Path
from src.types import JobPosting

def save_jobs(jobs: List[JobPosting], filepath: str) -> None:
    """
    Save jobs to JSON file.

    Args:
        jobs: List of JobPosting objects
        filepath: Path to save JSON
    """
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)

    jobs_data = [
        {
            "id": job.id,
            "empresa": job.empresa,
            "titulo": job.titulo,
            "descricao": job.descricao,
            "requisitos": job.requisitos,
            "skills_detectadas": job.skills_detectadas,
            "senioridade": job.senioridade,
            "localizacao": job.localizacao,
            "link": job.link,
            "data_coleta": job.data_coleta,
            "ats": job.ats,
            "url_empresa": job.url_empresa,
            "salario_min": job.salario_min,
            "salario_max": job.salario_max,
        }
        for job in jobs
    ]

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(jobs_data, f, indent=2, ensure_ascii=False)

def load_jobs(filepath: str) -> List[JobPosting]:
    """
    Load jobs from JSON file.

    Args:
        filepath: Path to JSON file

    Returns:
        List of JobPosting objects
    """
    if not Path(filepath).exists():
        return []

    with open(filepath, "r", encoding="utf-8") as f:
        jobs_data = json.load(f)

    jobs = [
        JobPosting(
            id=job["id"],
            empresa=job["empresa"],
            titulo=job["titulo"],
            descricao=job["descricao"],
            requisitos=job["requisitos"],
            skills_detectadas=job["skills_detectadas"],
            senioridade=job.get("senioridade"),
            localizacao=job["localizacao"],
            link=job["link"],
            data_coleta=job["data_coleta"],
            ats=job.get("ats"),
            url_empresa=job.get("url_empresa", ""),
            salario_min=job.get("salario_min"),
            salario_max=job.get("salario_max"),
        )
        for job in jobs_data
    ]

    return jobs

def merge_jobs(existing: List[JobPosting], new: List[JobPosting]) -> List[JobPosting]:
    """
    Merge job lists, removing duplicates by link.

    Args:
        existing: Previously saved jobs
        new: Newly scraped jobs

    Returns:
        Merged list with no duplicates
    """
    existing_links = {job.link for job in existing}

    merged = existing.copy()
    for job in new:
        if job.link not in existing_links:
            merged.append(job)
            existing_links.add(job.link)

    return merged
