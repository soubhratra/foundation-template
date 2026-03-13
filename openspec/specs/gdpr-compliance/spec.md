## ADDED Requirements

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
