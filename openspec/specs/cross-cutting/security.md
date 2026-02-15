# Security

> Baseline specification for the Foundation Template.
> This document is the source of truth. All implementations must conform to these specs.

## Overview

Security in the Foundation Template is applied at every layer: authentication and session management, CSRF and CORS protection, secrets management, input validation, database access, API exposure, and dependency auditing. The template implements a dual-auth strategy -- session cookies for the web frontend and JWT tokens for the mobile app -- with platform-appropriate storage and transport mechanisms. Security defaults are strict; loosening them requires explicit configuration changes.

---

## Specifications

### 1. Authentication Security

#### 1.1 Dual Auth Strategy

| Platform | Auth Mechanism | Token Storage | Token Transport |
|----------|---------------|---------------|-----------------|
| Web (Next.js) | Session cookies | httpOnly cookie (server-managed) | Cookie header (automatic) |
| Mobile (Expo) | JWT access + refresh tokens | `expo-secure-store` | `Authorization: Bearer <token>` header |

#### 1.2 Session Cookie Configuration (Web)

```python
# config/settings/base.py
SESSION_COOKIE_HTTPONLY = True     # Not accessible via JavaScript
SESSION_COOKIE_SECURE = True      # Sent only over HTTPS (set False for local dev)
SESSION_COOKIE_SAMESITE = "Lax"   # Sent with same-site and top-level navigation requests
SESSION_COOKIE_AGE = 1209600      # 14 days
SESSION_COOKIE_NAME = "sessionid"
```

| Attribute | Value | Rationale |
|-----------|-------|-----------|
| `httpOnly` | `True` | Prevents XSS attacks from reading the session cookie via `document.cookie` |
| `Secure` | `True` (prod) / `False` (dev) | Ensures cookies are only sent over HTTPS in production |
| `SameSite` | `Lax` | Blocks cross-site POST requests while allowing top-level navigation |
| `Domain` | Not set (dev) / `.example.com` (prod) | Scoped to the specific domain; shared across subdomains in production |

#### 1.3 JWT Token Configuration (Mobile)

| Token | Lifetime | Storage | Purpose |
|-------|----------|---------|---------|
| Access token | 15 minutes | `expo-secure-store` | Authenticates API requests |
| Refresh token | 7 days | `expo-secure-store` | Obtains new access tokens without re-login |

- Access tokens are short-lived to limit the window of compromise if intercepted.
- Refresh tokens are long-lived but stored in the device's secure enclave (Keychain on iOS, Keystore on Android) via `expo-secure-store`.
- Token refresh happens transparently via the API client interceptor.

#### 1.4 Forbidden Token Storage

| Storage Mechanism | Platform | Permitted? | Reason |
|-------------------|----------|------------|--------|
| `localStorage` | Web | NO | Accessible via XSS; tokens readable by any injected script |
| `sessionStorage` | Web | NO | Same XSS vulnerability as localStorage |
| `AsyncStorage` | Mobile | NO | Stored in plaintext on device filesystem; readable with root/jailbreak access |
| httpOnly cookie | Web | YES | Not accessible to JavaScript |
| `expo-secure-store` | Mobile | YES | Uses OS-level secure storage (Keychain/Keystore) |

#### 1.5 Password Hashing

Django's default password hasher is PBKDF2 with SHA256 and a per-user salt. The template does not change this default.

```python
# Django default (no configuration needed):
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]
```

- Passwords are never stored in plaintext.
- Passwords are never logged at any level.
- The password hashing iterations count increases with each Django release automatically.

---

### 2. CSRF Protection

#### 2.1 Web (Session-Based Auth)

CSRF protection is enabled by default in Django and remains enabled for all web-facing endpoints.

```python
# config/settings/base.py
CSRF_COOKIE_HTTPONLY = False       # Frontend JS needs to read the CSRF token
CSRF_COOKIE_SECURE = True         # HTTPS only in production
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_TRUSTED_ORIGINS = [
    "https://app.example.com",    # Production web frontend
]
```

```python
# config/settings/development.py
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",       # Next.js dev server
]
CSRF_COOKIE_SECURE = False        # Allow HTTP in development
```

#### 2.2 Next.js API Proxy for Same-Origin Cookies

The recommended pattern routes API calls through Next.js rewrites so that the browser perceives the API as same-origin, eliminating CSRF cross-origin complexity:

```javascript
// next.config.ts
async rewrites() {
  return [
    {
      source: "/api/:path*",
      destination: `${process.env.DJANGO_API_URL}/api/:path*`,
    },
  ];
}
```

When using this proxy pattern:
- The browser sends cookies to `localhost:3000/api/*` (same origin).
- Next.js forwards the request to `localhost:8000/api/*` (Django).
- CSRF cookie is set on the Next.js origin, so it travels with every request.

#### 2.3 Mobile (Token-Based Auth)

CSRF protection is not applicable to mobile API requests because:
- Mobile uses `Authorization: Bearer <token>` headers, not cookies.
- CSRF attacks exploit automatic cookie inclusion in browser requests. Mobile HTTP clients do not automatically include cookies.
- Django's CSRF middleware skips token-authenticated requests.

---

### 3. CORS Configuration

#### 3.1 Explicit Allowed Origins

```python
# config/settings/base.py
CORS_ALLOWED_ORIGINS = []  # Override in environment-specific settings

CORS_ALLOW_CREDENTIALS = True  # Required for session cookie auth
CORS_ALLOW_HEADERS = [
    "accept",
    "authorization",
    "content-type",
    "x-csrftoken",
    "x-requested-with",
]
```

```python
# config/settings/development.py
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",   # Next.js dev server
    "http://localhost:8081",   # Expo Metro bundler
]
```

```python
# config/settings/production.py
import os
CORS_ALLOWED_ORIGINS = os.environ.get(
    "CORS_ALLOWED_ORIGINS", ""
).split(",")
# Example: CORS_ALLOWED_ORIGINS=https://app.example.com,https://admin.example.com
```

#### 3.2 Forbidden CORS Patterns

| Pattern | Permitted? | Reason |
|---------|------------|--------|
| `CORS_ALLOW_ALL_ORIGINS = True` | NEVER in production | Allows any website to make authenticated API requests |
| Wildcard `*` in allowed origins | NEVER | Same as allow-all; defeats CORS purpose |
| `CORS_ALLOW_ALL_ORIGINS = True` in development | Acceptable | Simplifies local dev; overridden in production settings |

---

### 4. Secrets Management

#### 4.1 Django SECRET_KEY

- Each project instance MUST have a unique `SECRET_KEY`.
- The CLI scaffolder generates a cryptographically random `SECRET_KEY` when creating a new project from the template.
- The template repository contains `SECRET_KEY=django-insecure-change-me-in-production` in `.env.example` as a placeholder.
- The actual `SECRET_KEY` lives in `.env` (gitignored) or in environment variables in production.

#### 4.2 Environment Variable Strategy

| Secret | Where Stored | Committed to Git? |
|--------|-------------|-------------------|
| `SECRET_KEY` | `.env` / environment variable | No |
| `DATABASE_URL` | `.env` / environment variable | No |
| `OPENAI_API_KEY` | `.env` / environment variable | No |
| `ANTHROPIC_API_KEY` | `.env` / environment variable | No |
| `STRIPE_SECRET_KEY` | `.env` / environment variable | No |
| `.env.example` | Repository root | Yes (dummy values only) |

```bash
# .env.example (committed)
SECRET_KEY=django-insecure-change-me-in-production
DATABASE_URL=postgres://foundation:foundation@localhost:5432/foundation
DEBUG=True
OPENAI_API_KEY=sk-your-key-here
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

- `.env` files are listed in `.gitignore` at the repository root.
- `.env.example` files contain placeholder/dummy values and are committed.
- Developers copy `.env.example` to `.env` and fill in real values.
- In production, secrets are provided via environment variables from the deployment platform (not from `.env` files).

---

### 5. Input Validation

#### 5.1 Double Validation Strategy

All user input is validated twice: once on the client (Zod) and once on the server (Pydantic).

```
User Input
  |
  v
[Client: Zod schema validation]
  |-- Fails: Show field errors immediately, do NOT send request
  |-- Passes: Send request to API
  |
  v
[Server: Pydantic schema validation]
  |-- Fails: Return 400 with field errors in standardized format
  |-- Passes: Process request
```

#### 5.2 Backend Validation (Pydantic)

```python
# apps/api/apps/accounts/schemas.py
from ninja import Schema
from pydantic import Field, EmailStr

class SignupIn(Schema):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    first_name: str = Field(..., min_length=1, max_length=150)
    last_name: str = Field(..., min_length=1, max_length=150)
```

- Every API endpoint that accepts input uses a Pydantic schema.
- No endpoint processes raw `request.body` or `request.POST` directly.
- Pydantic schemas define all constraints: types, lengths, patterns, required/optional.

#### 5.3 Frontend Validation (Zod)

```typescript
// packages/schemas/src/auth.ts
import { z } from "zod";

export const signupSchema = z.object({
  email: z.string().email("Enter a valid email address."),
  password: z.string().min(8, "Password must be at least 8 characters.").max(128),
  first_name: z.string().min(1, "First name is required.").max(150),
  last_name: z.string().min(1, "Last name is required.").max(150),
});

export type SignupInput = z.infer<typeof signupSchema>;
```

- Zod schemas live in `packages/schemas/` and are shared between web and mobile.
- Zod schemas mirror the constraints of the corresponding Pydantic schemas.
- Client-side validation is a UX optimization, not a security boundary. The server MUST re-validate all input regardless of what the client validated.

---

### 6. OpenAPI Spec Exposure

```python
# config/settings/base.py
OPENAPI_DOCS_ENABLED = False  # Default: do not serve docs

# config/settings/development.py
OPENAPI_DOCS_ENABLED = True  # Serve Swagger/Redoc in development

# config/api.py
from django.conf import settings

api = NinjaExtraAPI(
    title="Foundation API",
    version="1.0.0",
    docs_url="/api/docs" if settings.OPENAPI_DOCS_ENABLED else None,
    openapi_url="/api/openapi.json" if settings.OPENAPI_DOCS_ENABLED else None,
)
```

| Environment | `/api/docs` | `/api/openapi.json` | Rationale |
|-------------|-------------|---------------------|-----------|
| Development | Served | Served | Developers need docs and the spec for type generation |
| Staging | Served (optional) | Served (optional) | QA may need docs; restrict via network/auth if exposed |
| Production | NOT served | NOT served | Prevents attackers from discovering API surface area |

---

### 7. Database Security

#### 7.1 Parameterized Queries

- All database access goes through Django ORM, which uses parameterized queries by default.
- Raw SQL is permitted only when the ORM cannot express the query (e.g., PGVector similarity search).
- Raw SQL MUST use parameterized queries:

```python
# Correct: parameterized
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute(
        "SELECT * FROM items ORDER BY embedding <=> %s LIMIT %s",
        [embedding_vector, limit]
    )

# FORBIDDEN: string interpolation
cursor.execute(f"SELECT * FROM items WHERE id = {user_input}")  # SQL injection
```

#### 7.2 PGVector Dimension Validation

Embedding vectors MUST be validated for correct dimensions before storage or query:

```python
# apps/api/apps/ai/services.py
EMBEDDING_DIMENSION = 1536  # OpenAI text-embedding-3-small

def validate_embedding(embedding: list[float]) -> None:
    if len(embedding) != EMBEDDING_DIMENSION:
        raise ValueError(
            f"Embedding dimension mismatch: expected {EMBEDDING_DIMENSION}, "
            f"got {len(embedding)}"
        )
```

- Mismatched dimensions cause cryptic Postgres errors.
- The expected dimension is defined as a constant and referenced in both the model field and the validation function.
- The Django model uses `VectorField(dimensions=1536)` which enforces the constraint at the database level.

---

### 8. Dependency Security

#### 8.1 Automated Dependency Updates

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/apps/api"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5

  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
```

#### 8.2 Vulnerability Scanning

| Tool | Ecosystem | When Run | Action on Finding |
|------|-----------|----------|-------------------|
| `pip-audit` | Python | CI pipeline, weekly | Fail build on known vulnerabilities |
| `pnpm audit` | JavaScript/TypeScript | CI pipeline, weekly | Fail build on high/critical vulnerabilities |
| Dependabot / Renovate | Both | Automated PRs | Review and merge dependency update PRs |

```yaml
# In CI pipeline
- name: Audit Python dependencies
  run: cd apps/api && uv run pip-audit

- name: Audit JS dependencies
  run: pnpm audit --audit-level=high
```

---

### 9. Additional Security Headers

```python
# config/settings/production.py
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000        # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True
X_FRAME_OPTIONS = "DENY"
```

| Header | Value | Purpose |
|--------|-------|---------|
| `X-Content-Type-Options` | `nosniff` | Prevents MIME type sniffing |
| `X-Frame-Options` | `DENY` | Prevents clickjacking via iframe embedding |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains; preload` | Forces HTTPS for all future requests |
| `X-XSS-Protection` | `1; mode=block` | Legacy XSS filter (modern CSP is preferred) |

---

### 10. GIVEN/WHEN/THEN Scenarios

#### Scenario: CSRF Token Handling on Web Form Submission

```
GIVEN a user is logged in on the web frontend
  AND the browser holds a session cookie and a CSRF cookie
  AND the Next.js app proxies API requests through rewrites (same-origin)
WHEN the user submits a form (e.g., updating their profile)
THEN the JavaScript reads the CSRF token from the CSRF cookie
  AND the request includes the CSRF token in the X-CSRFToken header
  AND Django validates the CSRF token against the cookie
  AND the request is processed successfully
  AND no CSRF-related 403 error occurs
```

```
GIVEN a malicious website attempts a cross-site POST to the Django API
  AND the user is logged in with a session cookie
WHEN the malicious site sends a POST request to the API
THEN the request lacks a valid CSRF token (attacker cannot read the httpOnly-adjacent CSRF cookie from a different origin)
  AND Django rejects the request with 403 Forbidden
  AND no state change occurs on the server
```

#### Scenario: Token Refresh Flow on Mobile

```
GIVEN a mobile user has a valid refresh token stored in expo-secure-store
  AND their access token has expired (15-minute lifetime passed)
WHEN the user opens the app and triggers an API request
THEN the API returns 401 (access token expired)
  AND the API client interceptor catches the 401
  AND the interceptor sends POST /api/v1/auth/token/refresh with the refresh token
  AND the server validates the refresh token and issues a new access token
  AND the interceptor stores the new access token in expo-secure-store
  AND the interceptor retries the original request with the new access token
  AND the user sees the data load without any login prompt
```

```
GIVEN a mobile user's refresh token has also expired (7-day lifetime passed)
WHEN the token refresh attempt returns 401
THEN both tokens are deleted from expo-secure-store
  AND the user is navigated to the login screen
  AND a message displays: "Your session has expired. Please log in again."
```

#### Scenario: Unauthorized Access Attempt

```
GIVEN an unauthenticated client sends a request to GET /api/v1/users/me
  AND no Authorization header or session cookie is present
WHEN Django Ninja Extra processes the request
THEN the IsAuthenticated permission check fails
  AND the API returns 401 with error code AUTH_001
  AND the response body is:
    {
      "error": {
        "code": "AUTH_001",
        "message": "Authentication credentials were not provided.",
        "details": {}
      }
    }
  AND no user data is exposed
```

```
GIVEN an authenticated user sends a request to an admin-only endpoint
  AND the user does not have admin privileges
WHEN Django Ninja Extra processes the request
THEN the permission check fails
  AND the API returns 403 with error code AUTH_005
  AND the response body is:
    {
      "error": {
        "code": "AUTH_005",
        "message": "You do not have permission to perform this action.",
        "details": {}
      }
    }
```

#### Scenario: Secret Rotation

```
GIVEN the Django SECRET_KEY needs to be rotated (suspected compromise or routine rotation)
WHEN the operations team generates a new SECRET_KEY
  AND updates the environment variable in the deployment platform
  AND restarts the Django application
THEN all existing session cookies are invalidated
  AND all logged-in web users are required to log in again
  AND JWT tokens issued with the old key fail signature verification
  AND mobile users with expired access tokens trigger a refresh, which also fails
  AND mobile users are redirected to login
  AND no data loss occurs (SECRET_KEY is used for signing, not encryption of user data)
  AND the application logs an INFO message: "Application started with new SECRET_KEY"
```

---

## Constraints

- `CORS_ALLOW_ALL_ORIGINS` MUST be `False` in production settings. No exceptions.
- Tokens MUST NOT be stored in `localStorage`, `sessionStorage`, or `AsyncStorage`. Only httpOnly cookies (web) and `expo-secure-store` (mobile) are permitted.
- All API endpoints that accept user input MUST use Pydantic schemas for validation. No raw body parsing.
- All raw SQL queries MUST use parameterized queries. String interpolation in SQL is forbidden.
- The OpenAPI documentation endpoints (`/api/docs`, `/api/openapi.json`) MUST NOT be served in production.
- `.env` files MUST be listed in `.gitignore`. Only `.env.example` with dummy values is committed.
- The Django `SECRET_KEY` MUST be unique per project instance. The template placeholder value MUST NOT be used in any deployed environment.
- CSRF protection MUST remain enabled for all web-facing endpoints. `@csrf_exempt` decorators are forbidden on API endpoints.
- `pip-audit` and `pnpm audit` MUST run in CI. Builds MUST fail on known high/critical vulnerabilities.
- PGVector embedding inputs MUST be validated for correct dimensions before database operations.

---

## References

- `.planning/research/STACK.md` -- django-cors-headers, django-environ, expo-secure-store, session configuration
- `.planning/research/ARCHITECTURE.md` -- Dual auth strategy (session for web, JWT for mobile), CSRF proxy pattern, environment variable strategy
- `.planning/research/PITFALLS.md` -- Auth misconfiguration pitfalls, CSRF disabling anti-pattern, secrets in git, OpenAPI exposure
- `.planning/PROJECT.md` -- Auth requirements (Django Allauth), security constraints
