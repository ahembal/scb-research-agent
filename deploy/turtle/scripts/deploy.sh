#!/usr/bin/env bash
# deploy/turtle/scripts/deploy.sh
# Deploys the research agent to the Turtle homelab Kubernetes cluster.
#
# What this does:
#   1. Checks prerequisites (.env, kubectl connectivity)
#   2. Creates the workshop namespace if it does not exist
#   3. Builds and pushes the Docker image to Docker Hub
#   4. Creates the Kubernetes Secret in the workshop namespace
#   5. Applies all manifests via Kustomize
#   6. Waits for the deployment to be ready

set -euo pipefail

IMAGE_NAME="ahembal/scb-research-agent:latest"
NAMESPACE="workshop"

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

# ── Create namespace if it does not exist ─────────────────────────────────────

if ! kubectl get namespace "${NAMESPACE}" &>/dev/null; then
  echo "==> Creating namespace '${NAMESPACE}'..."
  kubectl create namespace "${NAMESPACE}"
  kubectl label namespace "${NAMESPACE}" \
    pod-security.kubernetes.io/enforce=baseline \
    pod-security.kubernetes.io/enforce-version=latest
  echo "    Namespace created and labelled."
else
  echo "==> Namespace '${NAMESPACE}' already exists."
fi

# ── Build and push image ──────────────────────────────────────────────────────

echo "==> Building Docker image '${IMAGE_NAME}'..."
docker build -t "${IMAGE_NAME}" .
echo "    Image built."

echo "==> Pushing image to Docker Hub..."
docker push "${IMAGE_NAME}"
echo "    Image pushed."

# ── Create Kubernetes Secret ──────────────────────────────────────────────────

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
echo "    API is available at: http://192.168.1.16:31000"
echo "    Interactive docs:    http://192.168.1.16:31000/docs"
echo ""
echo "    To watch pod status: kubectl get pods -n ${NAMESPACE} -w"
echo "    To view logs:        kubectl logs -l app=research-agent -n ${NAMESPACE} -f"
