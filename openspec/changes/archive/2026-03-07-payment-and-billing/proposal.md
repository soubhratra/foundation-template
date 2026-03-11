## Why

SaaS products built on this template need subscription billing from day one. Without a reusable payment and billing capability, every product scaffolded from this template has to wire Stripe, subscription logic, webhook handling, and billing portal from scratch — creating repeated risk and delay. Adding this to the template foundation means new products inherit a working, tested billing layer immediately.

## What Changes

- Add a `billing` Django app to `apps/api/` with Stripe subscription management
- Add `stripe` Python package to the backend dependency group
- Introduce `Plan`, `Subscription`, and `BillingEvent` models
- Expose billing API endpoints via Django Ninja Extra (checkout, portal, subscription status)
- Add Stripe webhook endpoint with signature verification and idempotent event handling
- Add frontend billing UI to `apps/web/`: pricing page, subscription management, and upgrade/downgrade flows
- Integrate billing state into auth context (e.g., `subscription_status` on the user session)
- Provide Stripe CLI webhook forwarding config for local dev
- Add billing-specific environment variables to `.env.example`

## Capabilities

### New Capabilities

- `stripe-billing`: Stripe subscription lifecycle — plans, checkout sessions, customer portal, and subscription status. Covers the backend billing app, models, API endpoints, and webhook handler.
- `billing-ui`: Frontend pricing page and subscription management UI in `apps/web/`. Covers plan display, Stripe Checkout redirect, and the customer portal link.

### Modified Capabilities

- `auth`: User model gains `stripe_customer_id` and `subscription_status` fields. Session/token payload includes subscription tier so the frontend can gate features without a round-trip.

## Impact

- **apps/api/billing/**: New Django app (models, schemas, api, services, selectors, migrations)
- **apps/api/users/models.py**: Add `stripe_customer_id`, `subscription_status` fields to User model
- **apps/api/config/urls.py**: Register billing router
- **apps/web/app/(marketing)/pricing/**: New pricing page component
- **apps/web/app/(app)/settings/billing/**: Subscription management page
- **packages/shared-types/**: New `BillingTypes` from generated schemas
- **pyproject.toml**: `billing` optional dependency group with `stripe>=14.4,<15`
- **.env.example**: `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRICE_ID_*`
- **docker-compose.yml**: No changes needed (Stripe is external)
