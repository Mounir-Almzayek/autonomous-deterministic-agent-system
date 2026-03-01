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


# --- Phase 4: Sandbox & Validator ---


class SandboxResult(BaseModel):
    """
    Result of sandbox execution (dry-run or mock). No real commit until Decision Node commits.
    applied_ops used for auto rollback if validation fails or on explicit rollback.
    """

    success: bool = Field(..., description="True if mock execution completed without exception")
    dry_run: bool = Field(..., description="True if run was dry-run (no state changes)")
    output: dict[str, Any] = Field(default_factory=dict, description="Simulated output (echo of params + mock ids, etc.)")
    applied_ops: list[dict[str, Any]] = Field(default_factory=list, description="Ops applied in sandbox for rollback")
    error_code: str | None = Field(None, max_length=64, description="Set when success=False")
    error_message: str | None = Field(None, max_length=2000, description="Set when success=False")


class ValidationCheck(BaseModel):
    """Single validation step result (consistency, hallucination, cross-field)."""

    name: str = Field(..., max_length=128)
    passed: bool = Field(...)
    message: str = Field("", max_length=500)


class ValidationPass(BaseModel):
    """All validation checks passed; output is consistent and hallucination-free."""

    checks_passed: list[str] = Field(default_factory=list, description="Names of checks that passed")
    checks: list[ValidationCheck] = Field(default_factory=list)


class ValidationFail(BaseModel):
    """One or more validation checks failed."""

    failed_check: str = Field(..., max_length=128)
    reason: str = Field(..., max_length=1000)
    checks: list[ValidationCheck] = Field(default_factory=list, description="All checks with passed=False for failures")
    details: dict[str, Any] = Field(default_factory=dict)


class ValidationResult(BaseModel):
    """Result of validator node: pass or fail with check details. Used by Decision Node."""

    passed: bool = Field(...)
    pass_detail: ValidationPass | None = None
    fail_detail: ValidationFail | None = None

    @classmethod
    def ok(cls, pass_detail: ValidationPass) -> ValidationResult:
        return cls(passed=True, pass_detail=pass_detail, fail_detail=None)

    @classmethod
    def fail(cls, fail_detail: ValidationFail) -> ValidationResult:
        return cls(passed=False, pass_detail=None, fail_detail=fail_detail)
