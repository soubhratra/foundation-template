---
phase: 27-outbound-webhooks
verified: 2026-03-13T12:10:00Z
status: passed
score: 7/7 must-haves verified
re_verification: false
---

# Phase 27: Outbound Webhooks Verification Report

**Phase Goal:** Implement outbound webhooks — org admins can register HTTPS endpoints, the system delivers signed event payloads via Celery, retries on failure, and automatically disables persistently failing endpoints.
**Verified:** 2026-03-13T12:10:00Z
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| #   | Truth                                                                | Status   | Evidence                                                                                                                                                                              |
| --- | -------------------------------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Org admin can register HTTPS endpoints via API                       | VERIFIED | `POST /org/{slug}/webhooks/endpoints` in controllers.py; HTTPS-only enforced in `EndpointIn.url_must_be_https` validator; HTTP URL returns 422                                        |
| 2   | Event payloads are delivered via Celery with HMAC-SHA256 signing     | VERIFIED | `deliver_webhook` task in tasks.py; `_sign_payload()` uses `endpoint.signing_key`; `X-Webhook-Signature`, `X-Webhook-Id`, `X-Webhook-Timestamp` headers sent                          |
| 3   | Failed deliveries are retried with exponential backoff up to 7 times | VERIFIED | `@shared_task(max_retries=7, autoretry_for=(Exception,), retry_backoff=True, retry_backoff_max=600)` in tasks.py                                                                      |
| 4   | System automatically disables persistently failing endpoints         | VERIFIED | `_handle_terminal_failure` in tasks.py: sets `is_active=False` when `consecutive_failures >= WEBHOOK_CIRCUIT_BREAKER_THRESHOLD` (5)                                                   |
| 5   | Org admin receives email on auto-disable                             | VERIFIED | `_handle_terminal_failure` calls `send_email(template_name="webhooks/endpoint_disabled")` for every OWNER/ADMIN membership                                                            |
| 6   | Paginated delivery history is accessible via API                     | VERIFIED | `GET /org/{slug}/webhooks/endpoints/{id}/deliveries` with manual pagination (`page`/`page_size` query params), returns `{"items": [...], "count": N}` with `attempt_count` annotation |
| 7   | Manually retrying a failed delivery enqueues a new task              | VERIFIED | `POST /org/{slug}/webhooks/deliveries/{id}/retry` calls `deliver_webhook.delay(str(delivery.id))` and returns 202                                                                     |

**Score:** 7/7 truths verified

---

## Required Artifacts

### Plan 01 Artifacts (Test Suite / RED Stubs)

| Artifact                                      | Provides                                                         | Status   | Notes                                                                                               |
| --------------------------------------------- | ---------------------------------------------------------------- | -------- | --------------------------------------------------------------------------------------------------- |
| `apps/api/tests/webhooks/__init__.py`         | Module-level import forces RED at collection                     | VERIFIED | Imports `WebhookEndpoint`, `WebhookDelivery`, `WebhookDeliveryAttempt` from `apps.webhooks.models`  |
| `apps/api/tests/webhooks/conftest.py`         | `org_owner`, `org`, `org_admin`, `endpoint`, `delivery` fixtures | VERIFIED | All 5 fixtures present; `endpoint` uses `generate_secret()`                                         |
| `apps/api/tests/webhooks/test_models.py`      | Model field and cascade delete tests                             | VERIFIED | 4 substantive tests; all assertions against real model fields                                       |
| `apps/api/tests/webhooks/test_utils.py`       | `fire_webhook_event()` validation and dispatch tests             | VERIFIED | 6 tests covering unknown event, HTTPS validation, enqueue, rollback, inactive/unsubscribed endpoint |
| `apps/api/tests/webhooks/test_tasks.py`       | Delivery, retry, HMAC, circuit breaker, cleanup tests            | VERIFIED | 10 tests; HMAC verification test uses `hmac.compare_digest`                                         |
| `apps/api/tests/webhooks/test_controllers.py` | All HTTP endpoint tests (12 tests)                               | VERIFIED | Covers create/list/update/delete/rotate-secret/deliveries/retry/reenable/auth                       |
| `apps/api/tests/webhooks/test_checks.py`      | `manage.py check` WEBHOOK_EVENTS system check tests              | VERIFIED | 3 tests; checks `webhooks.W002`, `webhooks.W004` IDs                                                |

### Plan 02 Artifacts (Models + Utils + Settings)

| Artifact                                            | Provides                                                       | Status   | Notes                                                                                                                                                                                 |
| --------------------------------------------------- | -------------------------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `apps/api/apps/webhooks/models.py`                  | `WebhookEndpoint`, `WebhookDelivery`, `WebhookDeliveryAttempt` | VERIFIED | All 3 models with correct fields; `generate_secret()` returns `(raw, raw, sha256_hash)`; `clean()` enforces HTTPS; `WebhookDeliveryAttempt.save()` truncates `response_body` at 10 KB |
| `apps/api/apps/webhooks/utils.py`                   | `fire_webhook_event()` dispatch interface                      | VERIFIED | Validates against `WEBHOOK_EVENTS`; enqueues via `transaction.on_commit()`                                                                                                            |
| `apps/api/apps/webhooks/checks.py`                  | `WEBHOOK_EVENTS` Django system check                           | VERIFIED | Registers `@register()` check; validates `description` and `example_payload` keys; IDs `W001`-`W005`                                                                                  |
| `apps/api/apps/webhooks/migrations/0001_initial.py` | Initial migration for all 3 models                             | VERIFIED | Contains `WebhookEndpoint`, `WebhookDelivery`, `WebhookDeliveryAttempt`                                                                                                               |
| `apps/api/config/settings/base.py`                  | `apps.webhooks` in INSTALLED_APPS; `WEBHOOK_EVENTS` setting    | VERIFIED | `apps.webhooks` inside B2B_START/B2B_END; `WEBHOOK_EVENTS` dict with 3 events; `WEBHOOK_DELIVERY_RETENTION_DAYS=30`; `WEBHOOK_CIRCUIT_BREAKER_THRESHOLD=5`                            |

### Plan 03 Artifacts (Celery Tasks)

| Artifact                                                                      | Provides                                               | Status   | Notes                                                                                                                                                            |
| ----------------------------------------------------------------------------- | ------------------------------------------------------ | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `apps/api/apps/webhooks/tasks.py`                                             | `deliver_webhook` and `webhook_delivery_cleanup` tasks | VERIFIED | `deliver_webhook` with `max_retries=7`, HMAC signing via `endpoint.signing_key`, attempt logging, circuit breaker; `webhook_delivery_cleanup` with beat schedule |
| `apps/api/apps/notifications/templates/email/webhooks/endpoint_disabled.html` | HTML circuit breaker notification email                | VERIFIED | Full HTML template at `templates/email/webhooks/` — correct path per `send_email_task` which prepends `email/` to template_name                                  |
| `apps/api/apps/notifications/templates/webhooks/endpoint_disabled.txt`        | Plain text circuit breaker email                       | VERIFIED | 8-line plain text template at `templates/webhooks/`                                                                                                              |

**Note on template paths:** Plan 03 specified the HTML template at `apps/notifications/templates/webhooks/endpoint_disabled.html`. The implementation placed it at `apps/notifications/templates/email/webhooks/endpoint_disabled.html` to match the `send_email_task`'s `render_to_string(f"email/{template_name}", context)` resolution pattern. This is correct — the functional path is `email/webhooks/endpoint_disabled.html`. The `templates/webhooks/` path holds only the `.txt` file (an informational artifact per the SUMMARY). Both are substantive and the HTML template is resolved correctly at runtime.

### Plan 04 Artifacts (API Controllers)

| Artifact                                | Provides                                                  | Status   | Notes                                                                                                                                                                                  |
| --------------------------------------- | --------------------------------------------------------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `apps/api/apps/webhooks/schemas.py`     | All request/response schema classes                       | VERIFIED | `EndpointIn` (HTTPS validator), `EndpointOut` (no secret), `EndpointCreateOut` (has `secret`), `EndpointUpdateIn`, `RotateSecretOut`, `AttemptOut`, `DeliveryOut`, `DeliveryDetailOut` |
| `apps/api/apps/webhooks/controllers.py` | `WebhookEndpointController` + `WebhookDeliveryController` | VERIFIED | 8 routes; `IsOrgAdmin` on all write endpoints; manual pagination (deviation from `@paginate` per SUMMARY); `deliver_webhook.delay()` in retry endpoint                                 |

---

## Key Link Verification

| From               | To                                                                   | Via                                                                                                                          | Status | Evidence                                                                                                  |
| ------------------ | -------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | ------ | --------------------------------------------------------------------------------------------------------- |
| `utils.py`         | `apps.webhooks.tasks.deliver_webhook`                                | `transaction.on_commit` enqueue                                                                                              | WIRED  | Line 65: `transaction.on_commit(enqueue)` where `enqueue` calls `deliver_webhook.delay(did)`              |
| `settings/base.py` | `apps.webhooks`                                                      | `INSTALLED_APPS` B2B markers                                                                                                 | WIRED  | Line 121: `"apps.webhooks"` inside `# B2B_START` / `# B2B_END`                                            |
| `tasks.py`         | `apps.webhooks.models.WebhookDeliveryAttempt`                        | attempt creation on every HTTP call                                                                                          | WIRED  | Lines 112 and 138: `WebhookDeliveryAttempt.objects.create()` in both success and error paths              |
| `tasks.py`         | `apps.notifications.utils.send_email`                                | circuit breaker auto-disable notification                                                                                    | WIRED  | Line 165 (import) and line 190 (call) in `_handle_terminal_failure`                                       |
| `tasks.py`         | `apps/notifications/templates/email/webhooks/endpoint_disabled.html` | `send_email(template_name="webhooks/endpoint_disabled")` resolved by `send_email_task` as `email/webhooks/endpoint_disabled` | WIRED  | Template exists at `templates/email/webhooks/endpoint_disabled.html`; `send_email_task` prepends `email/` |
| `controllers.py`   | `apps.webhooks.tasks.deliver_webhook`                                | manual retry enqueue                                                                                                         | WIRED  | Line 269: `deliver_webhook.delay(str(delivery.id))`                                                       |
| `controllers.py`   | `apps.orgs.permissions.IsOrgAdmin`                                   | permission class on write endpoints                                                                                          | WIRED  | Lines 55, 98, 138, 154: `permissions=[IsAuthenticated, IsOrgMember, IsOrgAdmin]`                          |

---

## Requirements Coverage

| Requirement | Source Plans   | Description                                                                                                                                      | Status    | Evidence                                                                                                                                                                 |
| ----------- | -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| HOOK-01     | 01, 02, 03, 04 | Org admin can register webhook endpoints; deliveries sent via Celery with exponential backoff (7 retries), HMAC-SHA256 signed, payload versioned | SATISFIED | `WebhookEndpoint` model + `fire_webhook_event()` + `deliver_webhook` task + controllers CRUD all verified                                                                |
| HOOK-02     | 01, 04         | User can view paginated delivery history for a webhook endpoint                                                                                  | SATISFIED | `GET /org/{slug}/webhooks/endpoints/{id}/deliveries` returns `{"items": [...], "count": N}` with `attempt_count` per delivery                                            |
| HOOK-03     | 01, 04         | User can manually retry a failed delivery                                                                                                        | SATISFIED | `POST /org/{slug}/webhooks/deliveries/{id}/retry` enqueues `deliver_webhook.delay()` and returns 202                                                                     |
| HOOK-04     | 01, 03, 04     | System auto-disables endpoint after N consecutive failures and notifies org admin by email; re-enable resets counter                             | SATISFIED | `_handle_terminal_failure` sets `is_active=False` at threshold; `send_email()` called for all admins/owners; PATCH with `is_active:true` resets `consecutive_failures=0` |

All 4 requirements fully satisfied. No orphaned requirements.

---

## Anti-Patterns Found

None. No `TODO`, `FIXME`, `PLACEHOLDER`, empty return bodies, or console.log-only implementations found in any of the 8 implementation files (`models.py`, `utils.py`, `tasks.py`, `checks.py`, `controllers.py`, `schemas.py`, `apps.py`, `migrations/0001_initial.py`).

---

## Notable Deviations from Plan (Confirmed Correct)

1. **`@paginate` decorator replaced with manual pagination** — The `@paginate(PageNumberPagination)` decorator causes `TypeError: got multiple values for argument 'request'` with ninja_extra controllers. Manual `page`/`page_size` query params returning `{"items": [...], "count": N}` preserves the identical response shape. Behavioral contract unchanged.

2. **`from __future__ import annotations` removed from schemas.py and controllers.py** — Deferred type evaluation causes `PydanticUserError: QueryParams is not fully defined` in ninja's internal model builder. Removed; Python 3.12 `str | None` syntax used directly. No semantic change.

3. **`select_related("endpoint")` (not `select_related("endpoint__org")`)** — The `org` relation is only accessed in the circuit breaker path (`_handle_terminal_failure`). Eager-loading it on every delivery call would incur unnecessary queries on the success path. Lazy access in the exception path is correct.

4. **HTML template path** — Placed at `templates/email/webhooks/endpoint_disabled.html` (not `templates/webhooks/`). Matches `send_email_task`'s `render_to_string(f"email/{template_name}", ...)` resolution. Functional and correct.

---

## Human Verification Required

### 1. End-to-end delivery flow

**Test:** Register a webhook endpoint pointing to a test receiver (e.g., webhook.site), fire `user.created` via Django shell with `fire_webhook_event()`, and inspect the received HTTP request.
**Expected:** Request arrives at the receiver with `X-Webhook-Signature`, `X-Webhook-Id`, `X-Webhook-Timestamp` headers; HMAC-SHA256 signature is verifiable using the secret returned at registration; body contains `{"webhook_version": "v1", "event_type": "user.created", ...}`.
**Why human:** Requires a live Celery worker, real network request, and external receiver — cannot verify programmatically.

### 2. Circuit breaker email formatting

**Test:** Trigger circuit breaker by exhausting 5 deliveries, then inspect the received email.
**Expected:** Email contains endpoint URL, org name, last failure reason; HTML renders correctly in an email client; subject line reads "Your webhook endpoint has been disabled".
**Why human:** Visual rendering and email client compatibility cannot be verified programmatically.

### 3. Re-enable flow from dashboard

**Test:** After circuit breaker disables an endpoint, PATCH `is_active: true`, then fire another event.
**Expected:** Delivery succeeds; `consecutive_failures` is 0 in DB; subsequent success does not trigger another disable email.
**Why human:** Requires confirming end-to-end state after re-enable with a live Celery worker.

---

## Gaps Summary

No gaps. All 7 observable truths are verified, all 10 artifacts exist and are substantive, all 7 key links are wired, all 4 requirements (HOOK-01 through HOOK-04) are satisfied, and no anti-patterns were found in the implementation.

The phase goal is fully achieved: org admins can register HTTPS endpoints, the system delivers signed event payloads via Celery with exponential backoff (max 7 retries), automatically disables endpoints after 5 consecutive failures, notifies admins by email on auto-disable, and provides paginated delivery history and manual retry via REST API.

---

_Verified: 2026-03-13T12:10:00Z_
_Verifier: Claude (gsd-verifier)_
