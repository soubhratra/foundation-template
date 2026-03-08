---
phase: 11-api-endpoints-billing-frontend
plan: 06
subsystem: payments
tags: [stripe, billing, django-ninja, nextjs, server-actions, migrations]

# Dependency graph
requires:
  - phase: 11-02
    provides: BillingController with existing subscription endpoints and BillingService
  - phase: 11-03
    provides: billing-actions.ts with changePlanAction pattern
  - phase: 11-05
    provides: stub adapter PlanProviderMapping model via 0001_initial migration
provides:
  - POST /api/v1/billing/subscription/subscribe endpoint for free-tier users
  - CheckoutSessionIn and CheckoutSessionOut schemas in billing schemas module
  - Django data migration 0002 seeding 4 PlanProviderMapping stub rows
  - createCheckoutSessionAction server action in billing-actions.ts
affects: [billing-client, billing-page, free-tier-checkout-flow, plan-11-07]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Data migration pattern with RunPython for seeding lookup table rows
    - Origin detection via next/headers host for dynamic URL construction in server actions
    - Checkout session endpoint separate from subscription/change (no active subscription required)

key-files:
  created:
    - apps/api/apps/billing/migrations/0002_plan_provider_mapping_stub_seed.py
  modified:
    - apps/api/apps/billing/schemas.py
    - apps/api/apps/billing/controllers.py
    - apps/web/src/actions/billing-actions.ts

key-decisions:
  - "subscribe endpoint separate from change endpoint: create_checkout_session needs only Customer (auto-created), upgrade_subscription needs active subscription"
  - "PlanProviderMapping seeded via data migration not fixtures: guarantees correct ordering relative to schema migration 0001_initial"
  - "Origin derived from next/headers host header: avoids needing NEXT_PUBLIC_APP_URL env var in this template"
  - "No revalidatePath in createCheckoutSessionAction: subscription state changes via webhook after payment, not immediately"

patterns-established:
  - "Checkout entry point for free-tier users: POST /subscription/subscribe (checkout session) not /subscription/change (plan upgrade)"
  - "Stub provider rows must exist for _resolve_price_id() to work in dev/test"

requirements-completed: [BILL-03]

# Metrics
duration: 4min
completed: 2026-03-08
---

# Phase 11 Plan 06: Subscribe Endpoint and Checkout Action Summary

**POST /subscription/subscribe endpoint, stub PlanProviderMapping seed migration, and createCheckoutSessionAction server action enabling free-tier users to initiate Stripe Checkout**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-08T17:28:07Z
- **Completed:** 2026-03-08T17:32:07Z
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments

- Added CheckoutSessionIn/CheckoutSessionOut schemas and POST /api/v1/billing/subscription/subscribe endpoint to BillingController
- Created Django data migration 0002 seeding 4 PlanProviderMapping rows for the stub adapter (pro/monthly, pro/annual, enterprise/monthly, enterprise/annual)
- Added createCheckoutSessionAction to billing-actions.ts with dynamic origin detection via next/headers
- All 8 existing billing controller tests continue to pass (no regression)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add subscribe endpoint schemas and controller route** - `f202b33` (feat)
2. **Task 2: Seed PlanProviderMapping rows for stub adapter via data migration** - `ff06da1` (feat)
3. **Task 3: Add createCheckoutSessionAction to billing-actions.ts** - `d15cf52` (feat)

## Files Created/Modified

- `apps/api/apps/billing/schemas.py` - Added CheckoutSessionIn and CheckoutSessionOut schemas
- `apps/api/apps/billing/controllers.py` - Added subscribe_plan endpoint at POST /subscription/subscribe
- `apps/api/apps/billing/migrations/0002_plan_provider_mapping_stub_seed.py` - Data migration seeding 4 stub PlanProviderMapping rows
- `apps/web/src/actions/billing-actions.ts` - Added createCheckoutSessionAction with dynamic origin detection

## Decisions Made

- Separate subscribe endpoint from change endpoint: `create_checkout_session` only requires a Customer record (guaranteed via post_save signal), while `upgrade_subscription` requires an active subscription. Free-tier users have no subscription so they must use the new endpoint.
- PlanProviderMapping rows seeded via Django data migration to ensure correct ordering after the schema migration that creates the table.
- Origin derived from `next/headers` host rather than a `NEXT_PUBLIC_APP_URL` env var — the template has no such env var yet and dynamic detection is more portable.
- No `revalidatePath` in `createCheckoutSessionAction` — subscription state updates via Stripe webhook after payment completes, not at checkout session creation time.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all verification checks passed on first attempt.

## Next Phase Readiness

- Subscribe endpoint fully functional for free-tier checkout flow
- 4 stub PlanProviderMapping rows enable dev environment plan operations (subscribe, change, preview)
- createCheckoutSessionAction ready to be wired into billing-client.tsx for free-tier plan card clicks
- Ready for plan 11-07 (gap closure: free-tier UI wiring)

---

_Phase: 11-api-endpoints-billing-frontend_
_Completed: 2026-03-08_
