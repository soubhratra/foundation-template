# Phase 02: API Core + Auth Backend - Context

**Gathered:** 2026-02-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Django Ninja Extra API with auth endpoints, OpenAPI spec, and dual auth strategy (session cookies for web, JWT for mobile). This phase focuses on API surface and auth behavior; frontend flows are handled in later phases.

</domain>

<decisions>
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

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-api-core-auth-backend*
*Context gathered: 2026-02-15*
