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
