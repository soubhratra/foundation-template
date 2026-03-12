---
phase: quick
plan: 1
type: execute
wave: 1
depends_on: []
files_modified:
  - apps/api/tests/core/test_middleware.py
  - docker-compose.yml
  - docker-compose.prod.yml
autonomous: true
requirements: []

must_haves:
  truths:
    - "test_context_has_duration_ms passes (status_code 200 not 404)"
    - "All four middleware tests pass against /api/health/live"
    - "celery-worker and celery-beat in dev compose reach Redis cache/session backends via correct hostname"
    - "api, celery, celery-beat in prod compose reach Redis cache/session backends via correct hostname"
  artifacts:
    - path: apps/api/tests/core/test_middleware.py
      provides: Updated middleware tests using correct health URL
      contains: /api/health/live
    - path: docker-compose.yml
      provides: Dev compose with CACHE_REDIS_URL and SESSION_REDIS_URL env vars
      contains: "CACHE_REDIS_URL: redis://redis:6379/1"
    - path: docker-compose.prod.yml
      provides: Prod compose with CACHE_REDIS_URL and SESSION_REDIS_URL env vars
      contains: "CACHE_REDIS_URL: redis://redis:6379/1"
  key_links:
    - from: apps/api/tests/core/test_middleware.py
      to: /api/health/live
      via: Django test client GET
      pattern: /api/health/live
    - from: docker-compose.yml celery-worker/celery-beat
      to: redis service
      via: CACHE_REDIS_URL env var
      pattern: "redis://redis:6379"
---

<objective>
Fix two integration gaps found in the v1.2 milestone audit that cause test failures and
container runtime errors.

Purpose: Unblock CI (BREAK-1: stale test URL causes one middleware test to fail with 404)
and prevent cache/session backend timeouts in Docker deployments (BREAK-2: localhost Redis
URL inside containers resolves to the container itself, not the redis service).

Output: Updated test file + both compose files with correct Redis env vars.
</objective>

<execution_context>
@/Users/soubhratra/.claude/get-shit-done/workflows/execute-plan.md
@/Users/soubhratra/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Fix stale health URL in test_middleware.py</name>
  <files>apps/api/tests/core/test_middleware.py</files>
  <action>
    Replace every occurrence of `/api/v1/health` with `/api/health/live` in
    apps/api/tests/core/test_middleware.py.

    There are exactly 4 occurrences — one per test function (test_request_id_header,
    test_request_id_is_uuid4, test_context_has_duration_ms, test_context_isolation).

    The new URL `/api/health/live` was wired in Phase 15. It returns 200 when healthy.
    test_context_has_duration_ms asserts `status_code in (200, 503)` — both are valid
    outcomes for a liveness probe, so no assertion change is needed.

  </action>
  <verify>
    <automated>cd /Users/soubhratra/workspace/foundation-template/apps/api && python -m pytest tests/core/test_middleware.py -v 2>&1 | tail -20</automated>
  </verify>
  <done>All 4 tests in test_middleware.py pass. No occurrence of /api/v1/health remains in the file.</done>
</task>

<task type="auto">
  <name>Task 2: Add Redis cache/session env vars to Docker Compose files</name>
  <files>docker-compose.yml, docker-compose.prod.yml</files>
  <action>
    **docker-compose.yml** — add to the `environment:` block of both `celery-worker`
    and `celery-beat` services:

    ```yaml
    CACHE_REDIS_URL: redis://redis:6379/1
    SESSION_REDIS_URL: redis://redis:6379/2
    ```

    Also add to `celery-beat` (missing from that service, present on celery-worker):

    ```yaml
    OTEL_EXPORTER_OTLP_ENDPOINT: http://jaeger:4317
    ```

    Note: dev compose has no `api` service (Django runs outside Docker via manage.py
    runserver); only celery-worker and celery-beat need these vars in dev.

    **docker-compose.prod.yml** — add to the `environment:` block of `api`, `celery`
    (the worker service, named `celery` not `celery-worker` in prod), and `celery-beat`:

    ```yaml
    CACHE_REDIS_URL: redis://redis:6379/1
    SESSION_REDIS_URL: redis://redis:6379/2
    ```

    Do NOT add OTEL vars to prod compose — Jaeger is a dev-only service and does not
    appear in docker-compose.prod.yml.

    Preserve all existing env vars and indentation style in both files.

  </action>
  <verify>
    <automated>grep -n "CACHE_REDIS_URL\|SESSION_REDIS_URL\|OTEL_EXPORTER_OTLP_ENDPOINT" /Users/soubhratra/workspace/foundation-template/docker-compose.yml /Users/soubhratra/workspace/foundation-template/docker-compose.prod.yml</automated>
  </verify>
  <done>
    docker-compose.yml: CACHE_REDIS_URL and SESSION_REDIS_URL appear under both
    celery-worker and celery-beat; OTEL_EXPORTER_OTLP_ENDPOINT appears under
    celery-beat (in addition to the existing entry under celery-worker).

    docker-compose.prod.yml: CACHE_REDIS_URL and SESSION_REDIS_URL appear under
    api, celery, and celery-beat.

  </done>
</task>

</tasks>

<verification>
After both tasks complete, run the full middleware test suite and confirm no stale URLs remain:

```bash
cd /Users/soubhratra/workspace/foundation-template/apps/api
python -m pytest tests/core/test_middleware.py -v
grep -rn "api/v1/health" tests/core/test_middleware.py  # should return nothing
```

Spot-check compose files:

```bash
grep -c "CACHE_REDIS_URL" docker-compose.yml        # expect 2 (worker + beat)
grep -c "CACHE_REDIS_URL" docker-compose.prod.yml   # expect 3 (api + celery + beat)
```

</verification>

<success_criteria>

- All 4 tests in test_middleware.py pass
- No occurrence of `/api/v1/health` in tests/core/test_middleware.py
- CACHE_REDIS_URL and SESSION_REDIS_URL present in celery-worker and celery-beat in docker-compose.yml
- CACHE_REDIS_URL and SESSION_REDIS_URL present in api, celery, and celery-beat in docker-compose.prod.yml
- OTEL_EXPORTER_OTLP_ENDPOINT added to celery-beat in docker-compose.yml
  </success_criteria>

<output>
After completion, create `.planning/quick/1-fix-stale-test-url-in-test-middleware-py/1-SUMMARY.md`
</output>
