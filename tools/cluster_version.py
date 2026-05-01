"""Detect OpenShift cluster version from an extracted must-gather archive."""
from __future__ import annotations

import re
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


def load_cluster_version(extract_dir: Path) -> dict:
    """Find clusterversions/version.yaml in the extracted must-gather and parse it.

    Returns ``{"version": "4.20.15", "channel": "eus-4.20"}`` or
    ``{"version": "unknown", "channel": ""}`` on failure.
    """
    paths = list(
        extract_dir.rglob(
            "cluster-scoped-resources/config.openshift.io/clusterversions/version.yaml"
        )
    )
    if not paths or yaml is None:
        return {"version": "unknown", "channel": ""}
    d = yaml.safe_load(paths[0].read_text())
    st = d.get("status") or {}
    desired = st.get("desired") or {}
    spec = d.get("spec") or {}
    return {
        "version": desired.get("version") or "unknown",
        "channel": spec.get("channel") or "",
    }


def ocp_minor_version(version: str) -> str:
    """Return ``'4.20'`` from ``'4.20.15'`` for doc URLs and branch names."""
    m = re.match(r"^(\d+\.\d+)", (version or "").strip())
    return m.group(1) if m else "4.20"
