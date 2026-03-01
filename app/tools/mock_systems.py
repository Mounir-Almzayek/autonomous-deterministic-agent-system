"""
Mock systems for Sandbox execution (Phase 4).
Simulated external systems: execute, query, approve, reject, escalate.
Deterministic outputs for validator consistency and hallucination checks.
No real side effects; state is in-memory only for rollback simulation.
"""
from __future__ import annotations

import uuid
from typing import Any

from app.models import ActionType, ParsedIntent

# In-memory log of "applied" ops for rollback. Sandbox appends here; rollback clears.
_MOCK_APPLIED_OPS: list[dict[str, Any]] = []

# Deterministic mock id prefix for traceability (validator can allow this).
MOCK_ID_PREFIX = "mock_"


def _mock_id() -> str:
    """Deterministic-ish id for mock responses (same intent => same id per run pattern)."""
    return f"{MOCK_ID_PREFIX}{uuid.uuid4().hex[:12]}"


def _base_output(intent: ParsedIntent) -> dict[str, Any]:
    """Echo intent params + standard mock fields. Validator checks no extra invented fields."""
    return {
        "action_type": intent.action_type.value,
        "params_echo": dict(intent.params),
        "mock_id": _mock_id(),
        "status": "simulated",
        "summary": intent.summary[:500] if intent.summary else "",
    }


def execute_mock(intent: ParsedIntent) -> dict[str, Any]:
    """Simulate execute action (e.g. trade, order). Returns deterministic output."""
    out = _base_output(intent)
    out["executed"] = True
    out["result"] = "simulated_execution_ok"
    return out


def query_mock(intent: ParsedIntent) -> dict[str, Any]:
    """Simulate query (read-only). Returns deterministic mock data."""
    out = _base_output(intent)
    out["executed"] = False
    out["result"] = "simulated_query_ok"
    out["data"] = {"rows": 0, "params_used": list(intent.params.keys())}
    return out


def approve_mock(intent: ParsedIntent) -> dict[str, Any]:
    """Simulate approve action."""
    out = _base_output(intent)
    out["executed"] = True
    out["result"] = "simulated_approve_ok"
    return out


def reject_mock(intent: ParsedIntent) -> dict[str, Any]:
    """Simulate reject action."""
    out = _base_output(intent)
    out["executed"] = True
    out["result"] = "simulated_reject_ok"
    return out


def escalate_mock(intent: ParsedIntent) -> dict[str, Any]:
    """Simulate escalate (e.g. to human)."""
    out = _base_output(intent)
    out["executed"] = True
    out["result"] = "simulated_escalate_ok"
    out["escalation_id"] = _mock_id()
    return out


def unknown_mock(intent: ParsedIntent) -> dict[str, Any]:
    """Simulate unknown action type (treat as query-like)."""
    out = _base_output(intent)
    out["executed"] = False
    out["result"] = "simulated_unknown_ok"
    return out


_ACTION_HANDLERS: dict[ActionType, Any] = {
    ActionType.EXECUTE: execute_mock,
    ActionType.QUERY: query_mock,
    ActionType.APPROVE: approve_mock,
    ActionType.REJECT: reject_mock,
    ActionType.ESCALATE: escalate_mock,
    ActionType.UNKNOWN: unknown_mock,
}


def run_mock_action(intent: ParsedIntent) -> dict[str, Any]:
    """
    Dispatch intent to the correct mock system. Deterministic per intent.
    Returns output dict for Validator to check (consistency, hallucination).
    """
    handler = _ACTION_HANDLERS.get(intent.action_type, unknown_mock)
    return handler(intent)


def record_applied_op(op: dict[str, Any]) -> None:
    """Record an op for rollback. Called by sandbox."""
    _MOCK_APPLIED_OPS.append(op)


def get_applied_ops() -> list[dict[str, Any]]:
    """Return current list of applied ops (for sandbox to pass to result and rollback)."""
    return list(_MOCK_APPLIED_OPS)


def clear_applied_ops() -> None:
    """Rollback: clear applied ops. Called by sandbox on rollback."""
    _MOCK_APPLIED_OPS.clear()
