---
phase: 33-apikey-auth-example-endpoint
plan: "02"
subsystem: api-keys
tags: [api-keys, auth, ratelimit, ping, tdd]
dependency_graph:
  requires: [33-01]
  provides: [ping-endpoint, full-api-key-auth-chain]
  affects:
    [
      apps/api/apps/api_keys/controllers.py,
      apps/api/apps/api_keys/schemas.py,
      apps/api/apps/api_keys/middleware.py,
    ]
tech_stack:
  added: []
  patterns:
    - "Static route before parametric route to prevent shadowing (ping before /{key_id}/)"
    - "Middleware post-auth api_key detection: request.api_key set inside Ninja view dispatch"
    - "Rate limit enforcement in post-view path via increment=True + replace 429 if should_limit"
key_files:
  created: []
  modified:
    - apps/api/apps/api_keys/schemas.py
    - apps/api/apps/api_keys/controllers.py
    - apps/api/apps/api_keys/middleware.py
    - apps/api/tests/api_keys/test_ping.py
decisions:
  - "ping route must be declared before /{key_id}/ in APIKeyController to avoid route shadowing (405)"
  - "ApiKeyRateLimitMiddleware checks request.api_key after view for Ninja auth pattern (request.api_key not set at middleware entry)"
  - "Post-auth rate limit path uses increment=True then replaces view response with 429 if should_limit"
metrics:
  duration_minutes: 10
  completed_date: "2026-03-14"
  tasks_completed: 2
  files_modified: 4
---

# Phase 33 Plan 02: Ping Endpoint + Full Auth Chain Summary

**One-liner:** GET /api/v1/me/api-keys/ping/ activating ApiKeyAuth -> RequireScope -> ApiKeyRateLimitMiddleware with all 38 tests GREEN.

## Tasks Completed

| Task | Name                                                        | Commit  | Files                                                                             |
| ---- | ----------------------------------------------------------- | ------- | --------------------------------------------------------------------------------- |
| 1    | Add PingOut schema to schemas.py                            | ce8f577 | apps/api/apps/api_keys/schemas.py                                                 |
| 2    | Add ping route to APIKeyController and turn all tests GREEN | 7698c58 | apps/api/apps/api_keys/controllers.py, middleware.py, tests/api_keys/test_ping.py |

## Verification

All 38 tests in `tests/api_keys/` pass:

- test_ping.py: 8 passed (AKEY-01, AKEY-02, AKEY-03)
- test_controllers.py: 7 passed (no regressions)
- test_auth.py: 10 passed (no regressions)
- test_models.py: 6 passed (no regressions)
- test_ratelimit.py: 3 passed (no regressions)
- test_checks.py: 4 passed (no regressions)

`manage.py check` clean (pre-existing allauth deprecation warnings only, unrelated to this plan).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Route ordering: /ping/ shadowed by /{key_id}/**

- **Found during:** Task 2 — first test run returned 405 (DELETE only allowed)
- **Issue:** `/{key_id}/` DELETE route was declared before `/ping/` GET route. Django Ninja resolved `/ping/` as `key_id=ping`, registering it as DELETE-only. GET request returned 405.
- **Fix:** Moved ping route ABOVE revoke_key route in controller class body. Static routes must precede parametric routes when sharing a prefix.
- **Files modified:** apps/api/apps/api_keys/controllers.py
- **Commit:** 7698c58

**2. [Rule 1 - Bug] Middleware post-auth api_key detection**

- **Found during:** Task 2 — test_rate_limit_headers_on_success returned 200 without X-RateLimit-\* headers
- **Issue:** `ApiKeyRateLimitMiddleware.__call__` checked `request.api_key` before calling the view. Django Ninja's `ApiKeyAuth.authenticate()` sets `request.api_key` INSIDE the view dispatch cycle, so it was always None at middleware entry — the middleware short-circuited to passthrough.
- **Fix:** Restructured middleware to call `self.get_response(request)` first, then re-check `request.api_key` after. If set (auth succeeded), call `get_usage(increment=True)` and inject headers. If `should_limit`, replace view response with 429.
- **Files modified:** apps/api/apps/api_keys/middleware.py
- **Commit:** 7698c58

**3. [Rule 1 - Bug] Test missing username in create_user()**

- **Found during:** Task 2 — test_wrong_scope_returns_403 raised TypeError
- **Issue:** `User.objects.create_user(email=..., password=...)` in test_ping.py omitted `username` parameter. The custom user model requires username (conftest.py shows the correct pattern).
- **Fix:** Added `username="scopetest"` to the create_user() call.
- **Files modified:** apps/api/tests/api_keys/test_ping.py
- **Commit:** 7698c58

## Decisions Made

- Static route `/ping/` must be declared before parametric route `/{key_id}/` in Django Ninja controllers to prevent route shadowing.
- `ApiKeyRateLimitMiddleware` uses a dual-path approach: pre-auth (api_key already on request) uses the original block-before-view logic; post-auth (Ninja sets api_key during dispatch) calls view first then enforces + injects headers.
- The `_apply_rate_limit` helper handles the pre-auth path for future use cases where middleware runs after a pre-auth layer.

## Self-Check: PASSED

Files confirmed present:

- apps/api/apps/api_keys/schemas.py — PingOut class added
- apps/api/apps/api_keys/controllers.py — ping route added
- apps/api/apps/api_keys/middleware.py — post-auth path added

Commits confirmed:

- ce8f577 — feat(33-02): add PingOut schema to schemas.py
- 7698c58 — feat(33-02): add ping route to APIKeyController and fix auth chain
