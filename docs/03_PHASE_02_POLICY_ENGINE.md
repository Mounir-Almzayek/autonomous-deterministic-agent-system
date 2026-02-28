# المرحلة 2 – Policy Engine

## الهدف

التأكد من أن كل إجراء يتوافق مع قواعد الأمان والصلاحيات قبل المتابعة.

---

## المهام (Tasks)

- [x] بناء قاعدة Rules ديناميكية لكل سيناريو
- [x] **Role-based permissions:** user/agent-level
- [x] **Scenario-based dynamic rules:** مثلاً low-risk, high-volatility
- [x] Logging لكل قرار قبول أو رفض

---

## الفيتشرات (Features)

- Role & scenario aware rules
- Configurable thresholds
- Policy override for emergencies

---

## الميزة الرئيسية

يمنع تنفيذ أي **action غير مصرح به**.

---

## الملفات ذات الصلة

- `app/core/policy_engine.py`
- `app/config/` (قواعد وسيناريوهات)

---

## الحالة

✅ مكتمل (Policy Engine + Role/Scenario rules + POST /v1/policy/check + structured logging)
