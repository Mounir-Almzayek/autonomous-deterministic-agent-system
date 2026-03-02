# Pytest fixtures and shared test config
from __future__ import annotations

import pytest

from app.models import ActionType, ParsedIntent, Role, Scenario


@pytest.fixture
def sample_raw_intent() -> str:
    """Valid JSON intent for integration tests."""
    return '{"action_type":"query","params":{"id":"1"},"summary":"test query"}'


@pytest.fixture
def sample_parsed_intent() -> ParsedIntent:
    """ParsedIntent for unit tests."""
    return ParsedIntent(
        action_type=ActionType.QUERY,
        params={"symbol": "BTC", "limit": 10},
        summary="Get BTC price",
    )


@pytest.fixture
def role_agent() -> Role:
    return Role.AGENT


@pytest.fixture
def scenario_normal() -> Scenario:
    return Scenario.NORMAL
