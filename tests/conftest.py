# tests/conftest.py
"""
Shared pytest fixtures for the test suite.

Fixtures here are available to all test files automatically.
The FastAPI test client and common mock responses are defined here
to keep individual test files focused on what they are testing.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from research_agent.main import app


@pytest.fixture
def client():
    """
    FastAPI test client.
    Makes HTTP requests to the app without needing a running server.
    """
    with TestClient(app) as c:
        yield c


@pytest.fixture
def mock_scb_tables():
    """
    A realistic mock response from the SCB table search endpoint.
    Used to avoid real network calls in unit tests.
    """
    return {
        "tables": [
            {
                "id": "TAB5169",
                "label": "Population statistics per quarter/half year/year by region and sex. Year 2000-2024"
            },
            {
                "id": "TAB1625",
                "label": "Population statistics by region and sex. Month 2000M01-2024M12"
            },
        ]
    }


@pytest.fixture
def mock_scb_metadata():
    """
    A realistic mock response from the SCB table metadata endpoint.
    Mirrors the structure of TAB5169.
    """
    return {
        "label": "Population statistics per quarter/half year/year by region and sex. Year 2000-2024",
        "id": ["Region", "Kon", "Tid"],
        "dimension": {
            "Region": {
                "label": "region",
                "category": {
                    "label": {
                        "00": "Whole country",
                        "01": "Stockholm county",
                        "03": "Uppsala county",
                    }
                }
            },
            "Kon": {
                "label": "sex",
                "category": {
                    "label": {
                        "1+2": "total",
                        "1": "men",
                        "2": "women",
                    }
                }
            },
            "Tid": {
                "label": "year",
                "category": {
                    "label": {
                        "2022": "2022",
                        "2023": "2023",
                        "2024": "2024",
                    }
                }
            },
        }
    }


@pytest.fixture
def mock_scb_query_result():
    """
    A realistic mock response from the SCB data query endpoint.
    """
    return {
        "label": "Population statistics",
        "value": [2473307],
        "dimension": {
            "Region": {
                "label": "region",
                "category": {
                    "label": {"01": "Stockholm county"}
                }
            },
            "Kon": {
                "label": "sex",
                "category": {
                    "label": {"1+2": "total"}
                }
            },
            "Tid": {
                "label": "year",
                "category": {
                    "label": {"2024": "2024"}
                }
            },
        }
    }
