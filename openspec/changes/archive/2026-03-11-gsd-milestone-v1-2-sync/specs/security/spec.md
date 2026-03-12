## ADDED Requirements

### Requirement: Auth Endpoint Rate Limiting with Redis Backend

The Django API SHALL rate-limit authentication endpoints using `django-ratelimit` backed by Redis to prevent credential stuffing and brute-force attacks.

#### Scenario: Login endpoint rate-limited by IP

- **WHEN** more than the configured limit of login requests arrive from a single IP within the rate window
- **THEN** `django-ratelimit` MUST return HTTP 429 with a `Retry-After` header
- **AND** the rate limit MUST be configurable per endpoint via `RATELIMIT_*` Django settings
- **AND** the rate counter MUST be stored in Redis so it persists across Django process restarts and scales across multiple workers

#### Scenario: Rate limit state survives Django restart

- **WHEN** the Django process is restarted
- **THEN** the rate limit counters MUST persist in Redis
- **AND** a user who was near the limit before the restart MUST remain near the limit after restart

#### Scenario: Rate limiting disabled in tests

- **WHEN** `RATELIMIT_ENABLE = False` is set in test settings
- **THEN** all rate limit decorators MUST be bypassed
- **AND** tests MUST NOT depend on Redis being available for rate limit state

### Requirement: HTTP Security Headers

The Django API and Next.js web app SHALL send HTTP security headers on every response to defend against XSS, clickjacking, and information leakage.

#### Scenario: Django sends security headers via django-csp and middleware

- **WHEN** any Django HTTP response is returned
- **THEN** it MUST include `Content-Security-Policy` (via `django-csp` with per-request nonces for inline scripts)
- **AND** it MUST include `X-Frame-Options: DENY`
- **AND** it MUST include `Referrer-Policy: strict-origin-when-cross-origin`
- **AND** in production, it MUST include `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- **AND** HSTS MUST NOT be set in development (to avoid breaking localhost)

#### Scenario: Next.js sends matching security headers via next.config.ts

- **WHEN** any Next.js page or API route responds
- **THEN** the `headers()` function in `next.config.ts` MUST apply `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`, and `X-Content-Type-Options: nosniff` to all routes
- **AND** CSP headers MUST be coordinated with the Django API to allow the web app's origin

#### Scenario: CSP nonces for inline scripts

- **WHEN** a Django template or middleware generates an HTTP response with inline scripts
- **THEN** `django-csp` MUST inject a unique per-request nonce into both the CSP header and the inline script tag
- **AND** inline scripts without a valid nonce MUST be blocked by the browser

### Requirement: Redis as Default Cache and Session Backend

Django SHALL use Redis as the default cache and session backend, replacing `LocMemCache`, to support multi-process and multi-instance deployments.

#### Scenario: Cache reads and writes go to Redis

- **WHEN** Django code calls `cache.set(key, value)` or `cache.get(key)`
- **THEN** the operation MUST target the Redis instance configured at `CACHE_REDIS_URL`
- **AND** Redis database 1 MUST be used for caching (isolating from Celery broker on DB 0)
- **AND** the `django-redis` backend MUST be configured in `CACHES["default"]`

#### Scenario: Session data stored in Redis

- **WHEN** a user logs in and a session is created
- **THEN** the session data MUST be stored in Redis at `SESSION_REDIS_URL` (database 2)
- **AND** the session cookie MUST reference only a session key, not contain session data
- **AND** sessions MUST expire according to `SESSION_COOKIE_AGE`

#### Scenario: Separate Redis databases prevent key collisions

- **WHEN** Celery broker (DB 0), Django cache (DB 1), and session backend (DB 2) all use the same Redis instance
- **THEN** keys from each subsystem MUST reside in separate logical databases
- **AND** flushing the cache database MUST NOT affect Celery task queue or session data
