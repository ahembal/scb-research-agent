# Implementation Plan

*Last updated: 2026-04-06*

This document reflects the current state of the project and what is genuinely next.
It supersedes the original three-phase plan which was written before the workshop.

---

## Design Principles (established during workshop)

- **Assisted AI, not autonomous AI** — the agent ranks and explains, the human decides
- **Four-step pipeline** — evaluate → search → review → answer. Nothing happens between steps automatically.
- **Grounded answers only** — every answer comes from live SCB data, never from LLM knowledge
- **Transparent sources** — every response includes the source table, exact selection, and raw values

---

## Current State

### Core Agent — Done
| Module | Status | Notes |
|---|---|---|
| `config.py` | ✅ | Anthropic + SCB + session config via env vars |
| `models.py` | ✅ | SessionState, TableCandidate, Dimension, DimensionSuggestion, QuerySuggestion |
| `schema.py` | ✅ | Full session + exploration HTTP schemas including evaluate step |
| `prompts.py` | ✅ | query_suggestion, table_ranking, dimension_suggestion, answer_generation, keyword_extraction |
| `agent.py` | ✅ | Four-step assisted pipeline: evaluate_question, start_session, select_table, confirm_query |
| `session_store.py` | ✅ | In-memory session store with TTL expiry, deleted after confirm_query |
| `scb_metadata.py` | ✅ | search_tables, get_table_metadata |
| `metadata_parser.py` | ✅ | Parses SCB dimension structures |
| `scb_query_builder.py` | ✅ | Builds PxWebApi v2 query payloads |
| `result_parser.py` | ✅ | Maps dimension codes to human-readable labels |
| `main.py` | ✅ | Session endpoints + direct exploration endpoints + CORS middleware |

### Tests — Done
| File | Status | Notes |
|---|---|---|
| `tests/test_scb_api.py` | ✅ | Integration tests against real SCB API |
| `tests/test_agent_flow.py` | ✅ | Pipeline tests with mocked LLM and SCB |
| `tests/test_session_store.py` | ✅ | Session lifecycle unit tests |
| `tests/test_api_endpoints.py` | ✅ | HTTP layer tests with FastAPI TestClient |

### Infrastructure — Done
| Item | Status | Notes |
|---|---|---|
| `Dockerfile` | ✅ | Non-root user (uid 1000), no HEALTHCHECK, correct build order |
| `deploy/base/` | ✅ | ConfigMap, Deployment, Service, Kustomization with security context |
| `deploy/kind/` | ✅ | Cluster config, manifests, scripts — tested end to end |
| `deploy/turtle/` | ✅ | NodePort + Squid proxy + node selector — working end to end |
| `deploy/k8s/` | ⏳ | Pending — generic cloud overlay |
| Docker Hub image | ✅ | ahembal/scb-research-agent:latest |

### UI — Done
| Item | Status | Notes |
|---|---|---|
| Lovable UI | ✅ | Four-step flow, hosted at scb-research-agent.demo.balsever.se |
| Tailscale Funnel | ✅ | Public HTTPS endpoint via quick-thrush.tailce4064.ts.net |
| CORS middleware | ✅ | Allow-Private-Network header added |

### Documentation — Done
| File | Status | Notes |
|---|---|---|
| `docs/01-overview.md` | ✅ | Architecture, design principle, component table |
| `docs/02-scb-data.md` | ✅ | SCB API, known limitations (Swedish characters) |
| `docs/03-agent-flow.md` | ✅ | Sequence diagram, assisted flow |
| `docs/04-session-model.md` | ✅ | API contract, session lifecycle |
| `docs/05-api-usage.md` | ✅ | curl examples for all endpoints |
| `docs/06-prerequisites.md` | ✅ | API key, billing, Docker Hub image |
| `docs/technical-design.md` | ✅ | Full technical design document |
| `docs/implementation-plan.md` | ✅ | This file |
| `docs/deployment/kind.md` | ✅ | Full Kind walkthrough |
| `docs/deployment/turtle.md` | ✅ | Turtle homelab walkthrough |
| `docs/deployment/k8s.md` | ⏳ | Pending generic cloud overlay |
| `docs/infrastructure/proxy.md` | ✅ | Squid proxy setup, operations, and rationale |

---

## API Endpoints

### Session endpoints — assisted pipeline

| Method | Path | Step | Description |
|---|---|---|---|
| POST | `/session/evaluate` | 0 | Evaluate question, return 2-3 query suggestions |
| POST | `/session/start` | 1 | Search SCB with chosen query, return ranked candidates |
| POST | `/session/select-table` | 2 | Fetch metadata, return dimension suggestions |
| POST | `/session/confirm-query` | 3 | Query SCB, return answer + raw data |

### Direct exploration endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/` | Health check |
| POST | `/tables/search` | Search SCB tables by keyword |
| GET | `/tables/{id}/metadata` | Fetch dimensions for a table |
| POST | `/tables/{id}/query` | Query a table directly |

---

## Known Issues & Limitations

| Issue | Severity | Notes |
|---|---|---|
| SCB search strips Swedish characters | Low | By design — keyword extraction avoids place names, region names resolved at dimension step |
| In-memory session store | Low | Intentional for workshop — sessions deleted after confirm_query, lost on restart |
| No session cleanup job | Low | `cleanup_expired()` exists but is never called automatically |
| No request rate limiting | Medium | SCB allows ~30 req/10s per IP — could be hit under load |
| No authentication | Medium | API is open — acceptable for workshop, add auth for production |
| Dimension value truncation | Low | Fixed at 200 values per dimension — very large tables may still truncate |

---

## What Is Genuinely Next

### Docker Compose (bonus local option)
For quick demos and CI without Kubernetes.
- `docker-compose.yml`
- `deploy/compose/up.sh` and `down.sh`
- `docs/deployment/compose.md`

### Generic K8s overlay
For deploying to any cloud or bare-metal Kubernetes cluster.
- `deploy/k8s/manifests/` — Ingress, Kustomization
- `deploy/k8s/scripts/` — deploy.sh, teardown.sh
- `docs/deployment/k8s.md`

### Hardening (production readiness)
Items to address before calling this production-ready:
- Session cleanup background task (call `cleanup_expired()` periodically)
- SCB API retry with exponential backoff
- Request rate limiting
- Structured logging (structlog or Python logging)
- FastAPI exception handlers for SCB errors
- Authentication (API key header minimum)
- Ceph RGW integration for session persistence (optional)

### Session Store — Future Improvement
Replace the in-memory session store with a stateless JWT-based flow.
The client holds the pipeline state in a signed token and sends it back
with each request. Server becomes fully stateless — no shared memory,
scales horizontally without Redis.

Priority: Low — only needed if multiple replicas or horizontal scaling required.

---

## Deployment Targets Summary

| Target | Status | Access | Notes |
|---|---|---|---|
| Local (uvicorn) | ✅ | localhost:8000 | Development |
| Kind cluster | ✅ | localhost:8080 | Local Kubernetes testing |
| Turtle homelab | ✅ | quick-thrush.tailce4064.ts.net | Bare-metal kubeadm, NodePort + Tailscale Funnel |
| Generic K8s | ⏳ | configurable | Cloud or bare-metal |

---

## Turtle Infrastructure Reference

| Node | IP | Tailscale IP | Role |
|---|---|---|---|
| clever-fly | 192.168.1.184 | — | Kubernetes control-plane |
| sought-perch | 192.168.1.16 | — | Kubernetes worker + Ceph OSD |
| quick-thrush | 192.168.1.200 | 100.82.75.34 | Kubernetes worker + Ceph OSD |
| alert-lizard | 192.168.1.183 | — | Ceph control-plane + Squid proxy |

CNI: Flannel
Ingress: NodePort 31000 on quick-thrush (nginx Ingress pending Flannel fix)
Storage: Ceph (outside K8s, no CSI yet)
Registry: Docker Hub (ahembal/)
Namespace: workshop (baseline pod security)
Outbound proxy: Squid on alert-lizard:3128
Public endpoint: Tailscale Funnel on quick-thrush

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