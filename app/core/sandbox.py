"""
Execution Sandbox Node (Phase 4).
Dry-run and mock execution before real commit; auto rollback on failure or explicit rollback.
Runs actions against mock systems only; no side effects on real systems.
"""
from __future__ import annotations

import logging
from typing import Any

from app.models import ParsedIntent, SandboxResult, Scenario
from app.tools.mock_systems import (
    clear_applied_ops,
    get_applied_ops,
    record_applied_op,
    run_mock_action,
)

logger = logging.getLogger(__name__)


def run(
    intent: ParsedIntent,
    scenario: Scenario,
    *,
    dry_run: bool = True,
) -> SandboxResult:
    """
    Execute intent in sandbox (mock systems only). Never touches real systems.
    - dry_run=True: simulate execution, record applied_ops for rollback but do not persist.
    - dry_run=False: same mock execution but applied_ops are recorded for later rollback if validation fails.
    Returns SandboxResult with output and applied_ops for Validator and Decision Node.
    """
    try:
        # Clear any previous run's ops for this sandbox session (optional; caller may want isolated runs)
        clear_applied_ops()

        # Run mock action (deterministic output)
        output = run_mock_action(intent)

        # Record as "applied" for rollback (even in dry_run we track what would have been applied)
        op = {
            "action_type": intent.action_type.value,
            "params": dict(intent.params),
            "output_mock_id": output.get("mock_id"),
            "scenario": scenario.value,
        }
        record_applied_op(op)

        applied_ops = get_applied_ops()

        logger.info(
            "sandbox_run",
            extra={
                "dry_run": dry_run,
                "action_type": intent.action_type.value,
                "scenario": scenario.value,
                "mock_id": output.get("mock_id"),
            },
        )

        return SandboxResult(
            success=True,
            dry_run=dry_run,
            output=output,
            applied_ops=applied_ops,
            error_code=None,
            error_message=None,
        )
    except Exception as e:
        logger.warning("sandbox_run_failed", extra={"action_type": intent.action_type.value, "error": str(e)})
        return SandboxResult(
            success=False,
            dry_run=dry_run,
            output={},
            applied_ops=get_applied_ops(),
            error_code="SANDBOX_EXECUTION_ERROR",
            error_message=str(e)[:2000],
        )


def rollback(applied_ops: list[dict[str, Any]] | None = None) -> None:
    """
    Auto rollback: clear applied ops from mock state. If applied_ops is given, we clear
    our internal list (we don't persist per-op state; clearing is the rollback).
    Call after validation fail or before rejecting commit.
    """
    clear_applied_ops()
    logger.info("sandbox_rollback", extra={"message": "Applied ops cleared (mock state reverted)"})
