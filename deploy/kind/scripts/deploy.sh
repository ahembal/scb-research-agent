#!/usr/bin/env bash
# scripts/kind/deploy.sh
# Builds the Docker image and deploys it to the local Kind cluster.
# Run this after any code change to redeploy.
#
# What this does:
#   1. Checks the cluster is running
#   2. Builds the Docker image locally
#   3. Loads the image into Kind (no registry needed)
#   4. Creates the Kubernetes Secret from your .env file
#   5. Applies all manifests via Kustomize
#   6. Waits for the deployment to be ready
#
# Requirements:
#   - Kind cluster must be running (run scripts/kind/setup.sh first)
#   - .env file must exist with ANTHROPIC_API_KEY set

set -euo pipefail

CLUSTER_NAME="research-agent"
IMAGE_NAME="research-agent:latest"
NAMESPACE="default"

# ── Preflight checks ──────────────────────────────────────────────────────────

echo "==> Checking cluster..."
if ! kind get clusters | grep -q "^${CLUSTER_NAME}$"; then
  echo "ERROR: Kind cluster '${CLUSTER_NAME}' not found."
  echo "       Run scripts/kind/setup.sh first."
  exit 1
fi

echo "==> Checking .env file..."
if [ ! -f .env ]; then
  echo "ERROR: .env file not found."
  echo "       Copy .env.example to .env and fill in your ANTHROPIC_API_KEY."
  exit 1
fi

# Load .env to read ANTHROPIC_API_KEY
set -a && source .env && set +a

if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  echo "ERROR: ANTHROPIC_API_KEY is not set in .env."
  exit 1
fi

# ── Build image ───────────────────────────────────────────────────────────────

echo "==> Building Docker image '${IMAGE_NAME}'..."
docker build -t "${IMAGE_NAME}" .
echo "    Image built."

# ── Load image into Kind ──────────────────────────────────────────────────────

# Kind runs its own container runtime — images must be explicitly loaded
# into the cluster. They are not automatically available from Docker.
echo "==> Loading image into Kind cluster..."
kind load docker-image "${IMAGE_NAME}" --name "${CLUSTER_NAME}"
echo "    Image loaded."

# ── Create Kubernetes Secret ──────────────────────────────────────────────────

# The secret is created imperatively (not from a file) so the API key
# is never written to disk or committed to git.
echo "==> Creating Kubernetes secret..."
kubectl create secret generic research-agent-secret \
  --from-literal=ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY}" \
  --dry-run=client -o yaml | kubectl apply -f -
echo "    Secret applied."

# ── Apply manifests ───────────────────────────────────────────────────────────

echo "==> Applying Kubernetes manifests..."
kubectl apply -k deploy/kind/manifests
echo "    Manifests applied."

# ── Wait for rollout ──────────────────────────────────────────────────────────

echo "==> Waiting for deployment to be ready..."
kubectl rollout status deployment/research-agent --timeout=120s
echo "    Deployment ready."

# ── Done ──────────────────────────────────────────────────────────────────────

echo ""
echo "==> Deploy complete."
echo "    API is available at: http://localhost:8080"
echo "    Interactive docs:    http://localhost:8080/docs"
echo ""
echo "    To watch pod status: kubectl get pods -w"
echo "    To view logs:        kubectl logs -l app=research-agent -f"
