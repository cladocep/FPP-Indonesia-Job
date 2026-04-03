"""
config.py

Central configuration for the Multi-Agent System.
Loads environment variables and provides shared settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ── paths ────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).parent.parent.parent  # project-root/
BACKEND_DIR = Path(__file__).parent.parent           # backend/
APP_DIR = Path(__file__).parent                      # backend/app/
DATA_DIR = PROJECT_ROOT / "data"

# ── load .env ────────────────────────────────────────────────────────────────

load_dotenv(PROJECT_ROOT / ".env")

# ── API keys ─────────────────────────────────────────────────────────────────

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "indonesian_jobs")
APP_PORT = int(os.getenv("APP_PORT", 8000))

# ── model settings ───────────────────────────────────────────────────────────

LLM_MODEL = "gpt-4o-mini"            # main LLM for agents
EMBED_MODEL = "text-embedding-3-small" # must match prepare_data.py
VECTOR_DIM = 1536

# ── database paths ───────────────────────────────────────────────────────────

SQLITE_DB_PATH = DATA_DIR / "jobs.db"

# ── RAG settings ─────────────────────────────────────────────────────────────

RAG_TOP_K = 5  # number of documents to retrieve from Qdrant

# ── validation ───────────────────────────────────────────────────────────────

def validate_config():
    """Check that all required env vars are set."""
    missing = []
    if not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")
    if not QDRANT_URL:
        missing.append("QDRANT_URL")
    if not QDRANT_API_KEY:
        missing.append("QDRANT_API_KEY")
    if missing:
        raise ValueError(f"Missing environment variables: {', '.join(missing)}")
    if not SQLITE_DB_PATH.exists():
        raise FileNotFoundError(f"SQLite DB not found: {SQLITE_DB_PATH}")
