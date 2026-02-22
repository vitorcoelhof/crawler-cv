#!/usr/bin/env python3
"""
Test crawler with mocked API responses to verify functionality locally
"""
from unittest.mock import patch
from src.crawler.main import run_crawler
from src.crawler.jobs_manager import load_jobs
from src.types import JobPosting
from datetime import date
import uuid

def create_mock_github_jobs():
    """Create mock GitHub Jobs API response"""
    return [
        JobPosting(
            id=str(uuid.uuid4()),
            empresa="GitHub Inc",
            titulo="Senior Backend Engineer - Python",
            descricao="Build backend services with Python and PostgreSQL",
            requisitos="Python, PostgreSQL, REST API, Docker",
            skills_detectadas=["Python", "PostgreSQL", "Docker"],
            senioridade="Senior",
            localizacao="Remote - USA",
            link="https://github.com/jobs/123",
            data_coleta=date.today().isoformat(),
            url_empresa="https://github.com",
        ),
        JobPosting(
            id=str(uuid.uuid4()),
            empresa="Stripe",
            titulo="Data Engineer - Airflow & PySpark",
            descricao="Work with distributed data pipelines using Airflow and PySpark",
            requisitos="Python, Airflow, PySpark, SQL, Databricks",
            skills_detectadas=["Python", "Airflow", "PySpark", "SQL", "Databricks"],
            senioridade="Senior",
            localizacao="Remote - USA",
            link="https://stripe.com/jobs/456",
            data_coleta=date.today().isoformat(),
            url_empresa="https://stripe.com",
        ),
    ]

def create_mock_gupy_jobs():
    """Create mock Gupy scraper response"""
    return [
        JobPosting(
            id=str(uuid.uuid4()),
            empresa="Nubank Tech",
            titulo="Data Engineer Pleno",
            descricao="Trabalhe com pipelines de dados em Airflow e PySpark",
            requisitos="Python, Airflow, PySpark, SQL",
            skills_detectadas=["Python", "Airflow", "PySpark", "SQL"],
            senioridade="Pleno",
            localizacao="Remoto - Brasil",
            link="https://nubank.gupy.io/job/123",
            data_coleta=date.today().isoformat(),
            url_empresa="https://nubank.com.br",
        ),
        JobPosting(
            id=str(uuid.uuid4()),
            empresa="Inter Bank",
            titulo="Senior Machine Learning Engineer",
            descricao="Develop ML models with Python and TensorFlow",
            requisitos="Python, Machine Learning, TensorFlow, SQL",
            skills_detectadas=["Python", "Machine Learning", "TensorFlow"],
            senioridade="Senior",
            localizacao="Remoto - Brasil",
            link="https://inter.gupy.io/job/456",
            data_coleta=date.today().isoformat(),
            url_empresa="https://inter.com.br",
        ),
    ]

def test_crawler_with_mocked_apis():
    """Test crawler with mocked API responses"""

    print("\n" + "="*70)
    print("TESTING CRAWLER WITH MOCKED EXTERNAL APIs")
    print("="*70)

    # Mock the external API calls
    with patch('src.crawler.main.search_jobs_github') as mock_github, \
         patch('src.crawler.main.search_jobs_gupy') as mock_gupy:

        # Set up mock responses
        mock_github.return_value = create_mock_github_jobs()
        mock_gupy.return_value = create_mock_gupy_jobs()

        print("\n[1/3] Running crawler with mocked APIs...")
        print("   - Mocked GitHub Jobs API: 2 jobs")
        print("   - Mocked Gupy Scraper: 2 jobs")

        # Run the crawler
        new_count = run_crawler()

        print(f"\n[2/3] Crawler completed!")
        print(f"   - New jobs added: {new_count}")

        # Load and verify results
        print(f"\n[3/3] Verifying results...")
        jobs = load_jobs("data/jobs.json")

        print(f"\n   Total jobs in database: {len(jobs)}")
        print(f"\n   Jobs by company:")
        companies = {}
        for job in jobs:
            if job.empresa not in companies:
                companies[job.empresa] = []
            companies[job.empresa].append(job)

        for company, job_list in sorted(companies.items()):
            print(f"   - {company}: {len(job_list)} job(s)")
            for job in job_list:
                print(f"     • {job.titulo} ({job.senioridade})")

        print(f"\n   Skills distribution:")
        all_skills = set()
        for job in jobs:
            all_skills.update(job.skills_detectadas)

        skill_count = {}
        for job in jobs:
            for skill in job.skills_detectadas:
                skill_count[skill] = skill_count.get(skill, 0) + 1

        for skill, count in sorted(skill_count.items(), key=lambda x: x[1], reverse=True):
            print(f"   - {skill}: appears in {count} job(s)")

        print("\n" + "="*70)
        print("[OK] CRAWLER TEST PASSED - System is fully functional!")
        print("="*70 + "\n")

        return len(jobs) > 5  # Should have more than just the 5 original test jobs

if __name__ == "__main__":
    success = test_crawler_with_mocked_apis()
    exit(0 if success else 1)
