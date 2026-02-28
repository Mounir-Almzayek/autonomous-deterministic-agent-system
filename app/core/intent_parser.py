"""
Intent Parser Node (Phase 1).
Converts LLM output to structured JSON actions; rejects invalid or ambiguous output.
"""
from __future__ import annotations

import json
import re
from typing import Any

from app.models import ActionType, IntentParseError, IntentParserResult, ParsedIntent

# Max length to attempt JSON parse (avoid DoS on huge payloads)
MAX_RAW_LENGTH = 50_000
# Safe preview length for error messages
PREVIEW_LENGTH = 500


def _safe_preview(raw: str) -> str:
    """Return a safe, truncated preview for logs/errors."""
    if not raw or not isinstance(raw, str):
        return ""
    s = raw.strip()[:PREVIEW_LENGTH]
    return s + ("..." if len(raw) > PREVIEW_LENGTH else "")


def parse(raw: str, correlation_id: str | None = None) -> IntentParserResult:
    """
    Parse raw LLM output into a structured ParsedIntent.
    Ensures all required fields are present and valid; rejects invalid or ambiguous output.
    """
    if not isinstance(raw, str):
        return IntentParserResult.fail(
            IntentParseError(
                error_code="INVALID_INPUT_TYPE",
                message="Input must be a string",
                details={"type": type(raw).__name__},
            )
        )

    raw = raw.strip()
    if not raw:
        return IntentParserResult.fail(
            IntentParseError(
                error_code="EMPTY_INPUT",
                message="Empty input cannot be parsed as intent",
                raw_input_preview="",
            )
        )

    if len(raw) > MAX_RAW_LENGTH:
        return IntentParserResult.fail(
            IntentParseError(
                error_code="INPUT_TOO_LONG",
                message=f"Input exceeds maximum length of {MAX_RAW_LENGTH} characters",
                raw_input_preview=_safe_preview(raw),
            )
        )

    # Try to extract JSON (allow wrapped in markdown code blocks)
    data: Any = None
    json_str = raw

    code_block = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    if code_block:
        json_str = code_block.group(1).strip()

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        return IntentParserResult.fail(
            IntentParseError(
                error_code="INVALID_JSON",
                message=str(e.msg) if getattr(e, "msg", None) else "Invalid JSON",
                details={"position": e.pos if getattr(e, "pos", None) else None},
                raw_input_preview=_safe_preview(raw),
            )
        )

    if not isinstance(data, dict):
        return IntentParserResult.fail(
            IntentParseError(
                error_code="ROOT_NOT_OBJECT",
                message="Parsed JSON root must be an object",
                details={"type": type(data).__name__},
                raw_input_preview=_safe_preview(raw),
            )
        )

    # Normalize action_type to enum
    action_type_raw = data.get("action_type")
    if action_type_raw is None or (isinstance(action_type_raw, str) and not action_type_raw.strip()):
        return IntentParserResult.fail(
            IntentParseError(
                error_code="MISSING_ACTION_TYPE",
                message="Required field 'action_type' is missing or empty",
                raw_input_preview=_safe_preview(raw),
            )
        )

    action_type_str = str(action_type_raw).strip().lower()
    try:
        action_type = ActionType(action_type_str)
    except ValueError:
        # Map common variants to enum or UNKNOWN
        if action_type_str in ("trade", "execute_trade", "order"):
            action_type = ActionType.EXECUTE
        elif action_type_str in ("ask", "get", "fetch"):
            action_type = ActionType.QUERY
        else:
            action_type = ActionType.UNKNOWN

    params = data.get("params")
    if params is not None and not isinstance(params, dict):
        return IntentParserResult.fail(
            IntentParseError(
                error_code="INVALID_PARAMS",
                message="Field 'params' must be an object",
                details={"type": type(params).__name__},
                raw_input_preview=_safe_preview(raw),
            )
        )

    summary = data.get("summary")
    if summary is not None and not isinstance(summary, str):
        summary = str(summary)
    summary = (summary or "").strip() or "No summary"

    try:
        intent = ParsedIntent(
            action_type=action_type,
            params=params or {},
            summary=summary[:2000],
            correlation_id=correlation_id or data.get("correlation_id"),
            raw_snippet=raw[:5000] if len(raw) <= 5000 else raw[:4997] + "...",
        )
        return IntentParserResult.ok(intent)
    except Exception as e:
        return IntentParserResult.fail(
            IntentParseError(
                error_code="VALIDATION_ERROR",
                message=str(e),
                details={"exception": type(e).__name__},
                raw_input_preview=_safe_preview(raw),
            )
        )
