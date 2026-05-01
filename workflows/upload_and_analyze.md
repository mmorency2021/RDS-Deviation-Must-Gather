# Upload and Analyse Must-Gather (Web Flow)

## Objective

Accept an OpenShift must-gather archive via the web UI, run RDS compliance analysis against the telco-reference bundle, and produce HTML + Markdown dashboards.

## Required Inputs

- Must-gather archive (`.tar.gz`, `.tgz`, or `.tar`) — max 500 MB
- Profile selection: **RAN** (vDU), **CORE**, or **HUB**

## Pipeline Steps

1. **Extract archive** — `tools/mustgather.extract_tarball()` with path traversal protection
2. **Discover payload** — `tools/mustgather.find_payload_root()` prefers `quay-io-*` directories
3. **Detect cluster version** — `tools/cluster_version.load_cluster_version()` finds and parses `clusterversions/version.yaml`
4. **Fetch reference bundle** — `tools/reference_repo.ensure_reference()` clones `openshift-kni/telco-reference` at branch `release-{minor}` into `.tmp/reference-cache/`
5. **Run kube-compare** — `tools/kube_compare.run_cluster_compare()` executes `kubectl cluster_compare` with profile-specific `metadata.yaml`, outputs JSON + YAML
6. **Run OMC validation** — `tools/omc_runner.capture_omc_validation()` runs `omc use` + `omc get clusterversion` (best-effort, skipped if omc is unavailable)
7. **Build dashboard** — `tools/dashboard_core.prepare_dashboard_data()` → `tools/html_renderer.render_html_dashboard()` + `tools/md_renderer.render_cluster_compare_markdown()`

## Expected Outputs

- `dashboard.html` — self-contained HTML dashboard (dark/light mode, search, filters)
- `report.md` — Markdown compliance report
- `cluster-compare-report.json` — raw kube-compare JSON output
- `cluster-compare-report.yaml` — raw kube-compare YAML output

All outputs are stored in `.tmp/jobs/<job-id>/`.

## Edge Cases

- **Missing cluster version**: defaults to `4.20` and proceeds
- **Branch not found on remote**: pipeline errors with clear message asking user to verify the branch exists
- **omc not installed**: OMC validation is skipped; dashboard shows "OMC validation not run"
- **kubectl / cluster_compare not found**: pipeline errors immediately with install instructions
- **Empty or malformed archive**: errors at extraction step with descriptive message
- **No quay-io-* directory**: falls back to first subdirectory in extracted archive

## How to Run

**Local development:**
```bash
pip install -r requirements.txt
python run.py
# Open http://localhost:5001
```

**Container:**
```bash
podman build -t rds-webapp .
podman run -p 5001:5001 rds-webapp
```
