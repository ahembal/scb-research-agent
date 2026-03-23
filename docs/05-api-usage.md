# API Usage Examples

All examples assume the API is running at `http://localhost:8000`.

Start the API:
```bash
uvicorn research_agent.main:app --reload --app-dir src
```

---

## Health check
```bash
curl http://localhost:8000/
```

Expected:
```json
{"status": "ok"}
```

---

## Full assisted flow

### Step 1 — Start a session
```bash
curl -s -X POST http://localhost:8000/session/start \
  -H "Content-Type: application/json" \
  -d '{"question": "What was the population of Stockholm county in 2024?"}' \
  | python3 -m json.tool
```

Note the `session_id` and review the ranked `candidates`.

---

### Step 2 — Select a table

Replace `SESSION_ID` and `TABLE_ID` with values from step 1.
```bash
curl -s -X POST http://localhost:8000/session/select-table \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "SESSION_ID",
    "table_id": "TABLE_ID"
  }' \
  | python3 -m json.tool
```

Review the `suggestions` for each dimension. You can accept them or adjust in step 3.

---

### Step 3 — Confirm the query

Use the suggested selection from step 2, adjusting any values if needed.
```bash
curl -s -X POST http://localhost:8000/session/confirm-query \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "SESSION_ID",
    "selection": {
      "Region": ["01"],
      "Kon": ["1", "2"],
      "Tid": ["2024"]
    }
  }' \
  | python3 -m json.tool
```

---

## Explore tables directly (no session needed)

### Search tables by keyword
```bash
curl -s -X POST http://localhost:8000/tables/search \
  -H "Content-Type: application/json" \
  -d '{"question": "population region"}' \
  | python3 -m json.tool
```

### Fetch table metadata
```bash
curl -s http://localhost:8000/tables/TAB1234/metadata \
  | python3 -m json.tool
```

### Query a table directly
```bash
curl -s -X POST http://localhost:8000/tables/TAB1234/query \
  -H "Content-Type: application/json" \
  -d '{
    "selection": {
      "Region": ["00"],
      "Kon": ["1", "2"],
      "Tid": ["2024"]
    }
  }' \
  | python3 -m json.tool
```

---

## Interactive API docs

FastAPI generates interactive documentation automatically:
```
http://localhost:8000/docs
```

You can try all endpoints directly from the browser.
