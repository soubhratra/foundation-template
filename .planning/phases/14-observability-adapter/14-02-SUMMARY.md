---
phase: 14-observability-adapter
plan: "02"
subsystem: api
tags: [observability, posthog, django-middleware, celery-signals, tdd, python]

# Dependency graph
requires:
  - phase: 13-structured-logging-distributed-tracing
    provides: RequestContextMiddleware in apps/core/middleware.py — ObservabilityMiddleware sits after it
  - phase: 14-observability-adapter
    plan: "01"
    provides: RED test stubs in tests/core/test_observability.py — all 6 made GREEN in this plan
provides:
  - ObservabilityAdapter ABC with capture_exception/capture_event interface
  - PostHogAdapter using posthog.Posthog instance (thread-safe, lazy import)
  - NoOpAdapter (default, zero overhead, no errors when POSTHOG_API_KEY absent)
  - SentryAdapter stub with migration guide comment
  - get_observability_adapter() factory mirroring billing get_adapter() pattern
  - ObservabilityMiddleware.process_exception auto-capturing all unhandled Django exceptions
  - task_failure Celery signal connected in CoreConfig.ready() with weak=False
  - OBSERVABILITY MODULE settings block in base.py (POSTHOG_API_KEY, POSTHOG_HOST, OBSERVABILITY_ADAPTER)
affects:
  - 14-03 (Next.js PostHogProvider setup — depends on backend adapter being complete)
  - 14-04 (removeObservability() CLI — must clean all 5 files modified here)

# Tech tracking
tech-stack:
  added:
    - "posthog>=7.9.0 (posthog 7.9.11 installed) — in main [project.dependencies], not optional group"
  patterns:
    - "ObservabilityAdapter ABC mirrors PaymentAdapter — swap provider via one Django setting"
    - "get_observability_adapter() mirrors get_adapter() in billing/utils.py — import_string factory pattern"
    - "Lazy posthog import inside PostHogAdapter.__init__ — avoids ImportError when NoOpAdapter is active"
    - "process_exception returns None (not re-raise) — Django continues normal 500 flow"
    - "task_failure signal connected in CoreConfig.ready() with weak=False — prevents GC"
    - "Lazy import of get_observability_adapter inside signal handler — avoids circular import at module level"

key-files:
  created:
    - apps/api/apps/core/observability.py
  modified:
    - apps/api/apps/core/middleware.py
    - apps/api/apps/core/apps.py
    - apps/api/config/settings/base.py
    - apps/api/pyproject.toml
    - apps/api/.env.example

key-decisions:
  - "posthog in main [project.dependencies] (not optional group) — runtime dep; NoOpAdapter handles absent key at runtime, not at install time"
  - "process_exception returns None (not re-raise) — Django propagates exception naturally; re-raise causes duplicate processing"
  - "Lazy posthog import inside PostHogAdapter.__init__ — avoids ImportError in test environments using NoOpAdapter without posthog installed"
  - "task_failure signal connected in CoreConfig.ready(), not worker_process_init — PostHogAdapter creates fresh client per call so no pre-fork thread issue"
  - "NoOpAdapter is the OBSERVABILITY_ADAPTER default — CI and local dev without POSTHOG_API_KEY produce zero overhead and zero errors"

patterns-established:
  - "ObservabilityMiddleware appended to middleware.py below RequestContextMiddleware — sibling pattern"
  - "Celery signal handler defined inline in CoreConfig.ready() with lazy import — avoids circular import while keeping wiring co-located with other startup config"
  - "OBSERVABILITY MODULE / END OBSERVABILITY MODULE comment delimiters in base.py — enables reliable regex removal by removeObservability() in Plan 14-04"

requirements-completed:
  - OBS-03

# Metrics
duration: 4min
completed: 2026-03-11
---

# Phase 14 Plan 02: Django ObservabilityAdapter Implementation Summary

**PostHogAdapter ABC + NoOpAdapter default + ObservabilityMiddleware auto-capture + Celery task_failure signal, all 6 RED test stubs turned GREEN**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-11T19:29:10Z
- **Completed:** 2026-03-11T19:32:50Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Created `apps/api/apps/core/observability.py` with the full adapter hierarchy: `ObservabilityAdapter` ABC, `PostHogAdapter` (thread-safe posthog.Posthog instance), `NoOpAdapter` (zero-overhead default), `SentryAdapter` stub with migration guide, and `get_observability_adapter()` factory
- Appended `ObservabilityMiddleware` to `middleware.py`; `process_exception` captures all unhandled Django exceptions with user_id/path/method/exc_type context and returns None to preserve Django's normal 500 flow
- Wired `task_failure` Celery signal in `CoreConfig.ready()` with `weak=False`; lazy import inside handler avoids circular import
- Added OBSERVABILITY MODULE block to `base.py` (POSTHOG_API_KEY, POSTHOG_HOST, OBSERVABILITY_ADAPTER defaulting to NoOpAdapter) and updated MIDDLEWARE list

## Task Commits

Each task was committed atomically:

1. **Task 1: Create observability.py with ABC + adapters + factory** - `19394be` (feat)
2. **Task 2: Wire middleware, Celery signal, and Django settings** - `9cfdbd5` (feat)

## Files Created/Modified

- `apps/api/apps/core/observability.py` — ObservabilityAdapter ABC, PostHogAdapter, NoOpAdapter, SentryAdapter stub, get_observability_adapter() factory
- `apps/api/apps/core/middleware.py` — ObservabilityMiddleware appended below RequestContextMiddleware
- `apps/api/apps/core/apps.py` — task_failure signal handler connected in CoreConfig.ready() with weak=False
- `apps/api/config/settings/base.py` — OBSERVABILITY MODULE block + ObservabilityMiddleware in MIDDLEWARE
- `apps/api/pyproject.toml` — posthog>=7.9.0 added to main [project.dependencies]
- `apps/api/.env.example` — POSTHOG_API_KEY and POSTHOG_HOST env var documentation

## Decisions Made

- `posthog` added to main `[project.dependencies]` not an optional group — it is a runtime dependency; the NoOpAdapter handles the "turned off" case at runtime via the OBSERVABILITY_ADAPTER setting, not at install time (avoids `ImportError: No module named 'posthog'` in production)
- `process_exception` returns `None` (no re-raise) — Django propagates the exception naturally through its normal 500 handling chain; re-raising inside process_exception causes duplicate exception processing
- Lazy `import posthog` inside `PostHogAdapter.__init__` — avoids ImportError when posthog is not installed in test environments that exclusively use NoOpAdapter
- Signal connected in `CoreConfig.ready()` (not `worker_process_init`) — PostHogAdapter creates a fresh client per call so there is no pre-fork thread issue; `weak=False` prevents GC

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Installed posthog package before running tests**

- **Found during:** Task 1 (running test_posthog_adapter_capture_exception)
- **Issue:** `patch("posthog.Posthog")` requires posthog to be importable at test collection time; package was not yet installed in the venv even though it was already added to pyproject.toml
- **Fix:** Ran `uv pip install posthog` to install into the project venv; pyproject.toml had already been updated in the same task
- **Files modified:** None (venv state only; pyproject.toml already modified)
- **Verification:** 3 Task 1 tests passed GREEN after install
- **Committed in:** `19394be` (Task 1 commit)

**2. [Rule 1 - Bug] Fixed two ruff line-length violations**

- **Found during:** Task 2 commit (pre-commit hook)
- **Issue:** `middleware.py` docstring line exceeded 100 chars; `base.py` MIDDLEWARE comment exceeded 100 chars
- **Fix:** Split middleware docstring into multi-line; shortened base.py comment from "# OBSERVABILITY MODULE — remove this line to exclude observability" to "# OBSERVABILITY MODULE"
- **Files modified:** apps/api/apps/core/middleware.py, apps/api/config/settings/base.py
- **Verification:** ruff hook passed on second commit attempt; 6 tests still GREEN
- **Committed in:** `9cfdbd5` (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 blocking install, 1 bug/lint)
**Impact on plan:** Both fixes necessary for tests to run and commit to succeed. No scope creep.

## Issues Encountered

- Pre-commit ruff hook caught two line-length violations on first Task 2 commit attempt; ruff-format auto-fixed apps.py formatting in the same run. Fixed and recommitted cleanly.

## User Setup Required

None - no external service configuration required for this plan. POSTHOG_API_KEY is optional (defaults to NoOpAdapter).

## Next Phase Readiness

- All 6 tests in `tests/core/test_observability.py` GREEN
- `manage.py check` passes (3 pre-existing allauth deprecation warnings, all pre-existing, none introduced here)
- Plan 14-03 (Next.js PostHogProvider) can proceed — Django backend adapter is complete
- Plan 14-04 (removeObservability() CLI) can target all 5 modified files; OBSERVABILITY MODULE comment delimiters in base.py are in place for reliable regex removal

---

_Phase: 14-observability-adapter_
_Completed: 2026-03-11_

## Self-Check: PASSED

- FOUND: apps/api/apps/core/observability.py
- FOUND: apps/api/apps/core/middleware.py
- FOUND: apps/api/apps/core/apps.py
- FOUND: apps/api/config/settings/base.py
- FOUND: .planning/phases/14-observability-adapter/14-02-SUMMARY.md
- FOUND: commit 19394be (observability.py + pyproject.toml)
- FOUND: commit 9cfdbd5 (middleware, apps.py, settings, env.example)
