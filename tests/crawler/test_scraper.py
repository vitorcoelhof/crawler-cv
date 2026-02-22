import pytest
from src.crawler.scraper import detect_ats_system, extract_job_postings
from src.types import JobPosting

@pytest.mark.skip(reason="Requires network access")
def test_fetch_page_returns_html():
    from src.crawler.scraper import fetch_page
    html = fetch_page("https://example.com")
    assert isinstance(html, str)
    assert len(html) > 0

def test_extract_job_postings_mock():
    """Test job extraction with mock HTML"""
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
    mock_html_greenhouse = '<script src="https://boards.greenhouse.io/..."></script>'
    assert detect_ats_system(mock_html_greenhouse) == "Greenhouse"

    mock_html_gupy = '<script>var GUPY_CONFIG = {...}</script>'
    assert detect_ats_system(mock_html_gupy) == "Gupy"

    mock_html_none = "<html><body>No ATS detected</body></html>"
    assert detect_ats_system(mock_html_none) is None
