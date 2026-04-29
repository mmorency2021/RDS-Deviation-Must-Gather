#!/usr/bin/env bash
#
# RDS-Deviation-Must-Gather — end-to-end flow for **CU (vCU)** and **DU (vDU)**:
#
#   CU — OpenShift must-gather for the centralized unit; outputs under ./CU/
#   DU — OpenShift must-gather for the DU site; outputs under ./DU/
#
# Steps per site:
#   1) Extract must-gather into CU/extracted/ or DU/extracted/ (CU archive may be plain tar: tar -xf …)
#   2) cluster-compare against **telco-reference release-4.20** kube-compare bundle (local metadata.yaml)
#   3) python3 build-cu-dashboard.py | build-du-dashboard.py → detailed HTML + cluster-compare-report.md (+ OMC block if omc exists)
#
# Reference checked out beside DU material:
#   DU/telco-reference-release-4.20/telco-ran/configuration/kube-compare-reference/metadata.yaml
#
# If bundled oc/kubectl cluster_compare is too old (missing lookupCRs), use upstream kube-compare v0.12+ binary:
#   export CLUSTER_COMPARE_BIN=/tmp/kubectl-cluster_compare   # example
#
# Usage:
#   ./run-cluster-compare-pipeline.sh cu|du|all
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${1:-all}"

# Default: telco-reference bundle next to DU material in this tree
DEFAULT_REF="${ROOT}/DU/telco-reference-release-4.20/telco-ran/configuration/kube-compare-reference/metadata.yaml"
REFERENCE_METADATA="${REFERENCE_METADATA:-$DEFAULT_REF}"

usage() {
  echo "Usage: $0 <cu|du|all>" >&2
  echo "Environment:" >&2
  echo "  REFERENCE_METADATA  Path to metadata.yaml (default: DU/.../kube-compare-reference/metadata.yaml)" >&2
  echo "  CLUSTER_COMPARE_BIN If set, run this binary instead of 'kubectl cluster_compare'" >&2
  echo "  OMC_PATH            Optional; passed through for dashboard OMC section" >&2
  exit 1
}

[[ "$TARGET" == "-h" || "$TARGET" == "--help" ]] && usage
case "$TARGET" in
  cu|du|all) ;;
  *) usage ;;
esac

if [[ ! -f "$REFERENCE_METADATA" ]]; then
  echo "ERROR: Reference metadata not found: $REFERENCE_METADATA" >&2
  echo "Set REFERENCE_METADATA to your telco-reference .../kube-compare-reference/metadata.yaml" >&2
  exit 1
fi

run_kube_compare() {
  local site_dir="$1"
  local extract="${site_dir}/extracted"
  local out_json="${site_dir}/cluster-compare-report.json"
  local out_yaml="${site_dir}/cluster-compare-report.yaml"
  local errlog="${site_dir}/cluster-compare-stderr.log"

  if [[ ! -d "$extract" ]] || ! find "$extract" -mindepth 1 -maxdepth 1 -type d | grep -q .; then
    echo "ERROR: No must-gather under $extract — extract an archive there first." >&2
    return 1
  fi

  # kube-compare expects the inner payload dir that holds YAML (typically …/quay-io-*-sha256-…), not extracted/ alone.
  local mg_input
  mg_input="$(find "$extract" -type d -name 'quay-io-*' 2>/dev/null | sort | head -1)"
  if [[ -z "$mg_input" ]]; then
    mg_input="$(find "$extract" -mindepth 1 -maxdepth 1 -type d | sort | head -1)"
  fi
  if [[ -z "$mg_input" || ! -d "$mg_input" ]]; then
    echo "ERROR: Could not resolve must-gather input under $extract (look for quay-io-* or a subdir)." >&2
    return 1
  fi
  local nq
  nq="$(find "$extract" -type d -name 'quay-io-*' 2>/dev/null | wc -l | tr -d ' ')"
  if [[ "${nq:-0}" -gt 1 ]]; then
    echo "NOTE: multiple quay-io-* dirs — using: $mg_input" >&2
  fi

  # OpenShift must-gather stores Kubernetes resources under cluster-scoped-resources/ and namespaces/.
  # Passing only the quay-io-* root without -R reads almost nothing at depth 1; passing the whole tree with -R
  # fails on non-resource JSON (etcd_info, etc.). Match upstream kube-compare examples:
  #   -f .../cluster-scoped-resources -f .../namespaces -R
  local -a cc_cmd
  cc_cmd=(-r "$REFERENCE_METADATA")
  if [[ -d "$mg_input/cluster-scoped-resources" && -d "$mg_input/namespaces" ]]; then
    cc_cmd+=(-f "$mg_input/cluster-scoped-resources" -f "$mg_input/namespaces" -R)
    echo "==> [$site_dir] cluster-compare → ${out_json##*/}"
    echo "    input (-f): $mg_input/cluster-scoped-resources + $mg_input/namespaces (-R)"
  else
    cc_cmd+=(-f "$mg_input")
    echo "==> [$site_dir] cluster-compare → ${out_json##*/}"
    echo "    WARN: missing cluster-scoped-resources/ or namespaces/ under payload — using (-f): $mg_input" >&2
    echo "    input (-f): $mg_input"
  fi

  if [[ -n "${CLUSTER_COMPARE_BIN:-}" ]]; then
    if [[ ! -x "$CLUSTER_COMPARE_BIN" ]]; then
      echo "ERROR: CLUSTER_COMPARE_BIN is not executable: $CLUSTER_COMPARE_BIN" >&2
      return 1
    fi
    set +e
    "$CLUSTER_COMPARE_BIN" "${cc_cmd[@]}" -o json >"$out_json" 2>"$errlog"
    rc=$?
    "$CLUSTER_COMPARE_BIN" "${cc_cmd[@]}" -o yaml >"$out_yaml" 2>>"$errlog"
    set -e
  else
    if ! command -v kubectl >/dev/null 2>&1; then
      echo "ERROR: kubectl not in PATH. Install kubectl and the cluster_compare plugin, or set CLUSTER_COMPARE_BIN." >&2
      return 1
    fi
    set +e
    kubectl cluster_compare "${cc_cmd[@]}" -o json >"$out_json" 2>"$errlog"
    rc=$?
    kubectl cluster_compare "${cc_cmd[@]}" -o yaml >"$out_yaml" 2>>"$errlog"
    set -e
  fi

  if [[ "$rc" != 0 ]]; then
    echo "WARN: cluster-compare exited $rc (see $errlog). JSON may still be usable." >&2
  fi
  echo "    wrote $(wc -c <"$out_json") bytes json, $(wc -c <"$out_yaml") bytes yaml"
}

run_dashboards() {
  local site_dir="$1"
  local short
  short="$(basename "$site_dir")"
  local slug="${short,,}"
  local py="${site_dir}/build-${slug}-dashboard.py"
  if [[ ! -f "$py" ]]; then
    echo "ERROR: Dashboard builder not found: $py" >&2
    return 1
  fi
  echo "==> [$site_dir] dashboards (HTML + MD)"
  (cd "$site_dir" && python3 "$(basename "$py")")
}

run_site() {
  local short="$1"
  local dir="${ROOT}/${short}"
  run_kube_compare "$dir"
  run_dashboards "$dir"
}

case "$TARGET" in
  cu) run_site CU ;;
  du) run_site DU ;;
  all)
    run_site CU
    run_site DU
    ;;
esac

echo ""
echo "Done. Open:"
echo "  file://${ROOT}/CU/cluster-compare-dashboard-detailed.html"
echo "  file://${ROOT}/CU/vCU-RDS-compliance-dashboard.html"
echo "  file://${ROOT}/DU/cluster-compare-dashboard-detailed.html"
echo "  file://${ROOT}/DU/vDU-RDS-compliance-dashboard.html"
