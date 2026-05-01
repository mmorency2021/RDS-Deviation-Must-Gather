"""Fetch and cache the openshift-kni/telco-reference repository per branch."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

TELCO_REFERENCE_REPO = "https://github.com/openshift-kni/telco-reference"

PROFILE_METADATA_PATHS: dict[str, str] = {
    "RAN": "telco-ran/configuration/kube-compare-reference/metadata.yaml",
    "CORE": "telco-core/configuration/reference-crs-kube-compare/metadata.yaml",
    "HUB": "telco-hub/configuration/reference-crs-kube-compare/metadata.yaml",
}


def reference_config(profile: str, minor_version: str) -> dict[str, str]:
    """Return repo URL, branch name, and metadata path for a profile + version."""
    profile = profile.upper()
    if profile not in PROFILE_METADATA_PATHS:
        raise ValueError(f"Unknown profile: {profile!r}. Expected RAN, CORE, or HUB.")
    branch = f"release-{minor_version}"
    return {
        "repo": TELCO_REFERENCE_REPO,
        "branch": branch,
        "metadata_subpath": PROFILE_METADATA_PATHS[profile],
        "profile": profile,
        "minor_version": minor_version,
    }


def ensure_reference(
    profile: str, minor_version: str, cache_dir: Path
) -> Path:
    """Clone the telco-reference branch if not already cached.

    Returns the absolute path to the ``metadata.yaml`` for the requested
    profile and version.
    """
    cfg = reference_config(profile, minor_version)
    branch = cfg["branch"]
    clone_dir = cache_dir / branch

    metadata_path = clone_dir / cfg["metadata_subpath"]
    if metadata_path.is_file():
        return metadata_path

    # Remove stale/partial clone so git clone doesn't fail
    if clone_dir.exists():
        shutil.rmtree(clone_dir, ignore_errors=True)

    cache_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        "git", "clone",
        "--branch", branch,
        "--depth", "1",
        cfg["repo"],
        str(clone_dir),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=300)
    except subprocess.CalledProcessError as e:
        stderr = (e.stderr or "").strip()
        raise RuntimeError(
            f"Failed to clone telco-reference branch {branch!r}. "
            f"Verify that branch exists at {cfg['repo']}.\n{stderr}"
        ) from e
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(f"Git clone timed out after 300 s for branch {branch!r}.") from e

    if not metadata_path.is_file():
        raise FileNotFoundError(
            f"metadata.yaml not found at expected path after clone: {metadata_path}"
        )
    return metadata_path
