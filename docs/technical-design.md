# Technical Design

*Last updated: 2026-03-29*

A stateless FastAPI application that acts as an assisted bridge between
natural-language user questions and the SCB Statistical Database API.
The agent never makes silent decisions — it ranks, explains, and waits
for the human to choose at every meaningful step.

## Stack

- Python 3.10+
- FastAPI
- uvicorn
- httpx (async)
- Pydantic v2
- anthropic SDK
- Docker
- Kubernetes (Kind + Turtle)

---

## Architecture Layers

| Layer | Files | Responsibility |
|---|---|---|
| API / Routing | `main.py` | FastAPI endpoints, request/response handling |
| Agent Orchestration | `agent.py` | Three-step assisted pipeline, LLM integration |
| Session State | `session_store.py` | In-memory session store with TTL |
| LLM Prompts | `prompts.py` | Rank and explain prompts — never silent decisions |
| SCB Integration | `scb_metadata.py` | HTTP calls to PxWebApi v2 |
| Data Processing | `metadata_parser.py`, `scb_query_builder.py`, `result_parser.py` | Parse dimensions, build queries, map labels |
| Configuration | `config.py` | Environment-based config |
| Internal Models | `models.py` | SessionState, TableCandidate, Dimension, DimensionSuggestion |
| API Schemas | `schema.py` | Pydantic request/response models |

---

## Request Flow

A complete end-to-end interaction follows this sequence:
```
01  POST /session/start
    Client sends natural language question

02  keyword_extraction_prompt()
    Claude extracts short SCB-friendly keywords
    (place names stripped — SCB search does not match ASCII approximations
    of Swedish characters e.g. Ostergotland → 0 results)

03  search_tables(keywords)
    Agent calls SCB metadata search

04  table_ranking_prompt()
    Claude ranks candidates and provides a reason for each

05  → Ranked candidates returned to user
    User reviews and picks a table

06  POST /session/select-table
    Client sends chosen table_id

07  get_table_metadata(table_id)
    Fetch full dimension/variable structure from SCB

08  parse_table_dimensions()
    Extract ordered dimension/value pairs

09  dimension_suggestion_prompt()
    Claude suggests dimension values with reasons

10  → Suggestions returned to user
    User reviews and confirms or adjusts

11  POST /session/confirm-query
    Client sends confirmed dimension selection

12  build_scb_query()
    Construct PxWebApi v2 payload

13  SCB data query
    Execute filtered data request

14  map_selection_to_labels()
    Resolve dimension codes to human-readable labels

15  answer_generation_prompt()
    Claude generates natural language answer from raw data

16  → Answer + raw values + source table returned to user
```

---

## API Endpoints

### Session endpoints — assisted pipeline

| Method | Path | Description |
|---|---|---|
| POST | `/session/start` | Step 1 — search tables, return ranked candidates |
| POST | `/session/select-table` | Step 2 — fetch metadata, return dimension suggestions |
| POST | `/session/confirm-query` | Step 3 — query SCB, return answer + raw data |

### Direct exploration endpoints — no session needed

| Method | Path | Description |
|---|---|---|
| GET | `/` | Health check — returns `{"status": "ok"}` |
| POST | `/tables/search` | Search SCB tables by keyword |
| GET | `/tables/{id}/metadata` | Parsed metadata for a specific table |
| POST | `/tables/{id}/query` | Execute a data query with known selection |

---

## Session Model

Sessions are stored in memory between the three HTTP requests.
Each session holds the full pipeline state:

| Field | Set at | Description |
|---|---|---|
| `session_id` | start | UUID identifier |
| `question` | start | Original user question |
| `table_candidates` | start | Ranked TableCandidate list |
| `selected_table` | select-table | Chosen TableCandidate |
| `dimensions` | select-table | Parsed Dimension list |
| `suggestions` | select-table | DimensionSuggestion list |
| `confirmed_selection` | confirm-query | Final dimension selection |
| `answer` | confirm-query | Generated natural language answer |
| `raw_values` | confirm-query | Raw numeric values from SCB |
| `selection_labels` | confirm-query | Human-readable selection summary |
| `created_at` | start | Used for TTL expiry |

TTL is configurable via `SESSION_TTL_SECONDS` (default: 3600s).

---

## LLM Integration

All LLM calls go through `_call_claude()` in `agent.py` — the single
integration point with the Anthropic API.

| Prompt | Input | Output |
|---|---|---|
| `keyword_extraction_prompt` | question | 2-4 search keywords |
| `table_ranking_prompt` | question + candidates | ranked list with reasons |
| `dimension_suggestion_prompt` | question + dimensions | suggested codes with reasons |
| `answer_generation_prompt` | question + data | natural language answer |

Model: `claude-sonnet-4-20250514` (configurable via `MODEL_NAME`)

---

## SCB API Integration

Base URL (configurable via `SCB_API_BASE_URL`):
```
https://statistikdatabasen.scb.se/api/v2
```

Key endpoints used:
```
GET  /tables?query={keywords}        discover tables
GET  /tables/{id}/metadata           full dimension metadata
POST /tables/{id}/data?lang=en       execute filtered data query
```

| Limit | Value |
|---|---|
| Max cells per request | 150,000 |
| Rate limit | ~30 requests / 10s / IP |
| Authentication | None required |

### Known limitation — Swedish characters

SCB search does not reliably match ASCII approximations of Swedish
place names. `Ostergotland` returns 0 results. The keyword extraction
prompt is designed to strip all place names and use generic topic
keywords instead. Region names are resolved later via dimension
value codes from the table metadata.

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `SCB_API_BASE_URL` | https://statistikdatabasen.scb.se/api/v2 | SCB API base URL |
| `ANTHROPIC_API_KEY` | — | Required. Get from console.anthropic.com |
| `MODEL_NAME` | claude-sonnet-4-20250514 | Claude model |
| `MAX_TOKENS` | 1024 | Max tokens for LLM responses |
| `SESSION_TTL_SECONDS` | 3600 | Session expiry in seconds |

---

## Error Handling

| Situation | Behaviour |
|---|---|
| SCB returns no tables | `ValueError` → HTTP 404 |
| Invalid table_id for session | `ValueError` → HTTP 400 |
| Expired or unknown session | `KeyError` → HTTP 404 |
| SCB API error (4xx/5xx) | `HTTPStatusError` → HTTP 502 |
| Claude returns invalid JSON | `ValueError` → HTTP 500 |
| SCB timeout (30s) | `TimeoutException` → HTTP 504 |

---

## Testing

### Test files

| File | Type | Coverage |
|---|---|---|
| `tests/test_scb_api.py` | Integration | Real SCB API calls — search, metadata, dimension parsing |
| `tests/test_agent_flow.py` | Unit | Full pipeline with mocked LLM and SCB |
| `tests/test_session_store.py` | Unit | Session create, get, save, delete, expiry, cleanup |
| `tests/test_api_endpoints.py` | Unit | HTTP layer — status codes, response shapes, error cases |

### Running tests
```bash
make test-unit          # no network needed
make test-integration   # requires internet + SCB reachable
make test-all           # everything
```

### Test markers
```
@pytest.mark.integration   # marks tests requiring network access
@pytest.mark.asyncio       # marks async tests (auto-applied via asyncio_mode=auto)
```

### What is mocked in unit tests

- `_call_claude()` — all LLM calls replaced with controlled responses
- `search_tables()` — returns fixture data
- `get_table_metadata()` — returns fixture data
- `httpx.AsyncClient` — SCB data query replaced with mock response

Real SCB API is only called in `test_scb_api.py` (integration tests).

---

## Deployment

| Target | Method | Access | Status |
|---|---|---|---|
| Local | uvicorn --reload | localhost:8000 | ✅ |
| Kind | NodePort 30080 | localhost:8080 | ✅ |
| Turtle | NodePort + nginx Ingress | research-agent.turtle.local | 🔄 |
| Generic K8s | Ingress | configurable | ⏳ |

Docker image: `ahembal/scb-research-agent:latest`
