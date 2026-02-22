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
