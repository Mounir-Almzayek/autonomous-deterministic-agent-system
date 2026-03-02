"""
Metrics collection for Phase 7 (Logging & Monitoring).
Stores run-level and step-level metrics: latency, risk score, success/failure, scenario.
In-memory store with optional file persistence for historical dashboard.
"""
from __future__ import annotations

import json
import threading
from collections import deque
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Max in-memory runs to keep (FIFO). Increase or use file for long history.
MAX_RUNS_IN_MEMORY = 500


class MetricsStore:
    """Thread-safe in-memory store of execution runs and step metrics."""

    def __init__(self, max_runs: int = MAX_RUNS_IN_MEMORY, persist_path: Path | str | None = None):
        self._max_runs = max_runs
        self._persist_path = Path(persist_path) if persist_path else None
        self._runs: deque[dict[str, Any]] = deque(maxlen=max_runs)
        self._lock = threading.Lock()

    def record_run(
        self,
        correlation_id: str | None,
        outcome: str,
        scenario: str,
        risk_score: float | None = None,
        node_latencies_ms: dict[str, float] | None = None,
        nodes_executed: list[str] | None = None,
        decision_reason: str | None = None,
    ) -> None:
        """Append one full run (after decision node)."""
        with self._lock:
            record = {
                "ts": datetime.now(UTC).isoformat(),
                "correlation_id": correlation_id or "",
                "outcome": outcome,
                "scenario": scenario,
                "risk_score": risk_score,
                "node_latencies_ms": node_latencies_ms or {},
                "nodes_executed": nodes_executed or [],
                "decision_reason": (decision_reason or "")[:500],
            }
            self._runs.append(record)
            if self._persist_path:
                self._append_to_file(record)

    def _append_to_file(self, record: dict[str, Any]) -> None:
        try:
            with open(self._persist_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, default=str) + "\n")
        except OSError:
            pass

    def get_recent_runs(self, limit: int = 100) -> list[dict[str, Any]]:
        """Return most recent runs (newest first)."""
        with self._lock:
            runs = list(self._runs)
        runs.reverse()
        return runs[:limit]

    def get_metrics_summary(self) -> dict[str, Any]:
        """Aggregate: total runs, success/fail counts, avg risk, avg latency by node, by scenario."""
        with self._lock:
            runs = list(self._runs)
        if not runs:
            return {"total_runs": 0, "by_outcome": {}, "by_scenario": {}, "avg_risk_score": None, "avg_latency_by_node": {}}

        by_outcome: dict[str, int] = {}
        by_scenario: dict[str, int] = {}
        risk_sum = 0.0
        risk_count = 0
        latency_by_node: dict[str, list[float]] = {}

        for r in runs:
            o = r.get("outcome") or "unknown"
            by_outcome[o] = by_outcome.get(o, 0) + 1
            s = r.get("scenario") or "unknown"
            by_scenario[s] = by_scenario.get(s, 0) + 1
            if r.get("risk_score") is not None:
                risk_sum += r["risk_score"]
                risk_count += 1
            for node, ms in (r.get("node_latencies_ms") or {}).items():
                latency_by_node.setdefault(node, []).append(ms)

        avg_risk = risk_sum / risk_count if risk_count else None
        avg_latency_by_node = {n: sum(v) / len(v) for n, v in latency_by_node.items() if v}

        return {
            "total_runs": len(runs),
            "by_outcome": by_outcome,
            "by_scenario": by_scenario,
            "avg_risk_score": round(avg_risk, 4) if avg_risk is not None else None,
            "avg_latency_by_node": {k: round(v, 2) for k, v in avg_latency_by_node.items()},
        }

    def load_from_file(self) -> None:
        """Load persisted runs from NDJSON file (append to current in-memory)."""
        if not self._persist_path or not self._persist_path.exists():
            return
        with self._lock:
            with open(self._persist_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        self._runs.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass


# Singleton for app-wide use
_metrics_store: MetricsStore | None = None


def get_metrics_store(persist_path: str | Path | None = None) -> MetricsStore:
    global _metrics_store
    if _metrics_store is None:
        _metrics_store = MetricsStore(persist_path=persist_path)
        if persist_path:
            _metrics_store.load_from_file()
    return _metrics_store
