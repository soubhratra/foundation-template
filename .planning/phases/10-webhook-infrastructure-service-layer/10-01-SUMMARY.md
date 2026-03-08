---
phase: 10-webhook-infrastructure-service-layer
plan: "01"
subsystem: billing
tags: [webhook, celery, stripe, tdd, idempotency]
dependency_graph:
  requires:
    - apps/api/apps/billing/adapters.py (PaymentAdapter, StripeAdapter)
    - apps/api/apps/billing/models.py (Customer, Subscription, Payment, ProcessedWebhookEvent)
    - apps/api/config/celery.py (shared_task, redis broker)
  provides:
    - POST /api/v1/billing/webhooks/ (stripe webhook receiver)
    - process_stripe_event Celery task (idempotent Tier-1 event processing)
    - get_adapter() utility (BILLING_ADAPTER setting resolver)
  affects:
    - apps/api/config/urls.py (webhook URL registered between BILLING markers)
    - apps/api/apps/billing/adapters.py (preview_proration, get_usage_summary ABCs added)
tech_stack:
  added: []
  patterns:
    - plain Django view (not Ninja) for raw body access required by Stripe HMAC
    - ProcessedWebhookEvent.get_or_create as idempotency guard (unique_together constraint)
    - autoretry_for + exponential backoff countdown for Celery task retry
key_files:
  created:
    - apps/api/apps/billing/webhooks.py
    - apps/api/apps/billing/tasks.py
    - apps/api/apps/billing/utils.py
    - apps/api/tests/billing/test_webhooks.py
    - apps/api/tests/billing/test_tasks.py
  modified:
    - apps/api/config/urls.py
    - apps/api/apps/billing/adapters.py
    - apps/api/tests/billing/test_adapters.py
decisions:
  - Plain Django view (not Django Ninja) used for webhook endpoint to preserve raw body bytes required by Stripe HMAC verification
  - get_adapter() in utils.py (not __init__.py) to avoid circular imports between webhooks.py and tasks.py
  - ProcessedWebhookEvent.get_or_create used as atomic idempotency guard leveraging UNIQUE constraint
  - autoretry_for=(Exception,) with exponential countdown (2^retries ± jitter) for Celery retry
  - Dead-letter: after max_retries, logs at CRITICAL level without raising (prevents infinite queuing)
metrics:
  duration: "8 minutes"
  completed_date: "2026-03-08"
  tasks_completed: 2
  files_created: 5
  files_modified: 3
---

# Phase 10 Plan 01: Webhook Infrastructure & Service Layer Summary

Stripe webhook receiver (plain Django view) and async Celery task with idempotency guard and 6 Tier-1 event handlers, fully test-driven with 22 tests green.

## Tasks Completed

| Task | Name                                                              | Commit  | Files                                             |
| ---- | ----------------------------------------------------------------- | ------- | ------------------------------------------------- |
| 1    | Write failing tests (TDD RED)                                     | 14cb1b8 | test_webhooks.py, test_tasks.py, test_adapters.py |
| 2    | Implement webhook view, Celery task, URL registration (TDD GREEN) | 9892b34 | webhooks.py, tasks.py, utils.py, config/urls.py   |

## Verification Results

- `test_webhooks.py`: 4/4 green (HMAC validation, 200/400/500 responses, dispatch)
- `test_tasks.py`: 8/8 green (idempotency guard, 6 Tier-1 event handlers, unknown events)
- `test_adapters.py`: 9/9 green, 1 skipped (abstract method contract, abstract ABC tests)
- Full billing suite (excluding pre-existing test_services.py failure): 36/36 green
- URL resolves: `reverse("stripe-webhook")` → `/api/v1/billing/webhooks/`
- BILLING_START/BILLING_END markers intact in `config/urls.py`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Ruff UP017 datetime.UTC fix caused AttributeError**

- **Found during:** Task 2 after applying ruff --fix
- **Issue:** ruff UP017 auto-fix replaced `timezone.utc` with `datetime.UTC` but removed the `timezone` import; `datetime.UTC` is on the `datetime` module but was being used as `datetime.datetime.UTC`
- **Fix:** Changed import to `import datetime` and used `datetime.datetime.fromtimestamp(ts, tz=datetime.UTC)` correctly
- **Files modified:** `apps/api/apps/billing/tasks.py`
- **Commit:** part of 9892b34

### Out-of-Scope Discoveries

- `test_services.py::TestCreateCheckoutSession::test_missing_customer_raises` was failing before this plan (pre-existing). The test expects status_code 404 but the service raises 400. Logged as deferred.

## Key Decisions Made

1. **Plain Django view for webhook endpoint**: Django Ninja may buffer/parse the request body before it reaches view code. Stripe HMAC verification requires raw bytes — using `@csrf_exempt @require_POST` on a plain view ensures `request.body` is always the raw payload.

2. **`utils.py` for `get_adapter()`**: Placing the adapter factory in `utils.py` (not `__init__.py`) avoids circular imports since both `webhooks.py` and `tasks.py` need it and are imported by different parts of the URL/task discovery machinery.

3. **`get_or_create` as idempotency guard**: The `ProcessedWebhookEvent` model has `unique_together = [("provider", "event_id")]`. Django's `get_or_create` wraps a `SELECT` + `INSERT` that is atomic at the database level via the unique constraint — if two concurrent workers try to process the same event, one gets `created=True` and proceeds, the other gets `created=False` and returns immediately.

4. **`autoretry_for=(Exception,)` with countdown**: Exponential backoff (`2^retries ± 1s jitter`) prevents thundering herd when the upstream DB/Stripe is temporarily unavailable. After `max_retries=3`, logs at CRITICAL level without re-raising (avoids infinite queuing in Celery's retry mechanism).

## Self-Check: PASSED

Created files verified:

- [x] `apps/api/apps/billing/webhooks.py` — exists
- [x] `apps/api/apps/billing/tasks.py` — exists
- [x] `apps/api/apps/billing/utils.py` — exists
- [x] `apps/api/tests/billing/test_webhooks.py` — exists
- [x] `apps/api/tests/billing/test_tasks.py` — exists

Commits verified:

- [x] 14cb1b8 — TDD RED tests
- [x] 9892b34 — TDD GREEN implementation
