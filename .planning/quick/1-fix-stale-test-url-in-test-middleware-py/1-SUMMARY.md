---
phase: quick
plan: 1
subsystem: api/tests, docker
tags: [bug-fix, testing, docker, redis]
dependency_graph:
  requires: []
  provides: [passing-middleware-tests, correct-redis-urls-in-compose]
  affects: [apps/api/tests/core/test_middleware.py, docker-compose.yml, docker-compose.prod.yml]
tech_stack:
  added: []
  patterns: []
key_files:
  modified:
    - apps/api/tests/core/test_middleware.py
    - docker-compose.yml
    - docker-compose.prod.yml
decisions:
  - Health endpoint URL in tests is /api/health/live (wired in Phase 15, not the old /api/v1/health)
  - Redis DB 1 for cache, DB 2 for sessions — separate namespaces from broker (DB 0)
  - OTEL_EXPORTER_OTLP_ENDPOINT added to celery-beat in dev compose for parity with celery-worker
  - No OTEL vars in prod compose — Jaeger is dev-only, does not appear in docker-compose.prod.yml
metrics:
  duration: 5 min
  completed: 2026-03-12
  tasks_completed: 2
  files_modified: 3
---

# Quick Fix 1: Fix Stale Test URL and Missing Redis Env Vars Summary

**One-liner:** Fixed 404-causing stale `/api/v1/health` test URL to `/api/health/live` and added `CACHE_REDIS_URL`/`SESSION_REDIS_URL` to all Docker Compose services that need Redis for cache and session backends.

## Tasks Completed

| Task | Name                                                     | Commit  | Files                                       |
| ---- | -------------------------------------------------------- | ------- | ------------------------------------------- |
| 1    | Fix stale health URL in test_middleware.py               | 5f9c12c | apps/api/tests/core/test_middleware.py      |
| 2    | Add Redis cache/session env vars to Docker Compose files | d7f5918 | docker-compose.yml, docker-compose.prod.yml |

## What Was Built

### Task 1: Fix stale health URL

All 4 occurrences of `/api/v1/health` in `apps/api/tests/core/test_middleware.py` were replaced with `/api/health/live`. The `/api/health/live` endpoint was wired in Phase 15 as a plain Django view (not Ninja) returning 200/503 for liveness probes. The old URL returned 404, causing `test_context_has_duration_ms` to fail (`assert 404 in (200, 503)` was False).

### Task 2: Add Redis cache/session env vars

Added `CACHE_REDIS_URL: redis://redis:6379/1` and `SESSION_REDIS_URL: redis://redis:6379/2` to:

- `docker-compose.yml`: `celery-worker` and `celery-beat` services
- `docker-compose.prod.yml`: `api`, `celery` (worker), and `celery-beat` services

Also added `OTEL_EXPORTER_OTLP_ENDPOINT: http://jaeger:4317` to `celery-beat` in `docker-compose.yml` for parity with `celery-worker` (Jaeger is dev-only).

Without these env vars, `CACHE_REDIS_URL` and `SESSION_REDIS_URL` resolved to `localhost` inside containers, pointing to the container itself rather than the `redis` service — causing Django cache and session backend timeouts.

## Verification

```
4 passed, 1 warning in 2.75s
grep -c "CACHE_REDIS_URL" docker-compose.yml     → 2 (worker + beat)
grep -c "CACHE_REDIS_URL" docker-compose.prod.yml → 3 (api + celery + beat)
```

## Deviations from Plan

None - plan executed exactly as written.

## Self-Check: PASSED

- apps/api/tests/core/test_middleware.py: modified, all 4 tests pass
- docker-compose.yml: 2 occurrences of CACHE_REDIS_URL (celery-worker + celery-beat)
- docker-compose.prod.yml: 3 occurrences of CACHE_REDIS_URL (api + celery + celery-beat)
- Commit 5f9c12c: FOUND
- Commit d7f5918: FOUND
