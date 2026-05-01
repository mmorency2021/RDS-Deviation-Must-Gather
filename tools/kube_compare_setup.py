"""Auto-download kubectl-cluster_compare if not available."""
from __future__ import annotations

import os
import platform
import stat
import urllib.request
from pathlib import Path

KUBE_COMPARE_VERSION = "v0.12.0"
BASE_URL = f"https://github.com/openshift/kube-compare/releases/download/{KUBE_COMPARE_VERSION}"

INSTALL_DIR = Path("/tmp")


def _asset_name() -> str:
    """Return the release asset filename for the current platform."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    os_map = {"darwin": "darwin", "linux": "linux", "windows": "windows"}
    arch_map = {
        "x86_64": "amd64",
        "amd64": "amd64",
        "arm64": "arm64",
        "aarch64": "arm64",
    }

    os_name = os_map.get(system)
    arch_name = arch_map.get(machine)

    if not os_name or not arch_name:
        raise RuntimeError(f"Unsupported platform: {system}/{machine}")

    ext = "zip" if os_name == "windows" else "tar.gz"
    return f"kube-compare_{os_name}_{arch_name}.{ext}"


def ensure_cluster_compare() -> str:
    """Return the path to kubectl-cluster_compare, downloading if needed.

    Check order:
    1. CLUSTER_COMPARE_BIN env var
    2. kubectl-cluster_compare on PATH
    3. /tmp/kubectl-cluster_compare (previously downloaded)
    4. Download from GitHub releases for current OS/arch
    """
    env_bin = (os.environ.get("CLUSTER_COMPARE_BIN") or "").strip()
    if env_bin and Path(env_bin).is_file():
        return env_bin

    import shutil
    import subprocess
    path_bin = shutil.which("kubectl-cluster_compare")
    if path_bin:
        try:
            subprocess.run([path_bin, "--help"], capture_output=True, timeout=5)
            return path_bin
        except (OSError, subprocess.TimeoutExpired):
            print(f"Warning: {path_bin} found on PATH but not executable on this platform, skipping.")

    local_bin = INSTALL_DIR / "kubectl-cluster_compare"
    if local_bin.is_file():
        try:
            subprocess.run([str(local_bin), "--help"], capture_output=True, timeout=5)
            os.environ["CLUSTER_COMPARE_BIN"] = str(local_bin)
            return str(local_bin)
        except (OSError, subprocess.TimeoutExpired):
            print(f"Warning: {local_bin} exists but not executable on this platform, will re-download.")

    asset = _asset_name()
    url = f"{BASE_URL}/{asset}"

    print(f"Downloading kubectl-cluster_compare ({asset})...")
    archive_path = INSTALL_DIR / asset
    try:
        urllib.request.urlretrieve(url, str(archive_path))
    except Exception as exc:
        raise RuntimeError(
            f"Failed to download kube-compare from {url}: {exc}\n"
            f"Install manually: https://github.com/openshift/kube-compare/releases"
        ) from exc

    if asset.endswith(".tar.gz"):
        import tarfile
        with tarfile.open(archive_path, "r:gz") as tf:
            tf.extractall(INSTALL_DIR)
        archive_path.unlink(missing_ok=True)
    elif asset.endswith(".zip"):
        import zipfile
        with zipfile.ZipFile(archive_path, "r") as zf:
            zf.extractall(INSTALL_DIR)
        archive_path.unlink(missing_ok=True)

    if not local_bin.is_file():
        raise FileNotFoundError(
            f"kubectl-cluster_compare not found after extracting {asset}. "
            f"Contents: {list(INSTALL_DIR.glob('kubectl-*'))}"
        )

    local_bin.chmod(local_bin.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    os.environ["CLUSTER_COMPARE_BIN"] = str(local_bin)
    print(f"Installed kubectl-cluster_compare at {local_bin}")
    return str(local_bin)
