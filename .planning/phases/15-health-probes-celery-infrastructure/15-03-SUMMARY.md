---
phase: 15-health-probes-celery-infrastructure
plan: "03"
subsystem: infra
tags: [celery, celery-beat, django-celery-beat, flower, docker-compose, periodic-tasks]

# Dependency graph
requires:
  - phase: 15-01
    provides: RED test stubs for test_periodic_tasks.py that this plan turns GREEN
  - phase: 15-02
    provides: health probe infrastructure (same phase, prior plan)

provides:
  - example_periodic_task Celery task with bind=True, max_retries=3, exponential backoff
  - _do_work() internal helper enabling mock-based retry testing
  - CELERY_BEAT_SCHEDULE with 60s example task and DatabaseScheduler
  - django_celery_beat in INSTALLED_APPS
  - celery-worker, celery-beat, flower services in docker-compose.yml (dev)
  - celery-beat service in docker-compose.prod.yml (prod, no flower)

affects:
  - any phase adding real periodic tasks (replace _do_work contents, add schedule entry)
  - phase 16 (future observability for periodic tasks)
  - new project scaffolding (docker-compose.yml is copied verbatim)

# Tech tracking
tech-stack:
  added:
    - django-celery-beat (already in deps from 15-01, now configured with migrations + AppConfig)
    - mher/flower:2.0 (Docker image, dev-only)
  patterns:
    - bind=True + max_retries + self.retry(countdown=60*(2**retries)) for exponential backoff
    - _do_work() helper pattern: keep task body thin, extract logic for patchability
    - DatabaseScheduler: beat schedule lives in DB, editable via admin without redeployment
    - Flower dev-only: visible in docker-compose.yml, absent from docker-compose.prod.yml

key-files:
  created:
    - apps/api/apps/core/tasks.py
  modified:
    - apps/api/config/settings/base.py
    - docker-compose.yml
    - docker-compose.prod.yml

key-decisions:
  - "example_periodic_task uses bind=True + self.retry() with exponential backoff (60s, 120s, 240s) — standard Celery retry pattern for transient failures"
  - "CELERY_BEAT_SCHEDULER = DatabaseScheduler — beat schedule is DB-backed so operators can modify intervals via admin without redeployment"
  - "Flower is dev-only (docker-compose.yml only, not docker-compose.prod.yml) per OBS-06 — no production monitoring exposure"
  - "celery-worker service added to docker-compose.yml alongside celery-beat — without a worker, beat-dispatched tasks would queue indefinitely in local dev"
  - "raise self.retry(...) from exc — ruff B904 requires chaining exceptions within except blocks for proper traceback context"

patterns-established:
  - "Periodic task scaffold: _do_work() helper + @shared_task(bind=True) + self.retry() with exponential backoff"
  - "Docker compose service split: dev compose includes observability/debug services (flower), prod compose omits them"

requirements-completed: [OBS-05, OBS-06]

# Metrics
duration: 4min
completed: 2026-03-11
---

# Phase 15 Plan 03: Example Periodic Task + Celery Beat Infrastructure Summary

**example_periodic_task scaffold with exponential-backoff retry, django-celery-beat DatabaseScheduler, and Flower dev dashboard wired into Docker Compose**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-11T19:57:48Z
- **Completed:** 2026-03-11T20:01:50Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Created `apps/core/tasks.py` with `example_periodic_task` demonstrating the standard periodic task pattern: `bind=True`, `max_retries=3`, exponential backoff via `self.retry(countdown=60*(2**retries))`
- Added `django_celery_beat` to INSTALLED_APPS and configured `CELERY_BEAT_SCHEDULE` with DatabaseScheduler — beat schedule is DB-backed and editable via admin
- Extended `docker-compose.yml` with `celery-worker`, `celery-beat`, and `flower` services (Flower at port 5555 for local task visibility)
- Extended `docker-compose.prod.yml` with `celery-beat` only — Flower absent per OBS-06 requirement

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement example_periodic_task + django-celery-beat settings** - `03d4fba` (feat) — note: landed in the 15-02 commit due to pre-commit hook stash behavior; changes are committed and verified
2. **Task 2: Add celery-beat + Flower to Docker Compose** - `5f1dd92` (feat)

**Plan metadata:** (docs commit — created below)

## Files Created/Modified

- `apps/api/apps/core/tasks.py` - example_periodic_task with bind, retry, backoff + \_do_work helper
- `apps/api/config/settings/base.py` - Added django_celery_beat to INSTALLED_APPS, CELERY_BEAT_SCHEDULER, CELERY_BEAT_SCHEDULE
- `docker-compose.yml` - Added celery-worker, celery-beat, flower services
- `docker-compose.prod.yml` - Added celery-beat service (no flower)

## Decisions Made

- `raise self.retry(...) from exc` is required (not `raise self.retry(...)`) — ruff B904 enforces exception chaining within except blocks for proper traceback context
- celery-worker added to dev compose alongside celery-beat — without it, tasks dispatched by beat would queue indefinitely with no consumer in local dev
- DatabaseScheduler chosen over PersistentScheduler — DB-backed schedule allows runtime edits via admin without container restart

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed ruff B904 lint error — raise self.retry() without from exc**

- **Found during:** Task 1 (example_periodic_task implementation)
- **Issue:** Pre-commit hook (ruff) rejected `raise self.retry(exc=exc, ...)` inside except block — B904 requires `raise ... from exc` to chain exceptions properly
- **Fix:** Changed to `raise self.retry(exc=exc, countdown=...) from exc`
- **Files modified:** apps/api/apps/core/tasks.py
- **Verification:** ruff check passes, both tests still GREEN
- **Committed in:** 03d4fba (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug/lint)
**Impact on plan:** Single minor fix required by ruff lint enforcement. No scope creep.

## Issues Encountered

- Pre-existing billing test failure (`test_create_checkout_session` — price_id mismatch) is unrelated to this plan's scope. Logged to deferred items.
- Pre-existing middleware test failure (`test_context_has_duration_ms` hitting `/api/v1/health` returning 404) is unrelated to this plan's scope.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 15 complete: health probes (15-01, 15-02) + periodic task scaffold (15-03) all done
- `docker compose up` now starts all development services including Flower at http://localhost:5555
- New projects scaffold with a working periodic task pattern from day one
- To add a real periodic task: replace `_do_work()` contents, add entry to `CELERY_BEAT_SCHEDULE`

---

_Phase: 15-health-probes-celery-infrastructure_
_Completed: 2026-03-11_
