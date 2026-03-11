---
phase: 11-api-endpoints-billing-frontend
verified: 2026-03-08T21:00:00Z
status: passed
score: 8/8 must-haves verified
re_verification:
  previous_status: gaps_found
  previous_score: 7/8
  gaps_closed:
    - "All billing tests pass GREEN — 63 passed, 1 skipped, 0 failed (price_id collision fixed by plan 11-08)"
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "Past-due banner smoke test"
    expected: "Set subscription status to 'past_due' in Django shell, navigate to any dashboard page, amber Alert banner appears above main content with 'Update payment method' CTA that opens Stripe portal"
    why_human: "UAT was skipped — could not set up past_due state during testing. Banner render is conditional on live billing status and requires DB mutation + browser check."
---

# Phase 11: API Endpoints + Billing Frontend Verification Report

**Phase Goal:** Developers scaffolding a new project have a working billing UI out of the box — the /billing page displays current plan and payment history, and users can upgrade, downgrade, cancel, and manage payment methods without any custom backend code

**Verified:** 2026-03-08T21:00:00Z
**Status:** human_needed
**Re-verification:** Yes — after gap closure plan 11-08 (price_id collision fix)

---

## Goal Achievement

### Observable Truths

| #   | Truth                                                                                            | Status                                     | Evidence                                                                                                                                                                                                    |
| --- | ------------------------------------------------------------------------------------------------ | ------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | /billing page renders current plan, billing period, and next renewal date                        | VERIFIED                                   | billing-client.tsx renders plan_overview section with CardTitle/CardDescription/CardContent showing plan name, billing_period, current_period_end                                                           |
| 2   | /billing page renders payment history table with invoice status and Stripe-hosted download links | VERIFIED                                   | payment_history section in billing-client.tsx renders Table with Date/Amount/Status/Invoice columns; invoice_url renders as anchor with target="\_blank"                                                    |
| 3   | Users can upgrade/downgrade with proration preview Sheet modal before confirming                 | VERIFIED                                   | handlePlanSelect calls previewProrationAction, opens Sheet in "proration" mode with amount_due_now + next_invoice_total; handleConfirmPlanChange wired to changePlanAction                                  |
| 4   | Users can cancel subscription via Sheet modal showing period-end date (not immediate deletion)   | VERIFIED                                   | cancel Sheet renders cancelModalBody(formatIsoDate(current_period_end)), "Cancel subscription" button calls cancelSubscriptionAction                                                                        |
| 5   | Users can manage payment methods via Stripe Customer Portal redirect                             | VERIFIED                                   | handlePortal calls createPortalSessionAction → window.location.href = portal_url; portal button shown per billingConfig.actions[subscriptionState]                                                          |
| 6   | past_due banner displays in dashboard layout when payment fails                                  | VERIFIED (code) / NEEDS HUMAN (smoke test) | layout.tsx is async, fetches getBillingStatus() in try/catch, renders PastDueBanner when status.status === "past_due"; PastDueBanner is self-contained client component importing createPortalSessionAction |
| 7   | /billing/return?session_id=xxx renders success state and auto-redirects after 3 seconds          | VERIFIED                                   | return/page.tsx reads searchParams.get("session_id"), useEffect sets 3000ms timeout to router.replace("/billing"), renders "Subscription activated" heading                                                 |
| 8   | All billing tests pass GREEN — no regressions                                                    | VERIFIED                                   | 63 passed, 1 skipped, 0 failed — price_id collision fixed by plan 11-08 updating conftest.py fixture to use "price_stub_pro_monthly" consistent with migration 0002                                         |

**Score:** 8/8 truths verified

---

## Required Artifacts

| Artifact                                                                   | Expected                                                                                | Status   | Details                                                                                                                                                                                                                    |
| -------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `apps/api/apps/billing/schemas.py`                                         | 10 Ninja schemas for all billing endpoints                                              | VERIFIED | BillingStatusOut, SubscriptionDetailOut, InvoiceOut, InvoiceListOut, PlanChangeIn, ProrationPreviewIn, ProrationPreviewOut, PortalSessionOut, CheckoutSessionIn, CheckoutSessionOut — all present with correct field types |
| `apps/api/apps/billing/controllers.py`                                     | BillingController with 9 routes (8 original + subscribe_plan)                           | VERIFIED | All 9 routes implemented, delegate 100% to self.service, no ORM access in controller                                                                                                                                       |
| `apps/api/apps/billing/services.py`                                        | BillingService with get_status() and get_subscription_detail()                          | VERIFIED | Both methods present; get_status returns sentinel all-None for no-subscription users; get_subscription_detail resolves plan_id from PlanProviderMapping                                                                    |
| `apps/api/tests/billing/test_controllers.py`                               | 8 GREEN controller tests                                                                | VERIFIED | 8 passed, 0 failed                                                                                                                                                                                                         |
| `apps/api/tests/billing/test_services.py`                                  | All service tests GREEN                                                                 | VERIFIED | 55 passed, 1 skipped, 0 failed (price_id collision resolved by plan 11-08)                                                                                                                                                 |
| `apps/api/apps/billing/migrations/0002_plan_provider_mapping_stub_seed.py` | Data migration seeding 4 stub PlanProviderMapping rows                                  | VERIFIED | Migration exists with RunPython seeding pro/monthly, pro/annual, enterprise/monthly, enterprise/annual for provider="stub"; conftest fixtures now aligned to use matching price_id values                                  |
| `apps/web/billing.config.ts`                                               | BillingConfig with 5 types, 3 sections, 3 plans, 6 subscription state actions, all copy | VERIFIED | BillingActionType includes "subscribe"; actions.no_subscription = ["subscribe"]; all 3 sections visible; all 9 copy fields present                                                                                         |
| `apps/web/src/lib/api/server.ts`                                           | ServerApi extended with 4 billing read methods + 5 billing type interfaces              | VERIFIED | getBillingStatus, getBillingSubscription, listBillingInvoices, previewBillingProration implemented via upstreamFetch; BillingStatusOut/SubscriptionDetailOut/InvoiceOut/InvoiceListOut/ProrationPreviewOut exported        |
| `apps/web/src/actions/billing-actions.ts`                                  | 6 server actions (5 original + createCheckoutSessionAction)                             | VERIFIED | All 6 exported: changePlanAction, cancelSubscriptionAction, reactivateSubscriptionAction, createPortalSessionAction, previewProrationAction, createCheckoutSessionAction                                                   |
| `apps/web/app/(dashboard)/layout.tsx`                                      | Async layout with getBillingStatus fetch + conditional PastDueBanner                    | VERIFIED | async function DashboardLayout; getBillingStatus() wrapped in try/catch; {isPastDue && <PastDueBanner />}                                                                                                                  |
| `apps/web/src/components/dashboard/past-due-banner.tsx`                    | Self-contained client component with portal CTA                                         | VERIFIED | "use client"; imports createPortalSessionAction directly; handlePortalClick calls action and redirects                                                                                                                     |
| `apps/web/app/(dashboard)/billing/page.tsx`                                | Async server component fetching subscription + invoices in parallel                     | VERIFIED | Promise.all([getBillingSubscription, listBillingInvoices]); passes all 6 actions to BillingClient as props                                                                                                                 |
| `apps/web/app/(dashboard)/billing/billing-client.tsx`                      | Client component with all interactivity                                                 | VERIFIED | "use client"; 3 sections rendered; Sheet modals for proration/cancel; subscribe handler wired to createCheckoutSessionAction; free-tier isCurrent fallback                                                                 |
| `apps/web/app/(dashboard)/billing/return/page.tsx`                         | Post-checkout return page                                                               | VERIFIED | Reads session_id from searchParams; useEffect timeout 3000ms to router.replace("/billing"); "Subscription activated" heading                                                                                               |
| `apps/web/src/components/dashboard/sidebar.tsx`                            | Billing nav item with CreditCard icon                                                   | VERIFIED | CreditCard imported from lucide-react; dashboardNavItems includes {title: "Billing", href: "/billing", icon: CreditCard, description: "Plan and payment history"}                                                          |

---

## Key Link Verification

| From                 | To                            | Via                                                | Status | Details                                                                                                                                                                                          |
| -------------------- | ----------------------------- | -------------------------------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `layout.tsx`         | `server.ts`                   | `api.getBillingStatus()` in async layout           | WIRED  | Confirmed: import getServerApi + call getBillingStatus in try/catch                                                                                                                              |
| `billing/page.tsx`   | `server.ts`                   | `getBillingSubscription() + listBillingInvoices()` | WIRED  | Promise.all with both calls; .catch() fallbacks prevent unhandled rejections                                                                                                                     |
| `billing-client.tsx` | `billing.config.ts`           | `import { billingConfig }`                         | WIRED  | billingConfig imported for sections, plans, actions, copy                                                                                                                                        |
| `billing-client.tsx` | `billing-actions.ts`          | All 6 action props called in handlers              | WIRED  | changePlanAction, cancelSubscriptionAction, reactivateSubscriptionAction, createPortalSessionAction, previewProrationAction, createCheckoutSessionAction all called in their respective handlers |
| `billing-actions.ts` | `/api/v1/billing/*` endpoints | `api.client.POST(...)` + `upstreamFetch`           | WIRED  | Each action calls the correct endpoint; revalidatePath("/billing") on mutations                                                                                                                  |
| `controllers.py`     | `services.py`                 | `self.service.{method}(request.user, ...)`         | WIRED  | 9 controller routes delegate exclusively to self.service; confirmed no ORM imports in controllers.py                                                                                             |
| `services.py`        | `models.py`                   | `PlanProviderMapping.objects.filter(...)`          | WIRED  | get_subscription_detail resolves plan_id via PlanProviderMapping query                                                                                                                           |
| `billing-actions.ts` | `next/cache`                  | `revalidatePath('/billing')` after mutations       | WIRED  | changePlanAction, cancelSubscriptionAction, reactivateSubscriptionAction all call revalidatePath                                                                                                 |

---

## Requirements Coverage

| Requirement | Source Plans                      | Description                                                                         | Status                                      | Evidence                                                                                                                                                                                      |
| ----------- | --------------------------------- | ----------------------------------------------------------------------------------- | ------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| INV-01      | 11-01, 11-02                      | API endpoint returns paginated list of invoices for authenticated user              | SATISFIED                                   | GET /api/v1/billing/invoices → InvoiceListOut{invoices, total}; test_list_invoices + test_list_invoices_fields both pass                                                                      |
| BILL-01     | 11-01, 11-02, 11-04, 11-05        | /billing page displays current plan, billing period, and next renewal date          | SATISFIED                                   | billing-client.tsx plan_overview section renders: CardTitle (plan name), CardDescription (billing_period + " billing"), CardContent (Renews + current_period_end)                             |
| BILL-02     | 11-01, 11-02, 11-04, 11-05        | /billing page displays payment history table with status and invoice download links | SATISFIED                                   | payment_history section renders Table; invoice_url as anchor with target="\_blank"; empty state via billingConfig.copy.emptyInvoices                                                          |
| BILL-03     | 11-03, 11-04, 11-06, 11-07        | User can initiate plan upgrade/downgrade with proration preview modal               | SATISFIED                                   | Plan cards render Subscribe/Upgrade/Downgrade buttons; proration Sheet shows amount_due_now + next_invoice_total before confirming; createCheckoutSessionAction for free-tier                 |
| BILL-04     | 11-03, 11-04, 11-07               | User can cancel subscription from billing page                                      | SATISFIED                                   | Cancel button shown when allowedActions includes "cancel"; Sheet modal with period-end date; cancelSubscriptionAction wired; reactivate button replaces cancel when cancel_at_period_end=true |
| BILL-05     | 11-04, 11-05                      | /billing/return page handles post-Stripe-Checkout redirect                          | SATISFIED                                   | return/page.tsx reads session_id, shows "Subscription activated", auto-redirects after 3s; no session_id case shows fallback with Return to billing link                                      |
| BILL-06     | 11-03, 11-04, 11-05               | Stripe Customer Portal redirect available for payment method management             | SATISFIED                                   | createPortalSessionAction calls /api/v1/billing/portal-session; portal button shown per actions config; window.location.href redirect on success                                              |
| BILL-07     | 11-01, 11-02, 11-03, 11-04, 11-05 | past_due subscription banner displayed in dashboard when payment fails              | SATISFIED (code) / NEEDS HUMAN (smoke test) | layout.tsx fetches billing status server-side; PastDueBanner renders when status.status === "past_due"; UAT required                                                                          |

All 8 required IDs accounted for across plans. No orphaned requirements detected.

---

## Anti-Patterns Found

| File                                      | Lines          | Pattern                                                       | Severity | Impact                                                                                                                 |
| ----------------------------------------- | -------------- | ------------------------------------------------------------- | -------- | ---------------------------------------------------------------------------------------------------------------------- |
| `apps/web/src/actions/billing-actions.ts` | 23,38,51,66,96 | `// TODO: use generated types after turbo run generate:types` | Info     | Intentional deferral — documented in plans; `as any` casts are isolated, do not propagate type holes to callers        |
| `apps/web/src/lib/api/server.ts`          | 23,123         | `// TODO: replace with generated @repo/api-client types`      | Info     | Same intentional deferral — types are fully declared locally as BillingStatusOut etc.; no actual type holes in callers |

No blocker anti-patterns remain. The migration/fixture price_id collision (previously Blocker) is resolved.

---

## Human Verification Required

### 1. Past-Due Banner Display

**Test:** In Django shell: `Subscription.objects.filter(customer__user__email="your@user.com").update(status="past_due")`. Then log in and navigate to /dashboard.
**Expected:** Amber alert banner appears above main content reading "Your payment failed. Update your payment method to continue access." with an "Update payment method" button. Clicking the button should redirect to the Stripe Customer Portal URL.
**Why human:** UAT was skipped during Plan 05 testing — tester could not set up past_due state at the time. Banner render is conditional on live DB state and portal redirect requires Stripe session creation.

---

## Re-verification Summary

**Gap closed:** The 1 failing gap from the initial verification (3 service tests failing due to price_id mismatch between migration 0002 and conftest fixtures) was resolved by plan 11-08. The fix aligned the conftest `plan_mapping` fixture to use `"price_stub_pro_monthly"` consistent with what migration 0002 seeds, rather than the previously expected `"price_pro_monthly"`.

**Test run result:** `63 passed, 1 skipped, 0 failed in 30.34s` — confirmed clean pass across all billing tests.

**Remaining item:** The past_due banner requires a human smoke test against a live DB + browser. This is not a code gap — the implementation is present and wired — but the runtime behavior cannot be verified programmatically.

---

_Verified: 2026-03-08T21:00:00Z_
_Verifier: Claude (gsd-verifier)_
