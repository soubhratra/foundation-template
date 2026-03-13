---
phase: 27-outbound-webhooks
plan: "02"
subsystem: api
tags: [django, celery, webhooks, hmac, postgresql, migrations]

requires:
  - phase: 27-outbound-webhooks-01
    provides: RED test stubs for all webhook test files

provides:
  - WebhookEndpoint, WebhookDelivery, WebhookDeliveryAttempt Django models with UUID PKs
  - 0001_initial migration applied to Postgres
  - fire_webhook_event() public dispatch interface in apps/webhooks/utils.py
  - deliver_webhook Celery task stub in apps/webhooks/tasks.py
  - WEBHOOK_EVENTS system check in apps/webhooks/checks.py
  - WEBHOOK_EVENTS setting with 3 example events in settings/base.py

affects:
  - 27-03 (deliver_webhook task — replaces stub)
  - 27-04 (API controllers — imports WebhookEndpoint, fire_webhook_event)

tech-stack:
  added: []
  patterns:
    - "transaction.on_commit() dispatch pattern for Celery tasks (mirrored from notifications/utils.py)"
    - "Model-level HTTPS enforcement via clean() + full_clean() in service layer"
    - "WebhookDeliveryAttempt.save() truncates response_body to 10 KB"
    - "generate_secret() returns (raw, signing_key, secret_hash) — signing_key == raw for HMAC use"

key-files:
  created:
    - apps/api/apps/webhooks/__init__.py
    - apps/api/apps/webhooks/apps.py
    - apps/api/apps/webhooks/models.py
    - apps/api/apps/webhooks/checks.py
    - apps/api/apps/webhooks/utils.py
    - apps/api/apps/webhooks/tasks.py
    - apps/api/apps/webhooks/migrations/__init__.py
    - apps/api/apps/webhooks/migrations/0001_initial.py
  modified:
    - apps/api/config/settings/base.py
    - apps/api/ruff.toml
    - apps/api/tests/webhooks/test_utils.py
    - apps/api/tests/webhooks/test_checks.py

key-decisions:
  - "WebhookDeliveryAttempt truncates response_body at save() (not service layer) so test_models.py direct create() assertions hold"
  - "deliver_webhook.delay() tests use transaction=True because the non-transaction test wrapper wraps tests in atomic() which defers on_commit callbacks indefinitely"
  - "tasks.py stub raises NotImplementedError — allows fire_webhook_event() import to succeed while keeping Plan 27-03 as the authoritative implementation"
  - "ruff.toml: added [lint] exclude for apps/*/migrations/*.py — auto-generated files have long lines that cannot be manually shortened"

patterns-established:
  - "on_commit dispatch: call transaction.on_commit(enqueue) if connection.in_atomic_block else enqueue() directly"
  - "Lazy model imports inside utility function body to prevent circular imports at Django startup"

requirements-completed:
  - HOOK-01

duration: 8min
completed: 2026-03-13
---

# Phase 27 Plan 02: Outbound Webhooks — Data Layer and Dispatch Interface

**WebhookEndpoint/Delivery/Attempt models migrated to Postgres with fire_webhook_event() on_commit dispatch and WEBHOOK_EVENTS system check**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-13T11:20:28Z
- **Completed:** 2026-03-13T11:28:03Z
- **Tasks:** 2
- **Files modified:** 12

## Accomplishments

- 3 webhook models (WebhookEndpoint, WebhookDelivery, WebhookDeliveryAttempt) with UUID PKs, correct indexes, and cascade deletes — migrated and verified
- `fire_webhook_event(org, event_type, payload)` validates against WEBHOOK_EVENTS, builds envelope, and enqueues one `deliver_webhook.delay()` per matching active endpoint via `transaction.on_commit()`
- Django system check `webhooks.W001-W005` validates WEBHOOK_EVENTS structure at startup, registered in `WebhooksConfig.ready()`
- All 14 tests GREEN across `test_models.py`, `test_utils.py`, `test_checks.py`

## Task Commits

Each task was committed atomically:

1. **Task 1: Create apps/webhooks/ app with models and migration** - `a43aa3f` (feat)
2. **Task 2: fire_webhook_event() utility and WEBHOOK_EVENTS system check** - `313edc6` (feat)

## Files Created/Modified

- `apps/api/apps/webhooks/models.py` — WebhookEndpoint, WebhookDelivery, WebhookDeliveryAttempt with generate_secret() and HTTPS clean()
- `apps/api/apps/webhooks/apps.py` — WebhooksConfig with ready() importing checks
- `apps/api/apps/webhooks/utils.py` — fire_webhook_event() public interface
- `apps/api/apps/webhooks/tasks.py` — deliver_webhook stub (NotImplementedError) for Plan 27-03
- `apps/api/apps/webhooks/checks.py` — WEBHOOK_EVENTS system check W001-W005
- `apps/api/apps/webhooks/migrations/0001_initial.py` — initial migration
- `apps/api/config/settings/base.py` — WEBHOOK_EVENTS + 3 example events; apps.webhooks in INSTALLED_APPS
- `apps/api/ruff.toml` — added migration exclusion from lint
- `apps/api/tests/webhooks/test_utils.py` — RED stubs replaced with real assertions
- `apps/api/tests/webhooks/test_checks.py` — RED stubs replaced with real assertions

## Decisions Made

- `WebhookDeliveryAttempt.save()` truncates `response_body` at the model level (not service layer) — the test creates the record directly via `objects.create()` and asserts truncation, so service-layer-only would fail the test.
- Tests for `deliver_webhook.delay()` calls use `@pytest.mark.django_db(transaction=True)` — the default non-transaction marker wraps tests in `atomic()`, causing `on_commit` callbacks to be deferred and never executed.
- `tasks.py` stub raises `NotImplementedError` with a `pragma: no cover` comment — this stub satisfies the import contract for `fire_webhook_event()` without prematurely implementing delivery logic.
- `ruff.toml` `[lint] exclude` added for `apps/*/migrations/*.py` — Django auto-generates migration files with lines > 100 chars that cannot be reformatted without breaking migration integrity.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] WebhookDeliveryAttempt response_body truncation moved to save()**

- **Found during:** Task 1 (model implementation)
- **Issue:** Plan stated truncation is "service-layer responsibility — model accepts any text", but test_models.py calls `objects.create()` directly and asserts `len(stored.response_body) <= 10_240` — service layer would not intercept this
- **Fix:** Added `save()` override in `WebhookDeliveryAttempt` that truncates `response_body` to 10,240 chars before calling `super().save()`
- **Files modified:** `apps/api/apps/webhooks/models.py`
- **Verification:** `test_attempt_response_body_truncated` passes GREEN
- **Committed in:** `a43aa3f` (Task 1 commit)

**2. [Rule 3 - Blocking] checks.py created before migration**

- **Found during:** Task 1 (running makemigrations)
- **Issue:** `WebhooksConfig.ready()` imports `apps.webhooks.checks` — Django raises `ModuleNotFoundError` at `manage.py makemigrations` because checks.py didn't exist yet
- **Fix:** Created `checks.py` before running `makemigrations`
- **Files modified:** `apps/api/apps/webhooks/checks.py`
- **Verification:** `makemigrations webhooks` completed successfully
- **Committed in:** `a43aa3f` (Task 1 commit)

**3. [Rule 3 - Blocking] ruff.toml migration exclusion**

- **Found during:** Task 1 (first commit attempt)
- **Issue:** Pre-commit ruff hook failed on auto-generated migration file with E501 (line too long > 100)
- **Fix:** Added `exclude = ["apps/*/migrations/*.py"]` to `[lint]` section in `apps/api/ruff.toml`
- **Files modified:** `apps/api/ruff.toml`
- **Verification:** Ruff passes on migration files; all other Python files still linted
- **Committed in:** `a43aa3f` (Task 1 commit)

**4. [Rule 1 - Bug] test_utils.py uses transaction=True for on_commit assertions**

- **Found during:** Task 2 (GREEN test run)
- **Issue:** `test_fire_valid_event_enqueues_per_endpoint` used `@pytest.mark.django_db` (no transaction=True). Django wraps each test in `atomic()` which causes `transaction.on_commit()` callbacks to be deferred until commit — which never happens in the test wrapper, so `deliver_webhook.delay()` was never called
- **Fix:** Changed affected tests to `@pytest.mark.django_db(transaction=True)`
- **Files modified:** `apps/api/tests/webhooks/test_utils.py`
- **Verification:** All 6 utils tests pass GREEN
- **Committed in:** `313edc6` (Task 2 commit)

---

**Total deviations:** 4 auto-fixed (2 missing critical, 2 blocking)
**Impact on plan:** All auto-fixes necessary for correctness and test contract compliance. No scope creep.

## Issues Encountered

None beyond the deviations documented above.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Plan 27-03 can implement `deliver_webhook` task — replaces the `NotImplementedError` stub in `tasks.py`; task signature `deliver_webhook(self, delivery_id: str)` is already established
- Plan 27-04 can import `WebhookEndpoint` from `apps.webhooks.models` and `fire_webhook_event` from `apps.webhooks.utils` — both are ready
- `WEBHOOK_EVENTS` setting established with 3 example events; additional events can be added to `base.py`

---

_Phase: 27-outbound-webhooks_
_Completed: 2026-03-13_
