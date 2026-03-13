# Phase 27: Outbound Webhooks - Context

**Gathered:** 2026-03-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Org admins can register external HTTP endpoints to receive HMAC-signed event notifications. The infrastructure handles delivery via Celery, delivery history, manual retry, and auto-disabling endpoints that fail persistently.

Scope: WebhookEndpoint registry, WEBHOOK_EVENTS settings-based catalog, `fire_webhook_event()` dispatch utility, HMAC-SHA256 signing, delivery + attempt log models, paginated delivery history API, manual retry endpoint, auto-disable circuit breaker, org admin email notification on disable, 30-day delivery log retention.

Not in scope: Webhook event catalog UI (HOOK-F01, deferred), inbound webhooks from third-party services, webhook secret auto-rotation without breaking integrations.

</domain>

<decisions>
## Implementation Decisions

### Event catalog design

- Event catalog is a **settings-based dict**: `WEBHOOK_EVENTS` in Django settings, mirroring the `BILLING_PLANS` pattern
  ```python
  WEBHOOK_EVENTS = {
      "user.created": {
          "description": "Fired when a new user signs up",
          "example_payload": {"user_id": 1, "email": "user@example.com"},
      },
      "subscription.updated": {
          "description": "Fired when a user's subscription status changes",
          "example_payload": {"user_id": 1, "plan": "pro", "status": "active"},
      },
  }
  ```
- Template ships 2–3 example events (`user.created`, `subscription.updated`) showing the pattern
- Validated at startup via `manage.py check` — unknown event types in DB deliveries surface as warnings, not errors
- Product developers extend the dict; no decorator registry, no DB-driven catalog

- **Dispatch API:** `fire_webhook_event(org, event_type, payload: dict)` in `apps/webhooks/utils.py`
  - Validates `event_type` against `WEBHOOK_EVENTS` (raises `ValueError` on unknown type)
  - Resolves active endpoints belonging to `org` that are subscribed to `event_type`
  - Enqueues one Celery delivery task per matching endpoint via `transaction.on_commit()` — no delivery if the triggering transaction rolls back
  - Product code calls this after a successful write (same pattern as `send_email()` in notifications)

- **Org admin subscription:** `event_types` is a list of event type strings on the endpoint record; multi-select at registration; empty list = receive nothing; updated via PATCH

### Endpoint registration

- **Registration fields:**
  - `url` (required) — HTTPS only; HTTP rejected at validation time
  - `event_types` (required) — non-empty list validated against `WEBHOOK_EVENTS`
  - `name` (optional) — human label (e.g. "Production Slack"), max 255 chars

- **Secret handling:**
  - Secret is auto-generated server-side (32-byte `secrets.token_hex(32)`) — never user-provided
  - **Shown once:** returned as `secret` in the POST `/endpoints` response body only; never returned by the API again
  - Stored as SHA-256 hash on `WebhookEndpoint.secret_hash` (no plaintext in DB)
  - Rotation: dedicated `POST /endpoints/{id}/rotate-secret` endpoint issues a new secret (old one invalidated immediately), returns new secret once

- **HMAC signature on delivery:**
  - Header: `X-Webhook-Signature: sha256=<hmac_hex>` — same convention as Stripe and GitHub
  - Additional headers per delivery: `X-Webhook-Id: <delivery_uuid>`, `X-Webhook-Timestamp: <unix_ts>`
  - Payload envelope always includes `webhook_version: "v1"` top-level field (HOOK-01 requirement)

### Circuit breaker

- **Threshold:** Auto-disable after **5 consecutive fully-exhausted delivery failures** (each delivery already attempted 7 times per HOOK-01)
- **Counter:** `consecutive_failures` integer field on `WebhookEndpoint`; incremented when a delivery reaches terminal `failed` status
- **Reset:** Any successful delivery (`HTTP 2xx`) resets `consecutive_failures` to 0 on the endpoint
- **Re-enable:** Admin can `PATCH /endpoints/{id}` with `is_active: true`; re-enabling also resets `consecutive_failures` to 0; no cooldown or lock-out
- **Notification:** On auto-disable, send email to org admin via existing `send_email()` utility with template identifying the endpoint URL and last failure reason (extends email templates from Phase 19)

### Delivery log

- **DeliveryStatus enum:** `pending → retrying → success | failed`
  - `pending`: enqueued, not yet attempted
  - `retrying`: at least one attempt made, more scheduled
  - `success`: any attempt returned HTTP 2xx
  - `failed`: max retries exhausted with no 2xx

- **WebhookDelivery (parent record):**
  - `id` (UUID), `endpoint` FK, `event_type`, `status`, `request_body` (full payload snapshot), `request_headers` (dict snapshot), `created_at`

- **WebhookDeliveryAttempt (per attempt):**
  - `delivery` FK, `attempt_number`, `http_status_code` (null if network error), `response_body` (truncated at **10KB**), `response_headers` (dict), `duration_ms`, `attempted_at`, `error_message` (for network/timeout errors)

- **Retention:** 30 days; periodic Celery beat task deletes `WebhookDelivery` records older than `WEBHOOK_DELIVERY_RETENTION_DAYS` (default `30`); cascade deletes attempts via FK

### Claude's Discretion

- Exact DB index strategy on `WebhookDelivery` (endpoint + created_at compound index likely needed for paginated delivery history)
- Pagination default page size for delivery history (follow existing pagination pattern in codebase)
- Exact Celery task countdown/backoff formula (follow billing task pattern: `2^retries` seconds)
- HTTP request timeout for outbound delivery calls (suggest 30s)
- Whether `WebhookEndpoint.url` validation uses urllib or a dedicated validator

</decisions>

<specifics>
## Specific Ideas

- `fire_webhook_event()` mirrors `send_email()` in philosophy: product code calls it, it validates, resolves recipients, and enqueues via `transaction.on_commit()`. Developers don't touch Celery directly.
- HMAC signature convention follows Stripe/GitHub — integrators already know the pattern; verification code is copy-pasteable from those docs.
- `WEBHOOK_EVENTS` mirrors `BILLING_PLANS` — same settings-based pattern, same `manage.py check` validation approach. Keeps the template consistent.
- Secret shown once on creation, same philosophy as API keys (Phase 28) — store hash, show raw value only at creation time.

</specifics>

<code_context>

## Existing Code Insights

### Reusable Assets

- `apps/billing/tasks.py` (`process_stripe_event`): `autoretry_for=(Exception,)`, `retry_backoff=True`, `max_retries=7` (set per HOOK-01), dead-letter CRITICAL log — copy this retry pattern verbatim for delivery task
- `apps/notifications/utils.py` (`send_email()`): `transaction.on_commit()` dispatch pattern — `fire_webhook_event()` follows exact same pattern
- `apps/core/tasks.py`: existing Celery beat setup — add retention cleanup task here or in webhooks app
- `apps/orgs/permissions.py` (`IsOrgAdmin`): permission class already resolves `request.org` — webhook endpoints are at `/api/v1/org/{org_slug}/webhooks/...`, use `IsOrgAdmin` directly

### Established Patterns

- Settings-based feature config: `BILLING_PLANS` dict with `manage.py check` validation — `WEBHOOK_EVENTS` uses same pattern
- Celery retry: `autoretry_for=(Exception,)`, `max_retries=N`, `retry_backoff=True` — apply to `deliver_webhook` task
- Adapter-based notification: `send_email(to, template_name, context)` — call for circuit-breaker admin notification
- `transaction.on_commit()` for async dispatch — used by both billing webhook ingestion and email sending; use for outbound webhook delivery too

### Integration Points

- `apps/orgs/` models: `WebhookEndpoint` has FK to `Organization` — lives in new `apps/webhooks/` app (follows orgs/ separation)
- `apps/notifications/`: `send_email()` called from `webhooks/services.py` when endpoint auto-disabled
- Celery beat: add `webhook_delivery_cleanup` periodic task (daily, prune records older than `WEBHOOK_DELIVERY_RETENTION_DAYS`)
- B2B_START/B2B_END markers: entire `apps/webhooks/` app is B2B-gated (scaffolder `--with b2b` flag, same as orgs/)

</code_context>

<deferred>
## Deferred Ideas

- **HOOK-F01: Webhook event catalog UI** — browsable event types with example payloads; already in REQUIREMENTS.md future features; not in this phase
- **Webhook secret auto-rotation** — updating existing integrations without breaking them; explicitly out of scope in REQUIREMENTS.md
- **Delivery replay for all events** — re-sending all missed events to a newly registered endpoint; future phase capability

</deferred>

---

_Phase: 27-outbound-webhooks_
_Context gathered: 2026-03-13_
