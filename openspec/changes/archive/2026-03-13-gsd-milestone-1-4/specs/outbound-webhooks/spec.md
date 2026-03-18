## ADDED Requirements

### Requirement: Webhook Endpoint Registry

Org admins SHALL be able to register, update, and delete external HTTPS endpoints that receive event notifications.

#### Scenario: Admin registers a webhook endpoint

- **WHEN** an org admin calls `POST /api/v1/org/{slug}/webhooks/endpoints/` with a URL and event type list
- **THEN** a `WebhookEndpoint` record SHALL be created
- **AND** a webhook secret SHALL be auto-generated server-side (32-byte `secrets.token_hex(32)`)
- **AND** the raw secret SHALL be returned in the response body exactly once
- **AND** the secret SHALL be stored as a SHA-256 hash — never as plaintext

#### Scenario: HTTP endpoint URLs rejected

- **WHEN** a user attempts to register a webhook endpoint with an `http://` URL
- **THEN** the system SHALL return `400 Bad Request`
- **AND** only `https://` URLs SHALL be accepted

#### Scenario: Secret shown once only

- **WHEN** the endpoint is retrieved via `GET /api/v1/org/{slug}/webhooks/endpoints/{id}`
- **THEN** the `secret` field SHALL NOT be present in the response
- **AND** the secret SHALL only be retrievable by rotating it

#### Scenario: Secret rotation issues new secret

- **WHEN** an org admin calls `POST /api/v1/org/{slug}/webhooks/endpoints/{id}/rotate-secret`
- **THEN** a new secret SHALL be generated and stored (old secret invalidated immediately)
- **AND** the new raw secret SHALL be returned once in the response body

### Requirement: HMAC-Signed Event Delivery via Celery

The system SHALL deliver webhook events asynchronously via Celery with HMAC-SHA256 signatures, exponential backoff, and a versioned payload envelope.

#### Scenario: Event delivery is triggered

- **WHEN** `fire_webhook_event(org, event_type, payload)` is called inside a database transaction
- **THEN** one Celery delivery task SHALL be enqueued per matching active endpoint via `transaction.on_commit()`
- **AND** no delivery SHALL be sent if the triggering transaction rolls back

#### Scenario: Delivered payload is signed and versioned

- **WHEN** a delivery task sends an HTTP POST to a registered endpoint
- **THEN** the request SHALL include `X-Webhook-Signature: sha256=<hmac_hex>`
- **AND** the request SHALL include `X-Webhook-Id: <delivery_uuid>` and `X-Webhook-Timestamp: <unix_ts>`
- **AND** the payload JSON SHALL include a top-level `webhook_version: "v1"` field

#### Scenario: Delivery retried with exponential backoff on failure

- **WHEN** the target endpoint returns a non-2xx response or times out
- **THEN** the delivery SHALL be retried up to 7 times with exponential backoff
- **AND** a `WebhookDeliveryAttempt` record SHALL be written for each attempt with status and response code

#### Scenario: Delivery reaches terminal failure after max retries

- **WHEN** all 7 retry attempts are exhausted without a 2xx response
- **THEN** the `WebhookDelivery` status SHALL be set to `failed`
- **AND** the endpoint's `consecutive_failures` counter SHALL be incremented

### Requirement: Delivery History and Manual Retry

Users SHALL be able to view paginated delivery history and manually retry failed deliveries.

#### Scenario: User views delivery history

- **WHEN** an org member calls `GET /api/v1/org/{slug}/webhooks/endpoints/{id}/deliveries`
- **THEN** the response SHALL include a paginated list of `WebhookDelivery` records with status, timestamp, and last attempt response code

#### Scenario: User manually retries a failed delivery

- **WHEN** an org admin calls `POST /api/v1/org/{slug}/webhooks/deliveries/{id}/retry`
- **THEN** a new Celery delivery task SHALL be enqueued for the same payload and endpoint
- **AND** the delivery status SHALL be reset to `pending`

### Requirement: Auto-Disable Circuit Breaker

The system SHALL automatically disable webhook endpoints after 5 consecutive fully-exhausted delivery failures and notify the org admin by email.

#### Scenario: Endpoint auto-disabled after threshold

- **WHEN** an endpoint accumulates 5 consecutive `failed` deliveries (each with all 7 retries exhausted)
- **THEN** `WebhookEndpoint.is_active` SHALL be set to `False`
- **AND** an email SHALL be sent to the org admin identifying the endpoint URL and last failure reason

#### Scenario: Consecutive failure counter resets on success

- **WHEN** any delivery to an endpoint returns HTTP 2xx
- **THEN** `WebhookEndpoint.consecutive_failures` SHALL be reset to 0

#### Scenario: Admin re-enables a disabled endpoint

- **WHEN** an org admin calls `PATCH /api/v1/org/{slug}/webhooks/endpoints/{id}` with `is_active: true`
- **THEN** the endpoint SHALL be re-enabled
- **AND** `consecutive_failures` SHALL be reset to 0

### Requirement: Settings-Based Event Catalog

Available webhook event types SHALL be defined in a `WEBHOOK_EVENTS` settings dict, validated at startup.

#### Scenario: Unknown event type rejected at dispatch

- **WHEN** `fire_webhook_event(org, "unknown.event", payload)` is called
- **THEN** the function SHALL raise `ValueError`
- **AND** no delivery task SHALL be enqueued

#### Scenario: Event catalog validated at startup

- **WHEN** the Django application starts
- **THEN** `manage.py check` SHALL validate that all event types stored in the database exist in `WEBHOOK_EVENTS`
- **AND** unknown DB event types SHALL surface as warnings (not errors)

## Implementation Decisions

### Why settings-based event catalog (not database-driven or decorator registry)

`WEBHOOK_EVENTS` dict in Django settings mirrors the `BILLING_PLANS` pattern already established in this codebase. It is validated at startup via `manage.py check`, versioned in source control, and requires no admin UI to manage. Database-driven catalogs add migration overhead for what is essentially configuration.

**Alternative rejected:** A decorator-based registry (`@webhook_event("user.created")`) — more ergonomic for large codebases but adds import-time side effects and makes the catalog harder to enumerate for validation.

### Why `transaction.on_commit()` for delivery enqueue

Enqueuing delivery tasks inside `on_commit()` prevents a race condition where the Celery task fires before the triggering write is committed — the task would read a database state that doesn't include the event's origin. If the transaction rolls back (e.g., validation failure), no spurious delivery is sent.

### Why the secret is auto-generated server-side and stored as SHA-256 hash only

User-provided secrets create weak security baselines (short, guessable, reused). Auto-generated 32-byte secrets give 256 bits of entropy. Storing only the SHA-256 hash means a database breach does not expose secrets — consistent with the API key hashing decision in `api-key-authentication`.

**"Shown once" contract:** The raw secret is returned in the POST response body only. Product UIs must present a copy-to-clipboard affordance and a warning that the secret cannot be retrieved again.

### Why HMAC uses the `sha256=<hex>` header format

This matches Stripe's and GitHub's webhook signing convention, which most developer tooling and integration platforms already know how to verify. Deviating from this convention increases integration friction for product customers.

### Why 5-consecutive-failures threshold for circuit breaker

5 fully-exhausted deliveries (each with 7 retries = 35 total HTTP attempts) is a strong signal of a persistently broken endpoint. A lower threshold would trigger false positives from transient infrastructure issues; higher would delay admin notification unnecessarily.

### Why delivery log retention is 30 days

Delivery logs are append-only and grow without bound. 30 days covers most debugging windows (charge disputes, integration issues) without requiring unlimited storage. Products with compliance requirements can extend this via a `WEBHOOK_DELIVERY_RETENTION_DAYS` setting override.
