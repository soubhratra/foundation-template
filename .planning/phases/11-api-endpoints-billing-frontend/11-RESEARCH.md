# Phase 11: API Endpoints + Billing Frontend - Research

**Researched:** 2026-03-08
**Domain:** Django Ninja Extra billing controller + Next.js 15 App Router billing UI
**Confidence:** HIGH

---

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions

**Config-driven billing UI**

- A single `apps/web/billing.config.ts` controls: page sections & visibility, labels & copy, available actions per subscription state, plan tier display data.
- Components import config via direct import (`import { billingConfig } from '@/billing.config'`). No React Context.

**Billing nav placement**

- `/billing` is a top-level sidebar nav item. Nav order: Dashboard → Profile → Activity → Settings → Billing.
- Icon: `CreditCard` (lucide-react), label: `"Billing"`. No badge on nav item.

**Plan display & change flow**

- Plans shown as a card grid. Current plan highlighted with a badge.
- Upgrade/Downgrade triggers a modal showing: "Charged today: $X" / "Next renewal: $Y on [date]" / Cancel + Confirm buttons.
- After confirming: Sonner toast + `revalidatePath('/billing')`. User stays on `/billing`.

**Cancel subscription UX**

- Cancel button on current plan card opens a confirmation modal.
- Modal copy: "Your plan cancels on [date]. You keep full access until then." with "Keep subscription" (primary) + "Cancel subscription" (destructive).
- After cancellation: toast + revalidate. Plan card shows "Cancels [date]" Badge. Cancel button replaced by "Reactivate" button.
- Reactivation is in scope. Uses server action, no modal.

**Past-due banner**

- Renders in `(dashboard)` layout for all dashboard pages when status is `past_due`.
- Uses shadcn `Alert` component. Copy: "Your payment failed. Update your payment method to continue access."
- CTA: "Update payment method" — calls `/api/v1/billing/portal-session`, redirects to Stripe portal.
- Data source: lightweight `/api/v1/billing/status` endpoint fetched server-side in layout.

**API endpoint shape (backend)**

- 8 Django Ninja endpoints in `apps/billing/controllers.py`:
  - GET `/api/v1/billing/status` — `{status, cancel_at_period_end, current_period_end}`
  - GET `/api/v1/billing/subscription` — full subscription detail for `/billing` page
  - GET `/api/v1/billing/invoices` — paginated payment history
  - POST `/api/v1/billing/subscription/change` — `{plan_id, billing_period}`
  - POST `/api/v1/billing/subscription/cancel`
  - POST `/api/v1/billing/subscription/reactivate`
  - POST `/api/v1/billing/portal-session`
  - POST `/api/v1/billing/proration-preview` — `{plan_id, billing_period}`
- Controllers delegate entirely to `BillingService`. No ORM access in controllers.

**Frontend data fetching pattern**

- `page.tsx` (async server component) fetches server-side via `getServerApi()`
- `billing-client.tsx` (client component) handles interactivity
- Server actions in `src/actions/billing-actions.ts` for all mutations
- No React Query — server actions + `revalidatePath` is sufficient

### Claude's Discretion

- Exact `billing.config.ts` TypeScript type shape (interfaces for section config, action config, plan config)
- Whether `Dialog` (new shadcn install needed) or repurpose `Sheet` for proration/cancel modals
- Pagination strategy for invoice table (server-side cursor or page offset)
- Skeleton loading states for billing page sections
- Exact layout of plan cards (2-column grid, 3-column, responsive breakpoints)

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within Phase 11 scope.
</user_constraints>

---

<phase_requirements>

## Phase Requirements

| ID      | Description                                                                               | Research Support                                                                                                                                                             |
| ------- | ----------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| INV-01  | API endpoint returns paginated list of invoices for the authenticated user                | `BillingService.list_invoices()` exists; need `InvoiceListOut` Ninja schema + controller route                                                                               |
| BILL-01 | `/billing` page displays current plan, billing period, and next renewal date              | Subscription model has `status`, `current_period_start`, `current_period_end`; plan name comes from `billing.config.ts` config keyed by `plan_id` from `PlanProviderMapping` |
| BILL-02 | `/billing` page displays payment history table with status and invoice download links     | `BillingService.list_invoices()` → adapter → Stripe invoices list; PDF download deferred to Phase 12 (INV-02) — Phase 11 shows placeholder download link                     |
| BILL-03 | User can initiate plan upgrade/downgrade from billing page (with proration preview modal) | `BillingService.preview_proration()` and `upgrade_subscription()`/`downgrade_subscription()` exist; Sheet (already installed) handles modal                                  |
| BILL-04 | User can cancel subscription from billing page                                            | `BillingService.cancel_subscription()` exists; server action pattern established                                                                                             |
| BILL-05 | `/billing/return` page handles post-Stripe-Checkout redirect (including 3DS/SCA result)   | New route `app/(dashboard)/billing/return/page.tsx`; reads `?session_id=` query param, fetches status, shows success/failure                                                 |
| BILL-06 | Stripe Customer Portal redirect available for payment method management                   | `BillingService.create_portal_session()` exists; POST `/api/v1/billing/portal-session` returns `{portal_url}`; server action redirects                                       |
| BILL-07 | `past_due` subscription banner displayed in dashboard when payment fails                  | GET `/api/v1/billing/status` fetched in `(dashboard)/layout.tsx`; `Alert` component already installed                                                                        |

</phase_requirements>

---

## Summary

Phase 11 bridges the fully-implemented backend service layer (Phase 10) and the user-facing billing UI. The heavy lifting is done: `BillingService` has all eight operations, `StubAdapter` provides deterministic test doubles, and all fixtures exist. This phase wires those services to HTTP endpoints (Django Ninja controller + schemas) and builds the Next.js billing page using established patterns from the settings/profile pages.

The architecture is well-defined and internally consistent. Server component pages call `getServerApi()` for reads, server actions (`"use server"` + `revalidatePath`) handle mutations, and Sonner toasts provide post-action feedback. The config-driven approach means `billing.config.ts` is the single developer-facing customization surface — components read it directly, no React Context needed.

The primary discretion areas are modal strategy (Sheet vs Dialog) and `billing.config.ts` type shape. Sheet is already installed and can serve double-duty for the proration/cancel confirmation dialogs. Dialog would require a new `npx shadcn add dialog` step. Sheet is recommended to avoid new installs and keep the component inventory minimal.

**Primary recommendation:** Use Sheet for proration preview and cancel confirmation modals (already installed). Define `billing.config.ts` types as three named interfaces — `BillingSection`, `BillingAction`, and `BillingPlanDisplay` — composed into a single `BillingConfig` root type.

---

## Standard Stack

### Core (already in project, verified by codebase inspection)

| Library                  | Version   | Purpose                                                    | Why Standard                                             |
| ------------------------ | --------- | ---------------------------------------------------------- | -------------------------------------------------------- |
| Django Ninja Extra       | ~0.22     | `@api_controller` + `ControllerBase` for billing endpoints | Project standard; all existing controllers use it        |
| Ninja Schema             | (bundled) | Request/response typing for Ninja endpoints                | Required for OpenAPI type generation                     |
| BillingService           | local     | All billing business logic                                 | Already implemented in Phase 10                          |
| Next.js App Router       | 15+       | Server components + server actions                         | Project standard                                         |
| `getServerApi()`         | local     | Server-side API client with cookie forwarding              | Established pattern: profile, settings pages use it      |
| `ActionResponse<TField>` | local     | Server action return envelope                              | Defined in `profile-actions.ts`, reuse directly          |
| sonner                   | installed | Toast notifications                                        | Already used for profile/settings mutations              |
| shadcn/ui: Alert         | installed | Past-due banner                                            | `apps/web/src/components/ui/alert.tsx` confirmed present |
| shadcn/ui: Sheet         | installed | Modal dialogs (proration preview, cancel confirm)          | Confirmed installed; used in sidebar mobile nav          |
| shadcn/ui: Badge         | installed | Plan status labels, "Cancels [date]"                       | Confirmed installed                                      |
| shadcn/ui: Table         | installed | Invoice history                                            | Confirmed installed                                      |
| shadcn/ui: Card          | installed | Plan cards, billing sections                               | Confirmed installed                                      |
| shadcn/ui: Skeleton      | installed | Loading states                                             | Confirmed installed                                      |

### Not Installed (avoid or install explicitly)

| Component     | Status                | Decision                                                     |
| ------------- | --------------------- | ------------------------------------------------------------ |
| shadcn Dialog | NOT installed         | Use Sheet instead for modals — avoids new install            |
| React Query   | NOT used on this page | Server actions + revalidatePath is sufficient per CONTEXT.md |

**Installation (new deps needed):** None. All required UI components are installed. No new Python packages needed either — `stripe` SDK already present from Phase 9.

---

## Architecture Patterns

### Recommended File Structure (new files only)

```
apps/api/apps/billing/
├── controllers.py          # NEW — 8 Ninja Extra endpoints
└── schemas.py              # NEW — Ninja request/response schemas

apps/web/
├── billing.config.ts                          # NEW — config root
└── app/(dashboard)/
    ├── layout.tsx                             # MODIFY — add past-due banner fetch
    └── billing/
        ├── page.tsx                           # NEW — async server component
        ├── billing-client.tsx                 # NEW — client component
        └── return/
            └── page.tsx                       # NEW — post-checkout return handler

apps/web/src/
├── actions/
│   └── billing-actions.ts                    # NEW — server actions for mutations
└── components/
    └── dashboard/
        └── sidebar.tsx                       # MODIFY — add CreditCard + /billing
```

### Pattern 1: Django Ninja Extra Controller (billing/controllers.py)

**What:** Single `@api_controller` class with all 8 billing endpoints. Auth: `[SessionAuth(), jwt_token_auth]`. Permissions: `[IsAuthenticated]`.

**When to use:** Consistent with `UserController` in `accounts/controllers.py` — one controller per domain.

**Example (verified from accounts/controllers.py):**

```python
# Source: apps/api/apps/accounts/controllers.py (project codebase)
from ninja.security import SessionAuth
from ninja_extra import ControllerBase, api_controller, route
from ninja_extra.permissions import IsAuthenticated
from allauth.headless.contrib.ninja.security import jwt_token_auth

from apps.billing.services import BillingService
from .schemas import (
    BillingStatusOut, SubscriptionDetailOut, InvoiceListOut,
    PlanChangeIn, ProrationPreviewIn, ProrationPreviewOut, PortalSessionOut,
)


@api_controller(
    "/billing",
    tags=["Billing"],
    permissions=[IsAuthenticated],
    auth=[SessionAuth(), jwt_token_auth],
)
class BillingController(ControllerBase):
    def __init__(self):
        self.service = BillingService()

    @route.get("/status", response=BillingStatusOut, url_name="billing-status")
    def get_status(self, request):
        """Lightweight status check for dashboard banner."""
        ...

    @route.get("/subscription", response=SubscriptionDetailOut, url_name="billing-subscription")
    def get_subscription(self, request):
        """Full subscription detail for /billing page."""
        ...

    @route.get("/invoices", response=InvoiceListOut, url_name="billing-invoices")
    def list_invoices(self, request, limit: int = 10):
        """Paginated payment history."""
        ...

    @route.post("/subscription/change", response=SubscriptionDetailOut, url_name="billing-change")
    def change_plan(self, request, payload: PlanChangeIn):
        """Upgrade or downgrade subscription."""
        ...

    @route.post("/subscription/cancel", response=BillingStatusOut, url_name="billing-cancel")
    def cancel_subscription(self, request):
        """Cancel at period end."""
        ...

    @route.post("/subscription/reactivate", response=BillingStatusOut, url_name="billing-reactivate")
    def reactivate_subscription(self, request, payload: PlanChangeIn):
        """Reactivate a pending-cancellation subscription."""
        ...

    @route.post("/portal-session", response=PortalSessionOut, url_name="billing-portal")
    def create_portal_session(self, request):
        """Create Stripe Customer Portal session."""
        ...

    @route.post("/proration-preview", response=ProrationPreviewOut, url_name="billing-proration-preview")
    def preview_proration(self, request, payload: ProrationPreviewIn):
        """Preview charge amounts before committing plan change."""
        ...
```

**Key:** `api.auto_discover_controllers()` in `config/urls.py` already handles registration — no URL change needed. The billing webhook is already registered as a plain Django view, separate from Ninja.

### Pattern 2: Ninja Schemas (billing/schemas.py)

**What:** Input/output schemas for all 8 endpoints. Uses `from ninja import Schema`.

**Verified from adapters.py — exact field shapes:**

```python
# Source: apps/api/apps/billing/adapters.py (project codebase)
from ninja import Schema
from typing import Optional
from datetime import datetime


class BillingStatusOut(Schema):
    status: Optional[str]           # SubscriptionStatus value or None
    cancel_at_period_end: bool
    current_period_end: Optional[datetime]


class SubscriptionDetailOut(Schema):
    status: str
    cancel_at_period_end: bool
    current_period_start: Optional[datetime]
    current_period_end: Optional[datetime]
    plan_id: Optional[str]          # resolved from PlanProviderMapping
    billing_period: Optional[str]   # "monthly" or "annual"
    stripe_subscription_id: str


class InvoiceOut(Schema):
    invoice_id: str
    amount: int                     # cents
    currency: str
    status: str
    created: int                    # unix timestamp
    invoice_url: Optional[str]      # Stripe-hosted invoice URL (for Phase 11 download link)


class InvoiceListOut(Schema):
    invoices: list[InvoiceOut]
    total: int


class PlanChangeIn(Schema):
    plan_id: str
    billing_period: str             # "monthly" | "annual"


class ProrationPreviewIn(Schema):
    plan_id: str
    billing_period: str


class ProrationPreviewOut(Schema):
    amount_due_now: int             # cents
    next_invoice_total: int         # cents
    proration_date: int             # unix timestamp
    currency: str


class PortalSessionOut(Schema):
    portal_url: str
```

**Note on `plan_id` in SubscriptionDetailOut:** The `Subscription` model does NOT store `plan_id` — it only has `stripe_subscription_id`. The controller must resolve plan_id from `PlanProviderMapping` by looking up the mapping where `price_id` matches the subscription's current price. This lookup belongs in a `selectors.py` or as a `BillingService.get_subscription_detail()` method. A simpler approach: add a `get_subscription_detail(user)` method to `BillingService` that fetches the subscription from Stripe and resolves the plan_id from `PlanProviderMapping`.

### Pattern 3: Server Component Page + Client Component

**What:** Exact same split as profile/settings pages.

**Verified from apps/web/app/(dashboard)/profile/page.tsx:**

```typescript
// Source: apps/web/app/(dashboard)/profile/page.tsx (project codebase)
export default async function BillingPage() {
  const api = await getServerApi();
  const [subscription, invoices] = await Promise.all([
    api.getBillingSubscription(),
    api.listBillingInvoices(),
  ]);

  return (
    <BillingClient
      subscription={subscription}
      invoices={invoices}
      changePlanAction={changePlanAction}
      cancelSubscriptionAction={cancelSubscriptionAction}
      reactivateSubscriptionAction={reactivateSubscriptionAction}
      createPortalSessionAction={createPortalSessionAction}
      previewProrationAction={previewProrationAction}
    />
  );
}
```

**Note:** `getServerApi()` must be extended with billing methods — it currently only has `getCurrentUser`, `updateCurrentUser`, `requestPasswordChange`. The billing API methods must be added to the `ServerApi` interface in `src/lib/api/server.ts`. These call the generated typed client (`client.GET("/api/v1/billing/subscription")` etc.) after OpenAPI types are regenerated.

### Pattern 4: Server Actions (billing-actions.ts)

**What:** All mutations go through server actions. Pattern verified from `profile-actions.ts`.

```typescript
// Source: apps/web/src/actions/profile-actions.ts (project codebase)
"use server";

import { revalidatePath } from "next/cache";
import { getServerApi } from "@/lib/api/server";
import type { ActionResponse } from "@/actions/profile-actions"; // reuse this type

export async function changePlanAction(
  planId: string,
  billingPeriod: string,
): Promise<ActionResponse> {
  try {
    const api = await getServerApi();
    await api.changeBillingPlan({ plan_id: planId, billing_period: billingPeriod });
    revalidatePath("/billing");
    return { status: "success", message: "Plan updated." };
  } catch (error) {
    return handleActionError(error, "Unable to change plan. Please try again.");
  }
}

// createPortalSessionAction returns portal_url, then client redirects:
export async function createPortalSessionAction(): Promise<
  ActionResponse & { portal_url?: string }
> {
  try {
    const api = await getServerApi();
    const result = await api.createBillingPortalSession();
    return { status: "success", message: "", portal_url: result?.portal_url };
  } catch (error) {
    return handleActionError(error, "Unable to open billing portal.");
  }
}
```

**Key:** The `portal-session` action is the only mutation that returns a URL (for client-side redirect). All others just revalidate `/billing`.

### Pattern 5: Past-Due Banner in Dashboard Layout

**What:** Server-side fetch in `(dashboard)/layout.tsx`. Currently the layout is a synchronous component (`export default function DashboardLayout`). Adding the banner requires making it `async` and calling `getServerApi()`.

**Verified from apps/web/app/(dashboard)/layout.tsx (line 24):**

```typescript
// BEFORE (existing):
export default function DashboardLayout({ children }: DashboardLayoutProps) { ... }

// AFTER (Phase 11):
export default async function DashboardLayout({ children }: DashboardLayoutProps) {
  let billingStatus: BillingStatusOut | null = null;
  try {
    const api = await getServerApi();
    billingStatus = await api.getBillingStatus();
  } catch {
    // Never block layout render due to billing API failure
  }

  const isPastDue = billingStatus?.status === "past_due";

  return (
    <DashboardShellClient>
      <SidebarProvider>
        <DashboardSidebar />
        <SidebarInset>
          <div className="flex min-h-screen flex-col bg-background">
            <DashboardHeader />
            {isPastDue && <PastDueBanner />}  {/* above <main> */}
            <main className="flex-1 p-6">
              <div className="mx-auto flex w-full max-w-5xl flex-col gap-6">
                {children}
              </div>
            </main>
          </div>
        </SidebarInset>
      </SidebarProvider>
    </DashboardShellClient>
  );
}
```

**Critical:** Wrap `getServerApi()` in try/catch so a billing API failure never breaks the dashboard layout. Return `null` status silently and skip the banner.

**Also note:** The layout uses `export const dynamic = "force-dynamic"` — already set, so the async fetch works correctly without static caching issues.

### Pattern 6: billing.config.ts Type Shape (Claude's Discretion)

Recommended TypeScript structure:

```typescript
// apps/web/billing.config.ts

export interface BillingPlanDisplay {
  /** Internal plan ID — must match BILLING_PLANS keys in Django settings */
  id: string;
  /** Display name shown in plan cards */
  name: string;
  /** Feature list for plan card bullet points */
  features: string[];
  /** Optional badge label (e.g. "Most Popular") */
  badge?: string;
}

export type SubscriptionState =
  | "active"
  | "trialing"
  | "past_due"
  | "canceled"
  | "cancel_at_period_end"
  | "no_subscription";

export type BillingActionType = "upgrade" | "downgrade" | "cancel" | "reactivate" | "portal";

export interface BillingSection {
  /** Section identifier used in component logic */
  id: "plan_overview" | "plan_selection" | "payment_history";
  /** Whether this section renders at all */
  visible: boolean;
  /** Section heading text */
  heading: string;
}

export interface BillingConfig {
  sections: BillingSection[];
  plans: BillingPlanDisplay[];
  /** Actions available per subscription state */
  actions: Record<SubscriptionState, BillingActionType[]>;
  copy: {
    cancelModalTitle: string;
    cancelModalBody: (periodEnd: string) => string;
    cancelConfirmButton: string;
    cancelKeepButton: string;
    prorationModalTitle: string;
    reactivateButton: string;
    portalButton: string;
    pastDueBannerBody: string;
    pastDueBannerCta: string;
    emptyInvoices: string;
  };
}

export const billingConfig: BillingConfig = {
  sections: [
    { id: "plan_overview", visible: true, heading: "Current Plan" },
    { id: "plan_selection", visible: true, heading: "Available Plans" },
    { id: "payment_history", visible: true, heading: "Payment History" },
  ],
  plans: [
    { id: "free", name: "Free", features: ["Up to 3 projects", "Community support"] },
    {
      id: "pro",
      name: "Pro",
      features: ["Unlimited projects", "Priority support", "API access"],
      badge: "Most Popular",
    },
    {
      id: "enterprise",
      name: "Enterprise",
      features: ["Everything in Pro", "Dedicated support", "Custom contracts", "SLA"],
    },
  ],
  actions: {
    active: ["upgrade", "downgrade", "cancel", "portal"],
    trialing: ["upgrade", "cancel", "portal"],
    past_due: ["portal"],
    canceled: [],
    cancel_at_period_end: ["reactivate", "portal"],
    no_subscription: [],
  },
  copy: {
    cancelModalTitle: "Cancel subscription?",
    cancelModalBody: (periodEnd) =>
      `Your plan cancels on ${periodEnd}. You keep full access until then.`,
    cancelConfirmButton: "Cancel subscription",
    cancelKeepButton: "Keep subscription",
    prorationModalTitle: "Confirm plan change",
    reactivateButton: "Reactivate",
    portalButton: "Update payment method",
    pastDueBannerBody: "Your payment failed. Update your payment method to continue access.",
    pastDueBannerCta: "Update payment method",
    emptyInvoices: "No invoices yet.",
  },
};
```

### Pattern 7: Sheet as Proration/Cancel Modal

**What:** Use shadcn `Sheet` (already installed) with `side="bottom"` or `side="right"` for the proration preview and cancel confirmation dialogs.

**Why not Dialog:** Dialog is not in the installed component list (`apps/web/src/components/ui/`). Installing it adds `dialog.tsx` and a `@radix-ui/react-dialog` dependency that is already transitively present (Radix is part of shadcn). The `Sheet` component uses the same Radix dialog primitive under the hood. Either would work, but Sheet is already installed.

**Recommendation for planner:** Use Sheet. If the plan card section feels cramped with a sheet, the planner can note "install Dialog via `npx shadcn@latest add dialog`" as a Task 1 Wave 0 step.

### Pattern 8: BILL-05 — /billing/return Page

**What:** A simple Next.js page that handles the post-Stripe-Checkout redirect. Stripe appends `?session_id=cs_xxx` to the success URL.

**Pattern:**

```
app/(dashboard)/billing/return/page.tsx
```

- Reads `searchParams.session_id` (passed by Stripe)
- Shows success state: "Your subscription is active. Redirecting..."
- Shows failure state if session_id is missing or checkout was abandoned
- Auto-redirects to `/billing` after 2–3 seconds using `useRouter().replace('/billing')`
- Minimal page — no API call needed in Phase 11 (webhook already updated subscription state)

### Anti-Patterns to Avoid

- **ORM access in controllers:** All controllers MUST call `BillingService` methods. No `Subscription.objects.get()` in controller methods.
- **Schema-free endpoints:** Every endpoint must have typed `response=` and typed payload. Required for OpenAPI type regeneration.
- **Client-side billing status fetch:** The `past_due` banner data is fetched server-side in layout. Do NOT use client-side `useEffect` for this — it causes flash-of-no-banner.
- **Hardcoding plan names in components:** All plan display data comes from `billing.config.ts`. Components never reference plan names as string literals.
- **Blocking layout on billing failure:** The layout's `getServerApi().getBillingStatus()` must be wrapped in try/catch. A Stripe outage should never break the dashboard.
- **Storing plan_id on Subscription model:** The model has no `plan_id` field by design. Resolve from `PlanProviderMapping` or from the adapter's subscription data.

---

## Don't Hand-Roll

| Problem                       | Don't Build                    | Use Instead                                                          | Why                                                    |
| ----------------------------- | ------------------------------ | -------------------------------------------------------------------- | ------------------------------------------------------ |
| Modal dialog                  | Custom overlay div             | shadcn Sheet (installed)                                             | Handles focus trap, escape key, a11y, backdrop         |
| Toast notifications           | Custom toast state             | sonner (installed)                                                   | Already wired in layout, handles stacking/dismissal    |
| Server-side API client        | Raw fetch in server components | `getServerApi()`                                                     | Already handles cookie forwarding, CSRF, error parsing |
| Action response envelope      | Custom success/error type      | `ActionResponse<TField>` from `profile-actions.ts`                   | Consistent shape across all server actions             |
| Subscription state resolution | Custom status logic            | `SubscriptionStatus` enum from billing models                        | Already covers all Stripe states                       |
| Invoice pagination            | Custom cursor logic            | Stripe's built-in `limit` param via `BillingService.list_invoices()` | Keep it simple — Stripe returns newest-first           |

---

## Common Pitfalls

### Pitfall 1: getServerApi() Missing Billing Methods

**What goes wrong:** `getServerApi()` currently exposes only user-related methods. Calling `api.getBillingStatus()` will be a TypeScript error.
**Why it happens:** The `ServerApi` interface in `src/lib/api/server.ts` must be manually extended with billing methods.
**How to avoid:** After regenerating shared types from OpenAPI spec, add billing methods to `ServerApi` interface AND the returned object in `getServerApi()`. This is a two-step change — both the interface and the implementation.
**Warning signs:** TypeScript error "Property 'getBillingStatus' does not exist on type 'ServerApi'".

### Pitfall 2: plan_id Not on Subscription Model

**What goes wrong:** `SubscriptionDetailOut` needs a `plan_id` field, but `Subscription` model has no `plan_id` column.
**Why it happens:** The adapter pattern deliberately avoids storing provider-specific data on the model. `stripe_subscription_id` is the only link to Stripe.
**How to avoid:** The controller (or a new `BillingService.get_subscription_detail()` method) must resolve `plan_id` via `PlanProviderMapping`. Look up `PlanProviderMapping.objects.filter(provider='stripe', price_id=<stripe_current_price>)`. Alternatively, call `adapter.retrieve_subscription()` (may need to be added to the adapter if not present) to get the current price from Stripe, then resolve locally.
**Simpler approach:** Add `plan_id` and `billing_period` fields to the `Subscription` model and populate them via webhook handlers (the webhook updates these when subscription is created/updated). Check if Phase 10 webhook handlers already set these fields. They do NOT based on `models.py` inspection — so the resolution-from-mapping approach is needed for Phase 11.

### Pitfall 3: Dashboard Layout Turns Async

**What goes wrong:** Making `DashboardLayout` async triggers a Next.js warning or breaks the layout if `DashboardShellClient` (a client component) doesn't support async parent.
**Why it happens:** Server components can be async; client components cannot. The layout is a server component, so making it async is fine. But if `DashboardShellClient` or `SidebarProvider` have issues with async parent rendering, the layout could fail.
**How to avoid:** The layout is already `"force-dynamic"` and is a server component (no `"use client"` directive). Making it `async` is safe and is the standard Next.js App Router pattern. The `PastDueBanner` should be a separate server or client component to keep the layout minimal.

### Pitfall 4: Sheet Bottom Sheet UX on Desktop

**What goes wrong:** `Sheet` with `side="bottom"` looks like a mobile pattern on desktop; `side="right"` is better for desktop but can feel like a slide-out panel, not a confirmation dialog.
**Why it happens:** Sheet is designed as a slide-out panel, not a centered modal.
**How to avoid:** Use `side="bottom"` with a `max-w-md mx-auto` constraint, or install Dialog for a centered modal experience. The planner should decide this in Task 1 and include `npx shadcn@latest add dialog` in Wave 0 if Dialog is preferred.

### Pitfall 5: Invoice Download Link (Phase 11 Scope)

**What goes wrong:** BILL-02 requires "invoice download links," but INV-02 (PDF generation) is deferred to Phase 12.
**Why it happens:** The requirements split invoice listing (Phase 11) from PDF generation (Phase 12).
**How to avoid:** In Phase 11, the invoice download link should use `invoice_url` from Stripe's hosted invoice URL (available via `list_invoices` adapter response). This is a Stripe-hosted link, not a server-generated PDF. Phase 12 will replace this with a server-generated PDF endpoint. Ensure `InvoiceOut` schema includes `invoice_url: Optional[str]` populated from the Stripe invoice's `hosted_invoice_url` field.

### Pitfall 6: OpenAPI Regeneration Required

**What goes wrong:** New billing endpoints won't have TypeScript types in `@repo/api-client` until the OpenAPI spec is regenerated and `packages/shared-types` is updated.
**Why it happens:** The type generation pipeline (Phase 3) must be re-run after any new Ninja endpoints are added.
**How to avoid:** Include OpenAPI type regeneration as a step in the same wave that adds the Django billing controller. Command: `turbo run generate:types` or equivalent. Check `packages/shared-types/` for the regeneration script.

---

## Code Examples

### Example 1: Controller with ServiceError Propagation

```python
# Source: apps/api/config/urls.py — ServiceError handler already registered globally
# Controllers can raise ServiceError; it will be handled by the global exception handler
@route.get("/subscription", response=SubscriptionDetailOut, url_name="billing-subscription")
def get_subscription(self, request):
    """Full subscription detail for /billing page."""
    # BillingService raises ServiceError if no customer found (404)
    # or if subscription doesn't exist
    return self.service.get_subscription_detail(request.user)
```

### Example 2: Server Action with Portal Redirect

```typescript
// Pattern: server action returns portal_url, client component uses router.push()
// Client side:
const result = await createPortalSessionAction();
if (result.status === "success" && result.portal_url) {
  window.location.href = result.portal_url; // external redirect to Stripe
}
```

### Example 3: Proration Preview Flow

```typescript
// 1. User clicks "Upgrade to Pro"
// 2. Client calls previewProrationAction(planId, billingPeriod)
// 3. Server action returns { amount_due_now, next_invoice_total, proration_date }
// 4. Client opens Sheet with proration summary
// 5. User clicks "Confirm" → changePlanAction(planId, billingPeriod)
// 6. Server action calls API, returns success → toast + revalidatePath('/billing')
```

### Example 4: Sidebar Nav Addition

```typescript
// Source: apps/web/src/components/dashboard/sidebar.tsx — dashboardNavItems array
import { Activity, CreditCard, LayoutDashboard, Settings, UserRound } from "lucide-react";

export const dashboardNavItems: DashboardNavItem[] = [
  { title: "Dashboard", href: "/dashboard", icon: LayoutDashboard, description: "..." },
  { title: "Profile", href: "/profile", icon: UserRound, description: "..." },
  { title: "Activity", href: "/activity", icon: Activity, description: "...", badge: "Live" },
  { title: "Settings", href: "/settings", icon: Settings, description: "..." },
  // ADD:
  { title: "Billing", href: "/billing", icon: CreditCard, description: "Plan and payment history" },
];
```

---

## State of the Art

| Old Approach                      | Current Approach                     | When Changed           | Impact                                                           |
| --------------------------------- | ------------------------------------ | ---------------------- | ---------------------------------------------------------------- |
| React Query for billing mutations | Server actions + revalidatePath      | Next.js 13+ App Router | No client-side cache management needed; simpler mutation pattern |
| Stripe-hosted invoice PDFs        | Server-generated PDFs (Phase 12)     | Project decision       | No expiry, rebrandable                                           |
| Stripe.js embedded checkout       | Stripe Checkout hosted page redirect | Project decision       | Avoids PCI scope                                                 |

---

## Open Questions

1. **plan_id Resolution in SubscriptionDetailOut**
   - What we know: `Subscription` model has no `plan_id`. `PlanProviderMapping` maps `plan_id` to `price_id` per provider.
   - What's unclear: The `Subscription` model only stores `stripe_subscription_id`, not the current `price_id`. To resolve `plan_id`, we need the current price either from Stripe (extra API call) or by storing it locally.
   - Recommendation: Add a `get_subscription_detail(user)` method to `BillingService` that calls `adapter.retrieve_subscription()` (a new adapter method, or use the existing `modify_subscription`'s retrieve pattern) to get current `price_id`, then does a `PlanProviderMapping.objects.filter(price_id=...)` lookup. Alternatively, store `plan_id` + `billing_period` on `Subscription` and populate from webhook. The planner should decide which approach based on complexity budget.

2. **Dialog vs Sheet for Modals**
   - What we know: Dialog is not installed. Sheet is installed.
   - What's unclear: Whether Sheet's slide-in motion feels appropriate for a confirmation dialog.
   - Recommendation: Planner chooses. If Sheet: use `side="bottom"` on mobile, constrain width. If Dialog: add `npx shadcn@latest add dialog` as Wave 0 step. Dialog is ~50 lines + the Radix dep is already present transitively, so installation is cheap.

3. **Invoice Pagination Approach**
   - What we know: `BillingService.list_invoices()` takes a `limit` param. Stripe returns newest-first.
   - What's unclear: Whether the page needs cursor-based pagination or if `limit=10` is sufficient for a template.
   - Recommendation: Start with `limit=10`, no cursor. Template projects rarely have >10 invoices in early stages. Add cursor pagination as a v2 enhancement.

---

## Validation Architecture

### Test Framework

| Property           | Value                                                                     |
| ------------------ | ------------------------------------------------------------------------- |
| Framework          | pytest + pytest-django                                                    |
| Config file        | `apps/api/pyproject.toml` (pytest section)                                |
| Quick run command  | `cd apps/api && python -m pytest tests/billing/test_controllers.py -x -q` |
| Full suite command | `cd apps/api && python -m pytest tests/billing/ -q`                       |

### Phase Requirements → Test Map

| Req ID  | Behavior                                                                                              | Test Type         | Automated Command                                                        | File Exists? |
| ------- | ----------------------------------------------------------------------------------------------------- | ----------------- | ------------------------------------------------------------------------ | ------------ |
| INV-01  | GET /billing/invoices returns paginated list for auth user                                            | unit (controller) | `pytest tests/billing/test_controllers.py::test_list_invoices -x`        | ❌ Wave 0    |
| BILL-01 | GET /billing/subscription returns plan name, period, renewal date                                     | unit (controller) | `pytest tests/billing/test_controllers.py::test_get_subscription -x`     | ❌ Wave 0    |
| BILL-02 | Invoices list includes status and download link                                                       | unit (controller) | `pytest tests/billing/test_controllers.py::test_list_invoices_fields -x` | ❌ Wave 0    |
| BILL-03 | POST /billing/subscription/change triggers proration; POST /billing/proration-preview returns amounts | unit (controller) | `pytest tests/billing/test_controllers.py::test_change_plan -x`          | ❌ Wave 0    |
| BILL-04 | POST /billing/subscription/cancel sets cancel_at_period_end=True                                      | unit (controller) | `pytest tests/billing/test_controllers.py::test_cancel_subscription -x`  | ❌ Wave 0    |
| BILL-05 | /billing/return page renders without error                                                            | manual smoke      | N/A — UI-only page                                                       | N/A          |
| BILL-06 | POST /billing/portal-session returns portal_url                                                       | unit (controller) | `pytest tests/billing/test_controllers.py::test_portal_session -x`       | ❌ Wave 0    |
| BILL-07 | GET /billing/status returns {status, cancel_at_period_end, current_period_end}                        | unit (controller) | `pytest tests/billing/test_controllers.py::test_get_status -x`           | ❌ Wave 0    |

### Sampling Rate

- **Per task commit:** `cd apps/api && python -m pytest tests/billing/test_controllers.py -x -q`
- **Per wave merge:** `cd apps/api && python -m pytest tests/billing/ -q`
- **Phase gate:** Full backend suite green + manual smoke of /billing page before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `apps/api/tests/billing/test_controllers.py` — covers all 8 controller endpoints (INV-01, BILL-01 through BILL-07)
- [ ] Fixtures already in `tests/billing/conftest.py` — `billing_service`, `stub_adapter`, `subscription`, `authenticated_client` are all present; no new fixture file needed
- [ ] `apps/api/apps/billing/controllers.py` — the controller file itself (does not exist yet)
- [ ] `apps/api/apps/billing/schemas.py` — the schema file (does not exist yet)

---

## Sources

### Primary (HIGH confidence)

- Project codebase: `apps/api/apps/billing/services.py` — all service method signatures verified
- Project codebase: `apps/api/apps/billing/adapters.py` — adapter return shapes for schemas
- Project codebase: `apps/api/apps/billing/models.py` — field names, SubscriptionStatus enum values
- Project codebase: `apps/api/apps/accounts/controllers.py` — Ninja Extra controller pattern
- Project codebase: `apps/web/src/actions/profile-actions.ts` — ActionResponse type, server action pattern
- Project codebase: `apps/web/src/lib/api/server.ts` — getServerApi() pattern, ServerApi interface
- Project codebase: `apps/web/app/(dashboard)/layout.tsx` — exact layout structure for banner placement
- Project codebase: `apps/web/src/components/dashboard/sidebar.tsx` — dashboardNavItems array
- Project codebase: `apps/web/src/components/ui/` — confirmed installed components list
- Project codebase: `apps/api/tests/billing/conftest.py` — StubAdapter, all billing fixtures
- Project codebase: `apps/api/config/urls.py` — auto_discover_controllers(), ServiceError handler

### Secondary (MEDIUM confidence)

- CONTEXT.md: Locked decisions from /gsd:discuss-phase session (user-reviewed)
- REQUIREMENTS.md: Requirement IDs and descriptions
- ROADMAP.md: Phase boundaries and success criteria

---

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — all libraries verified by direct codebase inspection
- Architecture: HIGH — patterns verified from three existing dashboard pages (profile, settings, activity)
- Pitfalls: HIGH — discovered by reading actual code, not assumptions
- Validation architecture: HIGH — test infrastructure and fixtures verified to exist

**Research date:** 2026-03-08
**Valid until:** 2026-04-07 (stable domain; Next.js App Router server actions pattern is settled)
