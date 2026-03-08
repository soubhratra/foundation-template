---
phase: 11-api-endpoints-billing-frontend
plan: 07
subsystem: payments
tags: [billing, nextjs, free-tier, checkout, billing-config, billing-client]

# Dependency graph
requires:
  - phase: 11-06
    provides: createCheckoutSessionAction server action for free-tier checkout flow
  - phase: 11-03
    provides: billing.config.ts config-driven billing UI pattern
  - phase: 11-04
    provides: BillingClient component with plan cards and action handlers
provides:
  - Free-tier plan card states: Free shows "Current plan" (disabled), Pro/Enterprise show "Subscribe to {Name}"
  - handleSubscribe handler redirecting browser to Stripe checkout URL
  - Coherent plan overview empty-state: "Free plan" title + single sentence body
  - createCheckoutSessionAction wired from page.tsx into BillingClient
affects: [billing-client, billing-page, free-tier-checkout-flow]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Config-driven action gating extended with "subscribe" type for no_subscription state
    - Free-tier isCurrent fallback: plan.id === "free" when subscription is undefined
    - canSubscribe check drives button label ("Subscribe to {Name}") and handler selection

key-files:
  created: []
  modified:
    - apps/web/billing.config.ts
    - apps/web/app/(dashboard)/billing/billing-client.tsx
    - apps/web/app/(dashboard)/billing/page.tsx

key-decisions:
  - "subscribe action type added to BillingActionType: signals free-tier checkout path distinct from upgrade/downgrade"
  - "isCurrent fallback: (!subscription && plan.id === 'free') marks Free card as current for users with no active subscription"
  - "handleSubscribe redirects window.location.href to checkout_url — same redirect pattern as handlePortal"
  - "CardTitle shows 'Free plan' literal (not getPlanName(undefined)) when subscription is undefined"

requirements-completed: [BILL-03, BILL-04]

# Metrics
duration: 127
completed: 2026-03-08
---

# Phase 11 Plan 07: Free-Tier Billing UI Gap Closure Summary

**Config-driven subscribe action type and billing-client fixes enabling free-tier users to see correct plan card states and initiate Stripe Checkout from the billing page**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-08T17:34:16Z
- **Completed:** 2026-03-08T17:36:23Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Added "subscribe" to BillingActionType and set no_subscription: ["subscribe"] in billing.config.ts — plan cards now receive allowed actions for free-tier state
- Fixed plan card isCurrent logic: Free plan card shows "Current plan" (disabled) when user has no active subscription (fallback: `!subscription && plan.id === "free"`)
- Added canSubscribe check to showButton derivation — Pro and Enterprise plan cards show "Subscribe to Pro" / "Subscribe to Enterprise" enabled buttons for free-tier users
- Added handleSubscribe handler that calls createCheckoutSessionAction and redirects to checkout_url on success
- Fixed plan overview empty-state: CardTitle renders "Free plan" (not getPlanName(undefined) → "No plan"), CardContent renders full sentence "No active subscription. Upgrade to a paid plan below."
- Imported createCheckoutSessionAction in page.tsx and passed it as a prop to BillingClient

## Task Commits

Each task was committed atomically:

1. **Task 1: Add subscribe action type and no_subscription actions to billing.config.ts** - `eeeb33a` (feat)
2. **Task 2: Fix billing-client.tsx — subscribe handler, isCurrent fallback, empty-state, prop wiring** - `ae8bcd9` (feat)

## Files Created/Modified

- `apps/web/billing.config.ts` - Added "subscribe" to BillingActionType union; set no_subscription: ["subscribe"]
- `apps/web/app/(dashboard)/billing/billing-client.tsx` - createCheckoutSessionAction prop, handleSubscribe handler, isCurrent fallback, canSubscribe button logic, empty-state fix
- `apps/web/app/(dashboard)/billing/page.tsx` - Import and pass createCheckoutSessionAction prop to BillingClient

## Decisions Made

- "subscribe" is a distinct action type from "upgrade" to signal free-tier checkout path — no active subscription exists to upgrade from, so the action triggers createCheckoutSessionAction rather than changePlanAction.
- Free-tier isCurrent fallback uses the literal plan ID "free" (matches billingConfig.plans[0].id) rather than a sentinel from the API — keeps the logic self-contained in the config layer.
- handleSubscribe follows the same redirect pattern as handlePortal: set window.location.href on success, toast.error on failure.
- CardTitle shows the literal string "Free plan" (not getPlanName(undefined)) when subscription is undefined — getPlanName(undefined) returns "No plan" which was causing the "No PlanNo active subscription" run-on.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all verification checks passed on first attempt. TypeScript compiled with zero errors after all changes.

## Next Phase Readiness

- Free-tier billing UI is now correct for users with no active subscription
- Clicking "Subscribe to Pro" / "Subscribe to Enterprise" triggers createCheckoutSessionAction and redirects to Stripe Checkout
- Plan overview shows coherent "Free plan" heading with descriptive empty-state text
- All three UAT gaps addressed by plans 11-06 and 11-07 are resolved

---

_Phase: 11-api-endpoints-billing-frontend_
_Completed: 2026-03-08_

## Self-Check: PASSED

- billing.config.ts: FOUND
- billing-client.tsx: FOUND
- page.tsx: FOUND
- 11-07-SUMMARY.md: FOUND
- Commit eeeb33a (Task 1): FOUND
- Commit ae8bcd9 (Task 2): FOUND
