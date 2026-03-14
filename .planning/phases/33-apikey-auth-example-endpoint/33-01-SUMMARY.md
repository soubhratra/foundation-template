---
phase: 33-apikey-auth-example-endpoint
plan: 01
subsystem: testing
tags: [api-keys, pytest, integration-tests, tdd, rate-limiting, scopes]

# Dependency graph
requires:
  - phase: 28-api-key-authentication
    provides: ApiKeyAuth, RequireScope, ApiKeyRateLimitMiddleware, APIKey model, conftest fixtures
provides:
  - RED integration test scaffold for GET /api/v1/me/api-keys/ping/ (8 test methods)
affects:
  - 33-02 (must turn these tests GREEN by implementing ping endpoint)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Rate limit tests use @override_settings(RATELIMIT_ENABLE=True) to override global RATELIMIT_ENABLE=False autouse fixture"
    - "Scope enforcement tested by creating a key with wrong scopes inline (no fixture)"

key-files:
  created:
    - apps/api/tests/api_keys/test_ping.py
  modified: []

key-decisions:
  - "8 test methods (not 6 as stated in objective): includes test_invalid_key_returns_401 and test_no_auth_returns_401 as auth-failure sanity cases per done criteria"
  - "test_wrong_scope_returns_403 creates user+key inline rather than using api_key fixture — fixture has read+write scopes; test needs write-only key"

patterns-established:
  - "Ping endpoint URL constant: URL = '/api/v1/me/api-keys/ping/' — defines test contract for Plan 02 implementation"

requirements-completed:
  - AKEY-01
  - AKEY-02
  - AKEY-03

# Metrics
duration: 5min
completed: 2026-03-14
---

# Phase 33 Plan 01: ApiKey Ping Endpoint RED Tests Summary

**8-test RED scaffold covering AKEY-01/02/03: scope enforcement, rate limit headers, usage tracking, and auth failure cases for GET /api/v1/me/api-keys/ping/**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-14T00:13:53Z
- **Completed:** 2026-03-14T00:15:00Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Created `apps/api/tests/api_keys/test_ping.py` with `TestApiKeyPingEndpoint` class (8 test methods)
- All 8 tests fail RED with 405 Method Not Allowed (route exists as DELETE-only; GET not yet defined)
- Imports resolve cleanly — no ImportError, no syntax errors
- Rate limit tests correctly use `@override_settings(RATELIMIT_ENABLE=True)` to override global test isolation fixture

## Task Commits

Each task was committed atomically:

1. **Task 1: Write RED integration tests for the ping endpoint** - `49a331d` (test)

**Plan metadata:** _(docs commit follows)_

## Files Created/Modified

- `apps/api/tests/api_keys/test_ping.py` - 8-test integration class for the ping endpoint; covers AKEY-01 (scope enforcement + session auth rejection), AKEY-02 (rate limit headers + 429), AKEY-03 (usage tracking)

## Decisions Made

- `test_wrong_scope_returns_403` creates a fresh user + key inline with `scopes=["write"]` rather than adapting the `api_key` fixture (which has `read+write`) — inline creation keeps the fixture contract stable and the intent explicit
- Test file includes 8 methods (not 6): plan objective said 6 but done criteria said 8 and the plan template listed 8; 8 is correct per the verification section

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- RED scaffold complete; Plan 33-02 adds the `GET /api/v1/me/api-keys/ping/` route to `APIKeyController` to turn these tests GREEN
- All fixture dependencies (`api_user`, `api_key`) already present in `tests/api_keys/conftest.py` — no conftest changes needed

---

_Phase: 33-apikey-auth-example-endpoint_
_Completed: 2026-03-14_
