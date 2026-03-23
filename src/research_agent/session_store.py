# src/research_agent/session_store.py
"""
In-memory session store for the assisted agent pipeline.

Holds SessionState objects between HTTP requests so the server remembers
where each conversation is in the three-step flow.

Design note: this is intentionally simple. In production you would replace
the _store dict with a Redis or database-backed implementation without
changing any other code — the interface stays the same.
"""
import uuid
from datetime import datetime, timezone
from research_agent.models import SessionState
from research_agent.config import SESSION_TTL_SECONDS


# Single in-memory store — maps session_id to SessionState
_store: dict[str, SessionState] = {}


def create_session(question: str) -> SessionState:
    """
    Create a new session for the given question.
    Returns the new SessionState with a generated session_id.
    """
    session_id = str(uuid.uuid4())
    state = SessionState(
        session_id=session_id,
        question=question,
        created_at=datetime.now(timezone.utc),
    )
    _store[session_id] = state
    return state


def get_session(session_id: str) -> SessionState:
    """
    Retrieve a session by ID.

    Raises KeyError if the session does not exist or has expired.
    Callers should catch this and return a 404 to the client.
    """
    state = _store.get(session_id)

    if state is None:
        raise KeyError(f"Session not found: {session_id}")

    # Check TTL
    age = (datetime.now(timezone.utc) - state.created_at).total_seconds()
    if age > SESSION_TTL_SECONDS:
        del _store[session_id]
        raise KeyError(f"Session expired: {session_id}")

    return state


def save_session(state: SessionState) -> None:
    """
    Persist an updated SessionState back to the store.
    Always call this after modifying a session.
    """
    _store[state.session_id] = state


def delete_session(session_id: str) -> None:
    """
    Remove a session from the store.
    Called after the final step when the session is no longer needed.
    """
    _store.pop(session_id, None)


def cleanup_expired() -> int:
    """
    Remove all expired sessions from the store.
    Returns the number of sessions removed.

    This can be called periodically to prevent memory growth in long-running
    instances. Not strictly needed for the workshop but good practice.
    """
    now = datetime.now(timezone.utc)
    expired = [
        sid for sid, state in _store.items()
        if (now - state.created_at).total_seconds() > SESSION_TTL_SECONDS
    ]
    for sid in expired:
        del _store[sid]
    return len(expired)
