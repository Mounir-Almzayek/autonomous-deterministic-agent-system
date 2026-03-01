# المرحلة 6 – LangGraph Orchestration

## الهدف

تحويل كل الخطوات إلى **Graph Nodes** مع branching و loops و retry و scenario handling.

---

## المهام (Tasks)

- [x] Node لكل module (Intent, Policy, Risk, Validator, Execution, Scenario Manager)
- [x] **Edge conditions:**
  - success → next node
  - fail → retry / escalation node
- [x] Multi-agent readiness: إضافة agents جديدة بسهولة

---

## الفيتشرات (Features)

- Conditional branching
- Retry loops
- Scenario switching
- Multi-agent orchestration support

---

## الميزة الرئيسية

تسهيل **الصيانة والتوسع** + **execution traceable** عبر الـ graph.

---

## الملفات ذات الصلة

- `app/core/graph.py` — StateGraph، تعريف الـ nodes والـ conditional edges والـ retry loop
- `app/core/scenario_manager.py` — Scenario Manager node (resolve scenario من إشارات الـ risk)
- `app/core/` — بقية الـ nodes (intent_parser، policy_engine، risk_engine، sandbox، validator، execution_controller)

---

## الحالة

✅ مكتمل (StateGraph، nodes، conditional edges، retry loop، scenario_manager، POST /v1/run)
