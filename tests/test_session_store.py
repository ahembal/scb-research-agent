# tests/test_session_store.py
"""
Tests for the in-memory session store (session_store.py).

These are pure unit tests — no network calls, no LLM calls.
They test the session lifecycle: create, get, save, delete, expiry.
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from research_agent.session_store import (
    create_session,
    get_session,
    save_session,
    delete_session,
    cleanup_expired,
    _store,
)
from research_agent.models import SessionState, TableCandidate


@pytest.fixture(autouse=True)
def clear_store():
    """
    Clear the session store before each test.
    Prevents state leaking between tests.
    """
    _store.clear()
    yield
    _store.clear()


def test_create_session_returns_state():
    """create_session returns a SessionState with the correct question."""
    state = create_session("What is the population of Sweden?")
    assert state.question == "What is the population of Sweden?"
    assert state.session_id is not None
    assert len(state.session_id) > 0


def test_create_session_stores_in_memory():
    """Created session is retrievable from the store."""
    state = create_session("test question")
    retrieved = get_session(state.session_id)
    assert retrieved.session_id == state.session_id


def test_get_session_raises_on_unknown_id():
    """get_session raises KeyError for an unknown session ID."""
    with pytest.raises(KeyError, match="Session not found"):
        get_session("nonexistent-id")


def test_save_session_persists_changes():
    """Changes to a session are saved and retrievable."""
    state = create_session("test question")
    state.table_candidates = [
        TableCandidate(id="TAB001", label="Test table", reason="test")
    ]
    save_session(state)

    retrieved = get_session(state.session_id)
    assert len(retrieved.table_candidates) == 1
    assert retrieved.table_candidates[0].id == "TAB001"


def test_delete_session_removes_from_store():
    """delete_session removes the session so it can no longer be retrieved."""
    state = create_session("test question")
    session_id = state.session_id

    delete_session(session_id)

    with pytest.raises(KeyError):
        get_session(session_id)


def test_get_session_raises_on_expired():
    """get_session raises KeyError for a session past its TTL."""
    state = create_session("test question")

    # Backdate the creation time beyond the TTL
    expired_time = datetime.now(timezone.utc) - timedelta(seconds=9999)
    state.created_at = expired_time
    save_session(state)

    with pytest.raises(KeyError, match="Session expired"):
        get_session(state.session_id)


def test_cleanup_expired_removes_old_sessions():
    """cleanup_expired removes all sessions past their TTL."""
    # Create two sessions
    active = create_session("active question")
    expired = create_session("expired question")

    # Expire one of them
    expired.created_at = datetime.now(timezone.utc) - timedelta(seconds=9999)
    save_session(expired)

    removed = cleanup_expired()

    assert removed == 1
    # Active session still exists
    retrieved = get_session(active.session_id)
    assert retrieved.session_id == active.session_id
    # Expired session is gone
    with pytest.raises(KeyError):
        get_session(expired.session_id)
