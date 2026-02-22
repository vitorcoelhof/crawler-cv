import pytest
from src.matching.scorer import score_job, calculate_skill_overlap, _senioridade_score
from src.types import ResumeProfile, JobPosting, Match

@pytest.fixture
def sample_profile():
    return ResumeProfile(
        area="Backend",
        senioridade="Pleno",
        skills=["Python", "Django", "AWS", "PostgreSQL"],
        soft_skills=["Lideranca"],
        anos_experiencia=4,
        keywords=["Backend", "Python", "AWS"],
    )

@pytest.fixture
def sample_job():
    return JobPosting(
        id="job-1",
        empresa="Acme Corp",
        titulo="Backend Developer",
        descricao="Python Django developer for AWS infrastructure",
        requisitos="Python, Django, AWS, Docker",
        skills_detectadas=["Python", "Django", "AWS", "Docker"],
        senioridade="Pleno",
        localizacao="Remoto",
        link="https://acme.com/jobs/1",
        data_coleta="2026-02-22",
    )

def test_calculate_skill_overlap(sample_profile, sample_job):
    overlap = calculate_skill_overlap(sample_profile.skills, sample_job.skills_detectadas)
    assert overlap > 0
    assert overlap <= 1.0

def test_score_job_returns_match(sample_profile, sample_job):
    match = score_job(sample_profile, sample_job)
    assert isinstance(match, Match)
    assert 0 <= match.score <= 1.0
    assert match.vaga == sample_job

def test_senioridade_match_logic():
    # Perfect match
    assert _senioridade_score("Pleno", "Pleno") == 1.0

    # One level difference is good
    assert _senioridade_score("Pleno", "Senior") > 0.7
    assert _senioridade_score("Pleno", "Junior") > 0.7

    # Two levels difference is worse
    assert _senioridade_score("Junior", "Senior") < 0.7
