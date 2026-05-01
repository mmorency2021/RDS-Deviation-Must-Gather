"""Flask application configuration."""
from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
TMP_DIR = BASE_DIR / ".tmp"
UPLOAD_DIR = TMP_DIR / "uploads"
JOBS_DIR = TMP_DIR / "jobs"
DB_PATH = TMP_DIR / "jobs.db"
REFERENCE_CACHE_DIR = TMP_DIR / "reference-cache"

MAX_CONTENT_LENGTH = int(os.environ.get("MAX_UPLOAD_MB", "6144")) * 1024 * 1024
ALLOWED_EXTENSIONS = {".tar.gz", ".tgz", ".tar", ".gz"}

SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "rds-dev-key-change-in-prod")


def ensure_dirs() -> None:
    """Create working directories if they don't exist."""
    for d in (UPLOAD_DIR, JOBS_DIR, REFERENCE_CACHE_DIR):
        d.mkdir(parents=True, exist_ok=True)
