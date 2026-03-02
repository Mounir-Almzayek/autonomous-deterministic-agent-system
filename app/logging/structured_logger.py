"""
Structured JSON logging (Phase 7).
Every log line is a single JSON object for easy parsing and audit.
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any


class JSONFormatter(logging.Formatter):
    """Format log records as single-line JSON for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        # Merge extra from record (e.g. node, correlation_id, latency_ms)
        if hasattr(record, "node"):
            log_obj["node"] = record.node
        if hasattr(record, "correlation_id"):
            log_obj["correlation_id"] = record.correlation_id
        if hasattr(record, "latency_ms"):
            log_obj["latency_ms"] = record.latency_ms
        if hasattr(record, "outcome"):
            log_obj["outcome"] = record.outcome
        for k, v in record.__dict__.items():
            if k not in ("name", "msg", "args", "created", "filename", "funcName", "levelname", "levelno", "lineno", "module", "msecs", "pathname", "process", "processName", "relativeCreated", "stack_info", "exc_info", "message", "taskName", "node", "correlation_id", "latency_ms", "outcome"):
                if v is not None:
                    log_obj[k] = v
        return json.dumps(log_obj, default=str)


def setup_structured_logging(
    level: int = logging.INFO,
    stream: Any = None,
) -> None:
    """Configure root logger to use JSON formatter. Call once at app startup."""
    if stream is None:
        stream = sys.stdout
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JSONFormatter())
    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(level)


def log_step(
    logger: logging.Logger,
    node: str,
    correlation_id: str | None,
    message: str,
    *,
    latency_ms: float | None = None,
    outcome: str | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    """Emit a structured audit log for one pipeline step."""
    log_extra: dict[str, Any] = {"node": node, "correlation_id": correlation_id}
    if latency_ms is not None:
        log_extra["latency_ms"] = round(latency_ms, 2)
    if outcome is not None:
        log_extra["outcome"] = outcome
    if extra:
        log_extra.update(extra)
    logger.info(message, extra=log_extra)
