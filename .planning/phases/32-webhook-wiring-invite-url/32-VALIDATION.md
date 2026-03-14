---
phase: 32
slug: webhook-wiring-invite-url
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-13
audited: 2026-03-13
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

| Task ID  | Plan | Wave | Requirement     | Test Type | Automated Command                                                                                                                                                                                                                                                  | File Exists | Status   |
| -------- | ---- | ---- | --------------- | --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------- | -------- |
| 32-01-01 | 01   | 0    | HOOK-01, ORG-02 | unit      | `cd apps/api && python -m pytest tests/orgs/test_services.py tests/billing/test_tasks.py -x -q`                                                                                                                                                                    | ✅          | ✅ green |
| 32-01-02 | 01   | 1    | HOOK-01         | unit      | `cd apps/api && python -m pytest tests/orgs/test_services.py::test_add_member_fires_user_created_for_first_org tests/orgs/test_services.py::test_add_member_fires_org_member_added tests/orgs/test_services.py::test_add_member_no_user_created_for_second_org -x` | ✅          | ✅ green |
| 32-01-03 | 01   | 1    | HOOK-01         | unit      | `cd apps/api && python -m pytest tests/billing/test_tasks.py::test_subscription_updated_fires_webhook_for_member_orgs -x`                                                                                                                                          | ✅          | ✅ green |
| 32-02-01 | 02   | 1    | ORG-02          | unit      | `cd apps/api && python -m pytest tests/orgs/test_services.py::test_invite_accept_url_uses_frontend_url -x`                                                                                                                                                         | ✅          | ✅ green |

_Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky_

---

## Wave 0 Requirements

- [x] `tests/orgs/test_services.py` — add test stubs: `test_add_member_fires_user_created_for_first_org`, `test_add_member_fires_org_member_added`, `test_add_member_no_user_created_for_second_org`, `test_invite_accept_url_uses_frontend_url`
- [x] `tests/billing/test_tasks.py` — add test stub: `test_subscription_updated_fires_webhook_for_member_orgs`

_(All tests exist and are green. 20 total tests pass in 23s.)_

---

## Manual-Only Verifications

| Behavior                                 | Requirement | Why Manual                                    | Test Instructions                                                      |
| ---------------------------------------- | ----------- | --------------------------------------------- | ---------------------------------------------------------------------- |
| Webhook delivery visible in delivery log | HOOK-01     | Requires running server + registered endpoint | Register endpoint, trigger event, check `/api/v1/webhooks/deliveries/` |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s (23s actual)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** 2026-03-13 — 5 named tests green, 20 total passing

---

## Validation Audit 2026-03-13

| Metric     | Count |
| ---------- | ----- |
| Gaps found | 0     |
| Resolved   | 0     |
| Escalated  | 0     |
