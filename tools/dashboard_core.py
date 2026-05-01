"""Shared dashboard data processing — profile-aware helpers and data preparation."""
from __future__ import annotations

import html
import json
import re
from collections import Counter
from pathlib import Path

from tools.cluster_version import load_cluster_version, ocp_minor_version
from tools.cluster_nodes import load_cluster_nodes, node_summary
from tools.omc_runner import capture_omc_validation, build_omc_html_section


# ---------------------------------------------------------------------------
# Profile configurations
# ---------------------------------------------------------------------------
PROFILES: dict[str, dict] = {
    "RAN": {
        "site_tag": "vDU",
        "site_tag_title": "virtual Distributed Unit — RAN DU site",
        "body_class": "vdu-dashboard",
        "brand_class": "brand-du",
        "brand_label": "RDS compliance",
        "brand_sub": "RAN distributed unit · cluster-compare · telco reference",
        "description_meta": "vDU (RAN DU site) cluster-compare report: missing CRs, mismatch diffs, OMC validation, telco RDS reference.",
        "page_title_prefix": "vDU",
        "page_title_suffix": "RDS compliance — cluster-compare (RAN distributed unit)",
        "reference_bundle_label": "telco RAN DU",
        "kube_compare_path": "telco-ran/configuration/kube-compare-reference",
        "docs_path_segment": "ran/telco-ran-ref-du-components.html",
        "docs_label": "Telco RAN reference components",
        "intro_bundle_label": "telco RAN DU",
        "md_reference_bundle_label": "telco RAN DU (vDU)",
        "md_compare_bundle_path": "telco-ran/configuration/kube-compare-reference/",
        "md_docs_label": "Product docs (RAN ref DU)",
        "build_script": "python3 build-du-dashboard.py",
        "extract_note": "Must-gather archive: `tar -xf must-gather-vdu.tar.gz`.",
    },
    "CORE": {
        "site_tag": "CORE",
        "site_tag_title": "Telco Core site",
        "body_class": "core-dashboard",
        "brand_class": "brand-core",
        "brand_label": "RDS compliance",
        "brand_sub": "Telco core · cluster-compare · telco reference",
        "description_meta": "Telco Core cluster-compare report: missing CRs, mismatch diffs, OMC validation, telco RDS reference.",
        "page_title_prefix": "CORE",
        "page_title_suffix": "RDS compliance — cluster-compare (telco core)",
        "reference_bundle_label": "telco core",
        "kube_compare_path": "telco-core/configuration/reference-crs-kube-compare",
        "docs_path_segment": "core/telco-core-ref-design-components.html",
        "docs_label": "Telco Core reference components",
        "intro_bundle_label": "telco core",
        "md_reference_bundle_label": "telco core",
        "md_compare_bundle_path": "telco-core/configuration/reference-crs-kube-compare/",
        "md_docs_label": "Product docs (Core ref)",
        "build_script": "python3 webapp",
        "extract_note": "",
    },
    "HUB": {
        "site_tag": "HUB",
        "site_tag_title": "Telco Hub / management cluster",
        "body_class": "hub-dashboard",
        "brand_class": "brand-hub",
        "brand_label": "RDS compliance",
        "brand_sub": "Telco hub · cluster-compare · telco reference",
        "description_meta": "Telco Hub cluster-compare report: missing CRs, mismatch diffs, OMC validation, telco RDS reference.",
        "page_title_prefix": "HUB",
        "page_title_suffix": "RDS compliance — cluster-compare (telco hub)",
        "reference_bundle_label": "telco hub",
        "kube_compare_path": "telco-hub/configuration/reference-crs-kube-compare",
        "docs_path_segment": "ran/telco-ran-ref-hub-components.html",
        "docs_label": "Telco Hub reference components",
        "intro_bundle_label": "telco hub",
        "md_reference_bundle_label": "telco hub",
        "md_compare_bundle_path": "telco-hub/configuration/reference-crs-kube-compare/",
        "md_docs_label": "Product docs (Hub ref)",
        "build_script": "python3 webapp",
        "extract_note": "",
    },
}


def get_profile_config(profile: str) -> dict:
    """Return the profile configuration dict. Raises on unknown profile."""
    profile = profile.upper()
    if profile not in PROFILES:
        raise ValueError(f"Unknown profile: {profile!r}. Expected RAN, CORE, or HUB.")
    return PROFILES[profile]


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def esc(x: str) -> str:
    """HTML-escape a value."""
    return html.escape(str(x) if x is not None else "")


def md_cell(x: str) -> str:
    """Escape pipe/newlines for Markdown pipe tables."""
    return str(x).replace("|", "\\|").replace("\n", " ").strip()


def gap_anchor_index(part_name: str, comp_name: str, index: int) -> str:
    """Stable id for validation gap detail + table jump links."""
    raw = f"{part_name}-{comp_name}-{index}"
    s = re.sub(r"[^a-zA-Z0-9_-]+", "-", raw).strip("-").lower()
    return f"gap-{s[:96]}" if s else f"gap-{index}"


def must_gather_source_label(extract_dir: Path, profile: str = "RAN") -> str:
    """Label for sidebar from extracted must-gather folder name(s)."""
    tag = get_profile_config(profile)["site_tag"]
    fallback = f"must-gather ({tag})"
    if not extract_dir.is_dir():
        return fallback
    subs = sorted(p.name for p in extract_dir.iterdir() if p.is_dir())
    if not subs:
        return fallback
    if len(subs) == 1:
        return subs[0]
    return f"{subs[0]} (+{len(subs) - 1} more)"


def telco_reference_urls(cv_version: str, profile: str = "RAN") -> dict[str, str]:
    """Build canonical reference URLs for the given profile and cluster version."""
    pcfg = get_profile_config(profile)
    minor = ocp_minor_version(cv_version if cv_version and cv_version != "unknown" else "4.20")
    branch = f"release-{minor}"
    gh = "https://github.com/openshift-kni/telco-reference"
    kube_path = pcfg["kube_compare_path"]
    return {
        "minor": minor,
        "branch": branch,
        "github_repo": gh,
        "tree_kube_compare": f"{gh}/tree/{branch}/{kube_path}",
        "metadata_yaml": f"{gh}/blob/{branch}/{kube_path}/metadata.yaml",
        "docs": (
            f"https://docs.openshift.com/container-platform/{minor}/scalability_and_performance/"
            f"telco_ref_design_specs/{pcfg['docs_path_segment']}"
        ),
        "docs_label": pcfg["docs_label"],
        "kube_compare_path": kube_path,
        "reference_bundle_label": pcfg["reference_bundle_label"],
    }


# ---------------------------------------------------------------------------
# Data preparation
# ---------------------------------------------------------------------------

def prepare_dashboard_data(
    report_json: Path,
    extract_dir: Path,
    profile: str = "RAN",
) -> dict:
    """Load cluster-compare JSON and build all derived data for rendering.

    Returns a dict consumed by ``html_renderer.render_html_dashboard()``
    and ``md_renderer.render_cluster_compare_markdown()``.
    """
    pcfg = get_profile_config(profile)
    cv = load_cluster_version(extract_dir)
    mg_label = must_gather_source_label(extract_dir, profile)
    d = json.loads(report_json.read_text())
    s = d["Summary"]
    ref = telco_reference_urls(cv["version"], profile)
    val = s.get("ValidationIssuses") or {}

    # Validation anchors for gap table + detail rows
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
                    if isinstance(doc, str) and doc.startswith("http")
                    else ""
                )
                li_items.append(f"<li><code>{esc(cr)}</code>{link}</li>")
            val_sections.append(
                f'<section class="val-part" id="{gid}">'
                f'<h4><span class="tier {tier_cls}">{tier}</span> {esc(part_name)} · '
                f"<em>{esc(comp_name)}</em> — {msg} ({len(crs)})</h4>"
                f'<p class="back-ref"><a href="#gaps-table">↑ Back to RDS deviation summary</a></p>'
                f'<ul class="cr-list">{"".join(li_items)}</ul>'
                f"</section>"
            )
            gap_table_rows.append(
                "<tr>"
                f'<td><span class="tier {tier_cls}">{tier}</span></td>'
                f'<td><a class="gap-jump" href="#{gid}" title="Open RDS deviation detail">{esc(part_name)}</a></td>'
                f'<td>{esc(comp.get("Msg", ""))}</td>'
                f'<td><a class="gap-jump gap-count" href="#{gid}" title="Open RDS deviation detail">{len(crs)}</a></td>'
                "</tr>"
            )

    # Correlation rows + diff panels
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
        panel = (
            f'<article class="diff-card" id="diff-{i}" data-has-diff="{"1" if out else "0"}">'
            f'<header><span class="mono">{esc(cr)}</span></header>'
            f'<p class="meta"><strong>Template:</strong> <code>{esc(tpl)}</code></p>'
            f'{desc_html}'
            f'<pre class="diff-pre"><code>{body}</code></pre>'
            f"</article>"
        )
        if out:
            diff_panels_mismatch.append(panel)
        else:
            diff_panels_nodiff.append(panel)

    mismatch_table_body = (
        "".join(corr_rows_mismatch)
        if corr_rows_mismatch
        else '<tr><td colspan="5" class="muted">No correlated resources produced unified diff text in this report.</td></tr>'
    )

    # Bar chart data
    c = Counter(x.get("CorrelatedTemplate", "") for x in d.get("Diffs", []))
    mx = max(c.values()) if c else 1
    bar_rows = []
    for bi, (k, v) in enumerate(c.most_common(14)):
        pct = round(100 * v / mx)
        bar_rows.append(
            f'<div class="bar-row">'
            f'<a class="bar-label bar-link" href="#correlations" title="Open correlation table">'
            f'{esc(k.split("/")[-1][:28])}</a>'
            f'<div class="bar-track"><div class="bar-fill bar-fill-{bi % 6}" style="width:{pct}%"></div></div>'
            f'<span class="bar-num">{v}</span></div>'
        )

    agg_rows = "".join(
        f"<tr><td>{esc(k[:78])}</td><td>{v}</td></tr>" for k, v in c.most_common(28)
    )

    # Cluster nodes
    cluster_nodes = load_cluster_nodes(extract_dir)
    cluster_node_summary = node_summary(cluster_nodes)

    # Node HTML for sidebar
    node_rows_html = ""
    for n in cluster_nodes:
        roles_str = ", ".join(n["roles"]) if n["roles"] else "none"
        ready_cls = "node-ready" if str(n["ready"]) == "True" else "node-notready"
        node_rows_html += (
            f'<tr><td class="mono small">{esc(n["name"][:48])}</td>'
            f'<td>{esc(roles_str)}</td>'
            f'<td class="{ready_cls}">{"Ready" if str(n["ready"]) == "True" else "NotReady"}</td>'
            f'<td>{esc(str(n["cpu"]))}</td>'
            f'<td>{esc(n["memory"])}</td></tr>'
        )

    # OMC
    omc_text, omc_skip = capture_omc_validation(extract_dir)
    omc_section = build_omc_html_section(omc_text, omc_skip)

    return {
        "profile": profile,
        "pcfg": pcfg,
        "cv": cv,
        "mg_label": mg_label,
        "d": d,
        "s": s,
        "ref": ref,
        "val": val,
        "val_sections": val_sections,
        "gap_table_rows": gap_table_rows,
        "corr_rows": corr_rows,
        "corr_rows_mismatch": corr_rows_mismatch,
        "diff_panels_mismatch": diff_panels_mismatch,
        "diff_panels_nodiff": diff_panels_nodiff,
        "mismatch_table_body": mismatch_table_body,
        "bar_rows": bar_rows,
        "agg_rows": agg_rows,
        "omc_text": omc_text,
        "omc_skip": omc_skip,
        "omc_section": omc_section,
        "cluster_nodes": cluster_nodes,
        "cluster_node_summary": cluster_node_summary,
        "node_rows_html": node_rows_html,
    }
