"""
Phase 7: Logging & Metrics unit tests.
"""
import pytest

from app.logging.metrics import MetricsStore, get_metrics_store


def test_metrics_store_record_and_recent():
    store = MetricsStore(max_runs=10)
    store.record_run(
        correlation_id="c1",
        outcome="commit",
        scenario="normal",
        risk_score=0.3,
        node_latencies_ms={"intent_parser": 1.0, "policy": 0.5},
        nodes_executed=["intent_parser", "policy", "decision"],
        decision_reason="ok",
    )
    runs = store.get_recent_runs(limit=5)
    assert len(runs) == 1
    assert runs[0]["outcome"] == "commit"
    assert runs[0]["risk_score"] == 0.3
    assert "intent_parser" in runs[0]["node_latencies_ms"]


def test_metrics_summary_aggregates():
    store = MetricsStore(max_runs=20)
    for i in range(5):
        store.record_run(
            correlation_id=f"c{i}",
            outcome="commit" if i % 2 == 0 else "reject",
            scenario="normal",
            risk_score=0.2 + i * 0.1,
            node_latencies_ms={"policy": 1.0 + i},
            nodes_executed=[],
        )
    summary = store.get_metrics_summary()
    assert summary["total_runs"] == 5
    assert summary["by_outcome"]["commit"] == 3
    assert summary["by_outcome"]["reject"] == 2
    assert summary["avg_risk_score"] is not None
    assert "policy" in summary["avg_latency_by_node"]


def test_metrics_store_fifo_cap():
    store = MetricsStore(max_runs=3)
    for i in range(5):
        store.record_run(
            correlation_id=f"c{i}",
            outcome="commit",
            scenario="normal",
            risk_score=0.0,
            nodes_executed=[],
        )
    runs = store.get_recent_runs(limit=10)
    assert len(runs) == 3
