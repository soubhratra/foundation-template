---
phase: 22
slug: rbac
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-12
audited: 2026-03-12
---

# Phase 22 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property               | Value                                                   |
| ---------------------- | ------------------------------------------------------- |
| **Framework**          | pytest 8.0+ with pytest-django 4.9+                     |
| **Config file**        | `apps/api/pyproject.toml` (`[tool.pytest.ini_options]`) |
| **Quick run command**  | `cd apps/api && python -m pytest tests/accounts/ -x -q` |
| **Full suite command** | `cd apps/api && python -m pytest -x -q`                 |
| **Estimated runtime**  | ~15 seconds                                             |

---

## Sampling Rate

- **After every task commit:** Run `cd apps/api && python -m pytest tests/accounts/ -x -q`
- **After every plan wave:** Run `cd apps/api && python -m pytest -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID  | Plan | Wave | Requirement               | Test Type        | Automated Command                                                                        | File Exists | Status   |
| -------- | ---- | ---- | ------------------------- | ---------------- | ---------------------------------------------------------------------------------------- | ----------- | -------- |
| 22-01-01 | 01   | 0    | RBAC-01, RBAC-02, RBAC-03 | unit/integration | `cd apps/api && python -m pytest tests/accounts/test_rbac.py -x -q`                      | ✅          | ✅ green |
| 22-02-01 | 02   | 1    | RBAC-01                   | unit             | `cd apps/api && python -m pytest tests/accounts/test_rbac.py::TestRequireRole -x`        | ✅          | ✅ green |
| 22-02-02 | 02   | 1    | RBAC-03                   | integration      | `cd apps/api && python -m pytest tests/accounts/test_rbac.py::TestSeedRolesMigration -x` | ✅          | ✅ green |
| 22-03-01 | 03   | 2    | RBAC-02                   | unit             | `cd apps/api && python -m pytest tests/accounts/test_rbac.py::TestAdminController -x`    | ✅          | ✅ green |

_Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky_

---

## Wave 0 Requirements

- [x] `tests/accounts/test_rbac.py` — RBAC-01/02/03 (14 tests: TestRequireRole×3, TestAdminController×8, TestSeedRolesMigration×3)
- [x] `tests/accounts/conftest.py` — fixtures in place

_Existing pytest + pytest-django infrastructure — no framework install required._

---

## Manual-Only Verifications

_All phase behaviors have automated verification._

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 15s (actual: 12.39s for 14 tests)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** ✅ 2026-03-12 — 14/14 tests passing, no manual-only

---

## Validation Audit 2026-03-12

| Metric        | Count |
| ------------- | ----- |
| Gaps found    | 0     |
| Resolved      | 0     |
| Escalated     | 0     |
| Tests run     | 14    |
| Tests passing | 14    |
