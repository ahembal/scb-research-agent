# tests/test_agent_flow.py
"""
Tests for the assisted agent pipeline (agent.py).

These are unit tests — all external calls (Claude API, SCB API) are mocked.
They test the flow logic: session creation, state transitions, error handling.

For real end-to-end tests with live APIs see test_scb_api.py (SCB)
and run the manual curl flow in docs/05-api-usage.md (full pipeline).
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from research_agent.agent import start_session, select_table, confirm_query
from research_agent.session_store import _store


@pytest.fixture(autouse=True)
def clear_store():
    """Clear the session store before each test."""
    _store.clear()
    yield
    _store.clear()


# ── start_session ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_start_session_creates_session(mock_scb_tables):
    """start_session creates a session and returns ranked candidates."""
    with patch("research_agent.agent.search_tables", new=AsyncMock(return_value=mock_scb_tables)), \
         patch("research_agent.agent._call_claude") as mock_claude:

        # First call: keyword extraction
        # Second call: table ranking
        mock_claude.side_effect = [
            "population region",
            '[{"id": "TAB5169", "reason": "Best match for population by region"}]'
        ]

        state = await start_session("What was the population of Stockholm in 2024?")

    assert state.session_id is not None
    assert state.question == "What was the population of Stockholm in 2024?"
    assert len(state.table_candidates) == 1
    assert state.table_candidates[0].id == "TAB5169"
    assert state.table_candidates[0].reason == "Best match for population by region"


@pytest.mark.asyncio
async def test_start_session_raises_when_no_tables_found():
    """start_session raises ValueError when SCB returns no tables."""
    with patch("research_agent.agent.search_tables", new=AsyncMock(return_value={"tables": []})), \
         patch("research_agent.agent._call_claude", return_value="population"):

        with pytest.raises(ValueError, match="No SCB tables found"):
            await start_session("some question")


@pytest.mark.asyncio
async def test_start_session_saves_to_store(mock_scb_tables):
    """start_session persists session state to the store."""
    with patch("research_agent.agent.search_tables", new=AsyncMock(return_value=mock_scb_tables)), \
         patch("research_agent.agent._call_claude") as mock_claude:

        mock_claude.side_effect = [
            "population region",
            '[{"id": "TAB5169", "reason": "Good match"}]'
        ]

        state = await start_session("test question")

    assert state.session_id in _store


# ── select_table ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_select_table_sets_selected_table(mock_scb_tables, mock_scb_metadata):
    """select_table stores the chosen table on session state."""
    with patch("research_agent.agent.search_tables", new=AsyncMock(return_value=mock_scb_tables)), \
         patch("research_agent.agent._call_claude") as mock_claude:

        mock_claude.side_effect = [
            "population region",
            '[{"id": "TAB5169", "reason": "Good match"}]'
        ]
        state = await start_session("What was the population of Stockholm in 2024?")

    with patch("research_agent.agent.get_table_metadata", new=AsyncMock(return_value=mock_scb_metadata)), \
         patch("research_agent.agent._call_claude") as mock_claude:

        mock_claude.return_value = '''[
            {"dimension_id": "Region", "suggested_codes": ["01"], "reason": "Stockholm county"},
            {"dimension_id": "Kon", "suggested_codes": ["1+2"], "reason": "Total population"},
            {"dimension_id": "Tid", "suggested_codes": ["2024"], "reason": "Year 2024"}
        ]'''

        state = await select_table(state.session_id, "TAB5169")

    assert state.selected_table is not None
    assert state.selected_table.id == "TAB5169"
    assert len(state.suggestions) == 3


@pytest.mark.asyncio
async def test_select_table_rejects_invalid_table(mock_scb_tables):
    """select_table raises ValueError for a table not in the candidate list."""
    with patch("research_agent.agent.search_tables", new=AsyncMock(return_value=mock_scb_tables)), \
         patch("research_agent.agent._call_claude") as mock_claude:

        mock_claude.side_effect = [
            "population region",
            '[{"id": "TAB5169", "reason": "Good match"}]'
        ]
        state = await start_session("test question")

    with pytest.raises(ValueError, match="was not in the candidate list"):
        await select_table(state.session_id, "TAB9999")


# ── confirm_query ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_confirm_query_returns_answer(
    mock_scb_tables, mock_scb_metadata, mock_scb_query_result
):
    """confirm_query returns a non-empty answer after querying SCB."""
    # Step 1
    with patch("research_agent.agent.search_tables", new=AsyncMock(return_value=mock_scb_tables)), \
         patch("research_agent.agent._call_claude") as mock_claude:
        mock_claude.side_effect = [
            "population region",
            '[{"id": "TAB5169", "reason": "Good match"}]'
        ]
        state = await start_session("What was the population of Stockholm in 2024?")

    # Step 2
    with patch("research_agent.agent.get_table_metadata", new=AsyncMock(return_value=mock_scb_metadata)), \
         patch("research_agent.agent._call_claude") as mock_claude:
        mock_claude.return_value = '''[
            {"dimension_id": "Region", "suggested_codes": ["01"], "reason": "Stockholm"},
            {"dimension_id": "Kon", "suggested_codes": ["1+2"], "reason": "Total"},
            {"dimension_id": "Tid", "suggested_codes": ["2024"], "reason": "2024"}
        ]'''
        state = await select_table(state.session_id, "TAB5169")

    # Step 3
    selection = {"Region": ["01"], "Kon": ["1+2"], "Tid": ["2024"]}

    with patch("research_agent.agent.httpx.AsyncClient") as mock_http, \
         patch("research_agent.agent._call_claude", return_value="The population was 2,473,307."):

        mock_response = MagicMock()
        mock_response.json.return_value = mock_scb_query_result
        mock_response.raise_for_status = MagicMock()
        mock_http.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )

        state = await confirm_query(state.session_id, selection)

    assert state.answer == "The population was 2,473,307."
    assert state.raw_values == [2473307]


@pytest.mark.asyncio
async def test_confirm_query_raises_without_selected_table(mock_scb_tables):
    """confirm_query raises ValueError if select_table was never called."""
    with patch("research_agent.agent.search_tables", new=AsyncMock(return_value=mock_scb_tables)), \
         patch("research_agent.agent._call_claude") as mock_claude:
        mock_claude.side_effect = [
            "population region",
            '[{"id": "TAB5169", "reason": "Good match"}]'
        ]
        state = await start_session("test question")

    with pytest.raises(ValueError, match="No table selected"):
        await confirm_query(state.session_id, {"Region": ["01"]})
