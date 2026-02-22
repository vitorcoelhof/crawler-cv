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
        matches.sort(key=lambda m: m.score, reverse=True)
        high_matches = [m for m in matches if m.score >= min_score]
        logger.info(f"  Scored all {len(matches)} jobs")
        logger.info(f"  Found {len(high_matches)} matches (score >= {min_score})")

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

        logger.info("Done!")
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
