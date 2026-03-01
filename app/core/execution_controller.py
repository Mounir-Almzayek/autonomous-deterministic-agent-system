"""
Execution Controller / Decision Node (Phase 5).
Deterministic commit / reject / escalate after Policy, Risk, Sandbox, Validator.
Dual confirmation for high risk, confidence threshold, retry signal, full logging.
"""
from __future__ import annotations

import logging
from typing import Any

from app.config.execution_config import (
    CONFIDENCE_THRESHOLD,
    DUAL_CONFIRMATION_RISK_THRESHOLD,
    RETRYABLE_REASON_PREFIXES,
)
from app.core.sandbox import rollback as sandbox_rollback
from app.models import (
    DecisionOutcome,
    DecisionResult,
    PolicyResult,
    RiskScoreResult,
    SandboxResult,
    ValidationResult,
)

logger = logging.getLogger(__name__)


def _suggest_retry(reason: str) -> bool:
    """True if reason indicates a transient failure suitable for retry."""
    r = (reason or "").lower()
    return any(r.startswith(p) or p in r for p in (p.lower() for p in RETRYABLE_REASON_PREFIXES))


def decide(
    policy_result: PolicyResult | None,
    risk_result: RiskScoreResult | None,
    sandbox_result: SandboxResult | None,
    validation_result: ValidationResult | None,
    *,
    confidence: float | None = None,
    confidence_threshold: float | None = None,
    dual_confirmation_risk_threshold: float | None = None,
    correlation_id: str | None = None,
) -> DecisionResult:
    """
    Decision Node: commit / reject / escalate from all upstream results.
    Deterministic order: policy → validation/sandbox → risk threshold → escalation → confidence → commit.
    """
    conf_thresh = confidence_threshold if confidence_threshold is not None else CONFIDENCE_THRESHOLD
    dual_thresh = dual_confirmation_risk_threshold if dual_confirmation_risk_threshold is not None else DUAL_CONFIRMATION_RISK_THRESHOLD

    # ---- Edge case: missing inputs ----
    if policy_result is None:
        out = DecisionResult(
            outcome=DecisionOutcome.REJECT,
            reason="Missing policy result; cannot proceed",
            details={"missing": "policy_result"},
            correlation_id=correlation_id,
        )
        logger.warning("decision", extra={"outcome": out.outcome.value, "reason": out.reason})
        return out

    if risk_result is None:
        out = DecisionResult(
            outcome=DecisionOutcome.REJECT,
            reason="Missing risk result; cannot proceed",
            details={"missing": "risk_result"},
            correlation_id=correlation_id,
        )
        logger.warning("decision", extra={"outcome": out.outcome.value, "reason": out.reason})
        return out

    if sandbox_result is None:
        out = DecisionResult(
            outcome=DecisionOutcome.REJECT,
            reason="Missing sandbox result; cannot proceed",
            details={"missing": "sandbox_result"},
            correlation_id=correlation_id,
        )
        logger.warning("decision", extra={"outcome": out.outcome.value, "reason": out.reason})
        return out

    if validation_result is None:
        out = DecisionResult(
            outcome=DecisionOutcome.REJECT,
            reason="Missing validation result; cannot proceed",
            details={"missing": "validation_result"},
            correlation_id=correlation_id,
        )
        logger.warning("decision", extra={"outcome": out.outcome.value, "reason": out.reason})
        return out

    # ---- 1) Policy deny → reject ----
    if not policy_result.allowed:
        deny = policy_result.deny
        reason = (deny.reason if deny else "Policy denied")[:1000]
        out = DecisionResult(
            outcome=DecisionOutcome.REJECT,
            reason=reason,
            details={"failed_check": deny.failed_check if deny else "policy", **(deny.details or {})},
            correlation_id=correlation_id,
        )
        logger.info("decision", extra={"outcome": out.outcome.value, "reason": reason, "failed_check": getattr(deny, "failed_check", None)})
        return out

    # ---- 2) Sandbox failure → reject ----
    if not sandbox_result.success:
        reason = (sandbox_result.error_message or sandbox_result.error_code or "Sandbox execution failed")[:1000]
        out = DecisionResult(
            outcome=DecisionOutcome.REJECT,
            reason=reason,
            suggested_retry=_suggest_retry(reason),
            details={"error_code": sandbox_result.error_code},
            correlation_id=correlation_id,
        )
        logger.info("decision", extra={"outcome": out.outcome.value, "reason": reason})
        return out

    # ---- 3) Validation failure → reject + optional rollback ----
    if not validation_result.passed:
        fail = validation_result.fail_detail
        reason = (fail.reason if fail else "Validation failed")[:1000]
        if sandbox_result.applied_ops:
            try:
                sandbox_rollback()
            except Exception as e:
                logger.warning("decision_rollback_failed", extra={"error": str(e)})
        out = DecisionResult(
            outcome=DecisionOutcome.REJECT,
            reason=reason,
            details={"failed_check": fail.failed_check if fail else "validation", **(fail.details if fail else {})},
            correlation_id=correlation_id,
        )
        logger.info("decision", extra={"outcome": out.outcome.value, "reason": reason, "failed_check": getattr(fail, "failed_check", None)})
        return out

    # ---- 4) Risk threshold breach → reject (hard stop) ----
    if risk_result.threshold_breach:
        reason = f"Risk threshold breached (score={risk_result.risk_score:.4f}); reject"
        out = DecisionResult(
            outcome=DecisionOutcome.REJECT,
            reason=reason[:1000],
            details={"risk_score": risk_result.risk_score, "signals": risk_result.signals, "scenario": risk_result.scenario.value},
            correlation_id=correlation_id,
        )
        logger.info("decision", extra={"outcome": out.outcome.value, "reason": reason, "risk_score": risk_result.risk_score})
        return out

    # ---- 5) Escalation required → escalate (human/external review) ----
    if risk_result.escalation_required:
        reason = f"Escalation required (risk_score={risk_result.risk_score:.4f}); human or external review"
        out = DecisionResult(
            outcome=DecisionOutcome.ESCALATE,
            reason=reason[:1000],
            details={"risk_score": risk_result.risk_score, "signals": risk_result.signals},
            correlation_id=correlation_id,
        )
        logger.info("decision", extra={"outcome": out.outcome.value, "reason": reason})
        return out

    # ---- 6) Confidence below threshold → reject ----
    if confidence is not None and conf_thresh > 0 and confidence < conf_thresh:
        reason = f"Confidence {confidence:.4f} below threshold {conf_thresh}; reject"
        out = DecisionResult(
            outcome=DecisionOutcome.REJECT,
            reason=reason[:1000],
            details={"confidence": confidence, "confidence_threshold": conf_thresh},
            correlation_id=correlation_id,
        )
        logger.info("decision", extra={"outcome": out.outcome.value, "reason": reason})
        return out

    # ---- 7) All passed: commit (with optional dual confirmation for high risk) ----
    requires_dual = risk_result.risk_score >= dual_thresh
    if requires_dual:
        reason = f"Commit allowed; dual confirmation required (risk_score={risk_result.risk_score:.4f} >= {dual_thresh})"
    else:
        reason = "All checks passed; commit allowed"

    out = DecisionResult(
        outcome=DecisionOutcome.COMMIT,
        reason=reason[:1000],
        requires_dual_confirmation=requires_dual,
        details={"risk_score": risk_result.risk_score, "scenario": risk_result.scenario.value},
        correlation_id=correlation_id,
    )
    logger.info(
        "decision",
        extra={
            "outcome": out.outcome.value,
            "reason": reason,
            "requires_dual_confirmation": requires_dual,
            "risk_score": risk_result.risk_score,
        },
    )
    return out
