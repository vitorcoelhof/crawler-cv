from typing import List, Dict
from urllib.parse import urljoin, urlparse
import requests
from pathlib import Path
import re
import json

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
            return json.loads(cache_file.read_text())
        raise RuntimeError(f"Failed to fetch companies list: {e}")

def _parse_companies_from_readme(readme_text: str) -> List[Dict[str, str]]:
    """
    Parse README markdown to extract company information.

    Looks for both markdown links and plain URLs in lists:
    [Company Name](https://company.com) or - Site: https://company.com
    """
    companies = []
    urls_found = set()

    # Pattern 1: [Company Name](URL)
    markdown_pattern = r'\[([^\]]+)\]\((https?://[^\)]+)\)'
    for match in re.finditer(markdown_pattern, readme_text):
        name = match.group(1)
        url = normalize_url(match.group(2))

        if url not in urls_found:
            companies.append({"name": name, "url": url})
            urls_found.add(url)

    # Pattern 2: Plain URLs in lists (e.g., "- Site: https://example.com")
    url_pattern = r'(?:^|\s)(?:https?://[^\s\)]+)'
    for match in re.finditer(url_pattern, readme_text, re.MULTILINE):
        url_str = match.group(0).strip()
        url = normalize_url(url_str)

        if url not in urls_found and url.startswith("https://"):
            # Extract a simple name from the URL
            parsed = urlparse(url)
            name = parsed.netloc.replace("www.", "").split(".")[0].title()
            companies.append({"name": name, "url": url})
            urls_found.add(url)

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
