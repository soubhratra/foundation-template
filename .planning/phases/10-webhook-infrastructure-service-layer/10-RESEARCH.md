# Phase 10: Webhook Infrastructure + Service Layer - Research

**Researched:** 2026-03-08
**Domain:** Django webhook receiver, Celery async dispatch, BillingService layer, Stripe subscription lifecycle
**Confidence:** HIGH

---

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions

**Phase Boundary**
Backend-only phase. Deliver the complete BillingService layer, Stripe webhook receiver (plain Django view, not Ninja), async Celery dispatch, Tier-1 event handlers, subscription lifecycle operations (create/upgrade/downgrade/cancel/reactivate), one-time payment, metered usage recording and retrieval, proration preview, and the `@require_active_subscription` access-gating decorator. No frontend work in this phase — that is Phase 11.

**@require_active_subscription gating behavior**

- Statuses that PASS the gate: `ACTIVE` and `TRIALING` only.
- Users with `cancel_at_period_end=True` PASS the gate — they paid through the current period.
- Users with no Customer or Subscription record FAIL the gate — treated as non-subscribers, not "free tier."
- Failed gate returns HTTP 403 Forbidden using the existing `PermissionDenied` exception.

**Webhook failure handling**

- Tier-1 event handlers run inside a Celery task dispatched after HMAC signature verification.
- On transient failure: retry with exponential backoff, max 3 attempts. `ProcessedWebhookEvent` idempotency check prevents double-processing on retry.
- After 3 failures: task moves to Celery dead-letter queue; error logged at CRITICAL level.
- If Celery task dispatch itself fails (broker down): return HTTP 500 to Stripe — do NOT swallow and return 200.
- Unrecognized / unsupported event types: acknowledge silently (HTTP 200, logged at DEBUG level).

**Proration preview**

- `preview_proration` is added to the `PaymentAdapter` ABC.
- Return shape: `{ "amount_due_now": int, "next_invoice_total": int, "proration_date": int, "currency": str }`
- Amounts in smallest currency unit (cents) matching Stripe convention.

**BillingService structure**

- Single `BillingService` class in `apps/billing/services.py`.
- Service methods call `get_adapter()` helper (imports and instantiates class at `settings.BILLING_ADAPTER`) — never importing `StripeAdapter` directly.
- Consistent with `accounts/services.py`, `ai/services.py` patterns.

### Claude's Discretion

- Celery task naming and retry backoff timing (jitter, base delay)
- Exact `get_adapter()` helper placement (billing `__init__` vs `utils.py`)
- How `StubAdapter` / `MockAdapter` is structured for tests (full Protocol implementation or selective override)
- Whether `@require_active_subscription` is a function decorator or a Django permission class (either works, decorator is more flexible for Ninja endpoints)

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>

## Phase Requirements

| ID       | Description                                                                                                                              | Research Support                                                                                                                 |
| -------- | ---------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| HOOK-01  | Plain Django view (not Ninja) receives Stripe webhook events with raw body for HMAC signature verification                               | Django `@csrf_exempt` + `request.body` pattern; must NOT use Ninja auto-routing                                                  |
| HOOK-02  | Webhook view returns HTTP 200 immediately after signature verification; processing dispatched to async Celery task                       | `task.delay()` dispatched before returning `HttpResponse(status=200)`                                                            |
| HOOK-03  | `ProcessedWebhookEvent` with `unique_together(provider, event_id)` prevents duplicate processing                                         | Model already exists; `get_or_create` with `IntegrityError` catch pattern                                                        |
| HOOK-04  | Tier-1 event handlers: `checkout.session.completed`, `customer.subscription.created/updated/deleted`, `invoice.payment_succeeded/failed` | Stripe event type→handler dispatch map; field extraction per event documented                                                    |
| SUB-01   | User can start a subscription via Stripe Checkout session                                                                                | `BillingService.create_checkout_session()` → adapter → `StripeAdapter.create_checkout_session()` already implemented             |
| SUB-02   | User can upgrade subscription plan (with proration preview)                                                                              | `BillingService.upgrade_subscription()` + new `preview_proration()` adapter method → Stripe invoice preview API                  |
| SUB-03   | User can downgrade subscription plan                                                                                                     | `BillingService.downgrade_subscription()` → `adapter.modify_subscription()` with `proration_behavior="create_prorations"`        |
| SUB-04   | User can cancel (at period end)                                                                                                          | `BillingService.cancel_subscription()` → `adapter.cancel_subscription(cancel_at_period_end=True)`                                |
| SUB-05   | User can reactivate a cancelled-at-period-end subscription                                                                               | `BillingService.reactivate_subscription()` → `adapter.modify_subscription()` with `cancel_at_period_end=False` via Stripe update |
| PAY-01   | User can complete a one-time payment via Stripe Checkout                                                                                 | `BillingService.create_one_time_payment()` → `adapter.create_checkout_session(mode="payment")`                                   |
| USAGE-01 | API endpoint to record metered usage via Stripe Meter Events v2                                                                          | `BillingService.record_usage()` → `adapter.record_usage()` → Stripe v2 billing meter events                                      |
| USAGE-02 | API endpoint to retrieve current period metered usage                                                                                    | `BillingService.get_usage()` → new `get_usage_summary()` adapter method → `client.billing.meters.list_event_summaries()`         |
| CUST-03  | `@require_active_subscription` decorator checks subscription status and `cancel_at_period_end`                                           | Function decorator using `PermissionDenied` (already handled by global handler in `config/urls.py`)                              |

</phase_requirements>

---

## Summary

Phase 10 is a pure backend phase that builds three interconnected layers over the Phase 9 scaffold: (1) a Stripe webhook receiver as a plain Django view with HMAC verification and async Celery dispatch, (2) a `BillingService` class that implements the complete subscription lifecycle using the `PaymentAdapter` interface without ever importing `StripeAdapter` directly, and (3) the `@require_active_subscription` access-gating decorator.

All foundational models exist (`Subscription`, `Customer`, `Payment`, `ProcessedWebhookEvent`, `PlanProviderMapping`), the `PaymentAdapter` ABC has all lifecycle methods, Celery is already configured with Redis broker and `django-db` result backend, and the `# BILLING_START / # BILLING_END` URL markers are in place. This phase is almost entirely new code on top of an already-wired scaffold with zero greenfield database work needed — the only model change is adding `preview_proration` and `get_usage_summary` to the `PaymentAdapter` ABC and `StripeAdapter`.

The key technical risks are: (a) getting the raw body read correctly before any Django middleware touches it (critical for HMAC), (b) the `ProcessedWebhookEvent` race condition on concurrent retries (use `get_or_create` with `IntegrityError` handling, not a pre-check), and (c) Stripe's `customer.subscription.created` firing before `checkout.session.completed` in some flows — the handler must be idempotent either way.

**Primary recommendation:** Structure the Celery task as a dispatcher that uses a type→handler map and wraps each handler call in the `ProcessedWebhookEvent` idempotency check. Keep all handler business logic in `BillingService` methods so they can be unit-tested with the `StubAdapter` without any Celery or HTTP involvement.

---

## Standard Stack

### Core (all already installed in Phase 9)

| Library                | Version            | Purpose                                                    | Why Standard                             |
| ---------------------- | ------------------ | ---------------------------------------------------------- | ---------------------------------------- |
| Django                 | 5.x                | Plain webhook view, ORM, `@csrf_exempt`                    | Already installed                        |
| Celery                 | 5.x                | Async task dispatch, exponential backoff retry             | Already configured at `config/celery.py` |
| stripe (Python SDK)    | v14 (StripeClient) | `construct_event`, `invoices.create_preview`, meter events | Phase 9 established StripeClient pattern |
| pytest + pytest-django | latest             | Unit tests with `StubAdapter`, DB fixture tests            | Project standard                         |
| factory_boy            | latest             | Test fixture generation                                    | Project standard                         |

### Supporting

| Library                                     | Version         | Purpose                                               | When to Use                                              |
| ------------------------------------------- | --------------- | ----------------------------------------------------- | -------------------------------------------------------- |
| `django.core.exceptions.PermissionDenied`   | Django built-in | `@require_active_subscription` gate failure           | Already handled by global handler in `config/urls.py`    |
| `django.utils.module_loading.import_string` | Django built-in | `get_adapter()` helper — load `BILLING_ADAPTER` class | Used in `BillingService.__init__` or module-level helper |
| `django.db.IntegrityError`                  | Django built-in | Catch duplicate `ProcessedWebhookEvent` insert        | Concurrent retry safety                                  |
| `celery.utils.log.get_task_logger`          | Celery built-in | Task-level logging that includes task ID              | Celery task best practice                                |

### Alternatives Considered

| Instead of                                            | Could Use                                      | Tradeoff                                                                                                                                                       |
| ----------------------------------------------------- | ---------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Function decorator for `@require_active_subscription` | Django permission class + Ninja `permissions=` | Decorator is more granular per-endpoint; permission class works for controller-wide gating. Either works — decorator recommended per CONTEXT.md                |
| `get_or_create` for idempotency                       | Pre-check `exists()` then insert               | `get_or_create` is atomic; `exists()` + insert has a TOCTOU race that breaks idempotency under concurrent retries                                              |
| `autoretry_for` with `retry_backoff`                  | Manual `self.retry()` with countdown           | `autoretry_for` is cleaner for fixed exception types; manual retry gives more control over specific cases (e.g., only retry DB errors, not programming errors) |

**Installation:** No new packages needed — all dependencies installed in Phase 9.

---

## Architecture Patterns

### Recommended File Structure for This Phase

```
apps/api/apps/billing/
├── adapters.py          # ADD: preview_proration() and get_usage_summary() to ABC + StripeAdapter
├── services.py          # NEW: BillingService class — all billing business logic
├── tasks.py             # NEW: Celery task: process_stripe_webhook + dispatch map
├── webhooks.py          # NEW: Plain Django view: stripe_webhook_view
├── decorators.py        # NEW: @require_active_subscription function decorator
├── models.py            # UNCHANGED: all models already exist
└── adapters.py          # MODIFY: add 2 new abstract methods

apps/api/config/
└── urls.py              # MODIFY: register webhook URL inside # BILLING_START block

apps/api/tests/billing/
├── conftest.py          # EXTEND: add StubAdapter fixture, subscription/payment fixtures
├── test_adapters.py     # EXTEND: add test for new abstract methods exist on ABC
├── test_services.py     # NEW: BillingService unit tests using StubAdapter
├── test_tasks.py        # NEW: Celery task tests (eager mode, idempotency)
├── test_webhooks.py     # NEW: Webhook view tests (HMAC valid/invalid, HTTP 200, dispatch)
└── test_decorators.py   # NEW: @require_active_subscription tests
```

### Pattern 1: Plain Django View for Webhook Receipt

The webhook view MUST be a plain Django function view, not a Ninja controller. Ninja routes go through different middleware and the `request.body` may be consumed before reaching the view. Register it with `@csrf_exempt` — this is safe because security is provided by HMAC signature verification, not CSRF tokens.

```python
# Source: Stripe official docs + Django csrf_exempt pattern
# apps/billing/webhooks.py

import logging

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.billing.adapters import get_adapter
from apps.billing.tasks import process_stripe_webhook

logger = logging.getLogger(__name__)


@require_POST
@csrf_exempt
def stripe_webhook_view(request: HttpRequest) -> HttpResponse:
    payload: bytes = request.body
    sig_header: str = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    webhook_secret: str = settings.STRIPE_WEBHOOK_SECRET

    adapter = get_adapter()
    try:
        event = adapter.construct_webhook_event(
            payload=payload,
            signature_header=sig_header,
            webhook_secret=webhook_secret,
        )
    except ValueError:
        logger.warning("Stripe webhook signature verification failed")
        return HttpResponse(status=400)

    try:
        process_stripe_webhook.delay(event)
    except Exception:
        logger.exception("Failed to dispatch Stripe webhook task — returning 500 so Stripe retries")
        return HttpResponse(status=500)

    return HttpResponse(status=200)
```

**Register in `config/urls.py` inside `# BILLING_START / # BILLING_END`:**

```python
# BILLING_START
path("api/v1/billing/webhooks/stripe/", stripe_webhook_view),
# BILLING_END
```

### Pattern 2: Celery Task with Idempotency Guard and Dispatcher

The task receives the full event dict, guards with `ProcessedWebhookEvent`, then dispatches to a handler by event type. All handler functions delegate to `BillingService` methods.

```python
# apps/billing/tasks.py
import logging
from typing import Any

from celery import shared_task
from celery.utils.log import get_task_logger
from django.db import IntegrityError

from apps.billing.models import ProcessedWebhookEvent

task_logger = get_task_logger(__name__)

TIER_1_HANDLERS: dict[str, str] = {
    "checkout.session.completed": "_handle_checkout_session_completed",
    "customer.subscription.created": "_handle_subscription_created",
    "customer.subscription.updated": "_handle_subscription_updated",
    "customer.subscription.deleted": "_handle_subscription_deleted",
    "invoice.payment_succeeded": "_handle_invoice_payment_succeeded",
    "invoice.payment_failed": "_handle_invoice_payment_failed",
}


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=5,          # base delay in seconds (5, 10, 20 with jitter)
    retry_backoff_max=60,     # cap retries at 60s delay
    retry_jitter=True,
    max_retries=3,
)
def process_stripe_webhook(self, event: dict[str, Any]) -> None:
    event_id: str = event["id"]
    event_type: str = event["type"]
    provider = "stripe"

    # Idempotency guard — race-safe via unique_together constraint
    try:
        _, created = ProcessedWebhookEvent.objects.get_or_create(
            provider=provider,
            event_id=event_id,
        )
    except IntegrityError:
        task_logger.info("Duplicate webhook event %s — skipping", event_id)
        return

    if not created:
        task_logger.info("Event %s already processed — skipping", event_id)
        return

    handler_name = TIER_1_HANDLERS.get(event_type)
    if handler_name is None:
        task_logger.debug("Unrecognized Stripe event type: %s — acknowledged", event_type)
        return

    from apps.billing.services import BillingService
    service = BillingService()
    handler = getattr(service, handler_name)
    handler(event["data"]["object"])
```

**On MaxRetriesExceededError (after 3 failures):** The task moves to the Celery failure state. Log at CRITICAL level using the `on_failure` callback OR by catching `MaxRetriesExceededError` in a wrapper. With Redis as the broker, tasks do not go to a native DLQ — instead, use `django-celery-results` (already configured: `CELERY_RESULT_BACKEND = "django-db"`) to inspect failed tasks, combined with a CRITICAL-level log.

```python
# on_failure callback approach (attach to the task)
def on_failure(self, exc, task_id, args, kwargs, einfo):
    import logging
    logging.getLogger(__name__).critical(
        "Stripe webhook task %s permanently failed after max retries: %s",
        task_id, exc, exc_info=einfo,
    )
```

### Pattern 3: BillingService — Adapter-Delegating Service Class

```python
# apps/billing/services.py
from django.conf import settings
from django.utils.module_loading import import_string

from apps.billing.adapters import PaymentAdapter


def get_adapter() -> PaymentAdapter:
    """Instantiate the configured payment adapter from BILLING_ADAPTER setting."""
    klass = import_string(settings.BILLING_ADAPTER)
    return klass()


class BillingService:
    """All billing business logic. Delegates I/O to the PaymentAdapter.

    Unit-testable with any stub that implements PaymentAdapter.
    """

    def __init__(self, adapter: PaymentAdapter | None = None) -> None:
        self._adapter = adapter or get_adapter()

    def create_checkout_session(self, user, plan_id: str, billing_period: str, ...) -> dict: ...
    def cancel_subscription(self, user) -> dict: ...
    def reactivate_subscription(self, user) -> dict: ...
    def upgrade_subscription(self, user, new_plan_id: str, billing_period: str) -> dict: ...
    def downgrade_subscription(self, user, new_plan_id: str, billing_period: str) -> dict: ...
    def preview_proration(self, user, new_plan_id: str, billing_period: str) -> dict: ...
    def create_one_time_payment(self, user, price_id: str, ...) -> dict: ...
    def record_usage(self, user, meter_event_name: str, value: int, identifier: str | None) -> dict: ...
    def get_usage_summary(self, user, meter_id: str, start_time: int, end_time: int) -> dict: ...

    # Internal webhook handlers (called by Celery task)
    def _handle_checkout_session_completed(self, session: dict) -> None: ...
    def _handle_subscription_created(self, subscription: dict) -> None: ...
    def _handle_subscription_updated(self, subscription: dict) -> None: ...
    def _handle_subscription_deleted(self, subscription: dict) -> None: ...
    def _handle_invoice_payment_succeeded(self, invoice: dict) -> None: ...
    def _handle_invoice_payment_failed(self, invoice: dict) -> None: ...
```

**Key rule:** Service methods look up `Customer` and `Subscription` via Django ORM; they never accept or return Stripe-specific objects. All provider interaction goes through `self._adapter`.

### Pattern 4: StubAdapter for Unit Testing

```python
# tests/billing/conftest.py (extend existing conftest)
from typing import Any
from apps.billing.adapters import PaymentAdapter

class StubAdapter(PaymentAdapter):
    """In-memory test double — no HTTP calls, no Stripe dependency."""

    def __init__(self):
        self.calls: list[tuple[str, dict]] = []

    def create_customer(self, user_id, email) -> dict:
        self.calls.append(("create_customer", {"user_id": user_id, "email": email}))
        return {"provider_customer_id": f"cus_stub_{user_id}"}

    def create_checkout_session(self, customer_id, price_id, mode, success_url, cancel_url, trial_days=0) -> dict:
        self.calls.append(("create_checkout_session", locals()))
        return {"checkout_url": "https://stub.checkout/", "session_id": "cs_stub_123"}

    def create_portal_session(self, customer_id, return_url) -> dict:
        return {"portal_url": "https://stub.portal/"}

    def cancel_subscription(self, subscription_id, cancel_at_period_end=True) -> dict:
        return {"subscription_id": subscription_id, "status": "active", "cancel_at_period_end": cancel_at_period_end}

    def modify_subscription(self, subscription_id, new_price_id, proration_behavior="create_prorations") -> dict:
        return {"subscription_id": subscription_id, "status": "active"}

    def construct_webhook_event(self, payload, signature_header, webhook_secret) -> dict:
        import json
        return json.loads(payload)

    def record_usage(self, meter_event_name, customer_id, value, identifier=None) -> dict:
        return {"identifier": identifier or "stub_id"}

    def list_invoices(self, customer_id, limit=10) -> list[dict]:
        return []

    def preview_proration(self, subscription_id, new_price_id, proration_date) -> dict:
        return {"amount_due_now": 0, "next_invoice_total": 0, "proration_date": proration_date, "currency": "usd"}

    def get_usage_summary(self, meter_id, customer_id, start_time, end_time) -> dict:
        return {"aggregated_value": 0, "start_time": start_time, "end_time": end_time}


@pytest.fixture
def stub_adapter():
    return StubAdapter()

@pytest.fixture
def billing_service(stub_adapter):
    from apps.billing.services import BillingService
    return BillingService(adapter=stub_adapter)
```

### Pattern 5: @require_active_subscription Decorator

```python
# apps/billing/decorators.py
import functools
from django.core.exceptions import PermissionDenied
from apps.billing.models import Subscription, SubscriptionStatus

PASSING_STATUSES = {SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING}

def require_active_subscription(view_func):
    """Gate a view to users with an active or trialing subscription.

    cancel_at_period_end=True passes — user paid through the current period.
    No Customer or Subscription record fails — treated as non-subscriber.
    Failed gate raises PermissionDenied → HTTP 403 via global handler.
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            customer = request.user.billing_customer
            sub = customer.subscription
        except Exception:
            raise PermissionDenied("Active subscription required")

        if sub.status not in PASSING_STATUSES:
            raise PermissionDenied("Active subscription required")

        return view_func(request, *args, **kwargs)
    return wrapper
```

For Ninja Extra controllers, apply as: `@require_active_subscription` on individual endpoint methods inside the controller class. The global `permission_denied_handler` in `config/urls.py` already formats 403 responses.

### Tier-1 Event Handler — Field Extraction Map

| Event                           | Key Fields                                                                                                              | Model Updates                                                                               |
| ------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| `checkout.session.completed`    | `session["subscription"]`, `session["customer"]`, `session["metadata"]`                                                 | Link `stripe_subscription_id` to `Subscription`; confirm `stripe_customer_id` on `Customer` |
| `customer.subscription.created` | `sub["id"]`, `sub["status"]`, `sub["current_period_start"]`, `sub["current_period_end"]`, `sub["cancel_at_period_end"]` | Upsert `Subscription` record; set status from `SubscriptionStatus` enum                     |
| `customer.subscription.updated` | Same as created + `sub["cancel_at_period_end"]`                                                                         | Update all fields on existing `Subscription`                                                |
| `customer.subscription.deleted` | `sub["id"]`, `sub["status"]` (will be `"canceled"`)                                                                     | Set `status=CANCELED` on `Subscription`                                                     |
| `invoice.payment_succeeded`     | `inv["subscription"]`, `inv["amount_paid"]`, `inv["currency"]`, `inv["payment_intent"]`                                 | Create or update `Payment` record; set `Subscription.status=ACTIVE` if was `PAST_DUE`       |
| `invoice.payment_failed`        | `inv["subscription"]`, `inv["amount_due"]`                                                                              | Set `Subscription.status=PAST_DUE`                                                          |

**Note:** `customer.subscription.created` may fire before `checkout.session.completed` in some Stripe flows. Handlers must be idempotent — use `update_or_create` on `Subscription` keyed on `stripe_subscription_id`.

### Anti-Patterns to Avoid

- **Reading `request.data` or `request.POST` in webhook view:** Parses the body — breaks HMAC. Always use `request.body` (raw bytes).
- **Using Ninja router for the webhook URL:** Ninja middleware may consume/transform the request body. Use a plain `path()` with a plain Django view.
- **Pre-check then insert for idempotency:** `if not ProcessedWebhookEvent.objects.filter(...).exists(): ProcessedWebhookEvent.objects.create(...)` has a race condition under concurrent retries. Use `get_or_create` and catch `IntegrityError`.
- **Importing `StripeAdapter` directly in `services.py`:** Breaks the adapter pattern. Always use `get_adapter()`.
- **Returning HTTP 200 when Celery dispatch fails:** If the broker is down and `task.delay()` raises, return HTTP 500 so Stripe retries the webhook delivery.
- **Handling all exceptions identically in the Celery task:** `autoretry_for=(Exception,)` retries everything, including programming errors. Consider narrowing to `(OSError, django.db.OperationalError)` in production — for this template, `Exception` is acceptable given `max_retries=3`.

---

## Don't Hand-Roll

| Problem                     | Don't Build                                                 | Use Instead                                                                                  | Why                                                                                                |
| --------------------------- | ----------------------------------------------------------- | -------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| HMAC signature verification | Custom timing-safe compare                                  | `adapter.construct_webhook_event()` (delegates to `stripe_sdk.StripeClient.construct_event`) | Stripe's SDK handles timestamp validation, replay attack window (5 min), and `hmac.compare_digest` |
| Celery exponential backoff  | Manual sleep/countdown calculation                          | `retry_backoff=5, retry_jitter=True, max_retries=3` on `@shared_task`                        | Built into Celery 5.x; handles jitter to prevent thundering herd                                   |
| Adapter resolution          | Hardcoded `from apps.billing.adapters import StripeAdapter` | `import_string(settings.BILLING_ADAPTER)`                                                    | Already established in Phase 9; allows swap by config                                              |
| Test doubles                | Mocking `stripe` module                                     | `StubAdapter(PaymentAdapter)` — full protocol implementation                                 | Stub tests service logic; mock tests adapter logic — they test different things                    |
| Subscription status mapping | String comparisons to Stripe statuses                       | `SubscriptionStatus` Django TextChoices enum                                                 | Already exists in `models.py`; type-safe, choices-validated                                        |

**Key insight:** The HMAC verification and retry logic are deceptively complex edge cases — Stripe's SDK and Celery's built-in backoff handle edge cases that custom implementations routinely miss (replay window, jitter, partial retries).

---

## Common Pitfalls

### Pitfall 1: Stripe `customer.subscription.created` fires before `checkout.session.completed`

**What goes wrong:** Handler for `subscription.created` tries to find a `Subscription` record that doesn't exist yet, or creates a duplicate when `checkout.session.completed` runs later.
**Why it happens:** Stripe's internal event sequencing is not guaranteed — `subscription.created` can arrive first.
**How to avoid:** Use `Subscription.objects.update_or_create(stripe_subscription_id=sub_id, ...)` in all subscription handlers. Never assume any particular event arrives first.
**Warning signs:** Duplicate `Subscription` rows, `DoesNotExist` errors in `_handle_checkout_session_completed`.

### Pitfall 2: Django Middleware Consuming `request.body`

**What goes wrong:** `request.body` returns empty bytes; signature verification always fails.
**Why it happens:** Some Django middleware (e.g., `GZipMiddleware`, custom JSON parsers) reads and decodes the body stream before the view. `request.body` is a property that reads the raw socket stream once.
**How to avoid:** Webhook view is a plain function view registered directly in `urls.py` — not through Ninja. Verify no custom middleware pre-processes the body.
**Warning signs:** Consistent 400 responses on all webhook calls even with valid signatures in tests.

### Pitfall 3: Race Condition in Idempotency Check

**What goes wrong:** Two concurrent retries of the same webhook both pass the existence check, both insert a `ProcessedWebhookEvent`, and both handlers run — creating duplicate `Subscription` or `Payment` records.
**Why it happens:** `if not exists(): create()` is two queries — not atomic.
**How to avoid:** Use `get_or_create()` which uses a single `SELECT ... WHERE ... OR INSERT` under the hood. Wrap in `try/except IntegrityError` for extra safety on databases with race conditions at the isolation level.
**Warning signs:** Duplicate `Payment` records with the same `stripe_payment_intent_id`.

### Pitfall 4: Celery Task Dispatch Failure Silently Swallowed

**What goes wrong:** Redis broker goes down; `task.delay()` raises; view catches it and returns 200; Stripe marks the webhook as delivered and never retries.
**Why it happens:** Over-broad exception handling in the view.
**How to avoid:** The webhook view must NOT catch dispatch exceptions. Let them propagate — or explicitly return HTTP 500. Stripe retries on 5xx.
**Warning signs:** Events silently dropped during Redis outages with no Stripe retry.

### Pitfall 5: `preview_proration` Using a Stale `proration_date`

**What goes wrong:** The proration amount shown in the UI differs from the amount actually charged because the proration date was computed at preview time but not passed to the actual subscription update.
**Why it happens:** Stripe uses the `proration_date` as an anchor for proration calculation — if you preview at T=0 and update at T=60, the amounts differ unless you pass the same `proration_date` to the update call.
**How to avoid:** Return `proration_date` from `preview_proration()` and pass it verbatim to `modify_subscription()` when the user confirms.
**Warning signs:** Users reporting "I was charged a different amount than shown."

### Pitfall 6: `@require_active_subscription` Applied to Ninja Controller vs. Individual Endpoints

**What goes wrong:** Decorator applied at class level doesn't fire for Ninja Extra because Django function decorators don't automatically wrap Ninja's method resolution.
**Why it happens:** Ninja Extra routes go through its own routing layer, not Django's standard view dispatch.
**How to avoid:** Apply `@require_active_subscription` to individual endpoint methods inside the controller class using `@route.get(...)` + the decorator in the method body, OR wire it using Ninja Extra's `permissions=` parameter with a custom permission class. The function decorator approach works when applied directly to the endpoint method.
**Warning signs:** Decorator applied but 403 never returned to unauthenticated users; all requests pass regardless of status.

---

## Code Examples

### Proration Preview — StripeAdapter Implementation

```python
# Source: https://docs.stripe.com/api/invoices/create_preview
# Add to StripeAdapter in adapters.py

def preview_proration(
    self,
    subscription_id: str,
    new_price_id: str,
    proration_date: int,  # unix timestamp
) -> dict[str, Any]:
    preview = self._client.invoices.create_preview(
        params={
            "subscription": subscription_id,
            "subscription_details": {
                "items": [
                    {
                        "id": self._get_subscription_item_id(subscription_id),
                        "price": new_price_id,
                    }
                ],
                "proration_behavior": "create_prorations",
                "proration_date": proration_date,
            },
        }
    )
    return {
        "amount_due_now": preview.amount_due,
        "next_invoice_total": preview.amount_due,  # same field for immediate invoice
        "proration_date": proration_date,
        "currency": preview.currency,
    }
```

### Usage Summary Retrieval — StripeAdapter Implementation

```python
# Source: https://docs.stripe.com/api/billing/meter-event-summary/list

def get_usage_summary(
    self,
    meter_id: str,
    customer_id: str,
    start_time: int,  # unix timestamp, aligned to minute boundary
    end_time: int,    # unix timestamp, aligned to minute boundary
) -> dict[str, Any]:
    summaries = self._client.billing.meters.list_event_summaries(
        meter_id,
        params={
            "customer": customer_id,
            "start_time": start_time,
            "end_time": end_time,
        },
    )
    total = sum(s.aggregated_value for s in summaries.data)
    return {
        "meter_id": meter_id,
        "customer_id": customer_id,
        "aggregated_value": total,
        "start_time": start_time,
        "end_time": end_time,
        "summaries": [
            {"aggregated_value": s.aggregated_value, "start_time": s.start_time, "end_time": s.end_time}
            for s in summaries.data
        ],
    }
```

### URL Registration

```python
# config/urls.py — inside # BILLING_START / # BILLING_END block
# Source: existing codebase pattern (line 182-185 in config/urls.py)

from apps.billing.webhooks import stripe_webhook_view

# BILLING_START
path("api/v1/billing/webhooks/stripe/", stripe_webhook_view, name="stripe-webhook"),
# BILLING_END
```

### Celery Task Testing (Eager Mode)

```python
# tests/billing/test_tasks.py
# Use Django's @override_settings to run tasks eagerly in tests

from unittest.mock import patch
import pytest
from django.test import override_settings

@pytest.mark.django_db
@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
def test_webhook_task_idempotency(subscription):
    event = {"id": "evt_test_123", "type": "customer.subscription.updated", "data": {"object": {...}}}
    from apps.billing.tasks import process_stripe_webhook
    process_stripe_webhook(event)  # first call
    process_stripe_webhook(event)  # second call — must not double-process
    assert ProcessedWebhookEvent.objects.filter(event_id="evt_test_123").count() == 1
```

---

## State of the Art

| Old Approach                                       | Current Approach                                                     | When Changed                                        | Impact                                                           |
| -------------------------------------------------- | -------------------------------------------------------------------- | --------------------------------------------------- | ---------------------------------------------------------------- |
| `stripe.Webhook.construct_event()` (global client) | `stripe_sdk.StripeClient.construct_event()`                          | stripe-python v14 (2024)                            | StripeClient pattern already established in Phase 9              |
| Stripe legacy usage recording (`UsageRecord`)      | Stripe Meter Events v2 API (`client.v2.billing.meter_events.create`) | 2024-09-30 Stripe API changelog                     | Already implemented in `StripeAdapter.record_usage()` in Phase 9 |
| `dj-stripe` for webhook handling                   | Custom `ProcessedWebhookEvent` table + Celery                        | Project decision (out of scope per REQUIREMENTS.md) | Keeps adapter pattern clean; no model coupling                   |
| `subscription.retrieve_summary` (older pattern)    | `billing.meters.list_event_summaries(meter_id, params={...})`        | Stripe Python SDK v14+                              | New method signature confirmed in official API docs              |

**Deprecated/outdated:**

- `stripe.UsageRecord.create()`: Legacy usage recording API — replaced by Meter Events. The `StripeAdapter.record_usage()` from Phase 9 already uses the v2 API correctly.
- `stripe.Invoice.upcoming()`: Deprecated in favor of `invoices.create_preview()` for proration previews.

---

## Open Questions

1. **`preview_proration` subscription item ID lookup**
   - What we know: `modify_subscription()` in `StripeAdapter` already retrieves the subscription and extracts `subscription.items.data[0].id`
   - What's unclear: `preview_proration` needs the same item ID — should it re-fetch the subscription, or should the caller pass `subscription_item_id` as a parameter?
   - Recommendation: Add a private `_get_subscription_item_id(subscription_id)` helper on `StripeAdapter` reused by both methods. This avoids duplicate fetch logic and keeps the ABC signature clean.

2. **`get_usage_summary` meter_id source**
   - What we know: Stripe meter IDs are separate from subscription/price IDs and must be configured
   - What's unclear: Where does `meter_id` come from in service calls — settings? `PlanProviderMapping`? Direct parameter?
   - Recommendation: Add `STRIPE_METER_ID` to settings (or a per-meter mapping) and pass it through `BillingService.get_usage_summary(user, meter_event_name)` → resolve to meter_id internally. This is a Claude's Discretion area.

3. **`reactivate_subscription` — Stripe API path**
   - What we know: Reactivation (removing `cancel_at_period_end=True`) is done via `subscriptions.update(subscription_id, params={"cancel_at_period_end": False})`
   - What's unclear: Is there a case where the subscription has already been fully canceled (status=`canceled`) before period end? In that case, a new checkout is required.
   - Recommendation: In `BillingService.reactivate_subscription()`, check `cancel_at_period_end` is `True` AND status is not `CANCELED` before calling `modify_subscription`. Raise `ServiceError` with a clear message if the subscription is already canceled.

---

## Validation Architecture

### Test Framework

| Property           | Value                                                   |
| ------------------ | ------------------------------------------------------- |
| Framework          | pytest + pytest-django (existing)                       |
| Config file        | `apps/api/pyproject.toml` (`[tool.pytest.ini_options]`) |
| Quick run command  | `cd apps/api && python -m pytest tests/billing/ -x -q`  |
| Full suite command | `cd apps/api && python -m pytest tests/ -x -q`          |

### Phase Requirements → Test Map

| Req ID   | Behavior                                                              | Test Type    | Automated Command                                                              | File Exists? |
| -------- | --------------------------------------------------------------------- | ------------ | ------------------------------------------------------------------------------ | ------------ |
| HOOK-01  | Webhook view uses `request.body` + `@csrf_exempt`; NOT via Ninja      | unit         | `pytest tests/billing/test_webhooks.py::test_webhook_view_structure -x`        | ❌ Wave 0    |
| HOOK-02  | Valid HMAC → HTTP 200 immediately; dispatch to Celery                 | integration  | `pytest tests/billing/test_webhooks.py::test_valid_signature_returns_200 -x`   | ❌ Wave 0    |
| HOOK-02  | Invalid HMAC → HTTP 400; no task dispatched                           | integration  | `pytest tests/billing/test_webhooks.py::test_invalid_signature_returns_400 -x` | ❌ Wave 0    |
| HOOK-02  | Celery dispatch failure → HTTP 500                                    | unit         | `pytest tests/billing/test_webhooks.py::test_dispatch_failure_returns_500 -x`  | ❌ Wave 0    |
| HOOK-03  | Same event_id twice → second call skipped                             | unit (eager) | `pytest tests/billing/test_tasks.py::test_idempotency_guard -x`                | ❌ Wave 0    |
| HOOK-04  | All 6 Tier-1 events update Subscription/Payment correctly             | unit (eager) | `pytest tests/billing/test_tasks.py -x`                                        | ❌ Wave 0    |
| SUB-01   | `BillingService.create_checkout_session()` returns URL                | unit (stub)  | `pytest tests/billing/test_services.py::test_create_checkout_session -x`       | ❌ Wave 0    |
| SUB-02   | `BillingService.upgrade_subscription()` calls `modify_subscription`   | unit (stub)  | `pytest tests/billing/test_services.py::test_upgrade_subscription -x`          | ❌ Wave 0    |
| SUB-03   | `BillingService.downgrade_subscription()` calls `modify_subscription` | unit (stub)  | `pytest tests/billing/test_services.py::test_downgrade_subscription -x`        | ❌ Wave 0    |
| SUB-04   | `cancel_subscription()` sets `cancel_at_period_end=True`              | unit (stub)  | `pytest tests/billing/test_services.py::test_cancel_subscription -x`           | ❌ Wave 0    |
| SUB-05   | `reactivate_subscription()` removes `cancel_at_period_end`            | unit (stub)  | `pytest tests/billing/test_services.py::test_reactivate_subscription -x`       | ❌ Wave 0    |
| PAY-01   | `create_one_time_payment()` calls checkout with mode="payment"        | unit (stub)  | `pytest tests/billing/test_services.py::test_one_time_payment -x`              | ❌ Wave 0    |
| USAGE-01 | `record_usage()` delegates to adapter                                 | unit (stub)  | `pytest tests/billing/test_services.py::test_record_usage -x`                  | ❌ Wave 0    |
| USAGE-02 | `get_usage_summary()` delegates to adapter                            | unit (stub)  | `pytest tests/billing/test_services.py::test_get_usage_summary -x`             | ❌ Wave 0    |
| CUST-03  | ACTIVE/TRIALING + cancel_at_period_end=True → pass gate               | unit         | `pytest tests/billing/test_decorators.py::test_active_user_passes -x`          | ❌ Wave 0    |
| CUST-03  | PAST_DUE/CANCELED/no subscription → HTTP 403                          | unit         | `pytest tests/billing/test_decorators.py::test_inactive_user_blocked -x`       | ❌ Wave 0    |

### Sampling Rate

- **Per task commit:** `cd apps/api && python -m pytest tests/billing/ -x -q`
- **Per wave merge:** `cd apps/api && python -m pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/billing/test_services.py` — covers SUB-01 through SUB-05, PAY-01, USAGE-01, USAGE-02 (all BillingService unit tests)
- [ ] `tests/billing/test_webhooks.py` — covers HOOK-01, HOOK-02
- [ ] `tests/billing/test_tasks.py` — covers HOOK-03, HOOK-04
- [ ] `tests/billing/test_decorators.py` — covers CUST-03
- [ ] Update `tests/billing/conftest.py` — add `StubAdapter`, `billing_service`, `subscription`, `payment` fixtures
- [ ] Update `tests/billing/test_adapters.py` — add tests verifying `preview_proration` and `get_usage_summary` exist as abstract methods on `PaymentAdapter`

---

## Sources

### Primary (HIGH confidence)

- Official Stripe docs: [Stripe webhooks signature verification](https://docs.stripe.com/webhooks/signature) — HMAC verification, raw body requirement, timing attack prevention
- Official Stripe docs: [Using webhooks with subscriptions](https://docs.stripe.com/billing/subscriptions/webhooks) — event order, field extraction, subscription lifecycle
- Official Stripe docs: [Invoice preview API](https://docs.stripe.com/api/invoices/create_preview) — `subscription_details.proration_date`, `amount_due`, response shape
- Official Stripe docs: [Meter Event Summary list](https://docs.stripe.com/api/billing/meter-event-summary/list) — `list_event_summaries(meter_id, params={...})` Python SDK call
- Official Celery docs: [Task retries](https://docs.celeryq.dev/en/stable/userguide/tasks.html) — `autoretry_for`, `retry_backoff`, `retry_jitter`, `max_retries`
- Codebase: `apps/api/apps/billing/adapters.py` — existing `PaymentAdapter` ABC and `StripeAdapter`
- Codebase: `apps/api/apps/billing/models.py` — existing models including `ProcessedWebhookEvent` with `unique_together`
- Codebase: `apps/api/config/celery.py` — existing Celery instance with autodiscover
- Codebase: `apps/api/config/urls.py` — `# BILLING_START / # BILLING_END` markers at lines 182-185
- Codebase: `apps/api/config/settings/base.py` — `STRIPE_WEBHOOK_SECRET`, `BILLING_ADAPTER`, `CELERY_RESULT_BACKEND="django-db"`

### Secondary (MEDIUM confidence)

- [TestDriven.io: Retrying Failed Celery Tasks](https://testdriven.io/blog/retrying-failed-celery-tasks/) — Verified `retry_backoff` and jitter behavior against Celery docs
- [Adam Johnson: How to Build a Webhook Receiver in Django](https://adamj.eu/tech/2021/05/09/how-to-build-a-webhook-receiver-in-django/) — `@csrf_exempt` + `@require_POST` + `request.body` pattern; verified against Stripe official docs

### Tertiary (LOW confidence)

- None — all key claims verified against official sources.

---

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — all libraries already installed and wired in Phase 9
- Architecture patterns: HIGH — verified against existing codebase conventions and Stripe official docs
- Stripe event field extraction: MEDIUM — documented from official Stripe webhook docs; exact field names should be verified against a live Stripe test event during implementation
- Celery retry configuration: HIGH — verified against Celery 5.x official docs
- `get_usage_summary` SDK call shape: MEDIUM — verified field names from official API reference; exact StripeClient v14 method path (`client.billing.meters.list_event_summaries`) should be confirmed during implementation with `stripe-python` SDK source

**Research date:** 2026-03-08
**Valid until:** 2026-04-08 (Stripe API stable; Celery 5.x stable)
