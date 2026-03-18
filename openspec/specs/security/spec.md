## Requirements

### Requirement: Dual Authentication Strategy with Secure Storage

The system SHALL implement session cookies for web and JWT tokens for mobile, with platform-appropriate secure storage mechanisms.

#### Scenario: Web session cookie configuration

- **WHEN** a user logs in on the Next.js web app
- **THEN** Django MUST set a session cookie with `httpOnly=True`, `Secure=True` (in production), and `SameSite=Lax`
- **THEN** the cookie MUST NOT be accessible via JavaScript `document.cookie`
- **THEN** the cookie MUST only be sent over HTTPS in production

#### Scenario: Mobile JWT storage

- **WHEN** a user logs in on the Expo mobile app
- **THEN** the access token MUST be stored in `expo-secure-store` under key `auth_access_token`
- **THEN** the refresh token MUST be stored in `expo-secure-store` under key `auth_refresh_token`
- **THEN** tokens MUST NOT be stored in `localStorage`, `sessionStorage`, or `AsyncStorage`

### Requirement: CSRF Protection for Session-Based Auth

The web application SHALL enforce CSRF protection for all state-changing requests using session authentication.

#### Scenario: CSRF token validation on form submission

- **WHEN** a logged-in web user submits a form that changes server state
- **THEN** the request MUST include the CSRF token in the `X-CSRFToken` header
- **THEN** Django MUST validate the CSRF token against the cookie
- **THEN** if the token is missing or invalid, Django MUST return HTTP 403

#### Scenario: Cross-site request attack prevention

- **WHEN** a malicious website attempts to submit a POST request to the Django API with a user's session cookie
- **THEN** the request MUST lack a valid CSRF token (attacker cannot read the CSRF cookie from different origin)
- **THEN** Django MUST reject the request with HTTP 403
- **THEN** no state change MUST occur on the server

### Requirement: CORS Policy with Explicit Allowed Origins

The Django API SHALL enforce CORS policy with explicitly allowed origins, never allowing all origins in production.

#### Scenario: CORS allowed origins in development

- **WHEN** Django runs in development mode
- **THEN** `CORS_ALLOWED_ORIGINS` MUST include `http://localhost:3000` and `http://localhost:8081`
- **THEN** `CORS_ALLOW_CREDENTIALS` MUST be `True` for session cookie auth

#### Scenario: CORS denied for unlisted origin

- **WHEN** a request arrives from an origin not in `CORS_ALLOWED_ORIGINS`
- **THEN** the Django CORS middleware MUST reject the request
- **THEN** the browser MUST NOT allow the response to be read by the requesting script

### Requirement: Secrets Management with Environment Variables

The system SHALL store all secrets in environment variables or `.env` files, never committing secrets to version control.

#### Scenario: SECRET_KEY generation and storage

- **WHEN** the CLI scaffolder creates a new project
- **THEN** it MUST generate a cryptographically random `SECRET_KEY`
- **THEN** it MUST write the key to `.env` file
- **THEN** `.env` MUST be listed in `.gitignore`
- **THEN** the repository MUST contain `.env.example` with placeholder value `django-insecure-change-me-in-production`

#### Scenario: Production secrets from environment

- **WHEN** the Django app runs in production
- **THEN** it MUST read `SECRET_KEY`, `DATABASE_URL`, and API keys from environment variables
- **THEN** secrets MUST NOT be hardcoded in any committed file

### Requirement: Input Validation with Double Validation Strategy

All user input SHALL be validated both client-side (Zod) and server-side (Pydantic) with identical constraints.

#### Scenario: Client-side Zod validation before API call

- **WHEN** a user submits a signup form on web or mobile
- **THEN** the Zod schema MUST validate the input before sending any API request
- **THEN** if validation fails, field errors MUST display inline
- **THEN** NO network request MUST be made

#### Scenario: Server-side Pydantic validation

- **WHEN** the Django API receives a request with user input
- **THEN** it MUST validate the input against a Pydantic schema
- **THEN** if validation fails, it MUST return HTTP 400 with field-level errors in standardized format
- **THEN** validation MUST enforce the same constraints as the client-side Zod schema

### Requirement: Dependency Vulnerability Scanning

The CI pipeline SHALL run automated dependency vulnerability scans for Python and JavaScript packages.

#### Scenario: Python dependency audit in CI

- **WHEN** the API CI job runs
- **THEN** it MUST execute `uv run pip-audit`
- **THEN** if known vulnerabilities are found, the build MUST fail

#### Scenario: JavaScript dependency audit in CI

- **WHEN** the web or mobile CI job runs
- **THEN** it MUST execute `pnpm audit --audit-level=high`
- **THEN** if high or critical vulnerabilities are found, the build MUST fail

### Requirement: Secure Database Access with Parameterized Queries

All database queries SHALL use parameterized queries via Django ORM or parameterized raw SQL to prevent SQL injection.

#### Scenario: ORM query safety

- **WHEN** a service layer queries the database
- **THEN** it MUST use Django ORM methods like `filter()`, `get()`, `create()`
- **THEN** user input MUST be passed as parameters, not interpolated into query strings

#### Scenario: Raw SQL with parameters

- **WHEN** raw SQL is necessary (e.g., PGVector similarity search)
- **THEN** the query MUST use parameterized placeholders: `cursor.execute("SELECT * FROM items WHERE id = %s", [user_input])`
- **THEN** string interpolation (f-strings, `%` formatting) MUST NOT be used

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
