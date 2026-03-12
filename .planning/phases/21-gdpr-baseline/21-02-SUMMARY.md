---
phase: 21-gdpr-baseline
plan: "02"
subsystem: api
tags: [gdpr, django, celery, posthog, stripe, deletion, export]

requires:
  - phase: 21-gdpr-baseline plan 01
    provides: RED test stubs for AccountController, delete_user_account task, UserDeletionService, AccountExportService

provides:
  - AccountController with DELETE /account/ (202, password-verified, task-enqueued) and GET /account/export (JSON download)
  - UserDeletionService: 4-step GDPR cascade (cancel_subscription, delete_customer, delete_person, user.delete())
  - AccountExportService: profile + social_accounts + billing export (no Stripe IDs)
  - delete_user_account Celery shared_task (bound, max_retries=3, continues on step failure)
  - ObservabilityAdapter.delete_person() abstract method + PostHogAdapter implementation using httpx management REST API
  - PaymentAdapter.delete_customer() abstract method + StripeAdapter and StubAdapter implementations
  - POSTHOG_PROJECT_ID and POSTHOG_PERSONAL_API_KEY settings and .env.example entries

affects:
  - phase 23 entitlements (user deletion removes billing Customer via ORM cascade)
  - any future observability phase (PostHogAdapter now has delete_person)

tech-stack:
  added: [httpx (already in uv.lock, now used for PostHog management REST API)]
  patterns:
    - Alias-import pattern for patchable callables in Celery tasks (get_adapter as PaymentAdapter, get_observability_adapter as ObservabilityAdapter)
    - conftest.py session fixture patches ninja.testing.TestClient with ninja_extra.testing.TestClient for ControllerBase support + adds force_login()

key-files:
  created:
    - apps/api/apps/accounts/tasks.py
    - apps/api/tests/accounts/conftest.py
  modified:
    - apps/api/apps/core/observability.py
    - apps/api/apps/billing/adapters.py
    - apps/api/apps/billing/stub_adapter.py
    - apps/api/apps/accounts/services.py
    - apps/api/apps/accounts/controllers.py
    - apps/api/config/settings/base.py
    - apps/api/.env.example
    - apps/api/tests/billing/test_adapters.py

key-decisions:
  - "Alias-import pattern for Celery task patchability: import get_adapter as PaymentAdapter so tests can patch apps.accounts.tasks.PaymentAdapter while production calls get_adapter() — avoids abstract class instantiation in production"
  - "PostHog management API host fixup: settings.POSTHOG_HOST.replace('i.posthog', 'posthog') handles EU cloud vs US cloud difference between ingestion and management API"
  - "GDPR export plan_id is None — Subscription model stores stripe_subscription_id but not internal plan_id; exposing stripe_subscription_id in export would violate the no-Stripe-IDs requirement"
  - "conftest force_login patch scoped to tests/accounts/ only — avoids polluting other test modules with global ninja TestClient mutation"

patterns-established:
  - "Deletion cascade pattern: each step wrapped in try/except, user.delete() always called last — Article 17 compliance even when external service calls fail"
  - "Export service pattern: service assembles dict, controller adds exported_at and returns HttpResponse with Content-Disposition header"

requirements-completed: [GDPR-01, GDPR-02]

duration: 25min
completed: 2026-03-12
---

# Phase 21 Plan 02: GDPR Baseline Implementation Summary

**GDPR Article 17 deletion cascade (cancel_subscription → delete_customer → delete_person → user.delete()) and Article 20 JSON export via AccountController, turning all 13 RED test stubs GREEN**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-03-12T19:50:00Z
- **Completed:** 2026-03-12T20:15:00Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments

- Full GDPR Article 17 deletion cascade implemented across 4 service layers (billing, observability, ORM)
- GDPR Article 20 export endpoint returning JSON download with profile, social accounts, and billing history (Stripe IDs excluded)
- PostHogAdapter extended with httpx-based management REST API calls for person deletion (POSTHOG_PROJECT_ID + POSTHOG_PERSONAL_API_KEY)
- All 13 accounts tests pass GREEN; billing adapter contract test updated; pre-existing billing service errors unrelated to this plan

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend ObservabilityAdapter and PaymentAdapter ABCs** - `5d3e629` (feat)
2. **Task 2: Implement services, task, and controller** - `15fe783` (feat)
3. **Deviation fix: billing adapter contract test** - `5404853` (fix)

## Files Created/Modified

- `apps/api/apps/core/observability.py` - Added delete_person() abstract method + PostHogAdapter httpx implementation + NoOpAdapter/SentryAdapter no-ops
- `apps/api/apps/billing/adapters.py` - Added delete_customer() abstract method to PaymentAdapter ABC
- `apps/api/apps/billing/stub_adapter.py` - Added delete_customer() returning {"deleted": True}
- `apps/api/apps/accounts/services.py` - Added UserDeletionService and AccountExportService
- `apps/api/apps/accounts/tasks.py` - Created delete_user_account Celery shared_task (bind, max_retries=3)
- `apps/api/apps/accounts/controllers.py` - Added AccountController with DELETE /account/ and GET /account/export
- `apps/api/config/settings/base.py` - Added POSTHOG_PROJECT_ID and POSTHOG_PERSONAL_API_KEY settings
- `apps/api/.env.example` - Added POSTHOG_PROJECT_ID and POSTHOG_PERSONAL_API_KEY documentation
- `apps/api/tests/accounts/conftest.py` - Created: ninja TestClient patches for ControllerBase + force_login support
- `apps/api/tests/billing/test_adapters.py` - Added delete_customer to expected abstract methods set

## Decisions Made

- **Alias-import pattern for Celery tasks:** `from apps.billing.utils import get_adapter as PaymentAdapter` allows tests to patch `apps.accounts.tasks.PaymentAdapter` while production code calls the actual configured adapter via `get_adapter()`. This avoids trying to instantiate the ABC directly (which would fail) while keeping test patches working.
- **plan_id is None in export:** The Subscription model stores `stripe_subscription_id` not an internal `plan_id`. Exposing the Stripe ID would violate the no-Stripe-IDs requirement. `plan_id` is returned as None until a separate plan mapping table is added to the export.
- **PostHog EU cloud host fixup:** `POSTHOG_HOST.replace("i.posthog", "posthog")` converts the ingestion endpoint (`eu.i.posthog.com`) to the management API endpoint (`eu.posthog.com`). This is required because the management REST API uses a different subdomain.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] ninja.testing.TestClient incompatible with ninja_extra ControllerBase**

- **Found during:** Task 2 (AccountController implementation)
- **Issue:** The RED tests use `from ninja.testing import TestClient` but pass `AccountController` (a `ControllerBase` subclass) to it. ninja's plain `TestClient` doesn't have `set_api_instance()` support for controllers — only `ninja_extra.testing.TestClient` does.
- **Fix:** Created `tests/accounts/conftest.py` with a session-scoped autouse fixture that replaces `ninja.testing.TestClient` with `ninja_extra.testing.TestClient` and adds a `force_login()` method to `NinjaClientBase`.
- **Files modified:** `apps/api/tests/accounts/conftest.py` (created)
- **Verification:** All 13 accounts tests pass GREEN after patch.
- **Committed in:** `15fe783` (Task 2 commit)

**2. [Rule 1 - Bug] PaymentAdapter contract test did not include delete_customer**

- **Found during:** Task 2 verification (full suite run)
- **Issue:** `tests/billing/test_adapters.py::TestPaymentAdapterContract::test_abstract_methods_defined` checks an exact set of abstract method names. Adding `delete_customer` to the ABC caused this test to fail with a set mismatch.
- **Fix:** Added `"delete_customer"` to the expected set in the test.
- **Files modified:** `apps/api/tests/billing/test_adapters.py`
- **Verification:** `pytest tests/billing/test_adapters.py` passes.
- **Committed in:** `5404853`

---

**Total deviations:** 2 auto-fixed (2 Rule 1 bugs)
**Impact on plan:** Both fixes were necessary for the test suite to run. No scope creep.

## Issues Encountered

- Pre-existing billing test errors (`test_get_subscription`, `test_change_plan`, billing services tests) are NPlusOne errors unrelated to this plan. Verified pre-existing by stash-testing against Task 1 commit. Logged as out-of-scope.

## User Setup Required

This plan adds two new PostHog API credentials required for production GDPR person deletion:

- `POSTHOG_PROJECT_ID` — Numeric project ID from PostHog URL (Settings → Project)
- `POSTHOG_PERSONAL_API_KEY` — Personal API key (PostHog Settings → Personal API keys → Create)

Without these, `PostHogAdapter.delete_person()` logs a warning and returns (graceful no-op). `NoOpAdapter` (default in dev/CI) always no-ops silently.

## Next Phase Readiness

- Phase 21-03 (cookie consent) can proceed — deletion and export endpoints are live
- Phase 21-04 (frontend GDPR UI) can proceed — both backend endpoints are tested and operational
- Stripe customer is permanently deleted during cascade — Phase 23 entitlements must handle `Customer.DoesNotExist` gracefully

---

_Phase: 21-gdpr-baseline_
_Completed: 2026-03-12_
