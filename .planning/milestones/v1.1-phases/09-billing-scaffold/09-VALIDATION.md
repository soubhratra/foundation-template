---
phase: 9
slug: billing-scaffold
status: planned
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-07
---

# Phase 9 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property               | Value                                                    |
| ---------------------- | -------------------------------------------------------- |
| **Framework**          | pytest + pytest-django                                   |
| **Config file**        | `apps/api/pyproject.toml`                                |
| **Quick run command**  | `cd apps/api && uv run pytest apps/tests/billing/ -x -q` |
| **Full suite command** | `cd apps/api && uv run pytest apps/tests/billing/ -v`    |
| **Estimated runtime**  | ~15 seconds                                              |

---

## Sampling Rate

- **After every task commit:** Run `cd apps/api && uv run pytest apps/tests/billing/ -x -q`
- **After every plan wave:** Run `cd apps/api && uv run pytest apps/tests/billing/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan  | Wave | Requirement             | Test Type | Automated Command                                                      | File Exists | Status     |
| ------- | ----- | ---- | ----------------------- | --------- | ---------------------------------------------------------------------- | ----------- | ---------- |
| 09-01-1 | 09-01 | 0    | —                       | infra     | `pytest apps/tests/billing/ --collect-only -q`                         | ✅ W0       | ⬜ pending |
| 09-01-2 | 09-01 | 0    | ADPTR-01                | unit      | `pytest apps/tests/billing/test_adapters.py --collect-only -q`         | ✅ W0       | ⬜ pending |
| 09-02-1 | 09-02 | 1    | —                       | infra     | `python -c "from apps.billing.apps import BillingConfig; print('ok')"` | ❌ W1       | ⬜ pending |
| 09-02-2 | 09-02 | 1    | CUST-01, SUB-06, PAY-02 | unit      | `pytest apps/tests/billing/test_models.py -x -q`                       | ❌ W1       | ⬜ pending |
| 09-02-3 | 09-02 | 1    | ADPTR-01, ADPTR-02      | unit      | `pytest apps/tests/billing/test_adapters.py -x -q`                     | ❌ W1       | ⬜ pending |
| 09-03-1 | 09-03 | 2    | ADPTR-03, ADPTR-04      | unit      | `python manage.py check`                                               | ❌ W2       | ⬜ pending |
| 09-03-2 | 09-03 | 2    | CUST-02                 | unit      | `pytest apps/tests/billing/test_signals.py -x -q`                      | ❌ W2       | ⬜ pending |
| 09-03-3 | 09-03 | 2    | ALL                     | suite     | `pytest apps/tests/billing/ -x -q`                                     | ❌ W2       | ⬜ pending |

_Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky_

---

## Wave 0 Requirements

- [x] `apps/tests/billing/__init__.py` — test package
- [x] `apps/tests/billing/conftest.py` — shared fixtures (User factory, Customer factory)
- [x] `apps/tests/billing/test_adapters.py` — stubs for ADPTR-01..03
- [x] `apps/tests/billing/test_models.py` — stubs for CUST-01, SUB-06, PAY-02
- [x] `apps/tests/billing/test_signals.py` — stubs for CUST-02

_Wave 0 stubs live in Plan 09-01. They use `pytest.importorskip` so they skip cleanly until Wave 1 ships the billing module._

---

## Manual-Only Verifications

| Behavior                                                          | Requirement | Why Manual                                  | Test Instructions                                                                  |
| ----------------------------------------------------------------- | ----------- | ------------------------------------------- | ---------------------------------------------------------------------------------- |
| StripeAdapter calls real Stripe test API                          | ADPTR-02    | Requires STRIPE_SECRET_KEY in test env      | Set env var and run `pytest apps/tests/billing/test_adapters.py -v -m integration` |
| `manage.py check` passes with billing removed from INSTALLED_APPS | SCAFF-04    | Not in Phase 9 scope — deferred to Phase 12 | —                                                                                  |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 15s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** ✅ compliant
