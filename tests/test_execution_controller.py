"""
Phase 5: Execution Controller (Decision Node) unit tests.
"""
import pytest

from app.core.execution_controller import decide
from app.models import (
    DecisionOutcome,
    PolicyAllow,
    PolicyDeny,
    PolicyResult,
    RiskScoreResult,
    Role,
    SandboxResult,
    Scenario,
    ValidationFail,
    ValidationResult,
    ValidationPass,
)


def _allow() -> PolicyResult:
    return PolicyResult.ok(
        PolicyAllow(reason="ok", checks_passed=[], role=Role.AGENT, scenario=Scenario.NORMAL)
    )


def _risk(risk_score=0.3, threshold_breach=False, escalation_required=False) -> RiskScoreResult:
    return RiskScoreResult(
        risk_score=risk_score,
        threshold_breach=threshold_breach,
        escalation_required=escalation_required,
        signals=[],
        scenario=Scenario.NORMAL,
        details={},
    )


def _sandbox_ok() -> SandboxResult:
    return SandboxResult(
        success=True,
        dry_run=True,
        output={"action_type": "query", "params_echo": {}, "mock_id": "mock_abc"},
        applied_ops=[],
    )


def _validation_ok() -> ValidationResult:
    return ValidationResult.ok(ValidationPass(checks_passed=["c1"], checks=[]))


def test_decide_commit():
    r = decide(_allow(), _risk(), _sandbox_ok(), _validation_ok())
    assert r.outcome == DecisionOutcome.COMMIT
    assert "commit" in r.reason.lower() or "passed" in r.reason.lower()
    assert r.requires_dual_confirmation is False


def test_decide_reject_policy_deny():
    deny = PolicyResult.fail(
        PolicyDeny(reason="not allowed", failed_check="role", role=Role.USER, scenario=Scenario.NORMAL)
    )
    r = decide(deny, _risk(), _sandbox_ok(), _validation_ok())
    assert r.outcome == DecisionOutcome.REJECT
    assert "not allowed" in r.reason or "denied" in r.reason.lower()


def test_decide_reject_missing_policy():
    r = decide(None, _risk(), _sandbox_ok(), _validation_ok())
    assert r.outcome == DecisionOutcome.REJECT
    assert "policy" in r.reason.lower() or "missing" in r.reason.lower()


def test_decide_reject_sandbox_failed():
    sandbox_fail = SandboxResult(
        success=False, dry_run=True, output={}, applied_ops=[],
        error_code="ERR", error_message="Sandbox error",
    )
    r = decide(_allow(), _risk(), sandbox_fail, _validation_ok())
    assert r.outcome == DecisionOutcome.REJECT
    assert "sandbox" in r.reason.lower() or "ERR" in r.reason


def test_decide_reject_validation_failed():
    validation_fail = ValidationResult.fail(
        ValidationFail(failed_check="consistency", reason="params_echo mismatch", checks=[], details={})
    )
    r = decide(_allow(), _risk(), _sandbox_ok(), validation_fail)
    assert r.outcome == DecisionOutcome.REJECT
    assert "validation" in r.reason.lower() or "mismatch" in r.reason.lower()


def test_decide_reject_threshold_breach():
    risk_breach = _risk(risk_score=0.9, threshold_breach=True, escalation_required=False)
    r = decide(_allow(), risk_breach, _sandbox_ok(), _validation_ok())
    assert r.outcome == DecisionOutcome.REJECT
    assert "threshold" in r.reason.lower() or "breach" in r.reason.lower()


def test_decide_escalate():
    risk_esc = _risk(risk_score=0.65, threshold_breach=False, escalation_required=True)
    r = decide(_allow(), risk_esc, _sandbox_ok(), _validation_ok())
    assert r.outcome == DecisionOutcome.ESCALATE
    assert "escalat" in r.reason.lower()


def test_decide_commit_dual_confirmation():
    risk_high = _risk(risk_score=0.58, threshold_breach=False, escalation_required=False)
    r = decide(_allow(), risk_high, _sandbox_ok(), _validation_ok())
    assert r.outcome == DecisionOutcome.COMMIT
    assert r.requires_dual_confirmation is True


def test_decide_confidence_below_threshold():
    r = decide(
        _allow(), _risk(), _sandbox_ok(), _validation_ok(),
        confidence=0.4, confidence_threshold=0.7,
    )
    assert r.outcome == DecisionOutcome.REJECT
    assert "confidence" in r.reason.lower()


def test_decide_correlation_id():
    r = decide(_allow(), _risk(), _sandbox_ok(), _validation_ok(), correlation_id="trace-123")
    assert r.correlation_id == "trace-123"
