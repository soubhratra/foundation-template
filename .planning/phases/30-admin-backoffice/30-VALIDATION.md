---
phase: 30
slug: admin-backoffice
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-13
audited: 2026-03-13
---

# Phase 30 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property               | Value                                                 |
| ---------------------- | ----------------------------------------------------- |
| **Framework**          | pytest + pytest-django                                |
| **Config file**        | `apps/api/pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command**  | `cd apps/api && python -m pytest tests/admin/ -x -q`  |
| **Full suite command** | `cd apps/api && python -m pytest -x -q`               |
| **Estimated runtime**  | ~30 seconds                                           |

---

## Sampling Rate

- **After every task commit:** Run `cd apps/api && python -m pytest tests/admin/ -x -q`
- **After every plan wave:** Run `cd apps/api && python -m pytest -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID  | Plan | Wave | Requirement | Test Type   | Automated Command                                                                                                                                           | File Exists | Status   |
| -------- | ---- | ---- | ----------- | ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- | -------- |
| 30-01-01 | 01   | 0    | ADMIN-01    | unit        | `cd apps/api && python -m pytest tests/admin/test_admin_smoke.py -x -q`                                                                                     | ✅          | ✅ green |
| 30-01-02 | 01   | 0    | ADMIN-01    | unit        | `cd apps/api && python -m pytest tests/admin/test_unfold_config.py -x -q`                                                                                   | ✅          | ✅ green |
| 30-02-01 | 02   | 0    | ADMIN-02    | integration | `cd apps/api && python -m pytest tests/admin/test_hijack.py -x -q`                                                                                          | ✅          | ✅ green |
| 30-02-02 | 02   | 0    | ADMIN-02    | unit        | `cd apps/api && python -m pytest tests/admin/test_hijack.py::test_signal_start_writes_event tests/admin/test_hijack.py::test_signal_end_writes_event -x -q` | ✅          | ✅ green |
| 30-02-03 | 02   | 0    | ADMIN-02    | unit        | `cd apps/api && python -m pytest tests/admin/test_hijack.py::test_impersonator_context_injected_during_hijack -x -q`                                        | ✅          | ✅ green |
| 30-02-04 | 02   | 1    | ADMIN-02    | integration | `cd apps/api && python -m pytest tests/audit/test_controllers.py -x -q`                                                                                     | ✅          | ✅ green |

_Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky_

---

## Wave 0 Requirements

- [x] `tests/admin/__init__.py` — create tests/admin package
- [x] `tests/admin/conftest.py` — staff_user, regular_user, superuser fixtures + admin client
- [x] `tests/admin/test_admin_smoke.py` — ADMIN-01: ModelAdmin subclass inheritance checks (UnfoldModelAdmin)
- [x] `tests/admin/test_unfold_config.py` — ADMIN-01: UNFOLD settings structure validation (sidebar sections)
- [x] `tests/admin/test_hijack.py` — ADMIN-02: permission tests (staff→regular ✓, staff→staff ✗, staff→superuser ✗) + signal tests (start/end events)

_All Wave 0 files created and passing._

---

## Manual-Only Verifications

| Behavior                                                     | Requirement | Why Manual                                              | Test Instructions                                                                                        |
| ------------------------------------------------------------ | ----------- | ------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| Persistent impersonation banner visible on every page        | ADMIN-02    | Browser UI element — no headless test                   | Log in as staff, hijack a user, navigate multiple pages, verify banner persists                          |
| Unfold sidebar renders with correct section labels and icons | ADMIN-01    | Visual/CSS validation — Material Symbols icon rendering | Log into admin, verify sidebar sections: Organizations, API Keys, Webhooks, Audit Log with correct icons |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** 2026-03-13

---

## Validation Audit 2026-03-13

| Metric        | Count                                                                                   |
| ------------- | --------------------------------------------------------------------------------------- |
| Gaps found    | 1 (stale test reference for 30-02-03)                                                   |
| Resolved      | 1 (test exists as `test_impersonator_context_injected_during_hijack` in test_hijack.py) |
| Escalated     | 0                                                                                       |
| Tests passing | 29                                                                                      |
