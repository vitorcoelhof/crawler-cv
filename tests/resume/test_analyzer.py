import pytest
import json
from src.resume.analyzer import analyze_resume_with_groq, _extract_json_from_response
from src.types import ResumeProfile

@pytest.fixture
def sample_resume_text():
    return """
    João Silva
    Desenvolvedor Backend Pleno

    Experiência: 4 anos

    Habilidades Técnicas:
    - Python (3 anos)
    - Django (2 anos)
    - PostgreSQL (2 anos)
    - AWS (1 ano)
    - Docker (1 ano)

    Habilidades Comportamentais:
    - Liderança de equipe
    - Comunicação clara
    - Resolução de problemas

    Empresas anteriores:
    - Empresa A (2020-2022)
    - Empresa B (2022-atual)
    """

@pytest.mark.skip(reason="Requires GROQ_API_KEY")
def test_analyze_resume_returns_profile(sample_resume_text):
    profile = analyze_resume_with_groq(sample_resume_text)
    assert isinstance(profile, ResumeProfile)
    assert profile.area in ["Backend", "Frontend", "Data", "Product", "Design", "QA"]
    assert profile.senioridade in ["Junior", "Pleno", "Senior", "Lead"]
    assert len(profile.skills) > 0
    assert profile.anos_experiencia > 0

def test_analyze_resume_extract_json_mock():
    """Test JSON extraction without API call"""
    mock_response = """
    Some preamble text
    {
      "area": "Backend",
      "senioridade": "Pleno",
      "skills": ["Python", "Django"],
      "soft_skills": ["Lideranca"],
      "anos_experiencia": 4,
      "keywords": ["Backend", "Python"]
    }
    Some footer text
    """

    json_str = _extract_json_from_response(mock_response)
    data = json.loads(json_str)
    assert data["area"] == "Backend"
    assert "Python" in data["skills"]
