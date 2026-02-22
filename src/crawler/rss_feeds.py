"""
RSS Feeds aggregator - collects jobs from tech community RSS feeds
Legal, respectful, and doesn't require scraping
"""
import feedparser
from typing import List
from src.types import JobPosting
from datetime import date
import uuid
import logging

logger = logging.getLogger(__name__)

# Brazilian tech community RSS feeds
TECH_FEEDS = [
    # Tech job boards
    {
        "name": "Dev.to Brasil",
        "url": "https://dev.to/api/articles?username=devto&state=all&top=week",
        "type": "api"
    },
    # Tech communities
    {
        "name": "Python Brasil",
        "url": "https://pybr.org.br/feed.xml",
        "type": "rss"
    },
    {
        "name": "JavaScript Brasil",
        "url": "https://braziljs.org/feed.xml",
        "type": "rss"
    },
    # Tech news with job mentions
    {
        "name": "Hacker News",
        "url": "https://news.ycombinator.com/rss",
        "type": "rss"
    },
]

def search_rss_feeds(keywords: List[str] = None, max_jobs: int = 30) -> List[JobPosting]:
    """
    Search RSS feeds from Brazilian tech communities.

    This is the most respectful way to aggregate job listings.

    Args:
        keywords: Skills to filter by
        max_jobs: Maximum jobs to return

    Returns:
        List of JobPosting objects
    """
    if not keywords:
        keywords = ["Python", "Data", "Engineer", "Job"]

    jobs = []
    keyword_lower = [k.lower() for k in keywords]

    logger.info("Searching tech community RSS feeds...")

    for feed_config in TECH_FEEDS:
        try:
            feed_name = feed_config["name"]
            feed_url = feed_config["url"]

            logger.info(f"Fetching {feed_name}...")

            # Parse RSS feed
            feed = feedparser.parse(feed_url)

            if "entries" not in feed:
                logger.debug(f"No entries in {feed_name}")
                continue

            logger.info(f"Found {len(feed.entries)} entries in {feed_name}")

            for entry in feed.entries[:20]:  # Limit per feed
                if len(jobs) >= max_jobs:
                    break

                try:
                    # Check if entry mentions job-related keywords
                    title = entry.get("title", "").lower()
                    summary = entry.get("summary", "").lower()
                    content = f"{title} {summary}"

                    # Filter by keywords
                    matches = any(kw in content for kw in keyword_lower)

                    if not matches and "vaga" not in content and "job" not in content:
                        continue

                    job = _parse_rss_entry(entry, feed_name)
                    if job:
                        jobs.append(job)

                except Exception as e:
                    logger.debug(f"Error parsing RSS entry: {e}")
                    continue

        except Exception as e:
            logger.warning(f"Error fetching {feed_config['name']}: {e}")
            continue

    logger.info(f"Found {len(jobs)} jobs from RSS feeds")
    return jobs

def _parse_rss_entry(entry, source: str) -> JobPosting:
    """Parse RSS feed entry"""
    try:
        title = entry.get("title", "Unknown Job")
        summary = entry.get("summary", "")
        link = entry.get("link", "")
        author = entry.get("author", source)

        # Extract first 500 chars as description
        description = summary[:500] if summary else title

        full_text = f"{title} {summary}"
        skills = _extract_skills(full_text)
        senioridade = _detect_senioridade(full_text)

        job = JobPosting(
            id=str(uuid.uuid4()),
            empresa=author,
            titulo=title,
            descricao=description,
            requisitos=summary,
            skills_detectadas=skills,
            senioridade=senioridade,
            localizacao="Remoto - Brasil",
            link=link,
            data_coleta=date.today().isoformat(),
            url_empresa="",
        )

        return job

    except Exception as e:
        logger.debug(f"Error parsing RSS entry: {e}")
        return None

def _extract_skills(text: str) -> List[str]:
    """Extract skills from text"""
    known_skills = [
        "Python", "JavaScript", "TypeScript", "Java", "C#", "PHP",
        "Django", "FastAPI", "Flask", "Node.js", "React", "Vue",
        "AWS", "Docker", "Kubernetes", "PostgreSQL", "MongoDB",
        "Git", "REST API", "GraphQL", "SQL", "Linux",
        "Airflow", "PySpark", "Spark", "Databricks",
        "Machine Learning", "Data Science", "Data Engineer",
        "Backend", "Frontend", "Full Stack", "DevOps",
    ]

    text_lower = text.lower()
    found_skills = [skill for skill in known_skills if skill.lower() in text_lower]
    return list(set(found_skills))

def _detect_senioridade(text: str) -> str:
    """Detect seniority level"""
    text_lower = text.lower()

    if any(word in text_lower for word in ["senior", "staff", "lead", "principal"]):
        return "Senior"
    elif any(word in text_lower for word in ["mid", "pleno", "intermediate"]):
        return "Pleno"
    elif any(word in text_lower for word in ["junior", "entry", "trainee"]):
        return "Junior"

    return "Pleno"
