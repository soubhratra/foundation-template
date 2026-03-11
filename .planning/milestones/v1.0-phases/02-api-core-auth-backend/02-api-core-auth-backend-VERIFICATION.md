---
phase: 02-api-core-auth-backend
verified: 2026-02-15T00:00:00Z
status: gaps_found
score: 15/18 must-haves verified
gaps:
  - truth: "Signup/login responses return user payload and session login does not issue JWTs"
    status: failed
    reason: "Headless adapter provides user payload, but no response serializer/adapter overrides exist to suppress JWTs for session login responses."
    artifacts:
      - path: "apps/api/apps/accounts/headless.py"
        issue: "No login response customization to remove JWTs for session-based logins."
    missing:
      - "Headless response customization that omits JWTs for session logins while preserving user payload."
  - truth: "Logout returns HTTP 204 with no response body"
    status: failed
    reason: "Only the custom session view returns 204; the headless logout endpoint is not overridden to enforce empty 204 responses."
    artifacts:
      - path: "apps/api/apps/accounts/sessions.py"
        issue: "204 response implemented only for session endpoint, not headless logout."
    missing:
      - "Logout response override for headless endpoints to return 204 with empty body."
  - truth: "Password reset invalidates all existing sessions and JWTs for the user"
    status: failed
    reason: "Password reset handler only invalidates Django sessions; no JWT revocation is performed despite stateful JWT validation being enabled."
    artifacts:
      - path: "apps/api/apps/accounts/signals.py"
        issue: "Calls session invalidation only; no JWT revocation."
      - path: "apps/api/apps/accounts/services.py"
        issue: "No JWT revocation logic or token store handling."
    missing:
      - "JWT revocation when password reset occurs (stateful token store cleanup)."
---

# Phase 2: API Core + Auth Backend Verification Report

**Phase Goal:** Django API serves authenticated endpoints with auto-generated OpenAPI spec; dual auth strategy (session cookies for web, JWT for mobile) is configured and testable via API client
**Verified:** 2026-02-15T00:00:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #   | Truth                                                                                          | Status     | Evidence                                                                                                                          |
| --- | ---------------------------------------------------------------------------------------------- | ---------- | --------------------------------------------------------------------------------------------------------------------------------- |
| 1   | GET /api/v1/health returns status and database connectivity                                    | ✓ VERIFIED | `apps/api/apps/core/controllers.py` returns status/database with DB cursor check.                                                 |
| 2   | /api/docs is accessible only to authenticated users in development and protected in production | ✓ VERIFIED | `apps/api/config/urls.py` `docs_guard` enforces auth and staff-only in prod.                                                      |
| 3   | API errors return the standardized error envelope                                              | ✓ VERIFIED | `apps/api/config/urls.py` handlers return `{error:{code,message,details}}`.                                                       |
| 4   | Custom user model is configured before running initial migrations                              | ✓ VERIFIED | `apps/api/config/settings/base.py` `AUTH_USER_MODEL` set and `apps/api/apps/accounts/migrations/0001_initial.py` exists.          |
| 5   | Django admin is enabled and accessible for staff users                                         | ✓ VERIFIED | `apps/api/config/urls.py` includes `admin/` and `apps/api/apps/accounts/admin.py` registers user.                                 |
| 6   | Database migrations run against Postgres                                                       | ✓ VERIFIED | `apps/api/config/settings/base.py` uses `env.db("DATABASE_URL")` with Postgres default.                                           |
| 7   | Headless auth endpoints are available under /api/v1/auth/                                      | ✓ VERIFIED | `apps/api/config/urls.py` includes `allauth.headless.urls` under `/api/v1/auth/`.                                                 |
| 8   | Signup accepts email + password + name and persists name on the user                           | ✓ VERIFIED | `apps/api/apps/accounts/headless.py` `HeadlessSignupForm` saves `name` to user.                                                   |
| 9   | Signup/login responses return user payload and session login does not issue JWTs               | ✗ FAILED   | `apps/api/apps/accounts/headless.py` defines user payload but no response override to suppress JWTs for session logins.           |
| 10  | Logout returns HTTP 204 with no response body                                                  | ✗ FAILED   | `apps/api/apps/accounts/sessions.py` returns 204 for session endpoint only; headless logout not overridden.                       |
| 11  | Email verification is required before first login                                              | ✓ VERIFIED | `apps/api/config/settings/base.py` `ACCOUNT_EMAIL_VERIFICATION = "mandatory"`.                                                    |
| 12  | JWT access tokens expire in 15 minutes with rotating refresh tokens                            | ✓ VERIFIED | `apps/api/config/settings/base.py` `HEADLESS_JWT_ACCESS_TOKEN_EXPIRES_IN = 900`, `HEADLESS_JWT_ROTATE_REFRESH_TOKEN = True`.      |
| 13  | Verification email resend is rate-limited to ~1/min                                            | ✓ VERIFIED | `apps/api/config/settings/base.py` `ACCOUNT_RATE_LIMITS` sets `confirm_email: "1/m"`.                                             |
| 14  | CORS allows local web and mobile origins with credentials                                      | ✓ VERIFIED | `apps/api/config/settings/base.py` `CORS_ALLOWED_ORIGINS` and `CORS_ALLOW_CREDENTIALS = True`.                                    |
| 15  | Authenticated users can GET and PATCH /api/v1/users/me via session cookies or JWT              | ✓ VERIFIED | `apps/api/apps/accounts/controllers.py` uses `SessionAuth()` and `jwt_token_auth`.                                                |
| 16  | Password reset invalidates all existing sessions and JWTs for the user                         | ✗ FAILED   | `apps/api/apps/accounts/signals.py` only invalidates sessions; no JWT revocation.                                                 |
| 17  | Running the export command writes OpenAPI JSON to packages/api-client/openapi.json             | ✓ VERIFIED | `apps/api/apps/core/management/commands/export_openapi_schema.py` writes default path; `packages/api-client/openapi.json` exists. |
| 18  | The exported OpenAPI document reflects the running Ninja Extra API                             | ✓ VERIFIED | `packages/api-client/openapi.json` includes `/api/v1/users/me` and `/api/v1/health`.                                              |

**Score:** 15/18 truths verified

### Required Artifacts

| Artifact                                                          | Expected                                                         | Status      | Details                                                                 |
| ----------------------------------------------------------------- | ---------------------------------------------------------------- | ----------- | ----------------------------------------------------------------------- |
| `apps/api/apps/core/controllers.py`                               | Health controller with database connectivity check               | ✓ VERIFIED  | Implements DB `SELECT 1` and status payload.                            |
| `apps/api/apps/core/schemas.py`                                   | HealthOut and ErrorOut schemas                                   | ✓ VERIFIED  | Schemas defined and referenced by handlers.                             |
| `apps/api/apps/core/exceptions.py`                                | Service error types for API handlers                             | ✓ VERIFIED  | ServiceError hierarchy used in handlers.                                |
| `apps/api/config/urls.py`                                         | NinjaExtraAPI instance with docs guard and auto-discovery        | ✓ VERIFIED  | `docs_guard` + `api.auto_discover_controllers()`.                       |
| `apps/api/config/settings/base.py`                                | AUTH_USER_MODEL and Postgres DATABASE_URL configuration          | ✓ VERIFIED  | `AUTH_USER_MODEL` and `env.db("DATABASE_URL")` present.                 |
| `apps/api/apps/accounts/admin.py`                                 | Custom user model registered in Django admin                     | ✓ VERIFIED  | `admin.site.register(User, UserAdmin)`.                                 |
| `apps/api/apps/accounts/migrations/0001_initial.py`               | Initial migration for the custom user model                      | ✓ VERIFIED  | User model migration exists.                                            |
| `apps/api/apps/accounts/headless.py`                              | Headless signup field mapping, response shaping, logout override | ⚠️ ORPHANED | Signup/name mapping present; response/logout overrides not implemented. |
| `apps/api/config/settings/development.py`                         | Dev-only overrides for cookies and CORS                          | ✓ VERIFIED  | Cookie secure flags disabled in dev.                                    |
| `apps/api/config/settings/production.py`                          | Prod-only security cookie and CORS settings                      | ✓ VERIFIED  | Cookie secure flags enabled, CORS origins required.                     |
| `apps/api/apps/accounts/schemas.py`                               | UserOut and UserUpdateIn schemas                                 | ✓ VERIFIED  | Schemas used by controller.                                             |
| `apps/api/apps/accounts/services.py`                              | User profile retrieval and update logic                          | ✓ VERIFIED  | Service methods and session invalidation.                               |
| `apps/api/apps/accounts/controllers.py`                           | /users/me endpoints with IsAuthenticated                         | ✓ VERIFIED  | Controller wired with auth and routes.                                  |
| `apps/api/apps/accounts/signals.py`                               | Password reset invalidation hooks                                | ⚠️ ORPHANED | Sessions invalidated; JWT invalidation missing.                         |
| `apps/api/apps/core/management/commands/export_openapi_schema.py` | Management command to export OpenAPI JSON                        | ✓ VERIFIED  | Command writes `api.get_openapi_schema()` output.                       |
| `packages/api-client/openapi.json`                                | Committed OpenAPI spec for type generation                       | ✓ VERIFIED  | File present with API paths.                                            |

### Key Link Verification

| From                                                              | To                                        | Via                               | Status     | Details                                                            |
| ----------------------------------------------------------------- | ----------------------------------------- | --------------------------------- | ---------- | ------------------------------------------------------------------ |
| `apps/api/config/urls.py`                                         | `apps/api/apps/core/controllers.py`       | `api.auto_discover_controllers()` | ✓ WIRED    | Auto-discovery enabled.                                            |
| `apps/api/apps/core/controllers.py`                               | `django.db.connection`                    | health check query                | ✓ WIRED    | Uses `connection.cursor()`.                                        |
| `apps/api/config/urls.py`                                         | `apps/api/apps/core/exceptions.py`        | exception handlers                | ✓ WIRED    | `ServiceError` handled with `@api.exception_handler`.              |
| `apps/api/config/settings/base.py`                                | `apps/accounts/models.py`                 | `AUTH_USER_MODEL`                 | ✓ WIRED    | `AUTH_USER_MODEL = "accounts.User"`.                               |
| `apps/api/config/settings/base.py`                                | Postgres database                         | `DATABASE_URL`                    | ✓ WIRED    | `env.db("DATABASE_URL")` configured.                               |
| `apps/api/config/settings/base.py`                                | `allauth.headless`                        | `HEADLESS_*` settings             | ✓ WIRED    | Headless settings present.                                         |
| `apps/api/config/settings/base.py`                                | `apps/api/apps/accounts/headless.py`      | custom headless classes           | ✓ WIRED    | `ACCOUNT_SIGNUP_FORM_CLASS` + `HEADLESS_ADAPTER` set.              |
| `apps/api/config/settings/base.py`                                | `allauth.account`                         | `ACCOUNT_RATE_LIMITS`             | ✓ WIRED    | Rate limit config present.                                         |
| `apps/api/config/urls.py`                                         | `allauth.headless.urls`                   | include                           | ✓ WIRED    | URL include present.                                               |
| `apps/api/apps/accounts/controllers.py`                           | `apps/api/apps/accounts/services.py`      | service delegation                | ✓ WIRED    | `self.service` used.                                               |
| `apps/api/config/urls.py`                                         | `allauth.headless.contrib.ninja.security` | API auth configuration            | ⚠️ PARTIAL | `jwt_token_auth` used in controller, not in `urls.py` per plan.    |
| `apps/api/apps/accounts/signals.py`                               | `django.contrib.sessions.models.Session`  | session invalidation              | ⚠️ PARTIAL | Indirect via `invalidate_user_sessions`; no direct Session access. |
| `apps/api/apps/core/management/commands/export_openapi_schema.py` | `apps/api/config/urls.py`                 | `api.get_openapi_schema()`        | ✓ WIRED    | Command imports `api`.                                             |

### Requirements Coverage

| Requirement | Status      | Blocking Issue                                                                 |
| ----------- | ----------- | ------------------------------------------------------------------------------ |
| API-01      | ✓ SATISFIED | -                                                                              |
| API-02      | ✓ SATISFIED | -                                                                              |
| API-03      | ✓ SATISFIED | -                                                                              |
| API-04      | ✓ SATISFIED | -                                                                              |
| API-05      | ✓ SATISFIED | -                                                                              |
| API-06      | ✓ SATISFIED | -                                                                              |
| API-07      | ✓ SATISFIED | -                                                                              |
| API-08      | ✓ SATISFIED | -                                                                              |
| API-09      | ✓ SATISFIED | -                                                                              |
| AUTH-08     | ⚠️ BLOCKED  | Session login response and logout behavior not enforced in headless responses. |
| AUTH-09     | ⚠️ BLOCKED  | Password reset does not revoke JWTs.                                           |

### Anti-Patterns Found

None found in scanned Phase 2 artifacts.

### Human Verification Required

1. **Docs Access Control**

**Test:** Access `/api/docs` unauthenticated in dev and production modes.
**Expected:** 403/redirect in dev for anonymous, 404 or staff-only in production.
**Why human:** Requires runtime auth/session behavior.

2. **Session vs JWT Auth Behavior**

**Test:** Login with session cookie and JWT, then call `/api/v1/users/me`.
**Expected:** Both auth methods succeed for the same endpoint.
**Why human:** Requires runtime auth configuration and token issuance behavior.

3. **Logout Response**

**Test:** Call headless logout endpoint and session endpoint.
**Expected:** 204 with empty body for logout.
**Why human:** Response behavior depends on allauth headless runtime.

4. **Password Reset Invalidation**

**Test:** Obtain session + JWT, reset password, then call `/api/v1/users/me`.
**Expected:** Both prior session and JWT are rejected (401).
**Why human:** Requires token/session issuance and runtime invalidation.

### Gaps Summary

Auth response behavior and password reset invalidation are incomplete. The current headless customization provides user payloads but does not explicitly suppress JWTs for session logins or enforce 204 responses for logout across headless endpoints. Password reset only clears Django sessions; stateful JWT records are not revoked, leaving JWTs valid after reset.

---

_Verified: 2026-02-15T00:00:00Z_
_Verifier: Claude (gsd-verifier)_
