"""HTTP endpoints for the RDS compliance web application."""
from __future__ import annotations

import threading
from pathlib import Path

from flask import (
    Blueprint,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)

from webapp.config import ALLOWED_EXTENSIONS, JOBS_DIR, UPLOAD_DIR
from webapp.models import JobStore, Status
from webapp.tasks import run_pipeline

bp = Blueprint("main", __name__)


def _valid_extension(filename: str) -> bool:
    fn = filename.lower()
    return any(fn.endswith(ext) for ext in ALLOWED_EXTENSIONS)


@bp.route("/")
def index():
    store: JobStore = current_app.config["JOB_STORE"]
    recent = store.all_jobs()[:20]
    return render_template("upload.html", recent_jobs=recent)


@bp.route("/upload", methods=["POST"])
def upload():
    store: JobStore = current_app.config["JOB_STORE"]

    profile = request.form.get("profile", "RAN").upper()
    if profile not in ("RAN", "CORE", "HUB"):
        return render_template("error.html", message="Invalid profile."), 400

    partner_name = (request.form.get("partner_name") or "").strip()
    source = request.form.get("source", "path")

    if source == "path":
        filepath = (request.form.get("filepath") or "").strip()
        if not filepath:
            return render_template("error.html", message="No file path provided."), 400
        tar_path = Path(filepath)
        if not tar_path.is_file():
            return render_template("error.html", message=f"File not found: {filepath}"), 400
        if not _valid_extension(tar_path.name):
            return render_template(
                "error.html",
                message=f"Unsupported file type. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
            ), 400
        job = store.create(profile, partner_name)
    else:
        f = request.files.get("mustgather")
        if f is None or f.filename == "":
            return render_template("error.html", message="No file selected."), 400
        if not _valid_extension(f.filename):
            return render_template(
                "error.html",
                message=f"Unsupported file type. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
            ), 400
        job = store.create(profile, partner_name)
        tar_path = UPLOAD_DIR / f"{job.id}_{f.filename}"
        f.save(str(tar_path))

    t = threading.Thread(
        target=run_pipeline,
        args=(job.id, tar_path, profile, store),
        daemon=True,
    )
    t.start()

    return redirect(url_for("main.status", job_id=job.id))


@bp.route("/status/<job_id>")
def status(job_id: str):
    store: JobStore = current_app.config["JOB_STORE"]
    job = store.get(job_id)
    if job is None:
        return render_template("error.html", message="Job not found."), 404
    return render_template("status.html", job=job)


@bp.route("/api/status/<job_id>")
def api_status(job_id: str):
    store: JobStore = current_app.config["JOB_STORE"]
    job = store.get(job_id)
    if job is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(job.to_dict())


@bp.route("/results/<job_id>")
def results(job_id: str):
    store: JobStore = current_app.config["JOB_STORE"]
    job = store.get(job_id)
    if job is None:
        return render_template("error.html", message="Job not found."), 404
    if job.status != Status.DONE:
        return redirect(url_for("main.status", job_id=job_id))
    return render_template("results.html", job=job)


@bp.route("/results/<job_id>/dashboard")
def serve_dashboard(job_id: str):
    store: JobStore = current_app.config["JOB_STORE"]
    job = store.get(job_id)
    if job is None or job.html_path is None or not job.html_path.is_file():
        return render_template("error.html", message="Dashboard not available."), 404
    return send_file(job.html_path, mimetype="text/html")


@bp.route("/results/<job_id>/download/html")
def download_html(job_id: str):
    store: JobStore = current_app.config["JOB_STORE"]
    job = store.get(job_id)
    if job is None or job.html_path is None or not job.html_path.is_file():
        return render_template("error.html", message="File not available."), 404
    return send_file(job.html_path, as_attachment=True, download_name=f"rds-{job.profile}-{job_id}.html")


@bp.route("/results/<job_id>/download/md")
def download_md(job_id: str):
    store: JobStore = current_app.config["JOB_STORE"]
    job = store.get(job_id)
    if job is None or job.md_path is None or not job.md_path.is_file():
        return render_template("error.html", message="File not available."), 404
    return send_file(job.md_path, as_attachment=True, download_name=f"rds-{job.profile}-{job_id}.md")


@bp.route("/api/job/<job_id>/rename", methods=["POST"])
def rename_job(job_id: str):
    store: JobStore = current_app.config["JOB_STORE"]
    job = store.get(job_id)
    if job is None:
        return jsonify({"error": "not found"}), 404
    data = request.get_json(silent=True) or {}
    new_name = (data.get("partner_name") or "").strip()
    store.update(job_id, partner_name=new_name)
    meta_file = JOBS_DIR / job_id / "job-meta.json"
    if meta_file.is_file():
        import json
        try:
            meta = json.loads(meta_file.read_text())
        except (json.JSONDecodeError, OSError):
            meta = {}
        meta["partner_name"] = new_name
        meta_file.write_text(json.dumps(meta), encoding="utf-8")
    return jsonify({"ok": True, "partner_name": new_name})


@bp.route("/results/<job_id>/download/json")
def download_json(job_id: str):
    store: JobStore = current_app.config["JOB_STORE"]
    job = store.get(job_id)
    if job is None or job.json_path is None or not job.json_path.is_file():
        return render_template("error.html", message="File not available."), 404
    return send_file(job.json_path, as_attachment=True, download_name=f"cluster-compare-{job_id}.json")
