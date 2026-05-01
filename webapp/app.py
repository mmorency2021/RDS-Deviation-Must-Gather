"""Flask application factory."""
from __future__ import annotations

from flask import Flask

from webapp.config import DB_PATH, JOBS_DIR, MAX_CONTENT_LENGTH, SECRET_KEY, ensure_dirs
from webapp.models import JobStore
from webapp.routes import bp


def create_app() -> Flask:
    """Create and configure the Flask application."""
    ensure_dirs()

    app = Flask(__name__)
    app.config["SECRET_KEY"] = SECRET_KEY
    app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

    store = JobStore(DB_PATH)
    restored = store.restore_from_disk(JOBS_DIR)
    if restored:
        print(f"Restored {restored} completed job(s) from disk.")
    app.config["JOB_STORE"] = store

    app.register_blueprint(bp)

    return app
