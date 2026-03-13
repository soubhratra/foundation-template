---
phase: 26
slug: organization-model-per-org-billing
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-12
---

# Phase 26 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property               | Value                                                            |
| ---------------------- | ---------------------------------------------------------------- |
| **Framework**          | pytest 7.x + pytest-django                                       |
| **Config file**        | `apps/api/pytest.ini`                                            |
| **Quick run command**  | `cd apps/api && python -m pytest apps/orgs/ apps/billing/ -x -q` |
| **Full suite command** | `cd apps/api && python -m pytest -x -q`                          |
| **Estimated runtime**  | ~45 seconds                                                      |

---

## Sampling Rate

- **After every task commit:** Run `cd apps/api && python -m pytest apps/orgs/ apps/billing/ -x -q`
- **After every plan wave:** Run `cd apps/api && python -m pytest -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 45 seconds

---

## Per-Task Verification Map

| Task ID  | Plan | Wave | Requirement | Test Type   | Automated Command                                                                                       | File Exists | Status     |
| -------- | ---- | ---- | ----------- | ----------- | ------------------------------------------------------------------------------------------------------- | ----------- | ---------- |
| 26-01-01 | 01   | 1    | ORG-01      | unit        | `cd apps/api && python -m pytest apps/orgs/tests/test_models.py -x -q`                                  | ❌ W0       | ⬜ pending |
| 26-01-02 | 01   | 1    | ORG-02      | integration | `cd apps/api && python -m pytest apps/orgs/tests/test_api.py::test_org_scoping -x -q`                   | ❌ W0       | ⬜ pending |
| 26-01-03 | 01   | 1    | ORG-03      | integration | `cd apps/api && python -m pytest apps/orgs/tests/test_api.py::test_invite_flow -x -q`                   | ❌ W0       | ⬜ pending |
| 26-02-01 | 02   | 1    | ORG-04      | integration | `cd apps/api && python -m pytest apps/orgs/tests/test_api.py::test_role_management -x -q`               | ❌ W0       | ⬜ pending |
| 26-03-01 | 03   | 2    | BILL-01     | integration | `cd apps/api && python -m pytest apps/billing/tests/test_org_billing.py -x -q`                          | ❌ W0       | ⬜ pending |
| 26-03-02 | 03   | 2    | BILL-02     | integration | `cd apps/api && python -m pytest apps/billing/tests/test_org_billing.py::test_cache_invalidation -x -q` | ❌ W0       | ⬜ pending |
| 26-04-01 | 04   | 2    | ORG-05      | integration | `cd apps/api && python -m pytest apps/orgs/tests/test_api.py::test_ownership_transfer -x -q`            | ❌ W0       | ⬜ pending |

_Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky_

---

## Wave 0 Requirements

- [ ] `apps/orgs/tests/__init__.py` — test package init
- [ ] `apps/orgs/tests/test_models.py` — stubs for ORG-01 (Organization, OrgMembership, OrgInvitation models)
- [ ] `apps/orgs/tests/test_api.py` — stubs for ORG-02, ORG-03, ORG-04, ORG-05 (org scoping, invite flow, role management, ownership transfer)
- [ ] `apps/billing/tests/test_org_billing.py` — stubs for BILL-01, BILL-02 (has_org_feature, webhook cache invalidation)
- [ ] `apps/orgs/tests/conftest.py` — shared fixtures: `org_factory`, `membership_factory`, `invitation_factory`

---

## Manual-Only Verifications

| Behavior                  | Requirement | Why Manual                              | Test Instructions                                                |
| ------------------------- | ----------- | --------------------------------------- | ---------------------------------------------------------------- |
| Email invitation delivery | ORG-03      | Requires live SMTP/email service        | Send invite, verify email received in test inbox                 |
| Stripe webhook reception  | BILL-02     | Requires live Stripe webhook forwarding | Use `stripe listen --forward-to` and trigger subscription update |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 45s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
