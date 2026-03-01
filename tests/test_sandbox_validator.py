"""
Phase 4: Sandbox & Validator unit tests.
"""
import pytest

from app.core.sandbox import run as sandbox_run, rollback
from app.core.validator import validate
from app.models import (
    ActionType,
    ParsedIntent,
    SandboxResult,
    Scenario,
    ValidationResult,
)


@pytest.fixture(autouse=True)
def clear_sandbox_ops():
    """Clear applied ops before each test for isolation."""
    rollback()
    yield
    rollback()


def test_sandbox_run_dry_run():
    intent = ParsedIntent(
        action_type=ActionType.QUERY,
        params={"symbol": "BTC"},
        summary="Get price",
    )
    result = sandbox_run(intent, Scenario.NORMAL, dry_run=True)
    assert result.success is True
    assert result.dry_run is True
    assert result.error_code is None
    assert "action_type" in result.output
    assert result.output["action_type"] == "query"
    assert result.output.get("params_echo") == {"symbol": "BTC"}
    assert result.output.get("mock_id", "").startswith("mock_")
    assert len(result.applied_ops) >= 1


def test_sandbox_run_execute():
    intent = ParsedIntent(
        action_type=ActionType.EXECUTE,
        params={"ticker": "AAPL", "quantity": 100},
        summary="Buy 100 AAPL",
    )
    result = sandbox_run(intent, Scenario.LOW_RISK, dry_run=False)
    assert result.success is True
    assert result.output.get("executed") is True
    assert result.output.get("params_echo") == {"ticker": "AAPL", "quantity": 100}


def test_validator_pass():
    intent = ParsedIntent(
        action_type=ActionType.QUERY,
        params={"id": "1"},
        summary="Query 1",
    )
    sandbox_result = sandbox_run(intent, Scenario.NORMAL, dry_run=True)
    validation = validate(intent, sandbox_result)
    assert isinstance(validation, ValidationResult)
    assert validation.passed is True
    assert validation.pass_detail is not None
    assert "consistency_action_type" in validation.pass_detail.checks_passed


def test_validator_fail_consistency():
    """Validator should fail when sandbox output action_type does not match intent."""
    intent = ParsedIntent(
        action_type=ActionType.EXECUTE,
        params={"x": 1},
        summary="Execute",
    )
    # Tampered output: action_type mismatch
    sandbox_result = SandboxResult(
        success=True,
        dry_run=True,
        output={
            "action_type": "query",  # wrong
            "params_echo": {"x": 1},
            "mock_id": "mock_abc123",
            "status": "simulated",
            "summary": "Execute",
        },
        applied_ops=[],
    )
    validation = validate(intent, sandbox_result)
    assert validation.passed is False
    assert validation.fail_detail is not None
    assert "consistency" in validation.fail_detail.failed_check or "action_type" in validation.fail_detail.reason


def test_validator_fail_sandbox_failed():
    intent = ParsedIntent(action_type=ActionType.QUERY, params={}, summary="")
    sandbox_result = SandboxResult(
        success=False,
        dry_run=True,
        output={},
        applied_ops=[],
        error_code="SANDBOX_ERROR",
        error_message="Mock failure",
    )
    validation = validate(intent, sandbox_result)
    assert validation.passed is False
    assert validation.fail_detail.failed_check == "sandbox_success"


def test_rollback_clears_ops():
    intent = ParsedIntent(action_type=ActionType.QUERY, params={"a": 1}, summary="")
    sandbox_run(intent, Scenario.NORMAL, dry_run=True)
    from app.tools.mock_systems import get_applied_ops
    assert len(get_applied_ops()) >= 1
    rollback()
    assert len(get_applied_ops()) == 0
