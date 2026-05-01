#!/usr/bin/env python3
"""Entry point for the RDS compliance web application."""
from tools.kube_compare_setup import ensure_cluster_compare

ensure_cluster_compare()

from webapp.app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
