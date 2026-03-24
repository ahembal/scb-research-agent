#!/usr/bin/env bash
# scripts/kind/setup.sh
# Sets up the local Kind cluster for the research agent workshop.
# Run this once to prepare your machine. Safe to run again — idempotent.
#
# What this does:
#   1. Installs kubectl if not present
#   2. Installs Kind if not present
#   3. Creates the Kind cluster using deploy/kind/kind-config.yaml
#
# Requirements: Docker must be running.

set -euo pipefail

CLUSTER_NAME="research-agent"
KIND_VERSION="v0.22.0"
KUBECTL_VERSION="v1.29.0"

echo "==> Checking Docker..."
if ! docker info &>/dev/null; then
  echo "ERROR: Docker is not running. Please start Docker and try again."
  exit 1
fi

# ── Install kubectl ───────────────────────────────────────────────────────────

if ! command -v kubectl &>/dev/null; then
  echo "==> Installing kubectl ${KUBECTL_VERSION}..."
  curl -LO "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl"
  chmod +x kubectl
  sudo mv kubectl /usr/local/bin/kubectl
  echo "    kubectl installed."
else
  echo "==> kubectl already installed: $(kubectl version --client --short 2>/dev/null || kubectl version --client)"
fi

# ── Install Kind ──────────────────────────────────────────────────────────────

if ! command -v kind &>/dev/null; then
  echo "==> Installing Kind ${KIND_VERSION}..."
  curl -Lo ./kind "https://kind.sigs.k8s.io/dl/${KIND_VERSION}/kind-linux-amd64"
  chmod +x kind
  sudo mv kind /usr/local/bin/kind
  echo "    Kind installed."
else
  echo "==> Kind already installed: $(kind version)"
fi

# ── Create cluster ────────────────────────────────────────────────────────────

if kind get clusters | grep -q "^${CLUSTER_NAME}$"; then
  echo "==> Cluster '${CLUSTER_NAME}' already exists — skipping creation."
else
  echo "==> Creating Kind cluster '${CLUSTER_NAME}'..."
  kind create cluster \
    --name "${CLUSTER_NAME}" \
    --config deploy/kind/kind-config.yaml
  echo "    Cluster created."
fi

echo ""
echo "==> Setup complete."
echo "    Run 'make kind-deploy' to build and deploy the app."
