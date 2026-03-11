---
phase: 16-security-hardening
plan: 03
subsystem: infra
tags: [django-csp, csp, hsts, security-headers, x-frame-options, referrer-policy, next.js, pytest]

# Dependency graph
requires:
  - phase: 16-01
    provides: RED test stubs for SEC-02 (test_csp_header_present, test_hsts_header_production, test_x_frame_options_header, test_referrer_policy_header)
provides:
  - django-csp 4.0 installed with CONTENT_SECURITY_POLICY dict (nonce-based, PostHog + Stripe sources)
  - CSPMiddleware at position 1 in Django MIDDLEWARE (after SecurityMiddleware)
  - HSTS settings in production.py (SECURE_HSTS_SECONDS=31536000, includeSubDomains, preload)
  - X_FRAME_OPTIONS and SECURE_REFERRER_POLICY in base.py
  - Next.js security headers via headers() function (CSP, X-Frame-Options, Referrer-Policy, X-Content-Type-Options)
  - All 9 security tests GREEN (SEC-01, SEC-02, SEC-03)
affects: []

# Tech tracking
tech-stack:
  added:
    - django-csp==4.0 (Content-Security-Policy middleware with per-request nonces)
  patterns:
    - "django-csp 4.0 API: CONTENT_SECURITY_POLICY dict with DIRECTIVES key (not old CSP_* flat settings)"
    - "NONCE sentinel in directive lists — django-csp replaces with nonce-{uuid} per request"
    - "HSTS in production.py only — never in base.py or development.py (local HTTP breakage)"
    - "Next.js static CSP via headers() function — uses unsafe-inline (no nonces); Django CSP uses nonces (different origins)"
    - "HSTS test requires secure=True + ALLOWED_HOSTS override — SecurityMiddleware only sets header on HTTPS requests"

key-files:
  created: []
  modified:
    - apps/api/config/settings/base.py
    - apps/api/config/settings/production.py
    - apps/api/pyproject.toml
    - apps/api/uv.lock
    - apps/web/next.config.ts
    - apps/api/tests/core/test_security.py

key-decisions:
  - "django-csp 4.0 CONTENT_SECURITY_POLICY dict (not old CSP_* flat settings) — 4.0 silently ignores old API; verified by testing"
  - "NONCE sentinel used in script-src, script-src-elem, style-src — request.csp_nonce available in templates"
  - "upgrade-insecure-requests omitted from CSP — HSTS in production.py handles upgrade; adding to base.py breaks local HTTP"
  - "Next.js CSP uses unsafe-inline (static) — App Router inline hydration scripts require it; Django CSP uses nonces (per-request, different origin)"
  - "HSTS test uses secure=True + ALLOWED_HOSTS=['testserver'] override — Django SecurityMiddleware only emits HSTS header on HTTPS requests (is_secure() must return True)"
  - "PostHog (eu.i.posthog.com, us.i.posthog.com) and Stripe (js.stripe.com, hooks.stripe.com) explicitly in connect-src and script-src"

patterns-established:
  - "Security headers: CSPMiddleware at MIDDLEWARE[1] (after SecurityMiddleware, before WhiteNoise) — nonce available to all downstream views"
  - "HSTS in production.py only — test with override_settings(SECURE_HSTS_SECONDS=..., secure=True) in Django test client"

requirements-completed: [SEC-02]

# Metrics
duration: 9min
completed: 2026-03-11
---

# Phase 16 Plan 03: Security Headers Summary

**django-csp 4.0 with per-request nonces + HSTS in production + Next.js static CSP headers — all 9 security tests GREEN**

## Performance

- **Duration:** 9 min
- **Started:** 2026-03-11T20:55:23Z
- **Completed:** 2026-03-11T21:04:21Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Installed django-csp 4.0 and configured CONTENT_SECURITY_POLICY dict with DIRECTIVES key (4.0 API), NONCE sentinels, PostHog and Stripe sources
- Added SECURE_HSTS_SECONDS/SECURE_HSTS_INCLUDE_SUBDOMAINS/SECURE_HSTS_PRELOAD to production.py only
- Added async headers() to Next.js next.config.ts with CSP, X-Frame-Options: DENY, Referrer-Policy, X-Content-Type-Options
- Turned 4 RED SEC-02 stubs GREEN; all 9 tests in test_security.py now pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Install django-csp and configure Django security headers** - `f87c220` (feat) — note: merged into 16-02 commit due to pre-commit stash behavior
2. **Task 2: Add Next.js security headers + turn SEC-02 tests GREEN** - `ebe188d` (feat)

## Files Created/Modified

- `apps/api/config/settings/base.py` - Added "csp" to INSTALLED_APPS, CSPMiddleware at MIDDLEWARE[1], CONTENT_SECURITY_POLICY dict, X_FRAME_OPTIONS, SECURE_REFERRER_POLICY
- `apps/api/config/settings/production.py` - Added SECURE_HSTS_SECONDS, SECURE_HSTS_INCLUDE_SUBDOMAINS, SECURE_HSTS_PRELOAD
- `apps/api/pyproject.toml` - Added django-csp==4.0 dependency
- `apps/api/uv.lock` - Updated lockfile
- `apps/web/next.config.ts` - Added isDev flag, cspDirectives array, async headers() function
- `apps/api/tests/core/test_security.py` - Replaced 4 RED SEC-02 stubs with GREEN implementations

## Decisions Made

- **HSTS test approach:** `secure=True` on Django test client + `ALLOWED_HOSTS=['testserver']` override required because `SecurityMiddleware.process_response()` only sets Strict-Transport-Security when `request.is_secure()` returns True. Without `secure=True`, the test client sends plain HTTP and HSTS is never set.
- **SECURE_HSTS_INCLUDE_SUBDOMAINS in override_settings:** Must be included in the test override to verify `includeSubDomains` in the header value — production.py sets it but test uses development settings by default.
- **Next.js unsafe-inline:** App Router generates inline `<script>` tags for hydration that cannot be nonce'd without Next.js middleware CSP injection. Django uses nonces on its own origin; the two CSP policies are independent and non-conflicting.
- **No upgrade-insecure-requests in CSP:** Would break local HTTP development. HSTS in production.py is the correct mechanism for HTTPS enforcement in production.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] HSTS test required secure=True + ALLOWED_HOSTS override**

- **Found during:** Task 2 (SEC-02 test implementation)
- **Issue:** Plan's test stub used `override_settings(SECURE_HSTS_SECONDS=31536000, SECURE_SSL_REDIRECT=False)` with plain HTTP GET — Django SecurityMiddleware only sets HSTS on HTTPS requests (`is_secure()` must return True), so header was absent
- **Fix:** Added `secure=True` to `client.get()` call and `ALLOWED_HOSTS=['testserver']` + `SECURE_HSTS_INCLUDE_SUBDOMAINS=True` to override_settings
- **Files modified:** `apps/api/tests/core/test_security.py`
- **Verification:** test_hsts_header_production passes with `max-age=31536000; includeSubDomains` in header
- **Committed in:** `ebe188d` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug in plan's test approach)
**Impact on plan:** Required fix for correctness — test logic in plan stub wouldn't have worked without HTTPS simulation.

## Issues Encountered

- Task 1 commit was absorbed into the 16-02 commit (`f87c220`) due to pre-commit stash rollback behavior when unstaged files conflicted with hook auto-fixes. The changes are committed correctly; commit message attribution is slightly off but all code changes are in the repo.
- E501 line-too-long ruff violation on test error message string — fixed by extracting to local variable.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- SEC-02 complete: all Django responses ship CSP (nonces), X-Frame-Options: DENY, Referrer-Policy
- HSTS active in production.py; development is unaffected
- Next.js ships matching static security headers on all routes
- Phase 16 (Security Hardening) is now complete: SEC-01, SEC-02, SEC-03 all GREEN
- Phase 17 (Dev-Time Security Gates) can proceed if planned

---

_Phase: 16-security-hardening_
_Completed: 2026-03-11_
