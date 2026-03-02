"""
Integration tests: API endpoints (TestClient).
"""
import pytest
from fastapi.testclient import TestClient

from app.api.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "ok"
    assert "ADAS" in data.get("service", "")


def test_parse_success():
    r = client.post(
        "/v1/parse",
        json={"raw": '{"action_type":"query","params":{},"summary":"test"}'},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert "intent" in data
    assert data["intent"]["action_type"] == "query"


def test_parse_fail():
    r = client.post("/v1/parse", json={"raw": "not json"})
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is False
    assert "error" in data


def test_policy_check_allow():
    r = client.post(
        "/v1/policy/check",
        json={
            "intent": {"action_type": "query", "params": {}, "summary": ""},
            "role": "agent",
            "scenario": "normal",
            "emergency_override": False,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["allowed"] is True


def test_risk_score():
    r = client.post(
        "/v1/risk/score",
        json={
            "intent": {"action_type": "query", "params": {"id": "1"}, "summary": ""},
            "scenario": "normal",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert "risk_score" in data
    assert 0 <= data["risk_score"] <= 1


def test_metrics_empty_or_ok():
    r = client.get("/v1/metrics")
    assert r.status_code == 200
    data = r.json()
    assert "recent_runs" in data
    assert "summary" in data


def test_run_full_pipeline():
    r = client.post(
        "/v1/run",
        json={
            "raw_llm_output": '{"action_type":"query","params":{"id":"1"},"summary":"test"}',
            "role": "agent",
            "scenario": "normal",
            "max_retries": 2,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert "decision" in data
    assert data["decision"]["outcome"] in ("commit", "reject", "escalate")
    assert "reason" in data["decision"]
