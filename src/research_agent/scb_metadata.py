# src/research_agent/scb_metadata.py
"""
Low-level SCB API client for metadata operations.

Handles two operations:
  - Searching for tables by keyword
  - Fetching full metadata (dimensions + values) for a specific table

All functions are async — they are called from async FastAPI routes
and from agent step functions via asyncio.
"""
import httpx
from research_agent.config import SCB_API_BASE_URL


async def _fetch_json(path: str, params: dict | None = None) -> dict:
    """
    Make a GET request to the SCB API and return the parsed JSON response.
    Raises httpx.HTTPStatusError on non-2xx responses.
    """
    url = f"{SCB_API_BASE_URL.rstrip('/')}/{path.lstrip('/')}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()


async def search_tables(query: str) -> dict:
    """
    Search the SCB table catalogue by keyword.

    Returns a dict with a 'tables' list, each item containing at minimum:
      - id: the table identifier
      - label: human-readable table name
    """
    return await _fetch_json("tables", params={"query": query, "lang": "en"})


async def get_table_metadata(table_id: str) -> dict:
    """
    Fetch full metadata for a specific SCB table.

    Returns a dict containing:
      - label: table name
      - id: ordered list of dimension IDs
      - dimension: dict mapping dimension ID to its labels and values
    """
    return await _fetch_json(f"tables/{table_id}/metadata", params={"lang": "en"})
