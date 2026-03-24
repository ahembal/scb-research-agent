# Local Deployment — Kind Cluster

Kind (Kubernetes in Docker) lets you run a full Kubernetes cluster locally
inside Docker containers. This is the recommended way to test the deployment
setup before going to a real cluster.

## Prerequisites

- Docker installed and running
- `.env` file with `ANTHROPIC_API_KEY` set
- Run from the repo root directory

## Step 1 — Set up the cluster

Run once per machine:
```bash
make kind-setup
```

This installs `kubectl` and `kind` if not present, then creates a cluster
named `research-agent` using `kind-config.yaml`.

## Step 2 — Deploy the app

Run after every code change:
```bash
make kind-deploy
```

This:
1. Builds the Docker image locally
2. Loads it into Kind (no registry needed)
3. Creates a Kubernetes Secret from your `.env` file
4. Applies all manifests via Kustomize
5. Waits for the pod to be ready

## Step 3 — Test the deployment

Health check:
```bash
curl http://localhost:8080/
```

Full assisted flow:
```bash
curl -s -X POST http://localhost:8080/session/start \
  -H "Content-Type: application/json" \
  -d '{"question": "What was the population of Stockholm county in 2024?"}' \
  | python3 -m json.tool
```

Interactive docs:
```
http://localhost:8080/docs
```

## Useful commands
```bash
make kind-status    # show pod and service status
make kind-logs      # stream pod logs
make kind-teardown  # delete the cluster
```

## How it works
```
Your laptop
    │
    │ localhost:8080
    ▼
Kind cluster (Docker container)
    │
    │ NodePort 30080
    ▼
research-agent Service
    │
    ▼
research-agent Pod
    │
    ├── reads config from ConfigMap
    └── reads API key from Kubernetes Secret
```

## Troubleshooting

**Pod is not starting:**
```bash
kubectl describe pod -l app=research-agent
```

**App returns errors:**
```bash
make kind-logs
```

**Port 8080 already in use:**
Edit `kind-config.yaml` and change `hostPort` to another port,
then update `scripts/kind/deploy.sh` accordingly.
