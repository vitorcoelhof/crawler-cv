# src/types.py
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime

@dataclass
class ResumeProfile:
    """Extracted resume profile"""
    area: str
    senioridade: str  # Junior, Pleno, Senior, Lead
    skills: List[str]
    soft_skills: List[str]
    anos_experiencia: int
    keywords: List[str]
    empresas_anteriores: List[str] = field(default_factory=list)

@dataclass
class JobPosting:
    """Normalized job posting"""
    id: str
    empresa: str
    titulo: str
    descricao: str
    requisitos: str
    skills_detectadas: List[str]
    senioridade: Optional[str]
    localizacao: str
    link: str
    data_coleta: str  # ISO format: 2026-02-22
    ats: Optional[str] = None  # Greenhouse, Gupy, etc
    url_empresa: str = ""
    salario_min: Optional[float] = None
    salario_max: Optional[float] = None

@dataclass
class Match:
    """Score and match result"""
    vaga: JobPosting
    score: float  # 0.0 to 1.0
    skill_overlap: List[str]
    motivo: str
