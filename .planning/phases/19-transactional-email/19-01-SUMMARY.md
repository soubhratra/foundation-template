---
phase: 19-transactional-email
plan: "01"
subsystem: testing
tags: [pytest, tdd, notifications, celery, anymail, resend, css-inlining, scaffolder]

# Dependency graph
requires: []
provides:
  - Five RED test stubs covering all five EMAIL requirements (EMAIL-01 through EMAIL-05)
  - tests/notifications/ package with test_utils.py, test_tasks.py, test_settings.py
  - tests/test_scaffolder_email_removal.py modelled on existing billing/observability removal tests
affects:
  - 19-02 (settings): test_settings.py turns GREEN when EMAIL_BACKEND conditional added to base.py
  - 19-03 (notifications app): test_utils.py and test_tasks.py turn GREEN when apps.notifications created
  - 19-04 (scaffolder): test_scaffolder_email_removal.py turns GREEN when removeEmailModule() added

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "TDD RED stub pattern: import module that does not exist yet at module level to guarantee ImportError at collection time"
    - "Scaffolder removal test pattern: copy relevant source files to tmp_path, invoke compiled removeEmailModule() via node --input-type=module inline script, assert artifacts absent"

key-files:
  created:
    - apps/api/tests/notifications/__init__.py
    - apps/api/tests/notifications/test_utils.py
    - apps/api/tests/notifications/test_tasks.py
    - apps/api/tests/notifications/test_settings.py
    - apps/api/tests/test_scaffolder_email_removal.py
  modified: []

key-decisions:
  - "test_settings.py uses override_settings rather than re-importing settings module — Django's settings are loaded once at startup so direct env patching does not retroactively change EMAIL_BACKEND; override_settings is the correct mechanism"
  - "test_css_is_inlined uses send_email_task.run() to bypass Celery broker in tests — .run() calls the underlying Python function without queueing"
  - "TestEmailRemovalViaCLI is skipped (not RED) when dist/remove.js absent, becomes RED once dist exists but removeEmailModule export is missing"
  - "test_utils.py patches apps.notifications.tasks.send_email_task.delay at dotted path — avoids needing real Celery broker, verifies task is enqueued via mock call assertions"

patterns-established:
  - "Notifications test pattern: test_utils tests public send_email() function; test_tasks tests Celery task impl directly via .run()"
  - "Scaffolder test pattern mirrors test_scaffolder_billing_removal.py exactly — PROJECT_ROOT parents[3], CLI_DIST_REMOVE path, skipif guard, node --input-type=module inline script"

requirements-completed: [EMAIL-01, EMAIL-02, EMAIL-03, EMAIL-04, EMAIL-05]

# Metrics
duration: 4min
completed: 2026-03-12
---

# Phase 19 Plan 01: Transactional Email Test Stubs Summary

**Five Nyquist-compliant RED test stubs scaffolded for all EMAIL requirements using pytest, covering send_email() queuing, on_commit rollback protection, CSS inlining, backend auto-switch, and CLI scaffolder removal**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-12T03:11:12Z
- **Completed:** 2026-03-12T03:15:27Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Created `tests/notifications/` test package with stubs for EMAIL-01 through EMAIL-04 — all fail with `ModuleNotFoundError: No module named 'apps.notifications'` (correct RED state)
- Created `tests/test_scaffolder_email_removal.py` modelled exactly on the existing billing removal test pattern — fails because `removeEmailModule` export does not yet exist in dist/remove.js (correct RED state)
- Established `TestEmailRemovalViaCLI` with `@pytest.mark.skipif` guard matching the billing/observability pattern so it is skipped when CLI not built and RED once dist exists but export is missing

## Task Commits

Each task was committed atomically:

1. **Task 1: Create test_utils.py and test_tasks.py stubs (EMAIL-01, EMAIL-02, EMAIL-03)** - `b23435f` (test)
2. **Task 2: Create test_settings.py and test_scaffolder_email_removal.py stubs (EMAIL-01, EMAIL-04, EMAIL-05)** - `5dad8b3` (test)

## Files Created/Modified

- `apps/api/tests/notifications/__init__.py` - empty test package init
- `apps/api/tests/notifications/test_utils.py` - EMAIL-01 (send_email queues task) and EMAIL-02 (on_commit rollback protection) stubs
- `apps/api/tests/notifications/test_tasks.py` - EMAIL-03 (CSS inlining, plain-text alternative) stubs
- `apps/api/tests/notifications/test_settings.py` - EMAIL-01 (backend auto-switch) and EMAIL-04 (console fallback) stubs
- `apps/api/tests/test_scaffolder_email_removal.py` - EMAIL-05 (CLI removeEmailModule integration) stub

## Decisions Made

- `test_css_is_inlined` uses `send_email_task.run()` to bypass Celery broker — the `.run()` method calls the underlying Python function synchronously, allowing the test to exercise CSS inlining without a real broker
- `test_settings.py` uses `override_settings` for verifying backend selection rather than re-importing the settings module — Django settings are a singleton loaded at startup; `override_settings` is the idiomatic mechanism for per-test overrides
- `TestEmailRemovalViaCLI` is skip-guarded (not immediately RED) when dist/remove.js absent — this matches the established billing/observability pattern and avoids false RED state in environments where the CLI has not been built

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None — ruff auto-formatted two minor style issues (unused import, line length) during pre-commit hooks. Resolved by re-staging after hook modifications.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- All five EMAIL requirement test stubs are in place
- Plan 19-02 (Django settings): `test_settings.py` tests will turn GREEN when `EMAIL_BACKEND` conditional is added to `base.py`
- Plan 19-03 (notifications app): `test_utils.py` and `test_tasks.py` tests will turn GREEN when `apps.notifications` is created
- Plan 19-04 (scaffolder): `test_scaffolder_email_removal.py` will turn GREEN when `removeEmailModule()` is added to dist/remove.js

---

_Phase: 19-transactional-email_
_Completed: 2026-03-12_
