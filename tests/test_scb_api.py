# tests/test_scb_api.py
"""
Tests for the SCB API client (scb_metadata.py).

These are INTEGRATION TESTS — they make real network calls to the SCB API.
They require internet access and will fail if SCB is unreachable.

Run only:
    pytest tests/test_scb_api.py -v

Skip in CI if no network:
    pytest tests/ -v --ignore=tests/test_scb_api.py
"""
import pytest
from research_agent.scb_metadata import search_tables, get_table_metadata
from research_agent.metadata_parser import parse_table_dimensions


pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_search_tables_returns_results():
    """SCB search returns at least one table for a known keyword."""
    result = await search_tables("population region")
    tables = result.get("tables", [])
    assert len(tables) > 0, "Expected at least one table from SCB search"


@pytest.mark.asyncio
async def test_search_tables_result_has_id_and_label():
    """Each table result has an id and a label."""
    result = await search_tables("population")
    tables = result.get("tables", [])
    for table in tables[:3]:
        assert "id" in table, "Table missing 'id' field"
        assert "label" in table, "Table missing 'label' field"


@pytest.mark.asyncio
async def test_get_table_metadata_returns_dimensions():
    """Fetching metadata for a known table returns parseable dimensions."""
    metadata = await get_table_metadata("TAB5169")
    assert "dimension" in metadata, "Metadata missing 'dimension' key"
    assert "id" in metadata, "Metadata missing 'id' key"


@pytest.mark.asyncio
async def test_parse_table_dimensions_returns_ordered_list():
    """parse_table_dimensions returns one entry per dimension in order."""
    metadata = await get_table_metadata("TAB5169")
    dims = parse_table_dimensions(metadata)
    assert len(dims) > 0, "Expected at least one dimension"
    for d in dims:
        assert "id" in d
        assert "label" in d
        assert "values" in d
        assert len(d["values"]) > 0, f"Dimension {d['id']} has no values"


@pytest.mark.asyncio
async def test_parse_table_dimensions_values_have_code_and_label():
    """Each dimension value has a code and a label."""
    metadata = await get_table_metadata("TAB5169")
    dims = parse_table_dimensions(metadata)
    for dim in dims:
        for value in dim["values"][:3]:
            assert "code" in value, f"Value in {dim['id']} missing 'code'"
            assert "label" in value, f"Value in {dim['id']} missing 'label'"
