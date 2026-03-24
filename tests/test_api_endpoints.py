# tests/test_api_endpoints.py
"""
Tests for the FastAPI HTTP endpoints (main.py).

Uses FastAPI's TestClient to make real HTTP requests to the app
without needing a running server. All agent and SCB calls are mocked.

These tests verify:
  - Correct HTTP status codes
  - Response shape matches the schema
  - Error cases return appropriate status codes
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from research_agent.models import (
    SessionState, TableCandidate, Dimension,
    DimensionValue, DimensionSuggestion
)
from research_agent.session_store import _store


@pytest.fixture(autouse=True)
def clear_store():
    """Clear the session store before each test."""
    _store.clear()
    yield
    _store.clear()


# ── Health ────────────────────────────────────────────────────────────────────

def test_health_returns_ok(client):
    """GET / returns 200 with status ok."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ── POST /session/start ───────────────────────────────────────────────────────

def test_session_start_returns_candidates(client, mock_scb_tables):
    """POST /session/start returns session_id and candidate list."""
    mock_state = SessionState(
        session_id="test-session-id",
        question="What was the population of Stockholm in 2024?",
        table_candidates=[
            TableCandidate(id="TAB5169", label="Population by region", reason="Best match")
        ]
    )

    with patch("research_agent.main.start_session", new=AsyncMock(return_value=mock_state)):
        response = client.post(
            "/session/start",
            json={"question": "What was the population of Stockholm in 2024?"}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "test-session-id"
    assert len(data["candidates"]) == 1
    assert data["candidates"][0]["id"] == "TAB5169"
    assert data["candidates"][0]["reason"] == "Best match"


def test_session_start_returns_404_when_no_tables(client):
    """POST /session/start returns 404 when no SCB tables found."""
    with patch(
        "research_agent.main.start_session",
        new=AsyncMock(side_effect=ValueError("No SCB tables found"))
    ):
        response = client.post(
            "/session/start",
            json={"question": "xyzzy nonsense query"}
        )

    assert response.status_code == 404


# ── POST /session/select-table ────────────────────────────────────────────────

def test_session_select_table_returns_suggestions(client):
    """POST /session/select-table returns dimension suggestions."""
    mock_state = SessionState(
        session_id="test-session-id",
        question="What was the population of Stockholm in 2024?",
        selected_table=TableCandidate(id="TAB5169", label="Population by region"),
        suggestions=[
            DimensionSuggestion(
                dimension_id="Region",
                dimension_label="region",
                suggested_codes=["01"],
                suggested_labels=["Stockholm county"],
                reason="Question asks about Stockholm county"
            )
        ]
    )

    with patch("research_agent.main.select_table", new=AsyncMock(return_value=mock_state)):
        response = client.post(
            "/session/select-table",
            json={"session_id": "test-session-id", "table_id": "TAB5169"}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["table_id"] == "TAB5169"
    assert len(data["suggestions"]) == 1
    assert data["suggestions"][0]["dimension_id"] == "Region"


def test_session_select_table_returns_404_for_expired_session(client):
    """POST /session/select-table returns 404 for unknown session."""
    with patch(
        "research_agent.main.select_table",
        new=AsyncMock(side_effect=KeyError("Session not found"))
    ):
        response = client.post(
            "/session/select-table",
            json={"session_id": "expired-id", "table_id": "TAB5169"}
        )

    assert response.status_code == 404


# ── POST /session/confirm-query ───────────────────────────────────────────────

def test_session_confirm_query_returns_answer(client):
    """POST /session/confirm-query returns answer and raw values."""
    mock_state = SessionState(
        session_id="test-session-id",
        question="What was the population of Stockholm in 2024?",
        selected_table=TableCandidate(
            id="TAB5169",
            label="Population statistics per quarter/half year/year by region and sex"
        ),
        answer="The population of Stockholm county in 2024 was 2,473,307.",
        raw_values=[2473307],
        selection_labels={
            "Region": [{"code": "01", "label": "Stockholm county"}],
            "Tid": [{"code": "2024", "label": "2024"}],
        }
    )

    with patch("research_agent.main.confirm_query", new=AsyncMock(return_value=mock_state)):
        response = client.post(
            "/session/confirm-query",
            json={
                "session_id": "test-session-id",
                "selection": {"Region": ["01"], "Tid": ["2024"]}
            }
        )

    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert data["raw_values"] == [2473307]
    assert "source_table" in data


def test_session_confirm_query_returns_400_for_bad_selection(client):
    """POST /session/confirm-query returns 400 for invalid selection."""
    with patch(
        "research_agent.main.confirm_query",
        new=AsyncMock(side_effect=ValueError("No table selected"))
    ):
        response = client.post(
            "/session/confirm-query",
            json={"session_id": "test-id", "selection": {}}
        )

    assert response.status_code == 400
