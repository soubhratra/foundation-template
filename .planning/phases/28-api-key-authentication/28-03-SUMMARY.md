---
phase: 28-api-key-authentication
plan: 03
subsystem: auth
tags: [api-keys, django-ninja-extra, sha256, hmac, bearer-token, permissions]

# Dependency graph
requires:
  - phase: 28-02
    provides: APIKey model with generate_key() and migration — data foundation for auth lookup
  - phase: 28-01
    provides: RED test suite for api_keys (test_auth.py, test_controllers.py, conftest.py)
provides:
  - ApiKeyAuth HttpBearer backend (resolves Bearer token to User, sets request.api_key)
  - RequireScope permission class (rejects session-only requests, enforces scope membership)
  - APIKeyIn / APIKeyOut / APIKeyCreateOut schemas (validated scopes, raw key shown once)
  - APIKeyService.create(), revoke(), list_for_user() service methods
  - APIKeyController at /me/api-keys/ with POST/GET/DELETE endpoints
  - All 27 tests GREEN (test_auth.py: 10, test_controllers.py: 7, test_models.py: 6, test_checks.py: 4)
affects: [28-04, 29-org-api-keys]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "HttpBearer subclass with authenticate() returning None on failure — never raises"
    - "hmac.compare_digest for timing-safe hash comparison (defense-in-depth)"
    - "request.api_key set in authenticate() — consumed by RequireScope downstream"
    - "Partial UPDATE via .filter(pk=).update() for usage tracking — avoids full-model lock"
    - "api_key.refresh_from_db(fields=[...]) after partial UPDATE for accurate in-memory state"
    - "Route paths with trailing slash '/' to match test contract URLs"
    - "raise Http404 from None in service layer — clean exception chaining for ruff B904"

key-files:
  created:
    - apps/api/apps/api_keys/auth.py
    - apps/api/apps/api_keys/schemas.py
    - apps/api/apps/api_keys/services.py
    - apps/api/apps/api_keys/controllers.py

key-decisions:
  - "Route paths use trailing slash ('/' not '') — test contract URLs have trailing slash; Django Ninja preserves literal path string"
  - "RequireScope raises PermissionDenied (not returns False) for session-only requests — ensures 403 not 401 per AKEY-01 spec"
  - "Management controller uses session auth only — ApiKeyAuth is for product endpoints, not key management"
  - "list_for_user returns all keys (active + inactive) — user should see revoked keys in management UI"

patterns-established:
  - "Auth backend pattern: HttpBearer subclass, authenticate() catches DoesNotExist, returns None"
  - "Permission class pattern: raise PermissionDenied (not return False) to force 403 not fallthrough"
  - "Service layer: @classmethod methods, no business logic in controllers"

requirements-completed: [AKEY-01, AKEY-03]

# Metrics
duration: 18min
completed: 2026-03-13
---

# Phase 28 Plan 03: Auth Backend, Schemas, Service, Controller Summary

**ApiKeyAuth HttpBearer backend with hmac.compare_digest, RequireScope permission class, and /me/api-keys/ CRUD endpoints — 27/27 tests GREEN, AKEY-01 and AKEY-03 satisfied**

## Performance

- **Duration:** ~18 min
- **Started:** 2026-03-13T12:46:00Z
- **Completed:** 2026-03-13T13:04:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- ApiKeyAuth.authenticate() resolves Bearer token via SHA-256 hash lookup, sets request.api_key and request.user, updates last_used_at + usage_count via partial UPDATE
- RequireScope permission class raises PermissionDenied for session-only requests (no api_key fallback) and for keys missing the required scope
- APIKeyController at /me/api-keys/ with POST (201 + raw key), GET (list, no raw key), DELETE (204, is_active=False)
- 27/27 tests GREEN across all four test files

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement ApiKeyAuth backend and RequireScope** - `8823e15` (feat)
2. **Task 2: Schemas, service, controller** - `de09abd` (feat)

## Files Created/Modified

- `apps/api/apps/api_keys/auth.py` — ApiKeyAuth HttpBearer backend and RequireScope permission class
- `apps/api/apps/api_keys/schemas.py` — APIKeyIn (with scope validation), APIKeyCreateOut (with key), APIKeyOut (without key)
- `apps/api/apps/api_keys/services.py` — APIKeyService.create(), revoke(), list_for_user()
- `apps/api/apps/api_keys/controllers.py` — APIKeyController at /me/api-keys/ with POST/GET/DELETE

## Decisions Made

- Route paths use trailing slash (`"/"` not `""`) — the test contract URLs all have trailing slashes (`/api/v1/me/api-keys/`), and Django Ninja preserves the literal route path string from `@route.post("/", ...)`. Using `""` caused 404s; using `"/"` matches the test URLs.
- RequireScope raises `PermissionDenied` (not `return False`) — raising forces a 403 response immediately without fallthrough to other permission checks. This is the correct behavior for AKEY-01 (session-only requests must be rejected, not silently allowed via other backends).
- Management controller uses session auth only — the `APIKeyController` for creating/listing/revoking keys is for the web UI (session-authenticated). `ApiKeyAuth` is for product endpoints that accept key-based access.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Route paths corrected from `""` to `"/"` (trailing slash)**

- **Found during:** Task 2 (test_controllers.py verification)
- **Issue:** Tests hit `/api/v1/me/api-keys/` (with trailing slash) but `@route.post("")` registered route as `/api/v1/me/api-keys` (no slash), causing 404 on all controller tests
- **Fix:** Changed `@route.post("")` to `@route.post("/")`, `@route.get("")` to `@route.get("/")`, and `@route.delete("/{key_id}")` to `@route.delete("/{key_id}/")`
- **Files modified:** apps/api/apps/api_keys/controllers.py
- **Verification:** 7/7 test_controllers.py tests pass after fix
- **Committed in:** de09abd (Task 2 commit)

**2. [Rule 1 - Bug] ruff B904 — raise Http404 from None in services.py**

- **Found during:** Task 2 commit (pre-commit hook)
- **Issue:** `raise Http404` inside `except` clause fails ruff B904 (must use `raise ... from err` or `raise ... from None`)
- **Fix:** Changed to `raise Http404 from None` — suppresses exception chaining, which is correct since Http404 is a deliberate control-flow signal, not an error propagation
- **Files modified:** apps/api/apps/api_keys/services.py
- **Verification:** ruff passes on re-commit
- **Committed in:** de09abd (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Both fixes necessary for correct behavior. No scope creep.

## Issues Encountered

- ruff-format reformatted auth.py on first commit attempt (long lines in select_related call), requiring re-stage and re-commit. Standard pre-commit hook behavior.

## Next Phase Readiness

- ApiKeyAuth and RequireScope ready for Plan 28-04 (rate limiting middleware)
- All 27 api_keys tests GREEN; manage.py check clean of api_keys.\* warnings
- Controller endpoints verified working end-to-end via integration tests

---

_Phase: 28-api-key-authentication_
_Completed: 2026-03-13_

## Self-Check: PASSED

- FOUND: apps/api/apps/api_keys/auth.py
- FOUND: apps/api/apps/api_keys/schemas.py
- FOUND: apps/api/apps/api_keys/services.py
- FOUND: apps/api/apps/api_keys/controllers.py
- FOUND: .planning/phases/28-api-key-authentication/28-03-SUMMARY.md
- FOUND: commit 8823e15 (Task 1)
- FOUND: commit de09abd (Task 2)
