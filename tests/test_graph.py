"""
Phase 6: LangGraph orchestration tests.
"""
import pytest

from app.core.graph import build_graph, get_graph


@pytest.fixture
def graph():
    return get_graph()


def test_graph_invoke_success(graph):
    raw = '{"action_type":"query","params":{"id":"1"},"summary":"test"}'
    initial = {
        "raw_llm_output": raw,
        "role": "agent",
        "scenario": "normal",
        "retry_count": 0,
        "max_retries": 2,
    }
    final = graph.invoke(initial)
    assert "decision" in final
    assert final["decision"]["outcome"] in ("commit", "reject", "escalate")
    assert "reason" in final["decision"]


def test_graph_invoke_intent_fail(graph):
    initial = {
        "raw_llm_output": "not valid json at all",
        "role": "agent",
        "scenario": "normal",
        "retry_count": 0,
        "max_retries": 2,
    }
    final = graph.invoke(initial)
    assert final["decision"]["outcome"] == "reject"
    assert "Intent parse failed" in final["decision"]["reason"]
