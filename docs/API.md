# ADAS API Contracts

API base: `http://localhost:8000` (default). OpenAPI (Swagger): **GET /docs**.

---

## Health

- **GET /health**  
  - Response: `{ "status": "ok", "service": "ADAS" }`

---

## Intent Parser (Phase 1)

- **POST /v1/parse**  
  - Body: `{ "raw": "<string>", "correlation_id": "<optional>" }`  
  - Response: `IntentParserResult` — `success`, `intent` (ParsedIntent) or `error` (IntentParseError)

---

## Policy (Phase 2)

- **POST /v1/policy/check**  
  - Body: `{ "intent": ParsedIntent, "role": "user"|"agent"|"admin"|"system", "scenario": "normal"|"low_risk"|"high_volatility"|"maintenance", "emergency_override": false }`  
  - Response: `PolicyResult` — `allowed`, `allow` or `deny` with reason

---

## Risk (Phase 3)

- **POST /v1/risk/score**  
  - Body: `{ "intent": ParsedIntent, "scenario": "<scenario>", "context_override": { "volatility": 0.3, "exposure": 0.4 } (optional) }`  
  - Response: `RiskScoreResult` — `risk_score` (0–1), `threshold_breach`, `escalation_required`, `signals`, `scenario`, `details`

---

## Sandbox (Phase 4)

- **POST /v1/sandbox/run**  
  - Body: `{ "intent": ParsedIntent, "scenario": "<scenario>", "dry_run": true }`  
  - Response: `SandboxResult` — `success`, `dry_run`, `output`, `applied_ops`, `error_code`/`error_message` on failure

---

## Validator (Phase 4)

- **POST /v1/validate**  
  - Body: `{ "intent": ParsedIntent, "sandbox_result": SandboxResult }`  
  - Response: `ValidationResult` — `passed`, `pass_detail` or `fail_detail` with checks

---

## Decision (Phase 5)

- **POST /v1/decide**  
  - Body: `{ "policy_result", "risk_result", "sandbox_result", "validation_result", "confidence" (optional), "confidence_threshold" (optional), "dual_confirmation_risk_threshold" (optional), "correlation_id" (optional) }`  
  - Response: `DecisionResult` — `outcome` (commit|reject|escalate), `reason`, `requires_dual_confirmation`, `suggested_retry`, `correlation_id`, `details`

---

## Full Pipeline (Phase 6)

- **POST /v1/run**  
  - Body: `{ "raw_llm_output": "<string>", "role": "agent", "scenario": "normal", "correlation_id" (optional), "max_retries": 2 }`  
  - Response: Final state object with `decision`, `parsed_intent`, `policy_result`, `risk_result`, `sandbox_result`, `validation_result`, `_node_latencies_ms`, etc.

---

## Metrics (Phase 7)

- **GET /v1/metrics**  
  - Response: `{ "recent_runs": [ { "ts", "correlation_id", "outcome", "scenario", "risk_score", "node_latencies_ms", "nodes_executed", "decision_reason" }, ... ], "summary": { "total_runs", "by_outcome", "by_scenario", "avg_risk_score", "avg_latency_by_node" } }`
