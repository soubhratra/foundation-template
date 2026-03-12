---
phase: 20-social-auth
plan: "03"
subsystem: auth
tags: [jwt, apple-signin, jwks, pyjwt, social-auth, ios, expo, django-ninja-extra]

# Dependency graph
requires:
  - phase: 20-01
    provides: RED test stubs for verify_apple_identity_token() and handle_apple_login() in test_apple_auth.py
  - phase: 20-02
    provides: SOCIAL AUTH MODULE settings block with _APPLE_CLIENT_ID env read and allauth.socialaccount.providers.apple registration
provides:
  - apps/accounts/apple_auth.py with verify_apple_identity_token(), handle_apple_login(), and _fetch_apple_jwks()
  - POST /api/v1/auth/apple/ endpoint via AppleSignInController in accounts/controllers.py
  - Apple JWKS caching with 1-hour TTL and key rotation retry on InvalidSignatureError
affects: [20-04, 20-05, 20-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Apple JWKS cache-bust-on-invalid-signature: if verify fails with cached key, delete cache key and retry once — handles key rotation without downtime, also fixes test isolation (same kid, different test keys)"
    - "handle_apple_login() pure function in apple_auth.py: separates JWT verification (apple_auth.py) from HTTP transport (controllers.py) — testable without HTTP stack"
    - "AppleSignInController uses django_login() + JWTTokenStrategy.create_access_token_payload() fallback to jwt_internal.create_access_token() for token issuance after Apple Sign In"

key-files:
  created:
    - apps/api/apps/accounts/apple_auth.py
  modified:
    - apps/api/apps/accounts/controllers.py

key-decisions:
  - "handle_apple_login() lives in apple_auth.py (not controllers.py) — test_apple_auth.py imports it directly; keeping it in apple_auth.py satisfies both tests and controller"
  - "JWKS cache-bust-on-InvalidSignatureError: retry once on signature failure (not only on kid-not-found) — this handles both production key rotation AND test isolation where same kid maps to different key pairs across tests"
  - "AppleSignInController uses django_login() before token issuance — allauth JWT strategy requires request.session.session_key, so login() must be called first to create the session"
  - "full_name split on whitespace: first_name stores only the given name (first word) — matches test assertion (full_name='Alice Smith' -> first_name='Alice')"
  - "JWTTokenStrategy.create_access_token_payload() returns None when SessionAwareJWTTokenStrategy sees no Authorization header — fallback to jwt_internal.create_access_token() directly with the active session"

patterns-established:
  - "Apple Sign In JWT endpoint: verify_apple_identity_token() + handle_apple_login() + django_login() + JWTTokenStrategy flow — all in accounts app, no new Django app needed"
  - "JWKS cache-bust retry pattern: InvalidSignatureError -> delete cache -> re-fetch -> retry verification (once) — handles key rotation + test isolation"

requirements-completed:
  - SOCIAL-03

# Metrics
duration: 18min
completed: 2026-03-12
---

# Phase 20 Plan 03: Apple Sign In JWT Verification Summary

**Custom Apple Sign In endpoint: RS256 JWT verification against Apple JWKS with SOCIAL-03-compliant user find-or-create, name persistence, and JWT token issuance**

## Performance

- **Duration:** 18 min
- **Started:** 2026-03-12T12:10:00Z
- **Completed:** 2026-03-12T12:28:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- `apple_auth.py` with `verify_apple_identity_token()` (JWKS-cached RS256 JWT verification with key-rotation retry) and `handle_apple_login()` (user find-or-create with SocialAccount linkage and name persistence)
- `POST /api/v1/auth/apple/` endpoint via `AppleSignInController` — auto-discovered by `api.auto_discover_controllers()`, returns 400 on invalid token, 200 with `{access, refresh}` JWT tokens on success
- All 5 `test_apple_auth.py` tests GREEN — JWT verifier, audience rejection, valid token acceptance, first-login name persistence, return-login non-overwrite

## Task Commits

Each task was committed atomically:

1. **Task 1: Apple JWT verifier (apple_auth.py)** - `babe9ae` then `fd9324b` (feat — initial + key rotation fix)
2. **Task 2: AppleSignInController endpoint + name persistence** - `b852f3a` (feat)

_Note: Task 1 had two commits — initial implementation and JWKS cache-bust-on-InvalidSignatureError fix (auto-fix Rule 1)_

## Files Created/Modified

- `apps/api/apps/accounts/apple_auth.py` — Created: `verify_apple_identity_token()`, `handle_apple_login()`, `_fetch_apple_jwks()`, `_get_public_key_for_kid()` with key rotation retry
- `apps/api/apps/accounts/controllers.py` — Modified: `AppleSignInController` with `POST /auth/apple/` endpoint, `AppleSignInRequest`/`AppleSignInResponse` schemas, SOCIAL AUTH MODULE sentinel comments

## Decisions Made

- **JWKS cache-bust-on-InvalidSignatureError**: When signature verification fails with the cached public key, the JWKS cache is cleared and verification retried once. This handles both production Apple key rotation AND test isolation (where two tests use the same `kid="test-kid"` but different RSA key pairs — the second test's mock would never be called without a cache bust)
- **handle_apple_login() in apple_auth.py** (not controller): The test file imports it directly from `apps.accounts.apple_auth`, so it must live there. The controller delegates to it
- **AppleSignInController uses django_login()**: allauth's `JWTTokenStrategy.create_access_token()` requires `request.session.session_key` — calling `django_login(request, user)` establishes the session before token issuance
- **JWTTokenStrategy fallback to jwt_internal**: `SessionAwareJWTTokenStrategy.create_access_token_payload()` returns `None` for requests without an `Authorization` header (session-based flow protection). For Apple Sign In, we call `jwt_internal.create_access_token()` directly using the established session

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] JWKS cache invalidation on InvalidSignatureError for test isolation**

- **Found during:** Task 1 (Apple JWT verifier)
- **Issue:** Both `test_verify_identity_token_rejects_wrong_audience` and `test_verify_identity_token_accepts_valid_token` use `kid="test-kid"` but different RSA key pairs. The wrong-audience test populates the LocMemCache with JWKS for key1. The valid-token test generates key2 but the mock for `requests.get` is never called because the cached JWKS (key1) is returned first — signature verification fails with `InvalidSignatureError`
- **Fix:** Added cache-bust-on-InvalidSignatureError retry in `verify_apple_identity_token()`: on `InvalidSignatureError`, delete the JWKS cache key, re-fetch (calls the mock with key2), and retry verification. This also handles production Apple key rotation
- **Files modified:** apps/api/apps/accounts/apple_auth.py
- **Verification:** `uv run pytest tests/test_apple_auth.py -q` → 5 passed
- **Committed in:** fd9324b (Task 1 fix commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - Bug)
**Impact on plan:** Fix required for test correctness and also improves production key rotation handling. No scope creep.

## Issues Encountered

- Pre-commit ruff reordered imports and reformatted `Optional[str]` to `str | None` — both commits required a re-stage after hook modification. Expected behavior.

## Next Phase Readiness

- `verify_apple_identity_token` and `handle_apple_login` are exported from `apps.accounts.apple_auth` and importable by any future plans
- `POST /api/v1/auth/apple/` is live and auto-discovered — integration tests can use it directly
- Plan 20-04 (social adapter) can proceed — `FoundationSocialAccountAdapter` already exists at `apps.accounts.social_adapter` (from pre-existing fix commit `e7927ea`)

## Self-Check: PASSED

- apps/api/apps/accounts/apple_auth.py: FOUND
- apps/api/apps/accounts/controllers.py: FOUND (AppleSignInController)
- Commit babe9ae: FOUND
- Commit fd9324b: FOUND
- Commit b852f3a: FOUND

---

_Phase: 20-social-auth_
_Completed: 2026-03-12_
