"""
FastAPI application entry point - Phase 1, 2, 3, 4, 5, 6 & 7.
"""
import os

from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.core.execution_controller import decide
from app.core.intent_parser import parse
from app.core.policy_engine import evaluate
from app.core.risk_engine import score as risk_score
from app.core.sandbox import run as sandbox_run
from app.core.validator import validate as validate_result
from app.models import (
    DecisionResult,
    IntentParserResult,
    ParsedIntent,
    PolicyResult,
    RiskScoreResult,
    Role,
    SandboxResult,
    Scenario,
    ValidationResult,
)

app = FastAPI(
    title="ADAS",
    description="Autonomous Deterministic Agent System - Safe, Resilient, Multi-Scenario AI Agent Execution Engine",
    version="0.1.0",
)


@app.on_event("startup")
def _startup():
    """Optional: enable JSON structured logging when ADAS_JSON_LOGS=1."""
    if os.getenv("ADAS_JSON_LOGS", "").strip() in ("1", "true", "yes"):
        from app.logging import setup_structured_logging
        setup_structured_logging()


class ParseRequest(BaseModel):
    """Request body for /v1/parse."""

    raw: str = Field(..., description="Raw LLM output to parse")
    correlation_id: str | None = Field(None, description="Optional correlation id for tracing")


class PolicyCheckRequest(BaseModel):
    """Request body for /v1/policy/check."""

    intent: ParsedIntent = Field(..., description="Parsed intent from Intent Parser")
    role: Role = Field(..., description="Actor role")
    scenario: Scenario = Field(..., description="Runtime scenario")
    emergency_override: bool = Field(False, description="Apply emergency override if enabled in config")


class RiskScoreRequest(BaseModel):
    """Request body for /v1/risk/score."""

    intent: ParsedIntent = Field(..., description="Parsed intent to score")
    scenario: Scenario = Field(..., description="Runtime scenario")
    context_override: dict[str, float] | None = Field(None, description="Optional volatility/exposure override for testing")


class SandboxRunRequest(BaseModel):
    """Request body for /v1/sandbox/run (Phase 4)."""

    intent: ParsedIntent = Field(..., description="Parsed intent to run in sandbox")
    scenario: Scenario = Field(..., description="Runtime scenario")
    dry_run: bool = Field(True, description="If True, no state changes; applied_ops still recorded for rollback")


class ValidateRequest(BaseModel):
    """Request body for /v1/validate (Phase 4)."""

    intent: ParsedIntent = Field(..., description="Parsed intent")
    sandbox_result: SandboxResult = Field(..., description="Result from sandbox run to validate")


class DecideRequest(BaseModel):
    """Request body for /v1/decide (Phase 5 - Decision Node)."""

    policy_result: PolicyResult = Field(..., description="Result from policy check")
    risk_result: RiskScoreResult = Field(..., description="Result from risk scoring")
    sandbox_result: SandboxResult = Field(..., description="Result from sandbox run")
    validation_result: ValidationResult = Field(..., description="Result from validator")
    confidence: float | None = Field(None, ge=0.0, le=1.0, description="Optional confidence score; below threshold → reject")
    confidence_threshold: float | None = Field(None, ge=0.0, le=1.0, description="Override config; 0 = disabled")
    dual_confirmation_risk_threshold: float | None = Field(None, ge=0.0, le=1.0, description="Override; risk above this → requires_dual_confirmation")
    correlation_id: str | None = Field(None, description="Trace id for audit")


class GraphRunRequest(BaseModel):
    """Request body for /v1/run (Phase 6 - LangGraph pipeline)."""

    raw_llm_output: str = Field(..., description="Raw LLM output to parse and run through the full pipeline")
    role: Role = Field(Role.AGENT, description="Actor role for policy")
    scenario: Scenario = Field(Scenario.NORMAL, description="Initial scenario (can switch in scenario_manager)")
    correlation_id: str | None = Field(None, description="Trace id for audit")
    max_retries: int = Field(2, ge=0, le=10, description="Max validator retry loop count")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ADAS"}


@app.post("/v1/parse", response_model=IntentParserResult)
async def parse_intent(body: ParseRequest):
    """
    Parse raw LLM output into a structured intent (Phase 1 - Intent Parser Node).
    Accepts raw text or JSON; returns ParsedIntent on success or IntentParseError on failure.
    """
    return parse(body.raw, correlation_id=body.correlation_id)


@app.post("/v1/policy/check", response_model=PolicyResult)
async def policy_check(body: PolicyCheckRequest):
    """
    Evaluate intent against policy rules (Phase 2 - Policy Engine).
    Returns allow or deny with reason; every decision is logged for audit.
    """
    return evaluate(
        body.intent,
        body.role,
        body.scenario,
        emergency_override=body.emergency_override,
    )


@app.post("/v1/risk/score", response_model=RiskScoreResult)
async def risk_score_endpoint(body: RiskScoreRequest):
    """
    Compute risk score for intent in scenario (Phase 3 - Risk Scoring).
    Returns score, threshold_breach, escalation_required, and signals for Decision Node.
    """
    return risk_score(
        body.intent,
        body.scenario,
        context_override=body.context_override,
    )


@app.post("/v1/sandbox/run", response_model=SandboxResult)
async def sandbox_run_endpoint(body: SandboxRunRequest):
    """
    Run intent in execution sandbox (Phase 4). Mock systems only; dry_run by default.
    Returns SandboxResult with output and applied_ops for Validator and Decision Node.
    """
    return sandbox_run(body.intent, body.scenario, dry_run=body.dry_run)


@app.post("/v1/validate", response_model=ValidationResult)
async def validate_endpoint(body: ValidateRequest):
    """
    Validate intent + sandbox result (Phase 4). Consistency, hallucination, cross-field checks.
    Returns ValidationResult (pass/fail) for Decision Node.
    """
    return validate_result(body.intent, body.sandbox_result)


@app.post("/v1/decide", response_model=DecisionResult)
async def decide_endpoint(body: DecideRequest):
    """
    Decision Node (Phase 5). Commit / Reject / Escalate from policy, risk, sandbox, validation.
    Returns DecisionResult (outcome, reason, requires_dual_confirmation, suggested_retry). Logged for audit.
    """
    return decide(
        body.policy_result,
        body.risk_result,
        body.sandbox_result,
        body.validation_result,
        confidence=body.confidence,
        confidence_threshold=body.confidence_threshold,
        dual_confirmation_risk_threshold=body.dual_confirmation_risk_threshold,
        correlation_id=body.correlation_id,
    )


@app.get("/v1/metrics")
async def get_metrics():
    """
    Metrics for dashboard (Phase 7). Recent runs and aggregate summary.
    """
    from app.logging.metrics import get_metrics_store

    store = get_metrics_store()
    return {
        "recent_runs": store.get_recent_runs(limit=50),
        "summary": store.get_metrics_summary(),
    }


@app.post("/v1/run")
async def graph_run_endpoint(body: GraphRunRequest):
    """
    Run full ADAS pipeline via LangGraph (Phase 6). Intent -> Policy -> Risk -> Scenario -> Sandbox -> Validator -> Decision.
    Returns final state with decision; traceable execution. Records metrics for dashboard (Phase 7).
    """
    from app.core.graph import get_graph
    from app.logging.audit import record_run_complete

    initial: dict[str, object] = {
        "raw_llm_output": body.raw_llm_output,
        "role": body.role.value,
        "scenario": body.scenario.value,
        "correlation_id": body.correlation_id,
        "retry_count": 0,
        "max_retries": body.max_retries,
    }
    graph = get_graph()
    final = graph.invoke(initial)
    record_run_complete(body.correlation_id, final)
    return final
