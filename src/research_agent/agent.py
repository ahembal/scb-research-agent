# src/research_agent/agent.py
"""
Assisted agent pipeline — three discrete step functions.

Design principle: each step does its work, presents results, and stops.
The human reviews the output and explicitly triggers the next step.
Nothing happens automatically between steps.

Step 1 — start_session:   search SCB tables, rank candidates, return to user
Step 2 — select_table:    fetch metadata, suggest dimension values, return to user
Step 3 — confirm_query:   query SCB with confirmed selection, generate answer

All LLM calls go through _call_claude() — the single integration point
with the Anthropic API.
"""
import json
import asyncio

import anthropic
import httpx

from research_agent.config import (
    ANTHROPIC_API_KEY,
    MODEL_NAME,
    MAX_TOKENS,
    SCB_API_BASE_URL,
)
from research_agent.models import (
    SessionState,
    TableCandidate,
    Dimension,
    DimensionValue,
    DimensionSuggestion,
)
from research_agent.prompts import (
    table_ranking_prompt,
    dimension_suggestion_prompt,
    answer_generation_prompt,
)
from research_agent.scb_metadata import search_tables, get_table_metadata
from research_agent.metadata_parser import parse_table_dimensions
from research_agent.scb_query_builder import build_scb_query
from research_agent.result_parser import map_selection_to_labels
from research_agent.session_store import create_session, get_session, save_session


# ── LLM integration ───────────────────────────────────────────────────────────

def _call_claude(prompt: str) -> str:
    """
    Send a prompt to Claude and return the raw text response.

    This is the single point of contact with the Anthropic API.
    All prompt construction happens in prompts.py before reaching here.
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model=MODEL_NAME,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


def _parse_json_response(raw: str, context: str) -> any:
    """
    Safely parse a JSON response from Claude.

    Strips markdown code fences if Claude wraps the output.
    Raises ValueError with context info if parsing fails.
    """
    cleaned = (
        raw.strip()
        .removeprefix("```json")
        .removeprefix("```")
        .removesuffix("```")
        .strip()
    )
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Claude returned invalid JSON for {context}:\n{raw}"
        ) from e


# ── Step 1: Start session ─────────────────────────────────────────────────────

async def start_session(question: str) -> SessionState:
    """
    Step 1 of the assisted pipeline.

    - Creates a new session for the question
    - Searches SCB for relevant tables
    - Asks Claude to rank candidates and explain relevance
    - Saves ranked candidates to session state
    - Returns state to the caller (main.py exposes this to the user)

    The user reviews the ranked candidates and picks one before step 2 runs.
    """
    state = create_session(question)

    # Search SCB for candidate tables
    result = await search_tables(question)
    tables = result.get("tables", [])

    if not tables:
        raise ValueError(f"No SCB tables found for: '{question}'")

    candidates_raw = [
        {"id": t.get("id"), "label": t.get("label")}
        for t in tables[:10]
        if t.get("id") and t.get("label")
    ]

    # Ask Claude to rank and explain
    prompt = table_ranking_prompt(question, candidates_raw)
    ranked_raw = _call_claude(prompt)
    ranked = _parse_json_response(ranked_raw, "table ranking")

    # Build TableCandidate objects, preserving Claude's ranked order
    ranked_ids = {item["id"]: item.get("reason", "") for item in ranked}
    state.table_candidates = [
        TableCandidate(
            id=item["id"],
            label=next(
                (c["label"] for c in candidates_raw if c["id"] == item["id"]),
                item["id"],
            ),
            reason=item.get("reason", ""),
        )
        for item in ranked
        if item["id"] in {c["id"] for c in candidates_raw}
    ]

    save_session(state)
    return state


# ── Step 2: Select table ──────────────────────────────────────────────────────

async def select_table(session_id: str, table_id: str) -> SessionState:
    """
    Step 2 of the assisted pipeline.

    - Retrieves the session
    - Validates the chosen table_id against known candidates
    - Fetches full metadata for the selected table
    - Asks Claude to suggest dimension values with reasons
    - Saves selected table, dimensions, and suggestions to session state
    - Returns state to the caller

    The user reviews dimension suggestions and confirms or adjusts before step 3.
    """
    state = get_session(session_id)

    # Validate the chosen table exists in our candidate list
    valid_ids = {c.id for c in state.table_candidates}
    if table_id not in valid_ids:
        raise ValueError(
            f"Table '{table_id}' was not in the candidate list for this session."
        )

    chosen = next(c for c in state.table_candidates if c.id == table_id)
    state.selected_table = chosen

    # Fetch full metadata from SCB
    metadata = await get_table_metadata(table_id)
    parsed = parse_table_dimensions(metadata)

    # Store structured dimensions on state
    state.dimensions = [
        Dimension(
            id=d["id"],
            label=d["label"],
            values=[
                DimensionValue(code=v["code"], label=v["label"])
                for v in d["values"]
            ],
        )
        for d in parsed
    ]

    # Ask Claude to suggest values with reasons
    prompt = dimension_suggestion_prompt(state.question, parsed)
    suggestions_raw = _call_claude(prompt)
    suggestions = _parse_json_response(suggestions_raw, "dimension suggestions")

    # Build a lookup of valid codes per dimension for validation
    valid_codes = {
        d["id"]: {v["code"] for v in d["values"]}
        for d in parsed
    }

    # Build label lookup per dimension
    label_lookup = {
        d["id"]: {v["code"]: v["label"] for v in d["values"]}
        for d in parsed
    }

    # Build DimensionSuggestion objects, filtering out any invalid codes
    state.suggestions = []
    for item in suggestions:
        dim_id = item.get("dimension_id")
        if dim_id not in valid_codes:
            continue

        valid = [
            code for code in item.get("suggested_codes", [])
            if code in valid_codes[dim_id]
        ]
        if not valid:
            continue

        state.suggestions.append(
            DimensionSuggestion(
                dimension_id=dim_id,
                dimension_label=next(
                    (d["label"] for d in parsed if d["id"] == dim_id), dim_id
                ),
                suggested_codes=valid,
                suggested_labels=[
                    label_lookup[dim_id].get(c, c) for c in valid
                ],
                reason=item.get("reason", ""),
            )
        )

    save_session(state)
    return state


# ── Step 3: Confirm query ─────────────────────────────────────────────────────

async def confirm_query(session_id: str, selection: dict[str, list[str]]) -> SessionState:
    """
    Step 3 of the assisted pipeline.

    - Retrieves the session
    - Stores the user-confirmed dimension selection
    - Builds and sends the SCB data query
    - Asks Claude to generate a natural language answer from the result
    - Saves answer, raw values, and selection labels to session state
    - Returns state to the caller

    This is the final step — after this the session can be discarded.
    """
    state = get_session(session_id)

    if state.selected_table is None:
        raise ValueError(
            "No table selected for this session. "
            "Complete step 2 (select-table) before confirming a query."
        )

    state.confirmed_selection = selection

    # Build and send the SCB query
    data_url = f"{SCB_API_BASE_URL}/tables/{state.selected_table.id}/data?lang=en"
    payload = build_scb_query(selection)

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(data_url, json=payload)
        response.raise_for_status()
        result = response.json()

    # Parse result
    selection_labels = map_selection_to_labels(result, selection)
    raw_values = result.get("value", [])
    dimension_labels = {
        dim_id: dim_data.get("label")
        for dim_id, dim_data in result.get("dimension", {}).items()
    }

    state.raw_values = raw_values
    state.selection_labels = selection_labels

    # Ask Claude to generate the answer
    prompt = answer_generation_prompt(
        question=state.question,
        table_label=state.selected_table.label,
        selection_labels=selection_labels,
        values=raw_values,
        dimension_labels=dimension_labels,
    )
    state.answer = _call_claude(prompt)

    save_session(state)
    return state
