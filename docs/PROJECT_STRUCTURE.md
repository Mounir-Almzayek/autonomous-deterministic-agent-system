# هيكلية المشروع – ADAS

هذا الملف يوضح هيكل المجلدات والملفات وربطها بالمراحل.

---

## الشجرة الكاملة

```
ADAS/
├── app/
│   ├── __init__.py
│   ├── api/
│   │   └── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── intent_parser.py      ← Phase 1
│   │   ├── policy_engine.py      ← Phase 2
│   │   ├── risk_engine.py        ← Phase 3
│   │   ├── validator.py          ← Phase 4
│   │   ├── sandbox.py            ← Phase 4
│   │   ├── execution_controller.py ← Phase 5
│   │   ├── scenario_manager.py   ← Phase 6
│   │   └── (langgraph graph)     ← Phase 6
│   ├── models/
│   │   └── __init__.py           ← Phase 1 (schemas)
│   ├── tools/
│   │   └── __init__.py           ← Phase 3, 4 (mock/sim)
│   ├── logging/
│   │   └── __init__.py           ← Phase 7
│   └── config/
│       └── __init__.py           ← Phase 2, 3
├── tests/
│   ├── __init__.py
│   └── conftest.py               ← Phase 8
├── docker/
│   └── .gitkeep                  ← لاحقاً Dockerfile, compose
├── docs/
│   ├── 00_INDEX.md
│   ├── 01_ARCHITECTURE_OVERVIEW.md
│   ├── 02_PHASE_01_SETUP_AND_INPUT.md
│   ├── 03_PHASE_02_POLICY_ENGINE.md
│   ├── 04_PHASE_03_RISK_SCORING.md
│   ├── 05_PHASE_04_SANDBOX_AND_VALIDATOR.md
│   ├── 06_PHASE_05_EXECUTION_CONTROLLER.md
│   ├── 07_PHASE_06_LANGGRAPH_ORCHESTRATION.md
│   ├── 08_PHASE_07_LOGGING_AND_MONITORING.md
│   ├── 09_PHASE_08_TESTING_AND_DOCUMENTATION.md
│   └── PROJECT_STRUCTURE.md
├── README.md
└── requirements.txt
```

---

## ربط الملفات بالمراحل

| المرحلة | الملفات الرئيسية |
|---------|-------------------|
| 1 | `app/core/intent_parser.py`, `app/models/`, `app/api/` |
| 2 | `app/core/policy_engine.py`, `app/config/` |
| 3 | `app/core/risk_engine.py`, `app/tools/` |
| 4 | `app/core/sandbox.py`, `app/core/validator.py`, `app/tools/` |
| 5 | `app/core/execution_controller.py` |
| 6 | كل الـ core nodes + تعريف LangGraph |
| 7 | `app/logging/`, dashboard |
| 8 | `tests/`, `docs/`, `README.md` |

---

*يُحدَّث مع تقدم المشروع.*
