---
phase: 25
slug: gdpr-export-plan-id-accuracy
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-12
---

# Phase 25 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property               | Value                                                              |
| ---------------------- | ------------------------------------------------------------------ |
| **Framework**          | pytest 8.0+ with pytest-django 4.9+                                |
| **Config file**        | `apps/api/pyproject.toml` (`[tool.pytest.ini_options]`)            |
| **Quick run command**  | `cd apps/api && python -m pytest tests/accounts/test_export.py -x` |
| **Full suite command** | `cd apps/api && python -m pytest tests/accounts/ -x`               |
| **Estimated runtime**  | ~5 seconds                                                         |

---

## Sampling Rate

- **After every task commit:** Run `cd apps/api && python -m pytest tests/accounts/test_export.py -x`
- **After every plan wave:** Run `cd apps/api && python -m pytest tests/accounts/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID  | Plan | Wave | Requirement | Test Type | Automated Command                                                  | File Exists        | Status     |
| -------- | ---- | ---- | ----------- | --------- | ------------------------------------------------------------------ | ------------------ | ---------- |
| 25-01-01 | 01   | 0    | GDPR-02     | unit (DB) | `cd apps/api && python -m pytest tests/accounts/test_export.py -x` | ❌ W0 (new method) | ⬜ pending |
| 25-01-02 | 01   | 1    | GDPR-02     | unit (DB) | `cd apps/api && python -m pytest tests/accounts/test_export.py -x` | ✅ (existing file) | ⬜ pending |

_Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky_

---

## Wave 0 Requirements

- [ ] `tests/accounts/test_export.py::TestExportEndpoint::test_export_billing_plan_id_round_trip` — new test method covering GDPR-02 positive plan_id round-trip case

_File exists; only the new test method is missing._

---

## Manual-Only Verifications

_All phase behaviors have automated verification._

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
