"""
Stress testing: multiple sequential runs to verify stability and metrics.
"""
import pytest

from app.core.graph import get_graph


@pytest.mark.slow
def test_many_sequential_runs():
    """Run pipeline 50 times sequentially; no crash, outcomes consistent."""
    graph = get_graph()
    raw = '{"action_type":"query","params":{"id":"1"},"summary":"stress"}'
    outcomes = []
    for i in range(50):
        final = graph.invoke({
            "raw_llm_output": raw,
            "role": "agent",
            "scenario": "normal",
            "retry_count": 0,
            "max_retries": 2,
        })
        outcomes.append(final.get("decision", {}).get("outcome"))
    assert all(o in ("commit", "reject", "escalate") for o in outcomes)
    assert len(outcomes) == 50
