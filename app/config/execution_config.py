"""
Execution Controller config (Phase 5).
Thresholds for dual confirmation, confidence, and retry behaviour.
"""
from __future__ import annotations

# Risk score above this → commit still allowed but requires_dual_confirmation=True.
DUAL_CONFIRMATION_RISK_THRESHOLD: float = 0.55

# Optional confidence from upstream (0..1). Below this → reject or escalate.
CONFIDENCE_THRESHOLD: float = 0.0  # 0 = disabled; set e.g. 0.7 to enforce.

# When reject reason is in this set, suggested_retry=True (orchestrator may retry).
RETRYABLE_REASON_PREFIXES: tuple[str, ...] = (
    "transient",
    "timeout",
    "temporarily",
    "retry",
)

# Max retries the orchestrator should attempt when suggested_retry is True (hint only).
MAX_RETRIES_HINT: int = 2
