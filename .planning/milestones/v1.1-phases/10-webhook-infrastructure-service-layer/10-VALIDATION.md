---
phase: 10
slug: webhook-infrastructure-service-layer
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-07
---

# Phase 10 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property               | Value                                                   |
| ---------------------- | ------------------------------------------------------- |
| **Framework**          | pytest + pytest-django (existing from Phase 9)          |
| **Config file**        | `apps/api/pyproject.toml` (`[tool.pytest.ini_options]`) |
| **Quick run command**  | `cd apps/api && python -m pytest tests/billing/ -x -q`  |
| **Full suite command** | `cd apps/api && python -m pytest tests/ -x -q`          |
| **Estimated runtime**  | ~30 seconds                                             |

---

## Sampling Rate

- **After every task commit:** Run `cd apps/api && python -m pytest tests/billing/ -x -q`
- **After every plan wave:** Run `cd apps/api && python -m pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID  | Plan | Wave | Requirement | Test Type    | Automated Command                                                              | File Exists | Status     |
| -------- | ---- | ---- | ----------- | ------------ | ------------------------------------------------------------------------------ | ----------- | ---------- |
| 10-01-01 | 01   | 0    | HOOK-01     | unit         | `pytest tests/billing/test_webhooks.py::test_webhook_view_structure -x`        | ❌ W0       | ⬜ pending |
| 10-01-02 | 01   | 0    | HOOK-02     | integration  | `pytest tests/billing/test_webhooks.py::test_valid_signature_returns_200 -x`   | ❌ W0       | ⬜ pending |
| 10-01-03 | 01   | 0    | HOOK-02     | integration  | `pytest tests/billing/test_webhooks.py::test_invalid_signature_returns_400 -x` | ❌ W0       | ⬜ pending |
| 10-01-04 | 01   | 0    | HOOK-02     | unit         | `pytest tests/billing/test_webhooks.py::test_dispatch_failure_returns_500 -x`  | ❌ W0       | ⬜ pending |
| 10-01-05 | 01   | 0    | HOOK-03     | unit (eager) | `pytest tests/billing/test_tasks.py::test_idempotency_guard -x`                | ❌ W0       | ⬜ pending |
| 10-01-06 | 01   | 0    | HOOK-04     | unit (eager) | `pytest tests/billing/test_tasks.py -x`                                        | ❌ W0       | ⬜ pending |
| 10-02-01 | 02   | 0    | SUB-01      | unit (stub)  | `pytest tests/billing/test_services.py::test_create_checkout_session -x`       | ❌ W0       | ⬜ pending |
| 10-02-02 | 02   | 0    | SUB-02      | unit (stub)  | `pytest tests/billing/test_services.py::test_upgrade_subscription -x`          | ❌ W0       | ⬜ pending |
| 10-02-03 | 02   | 0    | SUB-03      | unit (stub)  | `pytest tests/billing/test_services.py::test_downgrade_subscription -x`        | ❌ W0       | ⬜ pending |
| 10-02-04 | 02   | 0    | SUB-04      | unit (stub)  | `pytest tests/billing/test_services.py::test_cancel_subscription -x`           | ❌ W0       | ⬜ pending |
| 10-02-05 | 02   | 0    | SUB-05      | unit (stub)  | `pytest tests/billing/test_services.py::test_reactivate_subscription -x`       | ❌ W0       | ⬜ pending |
| 10-02-06 | 02   | 0    | PAY-01      | unit (stub)  | `pytest tests/billing/test_services.py::test_one_time_payment -x`              | ❌ W0       | ⬜ pending |
| 10-02-07 | 02   | 0    | USAGE-01    | unit (stub)  | `pytest tests/billing/test_services.py::test_record_usage -x`                  | ❌ W0       | ⬜ pending |
| 10-02-08 | 02   | 0    | USAGE-02    | unit (stub)  | `pytest tests/billing/test_services.py::test_get_usage_summary -x`             | ❌ W0       | ⬜ pending |
| 10-03-01 | 03   | 0    | CUST-03     | unit         | `pytest tests/billing/test_decorators.py::test_active_user_passes -x`          | ❌ W0       | ⬜ pending |
| 10-03-02 | 03   | 0    | CUST-03     | unit         | `pytest tests/billing/test_decorators.py::test_inactive_user_blocked -x`       | ❌ W0       | ⬜ pending |

_Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky_

---

## Wave 0 Requirements

- [ ] `tests/billing/test_services.py` — stubs for SUB-01 through SUB-05, PAY-01, USAGE-01, USAGE-02 (all BillingService unit tests)
- [ ] `tests/billing/test_webhooks.py` — stubs for HOOK-01, HOOK-02
- [ ] `tests/billing/test_tasks.py` — stubs for HOOK-03, HOOK-04
- [ ] `tests/billing/test_decorators.py` — stubs for CUST-03
- [ ] Update `tests/billing/conftest.py` — add `StubAdapter`, `billing_service`, `subscription`, `payment` fixtures
- [ ] Update `tests/billing/test_adapters.py` — add tests verifying `preview_proration` and `get_usage_summary` exist as abstract methods on `PaymentAdapter`

---

## Manual-Only Verifications

| Behavior                                        | Requirement | Why Manual                          | Test Instructions                                                                                                                                  |
| ----------------------------------------------- | ----------- | ----------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| Stripe CLI live webhook delivery with real HMAC | HOOK-02     | Requires live Stripe CLI forwarding | Run `stripe listen --forward-to localhost:8000/billing/webhook/`, trigger `stripe trigger checkout.session.completed`, verify 200 response in logs |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
