"""
Audit trail for Phase 7.
Records each pipeline step (node, latency, result) for compliance and traceability.
"""
from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from typing import Any, Iterator

from app.logging.metrics import get_metrics_store
from app.logging.structured_logger import log_step

logger = logging.getLogger("adas.audit")


@contextmanager
def record_node(
    node_name: str,
    correlation_id: str | None,
    state_after: dict[str, Any] | None = None,
) -> Iterator[dict[str, float]]:
    """
    Context manager: measure latency and log structured step.
    Yields a dict that the caller can add to (e.g. node_latencies_ms).
    """
    start = time.perf_counter()
    latencies: dict[str, float] = {}
    try:
        yield latencies
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000
        latencies[node_name] = elapsed_ms
        outcome = _outcome_from_state(node_name, state_after)
        log_step(
            logger,
            node_name,
            correlation_id,
            f"node_finished {node_name}",
            latency_ms=elapsed_ms,
            outcome=outcome,
            extra=state_after if state_after else None,
        )


def _outcome_from_state(node_name: str, state: dict[str, Any] | None) -> str | None:
    if not state:
        return None
    if node_name == "intent_parser":
        return "success" if state.get("intent_parse_success") else "fail"
    if node_name == "policy":
        pr = state.get("policy_result") or {}
        return "allow" if pr.get("allowed") else "deny"
    if node_name == "risk":
        rr = state.get("risk_result") or {}
        return "breach" if rr.get("threshold_breach") else "ok"
    if node_name == "validator":
        vr = state.get("validation_result") or {}
        return "pass" if vr.get("passed") else "fail"
    if "decision" in node_name or node_name == "decision":
        dec = state.get("decision") or {}
        return dec.get("outcome")
    return None


def record_run_complete(
    correlation_id: str | None,
    final_state: dict[str, Any],
) -> None:
    """Called when a run finishes; push to metrics store for dashboard."""
    decision = final_state.get("decision") or {}
    outcome = decision.get("outcome", "unknown")
    scenario = final_state.get("scenario", "unknown")
    risk_result = final_state.get("risk_result") or {}
    risk_score = risk_result.get("risk_score")
    reason = decision.get("reason", "")

    # Execution path and latencies from graph (graph stores _node_latencies_ms per node)
    node_latencies_ms: dict[str, float] = dict(final_state.get("_node_latencies_ms") or {})
    nodes_executed = list(node_latencies_ms.keys())

    get_metrics_store().record_run(
        correlation_id=correlation_id,
        outcome=outcome,
        scenario=scenario,
        risk_score=risk_score,
        node_latencies_ms=node_latencies_ms if node_latencies_ms else None,
        nodes_executed=nodes_executed,
        decision_reason=reason,
    )
