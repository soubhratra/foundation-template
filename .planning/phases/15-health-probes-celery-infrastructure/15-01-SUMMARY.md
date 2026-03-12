---
phase: 15-health-probes-celery-infrastructure
plan: "01"
subsystem: api-testing
tags: [tdd, health-probes, celery, django-celery-beat, flower, red-tests]
dependency_graph:
  requires: []
  provides:
    - RED test contracts for /api/health/live (Plan 15-02)
    - RED test contracts for /api/health/ready (Plan 15-02)
    - RED test contracts for /api/health/startup (Plan 15-02)
    - RED test contracts for example_periodic_task (Plan 15-03)
  affects:
    - apps/api/tests/core/test_health_probes.py
    - apps/api/tests/core/test_periodic_tasks.py
tech_stack:
  added:
    - django-celery-beat==2.9.0 (runtime dep — needs migrations + AppConfig)
    - flower==2.0.1 (runtime dep — runs as standalone process in Docker Compose)
  patterns:
    - Deferred import pattern: all module imports inside test function bodies for clean per-test RED failures
    - unittest.mock.patch for isolating external dependency checks in readiness/startup probes
key_files:
  created:
    - apps/api/tests/core/test_health_probes.py
    - apps/api/tests/core/test_periodic_tasks.py
  modified:
    - apps/api/pyproject.toml (added django-celery-beat, flower to [project.dependencies])
    - apps/api/uv.lock (lockfile updated)
decisions:
  - django-celery-beat and flower placed in [project.dependencies] not dev group — both need runtime presence (beat needs migrations + AppConfig, flower runs as its own process)
  - _check_postgres and _count_pending_migrations mocked as internal helpers — drives the exact interface Plan 15-02 must implement
  - _do_work mocked as standalone helper — drives the exact interface Plan 15-03 must implement for the periodic task
metrics:
  duration_seconds: 92
  completed_date: "2026-03-11"
  tasks_completed: 2
  files_created: 2
  files_modified: 2
---

# Phase 15 Plan 01: TDD Red Phase — Health Probes + Celery Deps Summary

Install django-celery-beat + flower and write 7 failing RED test stubs defining exact interfaces for Kubernetes health probe endpoints and example periodic task.

## What Was Built

### Task 1: Install deps + write RED test stubs for health probes

Installed `django-celery-beat>=2.7` and `flower>=2.0` as runtime dependencies (not dev group) into `apps/api/pyproject.toml`. Both are runtime requirements: celery-beat needs database migrations and AppConfig registration, flower runs as its own process in Docker Compose.

Created `apps/api/tests/core/test_health_probes.py` with 5 RED test stubs:

- `test_live_returns_200` — GET /api/health/live returns 200 `{"status": "alive"}`
- `test_ready_returns_200_when_all_deps_ok` — GET /api/health/ready returns 200 with all checks ok
- `test_ready_returns_503_when_postgres_failing` — GET /api/health/ready returns 503 when postgres raises
- `test_startup_returns_200_when_no_pending_migrations` — GET /api/health/startup returns 200 with 0 pending
- `test_startup_returns_503_when_migrations_pending` — GET /api/health/startup returns 503 with N pending

All tests import `apps.core.health` inside the function body (deferred import pattern). All fail with `ImportError` on `apps.core.health` — correct RED state.

Commit: `4530919`

### Task 2: Write RED test stubs for example periodic task

Created `apps/api/tests/core/test_periodic_tasks.py` with 2 RED test stubs:

- `test_example_task_succeeds_and_returns_result` — `example_periodic_task.apply()` returns successful result
- `test_example_task_retries_on_transient_error` — `celery.exceptions.Retry` raised when `_do_work` raises

Both tests import `apps.core.tasks` inside the function body. Both fail with `ModuleNotFoundError` on `apps.core.tasks` — correct RED state.

Commit: `2d67a9a`

## Verification Results

```
FAILED tests/core/test_health_probes.py::test_live_returns_200 - ImportError
FAILED tests/core/test_health_probes.py::test_ready_returns_200_when_all_deps_ok
FAILED tests/core/test_health_probes.py::test_ready_returns_503_when_postgres_failing
FAILED tests/core/test_health_probes.py::test_startup_returns_200_when_no_pending_migrations
FAILED tests/core/test_health_probes.py::test_startup_returns_503_when_migrations_pending
FAILED tests/core/test_periodic_tasks.py::test_example_task_succeeds_and_returns_result
FAILED tests/core/test_periodic_tasks.py::test_example_task_retries_on_transient_error
7 failed — all with ModuleNotFoundError/ImportError (correct RED state)
```

## Decisions Made

1. **django-celery-beat and flower in [project.dependencies]** — Both are runtime requirements. celery-beat requires migrations to create schedule tables and AppConfig registration in INSTALLED_APPS. flower runs as a standalone process in Docker Compose and must be resolvable in the production virtualenv.

2. **Internal helper interface driven by tests** — `_check_postgres` and `_count_pending_migrations` mocked as internal helpers in health probe tests. `_do_work` mocked as standalone helper in periodic task tests. These mocking targets define the exact internal interface Plan 15-02 and Plan 15-03 must implement.

3. **Deferred import pattern** — All module imports inside test function bodies (matching Phase 13/14 pattern). Ensures clean per-test failure messages in RED phase and avoids collection-time errors that would hide individual test failures.

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED

- `apps/api/tests/core/test_health_probes.py` — exists, 87 lines (min 40 required)
- `apps/api/tests/core/test_periodic_tasks.py` — exists, 35 lines (min 20 required)
- `apps/api/pyproject.toml` — contains `django-celery-beat`
- Commit `4530919` — verified via git log
- Commit `2d67a9a` — verified via git log
