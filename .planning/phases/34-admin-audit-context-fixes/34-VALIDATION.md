---
phase: 34
slug: admin-audit-context-fixes
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-13
validated: 2026-03-14
---

# Phase 34 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property               | Value                                                             |
| ---------------------- | ----------------------------------------------------------------- |
| **Framework**          | pytest + pytest-django                                            |
| **Config file**        | `apps/api/pyproject.toml`                                         |
| **Quick run command**  | `cd apps/api && uv run pytest tests/admin/ tests/api_keys/ -x -q` |
| **Full suite command** | `cd apps/api && uv run pytest -x -q`                              |
| **Estimated runtime**  | ~30 seconds                                                       |

---

## Sampling Rate

- **After every task commit:** Run `cd apps/api && uv run pytest tests/admin/ tests/api_keys/ -x -q`
- **After every plan wave:** Run `cd apps/api && uv run pytest -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID  | Plan | Wave | Requirement | Test Type   | Automated Command                                                                | File Exists | Status   |
| -------- | ---- | ---- | ----------- | ----------- | -------------------------------------------------------------------------------- | ----------- | -------- |
| 34-01-01 | 01   | 0    | BILL-01     | unit        | `pytest tests/admin/test_admin_smoke.py -x -q -k orgcustomer`                    | ✅          | ✅ green |
| 34-01-02 | 01   | 0    | BILL-01     | unit        | `pytest tests/admin/test_unfold_config.py -x -q`                                 | ✅          | ✅ green |
| 34-01-03 | 01   | 1    | BILL-01     | unit        | `pytest tests/admin/test_admin_smoke.py tests/admin/test_unfold_config.py -x -q` | ✅          | ✅ green |
| 34-02-01 | 02   | 0    | AUDIT-01    | integration | `pytest tests/api_keys/test_controllers.py -x -q -k audit`                       | ✅          | ✅ green |
| 34-02-02 | 02   | 1    | AUDIT-01    | integration | `pytest tests/api_keys/test_controllers.py -x -q`                                | ✅          | ✅ green |
| 34-02-03 | 02   | 1    | AUDIT-01    | integration | `pytest tests/api_keys/test_controllers.py -x -q -k audit`                       | ✅          | ✅ green |

_Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky_

---

## Wave 0 Requirements

- [x] `tests/admin/test_admin_smoke.py` — `test_org_customer_admin_inherits_unfold` and `test_org_customer_admin_list_display` added for BILL-01
- [x] `tests/admin/test_unfold_config.py` — `test_unfold_sidebar_has_org_billing_link` added for BILL-01
- [x] `tests/api_keys/test_controllers.py` — 4 AUDIT-01 integration tests added: `test_create_key_with_org_slug`, `test_create_key_event_in_audit_log`, `test_revoke_key_event_in_audit_log`, `test_create_key_without_org_slug_still_works`

_All Wave 0 requirements fulfilled. No new test files created — additions to existing files only._

---

## Manual-Only Verifications

| Behavior                                                | Requirement | Why Manual                         | Test Instructions                                                       |
| ------------------------------------------------------- | ----------- | ---------------------------------- | ----------------------------------------------------------------------- |
| OrgCustomer appears in django-unfold sidebar in browser | BILL-01     | Sidebar rendering requires browser | Login as staff → check B2B section → confirm "Org Billing" link present |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** ✅ 2026-03-14 — 26 tests green (11 admin + 11 api_keys controllers), 0 gaps

---

## Validation Audit 2026-03-14

| Metric     | Count |
| ---------- | ----- |
| Gaps found | 0     |
| Resolved   | 0     |
| Escalated  | 0     |

All 6 requirements in the Per-Task Map were already covered by tests added during TDD execution (plans 01 and 02). Full run: 26 passed, 0 failed.
