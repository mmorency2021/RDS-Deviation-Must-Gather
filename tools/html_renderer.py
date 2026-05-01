"""Render a self-contained HTML compliance dashboard from prepared data."""
from __future__ import annotations

from tools.dashboard_core import esc


def render_html_dashboard(data: dict) -> str:
    """Generate a complete HTML document from *data* (as returned by
    ``dashboard_core.prepare_dashboard_data``).

    The output is a self-contained single-file HTML with inline CSS/JS,
    suitable for sharing or downloading.
    """
    pcfg = data["pcfg"]
    cv = data["cv"]
    ref = data["ref"]
    s = data["s"]
    mg_label = data["mg_label"]
    d = data["d"]

    cluster_node_summary = data.get("cluster_node_summary", {})
    node_rows_html = data.get("node_rows_html", "")

    bar_rows_html = "".join(data["bar_rows"])
    corr_rows_html = "".join(data["corr_rows"])
    diff_panels_nodiff_html = (
        "".join(data["diff_panels_nodiff"])
        if data["diff_panels_nodiff"]
        else '<p class="muted">No correlated resources without diff text.</p>'
    )
    gap_table_rows_html = "".join(data["gap_table_rows"])
    mismatch_table_body = data["mismatch_table_body"]
    diff_panels_mismatch_html = "".join(data["diff_panels_mismatch"])
    val_sections_html = "".join(data["val_sections"])
    omc_section = data["omc_section"]

    site_tag = pcfg["site_tag"]
    site_tag_title = pcfg["site_tag_title"]
    body_class = pcfg["body_class"]
    brand_class = pcfg["brand_class"]
    brand_label = pcfg["brand_label"]
    brand_sub = pcfg["brand_sub"]
    desc_meta = pcfg["description_meta"]
    title_prefix = pcfg["page_title_prefix"]
    title_suffix = pcfg["page_title_suffix"]
    ref_bundle_label = ref["reference_bundle_label"]
    docs_label = ref["docs_label"]

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{esc(title_prefix)} · {esc(title_suffix)}</title>
<meta name="description" content="{esc(desc_meta)}"/>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&display=swap" rel="stylesheet"/>
{_CSS}
</head>
<body class="{esc(body_class)}">
<div class="layout">
<aside id="table-of-contents" aria-label="{esc(site_tag)} report contents">
  <div class="{esc(brand_class)}">
    <span class="site-tag" title="{esc(site_tag_title)}">{esc(site_tag)}</span>
    <div>
      <div class="brand">{esc(brand_label)}</div>
      <p class="brand-sub">{esc(brand_sub)}</p>
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
  <h2>Cluster topology</h2>
  <p style="font-size:0.78rem;color:var(--muted);margin:0 0 8px;line-height:1.5;">
    <strong style="color:var(--text);">{cluster_node_summary.get("total", 0)} node{"s" if cluster_node_summary.get("total", 0) != 1 else ""}</strong>
    {"(SNO)" if cluster_node_summary.get("sno") else ""}<br/>
    masters: {cluster_node_summary.get("masters", 0)} · workers: {cluster_node_summary.get("workers", 0)} · infra: {cluster_node_summary.get("infra", 0)}
  </p>
</aside>
<main>
  <header class="hero" id="summary">
  <div class="hero-h1-wrap">
    <span class="site-tag lg" title="{esc(site_tag_title)}">{esc(site_tag)}</span>
    <h1 class="hero-h1">RDS compliance report <span class="hero-h1-sub">(cluster-compare)</span></h1>
  </div>
  <p class="lead">
    <strong>Reading order:</strong> <strong>Summary</strong> → <strong>RDS reference</strong> → <strong>Cluster information &amp; OMC</strong> →
    <strong>Required configurations</strong> (full compare inventory, highlighted) → <strong>RDS deviation table</strong> →
    <strong>Mismatched configurations</strong> → <strong>Missing configurations</strong>.
    Compare uses the <strong>{esc(ref_bundle_label)}</strong> bundle (<code>kube-compare-reference</code>, OpenShift {esc(ref["minor"])}).
    Score cards jump to inventory and gap areas.
  </p>
  <div class="version-line">
    <strong>OpenShift (must-gather):</strong> {esc(cv["version"])}
    · <strong>Channel:</strong> {esc(cv["channel"])}
    · <strong>Reference bundle:</strong> {esc(ref["minor"])} {esc(ref_bundle_label)}
  </div>

  <div class="stats">
    <a class="stat stat-crs" href="#corr-table-all" title="Jump to full correlation table">
      <div class="v">{s["TotalCRs"]}</div><div class="l">CRs compared</div>
    </a>
    <a class="stat stat-gaps" href="#missing-configurations" title="Jump to missing configurations">
      <div class="v">{s["NumMissing"]}</div><div class="l">Missing vs RDS</div>
    </a>
    <a class="stat stat-diff" href="#mismatch-diffs" title="Jump to mismatch / unified diffs">
      <div class="v">{s["NumDiffCRs"]}</div><div class="l">With diff output</div>
    </a>
    <a class="stat stat-ok" href="#corr-table-all" title="Jump to correlation table">
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
    then <strong>required configurations</strong> (inventory). Use the <strong>RDS deviation table</strong> for gap counts by part, then <strong>mismatched</strong> and <strong>missing</strong> for remediation detail.</p>

  <section class="deviation-zone zone-ref ref-panel" id="rds-reference" aria-labelledby="rds-ref-title">
  <h2 id="rds-ref-title"><span class="sec-dot" aria-hidden="true"></span> RDS reference</h2>
  <p class="section-lead">
    This <strong>{esc(site_tag)}</strong> report compares your cluster to the <strong>{esc(ref_bundle_label)}</strong> kube-compare bundle in openshift-kni/telco-reference.
    Use the links below to browse <code>metadata.yaml</code>, templates, and OpenShift {esc(ref["minor"])} documentation.
  </p>
  <dl class="ref-dl">
    <dt>Git repository</dt>
    <dd><a href="{esc(ref["github_repo"])}" target="_blank" rel="noopener">openshift-kni/telco-reference</a></dd>
    <dt>Branch</dt>
    <dd><code>{esc(ref["branch"])}</code> <span class="muted">(aligned to OpenShift <strong>{esc(ref["minor"])}</strong> minor)</span></dd>
    <dt>Compare bundle</dt>
    <dd>
      <a href="{esc(ref["tree_kube_compare"])}" target="_blank" rel="noopener"><code>{esc(ref["kube_compare_path"])}/</code></a>
      — templates + <code>metadata.yaml</code> consumed by <code>oc cluster-compare</code>
    </dd>
    <dt>metadata.yaml</dt>
    <dd><a href="{esc(ref["metadata_yaml"])}" target="_blank" rel="noopener">View on GitHub</a></dd>
    <dt>{esc(docs_label)}</dt>
    <dd><a href="{esc(ref["docs"])}" target="_blank" rel="noopener">{esc(docs_label)} — OpenShift {esc(ref["minor"])}</a></dd>
    <dt>Bundle hash (this run)</dt>
    <dd><code>{esc(s["MetadataHash"])}</code> <span class="muted">— fingerprint of the reference payload</span></dd>
  </dl>
  <p class="ref-note">
    If you compared against a <strong>local</strong> checkout, ensure it matches branch <code>{esc(ref["branch"])}</code>.
    Cluster OpenShift version from must-gather: <strong>{esc(cv["version"])}</strong>.
  </p>
  </section>

  <section class="deviation-zone zone-basic" id="basic-info">
  <h2><span class="sec-dot" aria-hidden="true"></span> Cluster information &amp; OMC validation</h2>
  <p class="section-lead">Cluster identity from must-gather and <strong>OMC</strong> validation.</p>

  <h3>Cluster topology ({cluster_node_summary.get("total", 0)} node{"s" if cluster_node_summary.get("total", 0) != 1 else ""}{"  — SNO" if cluster_node_summary.get("sno") else ""})</h3>
  <p class="section-lead">Masters: {cluster_node_summary.get("masters", 0)} · Workers: {cluster_node_summary.get("workers", 0)} · Infra: {cluster_node_summary.get("infra", 0)}</p>
  <div class="scroll-wrap" style="max-height:320px;">
  <table class="data" id="node-table">
    <thead><tr><th>Node name</th><th>Roles</th><th>Ready</th><th>CPU</th><th>Memory</th></tr></thead>
    <tbody>{node_rows_html if node_rows_html else '<tr><td colspan="5" class="muted">No node data found in must-gather.</td></tr>'}</tbody>
  </table>
  </div>

  {omc_section}
  </section>

  <section class="deviation-zone zone-required required-highlight" id="required-configurations">
  <h2><span class="sec-dot" aria-hidden="true"></span> Required configurations <span class="req-highlight-tag" title="Full cluster-compare inventory">Required</span></h2>
  <p class="section-lead">Full <strong>cluster-compare</strong> inventory: template volume, every correlated cluster resource vs reference template, and aligned resources.</p>

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
  <div class="bar-wrap">{bar_rows_html}</div>

  <h3 id="correlations"><span class="sec-dot" aria-hidden="true"></span> All correlated resources</h3>
  <p class="section-lead">{len(d.get("Diffs", []))} rows — complete list.</p>
  <div class="scroll-wrap">
  <table class="data" id="corr-table-all">
    <thead><tr><th>Cluster resource</th><th>Reference template</th><th>Diff</th><th>Note</th><th></th></tr></thead>
    <tbody>{corr_rows_html}</tbody>
  </table>
  </div>

  <h3 id="diffs"><span class="sec-dot" aria-hidden="true"></span> Aligned resources (no unified diff text)</h3>
  <p class="section-lead"><strong style="color:var(--ok);">Green</strong> edge — correlated; no diff output from compare.</p>
  {diff_panels_nodiff_html}
  </section>

  <section class="deviation-zone zone-deviation" id="rds-deviation-table">
  <h2><span class="sec-dot" aria-hidden="true"></span> RDS deviation table</h2>
  <p class="section-lead">Gaps vs the RDS reference — <strong>required</strong> rows are highlighted.</p>
  <table class="data" id="gaps-table">
    <thead><tr><th>Tier</th><th>Part</th><th>Message</th><th>Count</th></tr></thead>
    <tbody>{gap_table_rows_html}</tbody>
  </table>
  </section>

  <section class="deviation-zone zone-mismatch" id="mismatch-diffs">
  <h2><span class="sec-dot" aria-hidden="true"></span> Mismatched configurations</h2>
  <p class="section-lead"><strong>Diff</strong> = live cluster resource differs from the standard template.</p>

  <h3><span class="sec-dot" aria-hidden="true"></span> Resources with unified diff (incorrect)</h3>
  <div class="scroll-wrap">
  <table class="data" id="corr-table-mismatch">
    <thead><tr><th>Cluster resource</th><th>Reference template</th><th>Diff</th><th>Note</th><th></th></tr></thead>
    <tbody>{mismatch_table_body}</tbody>
  </table>
  </div>
  {diff_panels_mismatch_html}
  </section>

  <section class="deviation-zone zone-missing" id="missing-configurations">
  <h2><span class="sec-dot" aria-hidden="true"></span> Missing configurations</h2>
  <p class="section-lead"><strong>Missing CRs</strong> — reference expects these resources; they are absent or not validated.</p>
  <h3 id="validation"><span class="sec-dot" aria-hidden="true"></span> Missing CR detail (full inventory)</h3>
  {val_sections_html}
  </section>

  <footer>
    <strong>Generated by</strong> RDS Deviation Must-Gather Web Tool.
    Profile: <code>{esc(site_tag)}</code> · OpenShift <code>{esc(cv["version"])}</code> ·
    Reference: <code>{esc(ref["branch"])}</code>.
  </footer>
</main>
</div>
{_JS}
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Inline CSS (identical across all profiles — body class controls branding)
# ---------------------------------------------------------------------------
_CSS = """<style>
:root {
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
}
@media (prefers-color-scheme: light) {
  :root {
    --bg: #f1f5f9; --bg2: #e2e8f0; --surface: #ffffff; --surface2: #f8fafc;
    --border: #cbd5e1; --text: #0f172a; --muted: #64748b;
    --accent: #0284c7; --accent2: #4f46e5; --purple: #7c3aed; --pink: #db2777;
    --warn: #b45309; --warn-bg: rgba(251, 191, 36, 0.2);
    --ok: #047857; --ok-bg: rgba(52, 211, 153, 0.18);
    --coral: #e11d48;
    --missing-accent: #9a3412; --missing-accent-deep: #7c2d12; --missing-bg: rgba(124, 45, 18, 0.1);
    --req-emerald: #059669; --req-emerald-dim: rgba(5, 150, 105, 0.18); --req-emerald-glow: rgba(5, 150, 105, 0.4);
    --shadow: 0 4px 24px rgba(15, 23, 42, 0.08);
  }
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: "DM Sans", ui-sans-serif, system-ui, sans-serif;
  background: linear-gradient(165deg, var(--bg) 0%, var(--bg2) 45%, var(--bg) 100%);
  background-attachment: fixed;
  color: var(--text); line-height: 1.55; font-size: 0.95rem;
}
.site-tag {
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 0.62rem; font-weight: 800; letter-spacing: 0.14em;
  padding: 5px 11px; border-radius: 8px;
  background: linear-gradient(135deg, rgba(56,189,248,0.35), rgba(129,140,248,0.4));
  border: 1px solid rgba(56,189,248,0.55); color: var(--text); text-transform: uppercase;
  flex-shrink: 0;
}
.site-tag.lg { font-size: 0.72rem; padding: 7px 14px; border-radius: 10px; }
.brand-du, .brand-vcu, .brand-core, .brand-hub {
  display: flex; align-items: flex-start; gap: 12px; margin-bottom: 12px;
}
.brand-du .brand, .brand-vcu .brand, .brand-core .brand, .brand-hub .brand { margin-bottom: 2px; }
.brand-du .brand-sub, .brand-vcu .brand-sub, .brand-core .brand-sub, .brand-hub .brand-sub { margin-bottom: 0; }
.toc-heading { font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.14em; color: var(--muted); margin: 16px 0 10px; font-weight: 700; }
.toc-tree .toc-sub { margin: 4px 0 12px 6px; padding-left: 12px; border-left: 2px solid rgba(56, 189, 248, 0.25); }
.nav-link.nav-sub { font-size: 0.8rem; padding: 5px 10px; margin: 1px 0; color: var(--muted); }
.nav-link.nav-sub:hover { color: var(--accent); }
.toc-panel { margin-top: 20px; padding: 16px 18px; border-radius: var(--radius); background: var(--surface); border: 1px solid var(--border); box-shadow: 0 2px 12px rgba(0,0,0,0.1); }
.toc-panel-title { font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.1em; color: var(--muted); margin: 0 0 12px; font-weight: 700; }
.toc-ol { margin: 0; padding-left: 1.15rem; font-size: 0.88rem; }
.toc-ol ol { margin: 6px 0 10px; padding-left: 1.1rem; font-size: 0.86rem; }
.toc-ol a { color: var(--accent); text-decoration: none; font-weight: 500; }
.toc-ol a:hover { text-decoration: underline; color: var(--purple); }
.hero-h1-wrap { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; margin-bottom: 12px; }
.hero-h1 { font-size: 1.55rem; font-weight: 700; margin: 0; letter-spacing: -0.03em; line-height: 1.2; }
.hero-h1-sub { font-size: 1rem; font-weight: 500; color: var(--muted); }
.layout { display: grid; grid-template-columns: 260px 1fr; min-height: 100vh; }
@media (max-width: 880px) {
  .layout { grid-template-columns: 1fr; }
  aside { position: relative; border-right: none; border-bottom: 1px solid var(--border); max-height: none; }
}
aside {
  position: sticky; top: 0; align-self: start; max-height: 100vh; overflow: auto;
  padding: 22px 16px; border-right: 1px solid var(--border);
  background: linear-gradient(180deg, var(--surface2) 0%, var(--surface) 100%);
  box-shadow: inset -1px 0 0 rgba(56, 189, 248, 0.06);
}
.brand { font-weight: 700; font-size: 1rem; letter-spacing: -0.02em; margin-bottom: 4px;
  background: linear-gradient(90deg, var(--accent), var(--purple)); -webkit-background-clip: text; background-clip: text; color: transparent; }
.brand-sub { font-size: 0.72rem; color: var(--muted); margin-bottom: 18px; line-height: 1.35; }
aside h2 { font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.12em; color: var(--muted); margin: 20px 0 10px; font-weight: 600; }
.nav-link {
  color: var(--text); text-decoration: none; font-size: 0.88rem; display: flex; align-items: center; gap: 8px;
  padding: 8px 10px; margin: 2px 0; border-radius: 10px; transition: background 0.15s ease, color 0.15s ease;
}
.nav-link:hover { background: rgba(56, 189, 248, 0.12); color: var(--accent); }
.nav-ico { font-size: 1.05rem; opacity: 0.92; width: 1.25em; text-align: center; }
main { padding: 28px 32px 72px; max-width: 920px; }
html { scroll-behavior: smooth; }
h1, h2, .val-part, .diff-card, #rds-reference, #omc-validation, #basic-info, #required-configurations, #rds-deviation-table, #mismatch-diffs, #missing-configurations { scroll-margin-top: 96px; }
.deviation-zone { margin: 0 0 8px; }
.zone-basic { padding-left: 14px; margin-left: -2px; border-left: 4px solid #22d3ee; }
.zone-missing { padding-left: 14px; margin-left: -2px; border-left: 4px solid var(--missing-accent); background: linear-gradient(90deg, var(--missing-bg), transparent 52%); border-radius: 0 var(--radius) var(--radius) 0; }
.zone-mismatch { padding-left: 14px; margin-left: -2px; border-left: 4px solid var(--pink); }
.zone-other { padding-left: 14px; margin-left: -2px; border-left: 4px solid var(--accent2); }
.zone-ref { padding-left: 14px; margin-left: -2px; border-left: 4px solid var(--accent2); }
.zone-required { padding-left: 14px; margin-left: -2px; border-left: 4px solid var(--req-emerald); }
.zone-required.required-highlight {
  border-radius: var(--radius); padding-top: 12px; padding-bottom: 8px;
  background: linear-gradient(165deg, var(--req-emerald-dim) 0%, var(--surface) 55%);
  box-shadow: 0 0 0 1px var(--req-emerald-glow), 0 4px 28px rgba(16, 185, 129, 0.18), inset 0 1px 0 rgba(255,255,255,0.06);
}
.req-highlight-tag {
  display: inline-flex; align-items: center; font-size: 0.58rem; font-weight: 800; letter-spacing: 0.14em;
  text-transform: uppercase; padding: 6px 14px; margin-left: auto; border-radius: 999px; color: var(--text);
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.45), rgba(52, 211, 153, 0.22));
  border: 1px solid rgba(16, 185, 129, 0.75); box-shadow: 0 0 16px rgba(16, 185, 129, 0.35); flex-shrink: 0;
}
.nav-link.nav-link-req { background: rgba(16, 185, 129, 0.14); border: 1px solid rgba(16, 185, 129, 0.4); }
.nav-link.nav-link-req:hover { background: rgba(16, 185, 129, 0.22); color: var(--req-emerald); }
#missing-configurations h2 { border-bottom-color: rgba(194, 65, 12, 0.45); }
#missing-configurations h2 .sec-dot { background: var(--missing-accent); color: var(--missing-accent); }
#required-configurations h2 { border-bottom-color: rgba(16, 185, 129, 0.5); }
#required-configurations h2 .sec-dot { background: var(--req-emerald); color: var(--req-emerald); }
.zone-deviation { padding-left: 14px; margin-left: -2px; border-left: 4px solid var(--warn); }
table.data#gaps-table tbody tr:has(.tier-req) { background: rgba(251, 191, 36, 0.09); }
table.data#gaps-table tbody tr:has(.tier-req):hover { background: rgba(251, 191, 36, 0.14); }
.hero {
  padding: 28px 24px 24px; margin: -8px -12px 28px; border-radius: var(--radius);
  background: linear-gradient(135deg, rgba(56, 189, 248, 0.14) 0%, rgba(129, 140, 248, 0.12) 50%, rgba(244, 114, 182, 0.08) 100%);
  border: 1px solid rgba(56, 189, 248, 0.25); box-shadow: var(--shadow);
}
h1 { font-size: 1.65rem; font-weight: 700; margin: 0 0 12px; letter-spacing: -0.03em; line-height: 1.25; }
.lead { color: var(--muted); font-size: 0.95rem; margin-bottom: 0; max-width: 680px; }
.version-line {
  font-size: 0.88rem; margin-top: 18px; padding: 14px 16px;
  background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
  border-left: 4px solid var(--ok); box-shadow: 0 2px 12px rgba(0,0,0,0.12);
}
.version-line strong { color: var(--text); }
.stat-hint { font-size: 0.82rem; color: var(--muted); margin: 16px 0 20px; padding: 12px 14px; background: var(--surface2); border-radius: 10px; border-left: 3px solid var(--purple); }
.stats { display: grid; grid-template-columns: repeat(auto-fill, minmax(132px, 1fr)); gap: 14px; margin-top: 22px; }
a.stat {
  display: block; text-decoration: none; color: inherit; border-radius: var(--radius); padding: 16px 18px;
  transition: transform 0.18s ease, box-shadow 0.18s ease; border: 1px solid var(--border); box-shadow: 0 2px 12px rgba(0,0,0,0.15);
}
a.stat:hover { transform: translateY(-2px); box-shadow: 0 10px 28px rgba(56, 189, 248, 0.15); }
a.stat-crs { background: linear-gradient(145deg, rgba(56, 189, 248, 0.18), var(--surface)); border-color: rgba(56, 189, 248, 0.35); }
a.stat-crs .v { color: var(--accent); }
a.stat-gaps { background: linear-gradient(145deg, var(--missing-bg), var(--surface)); border-color: rgba(194, 65, 12, 0.4); }
a.stat-gaps .v { color: var(--missing-accent); }
a.stat-diff { background: linear-gradient(145deg, rgba(244, 114, 182, 0.12), var(--surface)); border-color: rgba(244, 114, 182, 0.3); }
a.stat-diff .v { color: var(--pink); }
a.stat-ok { background: linear-gradient(145deg, var(--ok-bg), var(--surface)); border-color: rgba(52, 211, 153, 0.35); }
a.stat-ok .v { color: var(--ok); }
a.stat .v { font-size: 1.75rem; font-weight: 700; letter-spacing: -0.02em; line-height: 1.1; }
a.stat .l { font-size: 0.7rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; margin-top: 8px; font-weight: 600; }
a.gap-jump { color: var(--accent); text-decoration: none; font-weight: 600; }
a.gap-jump:hover { text-decoration: underline; color: var(--purple); }
a.gap-count { font-weight: 700; }
table.data tbody tr:nth-child(even) td { background: rgba(56, 189, 248, 0.04); }
table.data tr:hover td { background: rgba(129, 140, 248, 0.1) !important; }
.back-ref { margin: 0 0 10px; font-size: 0.8rem; }
.back-ref a { color: var(--accent); text-decoration: none; font-weight: 500; }
.back-ref a:hover { color: var(--purple); text-decoration: underline; }
.controls {
  display: flex; flex-wrap: wrap; gap: 12px; align-items: center; margin: 20px 0 24px;
  padding: 16px 18px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); box-shadow: var(--shadow);
}
.controls label { font-weight: 600; font-size: 0.82rem; color: var(--muted); }
.controls input[type="search"] {
  flex: 1; min-width: 200px; padding: 10px 14px; border-radius: 10px; border: 2px solid var(--border);
  background: var(--bg); color: var(--text); font-size: 0.9rem; transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
.controls input[type="search"]:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.25); }
.controls select { padding: 10px 12px; border-radius: 10px; border: 2px solid var(--border); background: var(--bg); color: var(--text); font-weight: 500; cursor: pointer; }
.controls select:focus { outline: none; border-color: var(--accent); }
h2 {
  font-size: 1.15rem; font-weight: 700; margin: 40px 0 12px; padding: 0 0 10px 0;
  border-bottom: 2px solid var(--border); letter-spacing: -0.02em; display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
}
h2 .sec-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; box-shadow: 0 0 12px currentColor; }
h3 { font-size: 0.95rem; margin: 20px 0 10px; color: var(--muted); font-weight: 600; }
.ref-panel h2 { border-bottom-color: rgba(129, 140, 248, 0.5); padding-bottom: 10px; margin-top: 0; }
.ref-panel h2 .sec-dot { background: var(--accent2); color: var(--accent2); }
.ref-panel { margin: 0 0 28px; padding: 22px 22px 20px; border-radius: var(--radius); border: 1px solid rgba(129, 140, 248, 0.35); background: linear-gradient(145deg, rgba(129, 140, 248, 0.12), var(--surface)); box-shadow: var(--shadow); }
.ref-panel .section-lead { margin-bottom: 14px; }
.ref-dl { margin: 0; display: grid; grid-template-columns: minmax(120px, 200px) 1fr; gap: 10px 18px; font-size: 0.88rem; align-items: start; }
.ref-dl dt { margin: 0; color: var(--muted); font-weight: 600; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em; }
.ref-dl dd { margin: 0; word-break: break-word; }
.ref-dl a { color: var(--accent); font-weight: 500; text-decoration: none; }
.ref-dl a:hover { text-decoration: underline; color: var(--purple); }
.ref-dl code { font-size: 0.8rem; padding: 2px 6px; border-radius: 6px; background: var(--surface2); border: 1px solid var(--border); }
.ref-note { margin: 14px 0 0; font-size: 0.82rem; color: var(--muted); padding-top: 12px; border-top: 1px dashed var(--border); }
.section-lead { color: var(--muted); font-size: 0.9rem; margin: 0 0 16px; max-width: 720px; }
.val-part { margin-bottom: 16px; padding: 16px 18px; border-radius: var(--radius); background: var(--surface); border: 1px solid var(--border); box-shadow: 0 2px 8px rgba(0,0,0,0.12); }
.val-part h4 { margin: 0 0 10px; font-size: 0.95rem; font-weight: 600; line-height: 1.4; }
.tier { font-size: 0.62rem; font-weight: 700; text-transform: uppercase; padding: 3px 10px; border-radius: 999px; margin-right: 8px; vertical-align: middle; }
.tier-req { background: rgba(251, 113, 133, 0.2); color: var(--coral); border: 1px solid rgba(251, 113, 133, 0.35); }
.tier-opt { background: rgba(56, 189, 248, 0.15); color: var(--accent); border: 1px solid rgba(56, 189, 248, 0.3); }
.cr-list { margin: 0; padding-left: 20px; font-size: 0.88rem; }
.cr-list li { margin: 4px 0; }
.bar-wrap { margin: 8px 0 8px; }
.bar-row { display: flex; align-items: center; gap: 12px; margin: 8px 0; font-size: 0.84rem; }
.bar-label { width: 200px; flex-shrink: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bar-track { flex: 1; height: 12px; background: var(--surface2); border-radius: 999px; overflow: hidden; border: 1px solid var(--border); }
.bar-fill { height: 100%; border-radius: 999px; transition: width 0.4s ease; }
.bar-fill-0 { background: linear-gradient(90deg, var(--accent), #22d3ee); }
.bar-fill-1 { background: linear-gradient(90deg, var(--purple), var(--accent2)); }
.bar-fill-2 { background: linear-gradient(90deg, var(--pink), var(--coral)); }
.bar-fill-3 { background: linear-gradient(90deg, var(--ok), #5eead4); }
.bar-fill-4 { background: linear-gradient(90deg, #fbbf24, #fb923c); }
.bar-fill-5 { background: linear-gradient(90deg, var(--accent2), var(--pink)); }
.bar-num { min-width: 2rem; text-align: right; font-weight: 700; color: var(--accent); font-variant-numeric: tabular-nums; }
a.bar-link { color: var(--accent); text-decoration: none; font-weight: 500; }
a.bar-link:hover { color: var(--purple); text-decoration: underline; }
.val-part:target { box-shadow: 0 0 0 3px var(--accent), var(--shadow); }
table.data { width: 100%; border-collapse: collapse; font-size: 0.84rem; border-radius: 12px; overflow: hidden; }
table.data thead { background: linear-gradient(180deg, var(--surface2), var(--surface)); }
table.data th, table.data td { text-align: left; padding: 10px 12px; border-bottom: 1px solid var(--border); vertical-align: top; }
table.data th { color: var(--text); font-weight: 600; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.04em; }
.mono { font-family: ui-monospace, "Cascadia Code", monospace; }
.small { font-size: 0.78rem; }
.muted { color: var(--muted); }
.truncate { max-width: 260px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.scroll-wrap { overflow: auto; max-height: 480px; border: 1px solid var(--border); border-radius: var(--radius); box-shadow: var(--shadow); }
.diff-card { border-radius: var(--radius); margin-bottom: 16px; overflow: hidden; background: var(--surface); border: 1px solid var(--border); box-shadow: 0 2px 12px rgba(0,0,0,0.12); }
.diff-card[data-has-diff="1"] { border-left: 4px solid var(--warn); }
.diff-card[data-has-diff="0"] { border-left: 4px solid var(--ok); }
.diff-card header { padding: 14px 16px; font-size: 0.84rem; border-bottom: 1px solid var(--border); word-break: break-all; background: linear-gradient(90deg, rgba(56, 189, 248, 0.06), transparent); }
.diff-card .meta { margin: 0; padding: 10px 16px; font-size: 0.8rem; }
.diff-note { margin: 0; padding: 0 16px 10px; font-size: 0.8rem; color: var(--muted); white-space: pre-wrap; }
.diff-pre { margin: 0; padding: 16px; overflow: auto; max-height: 380px; font-size: 0.72rem; line-height: 1.45; background: var(--bg); border-top: 1px solid var(--border); }
.diff-pre code { font-family: ui-monospace, monospace; white-space: pre; }
.hidden { display: none !important; }
footer { margin-top: 48px; padding: 20px; border-radius: var(--radius); border: 1px dashed var(--border); font-size: 0.82rem; color: var(--muted); background: var(--surface2); }
.omc-panel { margin: 0 0 28px; padding: 22px 22px 20px; border-radius: var(--radius); border: 1px solid rgba(34, 211, 238, 0.35); background: linear-gradient(145deg, rgba(34, 211, 238, 0.1), var(--surface)); box-shadow: var(--shadow); }
.omc-panel h2 { border-bottom-color: rgba(34, 211, 238, 0.45); padding-bottom: 10px; margin-top: 0; }
.omc-panel h2 .sec-dot { background: #22d3ee; color: #22d3ee; }
.omc-panel-skipped { border-color: var(--border); background: var(--surface2); }
.omc-pre { margin: 12px 0 0; padding: 16px; overflow: auto; max-height: 420px; font-size: 0.76rem; line-height: 1.45; background: var(--bg); border: 1px solid var(--border); border-radius: 10px; }
.omc-pre code { font-family: ui-monospace, monospace; white-space: pre-wrap; word-break: break-word; }
.node-ready { color: var(--ok); font-weight: 600; }
.node-notready { color: var(--coral); font-weight: 600; }
</style>"""

_JS = """<script>
(function () {
  var q = document.getElementById("q");
  var flt = document.getElementById("flt");
  function norm(s) { return (s || "").toLowerCase(); }
  function apply() {
    var term = norm(q.value);
    var mode = flt.value;
    document.querySelectorAll(".diff-card").forEach(function (card) {
      var has = card.getAttribute("data-has-diff") === "1";
      if (mode === "diff" && !has) { card.classList.add("hidden"); return; }
      if (mode === "nodiff" && has) { card.classList.add("hidden"); return; }
      if (term && norm(card.innerText).indexOf(term) === -1) { card.classList.add("hidden"); return; }
      card.classList.remove("hidden");
    });
    document.querySelectorAll("#corr-table-mismatch tbody tr, #corr-table-all tbody tr").forEach(function (tr) {
      var has = tr.getAttribute("data-has-diff") === "1";
      if (mode === "diff" && !has) { tr.classList.add("hidden"); return; }
      if (mode === "nodiff" && has) { tr.classList.add("hidden"); return; }
      if (term && norm(tr.innerText).indexOf(term) === -1) { tr.classList.add("hidden"); return; }
      tr.classList.remove("hidden");
    });
  }
  q.addEventListener("input", apply);
  flt.addEventListener("change", apply);
})();
</script>"""
