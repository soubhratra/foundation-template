---
phase: 28-api-key-authentication
plan: "04"
subsystem: api
tags: [django-ratelimit, rate-limiting, middleware, api-keys, b2b]

# Dependency graph
requires:
  - phase: 28-02
    provides: APIKey model with prefix field used as rate limit key
  - phase: 28-03
    provides: ApiKeyAuth, RequireScope — API key auth chain for product endpoints
provides:
  - "ApiKeyRateLimitMiddleware — per-key rate enforcement via get_usage() + X-RateLimit-* header injection"
  - "AKEY-02 requirement satisfied — per-key rate limiting with standard response headers"
affects:
  - 29-api-key-scopes
  - any phase adding product API endpoints using ApiKeyAuth

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "ApiKeyRateLimitMiddleware uses get_usage() as single counter source — no header/enforcement drift"
    - "Rate limit key is api_key.prefix (unique per key), not per user or per IP"
    - "B2B_START/B2B_END markers wrap all B2B middleware entries in MIDDLEWARE list"
    - "key= parameter MUST be a callable lambda closure, not a string — django-ratelimit requirement"

key-files:
  created:
    - apps/api/apps/api_keys/middleware.py
  modified:
    - apps/api/config/settings/base.py

key-decisions:
  - "ApiKeyRateLimitMiddleware uses get_usage(increment=True) as sole enforcement point — not ApiKeyAuth.authenticate()"
  - "X-RateLimit-Reset is a Unix epoch timestamp (int(time.time()) + usage['time_left']), not a duration"
  - "Middleware injected inside B2B_START/B2B_END block in MIDDLEWARE list — consistent with template B2B marker convention"

patterns-established:
  - "Pattern: B2B middleware wrapped in B2B_START/B2B_END markers so products can strip entire B2B block cleanly"
  - "Pattern: rate limit key is api_key.prefix, not user.id — one key can be revoked independently"

requirements-completed: [AKEY-02]

# Metrics
duration: 7min
completed: 2026-03-13
---

# Phase 28 Plan 04: ApiKeyRateLimitMiddleware Summary

**Per-key rate limiting middleware using django-ratelimit get_usage(), injecting X-RateLimit-Limit/Remaining/Reset headers on all API key authenticated responses and returning 429 when exceeded**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-13T12:55:00Z
- **Completed:** 2026-03-13T13:02:00Z
- **Tasks:** 1
- **Files modified:** 3 (middleware.py created, base.py + .secrets.baseline modified)

## Accomplishments

- Created `ApiKeyRateLimitMiddleware` that enforces per-key rate limits via `get_usage(increment=True)`
- X-RateLimit-Limit, X-RateLimit-Remaining, and X-RateLimit-Reset headers injected on all API key responses (both 200 and 429)
- Session-authenticated requests (no `request.api_key`) pass through unchanged — no RL headers added
- Middleware wired into MIDDLEWARE list after `AuthRateLimitMiddleware` inside B2B_START/B2B_END markers
- All 3 test_ratelimit.py tests GREEN; all 30 api_keys tests passing

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement ApiKeyRateLimitMiddleware and wire into MIDDLEWARE** - `94667f7` (feat)

## Files Created/Modified

- `apps/api/apps/api_keys/middleware.py` - ApiKeyRateLimitMiddleware: per-key rate enforcement + X-RateLimit-\* header injection
- `apps/api/config/settings/base.py` - Added ApiKeyRateLimitMiddleware entry inside B2B_START/B2B_END block after AuthRateLimitMiddleware
- `.secrets.baseline` - Updated by detect-secrets pre-commit hook (API_KEY_RATE_LIMIT string added)

## Decisions Made

- `get_usage(increment=True)` is the single counter call — enforcement and header values derive from the same counter, preventing any header/enforcement drift
- Rate limit key is `api_key.prefix` (e.g., `ft_a1b2c3d4`) — unique per key, not per user or IP — allows per-key revocation and independent rate windows
- `key=lambda g, r: api_key.prefix` must be a callable closure, not a plain string — django-ratelimit raises ImproperlyConfigured for string keys

## Deviations from Plan

None — plan executed exactly as written. The ruff formatter made a minor whitespace change to the `_inject_headers` method signature (no behavior change), handled automatically by pre-commit hook.

## Issues Encountered

- Pre-commit hooks (ruff + detect-secrets) modified staged files on first commit attempt — re-staged modified files and committed successfully on second attempt. Standard pre-commit behavior, not a blocking issue.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- AKEY-02 satisfied: all API key authenticated requests now enforce per-key rate limits
- ApiKeyRateLimitMiddleware is production-ready: handles RATELIMIT_ENABLE=False gracefully (get_usage returns None, no headers injected)
- Phase 28 complete: all 4 plans executed — API key model, auth, controllers, and rate limiting

---

_Phase: 28-api-key-authentication_
_Completed: 2026-03-13_
