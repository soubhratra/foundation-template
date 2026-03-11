## 1. Dependencies and Configuration

- [ ] 1.1 Add `stripe>=14.4,<15` to `pyproject.toml` under `[dependency-groups] billing` and run `uv sync --group billing`
- [ ] 1.2 Add Stripe env vars to `.env.example`: `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_SUCCESS_URL`, `STRIPE_CANCEL_URL`, `STRIPE_PRICE_IDS` (JSON map of plan slug → Stripe price ID)
- [ ] 1.3 Add Stripe env vars to `config/settings/base.py` using `django-environ`, with dev-environment live-key guard (raise `ImproperlyConfigured` if `sk_live_` in development) and production webhook secret guard

## 2. User Model — Billing Fields

- [ ] 2.1 Add `stripe_customer_id` (`CharField`, nullable, unique, indexed) and `subscription_status` (`CharField`, default `"none"`) to `apps/accounts/models.py`
- [ ] 2.2 Run `python manage.py makemigrations accounts` to generate `0002_user_billing_fields.py`
- [ ] 2.3 Update `accounts` user response schema (`schemas.py`) to include `subscription_status` in the serialized output
- [ ] 2.4 Verify `GET /api/auth/me/` (or equivalent) returns `subscription_status` in the response

## 3. Billing Django App — Models

- [ ] 3.1 Create `apps/api/apps/billing/` directory with `__init__.py`, `apps.py`, `models.py`, `schemas.py`, `controllers.py`, `services.py`, `admin.py`, and `migrations/` directory
- [ ] 3.2 Implement `Subscription` model: fields `user` (OneToOne FK), `stripe_subscription_id` (unique), `stripe_customer_id`, `status`, `price_id`, `current_period_end`, plus `TimeStampedModel` base
- [ ] 3.3 Implement `BillingEvent` model: fields `stripe_event_id` (unique), `event_type`, `processed_at`, `raw_payload` (JSONField)
- [ ] 3.4 Run `python manage.py makemigrations billing` to generate initial billing migrations
- [ ] 3.5 Register `apps.billing` in `INSTALLED_APPS` in `config/settings/base.py`
- [ ] 3.6 Register `Subscription` and `BillingEvent` in `apps/billing/admin.py`

## 4. Billing Service Layer

- [ ] 4.1 Implement `BillingService.get_or_create_stripe_customer(user)` — creates Stripe Customer if `stripe_customer_id` is null, saves and returns the ID
- [ ] 4.2 Implement `BillingService.create_checkout_session(user, price_id)` — validates `price_id` is in allowed set, calls `get_or_create_stripe_customer`, creates Stripe Checkout Session, returns URL
- [ ] 4.3 Implement `BillingService.create_portal_session(user)` — validates user has `stripe_customer_id`, creates Stripe Customer Portal session, returns URL
- [ ] 4.4 Implement `BillingService.get_subscription_status(user)` — queries local `Subscription` model, returns status dict (no Stripe API call)

## 5. Webhook Handler

- [ ] 5.1 Implement `WebhookService.process_event(payload_bytes, stripe_signature)` — verifies signature with `stripe.Webhook.construct_event`, checks `BillingEvent` for duplicate `stripe_event_id`, dispatches to event-specific handlers inside a DB transaction that also creates the `BillingEvent` record
- [ ] 5.2 Implement handler for `checkout.session.completed` — upsert `Subscription`, set `User.subscription_status` to `"active"` or `"trialing"`
- [ ] 5.3 Implement handler for `customer.subscription.updated` — update `Subscription.status`, `price_id`, `current_period_end`; sync `User.subscription_status`
- [ ] 5.4 Implement handler for `customer.subscription.deleted` — set `Subscription.status = "canceled"`, `User.subscription_status = "canceled"`
- [ ] 5.5 Implement handler for `invoice.payment_failed` — set `User.subscription_status = "past_due"`

## 6. Billing API Endpoints

- [ ] 6.1 Implement `BillingController` with `@api_controller("/billing", tags=["Billing"])` in `apps/billing/controllers.py`
- [ ] 6.2 Add `POST /checkout/` endpoint — authenticated, accepts `{ price_id }`, delegates to `BillingService.create_checkout_session`, returns `{ checkout_url }`
- [ ] 6.3 Add `POST /portal/` endpoint — authenticated, delegates to `BillingService.create_portal_session`, returns `{ portal_url }`
- [ ] 6.4 Add `GET /subscription/` endpoint — authenticated, delegates to `BillingService.get_subscription_status`, returns subscription state
- [ ] 6.5 Add `POST /webhooks/` endpoint — unauthenticated, reads raw request body and `Stripe-Signature` header, delegates to `WebhookService.process_event`, returns HTTP 200 on success or 400 on signature failure
- [ ] 6.6 Verify `api.auto_discover_controllers()` in `config/urls.py` picks up the new controller (no manual registration needed)

## 7. Backend Tests

- [ ] 7.1 Write `tests/billing/test_services.py` — unit tests for `BillingService` methods (mock Stripe SDK calls with `pytest-mock`)
- [ ] 7.2 Write `tests/billing/test_webhook.py` — unit tests for `WebhookService.process_event` covering each event type, duplicate event skipping, and invalid signature
- [ ] 7.3 Write `tests/billing/test_controllers.py` — integration tests for all four billing endpoints (auth required on checkout/portal/subscription; unauthenticated webhook)

## 8. Frontend — Pricing Page

- [ ] 8.1 Create `apps/web/app/(marketing)/pricing/page.tsx` as a Server Component with a static plan config (plan name, price, interval, feature bullets)
- [ ] 8.2 Create `PricingCard` client component that handles the CTA click: authenticated users call `POST /api/billing/checkout/` and redirect; unauthenticated users redirect to `/login?next=/pricing`
- [ ] 8.3 Add `/pricing` link to the marketing nav

## 9. Frontend — Billing Settings Page

- [ ] 9.1 Create `apps/web/app/(app)/settings/billing/page.tsx` as a Server Component that fetches `GET /api/billing/subscription/` and passes data to client components
- [ ] 9.2 Create `ManageBillingButton` client component that calls `POST /api/billing/portal/` and redirects to the portal URL
- [ ] 9.3 Add "Billing" entry to the settings navigation

## 10. Frontend — Auth Context and Post-Checkout

- [ ] 10.1 Update the user type in `packages/shared-types/` to include `subscription_status: string`
- [ ] 10.2 Expose `subscriptionStatus` from the auth context / React Query user cache so components can gate features without extra API calls
- [ ] 10.3 Create `apps/web/app/(marketing)/checkout/success/page.tsx` — invalidates the auth cache on mount (React Query `invalidateQueries`) and shows a confirmation message
- [ ] 10.4 Set `STRIPE_SUCCESS_URL` default to `/checkout/success` and `STRIPE_CANCEL_URL` default to `/pricing` in `.env.example`

## 11. Shared Types Regeneration

- [ ] 11.1 Run `python manage.py export_openapi_schema --output openapi.json` from `apps/api/` to capture new billing endpoints
- [ ] 11.2 Run the type generation pipeline in `packages/shared-types/` to regenerate TypeScript types from the updated schema
- [ ] 11.3 Verify `BillingTypes` (checkout request/response, portal response, subscription status response) are present in the generated output
