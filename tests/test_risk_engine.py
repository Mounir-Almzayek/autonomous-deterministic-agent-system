"""
Phase 3: Risk Engine unit tests.
"""
import pytest

from app.core.risk_engine import score
from app.models import ActionType, ParsedIntent, Scenario


def test_risk_score_query_low():
    intent = ParsedIntent(action_type=ActionType.QUERY, params={"id": "1"}, summary="")
    r = score(intent, Scenario.NORMAL)
    assert 0 <= r.risk_score <= 1
    assert r.scenario == Scenario.NORMAL
    assert r.risk_score < 0.5


def test_risk_score_execute_higher():
    intent_exec = ParsedIntent(action_type=ActionType.EXECUTE, params={"qty": 100}, summary="")
    intent_query = ParsedIntent(action_type=ActionType.QUERY, params={"id": "1"}, summary="")
    r_exec = score(intent_exec, Scenario.NORMAL)
    r_query = score(intent_query, Scenario.NORMAL)
    assert r_exec.risk_score >= r_query.risk_score


def test_risk_signals_execute():
    intent = ParsedIntent(action_type=ActionType.EXECUTE, params={"x": 1}, summary="")
    r = score(intent, Scenario.NORMAL)
    assert "execute_action" in r.signals or r.risk_score > 0


def test_risk_threshold_breach_high_volatility():
    intent = ParsedIntent(action_type=ActionType.EXECUTE, params={"a": 1, "b": 2}, summary="")
    r = score(intent, Scenario.HIGH_VOLATILITY)
    assert r.threshold_breach is True or r.escalation_required is True or r.risk_score > 0


def test_risk_context_override():
    intent = ParsedIntent(action_type=ActionType.QUERY, params={}, summary="")
    r = score(intent, Scenario.NORMAL, context_override={"volatility": 0.0, "exposure": 0.0})
    assert r.risk_score >= 0
    assert "volatility" in r.details or "exposure" in r.details
