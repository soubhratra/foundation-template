---
phase: 10-webhook-infrastructure-service-layer
plan: "03"
subsystem: billing
tags: [billing, decorator, subscription-gate, tdd, permissions]
dependency_graph:
  requires:
    - 10-01 (ProcessedWebhookEvent, webhook endpoint)
    - 10-02 (Subscription model, SubscriptionStatus enum)
  provides:
    - require_active_subscription decorator importable from apps.billing.decorators
  affects:
    - Phase 11 Ninja controllers that apply @require_active_subscription to billing endpoints
tech_stack:
  added: []
  patterns:
    - functools.wraps for transparent function decorator wrapping
    - raise PermissionDenied from None (B904 compliant) for secure error chains
    - _PASSING_STATUSES set membership for O(1) status lookup
key_files:
  created:
    - apps/api/apps/billing/decorators.py
    - apps/api/tests/billing/test_decorators.py
  modified:
    - apps/api/tests/billing/conftest.py (added 7 status-specific subscription fixtures)
decisions:
  - cancel_at_period_end=True passes because status is still ACTIVE — no extra conditional; webhook handler sets CANCELED when period ends
  - except Exception (not AttributeError) for both Django RelatedObjectDoesNotExist and ORM version variations
  - raise PermissionDenied from None to suppress chained exception context (ruff B904 compliance)
  - _PASSING_STATUSES set defined at module level — evaluated once, not on each request
metrics:
  duration_seconds: 158
  completed_date: "2026-03-08"
  tasks_completed: 2
  files_changed: 3
---

# Phase 10 Plan 03: @require_active_subscription Decorator Summary

**One-liner:** TDD-built view decorator that gates Django/Ninja endpoints to ACTIVE/TRIALING subscriptions via PermissionDenied (HTTP 403), integrated with the existing permission_denied_handler.

## What Was Built

The `@require_active_subscription` decorator in `apps/api/apps/billing/decorators.py` protects any Django view function or Ninja endpoint. On each request it:

1. Looks up `request.user.billing_customer` — raises `PermissionDenied` if missing.
2. Looks up `customer.subscription` — raises `PermissionDenied` if missing.
3. Checks `subscription.status` against `{ACTIVE, TRIALING}` — raises `PermissionDenied` for any other status.

Users with `cancel_at_period_end=True` pass through because their subscription status is still `ACTIVE`. When the billing period ends, the Stripe webhook handler (10-01) sets `status=CANCELED`, blocking future requests automatically — no extra conditional required in the decorator.

## TDD Flow

**RED (637a5d3):** Created `test_decorators.py` with 9 test functions covering all gating conditions. All failed with `ModuleNotFoundError` as expected.

**GREEN (9d883a4):** Implemented `decorators.py`. All 9 tests passed immediately. Full billing suite (55 passed, 1 skipped) remained green.

## Test Coverage

| Test                             | Condition                                | Expected         |
| -------------------------------- | ---------------------------------------- | ---------------- |
| test_active_user_passes          | status=ACTIVE                            | HTTP 200         |
| test_trialing_user_passes        | status=TRIALING                          | HTTP 200         |
| test_cancel_at_period_end_passes | status=ACTIVE, cancel_at_period_end=True | HTTP 200         |
| test_past_due_user_blocked       | status=PAST_DUE                          | PermissionDenied |
| test_unpaid_user_blocked         | status=UNPAID                            | PermissionDenied |
| test_canceled_user_blocked       | status=CANCELED                          | PermissionDenied |
| test_incomplete_user_blocked     | status=INCOMPLETE                        | PermissionDenied |
| test_no_customer_blocked         | no Customer record                       | PermissionDenied |
| test_no_subscription_blocked     | Customer exists, no Subscription         | PermissionDenied |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Linting] Added `from None` to `raise PermissionDenied` in except clauses**

- **Found during:** Task 2 commit (pre-commit ruff hook, rule B904)
- **Issue:** `raise X` inside `except` without `from err` or `from None` leaks exception chain context
- **Fix:** Changed both `raise PermissionDenied(...)` to `raise PermissionDenied(...) from None`
- **Files modified:** apps/api/apps/billing/decorators.py

No other deviations — plan executed as written.

## Commits

| Hash    | Description                                                              |
| ------- | ------------------------------------------------------------------------ |
| 637a5d3 | test(10-03): add failing tests for require_active_subscription decorator |
| 9d883a4 | feat(10-03): implement @require_active_subscription decorator            |

## Self-Check: PASSED

- FOUND: apps/api/apps/billing/decorators.py
- FOUND: apps/api/tests/billing/test_decorators.py
- FOUND: commit 637a5d3 (RED phase tests)
- FOUND: commit 9d883a4 (GREEN implementation)
