---
phase: 28-api-key-authentication
plan: 01
subsystem: testing
tags: [api-keys, tdd, pytest, django, sha256, rate-limiting]

# Dependency graph
requires:
  - phase: 27-outbound-webhooks
    provides: RED trigger pattern (__init__.py module-level import) and lazy fixture pattern used as template
provides:
  - RED test suite for api_keys — 7 test files covering AKEY-01, AKEY-02, AKEY-03 behaviors
  - ImportError at collection time until apps.api_keys is implemented
  - Named test functions for every requirement behavior, targetable individually
affects:
  - 28-02-model-and-migration
  - 28-03-auth-backend-and-scope
  - 28-04-controllers-and-endpoints

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Module-level import in tests/__init__.py as RED trigger — causes ImportError at collection time, confirmed before implementation ships"
    - "Lazy imports inside fixture bodies in conftest.py — prevents double-import errors while keeping __init__.py as the single RED trigger"
    - "@override_settings(RATELIMIT_ENABLE=True) on all rate limit tests — overrides global test_isolation_settings autouse fixture that sets RATELIMIT_ENABLE=False"

key-files:
  created:
    - apps/api/tests/api_keys/__init__.py
    - apps/api/tests/api_keys/conftest.py
    - apps/api/tests/api_keys/test_models.py
    - apps/api/tests/api_keys/test_auth.py
    - apps/api/tests/api_keys/test_ratelimit.py
    - apps/api/tests/api_keys/test_controllers.py
    - apps/api/tests/api_keys/test_checks.py
  modified: []

key-decisions:
  - "Phase 28 RED trigger: __init__.py imports from apps.api_keys.models at module level — collection fails with ModuleNotFoundError until Wave 1 ships"
  - "conftest.py fixtures use lazy imports inside fixture bodies (same pattern as tests/webhooks/conftest.py) to avoid double-import conflicts while __init__.py remains the RED trigger"
  - "@override_settings(RATELIMIT_ENABLE=True) required on all rate limit tests — global autouse fixture sets RATELIMIT_ENABLE=False which silences rate limit behavior"

patterns-established:
  - "RED trigger: Module-level import in tests/api_keys/__init__.py ensures entire package fails at collection, not just individual tests"
  - "Fixture pattern: conftest.py api_key fixture attaches _raw_key as instance attribute after creation — tests that send Bearer tokens use key._raw_key"

requirements-completed:
  - AKEY-01
  - AKEY-02
  - AKEY-03

# Metrics
duration: 2min
completed: 2026-03-13
---

# Phase 28 Plan 01: API Key Authentication RED Test Suite Summary

**7 pytest stubs covering APIKey lifecycle (AKEY-01), rate limiting (AKEY-02), and usage tracking (AKEY-03) with ModuleNotFoundError at collection time confirming RED state before implementation**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-13T12:35:56Z
- **Completed:** 2026-03-13T12:38:42Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- Created `tests/api_keys/__init__.py` with module-level import as RED trigger — collection fails with `ModuleNotFoundError: No module named 'apps.api_keys'` until Wave 1 implementation ships
- Created `conftest.py` with `api_user`, `api_key`, and `revoked_api_key` fixtures using lazy imports inside fixture bodies (mirrors webhooks pattern)
- Created 5 test files (test_models, test_auth, test_ratelimit, test_controllers, test_checks) with named test functions for every AKEY-01/02/03 behavior

## Task Commits

Each task was committed atomically:

1. **Task 1: Create test module RED trigger and conftest fixtures** - `80315a0` (test)
2. **Task 2: Write RED test stubs — models, auth, ratelimit, controllers, checks** - `f0cec20` (test)

## Files Created/Modified

- `apps/api/tests/api_keys/__init__.py` - Module-level import RED trigger (`from apps.api_keys.models import APIKey`)
- `apps/api/tests/api_keys/conftest.py` - Shared fixtures: api_user, api_key (with \_raw_key), revoked_api_key
- `apps/api/tests/api_keys/test_models.py` - APIKey.generate*key() unit tests: three-tuple, prefix format (ft* + 8 chars), SHA-256 hash, raw key not stored in DB
- `apps/api/tests/api_keys/test_auth.py` - ApiKeyAuth and RequireScope tests: valid/revoked/invalid key, request.api_key set, last_used_at + usage_count updated, scope enforcement
- `apps/api/tests/api_keys/test_ratelimit.py` - ApiKeyRateLimitMiddleware tests: X-RateLimit-\* headers present, 429 on limit exceeded, no headers for session requests (all with RATELIMIT_ENABLE=True override)
- `apps/api/tests/api_keys/test_controllers.py` - HTTP endpoint tests: POST returns raw key once, GET hides raw key, DELETE sets is_active=False, 422 for invalid/empty scopes, usage fields in list
- `apps/api/tests/api_keys/test_checks.py` - manage.py check tests: valid scopes passes, None scopes → W001, list scopes → W002, missing description → W003

## Decisions Made

- Module-level import in `__init__.py` confirmed as the canonical RED trigger pattern (follows Phase 27 webhooks approach)
- Lazy imports inside conftest fixture bodies prevent double-import errors while keeping `__init__.py` as the sole RED trigger
- `@override_settings(RATELIMIT_ENABLE=True)` on all rate limit tests is mandatory — the global `test_isolation_settings` autouse fixture in `tests/conftest.py` sets `RATELIMIT_ENABLE=False`, which silences rate limiting and makes `get_usage()` return None

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

Ruff auto-formatted files on two pre-commit hook runs (added blank lines after docstrings, reordered imports). Files were re-staged after each formatting pass and commits succeeded on the second attempt.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- RED state confirmed: `uv run pytest tests/api_keys/ -x -q` fails with `ModuleNotFoundError: No module named 'apps.api_keys'`
- Wave 1 (Plan 28-02) can now implement the `apps/api_keys/` Django app — when models, auth, middleware, controllers, and checks exist the test suite will transition from RED to GREEN
- All AKEY-01, AKEY-02, AKEY-03 behaviors have named test functions that can be targeted individually

---

_Phase: 28-api-key-authentication_
_Completed: 2026-03-13_
