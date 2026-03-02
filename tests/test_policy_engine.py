"""
Phase 2: Policy Engine unit tests.
"""
import pytest

from app.core.policy_engine import evaluate
from app.models import ActionType, ParsedIntent, PolicyResult, Role, Scenario


def test_policy_allow_agent_query():
    intent = ParsedIntent(action_type=ActionType.QUERY, params={"id": "1"}, summary="")
    r = evaluate(intent, Role.AGENT, Scenario.NORMAL)
    assert r.allowed is True
    assert r.allow is not None


def test_policy_deny_user_execute():
    intent = ParsedIntent(action_type=ActionType.EXECUTE, params={"qty": 1}, summary="")
    r = evaluate(intent, Role.USER, Scenario.NORMAL)
    assert r.allowed is False
    assert r.deny is not None
    assert "execute" in r.deny.reason.lower() or "not allowed" in r.deny.reason.lower()


def test_policy_allow_admin_execute():
    intent = ParsedIntent(action_type=ActionType.EXECUTE, params={"ticker": "AAPL"}, summary="")
    r = evaluate(intent, Role.ADMIN, Scenario.NORMAL)
    assert r.allowed is True


def test_policy_deny_forbidden_param():
    intent = ParsedIntent(
        action_type=ActionType.QUERY,
        params={"symbol": "BTC", "exec": "rm -rf /"},
        summary="",
    )
    r = evaluate(intent, Role.AGENT, Scenario.NORMAL)
    assert r.allowed is False
    assert r.deny is not None
    assert "forbidden" in r.deny.reason.lower() or "exec" in r.deny.reason.lower()


def test_policy_deny_too_many_param_keys():
    intent = ParsedIntent(
        action_type=ActionType.QUERY,
        params={str(i): i for i in range(101)},
        summary="",
    )
    r = evaluate(intent, Role.AGENT, Scenario.NORMAL, max_param_keys=100)
    assert r.allowed is False
    assert r.deny is not None
    assert "key" in r.deny.reason.lower() or "param" in r.deny.reason.lower()


def test_policy_high_volatility_user_no_execute():
    intent = ParsedIntent(action_type=ActionType.EXECUTE, params={"x": 1}, summary="")
    r = evaluate(intent, Role.USER, Scenario.HIGH_VOLATILITY)
    assert r.allowed is False


def test_policy_maintenance_agent_query_only():
    intent = ParsedIntent(action_type=ActionType.QUERY, params={}, summary="")
    r = evaluate(intent, Role.AGENT, Scenario.MAINTENANCE)
    assert r.allowed is True
    intent_exec = ParsedIntent(action_type=ActionType.EXECUTE, params={}, summary="")
    r2 = evaluate(intent_exec, Role.AGENT, Scenario.MAINTENANCE)
    assert r2.allowed is False
