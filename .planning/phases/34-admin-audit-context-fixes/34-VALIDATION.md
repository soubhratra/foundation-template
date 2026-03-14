---
phase: 34
slug: admin-audit-context-fixes
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-13
---

# Phase 34 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property               | Value                                                                |
| ---------------------- | -------------------------------------------------------------------- |
| **Framework**          | pytest + pytest-django                                               |
| **Config file**        | `apps/api/pyproject.toml`                                            |
| **Quick run command**  | `cd apps/api && python -m pytest tests/admin/ tests/api_keys/ -x -q` |
| **Full suite command** | `cd apps/api && python -m pytest -x -q`                              |
| **Estimated runtime**  | ~30 seconds                                                          |

---

## Sampling Rate

- **After every task commit:** Run `cd apps/api && python -m pytest tests/admin/ tests/api_keys/ -x -q`
- **After every plan wave:** Run `cd apps/api && python -m pytest -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID  | Plan | Wave | Requirement | Test Type   | Automated Command                                                                | File Exists | Status     |
| -------- | ---- | ---- | ----------- | ----------- | -------------------------------------------------------------------------------- | ----------- | ---------- |
| 34-01-01 | 01   | 0    | BILL-01     | unit        | `pytest tests/admin/test_admin_smoke.py -x -q -k orgcustomer`                    | ❌ W0       | ⬜ pending |
| 34-01-02 | 01   | 0    | BILL-01     | unit        | `pytest tests/admin/test_unfold_config.py -x -q`                                 | ❌ W0       | ⬜ pending |
| 34-01-03 | 01   | 1    | BILL-01     | unit        | `pytest tests/admin/test_admin_smoke.py tests/admin/test_unfold_config.py -x -q` | ✅ after W0 | ⬜ pending |
| 34-02-01 | 02   | 0    | AUDIT-01    | integration | `pytest tests/api_keys/test_controllers.py -x -q -k audit`                       | ❌ W0       | ⬜ pending |
| 34-02-02 | 02   | 1    | AUDIT-01    | integration | `pytest tests/api_keys/test_controllers.py -x -q`                                | ✅ after W0 | ⬜ pending |
| 34-02-03 | 02   | 1    | AUDIT-01    | integration | `pytest tests/api_keys/test_controllers.py -x -q -k audit`                       | ✅ after W0 | ⬜ pending |

_Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky_

---

## Wave 0 Requirements

- [ ] `tests/admin/test_admin_smoke.py` — add `test_org_customer_admin_inherits_unfold` and `test_org_customer_admin_list_display` for BILL-01
- [ ] `tests/admin/test_unfold_config.py` — add sidebar link test for `admin:orgs_orgcustomer_changelist` for BILL-01
- [ ] `tests/api_keys/test_controllers.py` — add audit log integration tests for AUDIT-01 (create + revoke emit events visible in org audit log)

_No new test files needed — existing test files cover all domains; tests are additions to existing files._

---

## Manual-Only Verifications

| Behavior                                                | Requirement | Why Manual                         | Test Instructions                                                       |
| ------------------------------------------------------- | ----------- | ---------------------------------- | ----------------------------------------------------------------------- |
| OrgCustomer appears in django-unfold sidebar in browser | BILL-01     | Sidebar rendering requires browser | Login as staff → check B2B section → confirm "Org Billing" link present |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
