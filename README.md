# ADAS – Autonomous Deterministic Agent System

> **Tagline:** Safe, Resilient, Multi-Scenario AI Agent Execution Engine

---

## نظرة عامة

**ADAS** نظام يربط بين مخرجات LLM وعمليات تنفيذية آمنة، مع طبقات أمان، إدارة مخاطر، ودعم متعدد السيناريوهات. الهدف: تشغيل **agents آمنة وقادرة على قرارات مستقلة** مع سلوك deterministic و traceability.

---

## المكونات الأساسية


| المكون            | الوصف                                                |
| ----------------- | ---------------------------------------------------- |
| Intent Parser     | تحويل مخرجات LLM إلى JSON structured actions         |
| Policy Engine     | التحقق من الصلاحيات والقواعد (role & scenario-based) |
| Risk Scoring      | حساب المخاطر والانحرافات واعطاء score                |
| Execution Sandbox | تنفيذ محاكى مع دعم rollback                          |
| Validator         | consistency، integrity، hallucination-free           |
| Decision Node     | commit / reject / escalate                           |
| Logging & Audit   | تسجيل كل خطوة ومراجعة وأداء                          |
| Scenario Manager  | إدارة سيناريوهات متعددة واختيار المسار               |
| LangGraph         | ربط الـ nodes في graph مع branching و retry          |


---

## التقنيات

- **Orchestration:** LangGraph  
- **LLM:** OpenAI / Claude / OpenRouter  
- **Backend:** Python, FastAPI (async)  
- **Validation:** Pydantic, JSON schema  
- **Monitoring:** Prometheus/Grafana أو Streamlit

---

## هيكلية المشروع

```
ADAS/
├── app/
│   ├── api/           # FastAPI endpoints
│   ├── core/          # Nodes (intent, policy, risk, validator, execution, scenario, sandbox)
│   ├── models/        # Pydantic schemas
│   ├── tools/         # Simulated external systems
│   ├── logging/       # Structured logs & audit
│   └── config/        # Configuration
├── tests/             # Unit & integration tests
├── docker/            # Docker config
├── docs/              # المراحل، التوثيق، المعمارية
└── README.md
```

---

## المراحل والتقدم

التفاصيل الكاملة لكل مرحلة موجودة في مجلد `**docs/**`:

- `**docs/00_INDEX.md**` – فهرس المراحل وحالة التقدم  
- `**docs/01_ARCHITECTURE_OVERVIEW.md**` – نظرة معمارية  
- `**docs/02_PHASE_01_...**` حتى `**docs/09_PHASE_08_...**` – تفاصيل كل مرحلة

---

## التشغيل (لاحقاً)

```bash
# التبعيات
pip install -r requirements.txt

# تشغيل API
uvicorn app.api.main:app --reload
```

---

## الترخيص

# استخدام تعليمي/ portfolio. تعديل الترخيص حسب الحاجة.

