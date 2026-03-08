---
phase: 11-api-endpoints-billing-frontend
plan: 01
subsystem: api
tags: [django-ninja-extra, billing, tdd, pytest, schemas]

# Dependency graph
requires:
  - phase: 10-webhook-infrastructure-service-layer
    provides: BillingService with all 8 operations + StubAdapter + conftest fixtures
provides:
  - "BillingController skeleton (8 routes, all raise NotImplementedError)"
  - "8 Ninja schemas for billing API endpoints (request + response)"
  - "RED test suite: 8 failing tests covering all billing endpoints"
affects:
  - 11-02-PLAN (implements GREEN phase against these tests)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "django-ninja-extra @api_controller with SessionAuth + jwt_token_auth"
    - "Ninja Schema classes for typed request/response in controller routes"
    - "TDD RED phase: controller stubs raise NotImplementedError to produce deterministic 500 failures"

key-files:
  created:
    - apps/api/apps/billing/schemas.py
    - apps/api/apps/billing/controllers.py
    - apps/api/tests/billing/test_controllers.py
  modified: []

key-decisions:
  - "reactivate_subscription controller method has no payload (no PlanChangeIn needed — reactivation restores the previous plan)"
  - "test_controllers.py defines a local authenticated_client fixture that uses subscription.customer.user to ensure the logged-in user owns the test subscription (avoids mismatch with root conftest user fixture)"
  - "test_list_invoices_fields verifies field contract on each invoice item; passes vacuously when StubAdapter returns empty list — intentional for RED phase"

patterns-established:
  - "Billing controller: all endpoints delegate exclusively to BillingService (no ORM in controllers)"
  - "Billing test fixtures: local authenticated_client override ensures user/subscription ownership alignment"

requirements-completed: [BILL-01, BILL-02, BILL-07, INV-01]

# Metrics
duration: 4min
completed: 2026-03-08
---

# Phase 11 Plan 01: Billing Controller TDD Scaffold Summary

**8 Ninja schemas + BillingController skeleton with 8 stub routes + failing test suite establishing RED state for Plan 02 implementation**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-08T11:36:50Z
- **Completed:** 2026-03-08T11:40:43Z
- **Tasks:** 1 (single TDD scaffold task)
- **Files modified:** 3 created

## Accomplishments

- Created `schemas.py` with all 8 Ninja Schema classes: `BillingStatusOut`, `SubscriptionDetailOut`, `InvoiceOut`, `InvoiceListOut`, `PlanChangeIn`, `ProrationPreviewIn`, `ProrationPreviewOut`, `PortalSessionOut`
- Created `controllers.py` with `BillingController` using `@api_controller("/billing")` — 8 routes all raising `NotImplementedError("implement in plan 02")`
- Created `test_controllers.py` with 8 named test functions; confirmed RED state: `pytest` collects 8 tests, all FAIL with 500

## Task Commits

Each task was committed atomically:

1. **TDD Scaffold: schemas + controller skeleton + RED tests** - `85d0417` (test)

## Files Created/Modified

- `apps/api/apps/billing/schemas.py` — 8 Ninja Schema classes for all billing API endpoints
- `apps/api/apps/billing/controllers.py` — BillingController with 8 stub routes
- `apps/api/tests/billing/test_controllers.py` — 8 named failing tests (RED state)

## Decisions Made

- `reactivate_subscription` takes no payload — reactivation restores the subscription as-is, no plan selection needed. The RESEARCH.md pattern showed a `PlanChangeIn` payload on reactivate, but that is not needed by the service method signature.
- Local `authenticated_client` fixture in `test_controllers.py` overrides the root conftest fixture to use `subscription.customer.user`, ensuring the test user is the same one who owns the `Subscription` created by the `subscription` fixture. Without this, tests would be authenticated as a different user who has no subscription.
- `test_list_invoices_fields` passes vacuously in RED phase because `StubAdapter.list_invoices()` returns `[]`. The test correctly validates the field contract and will be meaningful in GREEN phase once invoices are returned.

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

- Pre-commit ruff hook flagged E501 (line too long) on a test docstring. Fixed by shortening the docstring to fit the 100-character limit. No logic changes.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- RED state committed and verified: 8 tests collected, 8 FAILED
- Plan 02 implements the GREEN phase: BillingController methods delegate to BillingService, all tests must pass
- `get_subscription_detail(user)` method needs to be added to BillingService in Plan 02 (noted in RESEARCH.md as a new method)

---

_Phase: 11-api-endpoints-billing-frontend_
_Completed: 2026-03-08_
