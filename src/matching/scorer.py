from typing import List
from src.types import ResumeProfile, JobPosting, Match
from src.config import SKILLS_WEIGHT, SENIORIDADE_WEIGHT, SEMANTIC_WEIGHT

def score_job(profile: ResumeProfile, job: JobPosting) -> Match:
    """
    Score a job posting against a resume profile.

    Scoring formula:
    score = 0.5 * skill_overlap + 0.3 * senioridade_match + 0.2 * semantic_similarity

    Args:
        profile: Analyzed resume profile
        job: Job posting

    Returns:
        Match object with score and reasoning
    """
    # Component 1: Skill overlap (50%)
    skill_overlap = calculate_skill_overlap(profile.skills, job.skills_detectadas)
    overlapping_skills = [
        s for s in profile.skills
        if s.lower() in [j.lower() for j in job.skills_detectadas]
    ]

    # Component 2: Senioridade match (30%)
    senioridade_score = _senioridade_score(profile.senioridade, job.senioridade)

    # Component 3: Semantic similarity (20%) - simplified for MVP
    semantic_score = _calculate_semantic_similarity(profile.keywords, job.descricao)

    # Weighted average
    final_score = (
        SKILLS_WEIGHT * skill_overlap +
        SENIORIDADE_WEIGHT * senioridade_score +
        SEMANTIC_WEIGHT * semantic_score
    )

    # Build reasoning
    reasons = []
    if overlapping_skills:
        reasons.append(f"Match de {len(overlapping_skills)} skills: {', '.join(overlapping_skills[:3])}")
    if senioridade_score > 0.7:
        reasons.append(f"Senioridade compativel ({profile.senioridade} -> {job.senioridade})")
    if semantic_score > 0.5:
        reasons.append("Descricao alinhada com seu perfil")

    motivo = "; ".join(reasons) if reasons else "Perfil parcialmente alinhado"

    return Match(
        vaga=job,
        score=final_score,
        skill_overlap=overlapping_skills,
        motivo=motivo,
    )

def calculate_skill_overlap(resume_skills: List[str], job_skills: List[str]) -> float:
    """
    Calculate overlap between resume and job required skills.

    Returns:
        Percentage (0.0 - 1.0)
    """
    if not job_skills:
        return 0.5  # Neutral if no skills detected in job

    resume_lower = {s.lower() for s in resume_skills}
    job_lower = {s.lower() for s in job_skills}

    overlap_count = len(resume_lower & job_lower)
    return min(1.0, overlap_count / len(job_lower))

def _senioridade_score(resume_senioridade: str, job_senioridade: str) -> float:
    """
    Score senioridade compatibility.

    Returns:
        Score (0.0 - 1.0)
    """
    if not job_senioridade:
        return 0.5  # Neutral if not specified

    seniority_levels = {
        "Junior": 0,
        "Pleno": 1,
        "Senior": 2,
        "Lead": 3,
    }

    resume_level = seniority_levels.get(resume_senioridade, 1)
    job_level = seniority_levels.get(job_senioridade, 1)

    # Perfect match
    if resume_level == job_level:
        return 1.0

    # One level difference
    if abs(resume_level - job_level) == 1:
        return 0.8

    # Two levels difference
    if abs(resume_level - job_level) == 2:
        return 0.5

    # Three+ levels
    return 0.2

def _calculate_semantic_similarity(keywords: List[str], description: str) -> float:
    """
    Simple semantic similarity: count keyword matches in description.
    For MVP, just count occurrences. Can be enhanced with embeddings later.

    Returns:
        Score (0.0 - 1.0)
    """
    if not keywords or not description:
        return 0.5

    description_lower = description.lower()
    matches = sum(1 for kw in keywords if kw.lower() in description_lower)

    return min(1.0, matches / len(keywords))
