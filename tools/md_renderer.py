"""Render a Markdown compliance report from prepared dashboard data."""
from __future__ import annotations

from tools.dashboard_core import md_cell


def render_cluster_compare_markdown(data: dict) -> str:
    """Generate the Markdown report from *data* (as returned by
    ``dashboard_core.prepare_dashboard_data``).
    """
    pcfg = data["pcfg"]
    cv = data["cv"]
    s = data["s"]
    ref = data["ref"]
    val = data["val"]
    d = data["d"]
    mg_label = data["mg_label"]
    omc_text = data["omc_text"]
    omc_skip = data["omc_skip"]

    cluster_nodes = data.get("cluster_nodes", [])
    cluster_node_summary = data.get("cluster_node_summary", {})

    site_tag = pcfg["site_tag"]
    bundle_label = pcfg["md_reference_bundle_label"]
    compare_path = pcfg["md_compare_bundle_path"]
    docs_label = pcfg["md_docs_label"]
    build_script = pcfg["build_script"]
    extract_note = pcfg["extract_note"]
    intro_bundle = pcfg["intro_bundle_label"]

    from collections import Counter

    lines: list[str] = []
    lines.append(f"# {site_tag} — RDS compliance (cluster-compare)\n")
    lines.append(
        f"**Reading order:** **Summary** → **RDS reference** → **Cluster information & OMC validation** → "
        f"**Required configurations** → **RDS deviation table** → **Mismatched configurations** → "
        f"**Missing configurations**. This must-gather is compared to the **{intro_bundle}** reference "
        f"(`kube-compare-reference`, OpenShift {ref['minor']}).\n"
    )

    lines.append("## OpenShift (must-gather)\n")
    lines.append(f"- **Version:** {md_cell(cv.get('version') or '')}")
    lines.append(f"- **Channel:** {md_cell(cv.get('channel') or '')}")
    lines.append(f"- **Reference bundle:** {md_cell(ref['minor'])} {bundle_label}")
    lines.append(f"- **Must-gather source:** {md_cell(mg_label)}\n")

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
        f"- **Compare bundle:** [`{compare_path}`]({ref['tree_kube_compare']})"
    )
    lines.append(f"- **metadata.yaml:** [View on GitHub]({ref['metadata_yaml']})")
    lines.append(
        f"- **{docs_label}:** [OpenShift {ref['minor']}]({ref['docs']})\n"
    )

    lines.append("## Cluster information & OMC validation\n")

    total = cluster_node_summary.get("total", 0)
    sno = cluster_node_summary.get("sno", False)
    lines.append(f"### Cluster topology ({total} node{'s' if total != 1 else ''}{' — SNO' if sno else ''})\n")
    lines.append(f"- **Masters:** {cluster_node_summary.get('masters', 0)}")
    lines.append(f"- **Workers:** {cluster_node_summary.get('workers', 0)}")
    lines.append(f"- **Infra:** {cluster_node_summary.get('infra', 0)}\n")
    if cluster_nodes:
        lines.append("| Node | Roles | Ready | CPU | Memory |")
        lines.append("| --- | --- | --- | --- | --- |")
        for n in cluster_nodes:
            roles = ", ".join(n["roles"]) if n["roles"] else "none"
            ready = "Ready" if str(n["ready"]) == "True" else "NotReady"
            lines.append(f"| {md_cell(n['name'][:48])} | {md_cell(roles)} | {ready} | {n.get('cpu', '')} | {md_cell(n.get('memory', ''))} |")
        lines.append("")
    else:
        lines.append("*No node data found in must-gather.*\n")

    lines.append("### OMC validation (must-gather)\n")
    if omc_text:
        lines.append("```text")
        lines.append(omc_text.rstrip())
        lines.append("```\n")
    elif omc_skip:
        lines.append(f"*{omc_skip}*\n")
    else:
        lines.append("*OMC validation not run.*\n")

    diffs = d.get("Diffs") or []
    c = Counter(x.get("CorrelatedTemplate", "") for x in diffs)

    lines.append("## Required configurations\n")
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
        lines.append("| — | *No correlated resources produced unified diff text.* | | |")
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
    if build_script:
        lines.append(f"*Regenerate: `{build_script}`. {extract_note}*\n")
    return "\n".join(lines)
