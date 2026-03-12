# Deferred Items — Phase 22 RBAC

## Pre-Existing Issue: billing/test_controllers.py N+1 Error

**Found during:** Plan 22-03 Task 2 full regression check

**File:** `apps/api/tests/billing/test_controllers.py::test_get_subscription`

**Error:** `nplusone.core.exceptions.NPlusOneError: Potential unnecessary eager load detected on Subscription.customer`

**Status:** Pre-existing — failure exists on commit `9361d2e` (before plan 22-03 changes). Not caused by RBAC implementation.

**Impact:** Out of scope for plan 22-03. Does not affect RBAC functionality.

**Action needed:** Fix `select_related("customer")` or `prefetch_related("customer")` in billing subscription query, or add an nplusone whitelist entry for that relationship.
