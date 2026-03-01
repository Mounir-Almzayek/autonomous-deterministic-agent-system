# المرحلة 4 – Sandbox & Validator

## الهدف

تنفيذ الأوامر في بيئة محاكية قبل commit حقيقي، والتحقق من صحة المخرجات.

---

## المهام (Tasks)

- [x] إنشاء **Execution Sandbox**
- [x] اختبار الإجراءات على mock systems
- [x] **Validator Node:**
  - Consistency checks
  - Hallucination detection
  - Cross-field validation

---

## الفيتشرات (Features)

- Dry-run mode
- Auto rollback
- Multi-step validation

---

## الميزة الرئيسية

حماية كاملة من **الأخطاء أو التصرفات غير المرغوبة** قبل التنفيذ الفعلي.

---

## الملفات ذات الصلة

- `app/core/sandbox.py`
- `app/core/validator.py`
- `app/tools/` (mock systems)

---

## الحالة

✅ مكتمل (Sandbox + Validator + mock systems + dry-run + rollback + POST /v1/sandbox/run و /v1/validate)
