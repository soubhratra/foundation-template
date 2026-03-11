## ADDED Requirements

### Requirement: Stripe customer is created on first checkout

When a user initiates their first subscription checkout, the system SHALL create a Stripe Customer object linked to their account and persist the `stripe_customer_id` on the User model. Subsequent checkouts reuse the same Stripe Customer.

#### Scenario: First checkout creates Stripe customer

- **WHEN** a user with no `stripe_customer_id` calls `POST /api/billing/checkout/`
- **THEN** a Stripe Customer is created with the user's email, the `stripe_customer_id` is saved on the User model, and a Stripe Checkout Session URL is returned

#### Scenario: Repeat checkout reuses existing customer

- **WHEN** a user with an existing `stripe_customer_id` calls `POST /api/billing/checkout/`
- **THEN** no new Stripe Customer is created, and the existing `stripe_customer_id` is used for the Checkout Session

---

### Requirement: Stripe Checkout Session creation

The system SHALL expose `POST /api/billing/checkout/` which creates a Stripe Checkout Session in `subscription` mode and returns the hosted URL. The endpoint MUST be authenticated. The `success_url` and `cancel_url` SHALL be configurable via `STRIPE_SUCCESS_URL` and `STRIPE_CANCEL_URL` environment variables.

#### Scenario: Authenticated user creates checkout session

- **WHEN** an authenticated user sends `POST /api/billing/checkout/` with a valid `price_id`
- **THEN** the response contains `{ "checkout_url": "<stripe_hosted_url>" }` with HTTP 200

#### Scenario: Unauthenticated request is rejected

- **WHEN** an unauthenticated request is sent to `POST /api/billing/checkout/`
- **THEN** the response is HTTP 401

#### Scenario: Invalid price_id is rejected

- **WHEN** an authenticated user sends `POST /api/billing/checkout/` with a `price_id` not present in `STRIPE_PRICE_IDS`
- **THEN** the response is HTTP 400 with an error message

---

### Requirement: Stripe Customer Portal session creation

The system SHALL expose `POST /api/billing/portal/` which creates a Stripe Customer Portal session and returns the portal URL. The endpoint MUST be authenticated. The user MUST have an existing `stripe_customer_id` (i.e., must have previously initiated checkout).

#### Scenario: Active subscriber accesses portal

- **WHEN** an authenticated user with a `stripe_customer_id` calls `POST /api/billing/portal/`
- **THEN** the response contains `{ "portal_url": "<stripe_portal_url>" }` with HTTP 200

#### Scenario: User without Stripe customer is rejected

- **WHEN** an authenticated user with no `stripe_customer_id` calls `POST /api/billing/portal/`
- **THEN** the response is HTTP 400 with `{ "detail": "No billing account found." }`

---

### Requirement: Webhook endpoint for Stripe events

The system SHALL expose `POST /api/billing/webhooks/` as an unauthenticated endpoint for Stripe webhook delivery. The endpoint MUST verify the Stripe webhook signature using `STRIPE_WEBHOOK_SECRET` before processing. Invalid signatures MUST return HTTP 400.

#### Scenario: Valid webhook is accepted and processed

- **WHEN** Stripe delivers a `customer.subscription.updated` event with a valid signature
- **THEN** the endpoint returns HTTP 200 and the subscription record is updated

#### Scenario: Invalid webhook signature is rejected

- **WHEN** a request arrives at `POST /api/billing/webhooks/` with a missing or invalid `Stripe-Signature` header
- **THEN** the endpoint returns HTTP 400 and no state is modified

#### Scenario: Duplicate event is silently skipped

- **WHEN** Stripe delivers an event whose `stripe_event_id` already exists in `BillingEvent`
- **THEN** the endpoint returns HTTP 200 and no state is modified (idempotent)

---

### Requirement: Subscription state is kept in sync via webhooks

The system SHALL handle the following Stripe events to maintain local subscription state:

| Event                           | Action                                                                                                |
| ------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `checkout.session.completed`    | Create or update `Subscription`; set `User.subscription_status = "active"` (or `"trialing"` if trial) |
| `customer.subscription.updated` | Update `Subscription.status`, `price_id`, `current_period_end`; sync `User.subscription_status`       |
| `customer.subscription.deleted` | Set `Subscription.status = "canceled"`; set `User.subscription_status = "canceled"`                   |
| `invoice.payment_failed`        | Set `User.subscription_status = "past_due"`                                                           |

#### Scenario: Checkout completion activates subscription

- **WHEN** Stripe delivers `checkout.session.completed` for a new subscription
- **THEN** a `Subscription` record is created and `User.subscription_status` is set to `"active"` or `"trialing"`

#### Scenario: Subscription cancellation is reflected immediately

- **WHEN** Stripe delivers `customer.subscription.deleted`
- **THEN** `User.subscription_status` is set to `"canceled"` within one webhook delivery cycle

#### Scenario: Payment failure is reflected in status

- **WHEN** Stripe delivers `invoice.payment_failed`
- **THEN** `User.subscription_status` is set to `"past_due"`

---

### Requirement: Subscription status endpoint

The system SHALL expose `GET /api/billing/subscription/` which returns the authenticated user's current subscription state from the local database (no live Stripe API call).

#### Scenario: Active subscriber retrieves status

- **WHEN** an authenticated user with an active subscription calls `GET /api/billing/subscription/`
- **THEN** the response includes `{ "status": "active", "price_id": "...", "current_period_end": "<ISO datetime>" }`

#### Scenario: User with no subscription retrieves status

- **WHEN** an authenticated user with no subscription record calls `GET /api/billing/subscription/`
- **THEN** the response is `{ "status": "none" }`

---

### Requirement: BillingEvent idempotency log

The system SHALL maintain a `BillingEvent` model that records every processed Stripe webhook event. Each record stores `stripe_event_id` (unique), `event_type`, `processed_at`, and `raw_payload` (JSON). Processing an event MUST be wrapped in a transaction that also creates the `BillingEvent` record, ensuring atomicity.

#### Scenario: Event is logged on processing

- **WHEN** a valid Stripe webhook is processed
- **THEN** a `BillingEvent` record is created with the event's ID and type

#### Scenario: Duplicate event is rejected before processing

- **WHEN** an event with an existing `stripe_event_id` arrives
- **THEN** no service logic is executed and the existing `BillingEvent` record is unchanged

---

### Requirement: Stripe key validation at startup

In non-development environments, if `STRIPE_SECRET_KEY` does not start with `sk_` or `STRIPE_WEBHOOK_SECRET` is not set, the application SHALL raise `django.core.exceptions.ImproperlyConfigured` on startup.

In development, if `STRIPE_SECRET_KEY` starts with `sk_live_`, the application SHALL raise `ImproperlyConfigured` to prevent live charges.

#### Scenario: Live key in development is rejected

- **WHEN** `DJANGO_SETTINGS_MODULE` points to `config.settings.development` and `STRIPE_SECRET_KEY` starts with `sk_live_`
- **THEN** the application raises `ImproperlyConfigured` at startup with a descriptive message

#### Scenario: Missing webhook secret in production is rejected

- **WHEN** `DJANGO_SETTINGS_MODULE` points to `config.settings.production` and `STRIPE_WEBHOOK_SECRET` is not set
- **THEN** the application raises `ImproperlyConfigured` at startup
