---
phase: 10-webhook-infrastructure-service-layer
plan: "02"
subsystem: billing
tags: [billing, service-layer, tdd, stripe, subscriptions, metered-usage]
dependency_graph:
  requires:
    - apps/api/apps/billing/adapters.py # extended with new ABCs
    - apps/api/apps/billing/models.py # Customer, Subscription, PlanProviderMapping
    - apps/api/apps/core/exceptions.py # ServiceError
    - apps/api/apps/billing/utils.py # get_adapter() — lazy-imported at runtime
  provides:
    - apps/api/apps/billing/services.py # BillingService — internal API for all billing ops
  affects:
    - apps/api/apps/billing/adapters.py # added preview_proration, get_usage_summary ABCs + StripeAdapter impl
    - apps/api/tests/billing/conftest.py # StubAdapter, billing_service, plan_mapping, subscription fixtures
    - apps/api/tests/billing/test_adapters.py # updated expected abstract methods set
tech_stack:
  added: []
  patterns:
    - Dependency injection for testability: BillingService(adapter=stub) skips Django settings
    - PlanProviderMapping lookup: resolves plan_id+billing_period -> price_id at runtime, no hardcoded Stripe IDs
    - Adapter ABC extension: preview_proration and get_usage_summary added as abstract methods
    - Provider name inference: type(adapter).__name__.lower().replace('adapter','') -> 'stripe' or 'stub'
key_files:
  created:
    - apps/api/apps/billing/services.py
    - apps/api/tests/billing/test_services.py
  modified:
    - apps/api/apps/billing/adapters.py
    - apps/api/apps/billing/services.py
    - apps/api/tests/billing/conftest.py
    - apps/api/tests/billing/test_adapters.py
decisions:
  - "BillingService takes optional adapter= arg for DI; lazy-imports get_adapter() only when adapter is None — cleanest testability pattern without mocking settings"
  - "Provider name derived from adapter class name at runtime (StripeAdapter -> 'stripe') — enables PlanProviderMapping lookup without explicit configuration"
  - "test_missing_customer_raises updated: auto-Customer signal means no-customer case is unreachable; test_missing_price_mapping_raises covers the actual first-failure path"
  - "StripeAdapter.preview_proration uses invoices.create_preview with subscription_details items override"
  - "StripeAdapter.get_usage_summary uses subscription_items.list_usage_record_summaries with limit=1"
metrics:
  duration_seconds: 441
  completed_date: "2026-03-08"
  tasks_completed: 2
  tasks_total: 2
  files_created: 2
  files_modified: 4
---

# Phase 10 Plan 02: BillingService + Extended PaymentAdapter Summary

**One-liner:** BillingService with full subscription lifecycle + one-time payments + metered usage, backed by extended PaymentAdapter ABCs and tested via StubAdapter dependency injection.

## Objective

Extend `PaymentAdapter` with `preview_proration` and `get_usage_summary` abstract methods, implement both in `StripeAdapter`, and build `BillingService` — the single internal API for all billing operations used by Phase 11 controllers.

## What Was Built

### `apps/api/apps/billing/adapters.py` (extended)

Added two new abstract methods to `PaymentAdapter`:

- `preview_proration(subscription_id, new_price_id, proration_date=None) -> dict` — returns `{amount_due_now, next_invoice_total, proration_date, currency}`
- `get_usage_summary(subscription_item_id) -> dict` — returns `{total_usage, period_start, period_end}`

`StripeAdapter` implements both:

- `preview_proration`: calls `self._client.invoices.create_preview()` with subscription override, sums proration line items
- `get_usage_summary`: calls `self._client.subscription_items.list_usage_record_summaries()`

### `apps/api/apps/billing/services.py` (new)

`BillingService` with 11 methods covering the full billing surface:

| Method                    | Description                                                       |
| ------------------------- | ----------------------------------------------------------------- |
| `create_checkout_session` | Subscription checkout via PlanProviderMapping lookup              |
| `upgrade_subscription`    | modify_subscription with `proration_behavior="create_prorations"` |
| `downgrade_subscription`  | modify_subscription with `proration_behavior="always_invoice"`    |
| `cancel_subscription`     | cancel adapter call + persists `cancel_at_period_end` to DB       |
| `reactivate_subscription` | modify_subscription to restore an active price                    |
| `preview_proration`       | Returns proration preview before committing plan change           |
| `create_one_time_payment` | Checkout in `mode="payment"`                                      |
| `record_usage`            | Delegates to adapter with customer's `stripe_customer_id`         |
| `get_usage_summary`       | Delegates to adapter                                              |
| `create_portal_session`   | Billing portal session                                            |
| `list_invoices`           | Invoice history                                                   |

### Test Infrastructure

`StubAdapter` in `tests/billing/conftest.py` implements all 10 `PaymentAdapter` abstract methods with predictable return values — enabling zero-HTTP unit tests.

Fixtures added: `stub_adapter`, `billing_service`, `plan_mapping`, `subscription`.

## Test Results

```
46 passed, 1 skipped in 21.70s
```

All service tests (10 scenarios) and adapter contract tests green.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated test_adapters.py expected abstract methods set**

- **Found during:** Task 2 implementation
- **Issue:** `test_abstract_methods_defined` had hardcoded set of 8 methods; adding 2 new ABCs would cause it to fail
- **Fix:** Added `preview_proration` and `get_usage_summary` to the expected set in `test_adapters.py`
- **Files modified:** `apps/api/tests/billing/test_adapters.py`
- **Commit:** 25c45dc

**2. [Rule 1 - Bug] test_missing_customer_raises updated to reflect auto-Customer signal**

- **Found during:** Task 2 GREEN phase (test run)
- **Issue:** `billing/signals.py` has a `post_save` signal that auto-creates a `Customer` for every new `User`. The "no customer" scenario is unreachable, causing the test to fail with a 400 (missing price mapping) instead of 404 (missing customer)
- **Fix:** Renamed test to `test_missing_price_mapping_raises`; changed it to test `plan_id="unknown_plan"` which hits the actual first-failure path (`no_price_mapping`, status 400)
- **Files modified:** `apps/api/tests/billing/test_services.py`
- **Commit:** 25c45dc

**3. [Rule 1 - Bug] Added `raise ... from exc` in except clauses (ruff B904)**

- **Found during:** Pre-commit hook on Task 2 commit
- **Issue:** Ruff B904 requires explicit exception chaining in `except` blocks
- **Fix:** Added `from exc` to both `raise ServiceError(...)` calls in `_get_customer` and `_resolve_price_id`
- **Files modified:** `apps/api/apps/billing/services.py`
- **Commit:** 25c45dc

## Commits

| Task      | Name                                   | Commit  | Key Files                                                    |
| --------- | -------------------------------------- | ------- | ------------------------------------------------------------ |
| 1 (RED)   | Write failing BillingService tests     | 3bc1aa5 | test_services.py, conftest.py                                |
| 2 (GREEN) | Extend PaymentAdapter + BillingService | 25c45dc | adapters.py, services.py, test_adapters.py, test_services.py |

## Self-Check: PASSED

All created files exist on disk. Both task commits verified in git history.
