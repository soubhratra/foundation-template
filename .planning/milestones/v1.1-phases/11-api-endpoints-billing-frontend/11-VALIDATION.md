---
phase: 11
slug: api-endpoints-billing-frontend
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-08
---

# Phase 11 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property               | Value                                                                     |
| ---------------------- | ------------------------------------------------------------------------- |
| **Framework**          | pytest + pytest-django (existing)                                         |
| **Config file**        | `apps/api/pyproject.toml` (`[tool.pytest.ini_options]`)                   |
| **Quick run command**  | `cd apps/api && python -m pytest tests/billing/test_controllers.py -x -q` |
| **Full suite command** | `cd apps/api && python -m pytest tests/billing/ -q`                       |
| **Estimated runtime**  | ~20 seconds                                                               |

---

## Sampling Rate

- **After every task commit:** Run `cd apps/api && python -m pytest tests/billing/test_controllers.py -x -q`
- **After every plan wave:** Run `cd apps/api && python -m pytest tests/billing/ -q`
- **Before `/gsd:verify-work`:** Full backend suite green + manual smoke of `/billing` page
- **Max feedback latency:** 20 seconds

---

## Per-Task Verification Map

| Task ID  | Plan | Wave | Requirement                       | Test Type         | Automated Command                                                                                                              | File Exists | Status     |
| -------- | ---- | ---- | --------------------------------- | ----------------- | ------------------------------------------------------------------------------------------------------------------------------ | ----------- | ---------- |
| 11-01-01 | 01   | 0    | BILL-01, BILL-07                  | unit (controller) | `pytest tests/billing/test_controllers.py::test_get_subscription tests/billing/test_controllers.py::test_get_status -x`        | ❌ W0       | ⬜ pending |
| 11-01-02 | 01   | 0    | INV-01, BILL-02                   | unit (controller) | `pytest tests/billing/test_controllers.py::test_list_invoices tests/billing/test_controllers.py::test_list_invoices_fields -x` | ❌ W0       | ⬜ pending |
| 11-01-03 | 01   | 1    | BILL-01, BILL-07, INV-01, BILL-02 | unit (controller) | `pytest tests/billing/test_controllers.py -x -q`                                                                               | ❌ W0       | ⬜ pending |
| 11-02-01 | 02   | 0    | BILL-03, BILL-04                  | unit (controller) | `pytest tests/billing/test_controllers.py::test_change_plan tests/billing/test_controllers.py::test_cancel_subscription -x`    | ❌ W0       | ⬜ pending |
| 11-02-02 | 02   | 0    | BILL-06                           | unit (controller) | `pytest tests/billing/test_controllers.py::test_portal_session -x`                                                             | ❌ W0       | ⬜ pending |
| 11-02-03 | 02   | 1    | BILL-03, BILL-04, BILL-06         | unit (controller) | `pytest tests/billing/test_controllers.py -x -q`                                                                               | ❌ W0       | ⬜ pending |
| 11-03-01 | 03   | 1    | BILL-05                           | manual smoke      | N/A — UI page render                                                                                                           | N/A         | ⬜ pending |
| 11-03-02 | 03   | 1    | BILL-05                           | manual smoke      | N/A — billing.config.ts integration                                                                                            | N/A         | ⬜ pending |

_Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky_

---

## Wave 0 Requirements

- [ ] `apps/api/tests/billing/test_controllers.py` — stubs for all 8 controller endpoints (INV-01, BILL-01 through BILL-07)
- [ ] `apps/api/apps/billing/controllers.py` — controller file (does not exist yet, Wave 0 creates skeleton)
- [ ] `apps/api/apps/billing/schemas.py` — request/response schemas (does not exist yet, Wave 0 creates stubs)

_Existing fixtures in `tests/billing/conftest.py` cover all needed fixtures — no new conftest required._

---

## Manual-Only Verifications

| Behavior                                                      | Requirement | Why Manual                            | Test Instructions                                                                                                                   |
| ------------------------------------------------------------- | ----------- | ------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `/billing` page renders current plan, history, action buttons | BILL-05     | Next.js frontend — no pytest coverage | Run `pnpm dev`, navigate to `/billing` as authenticated user, verify plan card, table, and buttons render without errors            |
| Past-due banner appears in dashboard header                   | BILL-05     | Frontend layout — no pytest coverage  | Set subscription status to `past_due` in DB, reload any dashboard page, verify amber Alert renders with "Update payment method" CTA |
| Proration modal shows two-line summary before plan change     | BILL-03     | Frontend interaction                  | Click Upgrade on a plan card, verify modal opens with "Charged today" and "Next renewal" lines                                      |
| Cancel modal shows end date, not immediate deletion           | BILL-04     | Frontend interaction                  | Click Cancel subscription, verify modal shows period end date                                                                       |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 20s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
