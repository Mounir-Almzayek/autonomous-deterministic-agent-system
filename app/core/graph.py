"""
LangGraph orchestration (Phase 6).
StateGraph: Intent -> Policy -> Risk -> Scenario -> Sandbox -> Validator -> Decision.
Conditional branching, retry loop on validation fail, scenario switching.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Callable, Literal, TypedDict

from app.config.execution_config import MAX_RETRIES_HINT
from app.logging.structured_logger import log_step as _log_step
from app.core.execution_controller import decide
from app.core.intent_parser import parse
from app.core.policy_engine import evaluate
from app.core.risk_engine import score as risk_score
from app.core.sandbox import run as sandbox_run
from app.core.scenario_manager import resolve as scenario_resolve
from app.core.validator import validate
from app.models import (
    DecisionOutcome,
    DecisionResult,
    ParsedIntent,
    PolicyResult,
    RiskScoreResult,
    Role,
    SandboxResult,
    Scenario,
    ValidationResult,
)

logger = logging.getLogger(__name__)

# --- State schema (serializable for checkpointing / multi-agent) ---


class ADASState(TypedDict, total=False):
    """State passed between graph nodes. All keys optional except initial input."""

    raw_llm_output: str
    role: str
    scenario: str
    correlation_id: str | None
    parsed_intent: dict[str, Any]
    intent_parse_success: bool
    policy_result: dict[str, Any]
    risk_result: dict[str, Any]
    sandbox_result: dict[str, Any]
    validation_result: dict[str, Any]
    decision: dict[str, Any]
    retry_count: int
    max_retries: int
    _node_latencies_ms: dict[str, float]


def _role(s: ADASState) -> Role:
    return Role(s.get("role", "agent"))


def _scenario(s: ADASState) -> Scenario:
    return Scenario(s.get("scenario", "normal"))


def _wrap_node(name: str, fn: Callable[[ADASState], dict[str, Any]]) -> Callable[[ADASState], dict[str, Any]]:
    """Wrap a node to record latency and structured audit log."""

    def wrapped(state: ADASState) -> dict[str, Any]:
        start = time.perf_counter()
        out = fn(state)
        elapsed_ms = (time.perf_counter() - start) * 1000
        merged = dict(state.get("_node_latencies_ms") or {})
        merged[name] = round(elapsed_ms, 2)
        out["_node_latencies_ms"] = merged
        _log_step(
            logger,
            name,
            state.get("correlation_id"),
            f"node_finished {name}",
            latency_ms=elapsed_ms,
            outcome=out.get("outcome"),
            extra={k: v for k, v in (out or {}).items() if k != "_node_latencies_ms"},
        )
        return out

    return wrapped


# --- Graph nodes (each receives state, returns partial state update) ---


def node_intent_parser(state: ADASState) -> dict[str, Any]:
    """Parse raw LLM output -> ParsedIntent or error."""
    raw = state.get("raw_llm_output") or ""
    cid = state.get("correlation_id")
    result = parse(raw, correlation_id=cid)
    if result.success and result.intent:
        return {
            "parsed_intent": result.intent.model_dump(mode="json"),
            "intent_parse_success": True,
        }
    return {"parsed_intent": None, "intent_parse_success": False}


def node_policy(state: ADASState) -> dict[str, Any]:
    """Evaluate policy for parsed intent."""
    pi = state.get("parsed_intent")
    if not pi:
        return {}
    intent = ParsedIntent.model_validate(pi)
    policy_result = evaluate(intent, _role(state), _scenario(state))
    return {"policy_result": policy_result.model_dump(mode="json")}


def node_risk(state: ADASState) -> dict[str, Any]:
    """Compute risk score for intent in scenario."""
    pi = state.get("parsed_intent")
    if not pi:
        return {}
    intent = ParsedIntent.model_validate(pi)
    risk_result = risk_score(intent, _scenario(state))
    return {"risk_result": risk_result.model_dump(mode="json")}


def node_scenario_manager(state: ADASState) -> dict[str, Any]:
    """Resolve effective scenario (optional switch from risk signals)."""
    scenario = _scenario(state)
    risk_dict = state.get("risk_result")
    risk_result = RiskScoreResult.model_validate(risk_dict) if risk_dict else None
    resolved = scenario_resolve(scenario, risk_result=risk_result)
    return {"scenario": resolved.value}


def node_sandbox(state: ADASState) -> dict[str, Any]:
    """Run intent in sandbox (dry-run)."""
    pi = state.get("parsed_intent")
    if not pi:
        return {}
    intent = ParsedIntent.model_validate(pi)
    scenario = _scenario(state)
    sandbox_result = sandbox_run(intent, scenario, dry_run=True)
    return {"sandbox_result": sandbox_result.model_dump(mode="json")}


def node_validator(state: ADASState) -> dict[str, Any]:
    """Validate intent + sandbox result."""
    pi = state.get("parsed_intent")
    sb = state.get("sandbox_result")
    if not pi or not sb:
        return {}
    intent = ParsedIntent.model_validate(pi)
    sandbox_result = SandboxResult.model_validate(sb)
    validation_result = validate(intent, sandbox_result)
    return {"validation_result": validation_result.model_dump(mode="json")}


def node_decision(state: ADASState) -> dict[str, Any]:
    """Decision Node: commit / reject / escalate from all results."""
    policy_dict = state.get("policy_result")
    risk_dict = state.get("risk_result")
    sandbox_dict = state.get("sandbox_result")
    validation_dict = state.get("validation_result")
    policy = PolicyResult.model_validate(policy_dict) if policy_dict else None
    risk = RiskScoreResult.model_validate(risk_dict) if risk_dict else None
    sandbox = SandboxResult.model_validate(sandbox_dict) if sandbox_dict else None
    validation = ValidationResult.model_validate(validation_dict) if validation_dict else None
    decision_result = decide(
        policy, risk, sandbox, validation,
        correlation_id=state.get("correlation_id"),
    )
    return {"decision": decision_result.model_dump(mode="json")}


def node_decision_after_intent_fail(state: ADASState) -> dict[str, Any]:
    """Synthetic decision when intent parse failed: reject with reason."""
    decision_result = DecisionResult(
        outcome=DecisionOutcome.REJECT,
        reason="Intent parse failed; cannot proceed",
        details={"intent_parse_success": False},
        correlation_id=state.get("correlation_id"),
    )
    return {"decision": decision_result.model_dump(mode="json")}


def node_decision_after_policy_deny(state: ADASState) -> dict[str, Any]:
    """Decision using only policy result (deny); risk/sandbox/validation not run."""
    policy_dict = state.get("policy_result")
    policy = PolicyResult.model_validate(policy_dict) if policy_dict else None
    decision_result = decide(
        policy, None, None, None,
        correlation_id=state.get("correlation_id"),
    )
    return {"decision": decision_result.model_dump(mode="json")}


def node_decision_after_risk_over(state: ADASState) -> dict[str, Any]:
    """Decision when risk over threshold; sandbox/validator skipped."""
    policy_dict = state.get("policy_result")
    risk_dict = state.get("risk_result")
    policy = PolicyResult.model_validate(policy_dict) if policy_dict else None
    risk = RiskScoreResult.model_validate(risk_dict) if risk_dict else None
    decision_result = decide(
        policy, risk, None, None,
        correlation_id=state.get("correlation_id"),
    )
    return {"decision": decision_result.model_dump(mode="json")}


# --- Conditional routing ---


def route_after_intent(state: ADASState) -> Literal["policy", "decision"]:
    if state.get("intent_parse_success"):
        return "policy"
    return "decision"


def route_after_policy(state: ADASState) -> Literal["risk", "decision"]:
    pr = state.get("policy_result")
    if pr and pr.get("allowed"):
        return "risk"
    return "decision"


def route_after_risk(state: ADASState) -> Literal["scenario_manager", "decision"]:
    rr = state.get("risk_result")
    if not rr:
        return "scenario_manager"
    if rr.get("threshold_breach") or rr.get("escalation_required"):
        return "decision"
    return "scenario_manager"


def route_after_validator(state: ADASState) -> Literal["decision", "increment_retry"]:
    vr = state.get("validation_result")
    if not vr or vr.get("passed"):
        return "decision"
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", MAX_RETRIES_HINT)
    # Check if validation fail suggests retry (e.g. transient); we don't have decision yet, so use validation details
    fail_detail = (vr.get("fail_detail") or {}) if isinstance(vr, dict) else {}
    reason = (fail_detail.get("reason") or "").lower()
    suggested_retry = "transient" in reason or "timeout" in reason or "retry" in reason
    if suggested_retry and retry_count < max_retries:
        return "increment_retry"
    return "decision"


def node_increment_retry(state: ADASState) -> dict[str, Any]:
    """Increment retry count before re-entering sandbox (retry loop)."""
    n = state.get("retry_count", 0) + 1
    return {"retry_count": n}


# --- Build graph ---


def build_graph():
    """Build and compile the ADAS StateGraph. Multi-agent ready: add nodes/edges as needed."""
    from langgraph.graph import END, START, StateGraph

    builder = StateGraph(ADASState)

    builder.add_node("intent_parser", _wrap_node("intent_parser", node_intent_parser))
    builder.add_node("policy", _wrap_node("policy", node_policy))
    builder.add_node("risk", _wrap_node("risk", node_risk))
    builder.add_node("scenario_manager", _wrap_node("scenario_manager", node_scenario_manager))
    builder.add_node("sandbox", _wrap_node("sandbox", node_sandbox))
    builder.add_node("validator", _wrap_node("validator", node_validator))
    builder.add_node("decision", _wrap_node("decision", node_decision))
    builder.add_node("decision_after_intent_fail", _wrap_node("decision_after_intent_fail", node_decision_after_intent_fail))
    builder.add_node("decision_after_policy_deny", _wrap_node("decision_after_policy_deny", node_decision_after_policy_deny))
    builder.add_node("decision_after_risk_over", _wrap_node("decision_after_risk_over", node_decision_after_risk_over))
    builder.add_node("increment_retry", _wrap_node("increment_retry", node_increment_retry))

    builder.add_edge(START, "intent_parser")
    builder.add_conditional_edges("intent_parser", route_after_intent, {"policy": "policy", "decision": "decision_after_intent_fail"})
    builder.add_conditional_edges("policy", route_after_policy, {"risk": "risk", "decision": "decision_after_policy_deny"})
    builder.add_conditional_edges("risk", route_after_risk, {"scenario_manager": "scenario_manager", "decision": "decision_after_risk_over"})
    builder.add_edge("scenario_manager", "sandbox")
    builder.add_edge("sandbox", "validator")
    builder.add_conditional_edges("validator", route_after_validator, {"decision": "decision", "increment_retry": "increment_retry"})
    builder.add_edge("increment_retry", "sandbox")
    builder.add_edge("decision", END)
    builder.add_edge("decision_after_intent_fail", END)
    builder.add_edge("decision_after_policy_deny", END)
    builder.add_edge("decision_after_risk_over", END)

    return builder.compile()


# Lazy singleton for reuse
_compiled_graph = None


def get_graph():
    """Return compiled ADAS graph. Thread-safe compile-once."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph
