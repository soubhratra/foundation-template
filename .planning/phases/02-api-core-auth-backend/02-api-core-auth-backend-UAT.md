---
status: testing
phase: 02-api-core-auth-backend
source:
  - 02-01-SUMMARY.md
  - 02-02-SUMMARY.md
  - 02-03-SUMMARY.md
  - 02-04-SUMMARY.md
  - 02-05-SUMMARY.md
started: 2026-02-16T01:50:29Z
updated: 2026-02-16T02:10:57Z
---

## Current Test

number: 4
name: JWT login flow
expected: |
  Using valid credentials, POST to /api/v1/auth/jwt/login/. Expect HTTP 200 JSON
  containing `access_token` and `refresh_token`, and using the access token in the
  Authorization header should allow authenticated requests.
awaiting: user response

## Tests

### 1. Health endpoint report
expected: Run dev server and GET /api/v1/health. Expect HTTP 200 JSON with `status` and `database` fields showing live DB connectivity.
result: pass

### 2. Docs access control
expected: Visiting http://localhost:8000/api/docs while unauthenticated should redirect or return 403; after logging in as a staff/admin user, the docs UI should load normally.
result: pass

### 3. Session login response payload
expected: POST to /api/v1/auth/session/login with valid credentials returns 200, sets session cookie, and response JSON contains user payload but NO `access_token` or `refresh_token` fields.
result: skipped
reason: Unable to reach session login endpoint manually (CSRF/csrf helper routing); revisit later if needed.

### 4. JWT login flow
expected: POST to /api/v1/auth/jwt/login with valid credentials returns 200 JSON containing `access_token` and `refresh_token`; using the access token in Authorization header allows authenticated requests.
result: pending

### 5. /users/me via session and JWT
expected: With session cookie, GET /api/v1/users/me returns 200 user payload; repeating request with Authorization: Bearer <access_token> (no session cookie) also returns 200 user payload.
result: pending

### 6. Password reset invalidates sessions + JWTs
expected: After requesting password reset and completing it, prior session cookies and JWT access tokens should both be invalid: subsequent /api/v1/users/me calls using old session/JWT should return 401 until logging in again.
result: pending

### 7. Headless logout response
expected: POST /api/v1/auth/logout/ (session logout) returns HTTP 204 with empty body; any response body should be absent.
result: pending

### 8. OpenAPI export artifact
expected: Running `uv run python manage.py export_openapi_schema` (without arguments) writes/updates packages/api-client/openapi.json with a valid OpenAPI 3.1 document.
result: pending

## Summary

total: 8
passed: 2
issues: 0
pending: 5
skipped: 1

## Gaps

[none]
