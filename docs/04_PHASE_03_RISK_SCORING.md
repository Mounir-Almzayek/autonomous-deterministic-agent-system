# المرحلة 3 – Risk Scoring Engine

## الهدف

حساب المخاطر المحتملة لأي إجراء قبل التنفيذ (كمّي وقابل للقياس).

---

## المهام (Tasks)

- [x] محاكاة البيانات الخاصة بالسيناريو (مثلاً trading, operations)
- [x] حساب **Risk Score** لكل action
- [x] Decision thresholds لتحديد action escalation

---

## الفيتشرات (Features)

- Financial / operational exposure calculation
- Volatility / scenario sensitivity
- Risk scoring dashboard (للمرحلة 7)

---

## الميزة الرئيسية

تقييم **quantitatively** لمدى أمان الإجراءات قبل تنفيذها.

---

## الملفات ذات الصلة

- `app/core/risk_engine.py`
- `app/tools/` (محاكاة بيانات السيناريو)

---

## الحالة

✅ مكتمل (Risk Engine + mock scenario data + thresholds + POST /v1/risk/score)
