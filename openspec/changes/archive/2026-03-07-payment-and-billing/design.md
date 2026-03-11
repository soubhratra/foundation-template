## Context

The Foundation Template ships without any payment infrastructure. Every SaaS product built on it must add billing before it can charge users. The billing layer integrates with Stripe — the industry standard for subscription payments — and touches three layers: the Django backend (subscription models, checkout sessions, webhook handling), the auth layer (user model gains billing state), and the Next.js frontend (pricing page, billing portal link).

This design targets the reusable template layer. It should be generic enough to drop into any product, but concrete enough to function out of the box with minimal product-specific customization.

Current state: `apps/api/apps/accounts/models.py` has the `User` model with no billing fields. No billing app exists. No Stripe dependency is installed.

## Goals / Non-Goals

**Goals:**

- Stripe Checkout integration for subscription creation (hosted page, not embedded Elements)
- Stripe Customer Portal for self-service subscription management (cancel, upgrade, downgrade)
- Webhook handler that keeps local subscription state in sync with Stripe events
- `subscription_status` field on the User model surfaced in auth responses so the frontend can gate features without extra API calls
- Pricing page and billing settings page in `apps/web/`
- Idempotent webhook processing (safe to replay events)
- Local dev support via Stripe CLI webhook forwarding

**Non-Goals:**

- One-time payments / metered usage billing (can be added per-product)
- In-app Stripe Elements (embedded card input) — hosted Checkout is simpler and more secure for the template
- Multi-seat / team billing — single-user subscriptions only
- Invoice PDF generation or custom receipts — Stripe handles this
- Dunning / retry logic — Stripe Smart Retries handles this automatically

## Decisions

### Decision 1: Stripe Checkout (hosted) over embedded Elements

**Why:** Hosted Checkout requires zero PCI compliance burden. Stripe handles card input, 3DS, and localization. For a template, eliminating surface area is more important than customization. Products that need embedded card forms can add Elements per-product.

**Alternative rejected:** Stripe Elements (embedded) — adds significant frontend complexity (field rendering, error handling, 3DS flow) that varies per product. Not appropriate for a reusable base.

### Decision 2: A dedicated `billing` Django app, not adding to `accounts`

**Why:** Billing has its own models, services, and webhook logic. Embedding it in `accounts` would violate single-responsibility and make the module harder to remove for products that don't need Stripe (e.g., enterprise licenses). A standalone `apps/billing/` app can be removed cleanly.

**Alternative rejected:** Adding billing fields to `accounts` — tightly couples auth and billing, making removal or replacement harder.

### Decision 3: `subscription_status` denormalized onto the User model

**Why:** The frontend needs to gate features behind subscription state on every page render. A foreign key join on every auth check adds latency and complexity. A denormalized `CharField` on `User` (e.g., `"active"`, `"trialing"`, `"past_due"`, `"canceled"`, `"none"`) lets the auth response include billing state at no extra cost.

**Sync mechanism:** The Stripe webhook handler updates `User.subscription_status` whenever a `customer.subscription.*` event arrives. The local field is eventually consistent with Stripe (typically < 1 second lag).

**Alternative rejected:** Querying the `Subscription` model on every auth check — adds a DB join to every request and couples auth latency to billing DB state.

### Decision 4: Store minimal billing state locally; Stripe is the source of truth

**Why:** Attempting to mirror all Stripe state locally creates a complex sync problem. Instead, store only what the app needs for feature gating and display: `stripe_customer_id` on User, and a `Subscription` model with `stripe_subscription_id`, `status`, `price_id`, `current_period_end`. Everything else is fetched from Stripe on demand (e.g., invoice history, upcoming invoice).

**Alternative rejected:** Full Stripe data mirror — over-engineered for a template; Stripe's API is fast enough for on-demand reads.

### Decision 5: Webhook idempotency via `BillingEvent` log

**Why:** Stripe can deliver webhooks more than once. Processing a `checkout.session.completed` twice would create duplicate subscriptions. A `BillingEvent` model records every processed `stripe_event_id`. The webhook handler checks for the event ID before processing and skips duplicates.

**Alternative rejected:** Database-level upsert on Subscription only — doesn't protect against multi-step side effects in more complex event handlers.

### Decision 6: Stripe CLI forwarding for local dev (no ngrok required)

**Why:** `stripe listen --forward-to localhost:8000/api/billing/webhooks/` routes live test events to the local server without exposing a public URL. This is the Stripe-recommended local dev workflow and requires no third-party tunnel.

**Configuration:** Document the `stripe listen` command in `apps/api/README.md` and `.env.example`.

### Decision 7: Frontend uses Server Components for pricing page; Client Component for billing portal redirect

**Why:** The pricing page is static-ish (plan names, prices from env or a config file). A Server Component renders it without client JS. The "Manage Billing" button must call the backend to create a portal session and redirect, requiring a Client Component (or a form action in a Server Component — either works).

## Risks / Trade-offs

- **Webhook signature verification depends on `STRIPE_WEBHOOK_SECRET`** → If this env var is missing in production, the webhook endpoint will reject all events. Mitigation: validate on startup and fail loudly if missing in non-dev environments.
- **`subscription_status` is eventually consistent** → There's a brief window after a Stripe event where local state lags. Mitigation: acceptable for feature gating (< 1s typical). For hard enforcement (e.g., access control), always verify against local DB, never trust client-sent state.
- **Stripe test/live key confusion** → Using live keys in development will charge real cards. Mitigation: validate that `STRIPE_SECRET_KEY` starts with `sk_test_` in development settings; raise `ImproperlyConfigured` otherwise.
- **User model migration is required** → Adding `stripe_customer_id` and `subscription_status` to `accounts.User` requires a migration. This is additive and non-breaking, but must be coordinated if a product has already run migrations.

## Migration Plan

1. Install `stripe>=14.4,<15` via `uv add --group billing stripe` in `apps/api/`
2. Add `stripe_customer_id` and `subscription_status` fields to `accounts.User` model
3. Run `python manage.py makemigrations accounts` — produces `accounts/migrations/0002_user_billing_fields.py`
4. Create `apps/billing/` app with models, schemas, controllers, services
5. Run `python manage.py makemigrations billing` — produces initial billing migrations
6. Register `apps.billing` in `INSTALLED_APPS` and register billing router in `config/urls.py`
7. Add Stripe env vars to `.env.example` and settings
8. Add frontend pricing and billing pages to `apps/web/`
9. Regenerate `packages/shared-types/` from updated OpenAPI schema

**Rollback:** The billing app is additive. To remove: delete `apps/billing/`, remove `apps.billing` from `INSTALLED_APPS`, remove billing fields from `accounts.User`, and run `makemigrations`. No data loss to non-billing tables.

## Open Questions

- **Plan configuration source:** Should `Plan` records be seeded via a fixture/migration (static) or read from Stripe Products API dynamically? _Recommendation: static fixture for the template (one default plan), overridable per product._
- **Trial period support:** The template should support a configurable trial period (`STRIPE_TRIAL_DAYS` env var, default `0`). Decision deferred to spec phase.
- **Mobile billing:** The Expo app is not in scope for this change. Stripe subscriptions managed via the web portal are accessible on mobile through the same `subscription_status` field on the auth token. In-app purchase (Apple/Google) is a separate future capability.
