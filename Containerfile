FROM python:3.11-slim

ARG OCP_VERSION=4.20
ARG KUBECTL_VERSION=1.30.2
ARG OMC_VERSION=3.5.1

RUN apt-get update && apt-get install -y --no-install-recommends \
        git curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# kubectl
RUN curl -fsSL "https://dl.k8s.io/release/v${KUBECTL_VERSION}/bin/linux/amd64/kubectl" \
        -o /usr/local/bin/kubectl && \
    chmod +x /usr/local/bin/kubectl

# kubectl-cluster_compare plugin (kube-compare)
RUN curl -fsSL "https://github.com/openshift/kube-compare/releases/latest/download/kubectl-cluster_compare_linux_amd64.tar.gz" | \
    tar -xz -C /usr/local/bin && \
    chmod +x /usr/local/bin/kubectl-cluster_compare

# omc (OpenShift Must-gather Client)
RUN curl -fsSL "https://github.com/gmeghnag/omc/releases/download/v${OMC_VERSION}/omc_Linux_x86_64.tar.gz" | \
    tar -xz -C /usr/local/bin omc && \
    chmod +x /usr/local/bin/omc

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
VOLUME /app/.tmp
EXPOSE 5001

CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "2", "--threads", "4", "--timeout", "900", "webapp.app:create_app()"]
