"""
Phase 6: Scenario Manager unit tests.
"""
import pytest

from app.core.scenario_manager import resolve
from app.models import RiskScoreResult, Scenario


def test_resolve_returns_same_scenario_without_signals():
    assert resolve(Scenario.NORMAL, risk_result=None) == Scenario.NORMAL
    assert resolve(Scenario.HIGH_VOLATILITY) == Scenario.HIGH_VOLATILITY


def test_resolve_switches_on_high_volatility_signal():
    risk = RiskScoreResult(
        risk_score=0.5,
        threshold_breach=False,
        escalation_required=False,
        signals=["high_volatility"],
        scenario=Scenario.NORMAL,
        details={},
    )
    r = resolve(Scenario.NORMAL, risk_result=risk)
    assert r == Scenario.HIGH_VOLATILITY


def test_resolve_force_scenario_from_context():
    r = resolve(Scenario.NORMAL, context={"force_scenario": "maintenance"})
    assert r == Scenario.MAINTENANCE
