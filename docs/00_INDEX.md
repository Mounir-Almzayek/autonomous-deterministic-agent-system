# ADAS – دليل المراحل والتوثيق

> **Autonomous Deterministic Agent System**  
> Safe, Resilient, Multi-Scenario AI Agent Execution Engine

---

## هيكل التوثيق


| الملف                                                                                | المحتوى                                           |
| ------------------------------------------------------------------------------------ | ------------------------------------------------- |
| [00_INDEX.md](00_INDEX.md)                                                           | هذا الملف – فهرس المراحل والتقدم                  |
| [01_ARCHITECTURE_OVERVIEW.md](01_ARCHITECTURE_OVERVIEW.md)                           | نظرة معمارية، مكونات النظام، تدفق البيانات        |
| [02_PHASE_01_SETUP_AND_INPUT.md](02_PHASE_01_SETUP_AND_INPUT.md)                     | المرحلة 1: Setup & Input Handling – Intent Parser |
| [03_PHASE_02_POLICY_ENGINE.md](03_PHASE_02_POLICY_ENGINE.md)                         | المرحلة 2: Policy Engine                          |
| [04_PHASE_03_RISK_SCORING.md](04_PHASE_03_RISK_SCORING.md)                           | المرحلة 3: Risk Scoring Engine                    |
| [05_PHASE_04_SANDBOX_AND_VALIDATOR.md](05_PHASE_04_SANDBOX_AND_VALIDATOR.md)         | المرحلة 4: Sandbox & Validator                    |
| [06_PHASE_05_EXECUTION_CONTROLLER.md](06_PHASE_05_EXECUTION_CONTROLLER.md)           | المرحلة 5: Execution Controller / Decision Node   |
| [07_PHASE_06_LANGGRAPH_ORCHESTRATION.md](07_PHASE_06_LANGGRAPH_ORCHESTRATION.md)     | المرحلة 6: LangGraph Orchestration                |
| [08_PHASE_07_LOGGING_AND_MONITORING.md](08_PHASE_07_LOGGING_AND_MONITORING.md)       | المرحلة 7: Logging & Monitoring Dashboard         |
| [09_PHASE_08_TESTING_AND_DOCUMENTATION.md](09_PHASE_08_TESTING_AND_DOCUMENTATION.md) | المرحلة 8: Testing & Documentation                |


---

## حالة التقدم (Progress Tracker)


| المرحلة                  | الحالة     | الملاحظات                                 |
| ------------------------ | ---------- | ----------------------------------------- |
| 1 – Setup & Input        | ✅ مكتمل   | Intent Parser, Pydantic, FastAPI, POST /v1/parse |
| 2 – Policy Engine        | ✅ مكتمل   | Rules, roles, scenarios, /v1/policy/check |
| 3 – Risk Scoring         | ✅ مكتمل   | Risk score, thresholds, /v1/risk/score   |
| 4 – Sandbox & Validator  | ✅ مكتمل   | Dry-run, validation, mock systems, rollback |
| 5 – Execution Controller | ✅ مكتمل   | Commit/Reject/Escalate, dual confirmation, /v1/decide |
| 6 – LangGraph            | 🔲 لم يبدأ | Graph, nodes, edges                       |
| 7 – Logging & Monitoring | 🔲 لم يبدأ | JSON logs, dashboard                      |
| 8 – Testing & Docs       | 🔲 لم يبدأ | Unit, integration, adversarial            |


**رموز الحالة:** 🔲 لم يبدأ | 🟡 قيد التنفيذ | ✅ مكتمل

---

## هيكلية الريبو (Repo Structure)

```
ADAS/
├── app/
│   ├── api/                # FastAPI endpoints
│   ├── core/                # Nodes: intent_parser, policy_engine, risk_engine,
│   │                        #        validator, execution_controller,
│   │                        #        scenario_manager, sandbox
│   ├── models/              # Pydantic schemas
│   ├── tools/               # Simulated external systems
│   ├── logging/             # Structured logs, audit
│   └── config/              # Configuration
├── tests/                   # Unit & integration tests
├── docker/                  # Dockerfiles, compose
├── docs/                    # هذا المجلد – المراحل والتوثيق
└── README.md
```

---

*آخر تحديث: حسب تقدم المشروع*