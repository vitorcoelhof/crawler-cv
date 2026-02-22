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
    template = env.get_template("results_simple.html")

    # Render
    html_content = template.render(
        profile=profile,
        matches=matches,
        generated_at=datetime.now().strftime("%d/%m/%Y %H:%M"),
    )

    # Save
    Path(output_path).write_text(html_content, encoding="utf-8")
