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

---

### Requirement: BillingService uses dependency injection for adapter

`BillingService` SHALL accept an optional `adapter=` constructor argument to enable direct injection in tests. When `adapter` is `None`, the service SHALL call `get_adapter()` lazily on first use rather than at import time.

**Rationale:** Lazy injection avoids circular imports between service modules and allows tests to pass a `StubAdapter` instance directly without monkeypatching global state.

_(Decision: Phase 10)_

#### Scenario: Test injects stub adapter directly

- **WHEN** a test instantiates `BillingService(adapter=StubAdapter())`
- **THEN** the service uses the injected adapter for all operations without calling `get_adapter()`

#### Scenario: Production uses lazy adapter resolution

- **WHEN** `BillingService()` is instantiated with no adapter argument
- **THEN** `get_adapter()` is called on the first service method invocation, not at import time

---

### Requirement: Provider name derived from adapter class name at runtime

The active provider name (e.g., `"stripe"`, `"stub"`) SHALL be derived from the adapter class name at runtime by stripping the `Adapter` suffix and lowercasing. No explicit provider configuration setting is required.

**Rationale:** Eliminates a redundant configuration field. `StripeAdapter` → `"stripe"`, `StubAdapter` → `"stub"`.

_(Decision: Phase 10)_

#### Scenario: Provider name resolves from StripeAdapter

- **WHEN** `BillingService` is using a `StripeAdapter` instance
- **THEN** `service.provider_name` returns `"stripe"`

---

### Requirement: Customer record created automatically via post_save signal

A `Customer` record SHALL be created for every new `User` via a `post_save` signal on the `User` model. The `Customer` record links the local user to their Stripe customer ID.

**Rationale:** Auto-creation ensures a `Customer` record always exists before any billing operation. A missing customer is unreachable in normal flow, eliminating a class of `ServiceError` conditions.

_(Decision: Phase 10)_

#### Scenario: New user gets Customer record

- **WHEN** a new `User` is saved for the first time (`created=True`)
- **THEN** a `Customer` record is created and associated with that user

#### Scenario: Existing user update does not create duplicate

- **WHEN** an existing `User` is saved (updated, not created)
- **THEN** no new `Customer` record is created

---

### Requirement: Webhook endpoint is a plain Django view, not a Ninja endpoint

The `POST /api/billing/webhooks/` endpoint SHALL be implemented as a plain Django view (not a Django Ninja Extra controller). It MUST read the raw request body bytes directly.

**Rationale:** Stripe HMAC signature verification requires access to the raw, unparsed request body bytes. Django Ninja Extra may buffer or parse the body before it reaches the handler, breaking Stripe's signature verification.

_(Decision: Phase 10-01)_

#### Scenario: Webhook signature verified against raw bytes

- **WHEN** Stripe delivers a webhook to `POST /api/billing/webhooks/`
- **THEN** the handler reads `request.body` (raw bytes) before any JSON parsing for HMAC verification

---

### Requirement: Webhook idempotency via get_or_create guard

The webhook handler SHALL use `get_or_create` on `ProcessedWebhookEvent` (keyed on `stripe_event_id`) inside an atomic transaction to guard against duplicate deliveries. The `stripe_event_id` column MUST have a UNIQUE constraint.

**Rationale:** Stripe may deliver the same event more than once. The UNIQUE constraint is the authoritative guard; `get_or_create` wraps it in a race-safe pattern.

_(Decision: Phase 10-01)_

#### Scenario: First delivery processes event

- **WHEN** a Stripe event arrives for the first time
- **THEN** `get_or_create` creates the `ProcessedWebhookEvent` record and processing continues

#### Scenario: Second delivery is silently skipped

- **WHEN** the same Stripe event arrives again
- **THEN** `get_or_create` finds the existing record, processing is skipped, and HTTP 200 is returned

---

### Requirement: get_adapter() defined in utils.py to avoid circular imports

The `get_adapter()` factory function SHALL live in `apps/api/apps/billing/utils.py`, not in `__init__.py` or `tasks.py`.

**Rationale:** `webhooks.py` and `tasks.py` both need `get_adapter()`. Placing it in either would create a circular import. `utils.py` is a leaf module with no internal billing imports.

_(Decision: Phase 10-01)_

#### Scenario: Adapter resolved without circular import

- **WHEN** both `webhooks.py` and `tasks.py` import `get_adapter` from `utils`
- **THEN** neither module creates a circular dependency

---

### Requirement: cancel_at_period_end does not immediately set CANCELED status

Setting `cancel_at_period_end=True` on a subscription SHALL leave the subscription's `status` as `ACTIVE` until the current billing period ends. The `CANCELED` status SHALL only be set when the `customer.subscription.deleted` webhook is delivered at period end.

**Rationale:** Stripe's model: `cancel_at_period_end=True` schedules cancellation but the subscription is still valid. The webhook fires when Stripe actually deletes the subscription.

_(Decision: Phase 10)_

#### Scenario: Cancel at period end keeps subscription active

- **WHEN** `cancel_at_period_end=True` is set on a subscription
- **THEN** `Subscription.status` remains `ACTIVE` and the user retains access until the period ends

#### Scenario: Webhook sets canceled status at period end

- **WHEN** Stripe delivers `customer.subscription.deleted` at the end of the billing period
- **THEN** `Subscription.status` is set to `CANCELED`

---

### Requirement: StubAdapter configured as a module in development settings

`StubAdapter` SHALL be a proper importable module at `apps/api/apps/billing/stub_adapter.py` and SHALL be configured as the active adapter in `config/settings/development.py`. It MUST NOT require per-test monkeypatching.

**Rationale:** Controller-level integration tests pick up the active adapter automatically from Django settings. Configuring `StubAdapter` at the settings level eliminates repetitive test setup and ensures consistent behavior across all tests that hit billing endpoints.

_(Decision: Phase 11)_

#### Scenario: Development environment uses StubAdapter automatically

- **WHEN** tests run with `DJANGO_SETTINGS_MODULE=config.settings.development`
- **THEN** billing controllers use `StubAdapter` without any per-test patching

---

### Requirement: PlanProviderMapping rows seeded via data migration for stub environment

A data migration (`0002`) SHALL seed `PlanProviderMapping` rows that map stub adapter `price_id` values to plan IDs. These seeded values SHALL be the canonical source of truth for `price_id` values used in tests.

**Rationale:** The `StubAdapter` returns fixed `price_id` values (e.g., `"price_stub_pro_monthly"`). Without a mapping row, `plan_id` resolution returns `None`, breaking plan identification in tests and the billing UI.

_(Decision: Phase 11)_

#### Scenario: Stub price_id resolves to plan

- **WHEN** `StubAdapter.retrieve_subscription()` returns `price_id="price_stub_pro_monthly"`
- **THEN** `PlanProviderMapping` lookup resolves it to `plan_id="pro"`

#### Scenario: Test conftest price_ids match migration data

- **WHEN** a test creates a `Subscription` with a `price_id` from `conftest.py`
- **THEN** the `price_id` matches a seeded `PlanProviderMapping` row

---

### Requirement: Subscribe endpoint is separate from modify/change endpoint

The `POST /api/billing/subscribe/` endpoint (creates a Stripe Checkout Session for a new subscriber) SHALL be separate from `POST /api/billing/subscription/change/` (modifies an existing subscription).

**Rationale:** Checkout session creation requires only a `Customer` record (auto-created for all users). Subscription modification requires an active `Subscription` record. Conflating them requires conditional logic and different permission checks in a single handler.

_(Decision: Phase 11)_

#### Scenario: Free-tier user initiates checkout

- **WHEN** a user with no active subscription calls `POST /api/billing/subscribe/`
- **THEN** a Stripe Checkout Session is created and the URL is returned (no existing subscription required)

#### Scenario: Active subscriber changes plan

- **WHEN** a user with an active subscription calls `POST /api/billing/subscription/change/`
- **THEN** the subscription is modified in-place (no new Checkout Session)

---

### Requirement: Invoice PDF generation via Celery task

The system SHALL expose `POST /api/billing/invoices/{invoice_id}/pdf/` which enqueues a Celery task to render a PDF using WeasyPrint and Jinja2. The endpoint SHALL return immediately with a task ID. A separate `GET /api/billing/invoices/{invoice_id}/pdf/` endpoint SHALL poll task status and return `pdf_base64` only when the task is in `SUCCESS` state.

**Rationale:** WeasyPrint rendering is CPU-bound and can take seconds. Blocking the HTTP thread risks timeouts and degrades API responsiveness. Celery offloads the work; the client polls for completion.

_(Decision: Phase 12-01)_

#### Scenario: POST enqueues PDF task

- **WHEN** an authenticated user calls `POST /api/billing/invoices/{invoice_id}/pdf/`
- **THEN** a Celery task is enqueued and the response returns `{ "task_id": "..." }` with HTTP 202

#### Scenario: GET returns base64 PDF when complete

- **WHEN** the Celery task is in `SUCCESS` state and the client calls `GET /api/billing/invoices/{invoice_id}/pdf/`
- **THEN** the response includes `{ "status": "SUCCESS", "pdf_base64": "..." }`

#### Scenario: GET returns pending status while task runs

- **WHEN** the Celery task is still `PENDING` or `STARTED`
- **THEN** the response includes `{ "status": "PENDING" }` with no `pdf_base64` field

---

### Requirement: WeasyPrint imported lazily to prevent Celery fork deadlock

WeasyPrint and its Jinja2 renderer SHALL be imported inside the PDF generation function body, not at module level. This applies to both the synchronous render function and the Celery task wrapper.

**Rationale:** WeasyPrint initializes fontconfig on import. If imported at module level, the fontconfig lock is held by the parent process. Celery's `fork()`-based worker inherits the locked state, causing a deadlock on the first worker invocation. Lazy import defers initialization to after the fork. (WeasyPrint issue #684)

_(Decision: Phase 12-01)_

#### Scenario: PDF renders successfully in Celery worker

- **WHEN** a Celery worker calls the PDF generation task after forking from the parent process
- **THEN** WeasyPrint initializes cleanly without a fontconfig deadlock

---

### Requirement: MAX_PDF_BYTES guard prevents runaway PDF output

The PDF generation function SHALL reject any rendered output exceeding `MAX_PDF_BYTES` (512 KB) and raise an error. The Celery task SHALL mark itself `FAILURE` if this guard triggers.

**Rationale:** `django-celery-results` stores task results in a `TEXT` column. An unbounded WeasyPrint output could exhaust the column or cause memory pressure in the worker.

_(Decision: Phase 12-01)_

#### Scenario: Oversized PDF is rejected

- **WHEN** WeasyPrint renders a PDF larger than 512 KB
- **THEN** the task raises an error and the Celery result is marked `FAILURE`

---

### Requirement: get_pdf_status uses untyped response schema

The `GET /api/billing/invoices/{invoice_id}/pdf/` endpoint SHALL use an untyped (dict) response rather than a typed Pydantic schema for its response body.

**Rationale:** The response shape varies by task state: `PENDING` returns `{ "status": "PENDING" }` while `SUCCESS` adds `{ "pdf_base64": "..." }`. A single Pydantic schema with all fields as optional would be misleading; an untyped dict accurately reflects the dynamic shape.

_(Decision: Phase 12-01)_

#### Scenario: Response shape varies by task state

- **WHEN** the task is `PENDING`
- **THEN** the response contains only `status`; `pdf_base64` is absent (not null)
