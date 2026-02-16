---
phase: 02-api-core-auth-backend
plan: 02
subsystem: auth
tags: [django-allauth, headless, jwt, cors, csrf, sessions]

# Dependency graph
requires:
  - phase: 02-01
    provides: Ninja Extra API base wiring and error envelope
provides:
  - Headless Allauth settings for session + JWT auth
  - JWT token strategy with stateful validation and refresh rotation
  - Auth endpoints mounted under /api/v1/auth/
affects: [web-auth, mobile-auth, api-client, docs]

# Tech tracking
tech-stack:
  added: [django-allauth]
  patterns: [Allauth headless dual-client routing, JWT stateful validation, custom headless adapter]

key-files:
  created: [apps/api/apps/accounts/headless.py]
  modified:
    - apps/api/config/settings/base.py
    - apps/api/config/settings/development.py
    - apps/api/config/settings/production.py
    - apps/api/config/urls.py
    - apps/api/pyproject.toml
    - apps/api/uv.lock

key-decisions:
  - "Use HS256 for headless JWTs backed by SECRET_KEY to avoid RSA key provisioning in the template."
  - "Expose headless browser/app endpoints under /api/v1/auth/ with explicit session logout overrides returning 204."

patterns-established:
  - "Custom headless adapter and signup form live in apps/api/apps/accounts/headless.py"
  - "Headless JWT settings are configured centrally in base settings"

# Metrics
duration: 0 min
completed: 2026-02-16
---

# Phase 02 Plan 02: Headless Auth Configuration Summary

**Allauth headless settings with JWT token strategy, rate limits, and auth routing under /api/v1/auth/.**

## Performance

- **Duration:** 0 min
- **Started:** 2026-02-15T19:12:32-05:00
- **Completed:** 2026-02-16T00:13:09Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Configured headless Allauth settings for email-only auth, mandatory verification, JWT rotation, and CSRF/CORS policy.
- Added headless adapter + signup form to persist name and return enriched user payloads.
- Mounted headless auth endpoints under /api/v1/auth/ with explicit session logout behavior.

## Task Commits

Each task was committed atomically:

1. **Task 1: Apply allauth headless + JWT/session settings** - `fc6dbf2` (feat)
2. **Task 2: Mount headless auth URLs under /api/v1/auth/** - `e64bb30` (feat)

**Plan metadata:** _pending_

## Files Created/Modified
- `apps/api/apps/accounts/headless.py` - Custom signup form, adapter, and logout response override.
- `apps/api/config/settings/base.py` - Allauth headless, JWT, CORS/CSRF, and rate-limit settings.
- `apps/api/config/settings/development.py` - Dev cookie security overrides.
- `apps/api/config/settings/production.py` - Prod cookie security and CORS/CSRF overrides.
- `apps/api/config/urls.py` - Headless auth routing under /api/v1/auth/.
- `apps/api/pyproject.toml` - Adds django-allauth dependency.
- `apps/api/uv.lock` - Locks django-allauth dependency.

## Decisions Made
- Use HS256 for headless JWTs backed by SECRET_KEY to avoid RSA key provisioning in the template.
- Override headless session logout responses to return HTTP 204 with no body.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added missing django-allauth dependency**
- **Found during:** Task 1 (Apply allauth headless + JWT/session settings)
- **Issue:** Allauth was required but not declared in apps/api/pyproject.toml.
- **Fix:** Added django-allauth via uv to update pyproject and lockfile.
- **Files modified:** apps/api/pyproject.toml, apps/api/uv.lock
- **Verification:** uv add completed successfully.
- **Committed in:** fc6dbf2

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Required for auth configuration to import correctly. No scope creep.

## Issues Encountered
- Verification call to `/api/v1/auth/config` not run (server not started in this execution).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Auth configuration and routing are in place for accounts endpoints.
- Ready for 02-03 plan work on /users/me and dual-auth behavior.

---
*Phase: 02-api-core-auth-backend*
*Completed: 2026-02-16*

## Self-Check: PASSED
