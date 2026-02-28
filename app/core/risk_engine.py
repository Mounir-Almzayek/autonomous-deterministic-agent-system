"""
Risk Scoring Node (Phase 3).
Computes quantitative risk score per action and scenario; sets threshold_breach and escalation.
Uses mock scenario data (volatility, exposure); deterministic for audit.
"""
from __future__ import annotations

import logging
from typing import Any

from app.config.risk_config import (
    get_escalation_threshold,
    get_max_risk_threshold,
    get_sensitivity,
)
from app.models import ActionType, ParsedIntent, RiskScoreResult, Scenario
from app.tools.scenario_data import get_scenario_context

logger = logging.getLogger(__name__)

# Base risk weight by action type (0=low, 1=high impact). Execute is highest.
_ACTION_BASE_RISK: dict[ActionType, float] = {
    ActionType.EXECUTE: 0.55,
    ActionType.QUERY: 0.12,
    ActionType.APPROVE: 0.45,
    ActionType.REJECT: 0.2,
    ActionType.ESCALATE: 0.35,
    ActionType.UNKNOWN: 0.5,
}

# Max param keys contributing to risk (cap effect).
_PARAM_KEYS_RISK_CAP = 20


def _param_risk(params: dict[str, Any]) -> float:
    """0..1 contribution from params size (more keys = slightly higher risk)."""
    n = min(len(params), _PARAM_KEYS_RISK_CAP)
    return (n / _PARAM_KEYS_RISK_CAP) * 0.2


def score(
    intent: ParsedIntent,
    scenario: Scenario,
    *,
    context_override: dict[str, float] | None = None,
) -> RiskScoreResult:
    """
    Compute risk score for intent in the given scenario.
    Uses scenario sensitivity, mock volatility/exposure, and action type.
    Sets threshold_breach and escalation_required for Decision Node.
    """
    ctx = context_override if context_override is not None else get_scenario_context(scenario)
    volatility = ctx.get("volatility", 0.3)
    exposure = ctx.get("exposure", 0.4)

    base = _ACTION_BASE_RISK.get(intent.action_type, 0.4)
    param_contrib = _param_risk(intent.params)

    # Blend: base + params + scenario context (volatility + exposure)
    raw = base * 0.6 + param_contrib + (volatility * 0.2 + exposure * 0.2)
    sensitivity = get_sensitivity(scenario)
    risk_score = min(1.0, max(0.0, raw * sensitivity))

    max_threshold = get_max_risk_threshold(scenario)
    esc_threshold = get_escalation_threshold(scenario)
    threshold_breach = risk_score > max_threshold
    escalation_required = risk_score > esc_threshold

    signals: list[str] = []
    if intent.action_type == ActionType.EXECUTE:
        signals.append("execute_action")
    if volatility > 0.5:
        signals.append("high_volatility")
    if exposure > 0.5:
        signals.append("elevated_exposure")
    if len(intent.params) > 10:
        signals.append("large_params")
    if threshold_breach:
        signals.append("threshold_breach")
    if escalation_required:
        signals.append("escalation_required")

    details: dict[str, Any] = {
        "volatility": volatility,
        "exposure": exposure,
        "sensitivity": sensitivity,
        "max_threshold": max_threshold,
        "escalation_threshold": esc_threshold,
    }

    result = RiskScoreResult(
        risk_score=round(risk_score, 4),
        threshold_breach=threshold_breach,
        escalation_required=escalation_required,
        signals=signals,
        scenario=scenario,
        details=details,
    )

    logger.info(
        "risk_score",
        extra={
            "risk_score": result.risk_score,
            "threshold_breach": threshold_breach,
            "escalation_required": escalation_required,
            "scenario": scenario.value,
            "action_type": intent.action_type.value,
        },
    )
    return result
