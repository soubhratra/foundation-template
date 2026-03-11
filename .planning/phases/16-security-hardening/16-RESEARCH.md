# Phase 16: Security Hardening - Research

**Researched:** 2026-03-11
**Domain:** Django rate limiting, CSP / security headers, Redis cache + session backend, Next.js security headers
**Confidence:** HIGH

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions

**Rate limiting**

- Default limit: 5 requests per minute per IP on all auth endpoints
- Scope: login, signup, password reset, email confirmation (allauth headless endpoints only)
- Password change endpoint included; all-API rate limiting is out of scope
- Fail behavior: fail open — if Redis is unreachable, requests pass through
- Configurability: settings-based — `RATELIMIT_AUTH_LOGIN = '5/m'` in `base.py`; projects override per risk tolerance (same pattern as `BILLING_ADAPTER`, `OBSERVABILITY_ADAPTER`)
- `Retry-After` header included in 429 responses

**CSP policy**

- Mode: enforcement from day one (not report-only)
- Inline scripts: use nonces — no `unsafe-inline`
- Third-party sources whitelisted: PostHog (`eu.i.posthog.com`, `us.i.posthog.com`), Stripe (`js.stripe.com`, `hooks.stripe.com`)
- Next.js `headers()` config mirrors Django's CSP — same source list, single mental model
- Additional headers: `Strict-Transport-Security` (max-age=31536000; includeSubDomains), `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`
- HSTS enabled in production only

**Redis cache + session backend**

- Applies to dev and production
- Separate Redis database indexes: Celery DB 0, Cache DB 1, Sessions DB 2
- Session TTL: 2 weeks (`SESSION_COOKIE_AGE = 1209600`)
- `SESSION_ENGINE = 'django.contrib.sessions.backends.cache'`

**Test suite isolation**

- Rate limiting: `RATELIMIT_ENABLE = False` in test settings
- Cache backend in tests: LocMemCache
- Security headers middleware: active in tests

### Claude's Discretion

- Exact nonce implementation details in django-csp config
- CSP `connect-src` and `img-src` directive values beyond the core third-party sources
- django-redis connection pool settings (timeout, max connections)
- Exact middleware insertion order beyond "after SessionMiddleware"

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>

## Phase Requirements

| ID     | Description                                                                                                                                                                                    | Research Support                                                                                                                                                                              |
| ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| SEC-01 | Auth endpoints are rate-limited via `django-ratelimit` with Redis-backed counters; limits configurable per endpoint via Django settings                                                        | django-ratelimit 4.1.0 with `RATELIMIT_USE_CACHE` pointing at a named Redis cache (DB 1); `RATELIMIT_ENABLE = False` in tests; custom 429 handler with `Retry-After` header                   |
| SEC-02 | Every HTTP response ships with security headers (`django-csp`, HSTS, `X-Frame-Options`, `Referrer-Policy`) via Django middleware; Next.js `headers()` config ships matching CSP + frame policy | django-csp 4.0 + `csp.middleware.CSPMiddleware`; Django `SecurityMiddleware` for HSTS; Next.js `headers()` async function in `next.config.ts`                                                 |
| SEC-03 | Django cache and session store use Redis via `django-redis` as default backend — `LocMemCache` not used in any non-test environment                                                            | django-redis 6.0.0 with separate `CACHES` entries for `default` (DB 1) and `sessions` (DB 2); `SESSION_ENGINE = 'django.contrib.sessions.backends.cache'`; `SESSION_CACHE_ALIAS = 'sessions'` |

</phase_requirements>

---

## Summary

Phase 16 wires three independent but related security infrastructure concerns into the Django + Next.js stack. Each concern maps to a distinct library with well-established integration patterns.

**Redis as cache and session backend (SEC-03)** is the most foundational change: switching `CACHES['default']` and a new `CACHES['sessions']` to `django-redis` 6.0.0 with separate Redis DB indexes (1 and 2, leaving 0 for Celery) unlocks persistent, cross-process rate limiting counters and eliminates the in-process `LocMemCache` from all non-test environments. `SESSION_ENGINE = 'django.contrib.sessions.backends.cache'` with `SESSION_CACHE_ALIAS = 'sessions'` completes the session migration with zero new infrastructure (Redis already runs in docker-compose).

**Rate limiting (SEC-01)** uses `django-ratelimit` 4.1.0 with `@ratelimit(key='ip', rate=settings.RATELIMIT_AUTH_LOGIN, block=True)` applied to allauth headless views. Because allauth's headless endpoints are Django views registered via `allauth.headless.urls`, rate limiting is applied at the URL wrapper layer — either via a custom view middleware or by wrapping allauth views using `ratelimit()`. A custom 429 handler injects the `Retry-After` header. `RATELIMIT_FAIL_OPEN = True` implements the fail-open decision; `RATELIMIT_ENABLE = False` in test settings prevents 429s in CI.

**Security headers (SEC-02)** use `django-csp` 4.0 (new `CONTENT_SECURITY_POLICY` dict config, not the old `CSP_*` settings API). `csp.middleware.CSPMiddleware` generates per-request nonces automatically. Django's built-in `SecurityMiddleware` handles HSTS and `X-Frame-Options`. The Next.js side uses a static `headers()` config in `next.config.ts` — not middleware — because nonces are generated by Django (Next.js has no server-side nonce to provide), so a static CSP mirroring Django's source list is the correct approach.

**Primary recommendation:** Implement in three sequential sub-tasks: (1) Redis CACHES + session backend, (2) rate limiting with 429 handler, (3) CSP/headers middleware + Next.js headers config. Each is independently testable and deployable.

---

## Standard Stack

### Core

| Library          | Version | Purpose                                           | Why Standard                                                                                         |
| ---------------- | ------- | ------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| django-redis     | 6.0.0   | Django cache + session backend over Redis         | Official jazzband project; supports Django 4.2+; zero extra infra when Redis already runs            |
| django-ratelimit | 4.1.0   | IP-based rate limiting with Redis-backed counters | Simplest decorator-based API; cache-agnostic (uses `CACHES` dict); `RATELIMIT_ENABLE` flag for tests |
| django-csp       | 4.0     | CSP header generation with nonce injection        | Mozilla-maintained; middleware-based; automatic nonce attachment to `request.csp_nonce`              |

### Supporting

| Library                   | Version               | Purpose                                       | When to Use                                                                          |
| ------------------------- | --------------------- | --------------------------------------------- | ------------------------------------------------------------------------------------ |
| Django SecurityMiddleware | built-in              | HSTS, X-Frame-Options, X-Content-Type-Options | Already in MIDDLEWARE — just needs settings enabled                                  |
| Next.js `headers()`       | built-in (Next.js 15) | Static security headers on all routes         | Static CSP (no nonces) — simpler than middleware approach for a backend-rendered CSP |

### Alternatives Considered

| Instead of                | Could Use                          | Tradeoff                                                                                   |
| ------------------------- | ---------------------------------- | ------------------------------------------------------------------------------------------ |
| django-ratelimit          | django-axes                        | axes is login-attempt focused only; ratelimit is generic and view-level                    |
| django-csp                | Custom SecurityMiddleware subclass | CSP is complex enough that hand-rolling is error-prone; django-csp handles nonce lifecycle |
| django-redis for sessions | django-session-redis               | django-redis already installed; no reason for a second redis library                       |

**Installation:**

```bash
uv add django-ratelimit django-csp django-redis
```

---

## Architecture Patterns

### Recommended Project Structure

No new directories. All changes are settings files and middleware configuration:

```
apps/api/
├── config/
│   └── settings/
│       ├── base.py          # CACHES, SESSION_ENGINE, RATELIMIT_*, CSP_* added
│       ├── development.py   # RATELIMIT_ENABLE = False (or use conftest override)
│       └── production.py    # SECURE_HSTS_SECONDS added
├── apps/
│   └── core/
│       └── ratelimit.py     # Custom 429 handler view with Retry-After header
apps/web/
└── next.config.ts           # headers() async function added
```

### Pattern 1: Redis CACHES with Separate DB Indexes

**What:** Two named cache entries pointing at separate Redis databases. `default` at DB 1, `sessions` at DB 2.
**When to use:** Required when multiple consumers (Celery, cache, sessions) share one Redis instance.

```python
# Source: django-redis docs (github.com/jazzband/django-redis)
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL.replace("/0", "/1"),  # DB 1 for cache
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
        },
    },
    "sessions": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL.replace("/0", "/2"),  # DB 2 for sessions
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
        },
    },
}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "sessions"
```

**Caution:** `REDIS_URL` in `base.py` is `redis://localhost:6379/0` by default. The string replacement `.replace("/0", "/1")` is brittle if the URL has no trailing `/0`. Use `urllib.parse` or `env()` to derive DB-indexed URLs safely, or define `CACHE_REDIS_URL` and `SESSION_REDIS_URL` as separate env vars with defaults derived from `REDIS_URL`.

### Pattern 2: Django-ratelimit on Allauth Headless Views

**What:** `@ratelimit` cannot be applied directly to allauth's views because they are not owned code. Apply via URL-level wrapping using `ratelimit_exempt` or a middleware that calls `is_ratelimited()`.
**When to use:** Any Django view you don't own directly.

The correct approach for allauth headless (which registers views via URL include) is to use `RatelimitMiddleware` with a custom 429 view, or to wrap allauth's URL includes with a rate-limiting middleware applied to the URL pattern.

**Recommended approach — URL path-scoped middleware via `is_ratelimited()` helper:**

```python
# Source: django-ratelimit docs (django-ratelimit.readthedocs.io/en/stable/usage.html)
# apps/api/apps/core/middleware.py  — add to existing middleware module

from django_ratelimit.core import is_ratelimited
from django_ratelimit.exceptions import Ratelimited

_AUTH_PATHS = (
    "/api/v1/auth/browser/v1/",
    "/api/v1/auth/app/v1/",
)

class AuthRateLimitMiddleware:
    """Rate-limit auth endpoints at middleware level (allauth views are not owned code)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith(_AUTH_PATHS):
            from django.conf import settings
            rate = getattr(settings, "RATELIMIT_AUTH_LOGIN", "5/m")
            limited = is_ratelimited(
                request,
                group="auth",
                key="ip",
                rate=rate,
                increment=True,
            )
            if limited:
                raise Ratelimited()
        return self.get_response(request)
```

Combined with a `RATELIMIT_VIEW` pointing at a JSON 429 handler:

```python
# apps/api/apps/core/ratelimit.py
import math
import time

from django.http import JsonResponse


def ratelimited_error(request, exception=None):
    """Return 429 with Retry-After header per RFC 6585."""
    retry_after = 60  # conservative default — matches '5/m' window
    response = JsonResponse(
        {"error": {"code": "RATE_001", "message": "Too many requests. Please try again later."}},
        status=429,
    )
    response["Retry-After"] = str(retry_after)
    return response
```

Settings wiring:

```python
# base.py  — RATE LIMITING MODULE
RATELIMIT_AUTH_LOGIN: str = "5/m"
RATELIMIT_ENABLE: bool = True
RATELIMIT_FAIL_OPEN: bool = True          # fail open — auth availability > strict enforcement
RATELIMIT_USE_CACHE: str = "default"      # uses the Redis cache backend
RATELIMIT_VIEW: str = "apps.core.ratelimit.ratelimited_error"
```

```python
# development.py — disable in tests by using conftest @override_settings
# NOTE: RATELIMIT_ENABLE = False goes in test conftest, NOT development.py
# (development.py is also used locally, and local devs should test with rate limiting off)
```

### Pattern 3: django-csp 4.0 Configuration (New API)

**Critical:** django-csp 4.0 introduced a **breaking configuration change**. The old per-directive settings (`CSP_DEFAULT_SRC`, `CSP_SCRIPT_SRC`, etc.) are **replaced** by a single `CONTENT_SECURITY_POLICY` dict. Do not mix old and new API.

```python
# Source: django-csp docs (django-csp.readthedocs.io/en/latest/configuration.html)

CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        "default-src": ["'self'"],
        "script-src": ["'self'", "NONCE"],  # NONCE sentinel — middleware replaces with 'nonce-{value}'
        "style-src": ["'self'", "NONCE"],
        "img-src": ["'self'", "data:", "blob:"],
        "font-src": ["'self'"],
        "connect-src": [
            "'self'",
            "https://eu.i.posthog.com",
            "https://us.i.posthog.com",
            "https://hooks.stripe.com",
        ],
        "frame-src": [
            "https://js.stripe.com",
        ],
        "script-src-elem": [
            "'self'",
            "NONCE",
            "https://js.stripe.com",
        ],
        "object-src": ["'none'"],
        "base-uri": ["'self'"],
        "form-action": ["'self'"],
        "frame-ancestors": ["'none'"],
        "upgrade-insecure-requests": True,  # omit in dev (no HTTPS)
    },
}
```

Middleware registration (order matters for nonce — must be before any view that uses `request.csp_nonce`):

```python
# base.py MIDDLEWARE — insert after SecurityMiddleware, before SessionMiddleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "csp.middleware.CSPMiddleware",          # <-- insert here
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    ...
]
```

Add `"csp"` to `INSTALLED_APPS`.

### Pattern 4: HSTS via Django SecurityMiddleware

HSTS is already supported by Django's built-in `SecurityMiddleware` (already in MIDDLEWARE at position 0). It just needs settings:

```python
# production.py only — HSTS must NOT be in development.py
SECURE_HSTS_SECONDS = 31536000          # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True              # optional but standard
```

`X-Frame-Options` is already handled by `django.middleware.clickjacking.XFrameOptionsMiddleware` which is in MIDDLEWARE. Set:

```python
# base.py
X_FRAME_OPTIONS = "DENY"  # already Django default but explicit is better
```

### Pattern 5: Next.js Static Security Headers

**What:** `headers()` in `next.config.ts` for static CSP (no nonces — Next.js does not generate nonces in this stack, Django does).
**When to use:** Server state CSP is owned by Django; Next.js just needs matching headers for browser's same-origin policy compliance.

```typescript
// Source: nextjs.org/docs/app/guides/content-security-policy
// apps/web/next.config.ts

const isDev = process.env.NODE_ENV === "development";

const cspHeader = [
  "default-src 'self'",
  isDev
    ? "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://js.stripe.com"
    : "script-src 'self' 'unsafe-inline' https://js.stripe.com",
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data: blob:",
  "font-src 'self'",
  "connect-src 'self' https://eu.i.posthog.com https://us.i.posthog.com https://hooks.stripe.com",
  "frame-src https://js.stripe.com",
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "frame-ancestors 'none'",
].join("; ");

const securityHeaders = [
  { key: "Content-Security-Policy", value: cspHeader },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  // HSTS omitted — Next.js may serve HTTP locally; let the CDN/reverse proxy handle it
];

const nextConfig: NextConfig = {
  async headers() {
    return [{ source: "/(.*)", headers: securityHeaders }];
  },
  // ... existing config
};
```

**Why `unsafe-inline` in Next.js CSP:** Next.js App Router generates inline scripts for hydration that are not controlled by the application. Without nonces (which require Next.js middleware for per-request nonce injection), `unsafe-inline` is required for Next.js to function. This is acceptable because the Next.js frontend is a static boundary — sensitive operations happen via the Django API which has full nonce-based CSP.

### Anti-Patterns to Avoid

- **Using old CSP settings API:** `CSP_DEFAULT_SRC = (...)` — this is the django-csp 3.x API. Version 4.0 uses `CONTENT_SECURITY_POLICY = {"DIRECTIVES": {...}}`. Mixing old and new causes silent misconfiguration.
- **Pointing `RATELIMIT_USE_CACHE` at the `sessions` cache:** Rate limit counters and sessions have different TTL requirements. Use `default` (DB 1) for rate limits.
- **Setting `RATELIMIT_ENABLE = False` in `development.py`:** Development settings are also loaded by `pytest` (per `pyproject.toml`). Use `@override_settings(RATELIMIT_ENABLE=False)` in test fixtures or a `pytest.ini_options` override, not in development.py.
- **Using `REDIS_URL.replace("/0", "/1")` string substitution:** The default `REDIS_URL` may not have a database number. Use `urllib.parse.urlparse` or define separate env vars.
- **Adding HSTS to `base.py` or `development.py`:** HSTS forces HTTPS. In local dev, Django may serve HTTP. HSTS goes in `production.py` only.

---

## Don't Hand-Roll

| Problem                                | Don't Build                                                                      | Use Instead                                                  | Why                                                                                                                                  |
| -------------------------------------- | -------------------------------------------------------------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------ |
| CSP nonce generation and injection     | Custom middleware that generates random nonces and injects into response headers | `csp.middleware.CSPMiddleware` with `"NONCE"` sentinel       | Nonce must be per-request, unique, and present in both the header and every inline script attribute — django-csp automates all three |
| 429 response for rate limited requests | Exception handler that catches all 403s and checks request.limited               | `RATELIMIT_VIEW` + `RatelimitMiddleware` pattern             | Keeps 403 (forbidden) and 429 (rate limited) semantically distinct                                                                   |
| Redis URL derivation for different DBs | String manipulation on `REDIS_URL`                                               | Separate env vars with sensible defaults                     | URL manipulation is fragile; separate vars are explicit and overridable per deployment                                               |
| Session TTL enforcement in Redis       | Manual `EXPIRE` calls in session save logic                                      | `SESSION_COOKIE_AGE` — django-redis reads this automatically | django-redis maps `SESSION_COOKIE_AGE` to Redis `EXPIRE`; no custom code needed                                                      |

**Key insight:** All three libraries (django-redis, django-ratelimit, django-csp) are thin wrappers around Django's existing hook points (CACHES, middleware, exception handling). The complexity is all in configuration, not integration code.

---

## Common Pitfalls

### Pitfall 1: django-csp 4.0 Breaking API Change

**What goes wrong:** Code uses old `CSP_DEFAULT_SRC`, `CSP_SCRIPT_SRC` etc. settings — these are silently ignored in 4.0, resulting in no CSP headers being sent.
**Why it happens:** Most Stack Overflow answers and blog posts use the 3.x API. The 4.0 migration is a breaking change.
**How to avoid:** Use `CONTENT_SECURITY_POLICY = {"DIRECTIVES": {...}}` exclusively. Verify headers are present in test assertions.
**Warning signs:** No `Content-Security-Policy` header in responses despite middleware being installed.

### Pitfall 2: Allauth Already Has Rate Limiting

**What goes wrong:** Double-rate-limiting allauth endpoints — both allauth's `ACCOUNT_RATE_LIMITS` and django-ratelimit fire independently, creating confusing behavior where the effective limit is whichever is more restrictive.
**Why it happens:** Allauth has built-in rate limiting backed by Django's cache (non-atomic, as documented). It uses `ACCOUNT_RATE_LIMITS` keys like `"login"` (default `"30/m/ip"`), `"signup"` (default `"20/m/ip"`), etc.
**How to avoid:** The decision (locked) is to add django-ratelimit at 5/m — this is stricter than allauth's defaults. The allauth built-in limits remain as a secondary layer. This is fine (defense in depth). Document the dual-layer behavior in settings comments.
**Warning signs:** Users hit 429 before reaching the django-ratelimit threshold.

### Pitfall 3: RATELIMIT_ENABLE Setting Location

**What goes wrong:** `RATELIMIT_ENABLE = False` is placed in `development.py`. Since `pyproject.toml` sets `DJANGO_SETTINGS_MODULE = "config.settings.development"`, pytest loads development settings. This disables rate limiting in tests — which is the intended test isolation. But it also disables rate limiting for local manual testing.
**Why it happens:** Development and test environments share the same settings file in this project.
**How to avoid:** Use `@override_settings(RATELIMIT_ENABLE=False)` in a pytest fixture rather than in `development.py`. This keeps local dev rate limiting active while disabling it in automated tests.

```python
# tests/conftest.py
import pytest
from django.test import override_settings

@pytest.fixture(autouse=True)
def disable_ratelimit():
    with override_settings(RATELIMIT_ENABLE=False):
        yield
```

### Pitfall 4: Redis URL DB Index Derivation

**What goes wrong:** `REDIS_URL.replace("/0", "/1")` fails when `REDIS_URL = "redis://localhost:6379"` (no database suffix) or when the URL contains `/0` in the hostname portion.
**Why it happens:** The default in `base.py` is `redis://localhost:6379/0` which has the trailing `/0`, but not all deployments will follow this pattern.
**How to avoid:** Define `CACHE_REDIS_URL` and `SESSION_REDIS_URL` as explicit env vars with defaults that encode the correct DB:

```python
CACHE_REDIS_URL = env("CACHE_REDIS_URL", default="redis://localhost:6379/1")
SESSION_REDIS_URL = env("SESSION_REDIS_URL", default="redis://localhost:6379/2")
```

Add these to `.env.example`.

### Pitfall 5: Next.js CSP Nonce Mismatch

**What goes wrong:** Next.js middleware is added to generate nonces for the frontend, creating a second nonce lifecycle that conflicts with or is independent of Django's nonces.
**Why it happens:** The Next.js CSP docs prominently feature nonce-via-middleware patterns. Applying that to a backend-driven SaaS template creates confusion about which nonce applies to which script.
**How to avoid:** Next.js static CSP (in `next.config.ts` `headers()`) with `unsafe-inline` for scripts. Django's CSP with nonces applies to Django-rendered content. These are separate origins/layers — no conflict.

### Pitfall 6: Cache Clear Wipes Sessions

**What goes wrong:** `cache.clear()` in tests or maintenance scripts wipes both cache entries AND sessions if they share a Redis database.
**Why it happens:** `cache.clear()` calls Redis `FLUSHDB` which clears the entire database.
**How to avoid:** Separate Redis DB indexes (decision is already locked: cache=DB1, sessions=DB2). Test fixtures that call `cache.clear()` only affect DB1.

---

## Code Examples

Verified patterns from official sources:

### django-redis CACHES Configuration

```python
# Source: github.com/jazzband/django-redis README
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://localhost:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
        },
    },
    "sessions": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://localhost:6379/2",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
        },
    },
}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "sessions"
```

### Test Settings Override for Cache + Rate Limiting

```python
# Source: django-ratelimit docs (RATELIMIT_ENABLE), Django docs (test cache)
# Use in conftest.py or via pytest.ini_options addopts

# Option A: conftest.py fixture (preferred — per-test isolation)
import pytest

@pytest.fixture(autouse=True)
def test_isolation_settings(settings):
    """Disable rate limiting; use fast in-memory cache in tests."""
    settings.RATELIMIT_ENABLE = False
    settings.CACHES = {
        "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
        "sessions": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
    }
```

### Custom 429 Handler with Retry-After

```python
# Source: django-ratelimit cookbook (django-ratelimit.readthedocs.io/en/latest/cookbook/429.html)
from django.http import JsonResponse


def ratelimited_error(request, exception=None):
    """RFC 6585 compliant 429 response with Retry-After header."""
    response = JsonResponse(
        {
            "error": {
                "code": "RATE_001",
                "message": "Too many requests. Please try again later.",
            }
        },
        status=429,
    )
    response["Retry-After"] = "60"  # seconds — matches '5/m' window
    return response
```

### django-csp 4.0 Settings (Enforcement Mode)

```python
# Source: django-csp docs v4.0 (django-csp.readthedocs.io/en/latest/configuration.html)
CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        "default-src": ["'self'"],
        "script-src": ["'self'", "NONCE", "https://js.stripe.com"],
        "style-src": ["'self'", "NONCE"],
        "img-src": ["'self'", "data:", "blob:"],
        "font-src": ["'self'"],
        "connect-src": [
            "'self'",
            "https://eu.i.posthog.com",
            "https://us.i.posthog.com",
            "https://hooks.stripe.com",
        ],
        "frame-src": ["https://js.stripe.com"],
        "script-src-elem": ["'self'", "NONCE", "https://js.stripe.com"],
        "object-src": ["'none'"],
        "base-uri": ["'self'"],
        "form-action": ["'self'"],
        "frame-ancestors": ["'none'"],
    },
}
```

### Next.js headers() with Security Headers

```typescript
// Source: nextjs.org/docs/app/guides/content-security-policy
// next.config.ts async headers() function

const isDev = process.env.NODE_ENV === "development";

const cspDirectives = [
  "default-src 'self'",
  isDev
    ? "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://js.stripe.com"
    : "script-src 'self' 'unsafe-inline' https://js.stripe.com",
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data: blob:",
  "font-src 'self'",
  "connect-src 'self' https://eu.i.posthog.com https://us.i.posthog.com https://hooks.stripe.com",
  "frame-src https://js.stripe.com",
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "frame-ancestors 'none'",
];

async headers() {
  return [
    {
      source: "/(.*)",
      headers: [
        { key: "Content-Security-Policy", value: cspDirectives.join("; ") },
        { key: "X-Frame-Options", value: "DENY" },
        { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
        { key: "X-Content-Type-Options", value: "nosniff" },
      ],
    },
  ];
}
```

---

## State of the Art

| Old Approach                                          | Current Approach                                                                   | When Changed          | Impact                                                                      |
| ----------------------------------------------------- | ---------------------------------------------------------------------------------- | --------------------- | --------------------------------------------------------------------------- |
| `CSP_DEFAULT_SRC = (...)` per-setting                 | `CONTENT_SECURITY_POLICY = {"DIRECTIVES": {...}}` dict                             | django-csp 4.0 (2023) | Breaking — old settings silently ignored                                    |
| `RATELIMIT_USE_CACHE` only (implicit default cache)   | `RATELIMIT_USE_CACHE = 'cache-name'` pointing at named Redis cache                 | django-ratelimit 4.x  | Explicit is better — avoids accidental use of LocMemCache                   |
| allauth `ACCOUNT_RATE_LIMITS` as single string        | `"5/m/ip"` vs `"5/m/key"` explicit scoping + combinations like `"20/m/ip,5/m/key"` | allauth 65.x (2024)   | More granular — existing `"1/m"` for `confirm_email` in base.py still valid |
| `SESSION_COOKIE_AGE` ignored by Redis session backend | django-redis automatically maps `SESSION_COOKIE_AGE` to Redis TTL                  | django-redis 5+       | No custom session expiry code needed                                        |

**Deprecated/outdated:**

- `CSP_*` flat settings (e.g., `CSP_DEFAULT_SRC`): Removed in django-csp 4.0. Use `CONTENT_SECURITY_POLICY["DIRECTIVES"]`.
- `RATELIMIT_CACHE` setting name: Was renamed to `RATELIMIT_USE_CACHE` in django-ratelimit 3.0.

---

## Open Questions

1. **Retry-After header value precision**
   - What we know: The `Retry-After` header value should match the rate window (60 seconds for `5/m`). django-ratelimit does not compute remaining window time.
   - What's unclear: Whether to compute the precise remaining window using `cache.get()` on the rate limit key, or use a static `60` second value.
   - Recommendation: Use a static 60-second value for simplicity. The header satisfies the success criterion; precise countdown adds complexity for minimal UX benefit in a security-critical endpoint.

2. **CSP `upgrade-insecure-requests` in development**
   - What we know: This directive forces HTTPS. In development, the API runs on HTTP.
   - What's unclear: Whether to include it in the base CSP or only in production CSP.
   - Recommendation: Omit from base `CONTENT_SECURITY_POLICY` and add in `production.py` via a separate `CONTENT_SECURITY_POLICY_REPORT_ONLY` or by overriding the directive. Simpler: just omit it entirely — HSTS already handles the upgrade-to-HTTPS concern.

3. **Auth middleware vs. URL-wrapper for rate limiting**
   - What we know: django-ratelimit's `@ratelimit` decorator cannot be applied to allauth's internally registered views without monkeypatching.
   - What's unclear: Whether to use `AuthRateLimitMiddleware` (path prefix check) or `RatelimitMiddleware` + `RATELIMIT_VIEW` (global 403→429 handler).
   - Recommendation: Use `AuthRateLimitMiddleware` as a lightweight middleware added to `MIDDLEWARE` (path-prefix scoped `is_ratelimited()` call). This is more explicit than `RatelimitMiddleware`'s global 403-catching behavior and avoids impacting non-auth 403 responses.

---

## Validation Architecture

### Test Framework

| Property           | Value                                                            |
| ------------------ | ---------------------------------------------------------------- |
| Framework          | pytest + pytest-django (see pyproject.toml)                      |
| Config file        | `apps/api/pyproject.toml` — `[tool.pytest.ini_options]`          |
| Quick run command  | `cd apps/api && python -m pytest tests/core/test_security.py -x` |
| Full suite command | `cd apps/api && python -m pytest`                                |

### Phase Requirements → Test Map

| Req ID  | Behavior                                                                 | Test Type   | Automated Command                                                           | File Exists? |
| ------- | ------------------------------------------------------------------------ | ----------- | --------------------------------------------------------------------------- | ------------ |
| SEC-01a | Auth endpoints return 429 after limit exceeded                           | integration | `pytest tests/core/test_security.py::test_rate_limit_returns_429 -x`        | Wave 0       |
| SEC-01b | 429 response includes `Retry-After` header                               | integration | `pytest tests/core/test_security.py::test_rate_limit_retry_after_header -x` | Wave 0       |
| SEC-01c | Rate limit counters NOT reset on Django restart (Redis-backed)           | integration | `pytest tests/core/test_security.py::test_rate_limit_uses_redis_cache -x`   | Wave 0       |
| SEC-02a | Django responses include `Content-Security-Policy` header                | integration | `pytest tests/core/test_security.py::test_csp_header_present -x`            | Wave 0       |
| SEC-02b | Django responses include `Strict-Transport-Security` header (production) | integration | `pytest tests/core/test_security.py::test_hsts_header_production -x`        | Wave 0       |
| SEC-02c | Django responses include `X-Frame-Options: DENY`                         | integration | `pytest tests/core/test_security.py::test_x_frame_options_header -x`        | Wave 0       |
| SEC-02d | Django responses include `Referrer-Policy` header                        | integration | `pytest tests/core/test_security.py::test_referrer_policy_header -x`        | Wave 0       |
| SEC-03a | `cache.get`/`cache.set` use Redis (not LocMemCache) in non-test env      | unit        | `pytest tests/core/test_security.py::test_default_cache_is_redis -x`        | Wave 0       |
| SEC-03b | Session reads/writes hit Redis backend in non-test env                   | unit        | `pytest tests/core/test_security.py::test_session_cache_is_redis -x`        | Wave 0       |

### Sampling Rate

- **Per task commit:** `cd apps/api && python -m pytest tests/core/test_security.py -x`
- **Per wave merge:** `cd apps/api && python -m pytest`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `apps/api/tests/core/test_security.py` — covers SEC-01, SEC-02, SEC-03; does not exist yet
- [ ] No new fixtures needed — existing `api_client` and `settings` fixtures from `tests/conftest.py` are sufficient
- [ ] No new packages for tests — existing `pytest-django` provides `settings` fixture and `@override_settings` support

---

## Sources

### Primary (HIGH confidence)

- `github.com/jazzband/django-redis` — CACHES configuration, session backend, multiple DB indexes, connection pool settings
- `django-ratelimit.readthedocs.io/en/stable/` — Decorator API, `RATELIMIT_ENABLE`, `RATELIMIT_FAIL_OPEN`, `RATELIMIT_USE_CACHE`, `RATELIMIT_VIEW`, `is_ratelimited()` helper
- `django-ratelimit.readthedocs.io/en/latest/cookbook/429.html` — 429 response pattern and custom error view
- `django-csp.readthedocs.io/en/latest/` — 4.0 configuration API, `CONTENT_SECURITY_POLICY` dict, `CSPMiddleware`, nonce lifecycle
- `nextjs.org/docs/app/guides/content-security-policy` — `headers()` config, static CSP approach, `unsafe-inline` for App Router, `unsafe-eval` in development
- `docs.allauth.org/en/dev/account/rate_limits.html` — `ACCOUNT_RATE_LIMITS` keys and defaults (login, signup, reset_password, confirm_email, change_password)

### Secondary (MEDIUM confidence)

- `pypi.org/project/django-redis/` — Version 6.0.0, Django 4.2+ compatibility — verified with PyPI
- `pypi.org/project/django-ratelimit/` — Version 4.1.0 — verified with PyPI

### Tertiary (LOW confidence)

- None

---

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — versions and APIs verified against official docs and PyPI
- Architecture: HIGH — patterns derived from official documentation examples
- Pitfalls: HIGH — django-csp 4.0 API change verified; allauth dual rate limiting verified from allauth docs; Redis URL derivation issue from direct code inspection of base.py

**Research date:** 2026-03-11
**Valid until:** 2026-06-11 (stable libraries; django-csp and django-ratelimit are mature, low churn)
