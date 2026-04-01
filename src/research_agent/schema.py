# src/research_agent/schema.py
"""
FastAPI request and response schemas.

These Pydantic models define the public HTTP API contract.
See docs/04-session-model.md for the full API design.
"""
from pydantic import BaseModel
from typing import Any


# ── Shared ────────────────────────────────────────────────────────────────────

class QuestionRequest(BaseModel):
    """A natural language question from the user."""
    question: str


# ── Session: Step 0 — Evaluate ────────────────────────────────────────────────

class QuerySuggestionResponse(BaseModel):
    """A suggested rephrased query with topic and reason."""
    query: str
    topic: str
    reason: str


class SessionEvaluateResponse(BaseModel):
    """
    Returned after POST /session/evaluate.
    Contains suggested queries for the user to choose from.
    """
    session_id: str
    question: str
    suggestions: list[QuerySuggestionResponse]


# ── Session: Step 1 — Start ───────────────────────────────────────────────────

class ChooseQueryRequest(BaseModel):
    """User picks a suggested query or types their own."""
    session_id: str
    chosen_query: str


class TableCandidateResponse(BaseModel):
    """A ranked SCB table candidate with a reason for its relevance."""
    id: str
    label: str
    reason: str


class SessionStartResponse(BaseModel):
    """
    Returned after POST /session/start.
    Contains ranked table candidates for the user to choose from.
    """
    session_id: str
    question: str
    chosen_query: str
    candidates: list[TableCandidateResponse]


# ── Session: Step 2 — Select Table ───────────────────────────────────────────

class SelectTableRequest(BaseModel):
    """User picks a table from the candidates returned in step 1."""
    session_id: str
    table_id: str


class DimensionSuggestionResponse(BaseModel):
    """
    Claude's suggested values for one dimension.
    The user can accept or override before confirming the query.
    """
    dimension_id: str
    dimension_label: str
    suggested_codes: list[str]
    suggested_labels: list[str]
    reason: str


class SelectTableResponse(BaseModel):
    """
    Returned after POST /session/select-table.
    Contains dimension suggestions for the user to review.
    """
    session_id: str
    table_id: str
    table_label: str
    suggestions: list[DimensionSuggestionResponse]


# ── Session: Step 3 — Confirm Query ──────────────────────────────────────────

class ConfirmQueryRequest(BaseModel):
    """
    User confirms (or adjusts) the dimension selection and triggers the query.
    Selection maps dimension IDs to lists of value codes.
    """
    session_id: str
    selection: dict[str, list[str]]


class ConfirmQueryResponse(BaseModel):
    """
    Returned after POST /session/confirm-query.
    Contains the natural language answer, source info, and raw data.
    """
    session_id: str
    question: str
    answer: str
    source_table: str
    selection_used: dict[str, list[str]]
    raw_values: list[Any]


# ── Direct table exploration (no session needed) ──────────────────────────────

class TableSearchResponse(BaseModel):
    """Response from POST /tables/search."""
    question: str
    tables: list[dict]


class TableMetadataResponse(BaseModel):
    """Response from GET /tables/{table_id}/metadata."""
    table_id: str
    label: str | None
    dimensions: list[dict]


class TableQueryRequest(BaseModel):
    """
    Request body for POST /tables/{table_id}/query.
    Allows direct querying of a table without going through the session flow.
    """
    selection: dict[str, list[str]]


# ── Legacy ────────────────────────────────────────────────────────────────────

class AnswerResponse(BaseModel):
    """
    Legacy response model kept for backwards compatibility.
    New code should use the session endpoints instead.
    """
    question: str
    answer: str
    sources: list[str]
    notes: list[str]
    next_action: dict[str, Any] | None = None
