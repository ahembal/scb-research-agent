# src/research_agent/main.py
"""
FastAPI application — HTTP routing and request/response handling.

Session endpoints (assisted pipeline):
  POST /session/start           — search tables, return ranked candidates
  POST /session/select-table    — fetch metadata, return dimension suggestions
  POST /session/confirm-query   — query SCB, return answer + raw data

Direct exploration endpoints (no session needed):
  POST /tables/search           — search SCB tables by keyword
  GET  /tables/{id}/metadata    — fetch dimensions for a table
  POST /tables/{id}/query       — query a table with a known selection
"""
from fastapi import FastAPI, HTTPException
import httpx

from research_agent.agent import start_session, select_table, confirm_query
from research_agent.schema import (
    QuestionRequest,
    SessionStartResponse,
    SelectTableRequest,
    SelectTableResponse,
    ConfirmQueryRequest,
    ConfirmQueryResponse,
    TableSearchResponse,
    TableMetadataResponse,
    TableQueryRequest,
    TableCandidateResponse,
    DimensionSuggestionResponse,
)
from research_agent.scb_metadata import search_tables, get_table_metadata
from research_agent.metadata_parser import parse_table_dimensions
from research_agent.scb_query_builder import build_scb_query
from research_agent.result_parser import map_selection_to_labels

app = FastAPI(
    title="Public Data Research Agent",
    description=(
        "An assisted AI agent that helps you explore and query "
        "Swedish public statistics from SCB. "
        "The agent ranks and explains — you decide."
    ),
    version="0.1.0",
)


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/", tags=["health"])
def health():
    """Basic health check."""
    return {"status": "ok"}


# ── Session endpoints — assisted pipeline ─────────────────────────────────────

@app.post(
    "/session/start",
    response_model=SessionStartResponse,
    tags=["session"],
    summary="Step 1 — search tables and get ranked candidates",
)
async def session_start(req: QuestionRequest):
    """
    Step 1 of the assisted pipeline.

    Searches SCB for tables relevant to the question.
    Claude ranks the candidates and provides a reason for each.
    The user reviews the list and picks a table before calling /session/select-table.
    """
    try:
        state = await start_session(req.question)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return SessionStartResponse(
        session_id=state.session_id,
        question=state.question,
        candidates=[
            TableCandidateResponse(
                id=c.id,
                label=c.label,
                reason=c.reason,
            )
            for c in state.table_candidates
        ],
    )


@app.post(
    "/session/select-table",
    response_model=SelectTableResponse,
    tags=["session"],
    summary="Step 2 — select a table and get dimension suggestions",
)
async def session_select_table(req: SelectTableRequest):
    """
    Step 2 of the assisted pipeline.

    Fetches metadata for the chosen table.
    Claude suggests dimension values with reasons.
    The user reviews and confirms or adjusts before calling /session/confirm-query.
    """
    try:
        state = await select_table(req.session_id, req.table_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return SelectTableResponse(
        session_id=state.session_id,
        table_id=state.selected_table.id,
        table_label=state.selected_table.label,
        suggestions=[
            DimensionSuggestionResponse(
                dimension_id=s.dimension_id,
                dimension_label=s.dimension_label,
                suggested_codes=s.suggested_codes,
                suggested_labels=s.suggested_labels,
                reason=s.reason,
            )
            for s in state.suggestions
        ],
    )


@app.post(
    "/session/confirm-query",
    response_model=ConfirmQueryResponse,
    tags=["session"],
    summary="Step 3 — confirm selection and get the answer",
)
async def session_confirm_query(req: ConfirmQueryRequest):
    """
    Step 3 of the assisted pipeline.

    Sends the confirmed dimension selection to SCB and fetches the data.
    Claude generates a natural language answer grounded in the result.

    The response always includes:
    - The natural language answer
    - The raw numeric values from SCB
    - The exact selection used with human-readable labels
    - The source table name and ID
    """
    try:
        state = await confirm_query(req.session_id, req.selection)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"SCB API error: {e.response.status_code} — {e.response.text}",
        )

    selection_used = {
        dim_id: [item["label"] for item in items]
        for dim_id, items in state.selection_labels.items()
    }

    return ConfirmQueryResponse(
        session_id=state.session_id,
        question=state.question,
        answer=state.answer,
        source_table=f"{state.selected_table.label} ({state.selected_table.id})",
        selection_used=selection_used,
        raw_values=state.raw_values,
    )


# ── Direct exploration endpoints — no session needed ──────────────────────────

@app.post(
    "/tables/search",
    response_model=TableSearchResponse,
    tags=["explore"],
    summary="Search SCB tables by keyword",
)
async def tables_search(req: QuestionRequest):
    """
    Search the SCB table catalogue by keyword.
    Useful for exploring available datasets without starting a session.
    """
    result = await search_tables(req.question)
    return TableSearchResponse(
        question=req.question,
        tables=result.get("tables", []),
    )


@app.get(
    "/tables/{table_id}/metadata",
    response_model=TableMetadataResponse,
    tags=["explore"],
    summary="Fetch dimensions and values for a specific table",
)
async def table_metadata(table_id: str):
    """
    Fetch the full metadata for a specific SCB table.
    Shows all available dimensions and their selectable values.
    """
    metadata = await get_table_metadata(table_id)
    dimensions = parse_table_dimensions(metadata)
    return TableMetadataResponse(
        table_id=table_id,
        label=metadata.get("label"),
        dimensions=dimensions,
    )


@app.post(
    "/tables/{table_id}/query",
    tags=["explore"],
    summary="Query a table directly with a known selection",
)
async def query_table(table_id: str, req: TableQueryRequest):
    """
    Query a specific SCB table directly with a known dimension selection.
    Bypasses the session flow — useful for manual testing and debugging.
    """
    data_url = (
        f"https://statistikdatabasen.scb.se/api/v2"
        f"/tables/{table_id}/data?lang=en"
    )
    payload = build_scb_query(req.selection)

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(data_url, json=payload)
        response.raise_for_status()
        result = response.json()

    return {
        "table_id": table_id,
        "label": result.get("label"),
        "selection": req.selection,
        "selection_labels": map_selection_to_labels(result, req.selection),
        "values": result.get("value", []),
        "dimension_labels": {
            dim_id: dim_data.get("label")
            for dim_id, dim_data in result.get("dimension", {}).items()
        },
    }
