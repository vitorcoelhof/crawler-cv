import json
import re
from typing import Optional
from groq import Groq
from src.types import ResumeProfile
from src.config import GROQ_API_KEY

def analyze_resume_with_groq(resume_text: str) -> ResumeProfile:
    """
    Analyze resume text using Groq API (Llama 3.3 70B).

    Args:
        resume_text: Raw resume text

    Returns:
        ResumeProfile with extracted information
    """
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not set in environment")

    client = Groq(api_key=GROQ_API_KEY)

    prompt = f"""Analise este currículo e retorne APENAS um JSON com as seguintes chaves:

{{
  "area": "Backend|Frontend|Data|Product|Design|QA",
  "senioridade": "Junior|Pleno|Senior|Lead",
  "skills": ["skill1", "skill2", ...],
  "soft_skills": ["skill1", "skill2", ...],
  "anos_experiencia": <número>,
  "keywords": ["palavra1", "palavra2", ...]
}}

Currículo:
{resume_text}

Retorne APENAS o JSON, sem explicações adicionais."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    response_text = response.choices[0].message.content
    json_str = _extract_json_from_response(response_text)
    data = json.loads(json_str)

    return ResumeProfile(
        area=data.get("area", "Backend"),
        senioridade=data.get("senioridade", "Pleno"),
        skills=data.get("skills", []),
        soft_skills=data.get("soft_skills", []),
        anos_experiencia=data.get("anos_experiencia", 0),
        keywords=data.get("keywords", []),
        empresas_anteriores=data.get("empresas_anteriores", [])
    )

def _extract_json_from_response(response_text: str) -> str:
    """
    Extract JSON object from response text.
    Handles cases where the response contains extra text.
    """
    # Find JSON object in response
    match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
    if match:
        return match.group()
    raise ValueError(f"Could not extract JSON from response: {response_text}")
