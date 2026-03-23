# Session Model & API Contract

## Why sessions are needed

The assisted pipeline has three steps with human decisions between them.
The server needs to remember the state between those steps — what question
was asked, which table was selected, what dimensions are available.

This is handled with a lightweight in-memory session store.

## Session lifecycle
```
POST /session/start
  → creates session
  → returns session_id + table candidates

POST /session/select-table
  → looks up session by session_id
  → stores selected table
  → returns dimension suggestions

POST /session/confirm-query
  → looks up session by session_id
  → stores confirmed selection
  → queries SCB
  → returns answer + raw data
  → session can be discarded
```

## Session state fields

| Field | Type | Set at | Description |
|---|---|---|---|
| `session_id` | string | start | Unique identifier for this session |
| `question` | string | start | The original user question |
| `table_candidates` | list | start | Ranked table candidates from SCB search |
| `selected_table_id` | string | select-table | Table chosen by the user |
| `dimensions` | list | select-table | Parsed dimensions from table metadata |
| `suggested_selection` | dict | select-table | Claude's suggested dimension values |
| `confirmed_selection` | dict | confirm-query | Final selection confirmed by the user |
| `answer` | string | confirm-query | Generated natural language answer |
| `raw_values` | list | confirm-query | Raw numeric values from SCB |
| `created_at` | datetime | start | Used for TTL expiry |

## API contract

### POST /session/start

**Request:**
```json
{
  "question": "What was the population of Stockholm county in 2024?"
}
```

**Response:**
```json
{
  "session_id": "abc-123",
  "question": "What was the population of Stockholm county in 2024?",
  "candidates": [
    {
      "id": "TAB1234",
      "label": "Population per region by age and sex",
      "reason": "Matches region and year filter in the question"
    }
  ]
}
```

---

### POST /session/select-table

**Request:**
```json
{
  "session_id": "abc-123",
  "table_id": "TAB1234"
}
```

**Response:**
```json
{
  "session_id": "abc-123",
  "table_id": "TAB1234",
  "table_label": "Population per region by age and sex",
  "suggestions": [
    {
      "dimension_id": "Region",
      "dimension_label": "Region",
      "suggested_codes": ["01"],
      "suggested_labels": ["Stockholm county"],
      "reason": "Question asks about Stockholm county"
    },
    {
      "dimension_id": "Tid",
      "dimension_label": "Year",
      "suggested_codes": ["2024"],
      "suggested_labels": ["2024"],
      "reason": "Question asks about 2024"
    }
  ]
}
```

---

### POST /session/confirm-query

**Request:**
```json
{
  "session_id": "abc-123",
  "selection": {
    "Region": ["01"],
    "Kon": ["1", "2"],
    "Tid": ["2024"]
  }
}
```

**Response:**
```json
{
  "session_id": "abc-123",
  "question": "What was the population of Stockholm county in 2024?",
  "answer": "The population of Stockholm county in 2024 was 2,422,021 people.",
  "source_table": "Population per region by age and sex (TAB1234)",
  "selection_used": {
    "Region": ["Stockholm county"],
    "Sex": ["men", "women"],
    "Year": ["2024"]
  },
  "raw_values": [1198432, 1223589]
}
```

## Session expiry

Sessions expire after `SESSION_TTL_SECONDS` (default: 3600 seconds).
Expired sessions return a `404` with a clear error message.

## Note on production use

The in-memory session store is intentional for this workshop — it keeps
the infrastructure simple and easy to understand. In a production system
you would replace it with Redis or a database-backed store.
