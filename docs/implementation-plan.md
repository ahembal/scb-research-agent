# Implementation Plan

*Last updated: 2026-03-29*

This document reflects the current state of the project and what is genuinely next.
It supersedes the original three-phase plan which was written before the workshop.

---

## Design Principles (established during workshop)

- **Assisted AI, not autonomous AI** — the agent ranks and explains, the human decides
- **Session-based pipeline** — three explicit steps, nothing happens between them automatically
- **Grounded answers only** — every answer comes from live SCB data, never from LLM knowledge
- **Transparent sources** — every response includes the source table, exact selection, and raw values

---

## Current State

### Core Agent — Done
| Module | Status | Notes |
|---|---|---|
| `config.py` | ✅ | Anthropic + SCB + session config via env vars |
| `models.py` | ✅ | SessionState, TableCandidate, Dimension, DimensionSuggestion |
| `schema.py` | ✅ | Full session + exploration HTTP schemas |
| `prompts.py` | ✅ | table_ranking, dimension_suggestion, answer_generation, keyword_extraction |
| `agent.py` | ✅ | Three-step assisted pipeline: start_session, select_table, confirm_query |
| `session_store.py` | ✅ | In-memory session store with TTL expiry |
| `scb_metadata.py` | ✅ | search_tables, get_table_metadata |
| `metadata_parser.py` | ✅ | Parses SCB dimension structures |
| `scb_query_builder.py` | ✅ | Builds PxWebApi v2 query payloads |
| `result_parser.py` | ✅ | Maps dimension codes to human-readable labels |
| `main.py` | ✅ | Session endpoints + direct exploration endpoints |

### Tests — Done
| File | Status | Notes |
|---|---|---|
| `tests/test_scb_api.py` | ✅ | Integration tests against real SCB API |
| `tests/test_agent_flow.py` | ✅ | Pipeline tests with mocked LLM and SCB |
| `tests/test_session_store.py` | ✅ | Session lifecycle unit tests |
| `tests/test_api_endpoints.py` | ✅ | HTTP layer tests with FastAPI TestClient |

### Infrastructure — Partially Done
| Item | Status | Notes |
|---|---|---|
| `Dockerfile` | ✅ | Non-root user, healthcheck, correct build order |
| `deploy/base/` | ✅ | Configmap, Deployment, Service, Kustomization |
| `deploy/kind/` | ✅ | Cluster config, manifests, scripts — tested end to end |
| `deploy/turtle/` | 🔄 | In progress — nginx Ingress being set up |
| `deploy/k8s/` | ⏳ | Pending — generic cloud overlay |
| Docker Hub image | ✅ | ahembal/scb-research-agent:latest |

### Documentation — Mostly Done
| File | Status | Notes |
|---|---|---|
| `docs/01-overview.md` | ✅ | Architecture, design principle, component table |
| `docs/02-scb-data.md` | ✅ | SCB API, known limitations (Swedish characters) |
| `docs/03-agent-flow.md` | ✅ | Sequence diagram, assisted flow |
| `docs/04-session-model.md` | ✅ | API contract, session lifecycle |
| `docs/05-api-usage.md` | ✅ | curl examples for all endpoints |
| `docs/06-prerequisites.md` | ✅ | API key, billing, Docker Hub image |
| `docs/deployment/kind.md` | ✅ | Full Kind walkthrough |
| `docs/deployment/turtle.md` | ⏳ | Pending Phase 7 |
| `docs/deployment/k8s.md` | ⏳ | Pending Phase 7 |
| `docs/implementation-plan.md` | ✅ | This file |

---

## Known Issues & Limitations

| Issue | Severity | Notes |
|---|---|---|
| SCB search strips Swedish characters | Low | By design — keyword extraction avoids place names, region names resolved at dimension step |
| In-memory session store | Low | Intentional for workshop — sessions lost on restart, replace with Redis for production |
| No session cleanup job | Low | `cleanup_expired()` exists but is never called automatically |
| No request rate limiting | Medium | SCB allows ~30 req/10s per IP — could be hit under load |
| No authentication | Medium | API is open — acceptable for workshop, add auth for production |

---

## What Is Genuinely Next

### Phase 7 — Turtle Deployment (in progress)
Side work currently underway:
- [x] Pod Security Admission enabled cluster-wide (baseline default)
- [x] Namespace labels set: kube-system/ingress-nginx/kube-flannel=privileged, workshop=baseline
- [ ] nginx Ingress controller running stably
- [ ] `deploy/turtle/manifests/` — Deployment, Service, Ingress, Kustomization
- [ ] `deploy/turtle/scripts/` — deploy.sh, teardown.sh
- [ ] `docs/deployment/turtle.md` — full walkthrough
- [ ] Makefile targets: `turtle-deploy`, `turtle-teardown`, `turtle-logs`, `turtle-status`

### Phase 8 — Simple Web UI
A minimal browser interface so the agent can be demonstrated interactively.

Goals:
- Single HTML page, no framework
- Three-step flow matching the API: start → select table → confirm → answer
- Shows candidates with reasons, suggestions with reasons
- Shows raw values alongside the answer (transparency)
- Deployable as a second container in the same namespace

### Phase 9 — Docker Compose (bonus local option)
For quick demos and CI without Kubernetes.
- `docker-compose.yml`
- `deploy/compose/up.sh` and `down.sh`
- `docs/deployment/compose.md`

### Phase 10 — Hardening (production readiness)
Items to address before calling this production-ready:
- Session cleanup background task
- SCB API retry with exponential backoff
- Request rate limiting
- Structured logging (structlog or Python logging)
- FastAPI exception handlers for SCB errors
- Authentication (API key header minimum)
- Ceph RGW integration for session persistence (optional)

---

## Deployment Targets Summary

| Target | Status | Access | Notes |
|---|---|---|---|
| Local (uvicorn) | ✅ | localhost:8000 | Development |
| Kind cluster | ✅ | localhost:8080 | Local Kubernetes testing |
| Turtle homelab | 🔄 | research-agent.turtle.local | Bare-metal kubeadm cluster |
| Generic K8s | ⏳ | configurable | Cloud or bare-metal |

---

## Turtle Infrastructure Reference

| Node | IP | Role |
|---|---|---|
| clever-fly | 192.168.1.184 | Kubernetes control-plane |
| sought-perch | 192.168.1.16 | Kubernetes worker + Ceph OSD |
| quick-thrush | 192.168.1.200 | Kubernetes worker + Ceph OSD |
| alert-lizard | 192.168.1.183 | Ceph control-plane |

CNI: Flannel
Ingress: nginx (being set up)
Storage: Ceph (outside K8s, no CSI yet)
Registry: Docker Hub (ahembal/)
Namespace: workshop (baseline pod security)

---

## Known Infrastructure Issues (Turtle)

### Flannel instability on sought-perch
- **Symptom:** kube-flannel-ds on sought-perch has 7922+ restarts
- **Impact:** Pod sandbox recreated repeatedly, kills any pod scheduled there
- **Workaround:** Pin workloads to quick-thrush via nodeSelector
- **Fix:** Investigate kubelet logs on sought-perch, likely OOM from Ceph + Flannel memory contention
- **Priority:** High — affects all workloads on sought-perch

### nginx Ingress not working
- **Symptom:** Controller receives SIGTERM ~15s after starting
- **Root cause:** Flannel instability on sought-perch causing sandbox recreation
- **Workaround:** NodePort 31000 on quick-thrush
- **Fix:** Resolve Flannel issue first, then reinstall nginx Ingress
- **Priority:** Medium — NodePort works for workshop purposes

### Session Store — Future Improvement (Option B)
Replace the in-memory session store with a stateless JWT-based flow.
The client holds the pipeline state in a signed token and sends it back
with each request. Server becomes fully stateless — no shared memory,
scales horizontally without Redis.

Priority: Low — only needed if multiple replicas or horizontal scaling required.
