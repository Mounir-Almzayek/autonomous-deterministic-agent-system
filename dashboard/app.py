"""
ADAS Monitoring Dashboard (Phase 7).
Streamlit app: real-time runs, execution path view, risk & performance charts, scenario comparison.
Run: streamlit run dashboard/app.py
Requires ADAS API to be running. Set ADAS_API_URL in Docker (e.g. http://api:8000) or use sidebar.
"""
from __future__ import annotations

import os
import streamlit as st

st.set_page_config(page_title="ADAS Monitoring", page_icon="📊", layout="wide")

DEFAULT_API_BASE = os.getenv("ADAS_API_URL", "http://localhost:8000")


def fetch_metrics(api_base: str):
    import json
    import urllib.request
    try:
        req = urllib.request.Request(f"{api_base.rstrip('/')}/v1/metrics")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e), "recent_runs": [], "summary": {}}


st.title("ADAS – Monitoring & Audit")
st.caption("Real-time execution metrics, risk scores, and pipeline visibility")

api_base = st.sidebar.text_input("API base URL", value=DEFAULT_API_BASE).rstrip("/")
if st.sidebar.button("Refresh"):
    st.rerun()

data = fetch_metrics(api_base)

if "error" in data:
    st.error(f"Cannot reach API: {data['error']}. Start the API with: uvicorn app.api.main:app --reload")
    st.stop()

summary = data.get("summary") or {}
runs = data.get("recent_runs") or []

# --- Summary row ---
st.subheader("Summary")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total runs", summary.get("total_runs", 0))
with col2:
    by_outcome = summary.get("by_outcome") or {}
    st.metric("Commit", by_outcome.get("commit", 0))
with col3:
    st.metric("Reject", by_outcome.get("reject", 0))
with col4:
    st.metric("Escalate", by_outcome.get("escalate", 0))
st.metric("Avg risk score", summary.get("avg_risk_score") or "—")

# --- Scenario comparison ---
st.subheader("By scenario")
by_scenario = summary.get("by_scenario") or {}
if by_scenario:
    import pandas as pd
    df_scenario = pd.DataFrame(list(by_scenario.items()), columns=["Scenario", "Count"])
    st.bar_chart(df_scenario.set_index("Scenario"))
else:
    st.info("No scenario data yet.")

# --- Avg latency by node ---
st.subheader("Avg latency by node (ms)")
avg_latency = summary.get("avg_latency_by_node") or {}
if avg_latency:
    import pandas as pd
    df_lat = pd.DataFrame(list(avg_latency.items()), columns=["Node", "Latency (ms)"])
    st.bar_chart(df_lat.set_index("Node"))
else:
    st.info("No latency data yet.")

# --- Recent runs table + execution path ---
st.subheader("Recent runs")
if not runs:
    st.info("No runs yet. Call POST /v1/run to generate traffic.")
else:
    import pandas as pd
    rows = []
    for r in runs:
        rows.append({
            "Time": r.get("ts", "")[:19],
            "Correlation ID": (r.get("correlation_id") or "")[:12],
            "Outcome": r.get("outcome", ""),
            "Scenario": r.get("scenario", ""),
            "Risk score": r.get("risk_score"),
            "Nodes": ", ".join(r.get("nodes_executed") or [])[:50],
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.subheader("Execution path (last run)")
    last = runs[0]
    nodes = last.get("nodes_executed") or []
    path = " → ".join(nodes) if nodes else "—"
    st.code(path, language=None)
    latencies = last.get("node_latencies_ms") or {}
    if latencies:
        st.caption("Latency (ms) per node:")
        st.json(latencies)
