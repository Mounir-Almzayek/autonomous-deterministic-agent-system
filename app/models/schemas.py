"""
Pydantic schemas for ADAS pipeline.
Unified structures for LLM output → structured actions (Phase 1).
"""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ActionType(str, Enum):
    """Supported action types for deterministic routing."""

    EXECUTE = "execute"
    QUERY = "query"
    APPROVE = "approve"
    REJECT = "reject"
    ESCALATE = "escalate"
    UNKNOWN = "unknown"


class ParsedIntent(BaseModel):
    """
    Structured action parsed from LLM output.
    All required fields enforced for deterministic downstream processing.
    """

    action_type: ActionType = Field(..., description="Type of action to perform")
    params: dict[str, Any] = Field(default_factory=dict, description="Action parameters")
    summary: str = Field("", max_length=2000, description="Short human-readable summary")
    correlation_id: str | None = Field(None, description="Optional correlation id for tracing")
    raw_snippet: str | None = Field(None, max_length=5000, description="Optional snippet of raw input for audit")

    @field_validator("params", mode="before")
    @classmethod
    def ensure_dict(cls, v: Any) -> dict[str, Any]:
        if v is None:
            return {}
        if isinstance(v, dict):
            return v
        if isinstance(v, list):
            return {"items": v}
        return {"value": v}


class IntentParseError(BaseModel):
    """Result when intent parsing fails. No ambiguous or invalid output is passed downstream."""

    error_code: str = Field(..., min_length=1, max_length=64)
    message: str = Field(..., min_length=1, max_length=2000)
    details: dict[str, Any] = Field(default_factory=dict)
    raw_input_preview: str | None = Field(None, max_length=500, description="Safe preview for logs")


class IntentParserResult(BaseModel):
    """Union-like result: either ParsedIntent or IntentParseError."""

    success: bool
    intent: ParsedIntent | None = None
    error: IntentParseError | None = None

    @classmethod
    def ok(cls, intent: ParsedIntent) -> IntentParserResult:
        return cls(success=True, intent=intent, error=None)

    @classmethod
    def fail(cls, error: IntentParseError) -> IntentParserResult:
        return cls(success=False, intent=None, error=error)


# --- Phase 2: Policy Engine ---


class Role(str, Enum):
    """Actor role for policy evaluation."""

    USER = "user"
    AGENT = "agent"
    ADMIN = "admin"
    SYSTEM = "system"


class Scenario(str, Enum):
    """Runtime scenario; rules and thresholds vary per scenario."""

    NORMAL = "normal"
    LOW_RISK = "low_risk"
    HIGH_VOLATILITY = "high_volatility"
    MAINTENANCE = "maintenance"


class PolicyAllow(BaseModel):
    """Policy check passed; action is allowed for this role and scenario."""

    reason: str = Field(..., max_length=500)
    checks_passed: list[str] = Field(default_factory=list, description="Names of checks that passed")
    role: Role = Field(...)
    scenario: Scenario = Field(...)


class PolicyDeny(BaseModel):
    """Policy check failed; action is not allowed."""

    reason: str = Field(..., max_length=500)
    failed_check: str = Field(..., max_length=128)
    details: dict[str, Any] = Field(default_factory=dict)
    role: Role = Field(...)
    scenario: Scenario = Field(...)


class PolicyResult(BaseModel):
    """Result of policy evaluation: either allow or deny (with reason)."""

    allowed: bool
    allow: PolicyAllow | None = None
    deny: PolicyDeny | None = None

    @classmethod
    def ok(cls, allow: PolicyAllow) -> PolicyResult:
        return cls(allowed=True, allow=allow, deny=None)

    @classmethod
    def fail(cls, deny: PolicyDeny) -> PolicyResult:
        return cls(allowed=False, allow=None, deny=deny)


# --- Phase 3: Risk Scoring ---


class RiskScoreResult(BaseModel):
    """
    Quantitative risk assessment for an action in a given scenario.
    risk_score in [0.0, 1.0]; threshold_breach and escalation_required drive Decision Node.
    """

    risk_score: float = Field(..., ge=0.0, le=1.0, description="Normalized risk 0=low, 1=high")
    threshold_breach: bool = Field(..., description="True if score exceeds scenario threshold")
    escalation_required: bool = Field(..., description="True if human or external review required")
    signals: list[str] = Field(default_factory=list, description="Risk factors e.g. high_volatility, execute_action")
    scenario: Scenario = Field(...)
    details: dict[str, Any] = Field(default_factory=dict, description="Exposure, volatility, etc.")
