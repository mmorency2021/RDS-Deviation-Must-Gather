"""Job state tracking — SQLite-backed, thread-safe store."""
from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional


class Status(str, Enum):
    PENDING = "pending"
    EXTRACTING = "extracting"
    DETECTING_VERSION = "detecting_version"
    FETCHING_REFERENCE = "fetching_reference"
    COMPARING = "comparing"
    RUNNING_OMC = "running_omc"
    BUILDING_DASHBOARD = "building_dashboard"
    DONE = "done"
    ERROR = "error"

    @property
    def label(self) -> str:
        return {
            "pending": "Queued",
            "extracting": "Extracting must-gather archive",
            "detecting_version": "Detecting OpenShift version",
            "fetching_reference": "Fetching telco-reference bundle",
            "comparing": "Running kube-compare",
            "running_omc": "Running OMC validation",
            "building_dashboard": "Building dashboard",
            "done": "Complete",
            "error": "Error",
        }[self.value]


@dataclass
class Job:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    partner_name: str = ""
    profile: str = "RAN"
    status: Status = Status.PENDING
    progress: str = ""
    ocp_version: str = ""
    created: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    error: Optional[str] = None
    html_path: Optional[Path] = None
    md_path: Optional[Path] = None
    json_path: Optional[Path] = None

    @property
    def display_name(self) -> str:
        return self.partner_name or self.id

    @property
    def created_local(self) -> str:
        local = self.created.astimezone()
        return local.strftime("%Y-%m-%d %H:%M")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "partner_name": self.partner_name,
            "profile": self.profile,
            "status": self.status.value,
            "status_label": self.status.label,
            "progress": self.progress,
            "ocp_version": self.ocp_version,
            "created": self.created.isoformat(),
            "error": self.error,
            "has_html": self.html_path is not None and self.html_path.is_file(),
            "has_md": self.md_path is not None and self.md_path.is_file(),
        }


class JobStore:
    """Thread-safe SQLite-backed job store."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = str(db_path)
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id          TEXT PRIMARY KEY,
                    partner_name TEXT NOT NULL DEFAULT '',
                    profile     TEXT NOT NULL DEFAULT 'RAN',
                    status      TEXT NOT NULL DEFAULT 'pending',
                    progress    TEXT NOT NULL DEFAULT '',
                    ocp_version TEXT NOT NULL DEFAULT '',
                    created     TEXT NOT NULL,
                    error       TEXT,
                    html_path   TEXT,
                    md_path     TEXT,
                    json_path   TEXT
                )
            """)
            conn.commit()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _row_to_job(row: sqlite3.Row) -> Job:
        return Job(
            id=row["id"],
            partner_name=row["partner_name"],
            profile=row["profile"],
            status=Status(row["status"]),
            progress=row["progress"],
            ocp_version=row["ocp_version"],
            created=datetime.fromisoformat(row["created"]),
            error=row["error"],
            html_path=Path(row["html_path"]) if row["html_path"] else None,
            md_path=Path(row["md_path"]) if row["md_path"] else None,
            json_path=Path(row["json_path"]) if row["json_path"] else None,
        )

    def create(self, profile: str, partner_name: str = "") -> Job:
        job = Job(profile=profile.upper(), partner_name=partner_name.strip())
        with self._lock:
            with self._connect() as conn:
                conn.execute(
                    "INSERT INTO jobs (id, partner_name, profile, status, progress, "
                    "ocp_version, created, error, html_path, md_path, json_path) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (job.id, job.partner_name, job.profile, job.status.value,
                     job.progress, job.ocp_version, job.created.isoformat(),
                     job.error, None, None, None),
                )
                conn.commit()
        return job

    def get(self, job_id: str) -> Optional[Job]:
        with self._lock:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT * FROM jobs WHERE id = ?", (job_id,)
                ).fetchone()
        return self._row_to_job(row) if row else None

    def update(self, job_id: str, **kwargs) -> None:
        if not kwargs:
            return
        columns = []
        values = []
        for k, v in kwargs.items():
            columns.append(f"{k} = ?")
            if k == "status":
                values.append(v.value if isinstance(v, Status) else v)
            elif k in ("html_path", "md_path", "json_path"):
                values.append(str(v) if v is not None else None)
            else:
                values.append(v)
        values.append(job_id)
        sql = f"UPDATE jobs SET {', '.join(columns)} WHERE id = ?"
        with self._lock:
            with self._connect() as conn:
                conn.execute(sql, values)
                conn.commit()

    def all_jobs(self) -> list[Job]:
        with self._lock:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT * FROM jobs ORDER BY created DESC"
                ).fetchall()
        return [self._row_to_job(row) for row in rows]

    def restore_from_disk(self, jobs_dir: Path) -> int:
        """Import completed jobs from disk that aren't yet in the database.

        This is a one-time migration helper: on the first run after switching
        to SQLite, it pulls in old jobs that were tracked via job-meta.json.
        On subsequent runs it skips jobs already present in the DB.
        """
        if not jobs_dir.is_dir():
            return 0
        restored = 0
        for job_path in sorted(jobs_dir.iterdir()):
            if not job_path.is_dir():
                continue
            job_id = job_path.name
            if self.get(job_id) is not None:
                continue
            html = job_path / "dashboard.html"
            md = job_path / "report.md"
            json_f = job_path / "cluster-compare-report.json"
            if not html.is_file():
                continue
            profile = "RAN"
            ocp_version = ""
            partner_name = ""
            meta_file = job_path / "job-meta.json"
            if meta_file.is_file():
                try:
                    meta = json.loads(meta_file.read_text())
                    profile = meta.get("profile", "RAN").upper()
                    ocp_version = meta.get("ocp_version", "")
                    partner_name = meta.get("partner_name", "")
                except (json.JSONDecodeError, OSError):
                    pass
            try:
                stat = job_path.stat()
                created = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
            except OSError:
                created = datetime.now(timezone.utc)
            with self._lock:
                with self._connect() as conn:
                    conn.execute(
                        "INSERT OR IGNORE INTO jobs (id, partner_name, profile, status, "
                        "progress, ocp_version, created, error, html_path, md_path, json_path) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (job_id, partner_name, profile, Status.DONE.value,
                         "Restored from disk", ocp_version, created.isoformat(),
                         None,
                         str(html) if html.is_file() else None,
                         str(md) if md.is_file() else None,
                         str(json_f) if json_f.is_file() else None),
                    )
                    conn.commit()
            restored += 1
        return restored
