#!/usr/bin/env bash
# deploy/turtle/scripts/deploy.sh
# Deploys the research agent to the Turtle homelab Kubernetes cluster.
#
# What this does:
#   1. Checks prerequisites (.env, kubectl connectivity)
#   2. Builds and pushes the Docker image to Docker Hub
#   3. Creates the Kubernetes Secret in the workshop namespace
#   4. Applies all manifests via Kustomize
#   5. Waits for the deployment to be ready
#
# Requirements:
#   - kubectl configured to point at Turtle (or run on clever-fly)
#   - .env file with ANTHROPIC_API_KEY set
#   - Docker Hub login (docker login)
#   - workshop namespace exists with baseline pod security label

set -euo pipefail

IMAGE_NAME="ahembal/scb-research-agent:latest"
NAMESPACE="workshop"
KUBECONFIG_PATH="${KUBECONFIG:-$HOME/.kube/config}"

# ── Preflight checks ──────────────────────────────────────────────────────────

echo "==> Checking .env file..."
if [ ! -f .env ]; then
  echo "ERROR: .env file not found."
  echo "       Copy .env.example to .env and fill in your ANTHROPIC_API_KEY."
  exit 1
fi

set -a && source .env && set +a

if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  echo "ERROR: ANTHROPIC_API_KEY is not set in .env."
  exit 1
fi

echo "==> Checking kubectl connectivity to Turtle..."
if ! kubectl get nodes &>/dev/null; then
  echo "ERROR: kubectl cannot reach the cluster."
  echo "       Check your kubeconfig or run this script on clever-fly directly."
  exit 1
fi

echo "==> Checking workshop namespace..."
if ! kubectl get namespace "${NAMESPACE}" &>/dev/null; then
  echo "ERROR: Namespace '${NAMESPACE}' does not exist."
  echo "       Run: kubectl create namespace ${NAMESPACE}"
  exit 1
fi

# ── Build and push image ──────────────────────────────────────────────────────

# Unlike Kind, Turtle pulls from Docker Hub — image must be pushed first
echo "==> Building Docker image '${IMAGE_NAME}'..."
docker build -t "${IMAGE_NAME}" .
echo "    Image built."

echo "==> Pushing image to Docker Hub..."
docker push "${IMAGE_NAME}"
echo "    Image pushed."

# ── Create Kubernetes Secret ──────────────────────────────────────────────────

# Created imperatively so the API key is never written to a file or git
echo "==> Creating Kubernetes secret in namespace '${NAMESPACE}'..."
kubectl create secret generic research-agent-secret \
  --from-literal=ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY}" \
  --namespace="${NAMESPACE}" \
  --dry-run=client -o yaml | kubectl apply -f -
echo "    Secret applied."

# ── Apply manifests ───────────────────────────────────────────────────────────

echo "==> Applying Kubernetes manifests..."
kubectl apply -k deploy/turtle/manifests
echo "    Manifests applied."

# ── Wait for rollout ──────────────────────────────────────────────────────────

echo "==> Waiting for deployment to be ready..."
kubectl rollout status deployment/research-agent \
  --namespace="${NAMESPACE}" \
  --timeout=120s
echo "    Deployment ready."

# ── Done ──────────────────────────────────────────────────────────────────────

echo ""
echo "==> Deploy complete."
echo "    API is available at: http://research-agent.turtle.local:32080"
echo "    Interactive docs:    http://research-agent.turtle.local:32080/docs"
echo ""
echo "    To watch pod status: kubectl get pods -n ${NAMESPACE} -w"
echo "    To view logs:        kubectl logs -l app=research-agent -n ${NAMESPACE} -f"
