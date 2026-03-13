---
phase: 32
slug: webhook-wiring-invite-url
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-13
---

# Phase 32 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property               | Value                                                                                           |
| ---------------------- | ----------------------------------------------------------------------------------------------- |
| **Framework**          | pytest + pytest-django                                                                          |
| **Config file**        | `apps/api/pytest.ini`                                                                           |
| **Quick run command**  | `cd apps/api && python -m pytest tests/orgs/test_services.py tests/billing/test_tasks.py -x -q` |
| **Full suite command** | `cd apps/api && python -m pytest -x -q`                                                         |
| **Estimated runtime**  | ~30 seconds                                                                                     |

---

## Sampling Rate

- **After every task commit:** Run `cd apps/api && python -m pytest tests/orgs/test_services.py tests/billing/test_tasks.py -x -q`
- **After every plan wave:** Run `cd apps/api && python -m pytest -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID  | Plan | Wave | Requirement     | Test Type | Automated Command                                                                                                                                                                                                                                                  | File Exists | Status     |
| -------- | ---- | ---- | --------------- | --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------- | ---------- |
| 32-01-01 | 01   | 0    | HOOK-01, ORG-02 | unit      | `cd apps/api && python -m pytest tests/orgs/test_services.py tests/billing/test_tasks.py -x -q`                                                                                                                                                                    | ❌ W0       | ⬜ pending |
| 32-01-02 | 01   | 1    | HOOK-01         | unit      | `cd apps/api && python -m pytest tests/orgs/test_services.py::test_add_member_fires_user_created_for_first_org tests/orgs/test_services.py::test_add_member_fires_org_member_added tests/orgs/test_services.py::test_add_member_no_user_created_for_second_org -x` | ✅          | ⬜ pending |
| 32-01-03 | 01   | 1    | HOOK-01         | unit      | `cd apps/api && python -m pytest tests/billing/test_tasks.py::test_subscription_updated_fires_webhook_for_member_orgs -x`                                                                                                                                          | ✅          | ⬜ pending |
| 32-02-01 | 02   | 1    | ORG-02          | unit      | `cd apps/api && python -m pytest tests/orgs/test_services.py::test_invite_accept_url_uses_frontend_url -x`                                                                                                                                                         | ✅          | ⬜ pending |

_Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky_

---

## Wave 0 Requirements

- [ ] `tests/orgs/test_services.py` — add test stubs: `test_add_member_fires_user_created_for_first_org`, `test_add_member_fires_org_member_added`, `test_add_member_no_user_created_for_second_org`, `test_invite_accept_url_uses_frontend_url`
- [ ] `tests/billing/test_tasks.py` — add test stub: `test_subscription_updated_fires_webhook_for_member_orgs`

_(Existing test files exist; new test functions must be added within them. No new files needed.)_

---

## Manual-Only Verifications

| Behavior                                 | Requirement | Why Manual                                    | Test Instructions                                                      |
| ---------------------------------------- | ----------- | --------------------------------------------- | ---------------------------------------------------------------------- |
| Webhook delivery visible in delivery log | HOOK-01     | Requires running server + registered endpoint | Register endpoint, trigger event, check `/api/v1/webhooks/deliveries/` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
