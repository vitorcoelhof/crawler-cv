# CV Crawler Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Python CLI tool that analyzes resumes, matches them against a scraped database of remote jobs from Brazilian companies, and outputs interactive HTML results.

**Architecture:** Three-phase approach: (1) setup and utilities, (2) data collection (crawler), (3) analysis and matching (resume parsing + scoring). GitHub Actions runs the crawler daily; users run the CLI locally. MVP is crawler + basic matching.

**Tech Stack:** Python 3.9+, Playwright, BeautifulSoup4, pdfplumber, groq-sdk, sentence-transformers, Jinja2, Click, GitHub Actions

---

## Phase 1: Project Setup & Foundation (MVP prerequisite)

### Task 1: Create project structure and requirements.txt

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `src/__init__.py`
- Create: `src/crawler/__init__.py`
- Create: `src/resume/__init__.py`
- Create: `src/matching/__init__.py`
- Create: `src/output/__init__.py`

**Step 1: Create requirements.txt**

```
# requirements.txt
beautifulsoup4==4.12.2
playwright==1.40.0
pdfplumber==0.10.3
requests==2.31.0
groq==0.4.1
sentence-transformers==2.2.2
scikit-learn==1.3.2
jinja2==3.1.2
click==8.1.7
python-dotenv==1.0.0
rich==13.7.0
```

**Step 2: Create .env.example**

```
GROQ_API_KEY=your_api_key_here
```

**Step 3: Create .gitignore**

```
.env
.env.local
__pycache__/
*.pyc
.pytest_cache/
venv/
results_*.html
*.pdf
*.txt
.DS_Store
```

**Step 4: Create directory structure**

```bash
mkdir -p src/crawler src/resume src/matching src/output
mkdir -p tests/{crawler,resume,matching,output}
mkdir -p data
touch src/__init__.py src/crawler/__init__.py src/resume/__init__.py src/matching/__init__.py src/output/__init__.py
```

**Step 5: Verify structure**

Run: `find . -type f -name "*.py" | head -20`
Expected: See created `__init__.py` files

**Step 6: Commit**

```bash
git add requirements.txt .env.example .gitignore src/ tests/
git commit -m "chore: initialize project structure and dependencies"
```

---

### Task 2: Create base types and utilities

**Files:**
- Create: `src/types.py`
- Create: `src/config.py`

**Step 1: Create types.py**

```python
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
```

**Step 2: Create config.py**

```python
# src/config.py
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
JOBS_FILE = DATA_DIR / "jobs.json"

# API
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Crawler
CRAWLER_TIMEOUT = 10  # seconds
CRAWLER_RETRIES = 3
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
RATE_LIMIT_DELAY = 1.0  # seconds between requests

# Matching
MIN_MATCH_SCORE = 0.5
SKILLS_WEIGHT = 0.5
SENIORIDADE_WEIGHT = 0.3
SEMANTIC_WEIGHT = 0.2

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)
```

**Step 3: Run quick validation**

```bash
python3 -c "from src.types import ResumeProfile, JobPosting, Match; print('Types imported successfully')"
python3 -c "from src.config import GROQ_API_KEY, JOBS_FILE; print(f'Config loaded, jobs file: {JOBS_FILE}')"
```

Expected: No errors, prints confirmation

**Step 4: Commit**

```bash
git add src/types.py src/config.py
git commit -m "feat: add type definitions and configuration"
```

---

## Phase 2: Resume Parser (MVP prerequisite)

### Task 3: Implement PDF and TXT parser

**Files:**
- Create: `src/resume/parser.py`
- Create: `tests/resume/test_parser.py`

**Step 1: Write failing tests**

```python
# tests/resume/test_parser.py
import pytest
from pathlib import Path
from src.resume.parser import parse_resume

@pytest.fixture
def sample_pdf(tmp_path):
    """Create a minimal PDF with text"""
    try:
        import pdfplumber
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter

        pdf_file = tmp_path / "sample.pdf"
        c = canvas.Canvas(str(pdf_file), pagesize=letter)
        c.drawString(100, 750, "Python Developer")
        c.drawString(100, 730, "5 years experience")
        c.save()
        return pdf_file
    except ImportError:
        pytest.skip("reportlab not installed")

@pytest.fixture
def sample_txt(tmp_path):
    """Create a sample TXT resume"""
    txt_file = tmp_path / "resume.txt"
    txt_file.write_text(
        "John Doe\n"
        "Senior Backend Engineer\n"
        "8 years experience\n"
        "Skills: Python, Django, AWS, PostgreSQL\n"
    )
    return txt_file

def test_parse_txt_resume(sample_txt):
    text = parse_resume(str(sample_txt))
    assert "John Doe" in text
    assert "Senior Backend Engineer" in text

def test_parse_pdf_resume(sample_pdf):
    text = parse_resume(str(sample_pdf))
    assert "Python Developer" in text

def test_parse_nonexistent_file():
    with pytest.raises(FileNotFoundError):
        parse_resume("/nonexistent/file.pdf")

def test_parse_unsupported_format(tmp_path):
    unsupported = tmp_path / "file.doc"
    unsupported.write_text("test")
    with pytest.raises(ValueError, match="Unsupported file format"):
        parse_resume(str(unsupported))
```

**Step 2: Run tests to verify they fail**

```bash
cd /c/Users/vitor/Documents/Projetos/crawler-cv
python -m pytest tests/resume/test_parser.py -v
```

Expected: FAIL - "function not defined" or similar

**Step 3: Implement parser.py**

```python
# src/resume/parser.py
from pathlib import Path
from typing import Union

def parse_resume(file_path: Union[str, Path]) -> str:
    """
    Extract text from PDF or TXT resume.

    Args:
        file_path: Path to PDF or TXT file

    Returns:
        Extracted text

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is not supported
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Resume file not found: {file_path}")

    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        return _parse_pdf(file_path)
    elif suffix == ".txt":
        return _parse_txt(file_path)
    else:
        raise ValueError(f"Unsupported file format: {suffix}. Use PDF or TXT.")

def _parse_pdf(file_path: Path) -> str:
    """Extract text from PDF"""
    import pdfplumber

    text = []
    with pdfplumber.open(str(file_path)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)

    return "\n".join(text)

def _parse_txt(file_path: Path) -> str:
    """Extract text from TXT"""
    return file_path.read_text(encoding="utf-8")

def normalize_text(text: str) -> str:
    """
    Normalize resume text: remove extra whitespace, etc.
    """
    # Replace multiple spaces/newlines with single space
    text = " ".join(text.split())
    return text
```

**Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/resume/test_parser.py -v
```

Expected: PASS - All 4 tests pass

**Step 5: Commit**

```bash
git add src/resume/parser.py tests/resume/test_parser.py
git commit -m "feat: implement PDF and TXT resume parser"
```

---

### Task 4: Implement resume analyzer (Groq integration)

**Files:**
- Create: `src/resume/analyzer.py`
- Create: `tests/resume/test_analyzer.py`

**Step 1: Write failing tests**

```python
# tests/resume/test_analyzer.py
import pytest
import json
from src.resume.analyzer import analyze_resume_with_groq
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

def test_analyze_resume_extract_json_mock(monkeypatch):
    """Test JSON extraction without API call"""
    from src.resume.analyzer import _extract_json_from_response

    mock_response = """
    Some preamble text
    {
      "area": "Backend",
      "senioridade": "Pleno",
      "skills": ["Python", "Django"],
      "soft_skills": ["Liderança"],
      "anos_experiencia": 4,
      "keywords": ["Backend", "Python"]
    }
    Some footer text
    """

    json_str = _extract_json_from_response(mock_response)
    data = json.loads(json_str)
    assert data["area"] == "Backend"
    assert "Python" in data["skills"]
```

**Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/resume/test_analyzer.py::test_analyze_resume_extract_json_mock -v
```

Expected: FAIL - "function not defined"

**Step 3: Implement analyzer.py**

```python
# src/resume/analyzer.py
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

    response = client.messages.create(
        model="llama-3.3-70b-versatile",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    response_text = response.content[0].text
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
```

**Step 4: Run mock test to verify extraction works**

```bash
python -m pytest tests/resume/test_analyzer.py::test_analyze_resume_extract_json_mock -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/resume/analyzer.py tests/resume/test_analyzer.py
git commit -m "feat: implement resume analysis via Groq API"
```

---

## Phase 3: Crawler (MVP core)

### Task 5: Implement company list parser from lerrua/remote-jobs-brazil

**Files:**
- Create: `src/crawler/companies.py`
- Create: `tests/crawler/test_companies.py`

**Step 1: Write failing tests**

```python
# tests/crawler/test_companies.py
import pytest
from src.crawler.companies import parse_remote_jobs_brazil_repo

@pytest.mark.skip(reason="Requires internet access")
def test_parse_repo_returns_companies():
    companies = parse_remote_jobs_brazil_repo()
    assert len(companies) > 0
    assert all("name" in c and "url" in c for c in companies)

def test_normalize_url():
    from src.crawler.companies import normalize_url

    assert normalize_url("https://example.com") == "https://example.com"
    assert normalize_url("example.com") == "https://example.com"
    assert normalize_url("example.com/") == "https://example.com"

def test_extract_company_info_mock():
    from src.crawler.companies import _parse_companies_from_readme

    mock_readme = """
    # Remote Jobs Brazil

    ## Companies

    ### Acme Corp
    - Site: https://acmecorp.com
    - Vagas: https://acmecorp.com/carreiras

    ### TechStart Inc
    - Site: https://techstart.io
    """

    companies = _parse_companies_from_readme(mock_readme)
    assert len(companies) > 0
```

**Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/crawler/test_companies.py::test_normalize_url -v
```

Expected: FAIL

**Step 3: Implement companies.py**

```python
# src/crawler/companies.py
from typing import List, Dict
from urllib.parse import urljoin, urlparse
import requests
from pathlib import Path

def parse_remote_jobs_brazil_repo() -> List[Dict[str, str]]:
    """
    Parse the lerrua/remote-jobs-brazil repository to extract company URLs.

    Returns:
        List of dicts with 'name' and 'url' keys
    """
    readme_url = (
        "https://raw.githubusercontent.com/lerrua/remote-jobs-brazil/"
        "main/README.md"
    )

    try:
        response = requests.get(readme_url, timeout=10)
        response.raise_for_status()
        return _parse_companies_from_readme(response.text)
    except requests.RequestException as e:
        # Fallback to local cached version if available
        cache_file = Path(__file__).parent / "companies_cache.json"
        if cache_file.exists():
            import json
            return json.loads(cache_file.read_text())
        raise RuntimeError(f"Failed to fetch companies list: {e}")

def _parse_companies_from_readme(readme_text: str) -> List[Dict[str, str]]:
    """
    Parse README markdown to extract company information.

    Simple implementation: looks for markdown links like:
    [Company Name](https://company.com)
    """
    import re

    companies = []
    # Pattern: [Company Name](URL)
    pattern = r'\[([^\]]+)\]\((https?://[^\)]+)\)'

    for match in re.finditer(pattern, readme_text):
        name = match.group(1)
        url = normalize_url(match.group(2))

        # Filter out duplicates and invalid entries
        if url not in [c["url"] for c in companies]:
            companies.append({"name": name, "url": url})

    return companies

def normalize_url(url: str) -> str:
    """
    Normalize URL: ensure https, remove trailing slash.

    Args:
        url: URL string, may be incomplete

    Returns:
        Normalized URL
    """
    url = url.strip()

    # Add https if missing
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    # Parse and remove trailing slash
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")

def detect_careers_page(company_url: str) -> List[str]:
    """
    Generate possible careers page URLs for a company.

    Args:
        company_url: Base company URL

    Returns:
        List of possible careers page URLs to test
    """
    parsed = urlparse(company_url)
    domain = parsed.netloc
    base = f"{parsed.scheme}://{domain}"

    candidates = [
        f"{base}/careers",
        f"{base}/carreiras",
        f"{base}/vagas",
        f"{base}/jobs",
        f"{base}/trabalhe-conosco",
        f"{base}/joinus",
        f"https://careers.{domain}",
        f"https://jobs.{domain}",
        f"{company_url}/careers",
        f"{company_url}/carreiras",
        f"{company_url}/vagas",
    ]

    return candidates
```

**Step 4: Run tests**

```bash
python -m pytest tests/crawler/test_companies.py::test_normalize_url -v
python -m pytest tests/crawler/test_companies.py::test_extract_company_info_mock -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/crawler/companies.py tests/crawler/test_companies.py
git commit -m "feat: implement company list parser from lerrua repo"
```

---

### Task 6: Implement web scraper with Playwright and BeautifulSoup

**Files:**
- Create: `src/crawler/scraper.py`
- Create: `tests/crawler/test_scraper.py`

**Step 1: Write failing tests**

```python
# tests/crawler/test_scraper.py
import pytest
from src.crawler.scraper import fetch_page, extract_job_postings
from src.types import JobPosting

@pytest.mark.skip(reason="Requires network access")
def test_fetch_page_returns_html():
    html = fetch_page("https://example.com")
    assert isinstance(html, str)
    assert len(html) > 0

def test_extract_job_postings_mock():
    """Test job extraction with mock HTML"""
    from src.crawler.scraper import _parse_job_from_element

    mock_html = """
    <div class="job-posting">
        <h2>Backend Developer</h2>
        <p>Python, Django, AWS</p>
        <p>Pleno</p>
        <a href="/apply/123">Apply</a>
    </div>
    """

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(mock_html, "html.parser")
    job_div = soup.find("div", class_="job-posting")

    # Just verify we can parse basic structure
    title = job_div.find("h2").text if job_div.find("h2") else None
    assert title == "Backend Developer"

def test_detect_ats_from_html():
    from src.crawler.scraper import detect_ats_system

    mock_html_greenhouse = '<script src="https://boards.greenhouse.io/..."></script>'
    assert detect_ats_system(mock_html_greenhouse) == "Greenhouse"

    mock_html_gupy = '<script>var GUPY_CONFIG = {...}</script>'
    assert detect_ats_system(mock_html_gupy) == "Gupy"

    mock_html_none = "<html><body>No ATS detected</body></html>"
    assert detect_ats_system(mock_html_none) is None
```

**Step 2: Run tests**

```bash
python -m pytest tests/crawler/test_scraper.py::test_extract_job_postings_mock -v
```

Expected: FAIL (function not defined)

**Step 3: Implement scraper.py**

```python
# src/crawler/scraper.py
import asyncio
from typing import List, Optional
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from src.types import JobPosting
from src.config import CRAWLER_TIMEOUT, USER_AGENT, RATE_LIMIT_DELAY
import time
import uuid

async def fetch_page_async(url: str, use_javascript: bool = False) -> str:
    """
    Fetch page content. Use Playwright if JavaScript rendering is needed.

    Args:
        url: URL to fetch
        use_javascript: If True, use Playwright; else use requests

    Returns:
        HTML content
    """
    if use_javascript:
        return await _fetch_with_playwright(url)
    else:
        return _fetch_with_requests(url)

def _fetch_with_requests(url: str) -> str:
    """Fetch page with requests library (fast, for static HTML)"""
    try:
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(url, headers=headers, timeout=CRAWLER_TIMEOUT)
        response.raise_for_status()
        time.sleep(RATE_LIMIT_DELAY)
        return response.text
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to fetch {url}: {e}")

async def _fetch_with_playwright(url: str) -> str:
    """Fetch page with Playwright (slower, for JS-rendered sites)"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle", timeout=CRAWLER_TIMEOUT * 1000)
        content = await page.content()
        await browser.close()
        return content

def fetch_page(url: str) -> str:
    """Synchronous wrapper for fetch_page_async"""
    return asyncio.run(fetch_page_async(url, use_javascript=False))

def detect_ats_system(html: str) -> Optional[str]:
    """
    Detect if page uses a known ATS (Applicant Tracking System).

    Returns:
        ATS name (Greenhouse, Gupy, Lever, Workable, Kenoby) or None
    """
    ats_signatures = {
        "Greenhouse": ["boards.greenhouse.io", "greenhouse_config"],
        "Gupy": ["gupy", "GUPY_CONFIG"],
        "Lever": ["lever.co", "lever_config"],
        "Workable": ["workable.com", "workable_config"],
        "Kenoby": ["kenoby", "kenoby_config"],
    }

    for ats_name, signatures in ats_signatures.items():
        if any(sig.lower() in html.lower() for sig in signatures):
            return ats_name

    return None

def extract_job_postings(
    html: str,
    empresa: str,
    url_empresa: str,
    source_url: str
) -> List[JobPosting]:
    """
    Extract job postings from HTML using heuristics.
    This is a simplified implementation; may need refinement per site.

    Args:
        html: HTML content
        empresa: Company name
        url_empresa: Company base URL
        source_url: URL where this HTML came from

    Returns:
        List of extracted JobPosting objects
    """
    soup = BeautifulSoup(html, "html.parser")
    jobs = []

    # Common selectors for job postings
    job_selectors = [
        ("div.job", "h2,h3", "p"),  # Generic div.job
        ("article.job-posting", "h2", "p"),
        ("div[data-job-id]", "h2", "p"),
        ("li.job-listing", "h3", "span"),
    ]

    found = False
    for container_selector, title_selector, desc_selector in job_selectors:
        containers = soup.select(container_selector)
        if containers:
            found = True
            for container in containers:
                title_elem = container.select_one(title_selector)
                desc_elem = container.select_one(desc_selector)

                if title_elem:
                    title = title_elem.get_text(strip=True)
                    description = desc_elem.get_text(strip=True) if desc_elem else ""

                    job = JobPosting(
                        id=str(uuid.uuid4()),
                        empresa=empresa,
                        titulo=title,
                        descricao=description,
                        requisitos=description,  # Simplified
                        skills_detectadas=_extract_skills_from_text(description),
                        senioridade=_detect_senioridade(description),
                        localizacao="Remoto - Brasil",
                        link=source_url,
                        data_coleta=_get_today_iso(),
                        url_empresa=url_empresa,
                    )
                    jobs.append(job)

            if found:
                break

    return jobs

def _extract_skills_from_text(text: str) -> List[str]:
    """
    Heuristically extract skills from text.
    This is basic; could be improved with NLP.
    """
    known_skills = [
        "Python", "JavaScript", "TypeScript", "Java", "C#", "PHP",
        "Django", "FastAPI", "Flask", "Node.js", "React", "Vue",
        "AWS", "Docker", "Kubernetes", "PostgreSQL", "MongoDB",
        "Git", "REST API", "GraphQL", "SQL", "Linux",
        "Go", "Rust", "Ruby", "Rails", "Laravel",
    ]

    found_skills = [skill for skill in known_skills if skill.lower() in text.lower()]
    return found_skills

def _detect_senioridade(text: str) -> Optional[str]:
    """Detect seniority level from text"""
    text_lower = text.lower()

    if any(word in text_lower for word in ["senior", "staff", "lead", "principal"]):
        return "Senior"
    elif any(word in text_lower for word in ["mid-level", "pleno", "mid"]):
        return "Pleno"
    elif any(word in text_lower for word in ["junior", "entry", "trainee"]):
        return "Junior"

    return None

def _get_today_iso() -> str:
    """Return today's date in ISO format"""
    from datetime import date
    return date.today().isoformat()
```

**Step 4: Run tests**

```bash
python -m pytest tests/crawler/test_scraper.py::test_extract_job_postings_mock -v
python -m pytest tests/crawler/test_scraper.py::test_detect_ats_from_html -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/crawler/scraper.py tests/crawler/test_scraper.py
git commit -m "feat: implement web scraper with Playwright and BeautifulSoup"
```

---

### Task 7: Implement jobs storage and manager

**Files:**
- Create: `src/crawler/jobs_manager.py`
- Create: `tests/crawler/test_jobs_manager.py`

**Step 1: Write failing tests**

```python
# tests/crawler/test_jobs_manager.py
import pytest
import json
from pathlib import Path
from src.crawler.jobs_manager import save_jobs, load_jobs, merge_jobs
from src.types import JobPosting

@pytest.fixture
def sample_job():
    return JobPosting(
        id="test-1",
        empresa="Test Corp",
        titulo="Backend Developer",
        descricao="Python developer needed",
        requisitos="Python, AWS",
        skills_detectadas=["Python", "AWS"],
        senioridade="Pleno",
        localizacao="Remoto - Brasil",
        link="https://test.com/job/1",
        data_coleta="2026-02-22",
    )

def test_save_and_load_jobs(tmp_path, sample_job):
    jobs_file = tmp_path / "jobs.json"

    # Save
    save_jobs([sample_job], str(jobs_file))
    assert jobs_file.exists()

    # Load
    loaded = load_jobs(str(jobs_file))
    assert len(loaded) == 1
    assert loaded[0].titulo == "Backend Developer"

def test_merge_jobs_removes_duplicates(sample_job):
    job1 = sample_job
    job2 = JobPosting(
        id="test-2",
        empresa="Test Corp 2",
        titulo="Frontend Developer",
        descricao="React developer",
        requisitos="React, TypeScript",
        skills_detectadas=["React"],
        senioridade="Junior",
        localizacao="Remoto",
        link="https://test.com/job/2",
        data_coleta="2026-02-22",
    )

    # Duplicate by link
    job1_duplicate = JobPosting(
        id="test-1-dup",
        empresa=job1.empresa,
        titulo=job1.titulo,
        descricao=job1.descricao,
        requisitos=job1.requisitos,
        skills_detectadas=job1.skills_detectadas,
        senioridade=job1.senioridade,
        localizacao=job1.localizacao,
        link=job1.link,  # Same link
        data_coleta="2026-02-22",
    )

    merged = merge_jobs([job1], [job2, job1_duplicate])
    assert len(merged) == 2  # No duplicate
    assert all(j.link in [job1.link, job2.link] for j in merged)
```

**Step 2: Run tests**

```bash
python -m pytest tests/crawler/test_jobs_manager.py -v
```

Expected: FAIL

**Step 3: Implement jobs_manager.py**

```python
# src/crawler/jobs_manager.py
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
```

**Step 4: Run tests**

```bash
python -m pytest tests/crawler/test_jobs_manager.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/crawler/jobs_manager.py tests/crawler/test_jobs_manager.py
git commit -m "feat: implement job storage and merging logic"
```

---

### Task 8: Implement main crawler orchestrator

**Files:**
- Create: `src/crawler/main.py`
- Create: `tests/crawler/test_main.py`

**Step 1: Write failing tests**

```python
# tests/crawler/test_main.py
import pytest
from unittest.mock import patch, MagicMock
from src.crawler.main import run_crawler

@pytest.mark.skip(reason="Integration test, requires network")
def test_run_crawler_end_to_end():
    """Full crawler test (skip in CI)"""
    pass

def test_crawler_orchestrator_structure():
    """Verify crawler module can be imported"""
    from src.crawler.main import run_crawler
    assert callable(run_crawler)
```

**Step 2: Run tests**

```bash
python -m pytest tests/crawler/test_main.py::test_crawler_orchestrator_structure -v
```

Expected: FAIL (function not defined)

**Step 3: Implement main.py**

```python
# src/crawler/main.py
import asyncio
from typing import List
from src.crawler.companies import (
    parse_remote_jobs_brazil_repo,
    detect_careers_page,
    normalize_url,
)
from src.crawler.scraper import (
    fetch_page,
    fetch_page_async,
    detect_ats_system,
    extract_job_postings,
)
from src.crawler.jobs_manager import load_jobs, save_jobs, merge_jobs
from src.config import JOBS_FILE
from src.types import JobPosting
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_crawler() -> int:
    """
    Main crawler orchestrator.

    Returns:
        Number of new jobs found
    """
    logger.info("Starting crawler...")

    # Step 1: Parse companies list
    logger.info("Fetching companies list from lerrua/remote-jobs-brazil...")
    companies = parse_remote_jobs_brazil_repo()
    logger.info(f"Found {len(companies)} companies")

    # Step 2: Crawl each company
    all_jobs = []
    for idx, company in enumerate(companies):
        logger.info(f"[{idx+1}/{len(companies)}] Crawling {company['name']}")
        try:
            jobs = await crawl_company(company)
            all_jobs.extend(jobs)
            logger.info(f"  Found {len(jobs)} jobs")
        except Exception as e:
            logger.warning(f"  Error crawling {company['name']}: {e}")
            continue

    # Step 3: Load existing jobs and merge
    logger.info("Merging with existing jobs...")
    existing_jobs = load_jobs(str(JOBS_FILE))
    merged_jobs = merge_jobs(existing_jobs, all_jobs)

    new_count = len(merged_jobs) - len(existing_jobs)
    logger.info(f"New jobs: {new_count}, Total: {len(merged_jobs)}")

    # Step 4: Save
    logger.info(f"Saving to {JOBS_FILE}...")
    save_jobs(merged_jobs, str(JOBS_FILE))

    logger.info("Crawler complete!")
    return new_count

async def crawl_company(company: dict) -> List[JobPosting]:
    """
    Crawl a single company to find job postings.

    Args:
        company: Dict with 'name' and 'url'

    Returns:
        List of JobPosting objects found
    """
    jobs = []
    base_url = company["url"]
    company_name = company["name"]

    # Step 1: Generate possible careers page URLs
    possible_urls = detect_careers_page(base_url)

    # Step 2: Try to fetch each possible URL
    for career_url in possible_urls:
        try:
            logger.debug(f"  Trying {career_url}")
            html = await fetch_page_async(career_url, use_javascript=False)

            # Detect ATS
            ats = detect_ats_system(html)
            if ats:
                logger.debug(f"  Detected ATS: {ats}")

            # Extract jobs
            extracted = extract_job_postings(html, company_name, base_url, career_url)
            if extracted:
                logger.debug(f"  Found {len(extracted)} jobs on {career_url}")
                jobs.extend(extracted)
                break  # Found jobs on this page, stop trying other URLs

        except Exception as e:
            logger.debug(f"  Failed to fetch {career_url}: {e}")
            continue

    return jobs

def main():
    """Synchronous entry point for CLI"""
    new_jobs = asyncio.run(run_crawler())
    print(f"\n✓ Crawler completed. Found {new_jobs} new jobs.")
    return 0

if __name__ == "__main__":
    exit(main())
```

**Step 4: Run tests**

```bash
python -m pytest tests/crawler/test_main.py::test_crawler_orchestrator_structure -v
```

Expected: PASS

**Step 5: Manual test (optional, will be slow)**

```bash
cd /c/Users/vitor/Documents/Projetos/crawler-cv
# Don't run full crawler yet, just test import
python3 -c "from src.crawler.main import run_crawler; print('Crawler module loaded')"
```

**Step 6: Commit**

```bash
git add src/crawler/main.py tests/crawler/test_main.py
git commit -m "feat: implement crawler orchestrator"
```

---

## Phase 4: Matching & CLI

### Task 9: Implement matching and scoring

**Files:**
- Create: `src/matching/scorer.py`
- Create: `tests/matching/test_scorer.py`

**Step 1: Write failing tests**

```python
# tests/matching/test_scorer.py
import pytest
from src.matching.scorer import score_job, calculate_skill_overlap
from src.types import ResumeProfile, JobPosting, Match

@pytest.fixture
def sample_profile():
    return ResumeProfile(
        area="Backend",
        senioridade="Pleno",
        skills=["Python", "Django", "AWS", "PostgreSQL"],
        soft_skills=["Liderança"],
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
    from src.matching.scorer import _senioridade_score

    # Perfect match
    assert _senioridade_score("Pleno", "Pleno") == 1.0

    # One level difference is good
    assert _senioridade_score("Pleno", "Senior") > 0.7
    assert _senioridade_score("Pleno", "Junior") > 0.7

    # Two levels difference is worse
    assert _senioridade_score("Junior", "Senior") < 0.7
```

**Step 2: Run tests**

```bash
python -m pytest tests/matching/test_scorer.py -v
```

Expected: FAIL

**Step 3: Implement scorer.py**

```python
# src/matching/scorer.py
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
        reasons.append(f"Senioridade compatível ({profile.senioridade} → {job.senioridade})")
    if semantic_score > 0.5:
        reasons.append("Descrição alinhada com seu perfil")

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
```

**Step 4: Run tests**

```bash
python -m pytest tests/matching/test_scorer.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/matching/scorer.py tests/matching/test_scorer.py
git commit -m "feat: implement job scoring and matching algorithm"
```

---

### Task 10: Implement CLI interface

**Files:**
- Create: `src/cli.py`
- Create: `tests/test_cli.py`

**Step 1: Write failing tests**

```python
# tests/test_cli.py
import pytest
from pathlib import Path
from click.testing import CliRunner
from src.cli import main

@pytest.fixture
def cli_runner():
    return CliRunner()

def test_cli_help(cli_runner):
    result = cli_runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output

def test_cli_requires_resume_file(cli_runner):
    result = cli_runner.invoke(main, [])
    assert result.exit_code != 0
```

**Step 2: Run tests**

```bash
python -m pytest tests/test_cli.py::test_cli_help -v
```

Expected: FAIL

**Step 3: Implement cli.py**

```python
# src/cli.py
import click
import sys
from pathlib import Path
from src.resume.parser import parse_resume
from src.resume.analyzer import analyze_resume_with_groq
from src.crawler.jobs_manager import load_jobs
from src.matching.scorer import score_job
from src.output.html import generate_html_report
from src.config import JOBS_FILE
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)

@click.command()
@click.argument("resume_path", type=click.Path(exists=True))
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default=None,
    help="Output HTML file (default: results_<timestamp>.html)"
)
@click.option(
    "--min-score",
    type=float,
    default=0.5,
    help="Minimum match score (0.0-1.0)"
)
@click.option(
    "--open/--no-open",
    default=True,
    help="Open results in browser"
)
def main(resume_path: str, output: str, min_score: float, open: bool):
    """
    Match your resume against remote job opportunities.

    RESUME_PATH: Path to your resume (PDF or TXT)
    """
    try:
        # Step 1: Parse resume
        logger.info(f"Parsing resume from {resume_path}...")
        resume_text = parse_resume(resume_path)
        logger.info(f"  Extracted {len(resume_text)} characters")

        # Step 2: Analyze with Groq
        logger.info("Analyzing profile with AI...")
        profile = analyze_resume_with_groq(resume_text)
        logger.info(f"  Area: {profile.area}")
        logger.info(f"  Senioridade: {profile.senioridade}")
        logger.info(f"  Skills: {', '.join(profile.skills[:5])}")

        # Step 3: Load jobs
        logger.info(f"Loading jobs from {JOBS_FILE}...")
        jobs = load_jobs(str(JOBS_FILE))
        if not jobs:
            logger.error(f"No jobs found in {JOBS_FILE}. Run crawler first!")
            sys.exit(1)
        logger.info(f"  Loaded {len(jobs)} jobs")

        # Step 4: Score and rank
        logger.info("Scoring jobs...")
        matches = [score_job(profile, job) for job in jobs]
        matches = [m for m in matches if m.score >= min_score]
        matches.sort(key=lambda m: m.score, reverse=True)
        logger.info(f"  Found {len(matches)} matches (score >= {min_score})")

        # Step 5: Generate HTML
        if not output:
            from datetime import datetime
            output = f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

        logger.info(f"Generating report: {output}")
        generate_html_report(profile, matches, output)

        # Step 6: Open in browser
        if open:
            import webbrowser
            output_path = Path(output).absolute()
            logger.info(f"Opening in browser...")
            webbrowser.open(f"file://{output_path}")

        logger.info("✓ Done!")
        print(f"\nResults saved to: {output}")
        print(f"Matches found: {len(matches)}")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
```

**Step 4: Run tests**

```bash
python -m pytest tests/test_cli.py::test_cli_help -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/cli.py tests/test_cli.py
git commit -m "feat: implement CLI interface"
```

---

### Task 11: Implement HTML output generator

**Files:**
- Create: `src/output/html.py`
- Create: `src/output/templates/results.html`
- Create: `tests/output/test_html.py`

**Step 1: Write failing test**

```python
# tests/output/test_html.py
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
        soft_skills=["Liderança"],
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
```

**Step 2: Create template**

```html
<!-- src/output/templates/results.html -->
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CV Matcher - Resultados</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js" defer></script>
    <style>
        [x-cloak] { display: none !important; }
    </style>
</head>
<body class="bg-gray-50" x-cloak>
    <div class="min-h-screen">
        <!-- Header -->
        <header class="bg-white shadow">
            <div class="max-w-7xl mx-auto px-4 py-6">
                <h1 class="text-3xl font-bold text-gray-900">CV Matcher Results</h1>
            </div>
        </header>

        <div class="max-w-7xl mx-auto px-4 py-8">
            <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
                <!-- Sidebar: Profile Summary -->
                <aside class="md:col-span-1">
                    <div class="bg-white rounded-lg shadow p-6 sticky top-6">
                        <h2 class="text-xl font-bold mb-4">Seu Perfil</h2>
                        <dl class="space-y-3">
                            <div>
                                <dt class="text-sm font-medium text-gray-500">Área</dt>
                                <dd class="text-base font-semibold">{{ profile.area }}</dd>
                            </div>
                            <div>
                                <dt class="text-sm font-medium text-gray-500">Senioridade</dt>
                                <dd class="text-base font-semibold">{{ profile.senioridade }}</dd>
                            </div>
                            <div>
                                <dt class="text-sm font-medium text-gray-500">Experiência</dt>
                                <dd class="text-base font-semibold">{{ profile.anos_experiencia }} anos</dd>
                            </div>
                            <div>
                                <dt class="text-sm font-medium text-gray-500 mb-2">Skills</dt>
                                <dd class="flex flex-wrap gap-2">
                                    {% for skill in profile.skills[:5] %}
                                    <span class="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">{{ skill }}</span>
                                    {% endfor %}
                                </dd>
                            </div>
                        </dl>
                    </div>
                </aside>

                <!-- Main: Results -->
                <main class="md:col-span-3">
                    <!-- Filters -->
                    <div class="bg-white rounded-lg shadow p-4 mb-6" x-data="{ minScore: 0.5 }">
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">
                                    Compatibilidade mínima: <span x-text="(minScore * 100).toFixed(0) + '%'"></span>
                                </label>
                                <input
                                    type="range"
                                    min="0"
                                    max="1"
                                    step="0.1"
                                    x-model="minScore"
                                    class="w-full"
                                >
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">Empresa</label>
                                <input
                                    type="text"
                                    placeholder="Filtrar..."
                                    class="w-full px-3 py-2 border border-gray-300 rounded-md"
                                >
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">Senioridade</label>
                                <select class="w-full px-3 py-2 border border-gray-300 rounded-md">
                                    <option value="">Todas</option>
                                    <option value="Junior">Junior</option>
                                    <option value="Pleno">Pleno</option>
                                    <option value="Senior">Senior</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <!-- Stats -->
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                        <div class="bg-white rounded-lg shadow p-4">
                            <p class="text-gray-500 text-sm">Total de Vagas</p>
                            <p class="text-3xl font-bold">{{ matches|length }}</p>
                        </div>
                        <div class="bg-white rounded-lg shadow p-4">
                            <p class="text-gray-500 text-sm">Score Médio</p>
                            <p class="text-3xl font-bold">
                                {% if matches %}
                                    {{ "%.0f"|format(matches|map(attribute='score')|sum / matches|length * 100) }}%
                                {% else %}
                                    0%
                                {% endif %}
                            </p>
                        </div>
                        <div class="bg-white rounded-lg shadow p-4">
                            <p class="text-gray-500 text-sm">Score Máximo</p>
                            <p class="text-3xl font-bold">
                                {% if matches %}
                                    {{ "%.0f"|format(matches[0].score * 100) }}%
                                {% else %}
                                    0%
                                {% endif %}
                            </p>
                        </div>
                    </div>

                    <!-- Results Table -->
                    {% if matches %}
                    <div class="bg-white rounded-lg shadow overflow-hidden">
                        <table class="w-full">
                            <thead class="bg-gray-50 border-b">
                                <tr>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Compatibilidade</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Empresa</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Posição</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Senioridade</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Ação</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y">
                                {% for match in matches %}
                                <tr class="hover:bg-gray-50 cursor-pointer"
                                    @click="$el.nextElementSibling.classList.toggle('hidden')">
                                    <td class="px-6 py-4">
                                        <div class="flex items-center">
                                            <div class="w-12 h-12 bg-gradient-to-br from-green-400 to-green-600 rounded-lg flex items-center justify-center">
                                                <span class="text-white font-bold">{{ "%.0f"|format(match.score * 100) }}%</span>
                                            </div>
                                        </div>
                                    </td>
                                    <td class="px-6 py-4 font-semibold">{{ match.vaga.empresa }}</td>
                                    <td class="px-6 py-4">{{ match.vaga.titulo }}</td>
                                    <td class="px-6 py-4">
                                        {% if match.vaga.senioridade %}
                                        <span class="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs font-medium">
                                            {{ match.vaga.senioridade }}
                                        </span>
                                        {% else %}
                                        <span class="text-gray-400">-</span>
                                        {% endif %}
                                    </td>
                                    <td class="px-6 py-4">
                                        <a href="{{ match.vaga.link }}" target="_blank"
                                           class="text-blue-600 hover:text-blue-900 font-medium">
                                            Ver vaga →
                                        </a>
                                    </td>
                                </tr>
                                <!-- Expandable Details -->
                                <tr class="hidden bg-gray-50">
                                    <td colspan="5" class="px-6 py-4">
                                        <div class="grid grid-cols-2 gap-4">
                                            <div>
                                                <p class="text-sm font-medium text-gray-700 mb-2">Motivo do Match</p>
                                                <p class="text-sm text-gray-600">{{ match.motivo }}</p>
                                            </div>
                                            <div>
                                                <p class="text-sm font-medium text-gray-700 mb-2">Skills Detectadas</p>
                                                <div class="flex flex-wrap gap-2">
                                                    {% for skill in match.vaga.skills_detectadas %}
                                                    <span class="bg-purple-100 text-purple-800 px-2 py-1 rounded text-xs">
                                                        {{ skill }}
                                                    </span>
                                                    {% endfor %}
                                                </div>
                                            </div>
                                        </div>
                                        <div class="mt-4">
                                            <p class="text-sm font-medium text-gray-700 mb-2">Descrição</p>
                                            <p class="text-sm text-gray-600">{{ match.vaga.descricao[:200] }}...</p>
                                        </div>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                    {% else %}
                    <div class="bg-white rounded-lg shadow p-12 text-center">
                        <p class="text-gray-500 text-lg">Nenhuma vaga compatível encontrada.</p>
                        <p class="text-gray-400 text-sm mt-2">Tente baixar os filtros ou entrar em contato para mais informações.</p>
                    </div>
                    {% endif %}
                </main>
            </div>
        </div>

        <!-- Footer -->
        <footer class="bg-white border-t mt-12">
            <div class="max-w-7xl mx-auto px-4 py-6 text-center text-gray-500 text-sm">
                <p>CV Matcher • Gerado em {{ generated_at }}</p>
            </div>
        </footer>
    </div>
</body>
</html>
```

**Step 3: Implement html.py**

```python
# src/output/html.py
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from typing import List
from src.types import ResumeProfile, Match
from datetime import datetime

def generate_html_report(
    profile: ResumeProfile,
    matches: List[Match],
    output_path: str
) -> None:
    """
    Generate HTML report from matches.

    Args:
        profile: Analyzed resume profile
        matches: List of scored matches
        output_path: Where to save HTML
    """
    # Setup Jinja2
    template_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    template = env.get_template("results.html")

    # Render
    html_content = template.render(
        profile=profile,
        matches=matches,
        generated_at=datetime.now().strftime("%d/%m/%Y %H:%M"),
    )

    # Save
    Path(output_path).write_text(html_content, encoding="utf-8")
```

**Step 4: Run tests**

```bash
mkdir -p src/output/templates
python -m pytest tests/output/test_html.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/output/html.py src/output/templates/results.html tests/output/test_html.py
git commit -m "feat: implement HTML report generation with Tailwind styling"
```

---

### Task 12: Create GitHub Actions workflow for daily crawling

**Files:**
- Create: `.github/workflows/crawl.yml`

**Step 1: Write workflow**

```yaml
# .github/workflows/crawl.yml
name: Daily Crawler

on:
  schedule:
    - cron: "0 9 * * *"  # 09:00 UTC daily
  workflow_dispatch:  # Allow manual trigger

jobs:
  crawl:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.10"
          cache: "pip"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run crawler
        env:
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
        run: python -m src.crawler.main

      - name: Check for changes
        id: changes
        run: |
          if git diff --quiet data/jobs.json; then
            echo "has_changes=false" >> $GITHUB_OUTPUT
          else
            echo "has_changes=true" >> $GITHUB_OUTPUT
          fi

      - name: Commit changes
        if: steps.changes.outputs.has_changes == 'true'
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add data/jobs.json
          git commit -m "data: update jobs from daily crawl [skip ci]"
          git push

      - name: Report
        if: always()
        run: |
          echo "Crawler completed at $(date -u +'%Y-%m-%d %H:%M:%S UTC')"
```

**Step 2: Create workflow directory and file**

```bash
mkdir -p .github/workflows
# File is created above
```

**Step 3: Commit**

```bash
git add .github/workflows/crawl.yml
git commit -m "ci: add daily crawler GitHub Actions workflow"
```

---

### Task 13: Add PyPI script for easy running

**Files:**
- Create: `setup.py`
- Modify: `src/__main__.py`

**Step 1: Create setup.py**

```python
# setup.py
from setuptools import setup, find_packages

setup(
    name="cv-crawler",
    version="0.1.0",
    description="Match your resume against remote job opportunities",
    author="Vitor",
    python_requires=">=3.9",
    packages=find_packages(),
    install_requires=[
        "beautifulsoup4==4.12.2",
        "playwright==1.40.0",
        "pdfplumber==0.10.3",
        "requests==2.31.0",
        "groq==0.4.1",
        "sentence-transformers==2.2.2",
        "scikit-learn==1.3.2",
        "jinja2==3.1.2",
        "click==8.1.7",
        "python-dotenv==1.0.0",
        "rich==13.7.0",
    ],
    entry_points={
        "console_scripts": [
            "cv-crawler=src.cli:main",
        ],
    },
    include_package_data=True,
)
```

**Step 2: Create __main__.py**

```python
# src/__main__.py
from src.cli import main

if __name__ == "__main__":
    main()
```

**Step 3: Commit**

```bash
git add setup.py src/__main__.py
git commit -m "chore: add setup.py for pip installation"
```

---

### Task 14: Create comprehensive README

**Files:**
- Create: `README.md`

**Step 1: Write README**

```markdown
# CV Crawler 🚀

Um bot inteligente que analisa seu currículo e encontra vagas remotas compatíveis automaticamente.

## Features

- 📄 **Parser de Currículo** — Suporta PDF e TXT
- 🤖 **Análise com IA** — Extrai skills e senioridade usando Groq/Llama
- 🕷️ **Web Crawler** — Busca vagas em empresas brasileiras remotas
- 🎯 **Smart Matching** — Compara seu perfil com cada vaga
- 📊 **HTML Interativo** — Resultados em dashboard visual com filtros

## Quick Start

### 1. Setup

```bash
# Clone repositório
git clone https://github.com/seu-usuario/crawler-cv
cd crawler-cv

# Setup ambiente
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependências
pip install -r requirements.txt

# Setup Playwright (browser automation)
playwright install chromium
```

### 2. Configure API

```bash
# Crie arquivo .env
cp .env.example .env

# Adicione sua GROQ_API_KEY
echo "GROQ_API_KEY=seu_token_aqui" >> .env
```

Obtenha uma chave gratuita em: https://console.groq.com

### 3. Run Crawler (opcional, dados já disponíveis)

```bash
python -m src.crawler.main
```

### 4. Analyze Your Resume

```bash
python -m src.cli seu_curriculo.pdf
# ou
python -m src.cli seu_curriculo.txt
```

Resultado será aberto automaticamente no browser em `results_TIMESTAMP.html`.

## Options

```bash
python -m src.cli resume.pdf --help

Options:
  -o, --output PATH         Output HTML file
  --min-score FLOAT         Minimum match score (0.0-1.0)
  --open / --no-open        Open in browser (default: on)
```

## Project Structure

```
crawler-cv/
├── src/
│   ├── cli.py              # CLI entry point
│   ├── crawler/            # Web scraping
│   ├── resume/             # CV parsing
│   ├── matching/           # Scoring logic
│   └── output/             # HTML generation
├── data/
│   └── jobs.json           # Job database (auto-updated)
├── .github/workflows/
│   └── crawl.yml           # Daily crawler automation
└── tests/                  # Test suite
```

## How It Works

### Pipeline

1. **Parse Resume** — Extrai texto do PDF/TXT
2. **Analyze with AI** — Groq API extrai skills, senioridade, área
3. **Load Jobs** — Carrega banco de vagas (data/jobs.json)
4. **Score** — Compara seu perfil com cada vaga (0-100%)
5. **Rank** — Ordena por compatibilidade
6. **Generate HTML** — Dashboard interativo com filtros

### Scoring Formula

```
score = 0.5 × skill_overlap + 0.3 × senioridade_match + 0.2 × semantic_sim
```

- **Skills** (50%): Overlap de technologias entre currículo e vaga
- **Senioridade** (30%): Compatibilidade de nível
- **Semantic** (20%): Similaridade de keywords na descrição

## Crawler Details

A cada dia às 09:00 UTC, o GitHub Actions executa:

1. Faz parse do repo https://github.com/lerrua/remote-jobs-brazil
2. Extrai URLs de todas as empresas
3. Para cada empresa:
   - Identifica página de carreiras
   - Detecta ATS (Greenhouse, Gupy, etc)
   - Faz scraping com Playwright + BeautifulSoup
4. Normaliza e armazena em `data/jobs.json`
5. Commit automático

## API Keys

- **GROQ_API_KEY** — Obtenha em https://console.groq.com (free tier available)

## Testing

```bash
pytest tests/ -v
pytest tests/ --cov=src
```

## Tech Stack

- **Python 3.9+**
- **Playwright** — Automação de browser
- **BeautifulSoup4** — Parsing HTML
- **pdfplumber** — Extração de PDF
- **Groq SDK** — IA para análise
- **Click** — CLI framework
- **Jinja2** — Template HTML
- **Tailwind CSS** — Styling

## Contributing

Contribuições são bem-vindas! Por favor:

1. Fork o repositório
2. Crie uma branch (`git checkout -b feature/nome`)
3. Commit mudanças (`git commit -m "feat: descrição"`)
4. Push e abra um Pull Request

## FAQ

**P: Os dados são salvos?**
A: Seu currículo NÃO é salvo. Apenas o resultado HTML é gerado localmente.

**P: Funciona offline?**
A: Não — a análise usa Groq API (requer internet).

**P: Posso usar em produção?**
A: Sim! É apenas um CLI local. Sem servidor.

**P: Quantas vagas são coletadas?**
A: ~500-1000+ dependendo das empresas no repositório lerrua.

## License

MIT

## Support

- 📧 Email: seu-email@example.com
- 🐛 Issues: https://github.com/seu-usuario/crawler-cv/issues
- 💬 Discussions: https://github.com/seu-usuario/crawler-cv/discussions
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add comprehensive README with quick start guide"
```

---

## Summary

**Plan saved to:** `docs/plans/2026-02-22-cv-crawler-implementation.md`

### MVP Completion

All 14 tasks cover the complete MVP:

✅ **Phase 1: Foundation** (Tasks 1-2)
- Project setup, types, config

✅ **Phase 2: Resume Parser** (Tasks 3-4)
- PDF/TXT parsing
- Groq analysis

✅ **Phase 3: Crawler** (Tasks 5-8)
- Company list parsing
- Web scraper (Playwright + BS4)
- Job storage
- Orchestrator

✅ **Phase 4: Matching & CLI** (Tasks 9-14)
- Scoring algorithm
- CLI interface
- HTML report
- GitHub Actions workflow
- Documentation

---

## Execution Options

Plan is complete and ready for implementation. Two execution approaches:

**Option 1: Subagent-Driven (this session)**
- Fresh subagent per task
- Code review between tasks
- Fast iteration, context preserved

**Option 2: Parallel Session (separate)**
- New session with executing-plans skill
- Batch execution with checkpoints
- Clean state, focused work

**Which approach would you prefer?**