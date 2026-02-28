"""
Mock scenario data for risk scoring (Phase 3).
Simulates market/operational context per scenario (e.g. volatility, exposure).
Deterministic for tests; replace with live data in production.
"""
from __future__ import annotations

from app.models import Scenario

# Simulated volatility index per scenario (0=calm, 1=high). Used to adjust risk.
VOLATILITY_INDEX: dict[Scenario, float] = {
    Scenario.NORMAL: 0.3,
    Scenario.LOW_RISK: 0.15,
    Scenario.HIGH_VOLATILITY: 0.85,
    Scenario.MAINTENANCE: 0.2,
}

# Simulated operational exposure factor (0=none, 1=high). E.g. open positions, pending ops.
EXPOSURE_FACTOR: dict[Scenario, float] = {
    Scenario.NORMAL: 0.4,
    Scenario.LOW_RISK: 0.2,
    Scenario.HIGH_VOLATILITY: 0.7,
    Scenario.MAINTENANCE: 0.1,
}


def get_volatility(scenario: Scenario) -> float:
    """Return current volatility index for scenario (mock)."""
    return VOLATILITY_INDEX.get(scenario, 0.3)


def get_exposure(scenario: Scenario) -> float:
    """Return current exposure factor for scenario (mock)."""
    return EXPOSURE_FACTOR.get(scenario, 0.4)


def get_scenario_context(scenario: Scenario) -> dict[str, float]:
    """Return full mock context for risk calculation."""
    return {
        "volatility": get_volatility(scenario),
        "exposure": get_exposure(scenario),
    }
