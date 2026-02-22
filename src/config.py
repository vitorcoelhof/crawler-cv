# src/config.py
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
JOBS_FILE = DATA_DIR / "jobs.json"

# API
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Crawler
CRAWLER_TIMEOUT = 10  # seconds
CRAWLER_RETRIES = 3
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
RATE_LIMIT_DELAY = 1.0  # seconds between requests

# Matching
MIN_MATCH_SCORE = 0.5
SKILLS_WEIGHT = 0.5
SENIORIDADE_WEIGHT = 0.3
SEMANTIC_WEIGHT = 0.2

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)
