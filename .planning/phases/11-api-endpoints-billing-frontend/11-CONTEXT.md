# Phase 11: API Endpoints + Billing Frontend - Context

**Gathered:** 2026-03-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Expose BillingService via Django Ninja API endpoints (subscription status, plan change with proration preview, cancel/reactivate, payment history, billing portal session), then build the `/billing` page in the Next.js app. The billing UI is config-driven: structural and functional elements are defined in `billing.config.ts` and consumed by components — visual theming uses shadcn's existing CSS variable system. No new payment provider work, no mobile app work in this phase.

</domain>

<decisions>
## Implementation Decisions

### Config-driven billing UI

- All billing frontend components are **config-driven**. A single `apps/web/billing.config.ts` file controls the functional and structural layer. Visual theming (colors, fonts, radius, spacing) is handled separately by shadcn/ui CSS variables — not in this config.
- The config controls **four things**:
  1. **Page sections & visibility** — which sections appear on `/billing` and in what order (e.g., plan cards, payment history table, usage meter). New projects can hide/reorder sections by editing this file, not touching component code.
  2. **Labels & copy** — button text, section headings, empty state messages, modal copy (e.g., "Cancel subscription", "Reactivate", "Update payment method"). All user-visible strings come from the config.
  3. **Available actions per subscription state** — which action buttons render based on subscription status (e.g., `reactivate` only shows when `cancel_at_period_end=true`). Config declares the action set; components read it.
  4. **Plan tier display data** — plan names, feature lists, badge labels (e.g., "Most Popular"). Mirrors `BILLING_PLANS` on the backend. Prices and status come from the API; plan metadata is config-driven. No extra API call needed.
- Components consume config via **direct import**: `import { billingConfig } from '@/billing.config'`. No React Context provider — works cleanly with Next.js server components.

### Billing nav placement

- `/billing` is a **top-level sidebar nav item** — same level as Dashboard, Profile, Activity, Settings.
- Nav order: Dashboard → Profile → Activity → Settings → **Billing** (billing is infrastructure, not primary workflow).
- Icon: `CreditCard` (lucide-react), label: `"Billing"`.
- **No badge** on the nav item for past-due status — the past-due alert is handled by a dashboard-wide banner, not a sidebar indicator.

### Plan display & change flow

- Available plans are shown as **plan cards in a grid**. Current plan is highlighted with a badge. Each card has Upgrade/Downgrade buttons (or "Current plan" label when applicable).
- When a user clicks Upgrade/Downgrade: a **modal dialog opens** showing a two-line proration summary:
  - "Charged today: $X"
  - "Next renewal: $Y on [date]"
  - Two buttons: "Cancel" and "Confirm change"
  - No full line-item breakdown — the `amount_due_now`, `next_invoice_total`, `proration_date` fields from the API are sufficient to render this.
- After confirming a plan change: **Sonner toast** ("Plan updated to Pro.") + **page data revalidates in place** using `revalidatePath('/billing')`. User stays on `/billing`. Consistent with the Settings/Profile update pattern.

### Cancel subscription UX

- Cancel trigger: a "Cancel subscription" button on the current plan card.
- **Confirmation modal** shows:
  - "Your plan cancels on [date]. You keep full access until then."
  - Two buttons: "Keep subscription" (primary) and "Cancel subscription" (destructive/secondary).
  - No feature loss list — keep it honest, not guilt-tripping.
- After cancellation confirmed: toast + page revalidates. The plan card gains a **"Cancels [date]" Badge**. The "Cancel subscription" button is replaced by a **"Reactivate" button**.
- **Reactivation** is in scope for Phase 11. "Reactivate" button calls `BillingService.reactivate_subscription()` via a server action. Same confirm-then-toast flow, no modal needed (reactivation is a lower-stakes action).

### Past-due banner

- Banner appears **dashboard-wide** — renders in the `(dashboard)` layout for all dashboard pages when subscription is `past_due`.
- Visual: shadcn `Alert` component (amber/destructive variant) placed above `<main>` content in the layout.
- Copy: "Your payment failed. Update your payment method to continue access."
- CTA: "Update payment method" button — opens **Stripe Customer Portal** (calls `/api/v1/billing/portal-session` endpoint, redirects to Stripe-hosted portal).
- **Data source**: a lightweight `/api/v1/billing/status` Django Ninja endpoint returns `{status, cancel_at_period_end, current_period_end}`. The `(dashboard)` layout fetches this server-side at render time (no client-side hydration flash). If the user has no subscription, the endpoint returns `{status: null}` — banner does not render.

### API endpoint shape (backend)

Six Django Ninja endpoints required in `apps/billing/controllers.py`:

| Method | Path                                      | Purpose                                                                  |
| ------ | ----------------------------------------- | ------------------------------------------------------------------------ |
| GET    | `/api/v1/billing/status`                  | Lightweight status: `{status, cancel_at_period_end, current_period_end}` |
| GET    | `/api/v1/billing/subscription`            | Full subscription detail for the /billing page                           |
| GET    | `/api/v1/billing/invoices`                | Paginated payment history                                                |
| POST   | `/api/v1/billing/subscription/change`     | Upgrade/downgrade (body: `{plan_id, billing_period}`)                    |
| POST   | `/api/v1/billing/subscription/cancel`     | Cancel (sets cancel_at_period_end=True)                                  |
| POST   | `/api/v1/billing/subscription/reactivate` | Reactivate (clears cancel_at_period_end)                                 |
| POST   | `/api/v1/billing/portal-session`          | Create Stripe portal session, return redirect URL                        |
| POST   | `/api/v1/billing/proration-preview`       | Preview charge before plan change (body: `{plan_id, billing_period}`)    |

Controllers delegate entirely to `BillingService` — no ORM access in controllers.

### Frontend data fetching pattern

- Consistent with existing settings/profile pattern:
  - `page.tsx` (server component) fetches data server-side via `getServerApi()`
  - `billing-client.tsx` (client component) handles interactivity
- Server actions in `src/actions/billing-actions.ts` for all mutations (plan change, cancel, reactivate, portal session).
- No React Query on this page — server actions + `revalidatePath` is sufficient for this mutation pattern.

### Claude's Discretion

- Exact `billing.config.ts` TypeScript type shape (interfaces for section config, action config, plan config)
- Whether `Dialog` (new shadcn install needed) or repurpose `Sheet` for the proration/cancel modals
- Pagination strategy for invoice table (server-side cursor or page offset)
- Skeleton loading states for billing page sections
- Exact layout of plan cards (2-column grid, 3-column, responsive breakpoints)

</decisions>

<specifics>
## Specific Ideas

- **Config-driven philosophy matches the template's core purpose**: the billing module should be something a developer drops into a new project and customizes by editing one config file and swapping CSS variables — not by rewriting components. This is the same philosophy as the AI module's extension points.
- The `billing.config.ts` file should include inline comments explaining what each field controls, so it's self-documenting for developers who are new to the template.
- Plan cards should follow the same Card component pattern as the Settings page — consistent with the established dashboard aesthetic.

</specifics>

<code_context>

## Existing Code Insights

### Reusable Assets

- `Card`, `CardContent`, `CardHeader`, `CardTitle`, `CardDescription` — plan cards and billing sections
- `Table` — payment history table (already installed)
- `Badge` — plan status badges ("Current plan", "Cancels [date]", "Past Due")
- `Button` — action buttons throughout
- `Sheet` — may double as modal for proration/cancel confirmations (already installed; avoids new Dialog install)
- `Skeleton` — loading states for billing sections
- `Alert` — past-due banner (already installed)
- `sonner` (toast) — post-action feedback
- `PreferenceCard` in `src/components/dashboard/` — card pattern with consistent padding/border style to follow
- `DashboardSidebar` in `src/components/dashboard/sidebar.tsx` — add `CreditCard` icon + `/billing` nav item to `dashboardNavItems` array
- `getServerApi()` in `src/lib/api/server` — server-side API client for page-level data fetching
- `ActionResponse<TField>` interface in `src/actions/profile-actions.ts` — reuse this response shape for billing server actions

### Established Patterns

- `page.tsx` (async server component) → `*-client.tsx` (client component with `"use client"`) — follow for `/billing` page
- Server actions: `"use server"` + `getServerApi()` + `revalidatePath()` — follow for all billing mutations
- `ActionResponse<TField>` return shape from server actions — consistent error/success envelope

### Integration Points

- `apps/web/app/(dashboard)/sidebar.tsx` → add Billing to `dashboardNavItems` array
- `apps/web/app/(dashboard)/layout.tsx` → add past-due banner fetch + render above `<main>`
- `apps/web/app/(dashboard)/billing/` → new route directory with `page.tsx` + `billing-client.tsx`
- `apps/web/src/actions/billing-actions.ts` → new server actions file
- `apps/web/billing.config.ts` → new config file at web app root
- `apps/api/apps/billing/controllers.py` → new Ninja controller (auto-discovered via `api.auto_discover_controllers()`)
- `apps/api/apps/billing/schemas.py` → request/response schemas for all 8 endpoints

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within Phase 11 scope.

</deferred>

---

_Phase: 11-api-endpoints-billing-frontend_
_Context gathered: 2026-03-08_
