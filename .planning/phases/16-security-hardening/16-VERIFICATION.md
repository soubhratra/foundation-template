---
phase: 16-security-hardening
verified: 2026-03-11T21:30:00Z
status: passed
score: 9/9 must-haves verified
re_verification: false
---

# Phase 16: Security Hardening Verification Report

**Phase Goal:** Every request is protected by Redis-backed rate limiting and security headers, and cache/session use Redis as the default backend
**Verified:** 2026-03-11T21:30:00Z
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| #   | Truth                                                                                                     | Status   | Evidence                                                                                                                                                   |
| --- | --------------------------------------------------------------------------------------------------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Django cache operations hit Redis DB 1 (not LocMemCache) in non-test environments                         | VERIFIED | `CACHES["default"]["BACKEND"] = "django_redis.cache.RedisCache"` in base.py:209                                                                            |
| 2   | Session reads/writes hit Redis DB 2 via the 'sessions' cache alias                                        | VERIFIED | `SESSION_ENGINE = "django.contrib.sessions.backends.cache"`, `SESSION_CACHE_ALIAS = "sessions"` in base.py:228-229                                         |
| 3   | Auth endpoints return HTTP 429 after 5 requests per minute per IP                                         | VERIFIED | `AuthRateLimitMiddleware` in middleware.py:116, wired in MIDDLEWARE at base.py:131; test_rate_limit_returns_429 PASSED                                     |
| 4   | 429 responses include a Retry-After: 60 header                                                            | VERIFIED | `ratelimited_error()` sets `response["Retry-After"] = "60"` in ratelimit.py:29; test_rate_limit_retry_after_header PASSED                                  |
| 5   | Rate limit counters persist in Redis (RATELIMIT_USE_CACHE = "default")                                    | VERIFIED | `RATELIMIT_USE_CACHE: str = "default"` in base.py:241; test_rate_limit_uses_redis_cache PASSED                                                             |
| 6   | Tests run without hitting rate limits (autouse fixture)                                                   | VERIFIED | `test_isolation_settings` autouse fixture sets `RATELIMIT_ENABLE = False` in conftest.py:18                                                                |
| 7   | Every Django response includes Content-Security-Policy with default-src 'self'                            | VERIFIED | `CONTENT_SECURITY_POLICY` dict with `"DIRECTIVES"` key in base.py:257-277; `csp.middleware.CSPMiddleware` at MIDDLEWARE[1]; test_csp_header_present PASSED |
| 8   | Production Django responses include Strict-Transport-Security: max-age=31536000; includeSubDomains        | VERIFIED | `SECURE_HSTS_SECONDS = 31536000` in production.py:14; absent from base.py and development.py; test_hsts_header_production PASSED                           |
| 9   | Every Django response includes X-Frame-Options: DENY and Referrer-Policy: strict-origin-when-cross-origin | VERIFIED | `X_FRAME_OPTIONS = "DENY"` at base.py:281, `SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"` at base.py:285; both tests PASSED                  |

**Score:** 9/9 truths verified

---

### Required Artifacts

| Artifact                                 | Expected                                                                       | Status   | Details                                                                                   |
| ---------------------------------------- | ------------------------------------------------------------------------------ | -------- | ----------------------------------------------------------------------------------------- |
| `apps/api/tests/core/test_security.py`   | 9 tests covering SEC-01, SEC-02, SEC-03                                        | VERIFIED | 128 lines, all 9 functions implemented, 9/9 tests PASS                                    |
| `apps/api/apps/core/ratelimit.py`        | `ratelimited_error()` returning JSON 429 + Retry-After                         | VERIFIED | 31 lines, substantive implementation, returns status=429 with Retry-After header          |
| `apps/api/apps/core/middleware.py`       | `AuthRateLimitMiddleware` path-scoped to /api/v1/auth/                         | VERIFIED | Class exists at line 116, uses `is_ratelimited()`, returns `ratelimited_error()` directly |
| `apps/api/config/settings/base.py`       | CACHES (Redis DB1+DB2), SESSION*ENGINE, RATELIMIT*\*, CONTENT_SECURITY_POLICY  | VERIFIED | All blocks present: CACHES at line 207, SESSION at 228, RATELIMIT at 238, CSP at 257      |
| `apps/api/config/settings/production.py` | SECURE_HSTS_SECONDS, SECURE_HSTS_INCLUDE_SUBDOMAINS, SECURE_HSTS_PRELOAD       | VERIFIED | All three present at lines 14-16; absent from base.py and development.py                  |
| `apps/api/tests/conftest.py`             | `test_isolation_settings` autouse fixture                                      | VERIFIED | Present at line 10; sets RATELIMIT_ENABLE=False + LocMemCache for all tests               |
| `apps/web/next.config.ts`                | `headers()` with CSP, X-Frame-Options, Referrer-Policy, X-Content-Type-Options | VERIFIED | `async headers()` at line 35, applied to source `/(.*)`                                   |

---

### Key Link Verification

| From                               | To                                      | Via                                                                       | Status | Details                                                                                                              |
| ---------------------------------- | --------------------------------------- | ------------------------------------------------------------------------- | ------ | -------------------------------------------------------------------------------------------------------------------- |
| `apps/api/apps/core/middleware.py` | `apps/api/config/settings/base.py`      | `getattr(settings, 'RATELIMIT_AUTH_LOGIN', '5/m')` in middleware.**call** | WIRED  | Line 137: `rate = getattr(settings, "RATELIMIT_AUTH_LOGIN", "5/m")`; also in MIDDLEWARE list at base.py:131          |
| `apps/api/config/settings/base.py` | `django_redis.cache.RedisCache`         | `CACHES['default']['BACKEND']` and `CACHES['sessions']['BACKEND']`        | WIRED  | Both CACHES entries use `"django_redis.cache.RedisCache"` at base.py:209, 218                                        |
| `apps/api/config/settings/base.py` | `apps.core.ratelimit.ratelimited_error` | `RATELIMIT_VIEW` setting                                                  | WIRED  | `RATELIMIT_VIEW: str = "apps.core.ratelimit.ratelimited_error"` at base.py:242; called directly in middleware.py:148 |
| `apps/api/config/settings/base.py` | `csp.middleware.CSPMiddleware`          | MIDDLEWARE list at position 1                                             | WIRED  | `"csp.middleware.CSPMiddleware"` present at base.py:121; `"csp"` in INSTALLED_APPS at base.py:105                    |
| `apps/api/config/settings/base.py` | `CONTENT_SECURITY_POLICY` directives    | django-csp 4.0 reads `CONTENT_SECURITY_POLICY` dict                       | WIRED  | Dict with `"DIRECTIVES"` key at base.py:257; uses 4.0 API (not deprecated CSP\_\* flat settings)                     |
| `apps/web/next.config.ts`          | Next.js HTTP headers                    | `headers()` async function, source `/(.*)`                                | WIRED  | Function at line 35 returns headers array applied to all routes                                                      |

---

### Requirements Coverage

| Requirement | Source Plan(s) | Description                                                                                          | Status    | Evidence                                                                                                                                                                 |
| ----------- | -------------- | ---------------------------------------------------------------------------------------------------- | --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| SEC-01      | 16-01, 16-02   | Auth endpoints are rate-limited via django-ratelimit with Redis-backed counters                      | SATISFIED | `AuthRateLimitMiddleware` in MIDDLEWARE; `RATELIMIT_*` settings in base.py; 3 tests GREEN                                                                                |
| SEC-02      | 16-01, 16-03   | Every HTTP response ships with security headers (django-csp, HSTS, X-Frame-Options, Referrer-Policy) | SATISFIED | `CSPMiddleware` at MIDDLEWARE[1]; `CONTENT_SECURITY_POLICY` dict; `X_FRAME_OPTIONS`; `SECURE_REFERRER_POLICY`; HSTS in production.py; Next.js `headers()`; 4 tests GREEN |
| SEC-03      | 16-01, 16-02   | Django cache and session store use Redis via django-redis as default backend                         | SATISFIED | `CACHES` dict with `django_redis.cache.RedisCache` for both "default" and "sessions"; `SESSION_ENGINE = "django.contrib.sessions.backends.cache"`; 2 tests GREEN         |

All three requirements (SEC-01, SEC-02, SEC-03) are satisfied. No orphaned requirements found — REQUIREMENTS.md maps all three to Phase 16, and all three are covered by plans 16-01 through 16-03.

---

### Anti-Patterns Found

No blocker or warning anti-patterns found.

Scan performed on all key files modified in this phase:

- `apps/api/tests/core/test_security.py` — no TODOs, no empty implementations, no placeholder returns
- `apps/api/apps/core/ratelimit.py` — substantive handler, no stubs
- `apps/api/apps/core/middleware.py` — `AuthRateLimitMiddleware.__call__` uses real `is_ratelimited()` logic, not a pass-through
- `apps/api/config/settings/base.py` — all settings blocks fully populated
- `apps/api/config/settings/production.py` — HSTS values are concrete (31536000, True, True)
- `apps/api/tests/conftest.py` — autouse fixture sets both `RATELIMIT_ENABLE` and `CACHES`
- `apps/web/next.config.ts` — `headers()` returns concrete header values, not empty array

One notable implementation detail: `AuthRateLimitMiddleware` returns `ratelimited_error(request)` directly rather than raising `Ratelimited()`. This was an intentional deviation from the plan (documented in 16-02-SUMMARY.md) because Django's default `Ratelimited` exception handler returns 403 HTML, not 429 JSON. The direct return pattern is correct.

---

### Human Verification Required

None required. All behavioral claims are verifiable from code inspection and passing tests:

- Rate limiting logic is exercised by `test_rate_limit_returns_429` and `test_rate_limit_retry_after_header` (both PASS)
- Security header presence is exercised by four SEC-02 tests hitting a live endpoint (all PASS)
- Redis CACHES configuration is verified by importing `config.settings.base` directly in tests (bypasses test isolation fixture override)

One item warrants awareness (not blocking):

- HSTS test uses `secure=True` on the Django test client to simulate HTTPS — this is the correct approach since `SecurityMiddleware` only emits HSTS on secure requests. The test accurately reflects production behavior.

---

### Test Execution Results

```
tests/core/test_security.py::test_rate_limit_returns_429          PASSED
tests/core/test_security.py::test_rate_limit_retry_after_header   PASSED
tests/core/test_security.py::test_rate_limit_uses_redis_cache     PASSED
tests/core/test_security.py::test_csp_header_present             PASSED
tests/core/test_security.py::test_hsts_header_production         PASSED
tests/core/test_security.py::test_x_frame_options_header         PASSED
tests/core/test_security.py::test_referrer_policy_header         PASSED
tests/core/test_security.py::test_default_cache_is_redis         PASSED
tests/core/test_security.py::test_session_cache_is_redis         PASSED

9 passed, 1 warning in 0.96s
```

---

### Summary

Phase 16 goal is fully achieved. Every artifact is substantive and wired:

- **SEC-01 (Rate Limiting):** `AuthRateLimitMiddleware` is registered in `MIDDLEWARE` and path-scoped to `/api/v1/auth/` routes. It calls `is_ratelimited()` with IP key at `RATELIMIT_AUTH_LOGIN = "5/m"`, returns a JSON 429 with `Retry-After: 60` directly from `ratelimited_error()`. Counters persist in Redis (DB 1) via `RATELIMIT_USE_CACHE = "default"`. Tests are isolated from rate limits via the `test_isolation_settings` autouse fixture.

- **SEC-02 (Security Headers):** `csp.middleware.CSPMiddleware` sits at `MIDDLEWARE[1]` and emits `Content-Security-Policy` with per-request nonces on every Django response. `X_FRAME_OPTIONS = "DENY"` and `SECURE_REFERRER_POLICY` are set in `base.py`. HSTS is scoped to `production.py` only, correctly absent from `base.py` and `development.py`. Next.js ships matching static security headers via `async headers()` applied to all routes.

- **SEC-03 (Redis Cache/Session):** `CACHES["default"]` and `CACHES["sessions"]` both use `django_redis.cache.RedisCache` on separate Redis DBs (1 and 2). `SESSION_ENGINE = "django.contrib.sessions.backends.cache"` with `SESSION_CACHE_ALIAS = "sessions"`. Tests override to `LocMemCache` to remove Redis as a CI dependency.

---

_Verified: 2026-03-11T21:30:00Z_
_Verifier: Claude (gsd-verifier)_
