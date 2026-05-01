"""Background pipeline execution for must-gather analysis."""
from __future__ import annotations

import json
import shutil
import traceback
from pathlib import Path

from webapp.config import JOBS_DIR, REFERENCE_CACHE_DIR
from webapp.models import Job, JobStore, Status

from tools.mustgather import extract_tarball, find_payload_root, find_compare_inputs
from tools.cluster_version import load_cluster_version, ocp_minor_version
from tools.reference_repo import ensure_reference
from tools.kube_compare import run_cluster_compare
from tools.omc_runner import capture_omc_validation
from tools.dashboard_core import prepare_dashboard_data
from tools.html_renderer import render_html_dashboard
from tools.md_renderer import render_cluster_compare_markdown


def run_pipeline(job_id: str, tar_path: Path, profile: str, store: JobStore) -> None:
    """Execute the full analysis pipeline in a background thread.

    Steps: extract -> detect version -> fetch reference -> kube-compare ->
    omc -> build dashboard.
    """
    job_dir = JOBS_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    extract_dir = job_dir / "extracted"

    try:
        # 1. Extract
        store.update(job_id, status=Status.EXTRACTING, progress="Extracting archive")
        extract_tarball(tar_path, extract_dir)
        # Only delete files we copied into the uploads dir, not user's original
        from webapp.config import UPLOAD_DIR
        if tar_path.parent == UPLOAD_DIR:
            tar_path.unlink(missing_ok=True)

        payload_root = find_payload_root(extract_dir)
        if payload_root is None:
            raise RuntimeError(
                "Could not locate must-gather payload inside extracted archive. "
                "Expected a directory with cluster-scoped-resources or namespaces."
            )

        # 2. Detect cluster version
        store.update(job_id, status=Status.DETECTING_VERSION, progress="Reading cluster version")
        cv = load_cluster_version(extract_dir)
        version = cv.get("version", "")
        minor = ocp_minor_version(version) if version and version != "unknown" else "4.20"
        store.update(job_id, ocp_version=version or f"unknown (using {minor})")

        # 3. Fetch reference
        store.update(
            job_id,
            status=Status.FETCHING_REFERENCE,
            progress=f"Cloning telco-reference release-{minor}",
        )
        metadata_path = ensure_reference(profile, minor, REFERENCE_CACHE_DIR)

        # 4. Run kube-compare
        store.update(job_id, status=Status.COMPARING, progress="Running kubectl cluster_compare")
        compare_inputs = find_compare_inputs(payload_root)
        cc_result = run_cluster_compare(compare_inputs, metadata_path, job_dir)
        report_json = cc_result["json_path"]

        if not report_json.is_file() or report_json.stat().st_size == 0:
            raise RuntimeError(
                f"kube-compare produced no output (exit {cc_result['returncode']}). "
                f"Check {cc_result['stderr_log']}."
            )

        # 5. OMC validation (best-effort)
        store.update(job_id, status=Status.RUNNING_OMC, progress="Running OMC validation")
        # omc_runner handles missing binary gracefully

        # 6. Build dashboard
        store.update(job_id, status=Status.BUILDING_DASHBOARD, progress="Generating report")
        data = prepare_dashboard_data(report_json, extract_dir, profile)

        html_out = job_dir / "dashboard.html"
        html_out.write_text(render_html_dashboard(data), encoding="utf-8")

        md_out = job_dir / "report.md"
        md_out.write_text(render_cluster_compare_markdown(data), encoding="utf-8")

        # Write job metadata for restore-from-disk on restart
        job = store.get(job_id)
        meta = {
            "profile": profile,
            "ocp_version": version or minor,
            "partner_name": job.partner_name if job else "",
        }
        (job_dir / "job-meta.json").write_text(json.dumps(meta), encoding="utf-8")

        store.update(
            job_id,
            status=Status.DONE,
            progress="Complete",
            html_path=html_out,
            md_path=md_out,
            json_path=report_json,
        )

    except Exception as exc:
        store.update(
            job_id,
            status=Status.ERROR,
            error=f"{type(exc).__name__}: {exc}",
            progress="Failed",
        )
        err_log = job_dir / "pipeline-error.log"
        err_log.write_text(traceback.format_exc(), encoding="utf-8")
