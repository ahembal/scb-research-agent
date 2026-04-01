# Turtle Homelab Deployment

Deploys the research agent to the Turtle homelab Kubernetes cluster.

## Infrastructure

| Node | IP | Role |
|---|---|---|
| clever-fly | 192.168.1.184 | Kubernetes control-plane |
| sought-perch | 192.168.1.16 | Kubernetes worker |
| quick-thrush | 192.168.1.200 | Kubernetes worker |

CNI: Flannel
Ingress: nginx (NodePort 32080/32443)
Namespace: workshop (baseline pod security)
Image: ahembal/scb-research-agent:latest (Docker Hub)

## Prerequisites

- kubectl configured to point at Turtle, or run from clever-fly
- Docker Hub login: `docker login`
- `.env` file with `ANTHROPIC_API_KEY` set
- `research-agent.turtle.local` in your `/etc/hosts`:
```
  192.168.1.16  research-agent.turtle.local
```

## Deploy
```bash
make turtle-deploy
```

This builds the image, pushes to Docker Hub, creates the Kubernetes
Secret, and applies all manifests via Kustomize.

## Test the deployment

Health check:
```bash
curl http://research-agent.turtle.local:32080/
```

Full assisted flow:
```bash
curl -s -X POST http://research-agent.turtle.local:32080/session/start \
  -H "Content-Type: application/json" \
  -d '{"question": "What was the population of Stockholm county in 2024?"}' \
  | python3 -m json.tool
```

Interactive docs:
```
http://research-agent.turtle.local:32080/docs
```

## Useful commands
```bash
make turtle-status      # show pods, services, ingress
make turtle-logs        # stream pod logs
make turtle-teardown    # remove from cluster
```

## How it works
```
Your laptop
    │
    │ http://research-agent.turtle.local:32080
    ▼
sought-perch (192.168.1.16) or quick-thrush (192.168.1.200)
    │
    │ NodePort 32080
    ▼
nginx Ingress controller (ingress-nginx namespace)
    │
    │ routes research-agent.turtle.local → research-agent service
    ▼
research-agent Service (workshop namespace)
    │
    ▼
research-agent Pod
    ├── reads config from ConfigMap
    └── reads API key from Kubernetes Secret
```

## Troubleshooting

**Pod not starting:**
```bash
kubectl describe pod -l app=research-agent -n workshop
```

**Ingress not routing:**
```bash
kubectl describe ingress research-agent -n workshop
kubectl get svc -n ingress-nginx
```

**App returning errors:**
```bash
make turtle-logs
```
