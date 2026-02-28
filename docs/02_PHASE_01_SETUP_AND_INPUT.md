# المرحلة 1 – Setup & Input Handling

## الهدف

استقبال مخرجات LLM بشكل موحد وتحويلها إلى خطوات قابلة للتنفيذ (structured actions).

---

## المهام (Tasks)

- [x] إعداد مشروع FastAPI مع هيكل modules واضح
- [x] تعريف **Pydantic schemas** لتوحيد مخرجات الـ LLM
- [x] بناء **Intent Parser Node**:
  - يحول النص إلى structured JSON
  - يتأكد من جميع الحقول المطلوبة
  - يرفض أي output غير صالح أو غامض

---

## الفيتشرات (Features)

- Input validation
- Schema enforcement
- Logging لكل input

---

## الميزة الرئيسية

ضمان **deterministic inputs** من أي LLM.

---

## الملفات ذات الصلة

- `app/core/intent_parser.py`
- `app/models/` (Pydantic schemas)
- `app/api/` (FastAPI skeleton)

---

## الحالة

✅ مكتمل (Intent Parser + Pydantic schemas + POST /v1/parse)
