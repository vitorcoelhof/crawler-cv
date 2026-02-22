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
