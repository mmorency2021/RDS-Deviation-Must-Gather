"""Run kubectl cluster_compare (kube-compare) against an extracted must-gather."""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


def resolve_compare_binary() -> str:
    """Return the cluster-compare command to invoke.

    Checks ``CLUSTER_COMPARE_BIN`` env var first, then ``kubectl`` on PATH.
    Raises ``FileNotFoundError`` if neither is available.
    """
    env_bin = (os.environ.get("CLUSTER_COMPARE_BIN") or "").strip()
    if env_bin:
        if not Path(env_bin).is_file():
            raise FileNotFoundError(f"CLUSTER_COMPARE_BIN is not a file: {env_bin}")
        return env_bin
    if shutil.which("kubectl"):
        return "kubectl"
    raise FileNotFoundError(
        "kubectl not found on PATH. Install kubectl and the cluster_compare plugin, "
        "or set CLUSTER_COMPARE_BIN."
    )


def run_cluster_compare(
    compare_inputs: list[Path],
    metadata_path: Path,
    output_dir: Path,
) -> dict:
    """Execute kube-compare and write JSON + YAML output.

    Returns a dict with ``json_path``, ``yaml_path``, ``stderr_log``, and
    ``returncode``.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    out_json = output_dir / "cluster-compare-report.json"
    out_yaml = output_dir / "cluster-compare-report.yaml"
    errlog = output_dir / "cluster-compare-stderr.log"

    binary = resolve_compare_binary()
    is_plugin = binary.endswith("kubectl") or binary.endswith("kubectl.exe")

    base_cmd: list[str] = []
    if is_plugin:
        base_cmd = [binary, "cluster_compare"]
    else:
        base_cmd = [binary]

    base_cmd.extend(["-r", str(metadata_path)])
    for inp in compare_inputs:
        base_cmd.extend(["-f", str(inp)])
    if len(compare_inputs) > 1 or any((p / "..").resolve() != p.parent for p in compare_inputs):
        base_cmd.append("-R")

    with open(errlog, "w") as err_fh:
        # JSON output
        result_json = subprocess.run(
            base_cmd + ["-o", "json"],
            stdout=open(out_json, "w"),
            stderr=err_fh,
            timeout=600,
        )
        # YAML output
        subprocess.run(
            base_cmd + ["-o", "yaml"],
            stdout=open(out_yaml, "w"),
            stderr=err_fh,
            timeout=600,
        )

    return {
        "json_path": out_json,
        "yaml_path": out_yaml,
        "stderr_log": errlog,
        "returncode": result_json.returncode,
    }
