---
status: resolved
trigger: "Investigate why plan cards on the billing page (/billing) are missing action buttons and current plan designation."
created: 2026-03-08T00:00:00.000Z
updated: 2026-03-11T00:00:00.000Z
---

## Current Focus

hypothesis: confirmed — see Resolution
test: n/a
expecting: n/a
next_action: fix applied by implementor

## Symptoms

expected: Plan cards show action buttons (Upgrade/Select) and current plan designation (Current plan button, disabled)
actual: Cards render with name and features but no buttons at all; no current plan designation; overview shows "No Plan / No active subscription"
errors: none (page loads without error)
reproduction: Navigate to /billing as any user in dev environment
started: UAT phase 11 — first manual test

## Eliminated

- hypothesis: Component not rendering at all
  evidence: User reports seeing cards with name and features
  timestamp: 2026-03-08

- hypothesis: billingConfig.sections visible:false hiding sections
  evidence: All three sections have visible:true in billing.config.ts
  timestamp: 2026-03-08

- hypothesis: Server action errors breaking the page
  evidence: Page loads without errors; invoices section passes UAT
  timestamp: 2026-03-08

## Evidence

- timestamp: 2026-03-08
  checked: billing-client.tsx lines 262-308 (plan card rendering)
  found: |
  Button render is gated on two conditions:
  1. isCurrent (plan.id === subscription?.plan_id) — shows "Current plan" disabled button
  2. showButton = !isCurrent && (canUpgrade || canDowngrade) — shows "Select" button
     Both depend on subscription?.plan_id being non-null AND matching a plan id in billingConfig.plans
     implication: If subscription is undefined OR plan_id is null/wrong, no button renders

- timestamp: 2026-03-08
  checked: billing-client.tsx lines 100-102 (allowedActions derivation)
  found: |
  subscriptionState = deriveSubscriptionState(subscription)
  allowedActions = billingConfig.actions[subscriptionState] ?? []
  deriveSubscriptionState returns "no_subscription" when subscription is undefined
  billingConfig.actions["no_subscription"] = [] (empty array)
  canUpgrade = allowedActions.includes("upgrade") → FALSE
  canDowngrade = allowedActions.includes("downgrade") → FALSE
  implication: Even if subscription exists, if plan_id is null, isCurrent is false for ALL plans
  and canUpgrade/canDowngrade are both false → showButton = false for ALL cards → no buttons

- timestamp: 2026-03-08
  checked: page.tsx line 13-15 (server data fetch)
  found: |
  api.getBillingSubscription().catch(() => undefined)
  If the endpoint returns 404, subscription is set to undefined in BillingClient
  implication: A user with no Subscription record in DB gets subscription=undefined → no buttons

- timestamp: 2026-03-08
  checked: services.py get_subscription_detail() lines 103-111
  found: |
  If Subscription.DoesNotExist, raises ServiceError(status_code=404)
  getBillingSubscription() in server.ts does NOT catch — it throws on non-ok response
  page.tsx wraps with .catch(() => undefined) catching the 404 → subscription=undefined
  implication: Free-tier user with no subscription record → subscription=undefined → deriveSubscriptionState → "no_subscription" → allowedActions=[] → no buttons

- timestamp: 2026-03-08
  checked: services.py get_subscription_detail() lines 113-128 (plan_id resolution)
  found: |
  Even when a Subscription record exists, plan_id resolution: 1. Calls adapter.retrieve_subscription(stripe_subscription_id) 2. Gets current_price_id from response 3. Looks up PlanProviderMapping with that price_id
  StubAdapter.retrieve_subscription returns {"current_price_id": "price_stub_monthly"}
  For plan_id to resolve, a PlanProviderMapping row with price_id="price_stub_monthly" must exist in DB
  implication: In dev, if PlanProviderMapping table is empty (no seed data), plan_id resolves to None even when subscription exists → isCurrent = (plan.id === null) → false for all plans → "Current plan" button never shows

- timestamp: 2026-03-08
  checked: billingConfig.actions in billing.config.ts
  found: |
  no_subscription: [] ← no upgrade/downgrade actions
  active: ["upgrade", "downgrade", "cancel", "portal"]
  canceled: [] ← no upgrade/downgrade actions either
  implication: Even if subscription is fetched (status="active"), plan_id must match a billingConfig.plans[].id for "Current plan" to show. And allowedActions must include "upgrade"/"downgrade" for Select buttons to show.

## Resolution

root_cause: |
TWO compounding root causes:

ROOT CAUSE A — No buttons on any card (major, affects all users):
The plan card button logic in billing-client.tsx requires BOTH:
(a) subscription?.plan_id to equal a plan's id (for "Current plan" button), OR
(b) allowedActions to include "upgrade" or "downgrade" (for "Select" button)

For a free-tier user (no Subscription DB record): - getBillingSubscription() hits the backend which raises 404 - page.tsx catches the error and passes subscription=undefined to BillingClient - deriveSubscriptionState(undefined) → "no_subscription" - billingConfig.actions["no_subscription"] = [] — intentionally empty - canUpgrade=false, canDowngrade=false → showButton=false for ALL cards - No "Current plan" button because plan_id=undefined matches nothing
RESULT: All cards render with zero buttons.

ROOT CAUSE B — plan_id is null even when subscription exists (medium):
Even when a Subscription DB record exists: - plan_id is resolved by looking up PlanProviderMapping for the price_id returned by the adapter - StubAdapter returns price_id="price_stub_monthly" - If PlanProviderMapping table has no row with price_id="price_stub_monthly", plan_id stays None - isCurrent = (plan.id === null) → false for all plans - "Current plan" designation never renders

THE DESIGN GAP:
The billingConfig intentionally has no_subscription:[] — meaning "no actions for free users".
But the billing page was designed assuming paid subscribers only. Free-tier users who are on
the page see empty cards because there's no "subscribe" action type, and no plan is "current".

fix: |
TWO fixes needed:

FIX A — Add "no_subscription" action support in billing.config.ts:
Change: no_subscription: []
To: no_subscription: ["upgrade"] (or a new action type like "subscribe")
This allows canUpgrade=true for free-tier users, making Select buttons visible on non-free plans.

Additionally, handle the "free" plan as current for no_subscription state:
In billing-client.tsx, derive isCurrent differently when subscription is undefined:
isCurrent = subscription === undefined ? plan.id === "free" : plan.id === subscription?.plan_id
(or whatever the free plan's id is per billingConfig)

FIX B — Seed PlanProviderMapping for dev/stub environment:
Add a data migration or fixture that creates PlanProviderMapping rows mapping
"price_stub_monthly" → plan_id (e.g. "pro"), provider="stub", billing_period="monthly"
So plan_id resolves correctly when StubAdapter is in use.

verification: |
FIX A — billing.config.ts + billing-client.tsx:

- billing.config.ts: no_subscription now includes "subscribe" action → canSubscribe=true for free users → plan cards show "Subscribe to Pro" / "Subscribe to Enterprise" buttons.
- billing-client.tsx: isCurrent fallback (!subscription && plan.id === "free") → Free plan card shows "Current plan" (disabled) for users with no subscription.
- billing-client.tsx: showButton gated on canSubscribe as well as canUpgrade/canDowngrade.
  Both changes were already applied before this session.

FIX B — PlanProviderMapping stub seed:

- Migration 0002 seeded ("pro", "stub", "monthly") with price_id="price_stub_pro_monthly".
- StubAdapter.retrieve_subscription() returns {"current_price_id": "price_stub_monthly"}.
- Mismatch meant plan_id resolved to None for any subscriber in dev.
- Migration 0003 updated the ("pro", "stub", "monthly") row to price_id="price_stub_monthly".
- Also corrected the STUB_MAPPINGS list in 0002 for future fresh DB setups.
- Verified via Django shell: pro/stub/monthly → price_stub_monthly.

files_changed:

- apps/web/billing.config.ts (no_subscription: ["subscribe"])
- apps/web/app/(dashboard)/billing/billing-client.tsx (isCurrent free fallback + canSubscribe)
- apps/api/apps/billing/migrations/0002_plan_provider_mapping_stub_seed.py (corrected STUB_MAPPINGS list)
- apps/api/apps/billing/migrations/0003_fix_stub_pro_monthly_price_id.py (new — fixes already-seeded DB row)
