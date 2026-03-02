# المرحلة 7 – Logging & Monitoring Dashboard

## الهدف

رؤية أداء كل node وكل execution في الوقت الفعلي، مع سجل audit كامل.

---

## المهام (Tasks)

- [x] **Structured logging (JSON)** لكل خطوة
- [x] **Metrics collection:** latency, risk score, success/failure
- [x] **Dashboard:**
  - Streamlit
  - Graphical view لكل execution path
  - Risk & performance charts

---

## الفيتشرات (Features)

- Real-time monitoring
- Historical metrics
- Scenario comparison

---

## الميزة الرئيسية

**Visibility** + **auditing** جاهزة للشركات والـ compliance.

---

## الملفات ذات الصلة

- `app/logging/structured_logger.py` — JSON formatter و log_step
- `app/logging/metrics.py` — MetricsStore (recent runs, summary)
- `app/logging/audit.py` — record_run_complete للـ pipeline
- `dashboard/app.py` — Streamlit dashboard (GET /v1/metrics + charts)
- `GET /v1/metrics` — API للمقاييس والعرض على الـ dashboard

---

## الحالة

✅ مكتمل (JSON logging، metrics، audit، Streamlit dashboard، GET /v1/metrics)
