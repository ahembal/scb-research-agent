#!/usr/bin/env bash
# deploy/turtle/scripts/teardown.sh
# Removes the research agent from the Turtle cluster.
# Does NOT delete the workshop namespace or the nginx Ingress controller
# as other workloads may use them.

set -euo pipefail

NAMESPACE="workshop"

echo "==> Removing research agent manifests..."
kubectl delete -k deploy/turtle/manifests --ignore-not-found
echo "    Manifests removed."

echo "==> Removing Kubernetes secret..."
kubectl delete secret research-agent-secret \
  --namespace="${NAMESPACE}" \
  --ignore-not-found
echo "    Secret removed."

echo ""
echo "==> Teardown complete."
echo "    Namespace '${NAMESPACE}' and nginx Ingress were left intact."
