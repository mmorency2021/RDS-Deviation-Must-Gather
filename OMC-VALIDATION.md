# Must-gather cross-check (omc)

**Tool:** [omc](https://github.com/gmeghnag/omc) v3.13.3 (OpenShift Must-gather Client). The `omg` command is not installed here; omc is the standard CLI to query extracted must-gather like `oc`.

## CU — `must-gather.local.3892438457315755728`

| Check | omc (`omc get clusterversion version`) | Report / MD (`cluster-compare-report.md`) |
|--------|----------------------------------------|-------------------------------------------|
| **Version** | 4.20.15 | 4.20.15 |
| **Channel** | eus-4.20 | eus-4.20 |

`omc use` resolved the same nested quay image path under `extracted/…/quay-io-openshift-release-dev-ocp-v4-0-art-dev-sha256-…` as the cluster-compare reports expect.

## DU — `must-gather.local.1112543954103552787`

| Check | omc | Report / MD |
|--------|-----|-------------|
| **Version** | 4.20.15 | 4.20.15 |
| **Channel** | stable-4.20 | stable-4.20 |

## cluster-compare JSON (sanity)

Values below are read directly from each site’s `cluster-compare-report.json` (plugin output, not omc).

| Site | `TotalCRs` | `NumMissing` | `NumDiffCRs` | `Diffs` array length |
|------|------------|--------------|--------------|----------------------|
| CU   | 42         | 37           | 20           | 42                   |
| DU   | 85         | 28           | 36           | 85                   |

`NumMissing` is the summary field from kube-compare; it does not equal the number of validation *sections* (nested groups differ).

## Re-run locally

Install or download [omc releases](https://github.com/gmeghnag/omc/releases), then:

```bash
REPO_ROOT=/path/to/RDS-Deviation-Must-Gather
MG_CU="$REPO_ROOT/CU/extracted/<your-vcu-must-gather-dir>"
MG_DU="$REPO_ROOT/DU/extracted/<your-vdu-must-gather-dir>"

omc use "$MG_CU"
omc get clusterversion version -o yaml

omc use "$MG_DU"
omc get clusterversion version -o yaml
```

Optional: `omc get nodes`, `omc get co`, etc., for deeper checks against the same archives used for cluster-compare.
