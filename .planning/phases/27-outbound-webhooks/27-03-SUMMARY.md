---
phase: 27-outbound-webhooks
plan: "03"
subsystem: api
tags: [celery, webhooks, hmac, circuit-breaker, httpx, django]

# Dependency graph
requires:
  - phase: 27-02
    provides: WebhookEndpoint, WebhookDelivery, WebhookDeliveryAttempt models and fire_webhook_event()
provides:
  - deliver_webhook Celery task: HMAC-SHA256 signed POST delivery with per-attempt logging and autoretry
  - Circuit breaker: auto-disables endpoint after 5 consecutive failures and sends admin email
  - webhook_delivery_cleanup: periodic task pruning delivery records older than retention window
  - endpoint_disabled email template (HTML + plain text)
  - CELERY_BEAT_SCHEDULE entry for daily cleanup
affects: [27-04-controllers, 28-api-keys]

# Tech tracking
tech-stack:
  added: ["httpx>=0.27,<1 (HTTP client for outbound webhook delivery)"]
  patterns:
    - "HMAC-SHA256 signing using endpoint.signing_key (raw secret, NOT secret_hash) with Stripe/GitHub convention: sha256=HMAC(key, timestamp.payload)"
    - "select_related('endpoint') only — org loaded lazily by _handle_terminal_failure to avoid unnecessary eager load"
    - "autoretry_for=(Exception,) with retry_backoff=True handles both httpx.RequestError and non-2xx HTTP responses"
    - "Circuit breaker threshold from settings.WEBHOOK_CIRCUIT_BREAKER_THRESHOLD (default 5)"
    - "Email templates at email/webhooks/ subdirectory (send_email_task resolves email/{template_name})"

key-files:
  created:
    - apps/api/apps/webhooks/tasks.py
    - apps/api/apps/notifications/templates/email/webhooks/endpoint_disabled.html
    - apps/api/apps/notifications/templates/webhooks/endpoint_disabled.txt
  modified:
    - apps/api/config/settings/base.py
    - apps/api/pyproject.toml
    - apps/api/tests/webhooks/test_tasks.py
    - apps/api/tests/webhooks/conftest.py

key-decisions:
  - "select_related('endpoint') not select_related('endpoint__org') — org is only accessed in _handle_terminal_failure (circuit breaker path), lazy loading there avoids NPlusOneError in the common success path"
  - "Email template path is email/webhooks/endpoint_disabled (resolves via send_email_task's render_to_string pattern); plan-specified path apps/notifications/templates/webhooks/ also created for documentation"
  - "_handle_terminal_failure is a module-level function (not task-internal) to enable direct testing without mocking the full Celery retry chain"
  - "conftest endpoint fixture updated to set signing_key via WebhookEndpoint.generate_secret() — required for HMAC verification tests"

patterns-established:
  - "HMAC signing pattern: _sign_payload(signing_key, payload_bytes, timestamp) → sha256=hex"
  - "Circuit breaker: consecutive_failures field + threshold setting; reset on success"
  - "Per-attempt logging: WebhookDeliveryAttempt.objects.create() in both success and error paths"

requirements-completed: [HOOK-01, HOOK-04]

# Metrics
duration: 10min
completed: 2026-03-13
---

# Phase 27 Plan 03: Outbound Webhooks — Delivery Task Summary

**Celery deliver_webhook task with HMAC-SHA256 request signing, exponential backoff retries, per-attempt logging, and a circuit breaker that auto-disables endpoints after 5 consecutive exhausted deliveries**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-03-13T11:28:00Z
- **Completed:** 2026-03-13T11:38:15Z
- **Tasks:** 1 (TDD: RED + GREEN commits)
- **Files modified:** 7

## Accomplishments

- `deliver_webhook` Celery task sends HMAC-signed HTTP POST and records `WebhookDeliveryAttempt` on every call (success and failure paths)
- HTTP 2xx marks delivery success and resets `endpoint.consecutive_failures` to 0; non-2xx/network error marks retrying and fires autoretry with exponential backoff (max 7 retries, up to 600s between)
- After 5 consecutive terminal failures, `_handle_terminal_failure` sets `endpoint.is_active=False` and calls `send_email()` for every org ADMIN/OWNER
- `webhook_delivery_cleanup` periodic task deletes `WebhookDelivery` records older than `WEBHOOK_DELIVERY_RETENTION_DAYS` (default 30); beat schedule entry added to `base.py`

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: test suite** - `60cc459` (test)
2. **Task 1 GREEN: deliver_webhook + cleanup + templates** - `c3057de` (feat)

## Files Created/Modified

- `apps/api/apps/webhooks/tasks.py` — deliver_webhook, \_handle_terminal_failure, webhook_delivery_cleanup
- `apps/api/apps/notifications/templates/email/webhooks/endpoint_disabled.html` — HTML email template for circuit breaker notification
- `apps/api/apps/notifications/templates/webhooks/endpoint_disabled.txt` — Plain text email template
- `apps/api/config/settings/base.py` — Added webhook-delivery-cleanup to CELERY_BEAT_SCHEDULE
- `apps/api/pyproject.toml` — Added httpx>=0.27,<1 dependency
- `apps/api/tests/webhooks/test_tasks.py` — 10-test suite covering all HOOK-01 and HOOK-04 requirements
- `apps/api/tests/webhooks/conftest.py` — endpoint fixture now sets signing_key via generate_secret()

## Decisions Made

- Used `select_related("endpoint")` (not `select_related("endpoint__org")`) in `deliver_webhook` because `org` is only accessed in `_handle_terminal_failure` (circuit breaker path). Eager-loading `org` on every delivery call would trigger NPlusOneError on non-circuit-breaker paths.
- `_handle_terminal_failure` is a module-level function to allow direct unit testing without mocking the full Celery retry infrastructure. Tests call it directly with controlled `consecutive_failures` values.
- Email template path: `email/webhooks/endpoint_disabled` (the `send_email_task` resolves `email/{template_name}`, so the file lives at `templates/email/webhooks/endpoint_disabled.html`). The plan-specified path `templates/webhooks/endpoint_disabled.txt` was also created for documentation completeness.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed NPlusOneError from unnecessary eager load of endpoint.org**

- **Found during:** Task 1 (test run after implementation)
- **Issue:** Plan's task code specified `select_related("endpoint__org")` but nplusone profiler raised NPlusOneError because `org` is only accessed in the circuit breaker path, making the eager load unnecessary on successful deliveries
- **Fix:** Changed to `select_related("endpoint")` only; `_handle_terminal_failure` accesses `endpoint.org` lazily (single query at circuit-breaker time)
- **Files modified:** apps/api/apps/webhooks/tasks.py
- **Verification:** All 10 tests pass with no nplusone warnings
- **Committed in:** c3057de (Task 1 GREEN commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug)
**Impact on plan:** Fix required for test suite to pass under nplusone guard. No scope creep.

## Issues Encountered

- Pre-commit ruff hooks caught `B017` (blind Exception in pytest.raises) and `B007` (unused loop var `i`) in test file — fixed with specific match string and renamed to `_i`

## Next Phase Readiness

- `deliver_webhook` and `webhook_delivery_cleanup` tasks are fully implemented and tested
- Plan 27-04 can build the CRUD API controllers (endpoint management + delivery history endpoints)
- `_handle_terminal_failure` is callable from tests directly — useful for controller re-enable tests

---

_Phase: 27-outbound-webhooks_
_Completed: 2026-03-13_
