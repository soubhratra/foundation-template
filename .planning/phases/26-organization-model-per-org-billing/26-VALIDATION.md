---
phase: 26
slug: organization-model-per-org-billing
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-12
audited: 2026-03-13
---

# Phase 26 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property               | Value                                                           |
| ---------------------- | --------------------------------------------------------------- |
| **Framework**          | pytest 7.x + pytest-django                                      |
| **Config file**        | `apps/api/pytest.ini`                                           |
| **Quick run command**  | `cd apps/api && uv run pytest tests/orgs/ tests/billing/ -x -q` |
| **Full suite command** | `cd apps/api && uv run pytest -x -q`                            |
| **Estimated runtime**  | ~65 seconds (97 tests)                                          |

---

## Sampling Rate

- **After every task commit:** Run `cd apps/api && uv run pytest tests/orgs/ tests/billing/ -x -q`
- **After every plan wave:** Run `cd apps/api && uv run pytest -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 65 seconds

---

## Per-Task Verification Map

| Task ID  | Plan | Wave | Requirement | Test Type   | Automated Command                                                                                                                       | File Exists | Status   |
| -------- | ---- | ---- | ----------- | ----------- | --------------------------------------------------------------------------------------------------------------------------------------- | ----------- | -------- |
| 26-01-01 | 01   | 1    | ORG-01      | unit        | `cd apps/api && uv run pytest tests/orgs/test_models.py tests/orgs/test_services.py::test_create_org_creates_owner_membership -x -q`    | ✅          | ✅ green |
| 26-01-02 | 01   | 1    | ORG-02      | unit+int    | `cd apps/api && uv run pytest tests/orgs/test_services.py tests/orgs/test_models.py::test_invitation_is_valid_false_after_expiry -x -q` | ✅          | ✅ green |
| 26-01-03 | 01   | 1    | ORG-03      | unit        | `cd apps/api && uv run pytest tests/orgs/test_permissions.py -x -q`                                                                     | ✅          | ✅ green |
| 26-02-01 | 02   | 1    | ORG-04      | unit        | `cd apps/api && uv run pytest tests/orgs/test_services.py::test_transfer_ownership -x -q`                                               | ✅          | ✅ green |
| 26-03-01 | 03   | 2    | BILL-01     | unit        | `cd apps/api && uv run pytest tests/orgs/test_models.py::test_org_customer_auto_created -x -q`                                          | ✅          | ✅ green |
| 26-03-02 | 03   | 2    | BILL-02     | unit+int    | `cd apps/api && uv run pytest tests/billing/test_tasks.py tests/core/test_entitlements.py -x -q`                                        | ✅          | ✅ green |
| 26-04-01 | 04   | 2    | ORG-05      | integration | `cd apps/api && uv run pytest tests/orgs/test_controllers.py::test_cross_org_access_forbidden -x -q`                                    | ✅          | ✅ green |

_Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky_

> **Note:** Tests were placed in `apps/api/tests/orgs/` and `apps/api/tests/billing/` (centralized test directory), not the per-app `apps/orgs/tests/` paths originally planned in Wave 0. Both conventions are valid; the actual location is authoritative.

---

## Wave 0 Requirements

- [x] `apps/api/tests/orgs/__init__.py` — test package init
- [x] `apps/api/tests/orgs/test_models.py` — ORG-01 (slug uniqueness), BILL-01 (OrgCustomer auto-create), ORG-02 (invitation expiry)
- [x] `apps/api/tests/orgs/test_services.py` — ORG-01 (create_org owner membership), ORG-02 (invite flow), ORG-04 (transfer_ownership)
- [x] `apps/api/tests/orgs/test_permissions.py` — ORG-03 (IsOrgMember 404, IsOrgAdmin 403)
- [x] `apps/api/tests/orgs/test_controllers.py` — ORG-05 (cross-org access 404)
- [x] `apps/api/tests/billing/test_tasks.py` — BILL-02 (org cache invalidation)
- [x] `apps/api/tests/core/test_entitlements.py` — BILL-02 (has_org_feature)

---

## Manual-Only Verifications

| Behavior                  | Requirement | Why Manual                              | Test Instructions                                                |
| ------------------------- | ----------- | --------------------------------------- | ---------------------------------------------------------------- |
| Email invitation delivery | ORG-03      | Requires live SMTP/email service        | Send invite, verify email received in test inbox                 |
| Stripe webhook reception  | BILL-02     | Requires live Stripe webhook forwarding | Use `stripe listen --forward-to` and trigger subscription update |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 65s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** ✅ Nyquist-compliant (audited 2026-03-13)

---

## Validation Audit 2026-03-13

| Metric     | Count                                                                     |
| ---------- | ------------------------------------------------------------------------- |
| Gaps found | 0                                                                         |
| Resolved   | 0                                                                         |
| Escalated  | 0                                                                         |
| Tests run  | 97 passed, 1 skipped                                                      |
| Note       | Tests at `tests/orgs/` + `tests/billing/` (centralized), not per-app dirs |
