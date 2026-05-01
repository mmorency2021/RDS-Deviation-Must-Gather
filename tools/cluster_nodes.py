"""Parse node information from an extracted must-gather."""
from __future__ import annotations

from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


def load_cluster_nodes(extract_dir: Path) -> list[dict]:
    """Return a list of node dicts parsed from must-gather YAML files.

    Each dict contains: name, roles, ready, kubelet, os, arch, cpu, memory.
    """
    if yaml is None:
        return []

    nodes_dirs = sorted(extract_dir.rglob("cluster-scoped-resources/core/nodes"))
    if not nodes_dirs:
        return []

    nodes = []
    for nodes_dir in nodes_dirs:
        for yf in sorted(nodes_dir.glob("*.yaml")):
            try:
                doc = yaml.safe_load(yf.read_text())
            except Exception:
                continue
            if not isinstance(doc, dict):
                continue

            meta = doc.get("metadata", {})
            labels = meta.get("labels", {})
            roles = sorted(
                k.replace("node-role.kubernetes.io/", "")
                for k in labels
                if k.startswith("node-role.kubernetes.io/")
            )

            status = doc.get("status", {})
            conditions = {c["type"]: c["status"] for c in status.get("conditions", []) if "type" in c}
            ni = status.get("nodeInfo", {})
            cap = status.get("capacity", {})

            mem_ki = cap.get("memory", "")
            if isinstance(mem_ki, str) and mem_ki.endswith("Ki"):
                try:
                    mem_gi = f"{int(mem_ki[:-2]) / 1048576:.0f} Gi"
                except ValueError:
                    mem_gi = mem_ki
            else:
                mem_gi = str(mem_ki)

            nodes.append({
                "name": meta.get("name", yf.stem),
                "roles": roles,
                "ready": conditions.get("Ready", "Unknown"),
                "kubelet": ni.get("kubeletVersion", ""),
                "os": ni.get("osImage", ""),
                "arch": ni.get("architecture", ""),
                "cpu": cap.get("cpu", ""),
                "memory": mem_gi,
            })
        if nodes:
            break

    return nodes


def node_summary(nodes: list[dict]) -> dict:
    """Return a summary of the cluster topology."""
    masters = [n for n in nodes if "master" in n["roles"] or "control-plane" in n["roles"]]
    workers = [n for n in nodes if "worker" in n["roles"]]
    infra = [n for n in nodes if "infra" in n["roles"]]
    return {
        "total": len(nodes),
        "masters": len(masters),
        "workers": len(workers),
        "infra": len(infra),
        "sno": len(nodes) == 1,
    }
