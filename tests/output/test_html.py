import pytest
from pathlib import Path
from src.output.html import generate_html_report
from src.types import ResumeProfile, JobPosting, Match

@pytest.fixture
def sample_profile():
    return ResumeProfile(
        area="Backend",
        senioridade="Pleno",
        skills=["Python", "Django", "AWS"],
        soft_skills=["Lideranca"],
        anos_experiencia=4,
        keywords=["Backend", "Python"],
    )

@pytest.fixture
def sample_matches():
    job = JobPosting(
        id="1",
        empresa="Acme",
        titulo="Backend Dev",
        descricao="Python + Django",
        requisitos="Python, Django",
        skills_detectadas=["Python", "Django"],
        senioridade="Pleno",
        localizacao="Remoto",
        link="https://acme.com/job/1",
        data_coleta="2026-02-22",
    )
    match = Match(
        vaga=job,
        score=0.85,
        skill_overlap=["Python", "Django"],
        motivo="Match de 2 skills",
    )
    return [match]

def test_generate_html_creates_file(tmp_path, sample_profile, sample_matches):
    output_path = tmp_path / "results.html"
    generate_html_report(sample_profile, sample_matches, str(output_path))
    assert output_path.exists()
    html_content = output_path.read_text()
    assert "Backend" in html_content
    assert "Acme" in html_content
