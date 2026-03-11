---
phase: 13-structured-logging-distributed-tracing
plan: 02
subsystem: infra
tags: [structlog, opentelemetry, django, middleware, observability, logging]

# Dependency graph
requires:
  - phase: 13-01
    provides: RED test stubs for OBS-01 + structlog/opentelemetry packages installed
provides:
  - structlog processor (add_otel_context) that injects trace_id/span_id from active OTel span
  - configure_structlog() call at Django startup via CoreConfig.ready()
  - RequestContextMiddleware binding request_id, user_id, method, path, status_code, duration_ms per request
  - X-Request-ID response header on every Django request
  - LOGGING dict in base.py with ConsoleRenderer (DEBUG=True) / JSONRenderer (DEBUG=False)
  - django_structlog in INSTALLED_APPS with DJANGO_STRUCTLOG_CELERY_ENABLED=True
affects:
  - 13-03 (adds configure_otel + DjangoInstrumentor/PsycopgInstrumentor calls to CoreConfig.ready())
  - 13-04 (Celery context propagation depends on django_structlog Celery signals being enabled)
  - 14-01 (PostHog ObservabilityAdapter receives structlog-enriched request context)

# Tech tracking
tech-stack:
  added:
    - django-structlog==10.0.0 (with celery extras)
    - django-ipware==7.0.1 (transitive dep of django-structlog)
  patterns:
    - structlog processor chain ending with ProcessorFormatter.wrap_for_formatter
    - DEBUG-gated renderer: ConsoleRenderer in dev, JSONRenderer in prod — automatic, no env var needed
    - clear_contextvars() before bind_contextvars() to prevent context leak across requests on sync workers
    - OTel fields omitted (not set to None) when no trace is active

key-files:
  created:
    - apps/api/apps/core/logging.py
    - apps/api/apps/core/middleware.py
  modified:
    - apps/api/apps/core/apps.py
    - apps/api/config/settings/base.py
    - apps/api/tests/core/test_middleware.py

key-decisions:
  - "LOGGING dict placed inline in base.py after DEBUG resolution — import structlog with alias _structlog to avoid shadowing user code"
  - "OTel fields (trace_id, span_id) are omitted from event_dict when no span active — not set to null — keeps log parsers clean"
  - "DJANGO_STRUCTLOG_CELERY_ENABLED=True set now even though Celery signals are only exercised in Plan 13-04"
  - "OTEL_EXPORTER_OTLP_ENDPOINT env var added to base.py in this plan so settings load correctly when Plan 13-03 adds configure_otel()"

patterns-established:
  - "CoreConfig.ready() is the single startup hook — all observability initialization goes here"
  - "RequestContextMiddleware inserts after AccountMiddleware so request.user is populated for user_id binding"
  - "X-Request-ID header echoed on every response — enables API clients to self-report request_id in bug reports"

requirements-completed:
  - OBS-01

# Metrics
duration: 12min
completed: 2026-03-11
---

# Phase 13 Plan 02: Structured Logging Implementation Summary

**OTel-aware structlog pipeline wired into Django with per-request UUID injection, DEBUG-automatic renderer switching (ConsoleRenderer dev / JSONRenderer prod), and X-Request-ID response header on every request**

## Performance

- **Duration:** 12 min
- **Started:** 2026-03-11T18:28:02Z
- **Completed:** 2026-03-11T18:40:05Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Implemented `add_otel_context` processor — injects 32-char hex trace_id and 16-char hex span_id when OTel span is active, omits fields entirely when no trace is active
- `RequestContextMiddleware` binds request_id (UUID4), user_id (authenticated PK or "anonymous"), method, path, status_code, duration_ms per request with `clear_contextvars()` guard to prevent cross-request context bleed
- Django LOGGING dict automatically uses ConsoleRenderer (dev) or JSONRenderer (prod) based on DEBUG setting — no extra configuration needed
- 8/8 target tests pass GREEN; 3 pre-existing billing test failures confirmed unrelated to this plan

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement apps/core/logging.py and apps/core/middleware.py** - `19d00e9` (feat)
2. **Task 2: Wire structlog into Django settings and AppConfig.ready()** - `8caf1a0` (feat)

**Plan metadata:** _(final docs commit — this summary)_

## Files Created/Modified

- `apps/api/apps/core/logging.py` - add_otel_context processor + configure_structlog() with full processor chain
- `apps/api/apps/core/middleware.py` - RequestContextMiddleware binding 6 fields per request + X-Request-ID header
- `apps/api/apps/core/apps.py` - CoreConfig.ready() calling configure_structlog() on Django startup
- `apps/api/config/settings/base.py` - LOGGING dict, django_structlog in INSTALLED_APPS, RequestContextMiddleware in MIDDLEWARE, DJANGO_STRUCTLOG_CELERY_ENABLED, OTEL_EXPORTER_OTLP_ENDPOINT
- `apps/api/tests/core/test_middleware.py` - Bug fix: corrected URL from /api/health/live to /api/v1/health

## Decisions Made

- LOGGING dict placed inline in base.py after the `DEBUG = env.bool(...)` line, importing structlog with `_structlog` alias to avoid any user-space shadowing
- OTel trace/span fields omitted (not set to None) when no span is active — clean event_dict for log parsers that don't expect optional OTel fields
- `OTEL_EXPORTER_OTLP_ENDPOINT` env var setting added now (defaulting to empty string) so settings load cleanly when Plan 13-03 adds `configure_otel()` that reads it

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed wrong URL in test_middleware.py stubs from Plan 13-01**

- **Found during:** Task 1 (GREEN phase — running tests after implementation)
- **Issue:** Test stubs (created in Plan 13-01) used `/api/health/live` but the actual health endpoint is at `/api/v1/health` (confirmed via test_health.py and url routing in config/urls.py). Tests returned 404 instead of 200/503.
- **Fix:** Updated all 4 test functions in test_middleware.py to use `/api/v1/health`
- **Files modified:** apps/api/tests/core/test_middleware.py
- **Verification:** All 8 middleware tests pass GREEN after URL correction
- **Committed in:** `19d00e9` (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug in test stubs)
**Impact on plan:** Essential fix — middleware tests could never pass with wrong URL. Consistent with plan intent (tests verify middleware behavior, not URL routing).

## Issues Encountered

- `django-structlog` was not installed in Plan 13-01 (only `structlog` + OTel packages were installed). Installed via `uv add "django-structlog[celery]>=10.0"` at the start of Task 1.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All OBS-01 tests GREEN — structlog pipeline fully operational on every Django request
- CoreConfig.ready() has commented-out stubs for Plan 13-03's configure_otel() / DjangoInstrumentor / PsycopgInstrumentor calls — merge conflict-free landing zone
- OTEL_EXPORTER_OTLP_ENDPOINT setting already in base.py — Plan 13-03 can add tracing.py and call it without touching settings

---

_Phase: 13-structured-logging-distributed-tracing_
_Completed: 2026-03-11_
