# Phase 02: API Core + Auth Backend - Research

**Researched:** 2026-02-15
**Domain:** Django Ninja Extra API + django-allauth headless auth (session + JWT)
**Confidence:** MEDIUM

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
## Implementation Decisions

### Auth surface + responses
- Login identifier: email only.
- Signup fields: email + password + name.
- Signup/login responses: return user payload; session cookie set. JWT access/refresh tokens are issued only by JWT-specific endpoints (not by session login).
- Logout response: 204 No Content.

### Session vs JWT policy
- Default split: web uses session cookies; mobile uses JWT.
- JWT access token lifetime: short-lived (15 minutes).
- Refresh tokens: rotating refresh tokens.
- Session cookies default to HttpOnly + SameSite=Lax.

### Account verification rules
- Email verification is required before first login.
- Password reset token expiry: 24 hours.
- Password reset invalidates all existing sessions/JWTs.
- Verification email resend is rate-limited (approx. 1/min).

### OpenAPI exposure
- /api/docs requires auth in dev and is protected in prod.
- OpenAPI export format: JSON only.
- Export location: packages/api-client/openapi.json.

### Claude's Discretion
- Exact error message wording for auth failures (within normalized error envelope).
- Exact rate-limit enforcement mechanism for verification resends (policy stays as defined above).

### Claude's Discretion
- Exact error message wording for auth failures (within normalized error envelope).
- Exact rate-limit enforcement mechanism for verification resends (policy stays as defined above).

### Deferred Ideas (OUT OF SCOPE)
## Deferred Ideas

None — discussion stayed within phase scope.
</user_constraints>

## Summary

Phase 02 should lean on django-allauth headless for the entire auth surface (signup/login/logout, email verification, password reset) while keeping Django Ninja Extra as the API boundary for all non-allauth endpoints. The headless module provides token strategies for session and JWT flows, settings for access/refresh lifetimes and rotation, and OpenAPI spec endpoints if needed. That maps cleanly to the dual auth split: browser uses Django sessions + CSRF, mobile uses JWT access/refresh with rotation.

For planning, the key is wiring settings and middleware correctly (HEADLESS_ONLY, HEADLESS_FRONTEND_URLS, HEADLESS_TOKEN_STRATEGY), enforcing the email verification rule, and implementing rate limits using allauth’s built-in ACCOUNT_RATE_LIMITS for confirmation emails. OpenAPI remains owned by Ninja Extra; export JSON to `packages/api-client/openapi.json` via management command, and restrict `/api/docs` access since it is public by default.

**Primary recommendation:** Use django-allauth headless JWT token strategy for mobile and Django sessions for web, with Ninja Extra controllers for non-auth endpoints and a dedicated OpenAPI export command.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Django | 5.x (pin in `apps/api/pyproject.toml`) | Core web framework | Required by stack and Ninja Extra | 
| django-ninja-extra | pinned in `apps/api/pyproject.toml` | API framework with class-based controllers and OpenAPI | Required by stack; controller pattern in specs | 
| django-allauth (headless) | pinned in `apps/api/pyproject.toml` | Auth endpoints + session/JWT token strategies | Required by stack; headless supports SPA/mobile auth | 

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| django-cors-headers | pinned | CORS for cross-origin web/mobile clients | Required for session cookies + API access | 
| django-environ | pinned | Env var management for settings | Standard settings loading | 
| psycopg | pinned | Postgres adapter | Required by stack | 
| django-allauth[headless-spec] | optional extra | Serve headless OpenAPI spec endpoints | Only if `/ _allauth /openapi.json` is needed | 

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| allauth headless JWT tokens | custom JWT libs (e.g., simplejwt) | Adds a second auth system; violates spec preference for allauth headless |

**Installation:**
```bash
uv add django django-ninja-extra django-allauth django-cors-headers django-environ psycopg[binary]
# Optional if serving headless OpenAPI endpoints:
uv add "django-allauth[headless-spec]"
```

## Architecture Patterns

### Recommended Project Structure
```
apps/api/
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   └── urls.py
└── apps/
    ├── accounts/
    │   ├── models.py
    │   ├── schemas.py
    │   ├── controllers.py
    │   └── services.py
    └── core/
        ├── controllers.py
        └── management/commands/export_openapi_schema.py
```

### Pattern 1: Headless Auth Configuration + Token Strategy
**What:** Configure django-allauth headless to run without HTML views, map frontend URLs, and choose JWT token strategy for mobile. 
**When to use:** Always in this template; required to meet dual auth split and email/verification policies.
**Example:**
```python
# Source: https://docs.allauth.org/en/latest/headless/configuration.html
HEADLESS_ONLY = True
HEADLESS_FRONTEND_URLS = {
    "account_confirm_email": "{FRONTEND_URL}/auth/verify-email/{key}",
    "account_reset_password_from_key": "{FRONTEND_URL}/auth/reset-password/{key}",
}

# Source: https://docs.allauth.org/en/latest/headless/token-strategies/jwt-tokens.html
HEADLESS_TOKEN_STRATEGY = "allauth.headless.tokens.strategies.jwt.JWTTokenStrategy"
HEADLESS_JWT_ACCESS_TOKEN_EXPIRES_IN = 900  # 15 minutes
HEADLESS_JWT_ROTATE_REFRESH_TOKEN = True
HEADLESS_JWT_STATEFUL_VALIDATION_ENABLED = True
```

### Pattern 2: Ninja Extra Controllers + Auto-Discovery
**What:** Use class-based controllers for endpoints and let Ninja Extra auto-discover them. 
**When to use:** All API endpoints outside allauth headless, including `/users/me` and `/health`.
**Example:**
```python
# Source: https://eadwincode.github.io/django-ninja-extra/
from ninja_extra import NinjaExtraAPI, api_controller, http_get

api = NinjaExtraAPI()

@api_controller("/health", tags=["Health"])
class HealthController:
    @http_get("/")
    def health(self, request):
        return {"status": "healthy"}

# in config/urls.py
# urlpatterns = [path("api/v1/", api.urls)]
```

### Pattern 3: Allauth JWT Auth for Ninja Endpoints (Mobile)
**What:** Use the allauth headless Ninja security class for JWT validation on mobile-authenticated endpoints.
**When to use:** When endpoints must accept JWT access tokens from mobile.
**Example:**
```python
# Source: https://docs.allauth.org/en/latest/headless/token-strategies/jwt-tokens.html
from allauth.headless.contrib.ninja.security import jwt_token_auth
from ninja import NinjaAPI

api = NinjaAPI()

@api.get("/mobile-only", auth=[jwt_token_auth])
def mobile_only(request):
    return {"ok": True}
```

### Anti-Patterns to Avoid
- **Custom auth endpoints over allauth headless:** Breaks the single auth system; causes inconsistent email verification and token behavior.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Auth endpoints | Custom signup/login/logout views | django-allauth headless API | Avoids drift; includes email verification, password reset, token flow |
| JWT refresh + rotation | Custom refresh tables | allauth HEADLESS_JWT_* settings | Built-in rotation, expiration, and validation | 
| Email verification resend throttling | Custom per-IP throttler | ACCOUNT_RATE_LIMITS.confirm_email | Official allauth rate limit hooks |
| OpenAPI generation | Manual schema writing | Ninja Extra OpenAPI export | Single source of truth |

**Key insight:** allauth headless already provides session/JWT flows and rate limiting hooks; custom work increases security risk and drift.

## Common Pitfalls

### Pitfall 1: Email verification resend not rate-limited
**What goes wrong:** Users can spam resend endpoints, triggering abuse and email provider throttling.
**Why it happens:** ACCOUNT_RATE_LIMITS not set for confirm_email.
**How to avoid:** Set `ACCOUNT_RATE_LIMITS` to include `"confirm_email": "1/m/key"` to match the 1/min policy.
**Warning signs:** Burst of verification emails per account or IP.

### Pitfall 2: Logout does not invalidate JWTs
**What goes wrong:** JWT access tokens remain valid after logout.
**Why it happens:** `HEADLESS_JWT_STATEFUL_VALIDATION_ENABLED` left disabled.
**How to avoid:** Enable stateful validation and invalidate sessions on logout/password reset.
**Warning signs:** Access tokens still accepted post-logout.

### Pitfall 3: CSRF errors on web mutations
**What goes wrong:** Session-authenticated POST/PATCH/DELETE fail with CSRF errors.
**Why it happens:** CSRF cookie not read or X-CSRFToken header missing.
**How to avoid:** Ensure CSRF cookie is readable and forwarded by the web client; keep CSRF middleware enabled.
**Warning signs:** 403 CSRF failures for authenticated web users.

### Pitfall 4: Public `/api/docs` in production
**What goes wrong:** Swagger UI is exposed to unauthenticated users.
**Why it happens:** Ninja Extra docs endpoint defaults to public access.
**How to avoid:** Gate `/api/docs` behind auth in dev and protect in prod (middleware or URL routing).
**Warning signs:** Docs accessible without session/JWT.

## Code Examples

Verified patterns from official sources:

### Configure Headless Settings
```python
# Source: https://docs.allauth.org/en/latest/headless/configuration.html
HEADLESS_ONLY = True
HEADLESS_FRONTEND_URLS = {
    "account_confirm_email": "https://app.project.org/account/verify-email/{key}",
    "account_reset_password_from_key": "https://app.project.org/account/password/reset/key/{key}",
}
```

### JWT Token Strategy Settings
```python
# Source: https://docs.allauth.org/en/latest/headless/token-strategies/jwt-tokens.html
HEADLESS_JWT_ACCESS_TOKEN_EXPIRES_IN = 300
HEADLESS_JWT_REFRESH_TOKEN_EXPIRES_IN = 86400
HEADLESS_JWT_ROTATE_REFRESH_TOKEN = True
```

### Allauth Rate Limit Configuration
```python
# Source: https://docs.allauth.org/en/latest/account/rate_limits.html
ACCOUNT_RATE_LIMITS = {
    "confirm_email": "1/m/key",
    "login": "30/m/ip",
    "signup": "20/m/ip",
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Custom JWT libs for mobile auth | allauth headless JWT token strategy | allauth headless introduced | Single auth system, consistent verification and logout |

**Deprecated/outdated:**
- Custom signup/login endpoints bypassing allauth — breaks headless flows and rate limits.

## Open Questions

1. **How to invalidate all sessions/JWTs on password reset?**
   - What we know: allauth supports session tracking (usersessions) and JWT stateful validation.
   - What's unclear: the canonical hook to purge all sessions when password reset completes.
   - Recommendation: verify allauth usersessions + password reset signals, then implement a purge using official hooks.

2. **Best mechanism to protect `/api/docs` in Ninja Extra?**
   - What we know: docs endpoint is public by default.
   - What's unclear: whether Ninja Extra exposes built-in auth guards for docs.
   - Recommendation: confirm in Ninja Extra docs and add middleware gating if needed.

3. **Final auth URL mapping for allauth headless endpoints**
   - What we know: headless endpoints live under `/_allauth/` and can serve spec if enabled.
   - What's unclear: whether to proxy through `/api/v1/auth/*` or use direct headless URLs.
   - Recommendation: decide in planning based on API surface expectations and frontend client needs.

## Sources

### Primary (HIGH confidence)
- https://docs.allauth.org/en/latest/headless/configuration.html - headless settings, token strategy, OpenAPI spec serving
- https://docs.allauth.org/en/latest/headless/token-strategies/jwt-tokens.html - JWT strategy settings and Ninja auth helper
- https://docs.allauth.org/en/latest/headless/token-strategies/session-tokens.html - session token behavior and Ninja auth helper
- https://docs.allauth.org/en/latest/account/rate_limits.html - ACCOUNT_RATE_LIMITS actions and defaults

### Secondary (MEDIUM confidence)
- https://eadwincode.github.io/django-ninja-extra/ - Ninja Extra API/controller patterns and docs access

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: MEDIUM - versions not pinned yet; stack choices locked by specs
- Architecture: MEDIUM - core patterns verified, but some operational details need confirmation
- Pitfalls: MEDIUM - based on docs + template constraints

**Research date:** 2026-02-15
**Valid until:** 2026-03-17
