"""
FastAPI application entry point - Phase 1, 2 & 3.
"""
from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.core.intent_parser import parse
from app.core.policy_engine import evaluate
from app.core.risk_engine import score as risk_score
from app.models import IntentParserResult, ParsedIntent, PolicyResult, RiskScoreResult, Role, Scenario

app = FastAPI(
    title="ADAS",
    description="Autonomous Deterministic Agent System - Safe, Resilient, Multi-Scenario AI Agent Execution Engine",
    version="0.1.0",
)


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
