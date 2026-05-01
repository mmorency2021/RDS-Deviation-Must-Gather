"""Run omc (OpenShift Must-gather Client) validation against an extracted must-gather."""
from __future__ import annotations

import html
import os
import shlex
import shutil
import subprocess
from pathlib import Path


def resolve_omc_binary() -> str | None:
    """Prefer OMC_PATH env var, then ``omc`` on PATH, then ``/tmp/omc``."""
    env = (os.environ.get("OMC_PATH") or "").strip()
    if env and Path(env).is_file():
        return env
    w = shutil.which("omc")
    if w:
        return w
    if Path("/tmp/omc").is_file():
        return "/tmp/omc"
    return None


def capture_omc_validation(extract_dir: Path) -> tuple[str | None, str | None]:
    """Run omc against the first must-gather directory under *extract_dir*.

    Returns ``(output_text, skip_reason)``.  Exactly one is non-None.
    """
    omc_bin = resolve_omc_binary()
    if not omc_bin:
        return None, (
            "OMC not available. Install from https://github.com/gmeghnag/omc/releases "
            "or set OMC_PATH to the `omc` binary."
        )
    subs = sorted([p for p in extract_dir.iterdir() if p.is_dir()])
    if not subs:
        return None, "No subdirectory under extracted/ — unpack must-gather first."
    root = subs[0]
    multi_note = ""
    if len(subs) > 1:
        multi_note = f"# Note: {len(subs)} directories under extracted/; using `{root.name}`.\n\n"
    try:
        cmd = (
            f"{shlex.quote(omc_bin)} use {shlex.quote(str(root))} 2>&1; "
            f"{shlex.quote(omc_bin)} get clusterversion version -o yaml 2>&1; "
            f'echo ""; echo "# --- omc get clusterversion version -o wide ---"; '
            f"{shlex.quote(omc_bin)} get clusterversion version -o wide 2>&1"
        )
        proc = subprocess.run(
            ["bash", "-c", cmd],
            capture_output=True,
            text=True,
            timeout=120,
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        if proc.returncode != 0:
            out = f"# omc pipeline exit code: {proc.returncode}\n\n" + out
        return multi_note + out, None
    except FileNotFoundError:
        return None, "OMC binary could not be executed."
    except subprocess.TimeoutExpired:
        return None, "OMC command timed out after 120 s."
    except OSError as e:
        return None, f"OMC error: {e}"


def build_omc_html_section(text: str | None, skip: str | None) -> str:
    """HTML block for the OMC validation sidebar section."""
    esc = lambda x: html.escape(str(x) if x is not None else "")
    if text:
        return (
            '<section class="omc-panel" id="omc-validation" aria-labelledby="omc-title">\n'
            '<h2 id="omc-title"><span class="sec-dot" aria-hidden="true"></span> OMC validation (must-gather)</h2>\n'
            '<p class="section-lead">Output from <a href="https://github.com/gmeghnag/omc" target="_blank" '
            'rel="noopener">omc</a> (OpenShift Must-gather Client): <code>omc use</code> on the extract below, '
            'then <code>omc get clusterversion version</code> (YAML + wide).</p>\n'
            f'<pre class="omc-pre"><code>{esc(text)}</code></pre>\n'
            "</section>\n"
        )
    msg = esc(skip or "OMC validation was not run.")
    return (
        '<section class="omc-panel omc-panel-skipped" id="omc-validation" aria-labelledby="omc-title">\n'
        '<h2 id="omc-title"><span class="sec-dot" aria-hidden="true"></span> OMC validation (must-gather)</h2>\n'
        f'<p class="section-lead muted">{msg}</p>\n'
        "</section>\n"
    )
