# RDS-Deviation-Must-Gather

OpenShift **must-gather** analysis for **RDS (RAN DU / CU) deviation** reporting: **kube-compare** (`cluster_compare`) against the telco-reference bundle, plus HTML/Markdown dashboards and optional **OMC** validation.

Originally developed as the RAN Gather cluster-compare dashboard workflow (vCU / vDU).

This workspace builds **RDS compliance HTML and Markdown reports** from OpenShift **must-gather** using **`kubectl cluster_compare`** (kube-compare) against the **telco-reference** `kube-compare-reference` bundle.

| Site | Folder | Tag | Dashboard builders |
|------|--------|-----|---------------------|
| Central unit (CU) | `CU/` | **vCU** | `CU/build-cu-dashboard.py` |
| Distributed unit (DU) | `DU/` | **vDU** | `DU/build-du-dashboard.py` |

The main automation entrypoint is **`run-cluster-compare-pipeline.sh`**: it runs cluster-compare, then the Python dashboard for each site you select.

---

## Prerequisites

1. **Kubernetes compare tool** — one of:
   - `kubectl` with the **`cluster_compare`** plugin, or
   - A standalone kube-compare binary (e.g. v0.12+ if your plugin lacks features such as `lookupCRs`):

     ```bash
     export CLUSTER_COMPARE_BIN=/path/to/kubectl-cluster_compare
     ```

2. **Python 3** with **PyYAML** (for reading ClusterVersion from must-gather):

   ```bash
   pip install pyyaml
   ```

3. **Optional — OMC** (OpenShift Must-gather Client): if `omc` is on `PATH` or **`OMC_PATH`** is set, the dashboards embed an **OMC validation** section against `extracted/`.

---

## Reference bundle (`metadata.yaml`)

The pipeline compares your must-gather to a **telco-reference** kube-compare bundle.

**Default** (relative to this repo):

```text
DU/telco-reference-release-4.20/telco-ran/configuration/kube-compare-reference/metadata.yaml
```

Override when needed:

```bash
export REFERENCE_METADATA=/absolute/path/to/kube-compare-reference/metadata.yaml
```

If this file is missing, the pipeline exits with an error before running compare.

---

## Step-by-step procedure

### 1. Extract must-gather

Each site keeps its own extract under **`CU/extracted/`** or **`DU/extracted/`**.

```bash
# Example: from repository root
mkdir -p CU/extracted DU/extracted

# Unpack your archives (adjust format/path to your files)
tar -xf /path/to/must-gather-vcu.tar -C CU/extracted
tar -xf /path/to/must-gather-du.tar  -C DU/extracted
```

You should have at least **one subdirectory** under `extracted/` (often a **`quay-io-*`** tree). Under that payload, OpenShift must-gather normally includes **`cluster-scoped-resources/`** and **`namespaces/`**. The pipeline uses those paths with **recursive** compare so nested CR YAML is included.

---

### 2. Run the pipeline

From the **repository root** (`RDS-Deviation-Must-Gather`):

```bash
chmod +x run-cluster-compare-pipeline.sh   # once, if needed

./run-cluster-compare-pipeline.sh cu    # vCU only (CU/)
./run-cluster-compare-pipeline.sh du    # vDU only (DU/)
./run-cluster-compare-pipeline.sh all   # both CU and DU
```

**What it does for each selected site** (`CU/` or `DU/`):

1. **Resolves** must-gather under `extracted/` (prefers a `quay-io-*` directory).
2. **Runs cluster-compare** with `-r "$REFERENCE_METADATA"` and:
   - If `cluster-scoped-resources` and `namespaces` exist under the payload:  
     `-f .../cluster-scoped-resources -f .../namespaces -R`
   - Otherwise: falls back to `-f <payload-root>` (with a warning).
3. **Writes** in that site folder:
   - `cluster-compare-report.json`
   - `cluster-compare-report.yaml`
   - `cluster-compare-stderr.log` (stderr from the compare tool)
4. **Runs** `python3 build-cu-dashboard.py` or `python3 build-du-dashboard.py` in that folder.

A non-zero cluster-compare exit code **may still produce usable JSON**; check `cluster-compare-stderr.log` if you see warnings.

---

### 3. Outputs (what to open)

Artifacts are written **inside `CU/` or `DU/`**.

#### CU (vCU)

| File | Description |
|------|-------------|
| `cluster-compare-report.json` | Source data for the dashboard (counts, diffs, validation). |
| `cluster-compare-report.yaml` | Same report in YAML. |
| `cluster-compare-dashboard-detailed.html` | Full interactive dashboard. |
| `vCU-RDS-compliance-dashboard.html` | Same HTML as above; **vCU-tagged** filename for sharing. |
| `cluster-compare-report.md` | Markdown report aligned with the HTML sections. |

#### DU (vDU)

| File | Description |
|------|-------------|
| `cluster-compare-report.json` | Source data for the dashboard. |
| `cluster-compare-report.yaml` | Same report in YAML. |
| `cluster-compare-dashboard-detailed.html` | Full interactive dashboard. |
| `vDU-RDS-compliance-dashboard.html` | Same HTML as above; **vDU-tagged** filename for sharing. |
| `cluster-compare-report.md` | Markdown report aligned with the HTML sections. |

Open locally with your browser, for example:

```text
file:///path/to/RDS-Deviation-Must-Gather/CU/vCU-RDS-compliance-dashboard.html
file:///path/to/RDS-Deviation-Must-Gather/DU/vDU-RDS-compliance-dashboard.html
```

---

## Manual run (without the shell pipeline)

If you already have **`cluster-compare-report.json`** in the right place:

```bash
cd CU && python3 build-cu-dashboard.py
cd DU && python3 build-du-dashboard.py
```

To produce JSON yourself, mirror the **`run_kube_compare`** logic in `run-cluster-compare-pipeline.sh`: same `-r metadata.yaml` and **`-f cluster-scoped-resources -f namespaces -R`** when those directories exist under the must-gather payload.

---

## Environment variables

| Variable | Purpose |
|----------|---------|
| `REFERENCE_METADATA` | Path to `kube-compare-reference/metadata.yaml` (defaults to the path under `DU/telco-reference-release-4.20/...`). |
| `CLUSTER_COMPARE_BIN` | If set, this executable is used instead of `kubectl cluster_compare`. |
| `OMC_PATH` | Optional path to the `omc` binary for the OMC section in dashboards. |

---

## Refresh after new data

1. Update or replace **`CU/extracted/`** and/or **`DU/extracted/`** with the new must-gather.
2. Run **`./run-cluster-compare-pipeline.sh cu`**, **`du`**, or **`all`** again.
3. Re-open the HTML files listed above.

---

## Troubleshooting

| Problem | What to check |
|--------|----------------|
| Compare JSON looks empty or CR counts are far too low | Ensure compare uses **`cluster-scoped-resources`** + **`namespaces`** with **`-R`** as in the pipeline; pointing only at the top of `quay-io-*` without walking namespaces often yields almost no YAML. |
| `cluster-compare` exits non-zero | Read **`cluster-compare-stderr.log`**; JSON may still be valid. |
| Plugin too old / missing features | Set **`CLUSTER_COMPARE_BIN`** to a newer **`kubectl-cluster_compare`**. |
| No OMC block in HTML | Install **`omc`** or set **`OMC_PATH`**; ensure **`extracted/`** contains a valid must-gather layout. |
| PyYAML errors | `pip install pyyaml`. |

---

## Script reference

| Script | Role |
|--------|------|
| `run-cluster-compare-pipeline.sh` | End-to-end: cluster-compare → `cluster-compare-report.json` → dashboard HTML + MD for **CU** and/or **DU**. |
| `CU/build-cu-dashboard.py` | Reads `CU/cluster-compare-report.json`, writes HTML + MD (**vCU** branded copy). |
| `DU/build-du-dashboard.py` | Reads `DU/cluster-compare-report.json`, writes HTML + MD (**vDU** branded copy). |

---

## Quick command cheat sheet

```bash
cd /path/to/RDS-Deviation-Must-Gather

# Full flow for both sites
./run-cluster-compare-pipeline.sh all

# Optional overrides
export REFERENCE_METADATA=/path/to/metadata.yaml
export CLUSTER_COMPARE_BIN=/path/to/kubectl-cluster_compare
./run-cluster-compare-pipeline.sh du
```
