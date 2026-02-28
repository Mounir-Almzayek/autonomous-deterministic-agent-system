"""
Policy Engine Node (Phase 2).
Evaluates ParsedIntent against role and scenario rules; allows or denies with reason.
Logs every allow/deny decision for audit.
"""
from __future__ import annotations

import logging
from typing import Any

from app.config.policy_rules import (
    FORBIDDEN_PARAM_KEYS,
    MAX_PARAM_KEYS,
    POLICY_OVERRIDE_FOR_EMERGENCY,
    is_action_allowed,
)
from app.models import (
    ParsedIntent,
    PolicyAllow,
    PolicyDeny,
    PolicyResult,
    Role,
    Scenario,
)

logger = logging.getLogger(__name__)


def _check_param_keys(params: dict[str, Any], max_keys: int) -> tuple[bool, str]:
    """Return (ok, failed_reason)."""
    if len(params) > max_keys:
        return False, f"params has {len(params)} keys; max allowed is {max_keys}"
    return True, ""


def _check_forbidden_keys(params: dict[str, Any]) -> tuple[bool, str]:
    """Return (ok, failed_reason)."""
    keys_lower = {k.lower() for k in params}
    for forbidden in FORBIDDEN_PARAM_KEYS:
        if forbidden in keys_lower:
            return False, f"forbidden param key: {forbidden}"
    return True, ""


def evaluate(
    intent: ParsedIntent,
    role: Role,
    scenario: Scenario,
    *,
    emergency_override: bool = False,
    max_param_keys: int | None = None,
) -> PolicyResult:
    """
    Evaluate intent against policy rules for the given role and scenario.
    Returns PolicyResult (allow or deny with reason). Every decision is logged.
    """
    if max_param_keys is None:
        max_param_keys = MAX_PARAM_KEYS

    if emergency_override and POLICY_OVERRIDE_FOR_EMERGENCY:
        allow = PolicyAllow(
            reason="Emergency policy override active",
            checks_passed=["emergency_override"],
            role=role,
            scenario=scenario,
        )
        logger.info("policy_decision", extra={"allowed": True, "reason": allow.reason, "role": role.value, "scenario": scenario.value})
        return PolicyResult.ok(allow)

    # 1) Role + scenario: is this action_type allowed?
    if not is_action_allowed(scenario, role, intent.action_type):
        deny = PolicyDeny(
            reason=f"Action type '{intent.action_type.value}' is not allowed for role={role.value} in scenario={scenario.value}",
            failed_check="role_scenario_action",
            details={"action_type": intent.action_type.value, "role": role.value, "scenario": scenario.value},
            role=role,
            scenario=scenario,
        )
        logger.info("policy_decision", extra={"allowed": False, "reason": deny.reason, "failed_check": deny.failed_check})
        return PolicyResult.fail(deny)

    # 2) Param key count
    ok_keys, msg_keys = _check_param_keys(intent.params, max_param_keys)
    if not ok_keys:
        deny = PolicyDeny(
            reason=msg_keys,
            failed_check="max_param_keys",
            details={"count": len(intent.params), "max": max_param_keys},
            role=role,
            scenario=scenario,
        )
        logger.info("policy_decision", extra={"allowed": False, "reason": deny.reason, "failed_check": deny.failed_check})
        return PolicyResult.fail(deny)

    # 3) Forbidden param keys
    ok_forbidden, msg_forbidden = _check_forbidden_keys(intent.params)
    if not ok_forbidden:
        deny = PolicyDeny(
            reason=msg_forbidden,
            failed_check="forbidden_param_key",
            details={},
            role=role,
            scenario=scenario,
        )
        logger.info("policy_decision", extra={"allowed": False, "reason": deny.reason, "failed_check": deny.failed_check})
        return PolicyResult.fail(deny)

    allow = PolicyAllow(
        reason=f"All policy checks passed for {intent.action_type.value}",
        checks_passed=["role_scenario_action", "max_param_keys", "forbidden_param_key"],
        role=role,
        scenario=scenario,
    )
    logger.info(
        "policy_decision",
        extra={"allowed": True, "reason": allow.reason, "role": role.value, "scenario": scenario.value, "action_type": intent.action_type.value},
    )
    return PolicyResult.ok(allow)
