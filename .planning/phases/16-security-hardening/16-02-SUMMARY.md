---
phase: 16-security-hardening
plan: 02
subsystem: infra
tags: [django-redis, django-ratelimit, redis, rate-limiting, caching, sessions, middleware]

# Dependency graph
requires:
  - phase: 16-01
    provides: RED test stubs for SEC-01 and SEC-03 in test_security.py

provides:
  - django-redis CACHES config (DB1 default, DB2 sessions) in base.py
  - SESSION_ENGINE + SESSION_CACHE_ALIAS wired to Redis sessions backend
  - RATELIMIT_* settings block (RATELIMIT_AUTH_LOGIN, RATELIMIT_ENABLE, RATELIMIT_FAIL_OPEN, RATELIMIT_VIEW)
  - AuthRateLimitMiddleware path-scoped to /api/v1/auth/ routes
  - ratelimited_error() RFC 6585 handler returning JSON 429 + Retry-After: 60
  - test_isolation_settings autouse fixture (LocMemCache + RATELIMIT_ENABLE=False)
  - SEC-01 and SEC-03 tests GREEN in test_security.py

affects:
  - 16-03 (SEC-02 security headers plan builds on this middleware foundation)
  - All future plans that use Django cache (now Redis-backed in non-test environments)

# Tech tracking
tech-stack:
  added:
    - django-redis==6.0.0
    - django-ratelimit==4.1.0
  patterns:
    - Middleware-based rate limiting for third-party views (not @ratelimit decorator)
    - Test isolation via autouse settings fixture (RATELIMIT_ENABLE=False + LocMemCache)
    - Fail-open rate limiting (RATELIMIT_FAIL_OPEN=True) for auth availability > enforcement
    - Separate Redis DBs per concern: DB0 Celery, DB1 cache, DB2 sessions

key-files:
  created:
    - apps/api/apps/core/ratelimit.py
  modified:
    - apps/api/config/settings/base.py
    - apps/api/apps/core/middleware.py
    - apps/api/tests/conftest.py
    - apps/api/tests/core/test_security.py
    - apps/api/.env.example
    - apps/api/pyproject.toml

key-decisions:
  - "django-redis CACHES placed in base.py (not development.py) — all non-test environments use Redis"
  - "RATELIMIT_FAIL_OPEN=True — auth availability is prioritised over strict enforcement during Redis outages"
  - "AuthRateLimitMiddleware returns ratelimited_error directly (not raise Ratelimited()) — avoids Django's default 403 handler for Ratelimited exceptions"
  - "test_isolation_settings autouse fixture disables rate limits + uses LocMemCache — no Redis in CI"
  - "Separate env vars CACHE_REDIS_URL + SESSION_REDIS_URL (not string manipulation on REDIS_URL DB 0)"

patterns-established:
  - "Middleware-based rate limiting: apply is_ratelimited() in middleware for third-party views that cannot use @ratelimit decorator"
  - "Test isolation pattern: autouse fixture overrides settings.CACHES + settings.RATELIMIT_ENABLE per test"

requirements-completed: [SEC-01, SEC-03]

# Metrics
duration: 5min
completed: 2026-03-11
---

# Phase 16 Plan 02: Redis Cache, Session Backend, and Auth Rate Limiting Summary

**django-redis CACHES on DB1+DB2, SESSION_ENGINE=cache, and AuthRateLimitMiddleware returning JSON 429 with Retry-After; SEC-01 and SEC-03 tests GREEN**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-11T20:54:27Z
- **Completed:** 2026-03-11T20:59:30Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- Installed django-redis 6.0.0 and django-ratelimit 4.1.0 as runtime dependencies
- Wired Redis DB1 as Django default cache and DB2 as sessions backend in base.py
- Created AuthRateLimitMiddleware (path-scoped to /api/v1/auth/) that returns JSON 429 + Retry-After
- Added test_isolation_settings autouse fixture — all tests use LocMemCache and RATELIMIT_ENABLE=False
- Turned 5 RED stubs GREEN: test_rate_limit_returns_429, test_rate_limit_retry_after_header, test_rate_limit_uses_redis_cache, test_default_cache_is_redis, test_session_cache_is_redis

## Task Commits

Each task was committed atomically:

1. **Task 1: Install packages and create ratelimit.py handler** - `69e8aa5` (feat)
2. **Task 2: Wire CACHES, SESSION backend, rate limiting settings + AuthRateLimitMiddleware** - `f87c220` (feat)

**Plan metadata:** TBD (docs: complete plan)

## Files Created/Modified

- `apps/api/apps/core/ratelimit.py` - RFC 6585 compliant 429 handler with Retry-After: 60 header
- `apps/api/config/settings/base.py` - CACHES dict (django*redis DB1+DB2), SESSION_ENGINE, RATELIMIT*\* block, AuthRateLimitMiddleware in MIDDLEWARE
- `apps/api/apps/core/middleware.py` - Added AuthRateLimitMiddleware class with is_ratelimited() path-scoped logic
- `apps/api/tests/conftest.py` - Added test_isolation_settings autouse fixture
- `apps/api/tests/core/test_security.py` - Replaced SEC-01 + SEC-03 stubs with real implementations
- `apps/api/.env.example` - Added CACHE_REDIS_URL and SESSION_REDIS_URL entries
- `apps/api/pyproject.toml` - Added django-redis==6.0.0 and django-ratelimit==4.1.0

## Decisions Made

- **Middleware returns response directly (not raise Ratelimited()):** When `Ratelimited` is raised, Django's default handler returns 403, not 429. To get a proper JSON 429 response, the middleware calls `ratelimited_error(request)` and returns its response directly. This avoids Django's exception handling path entirely.
- **RATELIMIT_FAIL_OPEN=True:** Auth endpoint availability is prioritised over strict rate limit enforcement. If Redis is unreachable, requests pass through rather than blocking all auth.
- **Separate Redis DBs:** CACHE_REDIS_URL (DB1) and SESSION_REDIS_URL (DB2) are separate env vars to avoid string manipulation on REDIS_URL (DB0 Celery). Avoids Pitfall 4 from research notes.
- **test_isolation_settings is autouse:** Every test automatically gets LocMemCache and RATELIMIT_ENABLE=False without requiring explicit fixture use. Rate limit tests that need enforcement use `override_settings(RATELIMIT_ENABLE=True, ...)`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] AuthRateLimitMiddleware returning response directly instead of raising Ratelimited**

- **Found during:** Task 2 (running tests after implementation)
- **Issue:** Plan specified `raise Ratelimited()` but Django's default handler for `Ratelimited` returns 403 HTML, not the custom JSON 429 handler
- **Fix:** Changed middleware to call `ratelimited_error(request)` and return its response directly instead of raising the exception
- **Files modified:** apps/api/apps/core/middleware.py
- **Verification:** test_rate_limit_returns_429 and test_rate_limit_retry_after_header now PASS
- **Committed in:** f87c220 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - Bug)
**Impact on plan:** Essential fix for correctness — the plan's `raise Ratelimited()` approach produces 403 not 429. Direct return is the correct pattern for middleware-based rate limiting.

## Issues Encountered

- Another agent running Plan 16-03 concurrently had already added CSP/HSTS settings to base.py and production.py. These were staged alongside Task 2 changes where needed (production.py noqa fix) but did not affect the SEC-01/SEC-03 test results.

## User Setup Required

None - no external service configuration required. Redis is already running via docker-compose from Phase 15.

## Next Phase Readiness

- SEC-01 and SEC-03 requirements are GREEN
- AuthRateLimitMiddleware is in MIDDLEWARE and ready for production
- Plan 16-03 can now turn SEC-02 (security headers) stubs GREEN
- The 4 remaining RED stubs in test_security.py (test_csp_header_present, test_hsts_header_production, test_x_frame_options_header, test_referrer_policy_header) are waiting for Plan 16-03

---

_Phase: 16-security-hardening_
_Completed: 2026-03-11_
