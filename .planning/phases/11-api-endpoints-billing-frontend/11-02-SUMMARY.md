---
phase: 11-api-endpoints-billing-frontend
plan: "02"
subsystem: billing-api
tags: [billing, django-ninja, controller, service-layer, tdd-green]
dependency_graph:
  requires: [11-01]
  provides: [billing-controller-impl, billing-service-read-methods, stub-adapter-module]
  affects:
    [
      apps/api/apps/billing/controllers.py,
      apps/api/apps/billing/services.py,
      apps/api/apps/billing/adapters.py,
    ]
tech_stack:
  added: []
  patterns:
    - BillingController delegates 100% to BillingService (no ORM in controllers)
    - StubAdapter in apps/billing/stub_adapter.py configured via BILLING_ADAPTER in development.py
    - get_status() returns all-None sentinel (no ServiceError) for free-tier users
    - reactivate_subscription() takes no plan_id — undoes cancel_at_period_end via adapter
    - create_portal_session() has optional return_url defaulting to empty string
key_files:
  created:
    - apps/api/apps/billing/stub_adapter.py
  modified:
    - apps/api/apps/billing/controllers.py
    - apps/api/apps/billing/services.py
    - apps/api/apps/billing/adapters.py
    - apps/api/config/settings/development.py
    - apps/api/tests/billing/conftest.py
    - apps/api/tests/billing/test_adapters.py
    - apps/api/tests/billing/test_services.py
decisions:
  - StubAdapter promoted to proper module (apps/billing/stub_adapter.py) and configured in development.py so controller tests use it automatically without per-test monkeypatching
  - reactivate_subscription() signature changed to take no plan_id — reactivation restores subscription as-is by setting cancel_at_period_end=False, not by modifying the price
  - get_status() returns sentinel dict (all-None) instead of raising ServiceError when no subscription exists, so dashboard renders correctly for free-tier users
  - list_invoices in controller maps hosted_invoice_url → invoice_url for schema field compatibility (StripeAdapter returns hosted_invoice_url; InvoiceOut.invoice_url)
  - subscription test fixture includes PlanProviderMapping creation so controller tests can call upgrade_subscription without requiring the separate plan_mapping fixture
metrics:
  duration_seconds: 435
  completed_date: "2026-03-08"
  tasks_completed: 2
  files_changed: 7
---

# Phase 11 Plan 02: BillingController Implementation Summary

**One-liner:** BillingController 8-endpoint implementation delegating 100% to BillingService via StubAdapter-wired development settings — all 63 billing tests green.

## What Was Built

Drove the RED test suite from Plan 01 to GREEN by implementing all 8 `BillingController` route methods and adding the missing `get_status()` and `get_subscription_detail()` service methods. The controller enforces strict thin-controller discipline — zero ORM access, every method delegates to `BillingService`.

### Key implementations

**BillingService additions:**

- `get_status(user)` — lightweight read returning `{status, cancel_at_period_end, current_period_end}` with all-None sentinel for no-subscription case
- `get_subscription_detail(user)` — full detail with `plan_id` resolved from `PlanProviderMapping` via `retrieve_subscription` adapter call (failure is non-fatal, returns `None`)

**PaymentAdapter ABC additions:**

- `retrieve_subscription(subscription_id)` — returns `{"current_price_id": str}` for plan_id resolution
- `reactivate_subscription(subscription_id)` — undoes `cancel_at_period_end` without a price change

**BillingController (all 8 routes implemented):**

- `GET /status` → `service.get_status()`
- `GET /subscription` → `service.get_subscription_detail()`
- `GET /invoices` → `service.list_invoices()` + field mapping to `InvoiceOut`
- `POST /subscription/change` → `service.upgrade_subscription()` + `get_subscription_detail()`
- `POST /subscription/cancel` → `service.cancel_subscription()` + `get_status()`
- `POST /subscription/reactivate` → `service.reactivate_subscription()` + `get_status()`
- `POST /portal-session` → `service.create_portal_session()`
- `POST /proration-preview` → `service.preview_proration()`

## Test Results

```
tests/billing/test_controllers.py — 8 passed (target: GREEN)
tests/billing/ (full suite)       — 63 passed, 1 skipped
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Infrastructure] StubAdapter promoted to proper module**

- **Found during:** Task 1 — controller tests use real Django test client, not stub adapter injection
- **Issue:** The plan expected tests to work via stub adapter, but the controller's `__init__` calls `BillingService()` which resolves `BILLING_ADAPTER` from Django settings (pointing to `StripeAdapter` in base settings). `StripeAdapter()` would fail on Stripe API calls.
- **Fix:** Created `apps/billing/stub_adapter.py` as a proper module and set `BILLING_ADAPTER = "apps.billing.stub_adapter.StubAdapter"` in `development.py`. Tests run under `config.settings.development`, so all controller tests automatically use the stub.
- **Files modified:** `apps/billing/stub_adapter.py` (created), `config/settings/development.py`
- **Commit:** 52a750e

**2. [Rule 1 - Bug] reactivate_subscription signature changed**

- **Found during:** Task 2 analysis — the plan noted "reactivate_subscription takes no payload" but the existing service method required `plan_id` and `billing_period` and called `modify_subscription` (a price change)
- **Issue:** Reactivation should undo `cancel_at_period_end=True` without changing the price, not modify the subscription price
- **Fix:** Added `reactivate_subscription(subscription_id)` to the PaymentAdapter ABC and implementations. Updated `BillingService.reactivate_subscription()` to call the new adapter method and clear `cancel_at_period_end` flag on the local record.
- **Files modified:** `adapters.py`, `services.py`, `stub_adapter.py`, `test_services.py`
- **Commit:** 953e64b

**3. [Rule 2 - Missing Test Data] subscription fixture extended with PlanProviderMapping**

- **Found during:** Task 2 — `test_change_plan` failed with 400 because `upgrade_subscription` couldn't resolve price ID (no mapping for `provider="stub"`)
- **Issue:** Controller tests use `subscription` fixture (no `plan_mapping` fixture) but the service's `_resolve_price_id` queries `PlanProviderMapping`
- **Fix:** Added `PlanProviderMapping.objects.get_or_create(plan_id="pro", provider="stub", ...)` to the `subscription` fixture in `tests/billing/conftest.py`
- **Files modified:** `tests/billing/conftest.py`
- **Commit:** 953e64b

**4. [Rule 1 - Bug] test_abstract_methods_defined updated for new ABC methods**

- **Found during:** Full billing suite run after Task 2 — `TestPaymentAdapterContract::test_abstract_methods_defined` had a hardcoded set of 10 methods that excluded the 2 new ones
- **Fix:** Added `retrieve_subscription` and `reactivate_subscription` to the expected set
- **Files modified:** `tests/billing/test_adapters.py`
- **Commit:** 953e64b

## Self-Check: PASSED

All created files verified present. All task commits verified in git history.

| Check                          | Result |
| ------------------------------ | ------ |
| `apps/billing/stub_adapter.py` | FOUND  |
| `apps/billing/controllers.py`  | FOUND  |
| `apps/billing/services.py`     | FOUND  |
| Commit 52a750e (Task 1)        | FOUND  |
| Commit 953e64b (Task 2)        | FOUND  |
