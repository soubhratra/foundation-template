# Phase 16: Security Hardening - Context

**Gathered:** 2026-03-11
**Status:** Ready for planning

<domain>
## Phase Boundary

Wire Redis as the default cache and session backend; add `django-ratelimit` rate limiting on
auth endpoints with Redis-backed counters; install `django-csp` + HSTS + security headers
middleware in Django; add matching `Content-Security-Policy` and `X-Frame-Options` headers
in Next.js via `headers()` config.

No user-visible UI. All changes affect HTTP infrastructure — every request passes through
these. Auth flow, billing pages, and API responses are unaffected beyond receiving headers.

</domain>

<decisions>
## Implementation Decisions

### Rate limiting

- Default limit: **5 requests per minute per IP** on all auth endpoints
- Scope: login, signup, password reset, email confirmation (allauth headless endpoints only)
- Password change endpoint included; all-API rate limiting is out of scope
- Fail behavior: **fail open** — if Redis is unreachable, requests pass through (auth availability > strict enforcement during outage)
- Configurability: **settings-based** — `RATELIMIT_AUTH_LOGIN = '5/m'` in `base.py`; projects override per risk tolerance (same pattern as `BILLING_ADAPTER`, `OBSERVABILITY_ADAPTER`)
- `Retry-After` header included in 429 responses (satisfies success criterion SC-01)

### CSP policy

- Mode: **enforcement from day one** (not report-only) — template is greenfield, stack is known, policy can be correct upfront
- Inline scripts: use **nonces** (django-csp injects automatically) — no `unsafe-inline`
- Third-party sources whitelisted in default template CSP:
  - PostHog: `eu.i.posthog.com` (default host) and `us.i.posthog.com`
  - Stripe: `js.stripe.com`, `hooks.stripe.com`
  - Projects extend via settings when they add additional third-party sources
- Next.js `headers()` config **mirrors Django's CSP** — same source list, single mental model, no drift
- Additional headers: `Strict-Transport-Security` (max-age=31536000; includeSubDomains), `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`
- HSTS enabled in production only (not dev — avoids HTTPS requirement during local development)

### Redis cache + session backend

- Applies to **dev and production** — Redis already runs in docker-compose for Celery; no extra setup required
- Separate Redis database indexes:
  - Celery: DB 0 (existing)
  - Cache: DB 1
  - Sessions: DB 2
  - Prevents `cache.clear()` from wiping sessions; allows independent TTL control
- Session TTL: **2 weeks** (matches Django's `SESSION_COOKIE_AGE = 1209600` default; django-redis respects this automatically)
- `SESSION_ENGINE = 'django.contrib.sessions.backends.cache'` pointing at the sessions cache

### Test suite isolation

- Rate limiting: **`RATELIMIT_ENABLE = False`** in test settings — django-ratelimit's official flag; tests hit auth endpoints freely without triggering 429s
- Cache backend in tests: **LocMemCache** — no Redis dependency in CI; fast, isolated per run
- Security headers middleware: **active in tests** — tests can assert headers are present (required by success criteria); adds no meaningful overhead

### Claude's Discretion

- Exact nonce implementation details in django-csp config
- CSP `connect-src` and `img-src` directive values beyond the core third-party sources
- django-redis connection pool settings (timeout, max connections)
- Exact middleware insertion order beyond "after SessionMiddleware"

</decisions>

<code_context>

## Existing Code Insights

### Reusable Assets

- `REDIS_URL` already defined in `base.py` (used by Celery) — reuse this same env var for `django-redis` CACHES config
- `SESSION_COOKIE_HTTPONLY = True`, `SESSION_COOKIE_SAMESITE = "Lax"` already set — no changes needed
- `SESSION_COOKIE_SECURE` already split: `False` in dev.py, `True` in production.py — HSTS should follow same pattern
- `apps/api/config/settings/base.py` → `development.py` → `production.py` structure established — test isolation settings go in `test.py` or conftest `@override_settings`

### Established Patterns

- Settings in `base.py` with env override; per-environment files for divergent values
- `BILLING_ADAPTER`, `OBSERVABILITY_ADAPTER` as settings-configurable paths — `RATELIMIT_AUTH_LOGIN` follows same pattern
- Middleware additions go in `MIDDLEWARE` list in `base.py` after `SessionMiddleware`
- Feature-specific constants grouped with comments (`# --- BILLING MODULE ---`, `# --- OBSERVABILITY ---`) — rate limit and CSP settings follow same grouping style

### Integration Points

- Allauth headless endpoints (`/api/v1/auth/browser/v1/`) — these are the targets for rate limiting decorators
- `apps/api/apps/accounts/controllers.py` (or `api.py`) — where `@ratelimit` decorators attach
- `apps/api/config/settings/` — CACHES, SESSION*ENGINE, CSP*\* settings added here
- `apps/web/next.config.ts` — `headers()` async function added to export security headers

</code_context>

<specifics>
## Specific Ideas

No specific product references. Standard security hardening for a greenfield SaaS template —
decisions above represent the conventional defaults for this stack.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

_Phase: 16-security-hardening_
_Context gathered: 2026-03-11_
