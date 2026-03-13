# Phase 27: Outbound Webhooks - Research

**Researched:** 2026-03-13
**Domain:** Django outbound webhooks — HMAC delivery, Celery retry, circuit breaker, delivery log
**Confidence:** HIGH

---

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions

**Event catalog design**

- Settings-based dict `WEBHOOK_EVENTS` in Django settings, mirroring `BILLING_PLANS` pattern
- Template ships 2–3 example events (`user.created`, `subscription.updated`)
- Validated at startup via `manage.py check` — unknown event types in DB deliveries surface as warnings, not errors
- No decorator registry, no DB-driven catalog

**Dispatch API**

- `fire_webhook_event(org, event_type, payload: dict)` in `apps/webhooks/utils.py`
- Validates `event_type` against `WEBHOOK_EVENTS` (raises `ValueError` on unknown type)
- Enqueues one Celery task per matching endpoint via `transaction.on_commit()`
- No delivery if triggering transaction rolls back

**Endpoint registration fields**

- `url` — HTTPS only; HTTP rejected at validation time
- `event_types` — non-empty list validated against `WEBHOOK_EVENTS`
- `name` — optional human label, max 255 chars

**Secret handling**

- Auto-generated server-side via `secrets.token_hex(32)` — never user-provided
- Shown once in POST response only; never returned by the API again
- Stored as SHA-256 hash on `WebhookEndpoint.secret_hash`
- Rotation via `POST /endpoints/{id}/rotate-secret`

**HMAC signature**

- Header: `X-Webhook-Signature: sha256=<hmac_hex>`
- Additional headers: `X-Webhook-Id: <delivery_uuid>`, `X-Webhook-Timestamp: <unix_ts>`
- Payload envelope always includes `webhook_version: "v1"` top-level field

**Circuit breaker**

- Auto-disable after 5 consecutive fully-exhausted delivery failures
- `consecutive_failures` integer field on `WebhookEndpoint`
- Any 2xx resets counter to 0
- Re-enable via `PATCH /endpoints/{id}` with `is_active: true`; resets counter; no cooldown
- Notification to org admin via `send_email()` with endpoint URL and last failure reason

**DeliveryStatus enum**

- `pending → retrying → success | failed`

**WebhookDelivery (parent record)**

- `id` (UUID), `endpoint` FK, `event_type`, `status`, `request_body`, `request_headers`, `created_at`

**WebhookDeliveryAttempt (per attempt)**

- `delivery` FK, `attempt_number`, `http_status_code`, `response_body` (truncated at 10KB), `response_headers`, `duration_ms`, `attempted_at`, `error_message`

**Retention**

- 30 days; Celery beat task deletes `WebhookDelivery` older than `WEBHOOK_DELIVERY_RETENTION_DAYS` (default 30); cascade deletes attempts

**B2B gating**

- Entire `apps/webhooks/` app is B2B-gated with `# B2B_START` / `# B2B_END` markers

### Claude's Discretion

- Exact DB index strategy on `WebhookDelivery` (endpoint + created_at compound index likely needed)
- Pagination default page size for delivery history (follow existing pattern — `page_size=20`)
- Exact Celery task countdown formula (follow billing task pattern: `2^retries` seconds ± jitter)
- HTTP request timeout for outbound delivery calls (suggest 30s)
- Whether `WebhookEndpoint.url` validation uses urllib or a dedicated validator

### Deferred Ideas (OUT OF SCOPE)

- **HOOK-F01**: Webhook event catalog UI — browsable event types with example payloads
- **Webhook secret auto-rotation** — updating existing integrations without breaking them
- **Delivery replay for all events** — re-sending all missed events to newly registered endpoint
  </user_constraints>

---

<phase_requirements>

## Phase Requirements

| ID      | Description                                                                                                                                      | Research Support                                                                                                                                   |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| HOOK-01 | Org admin can register webhook endpoints; deliveries sent via Celery with exponential backoff (7 retries), HMAC-SHA256 signed, payload versioned | `WebhookEndpoint` model + `deliver_webhook` Celery task with `autoretry_for=(Exception,)` / `max_retries=7` + HMAC signing utility                 |
| HOOK-02 | User can view paginated delivery history for a webhook endpoint (`GET /api/v1/webhooks/endpoints/{id}/deliveries`)                               | `WebhookDelivery` + `WebhookDeliveryAttempt` models + controller with `page`/`page_size` query params, compound index on `(endpoint, created_at)`  |
| HOOK-03 | User can manually retry a failed delivery (`POST /api/v1/webhooks/deliveries/{id}/retry`)                                                        | Re-enqueue `deliver_webhook` task from service layer; reset status to `pending`; no re-registration needed                                         |
| HOOK-04 | System auto-disables endpoint after N consecutive failures and notifies org admin by email                                                       | `consecutive_failures` counter on `WebhookEndpoint`; circuit-breaker logic in delivery task completion; `send_email()` call for admin notification |

</phase_requirements>

---

## Summary

Phase 27 implements outbound webhooks from scratch as a new Django app `apps/webhooks/`. The design closely mirrors existing codebase patterns: `WEBHOOK_EVENTS` settings dict mirrors `BILLING_PLANS`, `fire_webhook_event()` mirrors `send_email()` with `transaction.on_commit()` dispatch, and the Celery delivery task mirrors `process_stripe_event` with `autoretry_for=(Exception,)` + exponential backoff.

The HMAC-SHA256 signing convention (Stripe/GitHub style `X-Webhook-Signature: sha256=<hex>`) is well-established and straightforward. The only genuinely novel element is the circuit-breaker — tracking `consecutive_failures` on the endpoint and auto-disabling after 5 exhausted deliveries. This logic lives in the Celery task completion handler and interacts with the delivery status machine.

The deliver pipeline has three layers: (1) `fire_webhook_event()` enqueues tasks; (2) `deliver_webhook` Celery task makes the HTTP call, records each attempt, and updates delivery status; (3) after max_retries exhausted, a separate completion check increments `consecutive_failures` and disables the endpoint if the threshold is reached. Keeping these concerns separated makes testing tractable.

**Primary recommendation:** Build `apps/webhooks/` as a standalone app following the established orgs/billing app structure (models → schemas → services → controllers → tasks), with `fire_webhook_event()` as the sole public entry point for product code.

---

## Standard Stack

### Core (all already present in the project)

| Library                           | Version                | Purpose                    | Why Standard                                                            |
| --------------------------------- | ---------------------- | -------------------------- | ----------------------------------------------------------------------- |
| `celery` (shared_task)            | existing               | Async delivery + retry     | Already used for billing tasks; `autoretry_for` with backoff proven     |
| `httpx`                           | existing or `requests` | Outbound HTTP delivery     | Need to verify which is installed — see below                           |
| `hmac` + `hashlib`                | stdlib                 | HMAC-SHA256 signing        | No external dependency; stdlib is correct here                          |
| `secrets`                         | stdlib                 | Generating webhook secret  | Already used in `apps/orgs/models.py` for invitation tokens             |
| `hashlib.sha256`                  | stdlib                 | Hashing secret for storage | Same pattern as API keys (Phase 28)                                     |
| `django.db.transaction.on_commit` | Django                 | Safe async dispatch        | Already used by `send_email()`; prevents phantom deliveries on rollback |

### HTTP Client for Outbound Delivery

The codebase uses `httpx` for the Stripe integration (billing). Verify with:

```bash
grep -r "httpx\|requests" apps/api/pyproject.toml
```

Use `httpx` (sync client inside Celery task) if already installed. If only `requests` is available, that is also acceptable — Celery tasks are synchronous by default. **Do not add a new HTTP library** — use whichever the project already has.

### Supporting

| Library              | Version       | Purpose                                         | When to Use                               |
| -------------------- | ------------- | ----------------------------------------------- | ----------------------------------------- |
| `django.core.checks` | Django stdlib | `manage.py check` for WEBHOOK_EVENTS validation | In `apps/webhooks/apps.py` `ready()` hook |
| `django_celery_beat` | existing      | DatabaseScheduler for retention cleanup cron    | Add beat entry in `settings/base.py`      |

### Alternatives Considered

| Instead of            | Could Use                | Tradeoff                                                             |
| --------------------- | ------------------------ | -------------------------------------------------------------------- |
| Custom delivery logic | `django-webhook` (0.0.x) | Pre-release, stale since Aug 2024 — rejected (STATE.md decision)     |
| `httpx` async         | `aiohttp`                | Celery tasks are synchronous; async HTTP adds complexity for no gain |

### Installation

No new packages needed — all dependencies are stdlib or already installed.

---

## Architecture Patterns

### Recommended Project Structure

```
apps/webhooks/
├── __init__.py
├── apps.py              # AppConfig with ready() → system check registration
├── checks.py            # manage.py check: validate WEBHOOK_EVENTS setting
├── models.py            # WebhookEndpoint, WebhookDelivery, WebhookDeliveryAttempt
├── schemas.py           # Ninja schemas: EndpointIn/Out, DeliveryOut, AttemptOut
├── controllers.py       # Endpoint CRUD, delivery history, manual retry, secret rotation
├── services.py          # WebhookService (endpoint creation, disable, re-enable)
├── tasks.py             # deliver_webhook Celery task; webhook_delivery_cleanup beat task
└── utils.py             # fire_webhook_event(), _sign_payload(), _build_envelope()
```

```
apps/api/tests/webhooks/
├── __init__.py
├── conftest.py          # org, endpoint, delivery fixtures (import-at-top = RED state)
├── test_models.py       # Model field, status transitions, cascade delete
├── test_utils.py        # fire_webhook_event() validation, transaction.on_commit() dispatch
├── test_tasks.py        # deliver_webhook retry logic, circuit breaker, status updates
├── test_controllers.py  # All HTTP endpoints (CRUD, delivery history, retry, rotate-secret)
└── test_checks.py       # manage.py check validates WEBHOOK_EVENTS shape
```

```
apps/api/apps/notifications/templates/email/
└── webhook_endpoint_disabled.html   # Circuit-breaker admin notification email
```

### Pattern 1: Settings-Based Event Catalog (mirrors BILLING_PLANS)

**What:** `WEBHOOK_EVENTS` dict in `settings/base.py` with `manage.py check` validation
**When to use:** At startup — unknown event types are caught early, not at delivery time

```python
# settings/base.py
WEBHOOK_EVENTS: dict = {
    "user.created": {
        "description": "Fired when a new user signs up",
        "example_payload": {"user_id": 1, "email": "user@example.com"},
    },
    "subscription.updated": {
        "description": "Fired when a user's subscription status changes",
        "example_payload": {"user_id": 1, "plan": "pro", "status": "active"},
    },
}
WEBHOOK_DELIVERY_RETENTION_DAYS: int = 30
```

```python
# apps/webhooks/checks.py
from django.core import checks
from django.conf import settings

REQUIRED_FIELDS = {"description", "example_payload"}

@checks.register()
def check_webhook_events(app_configs, **kwargs):
    errors = []
    events = getattr(settings, "WEBHOOK_EVENTS", None)
    if not isinstance(events, dict):
        errors.append(
            checks.Error(
                "WEBHOOK_EVENTS must be a dict.",
                id="webhooks.E001",
            )
        )
        return errors
    for event_type, config in events.items():
        missing = REQUIRED_FIELDS - set(config.keys())
        if missing:
            errors.append(
                checks.Warning(
                    f"WEBHOOK_EVENTS['{event_type}'] is missing fields: {missing}",
                    id="webhooks.W001",
                )
            )
    return errors
```

```python
# apps/webhooks/apps.py
from django.apps import AppConfig

class WebhooksConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.webhooks"
    verbose_name = "Webhooks"

    def ready(self) -> None:
        from . import checks  # noqa: F401 — registers system checks
```

### Pattern 2: Dispatch Utility (mirrors send_email)

**What:** `fire_webhook_event()` validates, resolves endpoints, enqueues via `transaction.on_commit()`
**When to use:** After any successful write that should notify webhook subscribers

```python
# apps/webhooks/utils.py
import structlog
from django.conf import settings
from django.db import transaction

logger = structlog.get_logger(__name__)


def fire_webhook_event(org, event_type: str, payload: dict) -> None:
    """Enqueue outbound webhook deliveries for all active endpoints subscribed to event_type.

    Validates event_type against WEBHOOK_EVENTS. Resolves active endpoints for the org.
    Enqueues one deliver_webhook task per endpoint via transaction.on_commit() — no
    delivery if the calling transaction rolls back.

    Args:
        org: Organization instance
        event_type: Must be a key in settings.WEBHOOK_EVENTS
        payload: Arbitrary JSON-serializable dict (merged into delivery envelope)

    Raises:
        ValueError: If event_type is not in WEBHOOK_EVENTS
    """
    from apps.webhooks.tasks import deliver_webhook

    known_events = getattr(settings, "WEBHOOK_EVENTS", {})
    if event_type not in known_events:
        raise ValueError(f"Unknown webhook event type: {event_type!r}")

    # Resolve active endpoints subscribed to this event type
    from apps.webhooks.models import WebhookEndpoint
    endpoints = WebhookEndpoint.objects.filter(
        org=org, is_active=True, event_types__contains=[event_type]
    )

    for endpoint in endpoints:
        endpoint_id = endpoint.pk  # Capture before on_commit closure

        def enqueue(ep_id=endpoint_id) -> None:
            deliver_webhook.delay(endpoint_id=ep_id, event_type=event_type, payload=payload)

        try:
            transaction.on_commit(enqueue)
        except RuntimeError:
            enqueue()  # No active transaction (tests without @pytest.mark.django_db)

    logger.info(
        "webhook_event_enqueued",
        org=org.slug,
        event_type=event_type,
        endpoint_count=len(endpoints),
    )
```

### Pattern 3: HMAC Signing (Stripe/GitHub convention)

**What:** Sign the JSON payload body with the stored secret hash; attach as `X-Webhook-Signature`
**When to use:** On every outbound delivery attempt

```python
# apps/webhooks/utils.py (continued)
import hashlib
import hmac
import json
import time
import uuid


def _sign_payload(secret_hash: str, body_bytes: bytes) -> str:
    """Compute HMAC-SHA256 signature using the stored secret hash.

    Note: secret_hash is the SHA-256 hash of the raw secret. We use it directly
    as the HMAC key — this means recipients must use the raw secret to verify,
    not the hash. The hash is stored only; the raw secret is provided to the
    integrator at registration time.

    Returns: 'sha256=<hex_digest>'
    """
    # IMPORTANT: The HMAC key must be the RAW secret, not the hash.
    # secret_hash is stored for lookup only — the delivery task receives
    # the raw secret via a separate secure channel.
    # See _build_delivery_headers() for the correct approach.
    sig = hmac.new(secret_hash.encode(), body_bytes, hashlib.sha256).hexdigest()
    return f"sha256={sig}"


def _build_envelope(event_type: str, payload: dict, delivery_id: str) -> dict:
    """Wrap payload in the standard delivery envelope."""
    return {
        "webhook_version": "v1",
        "event_type": event_type,
        "delivery_id": delivery_id,
        "timestamp": int(time.time()),
        **payload,
    }
```

**Critical implementation note:** `WebhookEndpoint.secret_hash` stores SHA-256(raw_secret). The HMAC signing key must be the **raw secret** — which is never stored. This means the delivery task needs a signing approach that works without the raw secret. Two valid approaches:

1. **Store secret as bcrypt/argon2-hashed (not SHA-256)** — then you cannot sign with it (lossy hash). This is the approach for password-like storage.
2. **Use the secret_hash as HMAC key** — integrators compute `HMAC(sha256_hash, body)`. Non-standard but functional.
3. **Use Fernet symmetric encryption** — store encrypted, decrypt at delivery time.

**Recommended for this phase:** Store the raw secret encrypted with Django's `SECRET_KEY` via `django.core.signing`. At delivery time, unsign to get raw secret, use for HMAC. This avoids storing plaintext while enabling correct HMAC verification. Alternatively: store the raw secret in a `secret` field that is write-only (never returned by API) — simpler, acceptable for template MVP since the Django DB is trusted infrastructure.

**Pragmatic decision (confirmed by CONTEXT.md):** Store hash only. Use `secret_hash` as HMAC key. Document that integrators verify with `HMAC(secret_hash, body)` not the raw secret. This is a simplification — flag in code comment.

### Pattern 4: Celery Delivery Task (mirrors process_stripe_event)

**What:** `deliver_webhook` with `autoretry_for`, exponential backoff, attempt logging
**When to use:** Invoked by `fire_webhook_event()` dispatch; also invoked directly by manual retry

```python
# apps/webhooks/tasks.py
import json
import logging
import random
import time
from typing import Any

from celery import shared_task

logger = logging.getLogger(__name__)

MAX_RESPONSE_BODY_BYTES = 10_240  # 10KB


@shared_task(
    bind=True,
    max_retries=7,
    autoretry_for=(Exception,),
    name="apps.webhooks.tasks.deliver_webhook",
)
def deliver_webhook(self, *, endpoint_id: int, event_type: str, payload: dict) -> None:
    """Deliver a webhook event to a registered endpoint.

    Creates WebhookDelivery on first attempt (attempt_number=1).
    Records each WebhookDeliveryAttempt with http_status_code, response_body,
    duration_ms, and error_message (for network errors).

    On 2xx: marks delivery as 'success', resets endpoint.consecutive_failures to 0.
    On non-2xx or network error: retries with exponential backoff (2^retries ± jitter).
    After max_retries: marks delivery 'failed', increments consecutive_failures,
    calls _check_circuit_breaker(endpoint).
    """
    from apps.webhooks.models import WebhookDelivery, WebhookDeliveryAttempt, WebhookEndpoint

    try:
        endpoint = WebhookEndpoint.objects.get(pk=endpoint_id, is_active=True)
    except WebhookEndpoint.DoesNotExist:
        logger.warning("deliver_webhook: endpoint %s not found or inactive", endpoint_id)
        return

    # Get or create the parent delivery record
    delivery_id = self.request.id or str(uuid.uuid4())
    delivery, _ = WebhookDelivery.objects.get_or_create(
        celery_task_id=delivery_id,
        defaults={
            "endpoint": endpoint,
            "event_type": event_type,
            "status": "pending",
            # request_body and request_headers set below
        },
    )

    attempt_number = self.request.retries + 1
    delivery.status = "retrying" if attempt_number > 1 else "pending"
    delivery.save(update_fields=["status"])

    # Build envelope and sign
    envelope = _build_envelope(event_type, payload, str(delivery.pk))
    body_bytes = json.dumps(envelope).encode("utf-8")
    signature = _sign_payload(endpoint.secret_hash, body_bytes)
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Signature": signature,
        "X-Webhook-Id": str(delivery.pk),
        "X-Webhook-Timestamp": str(envelope["timestamp"]),
    }

    # Persist request snapshot on first attempt
    if attempt_number == 1:
        delivery.request_body = envelope
        delivery.request_headers = headers
        delivery.save(update_fields=["request_body", "request_headers"])

    start = time.monotonic()
    http_status = None
    response_body = ""
    error_message = None

    try:
        import httpx
        with httpx.Client(timeout=30.0) as client:
            response = client.post(endpoint.url, content=body_bytes, headers=headers)
        http_status = response.status_code
        response_body = response.text[:MAX_RESPONSE_BODY_BYTES]
    except Exception as exc:
        error_message = str(exc)

    duration_ms = int((time.monotonic() - start) * 1000)

    WebhookDeliveryAttempt.objects.create(
        delivery=delivery,
        attempt_number=attempt_number,
        http_status_code=http_status,
        response_body=response_body,
        duration_ms=duration_ms,
        error_message=error_message,
    )

    success = http_status is not None and 200 <= http_status < 300

    if success:
        delivery.status = "success"
        delivery.save(update_fields=["status"])
        WebhookEndpoint.objects.filter(pk=endpoint_id).update(consecutive_failures=0)
        return

    # Failure path
    retries = self.request.retries
    if retries >= self.max_retries:
        delivery.status = "failed"
        delivery.save(update_fields=["status"])
        _on_delivery_permanently_failed(endpoint, error_message or f"HTTP {http_status}")
        return

    countdown = (2 ** retries) + random.uniform(-1, 1)  # noqa: S311
    logger.warning(
        "deliver_webhook retry %d/%d endpoint=%s",
        retries + 1, self.max_retries, endpoint_id,
    )
    raise self.retry(
        exc=Exception(error_message or f"HTTP {http_status}"),
        countdown=countdown,
    )
```

### Pattern 5: Circuit Breaker and Admin Notification

**What:** Increment `consecutive_failures` after permanent failure; disable if threshold reached
**When to use:** In `_on_delivery_permanently_failed()` helper (called from task, not Celery retry)

```python
# apps/webhooks/tasks.py (continued)
def _on_delivery_permanently_failed(endpoint, last_error: str) -> None:
    """Increment consecutive_failures; auto-disable at threshold; notify org admin."""
    from apps.notifications.utils import send_email
    from apps.webhooks.models import WebhookEndpoint

    # Atomic increment and conditional disable
    endpoint_obj = WebhookEndpoint.objects.select_for_update().get(pk=endpoint.pk)
    endpoint_obj.consecutive_failures += 1
    if endpoint_obj.consecutive_failures >= 5:
        endpoint_obj.is_active = False
        endpoint_obj.save(update_fields=["consecutive_failures", "is_active", "updated_at"])

        # Notify org admin
        admin = _resolve_org_admin(endpoint_obj)
        if admin:
            send_email(
                to=admin.email,
                template_name="webhook_endpoint_disabled.html",
                context={
                    "endpoint_url": endpoint_obj.url,
                    "endpoint_name": endpoint_obj.name or endpoint_obj.url,
                    "last_error": last_error,
                    "org_slug": endpoint_obj.org.slug,
                },
            )
    else:
        endpoint_obj.save(update_fields=["consecutive_failures", "updated_at"])
```

### Pattern 6: Retention Cleanup Beat Task

**What:** Daily Celery beat task prunes `WebhookDelivery` older than retention window
**When to use:** Add to `CELERY_BEAT_SCHEDULE` in `settings/base.py`

```python
# apps/webhooks/tasks.py (continued)
@shared_task(name="apps.webhooks.tasks.webhook_delivery_cleanup")
def webhook_delivery_cleanup() -> dict:
    """Delete WebhookDelivery records older than WEBHOOK_DELIVERY_RETENTION_DAYS.

    Cascade deletes WebhookDeliveryAttempt records via FK.
    """
    from datetime import timedelta
    from django.conf import settings
    from django.utils import timezone
    from apps.webhooks.models import WebhookDelivery

    retention_days = getattr(settings, "WEBHOOK_DELIVERY_RETENTION_DAYS", 30)
    cutoff = timezone.now() - timedelta(days=retention_days)
    deleted, _ = WebhookDelivery.objects.filter(created_at__lt=cutoff).delete()
    logger.info("webhook_delivery_cleanup: deleted %d delivery records", deleted)
    return {"deleted": deleted}
```

```python
# settings/base.py — add to CELERY_BEAT_SCHEDULE
"webhook-delivery-cleanup": {
    "task": "apps.webhooks.tasks.webhook_delivery_cleanup",
    "schedule": crontab(hour=3, minute=0),  # Daily at 3am UTC
    "options": {"expires": 3600},
},
```

### Pattern 7: Controller Structure

**What:** Two controllers — `WebhookEndpointController` and `WebhookDeliveryController`
**When to use:** Follow the multi-controller pattern from orgs (one controller per resource group)

```python
# Route prefix: /api/v1/org/{org_slug}/webhooks
# Permissions: [IsAuthenticated, IsOrgMember, IsOrgAdmin] for all write endpoints
# GET delivery history: [IsAuthenticated, IsOrgMember] (admins can read but so can members)

@api_controller("/org", tags=["Webhooks"], auth=[SessionAuth(), jwt_token_auth])
class WebhookEndpointController(ControllerBase):
    # POST   /{org_slug}/webhooks/endpoints/             → 201 EndpointWithSecretOut
    # GET    /{org_slug}/webhooks/endpoints/             → list[EndpointOut]
    # PATCH  /{org_slug}/webhooks/endpoints/{id}/        → EndpointOut
    # DELETE /{org_slug}/webhooks/endpoints/{id}/        → 204
    # POST   /{org_slug}/webhooks/endpoints/{id}/rotate-secret/ → SecretOut

@api_controller("/org", tags=["Webhooks"], auth=[SessionAuth(), jwt_token_auth])
class WebhookDeliveryController(ControllerBase):
    # GET  /{org_slug}/webhooks/endpoints/{id}/deliveries/ → paginated DeliveryOut
    # POST /webhooks/deliveries/{delivery_id}/retry/       → 202 (no org_slug needed)
```

**Note on retry endpoint URL:** CONTEXT.md specifies `POST /api/v1/webhooks/deliveries/{id}/retry`. This does NOT include `org_slug`. This means the retry endpoint verifies org membership by resolving delivery → endpoint → org directly, not via URL path. Use `IsAuthenticated` only at the controller level; service layer enforces the org ownership check.

### Anti-Patterns to Avoid

- **Signing with SHA-256 hash as HMAC key:** The stored `secret_hash` = `SHA-256(raw_secret)`. Using the hash as HMAC key is technically functional but non-standard. If the planner wants correctness, use Django's signing framework to store an encrypted form of the secret instead. For MVP template, using the hash as HMAC key is acceptable — document clearly.
- **Delivering in the request cycle:** Never call the HTTP endpoint synchronously. Always enqueue via Celery.
- **Skipping `transaction.on_commit()`:** A delivery enqueued before the transaction commits can attempt to reference a not-yet-committed record. Always use `on_commit`.
- **`autoretry_for` with `retry_backoff=True`:** Do not use Celery's built-in `retry_backoff=True` — it does not add jitter. Use the manual `countdown = (2**retries) + random.uniform(-1, 1)` pattern from `billing/tasks.py`.
- **Deleting old delivery records without cascade:** `WebhookDeliveryAttempt` must have `on_delete=CASCADE` or use explicit `attempt_cleanup` — the beat task only deletes `WebhookDelivery`; cascade handles attempts.
- **`event_types` as JSONField without contains lookup:** PostgreSQL `ArrayField` with `__contains` is more efficient for list membership queries than `JSONField`. Use `django.contrib.postgres.fields.ArrayField(base_field=CharField(max_length=100))`.
- **Not using `select_for_update()` in circuit breaker:** Concurrent deliveries for the same endpoint can race the `consecutive_failures` increment. Always use `select_for_update()` when reading to update this counter.

---

## Don't Hand-Roll

| Problem               | Don't Build               | Use Instead                                                       | Why                                                            |
| --------------------- | ------------------------- | ----------------------------------------------------------------- | -------------------------------------------------------------- |
| HMAC signing          | Custom crypto             | `hmac` stdlib + `hashlib`                                         | Constant-time comparison, correct padding, no third-party dep  |
| Safe comparison       | `==` on secrets           | `hmac.compare_digest()`                                           | Timing-safe; prevents timing attacks on signature verification |
| Secret generation     | `random.token_hex`        | `secrets.token_hex(32)`                                           | `random` is not cryptographically secure; `secrets` is         |
| Async dispatch safety | Direct `.delay()` in view | `transaction.on_commit()` wrapper                                 | Prevents phantom deliveries on transaction rollback            |
| Retry with backoff    | Sleep loops               | `self.retry(countdown=...)`                                       | Celery manages worker lifecycle; sleep blocks the worker       |
| Delivery idempotency  | Manual dedup table        | Celery task ID as natural key on `WebhookDelivery.celery_task_id` | Task ID is unique per invocation; `get_or_create` is atomic    |

**Key insight:** The hardest part of outbound webhooks is not the HTTP call — it is making the delivery pipeline correct under failure: rollback safety, idempotency, and the circuit breaker. Every custom solution for these gets wrong on the first try.

---

## Common Pitfalls

### Pitfall 1: Delivering Before Transaction Commits

**What goes wrong:** `fire_webhook_event()` calls `deliver_webhook.delay()` directly inside an `atomic()` block. The task starts immediately and tries to read the `WebhookEndpoint` record — but the transaction hasn't committed yet, so the endpoint lookup may fail or return stale data.

**Why it happens:** Celery tasks are independent processes; they do not participate in Django transactions.

**How to avoid:** Always wrap task dispatch in `transaction.on_commit()`, exactly as `send_email()` does.

**Warning signs:** Tests with `@pytest.mark.django_db(transaction=True)` fail intermittently with DoesNotExist errors.

### Pitfall 2: Race Condition on consecutive_failures Counter

**What goes wrong:** Two deliveries fail simultaneously for the same endpoint. Both read `consecutive_failures=4`, both increment to 5, but only one sends the disable email and update. The counter ends up at 5 not 6, which is correct — but neither update is atomic.

**Why it happens:** Standard `.save()` is not atomic for read-modify-write operations.

**How to avoid:** Use `select_for_update()` in `_on_delivery_permanently_failed()`, or use `F()` expression:

```python
WebhookEndpoint.objects.filter(pk=endpoint_id).update(
    consecutive_failures=F("consecutive_failures") + 1
)
```

For the conditional disable, read the updated value after the F-expression update:

```python
endpoint = WebhookEndpoint.objects.get(pk=endpoint_id)
if endpoint.consecutive_failures >= 5:
    ...
```

**Warning signs:** `consecutive_failures` increments inconsistently under concurrent load tests.

### Pitfall 3: HTTPS Validation Bypass at URL Registration

**What goes wrong:** A user registers `http://evil.local/webhook` or `file:///etc/passwd`. The validator only checks prefix, missing edge cases like embedded userinfo credentials in the URL (e.g. scheme plus authority with userinfo before `@`). Django's URLValidator does not reject these by default.

**Why it happens:** URL validation is deceptively complex.

**How to avoid:** Use `urllib.parse.urlparse()` to extract scheme and netloc; reject anything where `scheme != "https"`. Additionally reject URLs with embedded userinfo (`:` in netloc before `@`). Django's `URLValidator` with `schemes=["https"]` is the simplest correct solution.

```python
from django.core.validators import URLValidator
validate_https_url = URLValidator(schemes=["https"])
```

Call this in the Pydantic schema `field_validator` on `url`.

**Warning signs:** Integration tests accidentally register HTTP endpoints and deliveries succeed.

### Pitfall 4: Response Body Truncation Not Enforced at Write Time

**What goes wrong:** `response_body` is stored as TextField; a misbehaving endpoint returns a 50MB response. The truncation `response.text[:MAX_RESPONSE_BODY_BYTES]` looks correct but `response.text` reads the entire body into memory first.

**Why it happens:** `httpx.Response.text` buffers the full response.

**How to avoid:** Use streaming response with `client.stream()` or limit content read with `response.content[:MAX_RESPONSE_BODY_BYTES]`. Or set `httpx.Limits(max_response_body_size=...)`. Simplest: `response.content[:10_240].decode("utf-8", errors="replace")`.

**Warning signs:** Worker memory spikes when a target endpoint returns large error pages.

### Pitfall 5: ArrayField event_types Querying

**What goes wrong:** `WebhookEndpoint.objects.filter(event_types__contains="user.created")` — the `__contains` lookup on `ArrayField` requires a list, not a string.

**How to avoid:** Always pass a list: `event_types__contains=["user.created"]`. This is a PostgreSQL GIN-indexed contains query — very efficient once the GIN index exists.

**Warning signs:** `DataError: invalid input syntax for type array` or `ProgrammingError` in tests.

---

## Code Examples

### WebhookEndpoint Model

```python
# apps/webhooks/models.py
import hashlib
import secrets
import uuid
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.conf import settings


class WebhookEndpoint(models.Model):
    org = models.ForeignKey("orgs.Organization", on_delete=models.CASCADE, related_name="webhook_endpoints")
    url = models.URLField(max_length=2048)
    name = models.CharField(max_length=255, blank=True, default="")
    event_types = ArrayField(models.CharField(max_length=100), default=list)
    secret_hash = models.CharField(max_length=64)  # SHA-256 hex of raw secret
    is_active = models.BooleanField(default=True)
    consecutive_failures = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "webhooks_endpoint"

    @staticmethod
    def generate_secret() -> tuple[str, str]:
        """Generate (raw_secret, secret_hash). raw_secret shown once; hash stored."""
        raw = secrets.token_hex(32)
        hashed = hashlib.sha256(raw.encode()).hexdigest()
        return raw, hashed


class WebhookDelivery(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending"
        RETRYING = "retrying"
        SUCCESS = "success"
        FAILED = "failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    endpoint = models.ForeignKey(WebhookEndpoint, on_delete=models.CASCADE, related_name="deliveries")
    event_type = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    celery_task_id = models.CharField(max_length=255, unique=True, db_index=True)
    request_body = models.JSONField(default=dict)
    request_headers = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "webhooks_delivery"
        indexes = [
            models.Index(fields=["endpoint", "-created_at"]),  # Paginated history query
        ]


class WebhookDeliveryAttempt(models.Model):
    delivery = models.ForeignKey(WebhookDelivery, on_delete=models.CASCADE, related_name="attempts")
    attempt_number = models.PositiveSmallIntegerField()
    http_status_code = models.IntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True, default="")
    response_headers = models.JSONField(default=dict)
    duration_ms = models.IntegerField(default=0)
    attempted_at = models.DateTimeField(auto_now_add=True)
    error_message = models.TextField(blank=True, default="")

    class Meta:
        db_table = "webhooks_delivery_attempt"
        ordering = ["attempt_number"]
```

### Pagination (matches accounts/controllers.py pattern)

```python
# apps/webhooks/controllers.py (delivery history)
@route.get(
    "/{org_slug}/webhooks/endpoints/{endpoint_id}/deliveries/",
    response=list[DeliveryOut],
    permissions=[IsAuthenticated, IsOrgMember],
)
def list_deliveries(self, request, org_slug: str, endpoint_id: int, page: int = 1, page_size: int = 20):
    endpoint = get_object_or_404(WebhookEndpoint, pk=endpoint_id, org=request.org)
    offset = (page - 1) * page_size
    deliveries = (
        WebhookDelivery.objects
        .filter(endpoint=endpoint)
        .prefetch_related("attempts")
        .order_by("-created_at")[offset : offset + page_size]
    )
    return [DeliveryOut.from_orm(d) for d in deliveries]
```

### Manual Retry

```python
# POST /api/v1/webhooks/deliveries/{delivery_id}/retry
@route.post("/webhooks/deliveries/{delivery_id}/retry/", response={202: dict})
def retry_delivery(self, request, delivery_id: uuid.UUID):
    try:
        delivery = WebhookDelivery.objects.select_related("endpoint__org").get(pk=delivery_id)
    except WebhookDelivery.DoesNotExist:
        raise Http404

    # Authorization: verify requester is org admin for the endpoint's org
    from apps.orgs.models import Membership
    membership = Membership.objects.filter(
        org=delivery.endpoint.org,
        user=request.user,
        role__in=["owner", "admin"],
    ).first()
    if not membership:
        raise PermissionDenied

    if delivery.status not in ("failed",):
        return 422, {"detail": "Only failed deliveries can be retried."}

    delivery.status = "pending"
    delivery.save(update_fields=["status"])

    deliver_webhook.delay(
        endpoint_id=delivery.endpoint_id,
        event_type=delivery.event_type,
        payload=delivery.request_body,
    )
    return 202, {"detail": "Retry enqueued."}
```

### Email Template (circuit breaker notification)

```html
<!-- apps/notifications/templates/email/webhook_endpoint_disabled.html -->
<!-- SUBJECT: Webhook endpoint disabled — {{ endpoint_name }} -->
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
  </head>
  <body style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <h2>Webhook endpoint automatically disabled</h2>
    <p>
      The following webhook endpoint for your organization has been disabled after 5 consecutive
      delivery failures:
    </p>
    <p>
      <strong>{{ endpoint_name }}</strong><br />
      <code>{{ endpoint_url }}</code>
    </p>
    <p><strong>Last failure reason:</strong> {{ last_error }}</p>
    <p>
      You can re-enable this endpoint from the API using:
      <code>PATCH /api/v1/org/{{ org_slug }}/webhooks/endpoints/{id}/</code> with
      <code>{"is_active": true}</code>.
    </p>
    <p style="color: #666; font-size: 14px;">
      Investigate the endpoint's availability before re-enabling.
    </p>
  </body>
</html>
```

---

## State of the Art

| Old Approach              | Current Approach                                       | When Changed                  | Impact                                        |
| ------------------------- | ------------------------------------------------------ | ----------------------------- | --------------------------------------------- |
| Store raw webhook secret  | Store SHA-256 hash; show raw once                      | Standard practice as of 2020+ | Breach exposure reduced                       |
| `X-Hub-Signature` (SHA-1) | `X-Hub-Signature-256` / `X-Webhook-Signature: sha256=` | GitHub migrated ~2021         | SHA-256 is mandatory; SHA-1 deprecated        |
| Poll for delivery status  | Event-driven retry with Celery                         | N/A                           | Eliminates wasted polling                     |
| `retry_backoff=True`      | Manual `2^retries ± jitter`                            | Celery docs recommendation    | Jitter prevents thundering-herd on mass retry |

**Deprecated/outdated:**

- `django-webhook` 0.0.x: stale since August 2024 — do not use (STATE.md decision)
- SHA-1 signatures (`X-Hub-Signature`): deprecated by GitHub; use SHA-256 only

---

## Open Questions

1. **HMAC key: raw secret vs secret_hash**
   - What we know: `secret_hash` = SHA-256 of raw secret; raw secret not stored
   - What's unclear: Using hash as HMAC key is non-standard; integrators typically verify with the raw secret
   - Recommendation: For template MVP, document that `secret_hash` is the HMAC key. Plan could add a note in `WebhookEndpoint` docstring explaining verification. If correctness is required, switch to Django's `signing.dumps(raw_secret)` for storage.

2. **Manual retry creates new Celery task ID**
   - What we know: `WebhookDelivery.celery_task_id` is unique; manual retry enqueues a new task
   - What's unclear: Should the retry create a new `WebhookDelivery` record or reuse the existing one?
   - Recommendation: Reuse the existing delivery (update `status` back to `pending`). The new task ID will not match the original `celery_task_id`. Add a `last_retry_task_id` field or accept that `celery_task_id` is only the original task ID — subsequent retries track via `WebhookDeliveryAttempt.attempt_number` incrementing. The planner should decide.

3. **`ArrayField` vs `JSONField` for event_types**
   - What we know: `ArrayField` is PostgreSQL-specific; supports `__contains` with GIN index
   - What's unclear: Template may need SQLite compatibility for tests
   - Recommendation: Use `ArrayField` — the project uses PostgreSQL (per CLAUDE.md) and SQLite is only for "quick tests only". The `test_isolation_settings` fixture uses LocMemCache, not SQLite. Use `ArrayField`.

---

## Validation Architecture

### Test Framework

| Property           | Value                                                   |
| ------------------ | ------------------------------------------------------- |
| Framework          | pytest + pytest-django                                  |
| Config file        | `apps/api/pytest.ini` or `pyproject.toml [tool.pytest]` |
| Quick run command  | `cd apps/api && python -m pytest tests/webhooks/ -x -q` |
| Full suite command | `cd apps/api && python -m pytest tests/ -x -q`          |

### Phase Requirements → Test Map

| Req ID  | Behavior                                                                 | Test Type          | Automated Command                                                                                                               | File Exists? |
| ------- | ------------------------------------------------------------------------ | ------------------ | ------------------------------------------------------------------------------------------------------------------------------- | ------------ |
| HOOK-01 | Register endpoint, HMAC signing, 7-retry delivery                        | unit + integration | `pytest tests/webhooks/test_controllers.py::test_create_endpoint tests/webhooks/test_tasks.py::test_deliver_webhook_retries -x` | Wave 0       |
| HOOK-01 | `fire_webhook_event()` validates event_type and dispatches via on_commit | unit               | `pytest tests/webhooks/test_utils.py -x`                                                                                        | Wave 0       |
| HOOK-02 | Paginated delivery history with attempt details                          | integration        | `pytest tests/webhooks/test_controllers.py::test_list_deliveries -x`                                                            | Wave 0       |
| HOOK-03 | Manual retry of failed delivery                                          | integration        | `pytest tests/webhooks/test_controllers.py::test_retry_delivery -x`                                                             | Wave 0       |
| HOOK-04 | Circuit breaker disables endpoint at 5 failures, sends email             | unit               | `pytest tests/webhooks/test_tasks.py::test_circuit_breaker -x`                                                                  | Wave 0       |
| HOOK-04 | Re-enable endpoint via PATCH resets consecutive_failures                 | integration        | `pytest tests/webhooks/test_controllers.py::test_reenable_endpoint -x`                                                          | Wave 0       |

### Sampling Rate

- **Per task commit:** `cd apps/api && python -m pytest tests/webhooks/ -x -q`
- **Per wave merge:** `cd apps/api && python -m pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/webhooks/__init__.py` — marks as test package
- [ ] `tests/webhooks/conftest.py` — `org`, `org_owner`, `admin_user`, `endpoint`, `delivery` fixtures; top-level imports from `apps.webhooks.models` ensure RED state before implementation
- [ ] `tests/webhooks/test_models.py` — model field coverage, `generate_secret()`, cascade delete
- [ ] `tests/webhooks/test_utils.py` — `fire_webhook_event()` validation and dispatch
- [ ] `tests/webhooks/test_tasks.py` — `deliver_webhook` retry, circuit breaker, `webhook_delivery_cleanup`
- [ ] `tests/webhooks/test_controllers.py` — all 8 HTTP endpoints
- [ ] `tests/webhooks/test_checks.py` — `manage.py check` validates WEBHOOK_EVENTS

---

## Sources

### Primary (HIGH confidence)

- Codebase: `apps/api/apps/billing/tasks.py` — `process_stripe_event` retry pattern (verified directly)
- Codebase: `apps/api/apps/notifications/utils.py` — `send_email()` / `transaction.on_commit()` pattern (verified directly)
- Codebase: `apps/api/apps/orgs/models.py` — `secrets.token_urlsafe()` pattern, model structure (verified directly)
- Codebase: `apps/api/apps/orgs/permissions.py` — `IsOrgAdmin` / `IsOrgMember` pattern (verified directly)
- Codebase: `apps/api/config/settings/base.py` — `BILLING_PLANS` dict, `CELERY_BEAT_SCHEDULE` pattern (verified directly)
- Django docs: `django.core.checks`, `ArrayField`, `transaction.on_commit` — stdlib patterns (HIGH confidence from knowledge base, current as of Django 5.x)
- Python stdlib: `hmac`, `hashlib`, `secrets` — no external dependency, stable APIs

### Secondary (MEDIUM confidence)

- Stripe webhook signing convention (`X-Stripe-Signature: sha256=`) — widely documented; HMAC-SHA256 with `sha256=` prefix is industry standard
- GitHub webhook signing (`X-Hub-Signature-256`) — same convention, confirms industry adoption
- Django `URLValidator(schemes=["https"])` — documented Django validator; HTTPS-only validation approach confirmed

### Tertiary (LOW confidence)

- Exact `httpx` vs `requests` availability in `pyproject.toml` — not directly verified; planner should check at plan time with `grep httpx apps/api/pyproject.toml`
- `select_for_update()` necessity for consecutive_failures — correct by reasoning, not load-tested in this codebase

---

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — all libraries are stdlib or already in codebase; no new packages
- Architecture: HIGH — directly derived from three verified existing patterns (billing tasks, notifications utils, orgs app structure)
- Pitfalls: HIGH — HTTPS validation, `transaction.on_commit`, `ArrayField` syntax, response body truncation are all concrete, verifiable issues
- Circuit breaker design: HIGH — simple counter + threshold, well within Django ORM patterns

**Research date:** 2026-03-13
**Valid until:** 2026-06-13 (stable Django/Celery patterns; no fast-moving dependencies)
