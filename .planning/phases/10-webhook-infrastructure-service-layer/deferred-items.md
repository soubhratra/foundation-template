# Deferred Items — Phase 10

## Pre-existing Test Failure (Out of Scope)

**File:** `apps/api/tests/billing/test_services.py`
**Test:** `TestCreateCheckoutSession::test_missing_customer_raises`
**Status:** Failing before Plan 10-01 was executed
**Issue:** Test expects `ServiceError.status_code == 404` when no Customer record exists,
but service raises `ServiceError('No active price mapping...')` with status_code=400.
The query order reaches the price-mapping lookup before the customer lookup.
**Action needed:** Fix `BillingService.create_checkout_session` to check for Customer
existence before checking PlanProviderMapping, and raise 404 with appropriate message.
**Discovered:** Plan 10-01, Task 2 verification
