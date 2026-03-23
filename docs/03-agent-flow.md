# Agent Flow

## Core principle

The agent never makes a silent decision. At every step where a choice matters,
it presents options with reasoning and waits for the human to decide.

## Step by step

### Step 1 — User asks a question

The user posts a natural language question:
```
"What was the population of Stockholm county in 2024?"
```

### Step 2 — Agent searches SCB tables

The agent sends the question as a keyword search to the SCB API.
It receives a list of matching tables.

Claude then ranks the top candidates and provides a one-line reason for each,
so the user can make an informed choice.

The agent returns candidates to the user — it does NOT pick one silently.

### Step 3 — User picks a table

The user reviews the ranked candidates and selects the table ID they want to use.

### Step 4 — Agent fetches metadata and suggests dimension values

The agent fetches the full metadata for the selected table.
It reads all dimensions (Region, Sex, Year, etc.) and their available values.

Claude then suggests which values best match the original question,
with a brief explanation for each suggestion.

The agent returns the suggestions — it does NOT submit a query silently.

### Step 5 — User confirms or adjusts the selection

The user reviews the suggested dimension values.
They can accept them as-is, or override specific values before confirming.

### Step 6 — Agent queries SCB and returns the answer

With the confirmed selection, the agent builds the SCB query and fetches the data.

Claude generates a natural language answer from the result.

The response includes:
- The natural language answer
- The raw data values
- The source table name and ID
- The exact dimension selection used

The user always sees where the data came from and what was selected.

## Sequence diagram
```
User          API            Agent          Claude         SCB
 │             │               │               │             │
 │  POST       │               │               │             │
 │  /session   │               │               │             │
 │  /start     │               │               │             │
 │────────────>│               │               │             │
 │             │  search_tables│               │             │
 │             │──────────────>│               │             │
 │             │               │  GET /tables  │             │
 │             │               │─────────────────────────────>
 │             │               │<─────────────────────────────
 │             │               │  rank candidates              │
 │             │               │──────────────>│             │
 │             │               │<──────────────│             │
 │  candidates │               │               │             │
 │<────────────│               │               │             │
 │             │               │               │             │
 │  POST       │               │               │             │
 │  /session   │               │               │             │
 │  /select-   │               │               │             │
 │  table      │               │               │             │
 │────────────>│               │               │             │
 │             │  get_metadata │               │             │
 │             │──────────────>│               │             │
 │             │               │  GET metadata │             │
 │             │               │─────────────────────────────>
 │             │               │<─────────────────────────────
 │             │               │  suggest values               │
 │             │               │──────────────>│             │
 │             │               │<──────────────│             │
 │  suggestions│               │               │             │
 │<────────────│               │               │             │
 │             │               │               │             │
 │  POST       │               │               │             │
 │  /session   │               │               │             │
 │  /confirm-  │               │               │             │
 │  query      │               │               │             │
 │────────────>│               │               │             │
 │             │  query + answer               │             │
 │             │──────────────>│               │             │
 │             │               │  POST data    │             │
 │             │               │─────────────────────────────>
 │             │               │<─────────────────────────────
 │             │               │  generate answer              │
 │             │               │──────────────>│             │
 │             │               │<──────────────│             │
 │  answer +   │               │               │             │
 │  raw data   │               │               │             │
 │<────────────│               │               │             │
```

## What Claude does at each step

| Step | Claude's role |
|---|---|
| Table search | Ranks candidates, gives one-line reason per table |
| Dimension selection | Suggests values, explains why each matches the question |
| Answer generation | Writes a natural language answer from raw SCB data |

## What Claude never does

- Silently pick a table
- Silently submit a query
- Answer from its own knowledge instead of SCB data
- Hide which data was used to generate the answer
