---
phase: 9
slug: billing-scaffold
status: draft
nyquist_compliant: false
wave_0_complete: false
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

_To be filled by planner when PLAN.md tasks are defined._

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command                                                       | File Exists | Status     |
| ------- | ---- | ---- | ----------- | --------- | ----------------------------------------------------------------------- | ----------- | ---------- |
| TBD     | —    | —    | ADPTR-01    | unit      | `pytest apps/tests/billing/test_adapters.py -x`                         | ❌ W0       | ⬜ pending |
| TBD     | —    | —    | ADPTR-02    | unit      | `pytest apps/tests/billing/test_stripe_adapter.py -x`                   | ❌ W0       | ⬜ pending |
| TBD     | —    | —    | CUST-01     | unit      | `pytest apps/tests/billing/test_models.py -x`                           | ❌ W0       | ⬜ pending |
| TBD     | —    | —    | CUST-02     | unit      | `pytest apps/tests/billing/test_signals.py -x`                          | ❌ W0       | ⬜ pending |
| TBD     | —    | —    | SUB-06      | unit      | `pytest apps/tests/billing/test_models.py::test_subscription_status -x` | ❌ W0       | ⬜ pending |

_Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky_

---

## Wave 0 Requirements

- [ ] `apps/tests/billing/__init__.py` — test package
- [ ] `apps/tests/billing/conftest.py` — shared fixtures (User factory, Customer factory)
- [ ] `apps/tests/billing/test_adapters.py` — stubs for ADPTR-01..05
- [ ] `apps/tests/billing/test_models.py` — stubs for CUST-01, SUB-06, PAY-02
- [ ] `apps/tests/billing/test_signals.py` — stubs for CUST-02

---

## Manual-Only Verifications

| Behavior                                                          | Requirement | Why Manual                                  | Test Instructions                                                                        |
| ----------------------------------------------------------------- | ----------- | ------------------------------------------- | ---------------------------------------------------------------------------------------- |
| StripeAdapter calls real Stripe test API                          | ADPTR-02    | Requires STRIPE_SECRET_KEY in test env      | Set env var and run `pytest apps/tests/billing/test_stripe_adapter.py -v -m integration` |
| `manage.py check` passes with billing removed from INSTALLED_APPS | SCAFF-04    | Not in Phase 9 scope — deferred to Phase 12 | —                                                                                        |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
