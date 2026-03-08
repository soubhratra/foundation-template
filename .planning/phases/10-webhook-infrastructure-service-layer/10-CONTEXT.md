# Phase 10: Webhook Infrastructure + Service Layer - Context

**Gathered:** 2026-03-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Backend-only phase. Deliver the complete BillingService layer, Stripe webhook receiver (plain Django view, not Ninja), async Celery dispatch, Tier-1 event handlers, subscription lifecycle operations (create/upgrade/downgrade/cancel/reactivate), one-time payment, metered usage recording and retrieval, proration preview, and the `@require_active_subscription` access-gating decorator. No frontend work in this phase — that is Phase 11.

</domain>

<decisions>
## Implementation Decisions

### @require_active_subscription gating behavior

- Statuses that PASS the gate: `ACTIVE` and `TRIALING` only. All other statuses (PAST_DUE, UNPAID, INCOMPLETE, INCOMPLETE_EXPIRED, CANCELED) are blocked.
- Users with `cancel_at_period_end=True` PASS the gate — they paid through the current period. The webhook updates their status to CANCELED when the period actually ends.
- Users with no Customer or Subscription record FAIL the gate — treated as non-subscribers, not as "free tier."
- Failed gate returns **HTTP 403 Forbidden** using the existing `PermissionDenied` exception (already handled by `permission_denied_handler` in `config/urls.py`).

### Webhook failure handling

- Tier-1 event handlers run inside a Celery task dispatched after HMAC signature verification.
- On transient failure (DB error, etc.): **retry with exponential backoff, max 3 attempts**. The `ProcessedWebhookEvent` idempotency check (unique on `provider + event_id`) prevents double-processing if a retry fires after partial success.
- After 3 failures: task moves to Celery dead-letter queue; error logged at CRITICAL level.
- If Celery task dispatch itself fails (broker down): **return HTTP 500 to Stripe** so Stripe retries delivery per its own retry schedule. Do NOT swallow the dispatch failure and return 200.
- Unrecognized / unsupported event types: acknowledge silently (HTTP 200, logged at DEBUG level). No error, no retry.

### Proration preview

- `preview_proration` is added to the `PaymentAdapter` ABC — consistent with the adapter pattern. Future providers (Paddle, LemonSqueezy) must implement it.
- Return shape: `{ "amount_due_now": int, "next_invoice_total": int, "proration_date": int, "currency": str }` — enough for Phase 11 to render "You'll be charged $X today and $Y on next renewal."
- Amounts are in the smallest currency unit (cents) matching Stripe convention.

### BillingService structure

- Single `BillingService` class in `apps/billing/services.py`. All billing operations live here: customer management, subscriptions, one-time payments, usage, proration preview.
- Consistent with all other Django apps in this codebase (`accounts`, `ai`, etc. each have a single `services.py`).
- Service methods call `get_adapter()` (a helper that imports and instantiates the class at `settings.BILLING_ADAPTER`) — never importing `StripeAdapter` directly.

### Claude's Discretion

- Celery task naming and retry backoff timing (jitter, base delay)
- Exact `get_adapter()` helper placement (billing module `__init__` vs `utils.py`)
- How `StubAdapter` / `MockAdapter` is structured for tests (full Protocol implementation or selective override)
- Whether `@require_active_subscription` is a function decorator or a Django permission class (either works, decorator is more flexible for Ninja endpoints)

</decisions>

<specifics>
## Specific Ideas

No specific UI/UX requirements — this is a pure backend phase. Standard Django/Celery patterns apply.

</specifics>

<code_context>

## Existing Code Insights

### Reusable Assets

- `PaymentAdapter` ABC in `apps/billing/adapters.py`: method signatures for checkout, portal, cancel, modify, usage, invoices — `preview_proration` needs to be ADDED to the ABC and `StripeAdapter` in this phase
- `ProcessedWebhookEvent` model in `apps/billing/models.py`: already has `unique_together(provider, event_id)` — idempotency table is ready, no new model needed
- `Subscription`, `Customer`, `Payment`, `PlanProviderMapping` models: all exist with migrations applied
- `SubscriptionStatus` enum in `apps/billing/models.py`: ACTIVE, PAST_DUE, CANCELED, TRIALING, INCOMPLETE, INCOMPLETE_EXPIRED, UNPAID
- `ServiceError` exception in `apps/core/exceptions.py`: standard error envelope — use this for billing-specific errors
- Celery instance at `config/celery.py`: already configured with Redis broker, autodiscover tasks
- `# BILLING_START / # BILLING_END` comment markers in `config/urls.py`: webhook URL must be registered inside these markers (CLI scaffolder uses them for removal)

### Established Patterns

- Service layer: thin controllers delegate to services; services call adapter; no ORM in controllers
- Error handling: raise `ServiceError(code=..., message=..., status_code=...)` from service methods; global handler in `config/urls.py` formats the response
- Celery tasks: decorated with `@shared_task`, placed in `apps/billing/tasks.py`
- Settings access: `django.conf.settings` only — never `os.environ` directly

### Integration Points

- Webhook view registers at `/api/v1/billing/webhooks/` inside `# BILLING_START / # BILLING_END` block in `config/urls.py` as a plain `path()` (not via Ninja auto-discovery)
- `BillingService` will be consumed by the Ninja controller in Phase 11 (`apps/billing/controllers.py`)
- `@require_active_subscription` decorator will be applied to Phase 11 billing endpoints

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

_Phase: 10-webhook-infrastructure-service-layer_
_Context gathered: 2026-03-08_
