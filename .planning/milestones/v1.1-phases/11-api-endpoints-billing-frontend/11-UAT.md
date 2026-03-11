---
status: resolved
phase: 11-api-endpoints-billing-frontend
source:
  - 11-02-SUMMARY.md
  - 11-03-SUMMARY.md
  - 11-04-SUMMARY.md
started: "2026-03-08T12:30:00.000Z"
updated: "2026-03-08T18:00:00.000Z"
---

## Current Test

[testing complete]

## Tests

### 1. Billing nav item in sidebar

expected: Open the dashboard. The sidebar shows a "Billing" nav item with a credit card icon after "Activity". Clicking it navigates to /billing.
result: pass

### 2. Billing page loads for free-tier user

expected: Navigate to /billing. The page loads without errors. You see a plan overview section, a plan selection grid with Free/Pro/Enterprise cards, and a payment history section with an empty-state message (no invoices yet).
result: pass

### 3. Plan cards show features and action buttons

expected: On /billing, the plan cards (Free, Pro, Enterprise) each show a name, a features list, and a button. The current plan (Free) shows a "Current plan" or disabled state; the other plans show "Upgrade" or "Select" buttons.
result: issue
reported: "I see the cards but there is no actions or buttons on them. There is no current plan designation on screen"
severity: major

### 4. Proration preview Sheet opens

expected: Click the Upgrade/Select button on a non-current plan (e.g. Pro). A Sheet slides up from the bottom showing proration amounts — a preview of the cost adjustment before confirming the plan change. A "Confirm" and "Cancel" button are visible.
result: issue
reported: "I see the cards but there is no actions or buttons on them. There is no current plan designation on screen"
severity: major

### 5. Cancel subscription Sheet opens

expected: If you have an active subscription, a Cancel button is visible. Clicking it opens a Sheet modal with a confirmation message (mentioning the period-end date) and a destructive "Cancel subscription" confirm button plus a dismiss option.
result: issue
reported: "Current plan at the top of the billing screen says 'No Plan No active subscription'"
severity: minor

### 6. Payment history section

expected: The /billing page shows a "Payment history" section. If no invoices exist, an empty-state message is displayed (e.g. "No invoices yet" or similar copy from config). The table headers (Date, Amount, Status, Download) are visible.
result: pass

### 7. /billing/return page

expected: Navigate directly to /billing/return?session_id=test. The page shows a success message (e.g. "Payment successful" or "Subscription updated"). After 3 seconds it automatically redirects to /billing.
result: pass

### 8. Past-due banner (conditional)

expected: If you can set a user's subscription_status to "past_due" in the Django shell, log in and navigate to any dashboard page. A warning banner should appear at the top of the layout (above the main content) with a link to manage billing. Skip this test if you cannot easily set up the past_due state.
result: skipped
reason: could not set up past_due state

## Summary

total: 8
passed: 4
issues: 3
pending: 0
skipped: 1

## Gaps

- truth: "Plan cards show action buttons (Upgrade/Select) and current plan designation"
  status: resolved
  reason: "User reported: I see the cards but there is no actions or buttons on them. There is no current plan designation on screen"
  severity: major
  test: 3
  root_cause: "billing.config.ts has no_subscription:[] (no actions defined for free-tier), so canUpgrade=false and showButton=false for all cards. Additionally isCurrent never matches because subscription is undefined for free users."
  artifacts:
  - path: "apps/web/billing.config.ts"
    issue: "no_subscription: [] — no upgrade/subscribe actions defined, gates button rendering to false"
  - path: "apps/web/app/(dashboard)/billing/billing-client.tsx"
    issue: "isCurrent and showButton logic assumes non-null plan_id; no free-tier fallback to mark the free plan as current"
  - path: "apps/web/app/(dashboard)/billing/page.tsx"
    issue: ".catch(() => undefined) swallows 404, subscription=undefined propagates with no free-tier fallback"
  - path: "apps/api/apps/billing/services.py"
    issue: "PlanProviderMapping miss silently returns plan_id=None — no PlanProviderMapping seed data in dev"
    missing:
  - "Add subscribe/upgrade action to no_subscription in billing.config.ts"
  - "Add free-plan isCurrent fallback in billing-client.tsx for no_subscription state"
  - "Add PlanProviderMapping seed/fixture rows for stub adapter price IDs"
    debug_session: ""

- truth: "Clicking Upgrade/Select opens a proration preview Sheet with Confirm and Cancel buttons"
  status: resolved
  reason: "User reported: I see the cards but there is no actions or buttons on them. There is no current plan designation on screen"
  severity: major
  test: 4
  root_cause: "Blocked by same root cause as test 3 — no buttons render so Sheet cannot be triggered"
  artifacts:
  - path: "apps/web/billing.config.ts"
    issue: "no_subscription: [] blocks all button rendering"
    missing:
  - "Fix plan card buttons (same fix as test 3 gap)"
    debug_session: ""

- truth: "Current plan section displays plan name and subscription status clearly; Cancel button visible when subscribed"
  status: resolved
  reason: "User reported: Current plan at the top of the billing screen says 'No Plan No active subscription'"
  severity: minor
  test: 5
  root_cause: "CardTitle always renders getPlanName() which returns 'No plan' when subscription is undefined, then CardContent renders 'No active subscription.' below it with no separator — two orphaned fragments read as one run-on label"
  artifacts:
  - path: "apps/web/app/(dashboard)/billing/billing-client.tsx"
    issue: "Line 191: getPlanName() renders unconditionally even when subscription is undefined. Lines 217-219: 'No active subscription.' in CardContent has no separator from CardTitle, creating run-on text"
    missing:
  - "Suppress CardTitle or replace with unified empty-state when subscription is undefined (e.g. 'No active plan' as single coherent phrase)"
    debug_session: ""
