---
phase: 15-health-probes-celery-infrastructure
plan: "02"
subsystem: api
tags: [health-probes, kubernetes, liveness, readiness, startup, django, celery, postgres, redis]

# Dependency graph
requires:
  - phase: 15-01
    provides: RED test stubs for health probe endpoints (_check_postgres, _count_pending_migrations mock targets)
provides:
  - Plain Django views: live_view, ready_view, startup_view at /api/health/{live,ready,startup}
  - apps/core/health.py with mockable helper functions
  - apps/core/health_urls.py URL patterns
  - Old /api/v1/health HealthController removed
affects: [15-03, docker-compose-healthchecks, kubernetes-deployment]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Plain Django views (not Ninja) for health probes so they work even if Ninja app misconfigures
    - Mockable internal helpers (_check_postgres, _check_redis, _check_celery, _count_pending_migrations) enable test isolation without real infra
    - Health probes mounted before Ninja api/ prefix in urls.py to prevent URL shadowing

key-files:
  created:
    - apps/api/apps/core/health.py
    - apps/api/apps/core/health_urls.py
  modified:
    - apps/api/config/urls.py
    - apps/api/apps/core/controllers.py
    - apps/api/apps/core/schemas.py
    - apps/api/tests/test_health.py

key-decisions:
  - "Plain Django views (not Ninja) for health probes — probes must work even if Ninja app is misconfigured, no auth/middleware overhead"
  - "Health probes mounted before Ninja path('api/', ...) in urls.py — prevents URL shadowing by Ninja wildcard"
  - "Internal helpers (_check_postgres, _check_redis, _check_celery, _count_pending_migrations) extracted as module-level functions — test stubs mock these directly per Phase 15-01 RED test contracts"
  - "ready_view collects all check results independently — a failing check does not short-circuit remaining checks"

patterns-established:
  - "Health probe pattern: plain Django JsonResponse views, no Ninja, no auth, mounted first in urlpatterns"
  - "Dependency check helpers extracted as module-level functions for mockability"

requirements-completed: [OBS-04]

# Metrics
duration: 12min
completed: 2026-03-11
---

# Phase 15 Plan 02: Health Probe Endpoints Summary

**Three Kubernetes-style health probes (live/ready/startup) as plain Django views at /api/health/, replacing the old Ninja HealthController**

## Performance

- **Duration:** 12 min
- **Started:** 2026-03-11T19:57:50Z
- **Completed:** 2026-03-11T20:09:50Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Implemented `live_view`, `ready_view`, `startup_view` as plain Django views with JsonResponse — no Ninja dependency
- `ready_view` checks Postgres, Redis, and Celery independently; returns 503 with named failing check if any dependency is down
- `startup_view` uses Django's `MigrationExecutor` to count unapplied migrations; returns 503 if any are pending
- Removed old `HealthController` (Ninja, at `/api/v1/health`) and `HealthOut` schema — superseded by new probes
- All 7 tests pass GREEN (5 in `test_health_probes.py` + 2 updated in `test_health.py`)

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement health probe view functions** - `03d4fba` (feat)
2. **Task 2: Wire health probes, remove old HealthController** - `731ede4` (feat)

## Files Created/Modified

- `apps/api/apps/core/health.py` — Three probe view functions + four mockable helper functions
- `apps/api/apps/core/health_urls.py` — URL patterns for /api/health/ prefix
- `apps/api/config/urls.py` — Added `path("api/health/", include("apps.core.health_urls"))` before Ninja path
- `apps/api/apps/core/controllers.py` — HealthController removed; file now contains only a comment
- `apps/api/apps/core/schemas.py` — HealthOut class removed (ErrorDetail/ErrorOut kept)
- `apps/api/tests/test_health.py` — Old /api/v1/health tests replaced with probe path tests

## Decisions Made

- Plain Django views chosen over Ninja for health probes so probes remain functional even if Ninja app misconfigures (e.g., missing controller registration)
- Health probes mounted before Ninja's `path("api/", ...)` catch-all to prevent URL shadowing
- Internal helpers extracted at module level (not inline in view body) because Phase 15-01 test stubs mock them directly via `unittest.mock.patch("apps.core.health._check_postgres", ...)`
- `ready_view` runs all three checks and collects results independently — a Postgres failure still reports Redis and Celery status

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] URL wiring moved to Task 1 commit**

- **Found during:** Task 1 (implement health probe view functions)
- **Issue:** Task 1's verification tests hit `/api/health/live` and `/api/health/startup`, which require URL routing to be in place. The plan deferred URL wiring to Task 2, but tests would have failed without the route.
- **Fix:** Added `path("api/health/", include("apps.core.health_urls"))` to `config/urls.py` as part of Task 1 commit
- **Files modified:** apps/api/config/urls.py
- **Verification:** All Task 1 tests pass GREEN
- **Committed in:** 03d4fba (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Necessary reordering — URL wiring belongs with view creation for testability. No scope creep.

## Issues Encountered

- Pre-commit hook caught an unrelated ruff B904 error in `apps/core/tasks.py` (created in Phase 15-01 but not yet committed). Fixed by including `tasks.py` in Task 1 commit staging to clear the pre-existing hook failure.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Health probe endpoints live at `/api/health/live`, `/api/health/ready`, `/api/health/startup`
- All 7 tests pass GREEN — Phase 15-03 can build on these probe functions
- Docker Compose healthcheck can now use `curl -f http://localhost:8000/api/health/live`
- Kubernetes liveness/readiness/startup probes can reference these endpoints directly

---

_Phase: 15-health-probes-celery-infrastructure_
_Completed: 2026-03-11_
