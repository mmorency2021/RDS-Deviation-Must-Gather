"""Extract must-gather .tar.gz archives and locate the payload directory."""
from __future__ import annotations

import tarfile
from pathlib import Path


def extract_tarball(tar_path: Path, dest: Path) -> Path:
    """Extract a ``.tar.gz`` / ``.tgz`` / ``.tar`` archive into *dest*.

    Returns *dest* after extraction.  Raises on path-traversal attempts.
    """
    dest.mkdir(parents=True, exist_ok=True)
    mode = "r:gz" if tar_path.name.endswith((".tar.gz", ".tgz")) else "r:*"
    with tarfile.open(tar_path, mode) as tf:
        for member in tf.getmembers():
            resolved = (dest / member.name).resolve()
            if not str(resolved).startswith(str(dest.resolve())):
                raise ValueError(f"Path traversal detected in archive member: {member.name}")
        if hasattr(tarfile, "data_filter"):
            tf.extractall(dest, filter="data")
        else:
            tf.extractall(dest)
    return dest


def find_payload_root(extract_dir: Path) -> Path | None:
    """Locate the must-gather payload root inside *extract_dir*.

    Prefers directories matching ``quay-io-*`` (the image-pull naming
    convention), otherwise falls back to the first subdirectory.
    """
    quay_dirs = sorted(extract_dir.rglob("quay-io-*"))
    quay_dirs = [p for p in quay_dirs if p.is_dir()]
    if quay_dirs:
        return quay_dirs[0]
    subs = sorted([p for p in extract_dir.iterdir() if p.is_dir()])
    return subs[0] if subs else None


def find_compare_inputs(payload_root: Path) -> list[Path]:
    """Return the ``-f`` arguments for ``kubectl cluster_compare``.

    If both ``cluster-scoped-resources/`` and ``namespaces/`` exist under
    *payload_root*, return those two paths (matching the upstream examples).
    Otherwise return ``[payload_root]``.
    """
    csr = payload_root / "cluster-scoped-resources"
    ns = payload_root / "namespaces"
    if csr.is_dir() and ns.is_dir():
        return [csr, ns]
    return [payload_root]
