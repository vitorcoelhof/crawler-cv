import pytest
from src.crawler.companies import parse_remote_jobs_brazil_repo, normalize_url, _parse_companies_from_readme

@pytest.mark.skip(reason="Requires internet access")
def test_parse_repo_returns_companies():
    companies = parse_remote_jobs_brazil_repo()
    assert len(companies) > 0
    assert all("name" in c and "url" in c for c in companies)

def test_normalize_url():
    assert normalize_url("https://example.com") == "https://example.com"
    assert normalize_url("example.com") == "https://example.com"
    assert normalize_url("example.com/") == "https://example.com"

def test_extract_company_info_mock():
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
