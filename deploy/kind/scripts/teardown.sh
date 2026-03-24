#!/usr/bin/env bash
# scripts/kind/teardown.sh
# Removes the Kind cluster and all associated resources.
# Run this to clean up after a workshop session.
#
# This deletes everything in the cluster including the secret.
# Your .env file is not affected.

set -euo pipefail

CLUSTER_NAME="research-agent"

echo "==> Deleting Kind cluster '${CLUSTER_NAME}'..."

if kind get clusters | grep -q "^${CLUSTER_NAME}$"; then
  kind delete cluster --name "${CLUSTER_NAME}"
  echo "    Cluster deleted."
else
  echo "    Cluster '${CLUSTER_NAME}' not found — nothing to do."
fi

echo ""
echo "==> Teardown complete."
echo "    To recreate the cluster run: scripts/kind/setup.sh"
