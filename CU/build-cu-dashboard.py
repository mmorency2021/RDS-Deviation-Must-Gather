#!/usr/bin/env python3
"""
Regenerate CU RDS / cluster-compare HTML report.

Output matches the original single-page compliance report layout:
  - Left nav (jump links) + one scrolling main column
  - Summary stats, template bars, full validation inventory (with doc links),
    correlation table, every unified diff, search + filter controls
  - OpenShift version from must-gather ClusterVersion
  - Also writes cluster-compare-report.md (Markdown mirror of the report)
  - When `omc` is available (PATH, OMC_PATH, or /tmp/omc), embeds OMC validation output
"""
from __future__ import annotations

import html
import json
import os
import re
import shlex
import shutil
import subprocess
from collections import Counter
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

BASE = Path(__file__).resolve().parent
REPORT_JSON = BASE / "cluster-compare-report.json"
EXTRACT = BASE / "extracted"
OUT_HTML = BASE / "cluster-compare-dashboard-detailed.html"
OUT_HTML_VCU = BASE / "vCU-RDS-compliance-dashboard.html"
OUT_MD = BASE / "cluster-compare-report.md"


def esc(x: str) -> str:
    return html.escape(str(x) if x is not None else "")


def must_gather_source_label(extract: Path) -> str:
    """Label for sidebar from extracted must-gather folder name(s)."""
    if not extract.is_dir():
        return "must-gather (vCU)"
    subs = sorted(p.name for p in extract.iterdir() if p.is_dir())
    if not subs:
        return "must-gather (vCU)"
    if len(subs) == 1:
        return subs[0]
    return f"{subs[0]} (+{len(subs) - 1} more)"


def gap_anchor_index(part_name: str, comp_name: str, index: int) -> str:
    """Stable id for validation gap detail + table jump links."""
    raw = f"{part_name}-{comp_name}-{index}"
    s = re.sub(r"[^a-zA-Z0-9_-]+", "-", raw).strip("-").lower()
    return f"gap-{s[:96]}" if s else f"gap-{index}"


def load_cluster_version() -> dict:
    paths = list(EXTRACT.rglob("cluster-scoped-resources/config.openshift.io/clusterversions/version.yaml"))
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
    """Return '4.20' from '4.20.15' for doc URLs and branch names."""
    m = re.match(r"^(\d+\.\d+)", (version or "").strip())
    return m.group(1) if m else "4.20"


def telco_reference_urls(cv_version: str) -> dict[str, str]:
    """
    Canonical links for the telco RAN DU kube-compare bundle (openshift-kni/telco-reference).
    Branch follows OpenShift minor (e.g. 4.20.x -> release-4.20).
    """
    minor = ocp_minor_version(cv_version if cv_version and cv_version != "unknown" else "4.20")
    branch = f"release-{minor}"
    gh = "https://github.com/openshift-kni/telco-reference"
    kube_path = "telco-ran/configuration/kube-compare-reference"
    return {
        "minor": minor,
        "branch": branch,
        "github_repo": gh,
        "tree_kube_compare": f"{gh}/tree/{branch}/{kube_path}",
        "metadata_yaml": f"{gh}/blob/{branch}/{kube_path}/metadata.yaml",
        "docs_ran_du": (
            f"https://docs.openshift.com/container-platform/{minor}/scalability_and_performance/"
            f"telco_ref_design_specs/ran/telco-ran-ref-du-components.html"
        ),
    }


def resolve_omc_binary() -> str | None:
    """Prefer OMC_PATH, then `omc` on PATH, then /tmp/omc if present."""
    env = (os.environ.get("OMC_PATH") or "").strip()
    if env and Path(env).is_file():
        return env
    w = shutil.which("omc")
    if w:
        return w
    if Path("/tmp/omc").is_file():
        return "/tmp/omc"
    return None


def capture_omc_validation(extract: Path) -> tuple[str | None, str | None]:
    """
    Run omc against the first must-gather directory under extract/.
    Returns (output_text, skip_reason). Exactly one of the two is non-None on success path.
    """
    omc_bin = resolve_omc_binary()
    if not omc_bin:
        return None, (
            "OMC not available. Install from https://github.com/gmeghnag/omc/releases "
            "or set OMC_PATH to the `omc` binary when running this script."
        )
    subs = sorted([p for p in extract.iterdir() if p.is_dir()])
    if not subs:
        return None, "No subdirectory under extracted/ — unpack must-gather before building the report."
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
        return None, "OMC command timed out after 120s."
    except OSError as e:
        return None, f"OMC error: {e}"


def build_omc_html_section(text: str | None, skip: str | None) -> str:
    """HTML block for sidebar section #omc-validation."""
    if text:
        return f"""
  <section class="omc-panel" id="omc-validation" aria-labelledby="omc-title">
  <h2 id="omc-title"><span class="sec-dot" aria-hidden="true"></span> OMC validation (must-gather)</h2>
  <p class="section-lead">Output from <a href="https://github.com/gmeghnag/omc" target="_blank" rel="noopener">omc</a> (OpenShift Must-gather Client): <code>omc use</code> on the extract below, then <code>omc get clusterversion version</code> (YAML + wide).</p>
  <pre class="omc-pre"><code>{esc(text)}</code></pre>
  </section>
"""
    msg = esc(skip or "OMC validation was not run.")
    return f"""
  <section class="omc-panel omc-panel-skipped" id="omc-validation" aria-labelledby="omc-title">
  <h2 id="omc-title"><span class="sec-dot" aria-hidden="true"></span> OMC validation (must-gather)</h2>
  <p class="section-lead muted">{msg}</p>
  </section>
"""


def md_cell(x: str) -> str:
    """Escape pipe/newlines for Markdown pipe tables."""
    return str(x).replace("|", "\\|").replace("\n", " ").strip()


def render_cluster_compare_markdown(
    *,
    document_title: str,
    intro: str,
    must_gather_label: str,
    build_script: str,
    extract_note: str,
    cv: dict,
    s: dict,
    ref: dict,
    val: dict,
    d: dict,
    omc_text: str | None = None,
    omc_skip_reason: str | None = None,
) -> str:
    """Plain Markdown report (same structure and headings as the HTML dashboard)."""
    lines: list[str] = []
    lines.append(f"# {document_title}\n")
    lines.append(intro.strip() + "\n")
    lines.append("## OpenShift (must-gather)\n")
    lines.append(f"- **Version:** {md_cell(cv.get('version') or '')}")
    lines.append(f"- **Channel:** {md_cell(cv.get('channel') or '')}")
    lines.append(f"- **Reference bundle:** {md_cell(ref['minor'])} telco RAN CU (vCU)")
    lines.append(f"- **Must-gather source:** {md_cell(must_gather_label)}\n")

    lines.append("## Summary\n")
    lines.append("| Metric | Value |")
    lines.append("| --- | --- |")
    lines.append(f"| CRs compared | {s.get('TotalCRs', '')} |")
    lines.append(f"| Missing vs RDS | {s.get('NumMissing', '')} |")
    lines.append(f"| With diff output | {s.get('NumDiffCRs', '')} |")
    lines.append(f"| Unmatched CRs | {len(s.get('UnmatchedCRS') or [])} |")
    lines.append(f"| Metadata hash | `{md_cell(s.get('MetadataHash', ''))}` |\n")

    lines.append("## RDS reference\n")
    lines.append(f"- **Git:** [{md_cell('openshift-kni/telco-reference')}]({ref['github_repo']})")
    lines.append(f"- **Branch:** `{md_cell(ref['branch'])}` (OpenShift **{ref['minor']}** minor)")
    lines.append(
        f"- **Compare bundle:** [`telco-ran/configuration/kube-compare-reference/`]({ref['tree_kube_compare']})"
    )
    lines.append(f"- **metadata.yaml:** [View on GitHub]({ref['metadata_yaml']})")
    lines.append(
        f"- **Product docs (RAN ref CU):** [OpenShift {ref['minor']}]({ref['docs_ran_du']})\n"
    )

    lines.append("## Cluster information & OMC validation\n")
    lines.append(
        "Cluster identity from must-gather (see above) and **OMC** validation against the extracted must-gather.\n"
    )
    lines.append("### OMC validation (must-gather)\n")
    lines.append(
        "Cross-check with [omc](https://github.com/gmeghnag/omc) (OpenShift Must-gather Client): "
        "`omc use <extracted must-gather>`, then `omc get clusterversion version -o yaml` and `-o wide`.\n"
    )
    if omc_text:
        lines.append("```text")
        lines.append(omc_text.rstrip())
        lines.append("```\n")
    elif omc_skip_reason:
        lines.append(f"*{omc_skip_reason}*\n")
    else:
        lines.append("*OMC validation not run.*\n")

    lines.append("## Required configurations\n")
    lines.append(
        "Full compare inventory (template volume, all correlations, aligned resources). Matches the highlighted HTML section.\n"
    )

    diffs = d.get("Diffs") or []
    c = Counter(x.get("CorrelatedTemplate", "") for x in diffs)
    lines.append("### Correlations per reference template (volume)\n")
    lines.append("| Reference template (path ends with) | Count |")
    lines.append("| --- | --- |")
    for tpl, cnt in c.most_common(28):
        tail = tpl.split("/")[-1][:56] if tpl else ""
        lines.append(f"| `{md_cell(tail)}` | {cnt} |")
    lines.append("")

    lines.append("### All correlated resources\n")
    lines.append("| # | Cluster resource | Reference template | Diff | Note |")
    lines.append("| --- | --- | --- | --- | --- |")
    for i, diff in enumerate(diffs):
        cr = diff.get("CRName", "") or ""
        tpl = diff.get("CorrelatedTemplate", "") or ""
        out = (diff.get("DiffOutput") or "").strip()
        desc = (diff.get("description") or "").strip()
        diff_yes = "Yes" if out else "No"
        lines.append(
            f"| {i} | {md_cell(cr[:200])} | {md_cell(tpl[:120])} | {diff_yes} | {md_cell(desc[:200])} |"
        )
    lines.append("")

    lines.append("### Aligned resources (no unified diff text)\n")
    aligned_any = False
    for i, diff in enumerate(diffs):
        out = (diff.get("DiffOutput") or "").strip()
        if out:
            continue
        aligned_any = True
        cr = diff.get("CRName", "") or ""
        tpl = diff.get("CorrelatedTemplate", "") or ""
        desc = (diff.get("description") or "").strip()
        lines.append(f"#### [{i}] `{md_cell(cr[:180])}`\n")
        lines.append(f"**Template:** `{md_cell(tpl)}`\n")
        if desc:
            lines.append(f"{desc}\n")
        lines.append("```")
        lines.append("(No unified diff text — correlated match without diff output.)")
        lines.append("```\n")
    if not aligned_any:
        lines.append("*No correlated resources without diff text.*\n")

    lines.append("## RDS deviation table\n")
    lines.append(
        "Gaps vs the RDS reference — **required** tier rows are called out in the table.\n"
    )
    lines.append("| Tier | Part | Message | Count |")
    lines.append("| --- | --- | --- | --- |")
    for part_name in sorted(val.keys()):
        for comp_name, comp in val[part_name].items():
            tier = "Required" if part_name.startswith("required") else "Optional"
            msg = comp.get("Msg", "") or ""
            n = len(comp.get("CRs") or [])
            lines.append(
                f"| {md_cell(tier)} | {md_cell(part_name)} | {md_cell(msg)} | {n} |"
            )
    lines.append("")

    lines.append("## Mismatched configurations\n")
    lines.append(
        "**Diff** — live cluster resource differs from the standard template (unified diff text).\n"
    )
    lines.append("### Resources with unified diff (incorrect)\n")
    lines.append("| # | Cluster resource | Reference template | Note |")
    lines.append("| --- | --- | --- | --- |")
    mismatch_count = 0
    for i, diff in enumerate(diffs):
        out = (diff.get("DiffOutput") or "").strip()
        if not out:
            continue
        mismatch_count += 1
        cr = diff.get("CRName", "") or ""
        tpl = diff.get("CorrelatedTemplate", "") or ""
        desc = (diff.get("description") or "").strip()
        lines.append(
            f"| {i} | {md_cell(cr[:200])} | {md_cell(tpl[:120])} | {md_cell(desc[:200])} |"
        )
    if mismatch_count == 0:
        lines.append("| — | *No correlated resources produced unified diff text in this report.* | | |")
    lines.append("")

    lines.append("### Unified diff output (incorrect)\n")
    for i, diff in enumerate(diffs):
        out = (diff.get("DiffOutput") or "").strip()
        if not out:
            continue
        cr = diff.get("CRName", "") or ""
        tpl = diff.get("CorrelatedTemplate", "") or ""
        desc = (diff.get("description") or "").strip()
        lines.append(f"#### [{i}] `{md_cell(cr[:180])}`\n")
        lines.append(f"**Template:** `{md_cell(tpl)}`\n")
        if desc:
            lines.append(f"{desc}\n")
        lines.append("```")
        lines.append(out)
        lines.append("```\n")

    lines.append("## Missing configurations\n")
    lines.append(
        "**Missing CRs** — the reference expects these resources; they are absent or not validated.\n"
    )
    lines.append("### Missing CR detail (full inventory)\n")
    for part_name in sorted(val.keys()):
        for comp_name, comp in val[part_name].items():
            tier = "Required" if part_name.startswith("required") else "Optional"
            msg = comp.get("Msg", "") or ""
            crs = comp.get("CRs") or []
            meta = comp.get("crMetadata") or {}
            lines.append(
                f"#### {md_cell(tier)} · `{md_cell(part_name)}` · *{md_cell(comp_name)}* — {md_cell(msg)} ({len(crs)})\n"
            )
            for cr in crs:
                doc = (meta.get(cr) or {}).get("description", "")
                if isinstance(doc, str) and doc.startswith("http"):
                    lines.append(f"- `{md_cell(cr)}` — [documentation]({doc})")
                else:
                    lines.append(f"- `{md_cell(cr)}`")
            lines.append("")

    lines.append("---\n")
    lines.append(
        f"*Regenerate HTML + this file: `{build_script}` after updating `cluster-compare-report.json`. "
        f"{extract_note}*\n"
    )
    return "\n".join(lines)


def main() -> None:
    cv = load_cluster_version()
    mg_label = must_gather_source_label(EXTRACT)
    d = json.loads(REPORT_JSON.read_text())
    s = d["Summary"]
    ref = telco_reference_urls(cv["version"])
    val = s.get("ValidationIssuses") or {}

    # --- Validation: anchors for gap table + detail rows ---
    val_sections: list[str] = []
    gap_table_rows: list[str] = []
    gidx = 0
    for part_name in sorted(val.keys()):
        for comp_name, comp in val[part_name].items():
            gid = gap_anchor_index(part_name, comp_name, gidx)
            gidx += 1
            msg = esc(comp.get("Msg", ""))
            crs = comp.get("CRs") or []
            meta = comp.get("crMetadata") or {}
            tier = "Required" if part_name.startswith("required") else "Optional"
            tier_cls = "tier-req" if tier == "Required" else "tier-opt"
            li_items = []
            for cr in crs:
                doc = (meta.get(cr) or {}).get("description", "")
                link = (
                    f' <a href="{esc(doc)}" target="_blank" rel="noopener">documentation</a>'
                    if doc.startswith("http")
                    else ""
                )
                li_items.append(f"<li><code>{esc(cr)}</code>{link}</li>")
            val_sections.append(
                f"""
    <section class="val-part" id="{gid}">
      <h4><span class="tier {tier_cls}">{tier}</span> {esc(part_name)} · <em>{esc(comp_name)}</em> — {msg} ({len(crs)})</h4>
      <p class="back-ref"><a href="#gaps-table">↑ Back to RDS deviation summary</a></p>
      <ul class="cr-list">{"".join(li_items)}</ul>
    </section>"""
            )
            gap_table_rows.append(
                "<tr>"
                f'<td><span class="tier {tier_cls}">{tier}</span></td>'
                f'<td><a class="gap-jump" href="#{gid}" title="Open RDS deviation detail">{esc(part_name)}</a></td>'
                f'<td>{esc(comp.get("Msg", ""))}</td>'
                f'<td><a class="gap-jump gap-count" href="#{gid}" title="Open RDS deviation detail">{len(crs)}</a></td>'
                "</tr>"
            )

    # --- Correlation rows (all + mismatch-only) and diff panels split by unified diff ---
    corr_rows: list[str] = []
    corr_rows_mismatch: list[str] = []
    diff_panels_mismatch: list[str] = []
    diff_panels_nodiff: list[str] = []
    for i, diff in enumerate(d.get("Diffs", [])):
        cr = diff.get("CRName", "")
        tpl = diff.get("CorrelatedTemplate", "")
        out = (diff.get("DiffOutput") or "").strip()
        desc = (diff.get("description") or "").strip()
        row = (
            f'<tr data-has-diff="{"1" if out else "0"}">'
            f'<td class="mono truncate" title="{esc(cr)}">{esc(cr[:100])}{"…" if len(cr) > 100 else ""}</td>'
            f'<td class="mono small">{esc(tpl[:72])}{"…" if len(tpl) > 72 else ""}</td>'
            f'<td>{"Yes" if out else "No"}</td>'
            f'<td class="muted small">{esc(desc[:140])}{"…" if len(desc) > 140 else ""}</td>'
            f'<td><a href="#diff-{i}">#diff-{i}</a></td></tr>'
        )
        corr_rows.append(row)
        if out:
            corr_rows_mismatch.append(row)
        body = esc(out) if out else "(No unified diff text — correlated match without diff output.)"
        desc_html = f'<p class="diff-note">{esc(desc)}</p>' if desc else ""
        panel = f"""
    <article class="diff-card" id="diff-{i}" data-has-diff="{"1" if out else "0"}">
      <header><span class="mono">{esc(cr)}</span></header>
      <p class="meta"><strong>Template:</strong> <code>{esc(tpl)}</code></p>
      {desc_html}
      <pre class="diff-pre"><code>{body}</code></pre>
    </article>"""
        if out:
            diff_panels_mismatch.append(panel)
        else:
            diff_panels_nodiff.append(panel)

    mismatch_table_body = (
        "".join(corr_rows_mismatch)
        if corr_rows_mismatch
        else '<tr><td colspan="5" class="muted">No correlated resources produced unified diff text in this report.</td></tr>'
    )

    c = Counter(x.get("CorrelatedTemplate", "") for x in d["Diffs"])
    mx = max(c.values()) if c else 1
    bar_rows = []
    for bi, (k, v) in enumerate(c.most_common(14)):
        pct = round(100 * v / mx)
        bar_rows.append(
            f'<div class="bar-row"><a class="bar-label bar-link" href="#correlations" title="Open correlation table (search for this template)">{esc(k.split("/")[-1][:28])}</a>'
            f'<div class="bar-track"><div class="bar-fill bar-fill-{bi % 6}" style="width:{pct}%"></div></div><span class="bar-num">{v}</span></div>'
        )

    agg_rows = "".join(
        f"<tr><td>{esc(k[:78])}</td><td>{v}</td></tr>" for k, v in c.most_common(28)
    )

    omc_text, omc_skip = capture_omc_validation(EXTRACT)
    omc_section = build_omc_html_section(omc_text, omc_skip)

    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>vCU · RDS compliance — cluster-compare (RAN central unit)</title>
<meta name="description" content="vCU (RAN CU site) cluster-compare report: missing CRs, mismatch diffs, OMC validation, telco RDS reference."/>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&display=swap" rel="stylesheet"/>
<style>
:root {{
  --bg: #0f1419;
  --bg2: #1a2332;
  --surface: #1c2433;
  --surface2: #252f42;
  --border: #3d4f66;
  --text: #f0f4f8;
  --muted: #94a3b8;
  --accent: #38bdf8;
  --accent2: #818cf8;
  --purple: #a78bfa;
  --pink: #f472b6;
  --warn: #fbbf24;
  --warn-bg: rgba(251, 191, 36, 0.12);
  --ok: #34d399;
  --ok-bg: rgba(52, 211, 153, 0.12);
  --coral: #fb7185;
  --missing-accent: #c2410c;
  --missing-accent-deep: #9a3412;
  --missing-bg: rgba(154, 52, 18, 0.12);
  --req-emerald: #10b981;
  --req-emerald-dim: rgba(16, 185, 129, 0.2);
  --req-emerald-glow: rgba(16, 185, 129, 0.45);
  --shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
  --radius: 14px;
}}
@media (prefers-color-scheme: light) {{
  :root {{
    --bg: #f1f5f9;
    --bg2: #e2e8f0;
    --surface: #ffffff;
    --surface2: #f8fafc;
    --border: #cbd5e1;
    --text: #0f172a;
    --muted: #64748b;
    --accent: #0284c7;
    --accent2: #4f46e5;
    --purple: #7c3aed;
    --pink: #db2777;
    --warn: #b45309;
    --warn-bg: rgba(251, 191, 36, 0.2);
    --ok: #047857;
    --ok-bg: rgba(52, 211, 153, 0.18);
    --coral: #e11d48;
    --missing-accent: #9a3412;
    --missing-accent-deep: #7c2d12;
    --missing-bg: rgba(124, 45, 18, 0.1);
    --req-emerald: #059669;
    --req-emerald-dim: rgba(5, 150, 105, 0.18);
    --req-emerald-glow: rgba(5, 150, 105, 0.4);
    --shadow: 0 4px 24px rgba(15, 23, 42, 0.08);
  }}
}}
* {{ box-sizing: border-box; }}
body.vcu-dashboard {{
  margin: 0;
  font-family: "DM Sans", ui-sans-serif, system-ui, sans-serif;
  background: linear-gradient(165deg, var(--bg) 0%, var(--bg2) 45%, var(--bg) 100%);
  background-attachment: fixed;
  color: var(--text);
  line-height: 1.55;
  font-size: 0.95rem;
}}
.site-tag {{
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 0.62rem; font-weight: 800; letter-spacing: 0.14em;
  padding: 5px 11px; border-radius: 8px;
  background: linear-gradient(135deg, rgba(56,189,248,0.35), rgba(129,140,248,0.4));
  border: 1px solid rgba(56,189,248,0.55); color: var(--text); text-transform: uppercase;
  flex-shrink: 0;
}}
.site-tag.lg {{ font-size: 0.72rem; padding: 7px 14px; border-radius: 10px; }}
.brand-vcu {{
  display: flex; align-items: flex-start; gap: 12px; margin-bottom: 12px;
}}
.brand-vcu .brand {{ margin-bottom: 2px; }}
.brand-vcu .brand-sub {{ margin-bottom: 0; }}
.toc-heading {{
  font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.14em;
  color: var(--muted); margin: 16px 0 10px; font-weight: 700;
}}
.toc-tree .toc-sub {{
  margin: 4px 0 12px 6px; padding-left: 12px; border-left: 2px solid rgba(56, 189, 248, 0.25);
}}
.nav-link.nav-sub {{
  font-size: 0.8rem; padding: 5px 10px; margin: 1px 0; color: var(--muted);
}}
.nav-link.nav-sub:hover {{ color: var(--accent); }}
.toc-panel {{
  margin-top: 20px; padding: 16px 18px; border-radius: var(--radius);
  background: var(--surface); border: 1px solid var(--border);
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
}}
.toc-panel-title {{
  font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.1em;
  color: var(--muted); margin: 0 0 12px; font-weight: 700;
}}
.toc-ol {{ margin: 0; padding-left: 1.15rem; font-size: 0.88rem; }}
.toc-ol ol {{ margin: 6px 0 10px; padding-left: 1.1rem; font-size: 0.86rem; }}
.toc-ol a {{ color: var(--accent); text-decoration: none; font-weight: 500; }}
.toc-ol a:hover {{ text-decoration: underline; color: var(--purple); }}
.hero-h1-wrap {{ display: flex; align-items: center; gap: 12px; flex-wrap: wrap; margin-bottom: 12px; }}
.hero-h1 {{ font-size: 1.55rem; font-weight: 700; margin: 0; letter-spacing: -0.03em; line-height: 1.2; }}
.hero-h1-sub {{ font-size: 1rem; font-weight: 500; color: var(--muted); }}
.layout {{ display: grid; grid-template-columns: 260px 1fr; min-height: 100vh; }}
@media (max-width: 880px) {{
  .layout {{ grid-template-columns: 1fr; }}
  aside {{ position: relative; border-right: none; border-bottom: 1px solid var(--border); max-height: none; }}
}}
aside {{
  position: sticky; top: 0; align-self: start; max-height: 100vh; overflow: auto;
  padding: 22px 16px;
  border-right: 1px solid var(--border);
  background: linear-gradient(180deg, var(--surface2) 0%, var(--surface) 100%);
  box-shadow: inset -1px 0 0 rgba(56, 189, 248, 0.06);
}}
.brand {{ font-weight: 700; font-size: 1rem; letter-spacing: -0.02em; margin-bottom: 4px;
  background: linear-gradient(90deg, var(--accent), var(--purple)); -webkit-background-clip: text; background-clip: text; color: transparent; }}
.brand-sub {{ font-size: 0.72rem; color: var(--muted); margin-bottom: 18px; line-height: 1.35; }}
aside h2 {{ font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.12em; color: var(--muted); margin: 20px 0 10px; font-weight: 600; }}
.nav-link {{
  color: var(--text); text-decoration: none; font-size: 0.88rem; display: flex; align-items: center; gap: 8px;
  padding: 8px 10px; margin: 2px 0; border-radius: 10px; transition: background 0.15s ease, color 0.15s ease;
}}
.nav-link:hover {{ background: rgba(56, 189, 248, 0.12); color: var(--accent); }}
.nav-ico {{ font-size: 1.05rem; opacity: 0.92; width: 1.25em; text-align: center; }}
main {{ padding: 28px 32px 72px; max-width: 920px; }}
html {{ scroll-behavior: smooth; }}
h1, h2, .val-part, .diff-card, #rds-reference, #omc-validation, #basic-info, #required-configurations, #rds-deviation-table, #mismatch-diffs, #missing-configurations {{ scroll-margin-top: 96px; }}
.deviation-zone {{ margin: 0 0 8px; }}
.zone-basic {{ padding-left: 14px; margin-left: -2px; border-left: 4px solid #22d3ee; }}
.zone-missing {{
  padding-left: 14px; margin-left: -2px;
  border-left: 4px solid var(--missing-accent);
  background: linear-gradient(90deg, var(--missing-bg), transparent 52%);
  border-radius: 0 var(--radius) var(--radius) 0;
}}
.zone-mismatch {{ padding-left: 14px; margin-left: -2px; border-left: 4px solid var(--pink); }}
.zone-other {{ padding-left: 14px; margin-left: -2px; border-left: 4px solid var(--accent2); }}
.zone-ref {{ padding-left: 14px; margin-left: -2px; border-left: 4px solid var(--accent2); }}
.zone-required {{ padding-left: 14px; margin-left: -2px; border-left: 4px solid var(--req-emerald); }}
.zone-required.required-highlight {{
  border-radius: var(--radius);
  padding-top: 12px; padding-bottom: 8px;
  background: linear-gradient(165deg, var(--req-emerald-dim) 0%, var(--surface) 55%);
  box-shadow:
    0 0 0 1px var(--req-emerald-glow),
    0 4px 28px rgba(16, 185, 129, 0.18),
    inset 0 1px 0 rgba(255,255,255,0.06);
}}
.req-highlight-tag {{
  display: inline-flex; align-items: center;
  font-size: 0.58rem; font-weight: 800; letter-spacing: 0.14em;
  text-transform: uppercase;
  padding: 6px 14px; margin-left: auto;
  border-radius: 999px;
  color: var(--text);
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.45), rgba(52, 211, 153, 0.22));
  border: 1px solid rgba(16, 185, 129, 0.75);
  box-shadow: 0 0 16px rgba(16, 185, 129, 0.35);
  flex-shrink: 0;
}}
.nav-link.nav-link-req {{
  background: rgba(16, 185, 129, 0.14);
  border: 1px solid rgba(16, 185, 129, 0.4);
}}
.nav-link.nav-link-req:hover {{
  background: rgba(16, 185, 129, 0.22);
  color: var(--req-emerald);
}}
#missing-configurations h2 {{ border-bottom-color: rgba(194, 65, 12, 0.45); }}
#missing-configurations h2 .sec-dot {{ background: var(--missing-accent); color: var(--missing-accent); }}
#missing-configurations h3#validation {{ border-bottom-color: rgba(194, 65, 12, 0.35); padding-bottom: 8px; }}
#missing-configurations h3#validation .sec-dot {{ background: var(--missing-accent-deep); color: var(--missing-accent-deep); }}
#required-configurations h2 {{ border-bottom-color: rgba(16, 185, 129, 0.5); }}
#required-configurations h2 .sec-dot {{ background: var(--req-emerald); color: var(--req-emerald); }}
.zone-deviation {{ padding-left: 14px; margin-left: -2px; border-left: 4px solid var(--warn); }}
table.data#gaps-table tbody tr:has(.tier-req) {{ background: rgba(251, 191, 36, 0.09); }}
table.data#gaps-table tbody tr:has(.tier-req):hover {{ background: rgba(251, 191, 36, 0.14); }}
.nav-section {{ font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.12em; color: var(--muted); margin: 18px 0 8px; font-weight: 600; }}
.hero {{
  padding: 28px 24px 24px; margin: -8px -12px 28px; border-radius: var(--radius);
  background: linear-gradient(135deg, rgba(56, 189, 248, 0.14) 0%, rgba(129, 140, 248, 0.12) 50%, rgba(244, 114, 182, 0.08) 100%);
  border: 1px solid rgba(56, 189, 248, 0.25);
  box-shadow: var(--shadow);
}}
h1 {{ font-size: 1.65rem; font-weight: 700; margin: 0 0 12px; letter-spacing: -0.03em; line-height: 1.25; }}
.lead {{ color: var(--muted); font-size: 0.95rem; margin-bottom: 0; max-width: 680px; }}
.version-line {{
  font-size: 0.88rem; margin-top: 18px; padding: 14px 16px;
  background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
  border-left: 4px solid var(--ok);
  box-shadow: 0 2px 12px rgba(0,0,0,0.12);
}}
.version-line strong {{ color: var(--text); }}
.stat-hint {{
  font-size: 0.82rem; color: var(--muted); margin: 16px 0 20px; padding: 12px 14px;
  background: var(--surface2); border-radius: 10px; border-left: 3px solid var(--purple);
}}
.stats {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(132px, 1fr)); gap: 14px; margin-top: 22px; }}
a.stat {{
  display: block; text-decoration: none; color: inherit;
  border-radius: var(--radius); padding: 16px 18px;
  transition: transform 0.18s ease, box-shadow 0.18s ease;
  border: 1px solid var(--border);
  box-shadow: 0 2px 12px rgba(0,0,0,0.15);
}}
a.stat:hover {{ transform: translateY(-2px); box-shadow: 0 10px 28px rgba(56, 189, 248, 0.15); }}
a.stat-crs {{ background: linear-gradient(145deg, rgba(56, 189, 248, 0.18), var(--surface)); border-color: rgba(56, 189, 248, 0.35); }}
a.stat-crs .v {{ color: var(--accent); }}
a.stat-gaps {{ background: linear-gradient(145deg, var(--missing-bg), var(--surface)); border-color: rgba(194, 65, 12, 0.4); }}
a.stat-gaps .v {{ color: var(--missing-accent); }}
a.stat-diff {{ background: linear-gradient(145deg, rgba(244, 114, 182, 0.12), var(--surface)); border-color: rgba(244, 114, 182, 0.3); }}
a.stat-diff .v {{ color: var(--pink); }}
a.stat-ok {{ background: linear-gradient(145deg, var(--ok-bg), var(--surface)); border-color: rgba(52, 211, 153, 0.35); }}
a.stat-ok .v {{ color: var(--ok); }}
a.stat .v {{ font-size: 1.75rem; font-weight: 700; letter-spacing: -0.02em; line-height: 1.1; }}
a.stat .l {{ font-size: 0.7rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; margin-top: 8px; font-weight: 600; }}
a.gap-jump {{ color: var(--accent); text-decoration: none; font-weight: 600; }}
a.gap-jump:hover {{ text-decoration: underline; color: var(--purple); }}
a.gap-count {{ font-weight: 700; }}
table.data tbody tr:nth-child(even) td {{ background: rgba(56, 189, 248, 0.04); }}
table.data tr:hover td {{ background: rgba(129, 140, 248, 0.1) !important; }}
.back-ref {{ margin: 0 0 10px; font-size: 0.8rem; }}
.back-ref a {{ color: var(--accent); text-decoration: none; font-weight: 500; }}
.back-ref a:hover {{ color: var(--purple); text-decoration: underline; }}
.controls {{
  display: flex; flex-wrap: wrap; gap: 12px; align-items: center; margin: 20px 0 24px;
  padding: 16px 18px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius);
  box-shadow: var(--shadow);
}}
.controls label {{ font-weight: 600; font-size: 0.82rem; color: var(--muted); }}
.controls input[type="search"] {{
  flex: 1; min-width: 200px; padding: 10px 14px; border-radius: 10px; border: 2px solid var(--border);
  background: var(--bg); color: var(--text); font-size: 0.9rem;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}}
.controls input[type="search"]:focus {{ outline: none; border-color: var(--accent); box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.25); }}
.controls select {{
  padding: 10px 12px; border-radius: 10px; border: 2px solid var(--border); background: var(--bg); color: var(--text); font-weight: 500;
  cursor: pointer;
}}
.controls select:focus {{ outline: none; border-color: var(--accent); }}
h2 {{
  font-size: 1.15rem; font-weight: 700; margin: 40px 0 12px; padding: 0 0 10px 0;
  border-bottom: 2px solid var(--border); letter-spacing: -0.02em;
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
}}
h2 .sec-dot {{
  width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0;
  box-shadow: 0 0 12px currentColor;
}}
h3#bars {{ border-bottom-color: rgba(56, 189, 248, 0.5); }}
h3#bars .sec-dot {{ background: var(--accent); color: var(--accent); }}
#rds-deviation-table h2 {{ border-bottom-color: rgba(251, 191, 36, 0.45); }}
#rds-deviation-table h2 .sec-dot {{ background: var(--warn); color: var(--warn); }}
h3#validation {{ border-bottom-color: rgba(167, 139, 250, 0.45); }}
h3#validation .sec-dot {{ background: var(--purple); color: var(--purple); }}
h3#correlations {{ border-bottom-color: rgba(52, 211, 153, 0.45); }}
h3#correlations .sec-dot {{ background: var(--ok); color: var(--ok); }}
h3#diffs {{ border-bottom-color: rgba(244, 114, 182, 0.45); }}
h3#diffs .sec-dot {{ background: var(--pink); color: var(--pink); }}
.ref-panel h2 {{ border-bottom-color: rgba(129, 140, 248, 0.5); padding-bottom: 10px; margin-top: 0; }}
.ref-panel h2 .sec-dot {{ background: var(--accent2); color: var(--accent2); }}
.ref-panel {{
  margin: 0 0 28px; padding: 22px 22px 20px; border-radius: var(--radius);
  border: 1px solid rgba(129, 140, 248, 0.35);
  background: linear-gradient(145deg, rgba(129, 140, 248, 0.12), var(--surface));
  box-shadow: var(--shadow);
}}
.ref-panel .section-lead {{ margin-bottom: 14px; }}
.ref-dl {{ margin: 0; display: grid; grid-template-columns: minmax(120px, 200px) 1fr; gap: 10px 18px; font-size: 0.88rem; align-items: start; }}
.ref-dl dt {{ margin: 0; color: var(--muted); font-weight: 600; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em; }}
.ref-dl dd {{ margin: 0; word-break: break-word; }}
.ref-dl a {{ color: var(--accent); font-weight: 500; text-decoration: none; }}
.ref-dl a:hover {{ text-decoration: underline; color: var(--purple); }}
.ref-dl code {{ font-size: 0.8rem; padding: 2px 6px; border-radius: 6px; background: var(--surface2); border: 1px solid var(--border); }}
.ref-note {{ margin: 14px 0 0; font-size: 0.82rem; color: var(--muted); padding-top: 12px; border-top: 1px dashed var(--border); }}
.section-lead {{ color: var(--muted); font-size: 0.9rem; margin: 0 0 16px; max-width: 720px; }}
h3 {{ font-size: 0.95rem; margin: 20px 0 10px; color: var(--muted); font-weight: 600; }}
.val-part {{
  margin-bottom: 16px; padding: 16px 18px; border-radius: var(--radius);
  background: var(--surface); border: 1px solid var(--border);
  box-shadow: 0 2px 8px rgba(0,0,0,0.12);
}}
.val-part h4 {{ margin: 0 0 10px; font-size: 0.95rem; font-weight: 600; line-height: 1.4; }}
.tier {{
  font-size: 0.62rem; font-weight: 700; text-transform: uppercase; padding: 3px 10px; border-radius: 999px; margin-right: 8px;
  vertical-align: middle;
}}
.tier-req {{ background: rgba(251, 113, 133, 0.2); color: var(--coral); border: 1px solid rgba(251, 113, 133, 0.35); }}
.tier-opt {{ background: rgba(56, 189, 248, 0.15); color: var(--accent); border: 1px solid rgba(56, 189, 248, 0.3); }}
.cr-list {{ margin: 0; padding-left: 20px; font-size: 0.88rem; }}
.cr-list li {{ margin: 4px 0; }}
.bar-wrap {{ margin: 8px 0 8px; }}
.bar-row {{ display: flex; align-items: center; gap: 12px; margin: 8px 0; font-size: 0.84rem; }}
.bar-label {{ width: 200px; flex-shrink: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
.bar-track {{
  flex: 1; height: 12px; background: var(--surface2); border-radius: 999px; overflow: hidden;
  border: 1px solid var(--border);
}}
.bar-fill {{ height: 100%; border-radius: 999px; transition: width 0.4s ease; }}
.bar-fill-0 {{ background: linear-gradient(90deg, var(--accent), #22d3ee); }}
.bar-fill-1 {{ background: linear-gradient(90deg, var(--purple), var(--accent2)); }}
.bar-fill-2 {{ background: linear-gradient(90deg, var(--pink), var(--coral)); }}
.bar-fill-3 {{ background: linear-gradient(90deg, var(--ok), #5eead4); }}
.bar-fill-4 {{ background: linear-gradient(90deg, #fbbf24, #fb923c); }}
.bar-fill-5 {{ background: linear-gradient(90deg, var(--accent2), var(--pink)); }}
.bar-num {{
  min-width: 2rem; text-align: right; font-weight: 700; color: var(--accent); font-variant-numeric: tabular-nums;
}}
a.bar-link {{ color: var(--accent); text-decoration: none; font-weight: 500; }}
a.bar-link:hover {{ color: var(--purple); text-decoration: underline; }}
.val-part:target {{ box-shadow: 0 0 0 3px var(--accent), var(--shadow); }}
table.data {{ width: 100%; border-collapse: collapse; font-size: 0.84rem; border-radius: 12px; overflow: hidden; }}
table.data thead {{
  background: linear-gradient(180deg, var(--surface2), var(--surface));
}}
table.data th, table.data td {{ text-align: left; padding: 10px 12px; border-bottom: 1px solid var(--border); vertical-align: top; }}
table.data th {{ color: var(--text); font-weight: 600; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.04em; }}
.mono {{ font-family: ui-monospace, "Cascadia Code", monospace; }}
.small {{ font-size: 0.78rem; }}
.muted {{ color: var(--muted); }}
.truncate {{ max-width: 260px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
.scroll-wrap {{
  overflow: auto; max-height: 480px; border: 1px solid var(--border); border-radius: var(--radius);
  box-shadow: var(--shadow);
}}
.diff-card {{
  border-radius: var(--radius); margin-bottom: 16px; overflow: hidden;
  background: var(--surface); border: 1px solid var(--border);
  box-shadow: 0 2px 12px rgba(0,0,0,0.12);
}}
.diff-card[data-has-diff="1"] {{ border-left: 4px solid var(--warn); }}
.diff-card[data-has-diff="0"] {{ border-left: 4px solid var(--ok); }}
.diff-card header {{
  padding: 14px 16px; font-size: 0.84rem; border-bottom: 1px solid var(--border); word-break: break-all;
  background: linear-gradient(90deg, rgba(56, 189, 248, 0.06), transparent);
}}
.diff-card .meta {{ margin: 0; padding: 10px 16px; font-size: 0.8rem; }}
.diff-note {{ margin: 0; padding: 0 16px 10px; font-size: 0.8rem; color: var(--muted); white-space: pre-wrap; }}
.diff-pre {{
  margin: 0; padding: 16px; overflow: auto; max-height: 380px; font-size: 0.72rem; line-height: 1.45;
  background: var(--bg); border-top: 1px solid var(--border);
}}
.diff-pre code {{ font-family: ui-monospace, monospace; white-space: pre; }}
.hidden {{ display: none !important; }}
footer {{
  margin-top: 48px; padding: 20px; border-radius: var(--radius); border: 1px dashed var(--border);
  font-size: 0.82rem; color: var(--muted); background: var(--surface2);
}}
.omc-panel {{
  margin: 0 0 28px; padding: 22px 22px 20px; border-radius: var(--radius);
  border: 1px solid rgba(34, 211, 238, 0.35);
  background: linear-gradient(145deg, rgba(34, 211, 238, 0.1), var(--surface));
  box-shadow: var(--shadow);
}}
.omc-panel h2 {{ border-bottom-color: rgba(34, 211, 238, 0.45); padding-bottom: 10px; margin-top: 0; }}
.omc-panel h2 .sec-dot {{ background: #22d3ee; color: #22d3ee; }}
.omc-panel-skipped {{ border-color: var(--border); background: var(--surface2); }}
.omc-pre {{
  margin: 12px 0 0; padding: 16px; overflow: auto; max-height: 420px; font-size: 0.76rem; line-height: 1.45;
  background: var(--bg); border: 1px solid var(--border); border-radius: 10px;
}}
.omc-pre code {{ font-family: ui-monospace, monospace; white-space: pre-wrap; word-break: break-word; }}
</style>
</head>
<body class="vcu-dashboard">
<div class="layout">
<aside id="table-of-contents" aria-label="vCU report contents">
  <div class="brand-vcu">
    <span class="site-tag" title="virtual Centralized Unit (RAN CU)">vCU</span>
    <div>
      <div class="brand">RDS compliance</div>
      <p class="brand-sub">RAN central unit · cluster-compare · telco reference</p>
    </div>
  </div>
  <h2 class="toc-heading">Contents</h2>
  <nav class="toc-tree" aria-label="Section navigation">
    <a class="nav-link" href="#summary"><span class="nav-ico" aria-hidden="true">🏠</span> Summary</a>
    <a class="nav-link" href="#rds-reference"><span class="nav-ico" aria-hidden="true">📚</span> RDS reference</a>
    <a class="nav-link" href="#basic-info"><span class="nav-ico" aria-hidden="true">📌</span> Cluster information &amp; OMC validation</a>
    <a class="nav-link nav-link-req" href="#required-configurations"><span class="nav-ico" aria-hidden="true">📋</span> Required configurations</a>
    <div class="toc-sub">
      <a class="nav-link nav-sub" href="#bars">Template volume</a>
      <a class="nav-link nav-sub" href="#correlations">All correlated resources</a>
      <a class="nav-link nav-sub" href="#diffs">Aligned (no diff)</a>
    </div>
    <a class="nav-link" href="#rds-deviation-table"><span class="nav-ico" aria-hidden="true">📊</span> RDS deviation table</a>
    <a class="nav-link" href="#mismatch-diffs"><span class="nav-ico" aria-hidden="true">✏️</span> Mismatched configurations</a>
    <div class="toc-sub">
      <a class="nav-link nav-sub" href="#corr-table-mismatch">Resources with unified diff</a>
    </div>
    <a class="nav-link" href="#missing-configurations"><span class="nav-ico" aria-hidden="true">⚠️</span> Missing configurations</a>
    <div class="toc-sub">
      <a class="nav-link nav-sub" href="#validation">Missing CR detail</a>
    </div>
  </nav>
  <h2>Source</h2>
  <p style="font-size:0.78rem;color:var(--muted);margin:0;line-height:1.5;">
    <strong style="color:var(--text);">{esc(mg_label)}</strong><br/>
    telco-reference <code>{esc(ref["branch"])}</code><br/>
    <code style="font-size:0.65rem;word-break:break-all;opacity:0.9;">{esc(s["MetadataHash"])}</code>
  </p>
</aside>
<main>
  <header class="hero" id="summary">
  <div class="hero-h1-wrap">
    <span class="site-tag lg" id="vcu-site-tag" title="virtual Centralized Unit — RAN CU site">vCU</span>
    <h1 class="hero-h1">RDS compliance report <span class="hero-h1-sub">(cluster-compare)</span></h1>
  </div>
  <p class="lead">
    <strong>Reading order:</strong> <strong>Summary</strong> → <strong>RDS reference</strong> → <strong>Cluster information &amp; OMC</strong> →
    <strong>Required configurations</strong> (full compare inventory, highlighted) → <strong>RDS deviation table</strong> →
    <strong>Mismatched configurations</strong> → <strong>Missing configurations</strong>.
    Compare uses the <strong>telco RAN CU</strong> bundle (<code>kube-compare-reference</code>, OpenShift {esc(ref["minor"])}).
    Score cards jump to inventory and gap areas.
  </p>
  <div class="version-line">
    <strong>OpenShift (must-gather):</strong> {esc(cv["version"])}
    · <strong>Channel:</strong> {esc(cv["channel"])}
    · <strong>Reference bundle:</strong> {esc(ref["minor"])} telco RAN CU (vCU)
  </div>

  <div class="stats">
    <a class="stat stat-crs" href="#corr-table-all" title="Jump to full correlation table (all compared CRs)">
      <div class="v">{s["TotalCRs"]}</div><div class="l">CRs compared</div>
    </a>
    <a class="stat stat-gaps" href="#missing-configurations" title="Jump to missing configurations">
      <div class="v">{s["NumMissing"]}</div><div class="l">Missing vs RDS</div>
    </a>
    <a class="stat stat-diff" href="#mismatch-diffs" title="Jump to mismatch / unified diffs">
      <div class="v">{s["NumDiffCRs"]}</div><div class="l">With diff output</div>
    </a>
    <a class="stat stat-ok" href="#corr-table-all" title="Jump to correlation table (unmatched usually empty)">
      <div class="v">{len(s.get("UnmatchedCRS") or [])}</div><div class="l">Unmatched CRs</div>
    </a>
  </div>
  <nav class="toc-panel" id="contents-list" aria-label="Table of contents">
    <h2 class="toc-panel-title">Table of contents</h2>
    <ol class="toc-ol">
      <li><a href="#summary">Summary</a></li>
      <li><a href="#rds-reference">RDS reference</a></li>
      <li><a href="#basic-info">Cluster information &amp; OMC validation</a></li>
      <li><a href="#required-configurations">Required configurations</a>
        <ol>
          <li><a href="#bars">Template volume</a></li>
          <li><a href="#correlations">All correlated resources</a></li>
          <li><a href="#diffs">Aligned resources</a></li>
        </ol>
      </li>
      <li><a href="#rds-deviation-table">RDS deviation table</a></li>
      <li><a href="#mismatch-diffs">Mismatched configurations</a>
        <ol><li><a href="#corr-table-mismatch">Resources with unified diff</a></li></ol>
      </li>
      <li><a href="#missing-configurations">Missing configurations</a>
        <ol><li><a href="#validation">Missing CR detail</a></li></ol>
      </li>
    </ol>
  </nav>
  </header>
  <p class="stat-hint"><strong>How to read:</strong> follow the section order in the sidebar — <strong>RDS reference</strong>, then <strong>cluster &amp; OMC</strong>,
    then <strong>required configurations</strong> (inventory). Use the <strong>RDS deviation table</strong> for gap counts by part, then <strong>mismatched</strong> and <strong>missing</strong> for remediation detail.
    Search/filter applies to correlation tables and diff cards in <a href="#required-configurations">Required configurations</a> and <a href="#mismatch-diffs">Mismatched configurations</a>.</p>

  <section class="deviation-zone zone-ref ref-panel" id="rds-reference" aria-labelledby="rds-ref-title">
  <h2 id="rds-ref-title"><span class="sec-dot" aria-hidden="true"></span> RDS reference</h2>
  <p class="section-lead">
    This <strong>vCU</strong> report compares your cluster to the <strong>telco RAN central unit (CU)</strong> kube-compare bundle in openshift-kni/telco-reference.
    Use the links below to browse <code>metadata.yaml</code>, templates, and OpenShift {esc(ref["minor"])} documentation that match this compare.
  </p>
  <dl class="ref-dl">
    <dt>Git repository</dt>
    <dd><a href="{esc(ref["github_repo"])}" target="_blank" rel="noopener">openshift-kni/telco-reference</a></dd>
    <dt>Branch</dt>
    <dd><code>{esc(ref["branch"])}</code> <span class="muted">(aligned to OpenShift <strong>{esc(ref["minor"])}</strong> minor)</span></dd>
    <dt>Compare bundle</dt>
    <dd>
      <a href="{esc(ref["tree_kube_compare"])}" target="_blank" rel="noopener"><code>telco-ran/configuration/kube-compare-reference/</code></a>
      — templates + <code>metadata.yaml</code> consumed by <code>oc cluster-compare</code>
    </dd>
    <dt>metadata.yaml</dt>
    <dd><a href="{esc(ref["metadata_yaml"])}" target="_blank" rel="noopener">View on GitHub</a></dd>
    <dt>Product docs (RAN reference)</dt>
    <dd><a href="{esc(ref["docs_ran_du"])}" target="_blank" rel="noopener">Telco RAN reference components — OpenShift {esc(ref["minor"])}</a></dd>
    <dt>Bundle hash (this run)</dt>
    <dd><code>{esc(s["MetadataHash"])}</code> <span class="muted">— fingerprint of the reference payload used for this compare</span></dd>
  </dl>
  <p class="ref-note">
    If you compared against a <strong>local</strong> checkout, ensure it matches branch <code>{esc(ref["branch"])}</code> or the hash above may differ from upstream.
    Cluster OpenShift version from must-gather: <strong>{esc(cv["version"])}</strong>.
  </p>
  </section>

  <section class="deviation-zone zone-basic" id="basic-info">
  <h2><span class="sec-dot" aria-hidden="true"></span> Cluster information &amp; OMC validation</h2>
  <p class="section-lead">Cluster identity from must-gather (see version above) and <strong>OMC</strong> validation against the extracted must-gather.</p>
  {omc_section}
  </section>

  <section class="deviation-zone zone-required required-highlight" id="required-configurations">
  <h2><span class="sec-dot" aria-hidden="true"></span> Required configurations <span class="req-highlight-tag" title="Full cluster-compare inventory">Required</span></h2>
  <p class="section-lead">Full <strong>cluster-compare</strong> inventory: template volume, every correlated cluster resource vs reference template, and resources that matched with <strong>no</strong> unified diff. Use search/filter to narrow rows and diff cards.</p>

  <div class="controls">
    <label for="q">Search</label>
    <input type="search" id="q" placeholder="Filter tables and diff cards…" autocomplete="off"/>
    <label for="flt">Show diff cards</label>
    <select id="flt">
      <option value="all">All</option>
      <option value="diff">Unified diff only</option>
      <option value="nodiff">No diff text</option>
    </select>
  </div>

  <h3 id="bars"><span class="sec-dot" aria-hidden="true"></span> Correlations per reference template</h3>
  <p class="section-lead">Volume of correlated objects per template path.</p>
  <div class="bar-wrap">{''.join(bar_rows)}</div>

  <h3 id="correlations"><span class="sec-dot" aria-hidden="true"></span> All correlated resources</h3>
  <p class="section-lead">{len(d.get("Diffs", []))} rows — complete list. Same filter applies to <a href="#corr-table-mismatch">mismatch table</a> and diff cards in <a href="#mismatch-diffs">Mismatched configurations</a>.</p>
  <div class="scroll-wrap">
  <table class="data" id="corr-table-all">
    <thead><tr><th>Cluster resource</th><th>Reference template</th><th>Diff</th><th>Note</th><th></th></tr></thead>
    <tbody>{"".join(corr_rows)}</tbody>
  </table>
  </div>

  <h3 id="diffs"><span class="sec-dot" aria-hidden="true"></span> Aligned resources (no unified diff text)</h3>
  <p class="section-lead"><strong style="color:var(--ok);">Green</strong> edge — correlated; no diff output from compare (treat as aligned unless you expect drift).</p>
  {''.join(diff_panels_nodiff) if diff_panels_nodiff else '<p class="muted">No correlated resources without diff text.</p>'}
  </section>

  <section class="deviation-zone zone-deviation" id="rds-deviation-table">
  <h2><span class="sec-dot" aria-hidden="true"></span> RDS deviation table</h2>
  <p class="section-lead">Gaps vs the RDS reference — <strong>required</strong> rows are highlighted. Click a part or count for missing CR detail.</p>
  <table class="data" id="gaps-table">
    <thead><tr><th>Tier</th><th>Part</th><th>Message</th><th>Count</th></tr></thead>
    <tbody>{"".join(gap_table_rows)}</tbody>
  </table>
  </section>

  <section class="deviation-zone zone-mismatch" id="mismatch-diffs">
  <h2><span class="sec-dot" aria-hidden="true"></span> Mismatched configurations</h2>
  <p class="section-lead"><strong>Diff</strong> = live cluster resource differs from the standard template (unified diff text). Use the filter controls in <a href="#required-configurations">Required configurations</a> or below.</p>

  <h3><span class="sec-dot" aria-hidden="true"></span> Resources with unified diff (incorrect)</h3>
  <div class="scroll-wrap">
  <table class="data" id="corr-table-mismatch">
    <thead><tr><th>Cluster resource</th><th>Reference template</th><th>Diff</th><th>Note</th><th></th></tr></thead>
    <tbody>{mismatch_table_body}</tbody>
  </table>
  </div>
  {''.join(diff_panels_mismatch)}
  </section>

  <section class="deviation-zone zone-missing" id="missing-configurations">
  <h2><span class="sec-dot" aria-hidden="true"></span> Missing configurations</h2>
  <p class="section-lead"><strong>Missing CRs</strong> — reference expects these resources; they are absent or not validated. Required vs optional tiers; links open telco RAN CU documentation where available.</p>
  <h3 id="validation"><span class="sec-dot" aria-hidden="true"></span> Missing CR detail (full inventory)</h3>
  {''.join(val_sections)}
  </section>

  <footer>
    <strong>Refresh this report:</strong> run <code>python3 build-cu-dashboard.py</code> after updating <code>cluster-compare-report.json</code>.
    Outputs: <code>cluster-compare-dashboard-detailed.html</code> and <code>vCU-RDS-compliance-dashboard.html</code> (same content, vCU-tagged name).
    Must-gather archive: <code>tar -xf must-gather-vcu.tar.gz</code> (plain tar, not gzip).
  </footer>
</main>
</div>
<script>
(function () {{
  var q = document.getElementById("q");
  var flt = document.getElementById("flt");
  function norm(s) {{ return (s || "").toLowerCase(); }}
  function apply() {{
    var term = norm(q.value);
    var mode = flt.value;
    document.querySelectorAll(".diff-card").forEach(function (card) {{
      var has = card.getAttribute("data-has-diff") === "1";
      if (mode === "diff" && !has) {{ card.classList.add("hidden"); return; }}
      if (mode === "nodiff" && has) {{ card.classList.add("hidden"); return; }}
      if (term && norm(card.innerText).indexOf(term) === -1) {{ card.classList.add("hidden"); return; }}
      card.classList.remove("hidden");
    }});
    document.querySelectorAll("#corr-table-mismatch tbody tr, #corr-table-all tbody tr").forEach(function (tr) {{
      var has = tr.getAttribute("data-has-diff") === "1";
      if (mode === "diff" && !has) {{ tr.classList.add("hidden"); return; }}
      if (mode === "nodiff" && has) {{ tr.classList.add("hidden"); return; }}
      if (term && norm(tr.innerText).indexOf(term) === -1) {{ tr.classList.add("hidden"); return; }}
      tr.classList.remove("hidden");
    }});
  }}
  q.addEventListener("input", apply);
  flt.addEventListener("change", apply);
}})();
</script>
</body>
</html>
"""

    md_doc = render_cluster_compare_markdown(
        document_title="vCU — RDS compliance (cluster-compare)",
        intro=(
            "**Reading order:** **Summary** → **RDS reference** → **Cluster information & OMC validation** → "
            "**Required configurations** → **RDS deviation table** → **Mismatched configurations** → "
            "**Missing configurations**. This vCU must-gather is compared to the **telco RAN CU** reference "
            f"(`kube-compare-reference`, OpenShift {ref['minor']})."
        ),
        must_gather_label=mg_label,
        build_script="python3 build-cu-dashboard.py",
        extract_note="Must-gather archive: `tar -xf must-gather-vcu.tar.gz` (plain tar, not gzip).",
        cv=cv,
        s=s,
        ref=ref,
        val=val,
        d=d,
        omc_text=omc_text,
        omc_skip_reason=omc_skip,
    )
    OUT_MD.write_text(md_doc)
    OUT_HTML.write_text(doc)
    OUT_HTML_VCU.write_text(doc)
    print("Wrote", OUT_HTML, "bytes", len(doc))
    print("Wrote", OUT_HTML_VCU, "bytes", len(doc))
    print("Wrote", OUT_MD, "bytes", len(md_doc))


if __name__ == "__main__":
    main()
