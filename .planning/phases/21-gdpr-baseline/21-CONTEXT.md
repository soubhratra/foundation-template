# Phase 21: GDPR Baseline - Context

**Gathered:** 2026-03-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement three discrete GDPR/CCPA compliance capabilities: (1) account hard-delete with async Celery cascade through Stripe and PostHog, (2) personal data JSON export as an immediate synchronous response, and (3) a cookie consent banner on the web app that gates PostHog initialization.

This phase does not cover: mobile app deletion/export UI, marketing email opt-out, data retention policies, or a full privacy preference center. CCPA basics (right to delete, right to know, opt-out of analytics) are covered as a side-effect of GDPR-01, GDPR-02, and GDPR-03 — no separate CCPA-specific work needed.

</domain>

<decisions>
## Implementation Decisions

### Account deletion — confirmation

- User must re-enter their current password to confirm deletion
- Standard for destructive irreversible actions; prevents accidental taps and mitigates CSRF
- Implemented as a modal with a password input field and a destructive "Delete my account" button

### Account deletion — cascade order

- Cascade order in `UserDeletionService` Celery task:
  1. Cancel active Stripe subscription immediately (no grace period, no "cancel at period end")
  2. Delete Stripe customer object
  3. Delete PostHog person record via `ObservabilityAdapter.delete_person()`
  4. Call `user.delete()` — Django ORM cascades all related tables (Customer, Subscription, allauth accounts, social accounts)
- Returns HTTP 202 immediately; all cascade steps happen asynchronously in Celery
- `ObservabilityAdapter` ABC gets a new `delete_person(distinct_id: str)` abstract method; `PostHogAdapter` implements it via PostHog's Delete Person API; `NoOpAdapter` is a no-op

### Account deletion — UI placement

- Web app: `/settings` page (new page) with a Danger Zone section at the bottom
- Mobile: out of scope for this phase — deletion is web-only for now
- After successful deletion: session is invalidated, user is redirected to `/` (landing page or login)

### Data export — scope

- Follows GDPR Article 20 / CCPA Right to Know standard practice:
  - `profile`: email, first_name, last_name, date_joined, last_login
  - `social_accounts`: list of connected providers (Google, GitHub, Apple) with provider UID
  - `billing`: subscription_status, plan_id, payment history (amount, currency, date — no raw card data)
- Auth event logs (login timestamps) are operational data — NOT included
- Response is a nested JSON object (not flat) — human-readable and machine-readable

### Data export — delivery

- Synchronous: `GET /api/v1/account/export` returns JSON directly in the HTTP response
- Response header: `Content-Disposition: attachment; filename="my-data.json"` — browser triggers download
- No async task, no email, no time-limited link — user data volume doesn't warrant it

### Cookie consent — banner design

- Fixed bottom bar (not modal — doesn't block content)
- Two buttons: **Accept Analytics** / **Decline**
- Short copy: "We use analytics to improve the app." with a Privacy Policy link
- Dismissing by clicking outside does NOT count as consent — user must explicitly Accept or Decline

### Cookie consent — storage

- `localStorage` key: `analytics_consent` = `'granted'` | `'denied'`
- Banner re-appears if localStorage is cleared or key is absent
- No server-side consent record — client-side only

### Cookie consent — PostHog gating

- PostHog is NOT initialized on page load — current unconditional `posthog.init()` in `providers.tsx` must be refactored
- On Accept: call `posthog.init(...)` with full config (page views, session recording)
- On Decline: `posthog.opt_out_capturing()` (prevents any future init from capturing)
- On subsequent page loads: read `localStorage` key; if `'granted'` → init immediately; if `'denied'` → opt-out; if absent → show banner
- Banner component lives in `apps/web/` as a client component, rendered in root `layout.tsx`

### CCPA basics

- Right to Delete → covered by GDPR-01 (`DELETE /api/v1/account/`)
- Right to Know → covered by GDPR-02 (`GET /api/v1/account/export`)
- Opt-out of analytics → covered by GDPR-03 (Decline button in consent banner)
- No "Do Not Sell My Personal Information" page needed — SaaS product does not sell personal data

### Claude's Discretion

- Exact `UserDeletionService` error handling if Stripe cancel fails (log + continue, or abort?)
- Whether to send a "your account has been deleted" email before deletion (nice-to-have)
- Exact styling of the consent banner (colors, typography — must be cohesive with existing Shadcn/ui theme)
- Whether `/settings` page uses a server or client component layout

</decisions>

<specifics>
## Specific Ideas

- `UserDeletionService` is an orchestrator pattern (matches `BillingService` style) — thin controller, logic in service
- Cookie banner: "We use analytics to improve the app." is the exact copy — keep it minimal
- Export JSON structure: top-level keys `profile`, `social_accounts`, `billing`, `exported_at` (ISO timestamp)

</specifics>

<code_context>

## Existing Code Insights

### Reusable Assets

- `apps/core/observability.py` (`ObservabilityAdapter`, `PostHogAdapter`): needs new `delete_person(distinct_id: str)` abstract method; `PostHogAdapter` implements it via PostHog's Delete Person API; `NoOpAdapter` no-ops it
- `apps/api/apps/billing/services.py` (`BillingService`): has `cancel_subscription()` — reuse or call directly in deletion cascade
- `apps/web/app/providers.tsx`: PostHog `posthog.init()` called unconditionally — must be refactored to be called only after consent is granted
- `apps/web/app/layout.tsx`: root layout — consent banner component renders here (client component)
- `apps/api/apps/accounts/controllers.py` (`UserController`): existing `/users/me` endpoints — add DELETE `/account/` and GET `/account/export` here or in a new `AccountController`
- `apps/api/apps/billing/models.py` (`Customer`): `stripe_customer_id` on `Customer` (not `User`) — deletion task must access via `user.billing_customer.stripe_customer_id`

### Established Patterns

- Service layer: `UserService`, `BillingService` — `UserDeletionService` follows same thin-service pattern
- Celery task with retry: `autoretry_for=(Exception,), max_retries=3, retry_backoff=True` — apply to deletion task
- HTTP 202 pattern: billing webhook handler returns 202 — same for deletion response
- Adapter method extension: `ObservabilityAdapter` already extended with `capture_exception` + `capture_event` — add `delete_person` following same ABC pattern

### Integration Points

- `apps/api/apps/accounts/controllers.py`: add DELETE and GET export endpoints
- `apps/core/observability.py`: add `delete_person()` to ABC + `PostHogAdapter` + `NoOpAdapter`
- `apps/web/app/providers.tsx`: refactor PostHog init to be consent-gated
- `apps/web/app/layout.tsx`: render `<CookieConsentBanner />` client component
- `apps/web/app/settings/page.tsx`: new page with Danger Zone section

</code_context>

<deferred>
## Deferred Ideas

- Account deletion on mobile — separate phase
- Data export on mobile — separate phase
- Full privacy preference center (granular per-cookie-category toggles) — overengineered for a SaaS baseline
- "Your account has been scheduled for deletion" grace-period flow — not needed for immediate hard delete
- Server-side consent logging for audit trail — out of scope for baseline

</deferred>

---

_Phase: 21-gdpr-baseline_
_Context gathered: 2026-03-12_
