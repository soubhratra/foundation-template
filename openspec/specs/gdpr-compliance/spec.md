# GDPR Compliance

> Implements GDPR Articles 17 (right to erasure) and 20 (data portability) via async account deletion and JSON data export. Also covers cookie consent gating for PostHog analytics.

## Overview

GDPR compliance is built around two user-facing endpoints and one frontend consent pattern:

1. **Account deletion** (`DELETE /api/v1/account/`) — returns `202 Accepted` immediately and enqueues a Celery task that cancels Stripe, deletes the PostHog person, then deletes the Django user record. The cascade is designed so `user.delete()` always executes last, even if external service calls fail — guaranteeing Article 17 compliance regardless of third-party availability.
2. **Data export** (`GET /api/v1/account/export`) — returns a `Content-Disposition: attachment` JSON response with all user-owned data. No async needed; the data is fully local.
3. **Cookie consent** — PostHog `posthog.init()` is gated behind the user's consent banner. Initialising PostHog before consent violates GDPR/ePrivacy; gating the init (not just capture) is the safest approach.

The deletion implementation has a known tech debt item: `UserDeletionService.execute()` and `delete_user_account` Celery task both implement the cascade independently. See the Known Issues section.

## Requirements

### Requirement: Async Account Deletion Cascade (Article 17 Compliance)

The system SHALL implement account deletion as an async Celery task that cascades across all external services, with the user record deleted last.

#### Scenario: Deletion cascade executes in correct order

- **WHEN** `DELETE /api/v1/account/` is called with the correct password
- **THEN** the system SHALL return `202 Accepted` with `{"message": "Account deletion initiated."}`
- **AND** `delete_user_account.delay(user_id)` SHALL be enqueued
- **AND** the task SHALL execute the following steps in order:
  1. Cancel Stripe subscription
  2. Delete Stripe customer
  3. Delete PostHog person record
  4. Delete Django user record (cascades to all related data)

#### Scenario: Cascade continues if an external service step fails

- **WHEN** any step in the cascade raises an exception
- **THEN** the exception SHALL be caught and logged
- **AND** the cascade SHALL continue to the next step
- **AND** `user.delete()` SHALL always be called last (Article 17 guarantee)

#### Scenario: Wrong password rejected

- **WHEN** `DELETE /api/v1/account/` is called with an incorrect password
- **THEN** the system SHALL return `400 Bad Request`

#### Scenario: Unauthenticated deletion rejected

- **WHEN** `DELETE /api/v1/account/` is called without authentication
- **THEN** the system SHALL return `401 Unauthorized`

### Requirement: GDPR Data Export via JSON Attachment

The system SHALL provide a data export endpoint that returns all user-owned data as a downloadable JSON file.

#### Scenario: Authenticated export returns JSON attachment

- **WHEN** `GET /api/v1/account/export` is called by an authenticated user
- **THEN** the response SHALL have `Content-Disposition: attachment; filename="my-data.json"`
- **AND** the response body SHALL be a JSON object containing the user's profile, email addresses, subscription details, and billing history

#### Scenario: Export response structure

- **WHEN** the export is generated
- **THEN** the JSON SHALL include:
  - `user.id`, `user.email`, `user.first_name`, `user.last_name`, `user.date_joined`
  - `email_addresses[]` — all allauth EmailAddress records
  - `subscription.plan_id` — internal plan identifier (NOT Stripe subscription ID)
  - `billing_history[]` — invoice records

#### Scenario: Unauthenticated export rejected

- **WHEN** `GET /api/v1/account/export` is called without authentication
- **THEN** the system SHALL return `401 Unauthorized`

### Requirement: Export Service and Controller Separation

The export logic SHALL be split: an `ExportService` assembles the data dict, and `AccountController` wraps it with `Content-Disposition` header.

#### Scenario: ExportService returns a plain dict

- **WHEN** `ExportService(user).get_export_data()` is called
- **THEN** it SHALL return a plain Python dict (not an HttpResponse)
- **AND** the dict SHALL be JSON-serializable

### Requirement: Alias-Import Pattern for Celery Task Patchability

Celery tasks in `apps/accounts/tasks.py` that call external adapters SHALL import them using aliases so they can be patched in tests.

#### Scenario: PaymentAdapter and ObservabilityAdapter are patchable

- **WHEN** `get_adapter` and `get_observability_adapter` are imported in `tasks.py`
- **THEN** they SHALL be imported with aliases (`PaymentAdapter`, `ObservabilityAdapter`)
- **AND** tests SHALL patch at `apps.accounts.tasks.PaymentAdapter` (not `apps.billing.adapters.get_adapter`)

## Known Issues / Tech Debt

**1. Deletion cascade duplication** (Phase 21 — non-critical)

`UserDeletionService.execute()` in `apps/accounts/services.py` and `delete_user_account` Celery task in `apps/accounts/tasks.py` both implement the same 4-step cascade independently. The task does not delegate to the service.

_Recommendation:_ Have `delete_user_account` call `UserDeletionService.execute(user)` instead of reimplementing the cascade.

**2. Missing "Download my data" UI button** (Phase 21 — non-critical)

`GET /api/v1/account/export` is production-ready. No trigger button or link exists in `apps/web/app/(dashboard)/settings/settings-client.tsx`.

_Recommendation:_ Add a "Download my data" button in the DangerZone section of `/settings`. The button should `fetch('/api/v1/account/export')` and trigger a browser download via a Blob URL.

## Implementation Decisions

### Why `UserDeletionService` orchestrator (not direct `user.delete()`)

`user.delete()` via Django's ORM cascade deletes the database record and any `on_delete=CASCADE` foreign keys, but it does not know about external systems. Without an orchestrator:

- The Stripe subscription remains active (continued charges)
- The Stripe customer record persists (leaks PII to Stripe)
- The PostHog person record persists (leaks behavioural data)

All three violate GDPR Article 17 (right to erasure). `UserDeletionService.execute()` runs the four-step cascade — cancel subscription → delete Stripe customer → delete PostHog person → `user.delete()` — with per-step exception catching so that an external service failure does not prevent the Django record from being deleted.

**Key invariant:** `user.delete()` is always called last and always executes, regardless of whether earlier steps raised exceptions.

### Why async Celery task (not synchronous deletion in the HTTP handler)

Stripe and PostHog API calls can take hundreds of milliseconds or fail transiently. Performing them synchronously in `DELETE /api/v1/account/` would block the HTTP worker and risk timeouts on the client side. The handler immediately returns `202 Accepted` and enqueues `delete_user_account.delay(user_id)`. The user is signed out from the client's perspective before the cascade completes.

### Why `transaction.on_commit()` is NOT used for deletion (unlike email)

Email tasks must not fire if the triggering transaction rolls back. Account deletion is the opposite: we want the cascade to proceed even if the handler's transaction had some issue. The Celery task is enqueued directly (not in `on_commit()`) because the primary concern is external service cleanup, not database consistency.

### Why cookie consent gates PostHog init (not just PostHog event capture)

`posthog.init()` itself can set cookies and begin session replay. Initialising PostHog before consent is granted violates GDPR/ePrivacy Directive requirements in EU jurisdictions. `providers.tsx` conditionally calls `posthog.init()` only after the user accepts the cookie consent banner. The banner state is stored in `localStorage` so it persists across page loads.

**Alternative rejected:** Initialising PostHog but setting `opt_out_capturing_by_default: true` — this is a valid GDPR approach but requires careful configuration of every PostHog capture point. Conditional init is simpler and more bulletproof.

### Why the alias-import pattern for Celery task patchability

`tasks.py` uses:

```python
from apps.billing.adapters import get_adapter as PaymentAdapter
from apps.observability.adapters import get_observability_adapter as ObservabilityAdapter
```

This allows tests to patch at `apps.accounts.tasks.PaymentAdapter` (the local name in the task module's namespace), which is the correct patching target for `unittest.mock.patch`. Patching at the original import path would not intercept calls already bound in the task module.
