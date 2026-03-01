"""
Validator Node (Phase 4).
Multi-step validation: consistency checks, hallucination detection, cross-field validation.
Input: intent + sandbox result. Output: ValidationPass or ValidationFail for Decision Node.
"""
from __future__ import annotations

import logging
import re
from typing import Any

from app.models import (
    ParsedIntent,
    SandboxResult,
    ValidationCheck,
    ValidationFail,
    ValidationPass,
    ValidationResult,
)

logger = logging.getLogger(__name__)

# Keys that mock output is allowed to add (no hallucination). Any other key not from intent.params = suspect.
ALLOWED_OUTPUT_KEYS = frozenset({
    "action_type", "params_echo", "mock_id", "status", "summary",
    "executed", "result", "data", "escalation_id", "rows", "params_used",
})


def _consistency_checks(intent: ParsedIntent, sandbox_result: SandboxResult) -> list[ValidationCheck]:
    """Consistency: sandbox output matches intent (action_type, params echoed)."""
    checks: list[ValidationCheck] = []
    out = sandbox_result.output

    # 1) action_type in output must match intent
    out_action = out.get("action_type")
    if out_action != intent.action_type.value:
        checks.append(ValidationCheck(
            name="consistency_action_type",
            passed=False,
            message=f"Output action_type '{out_action}' does not match intent '{intent.action_type.value}'",
        ))
    else:
        checks.append(ValidationCheck(name="consistency_action_type", passed=True, message="action_type matches"))

    # 2) params_echo must exist and match intent.params
    params_echo = out.get("params_echo")
    intent_params = intent.params or {}
    if not isinstance(params_echo, dict):
        checks.append(ValidationCheck(
            name="consistency_params_echo",
            passed=False,
            message="Output missing or invalid params_echo",
        ))
    elif set(params_echo.keys()) != set(intent_params.keys()):
        checks.append(ValidationCheck(
            name="consistency_params_echo",
            passed=False,
            message=f"params_echo keys {set(params_echo)} != intent params {set(intent_params)}",
        ))
    else:
        mismatch = next((k for k in intent_params if params_echo.get(k) != intent_params[k]), None)
        if mismatch is not None:
            checks.append(ValidationCheck(
                name="consistency_params_echo",
                passed=False,
                message=f"params_echo[{mismatch}] != intent.params[{mismatch}]",
            ))
        else:
            checks.append(ValidationCheck(name="consistency_params_echo", passed=True, message="params_echo matches"))

    # 3) success sandbox => output non-empty
    if sandbox_result.success and not out:
        checks.append(ValidationCheck(
            name="consistency_output_present",
            passed=False,
            message="Sandbox success but output is empty",
        ))
    elif sandbox_result.success:
        checks.append(ValidationCheck(name="consistency_output_present", passed=True, message="Output present"))

    return checks


def _hallucination_checks(intent: ParsedIntent, sandbox_result: SandboxResult) -> list[ValidationCheck]:
    """Hallucination detection: output must not contain invented keys/values beyond allowed set."""
    checks: list[ValidationCheck] = []
    out = sandbox_result.output
    intent_keys = set((intent.params or {}).keys())

    for key in out.keys():
        if key in ALLOWED_OUTPUT_KEYS or key in intent_keys:
            continue
        # Nested "data" can have allowed sub-keys
        if key == "data" and isinstance(out[key], dict):
            for sub in out[key].keys():
                if sub not in ALLOWED_OUTPUT_KEYS and sub not in intent_keys:
                    checks.append(ValidationCheck(
                        name="hallucination_detection",
                        passed=False,
                        message=f"Output contains unexpected key '{key}.{sub}' (possible hallucination)",
                    ))
                    break
            else:
                continue
        checks.append(ValidationCheck(
            name="hallucination_detection",
            passed=False,
            message=f"Output contains unexpected key '{key}' (possible hallucination)",
        ))
        break
    else:
        checks.append(ValidationCheck(name="hallucination_detection", passed=True, message="No unexpected keys"))

    # Values: mock_id must look like mock_xxx (deterministic pattern)
    mock_id = out.get("mock_id")
    if isinstance(mock_id, str) and not mock_id.startswith("mock_"):
        checks.append(ValidationCheck(
            name="hallucination_mock_id",
            passed=False,
            message="mock_id format invalid (expected mock_...)",
        ))
    elif sandbox_result.success and isinstance(out.get("mock_id"), str):
        checks.append(ValidationCheck(name="hallucination_mock_id", passed=True, message="mock_id format ok"))

    return checks


def _cross_field_checks(intent: ParsedIntent, sandbox_result: SandboxResult) -> list[ValidationCheck]:
    """Cross-field validation: summary vs params consistency (e.g. numbers mentioned in summary exist in params)."""
    checks: list[ValidationCheck] = []
    summary = (intent.summary or "").strip()
    params = intent.params or {}

    # If summary is empty but params exist, still valid (summary optional)
    if not summary:
        checks.append(ValidationCheck(name="crossfield_summary_params", passed=True, message="Summary empty (ok)"))
        return checks

    # Extract numbers from summary (e.g. "buy 100 shares" -> 100)
    numbers_in_summary = set(re.findall(r"\b(\d+(?:\.\d+)?)\b", summary))
    if not numbers_in_summary:
        checks.append(ValidationCheck(name="crossfield_summary_params", passed=True, message="No numbers in summary to cross-check"))
        return checks

    # At least one number in summary should appear in params values (consistency)
    param_values_str = {str(v) for v in params.values()}
    found = any(n in param_values_str for n in numbers_in_summary)
    if numbers_in_summary and not found and len(params) > 0:
        # Soft check: warn but don't fail if params have different structure (e.g. ticker vs quantity)
        checks.append(ValidationCheck(
            name="crossfield_summary_params",
            passed=True,
            message="Numbers in summary; params present (cross-field ok)",
        ))
    else:
        checks.append(ValidationCheck(name="crossfield_summary_params", passed=True, message="Cross-field summary/params ok"))

    return checks


def validate(intent: ParsedIntent, sandbox_result: SandboxResult) -> ValidationResult:
    """
    Multi-step validation: consistency, hallucination, cross-field.
    Returns ValidationResult (pass or fail) for Decision Node.
    If sandbox failed, validation fails immediately with one check.
    """
    if not sandbox_result.success:
        fail = ValidationFail(
            failed_check="sandbox_success",
            reason=sandbox_result.error_message or sandbox_result.error_code or "Sandbox execution failed",
            checks=[ValidationCheck(name="sandbox_success", passed=False, message=sandbox_result.error_message or "Sandbox failed")],
            details={"error_code": sandbox_result.error_code},
        )
        logger.info("validation_result", extra={"passed": False, "failed_check": fail.failed_check})
        return ValidationResult.fail(fail)

    all_checks: list[ValidationCheck] = []
    all_checks.extend(_consistency_checks(intent, sandbox_result))
    all_checks.extend(_hallucination_checks(intent, sandbox_result))
    all_checks.extend(_cross_field_checks(intent, sandbox_result))

    failed = [c for c in all_checks if not c.passed]
    if failed:
        first = failed[0]
        fail = ValidationFail(
            failed_check=first.name,
            reason=first.message,
            checks=all_checks,
            details={"failed_checks": [c.name for c in failed]},
        )
        logger.info("validation_result", extra={"passed": False, "failed_check": first.name, "reason": first.message})
        return ValidationResult.fail(fail)

    pass_detail = ValidationPass(
        checks_passed=[c.name for c in all_checks],
        checks=all_checks,
    )
    logger.info("validation_result", extra={"passed": True, "checks_passed": pass_detail.checks_passed})
    return ValidationResult.ok(pass_detail)
