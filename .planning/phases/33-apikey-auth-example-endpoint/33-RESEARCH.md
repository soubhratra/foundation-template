# Phase 33: ApiKeyAuth Example Endpoint - Research

**Researched:** 2026-03-13
**Domain:** Django Ninja Extra — route-level auth override, permission composition, integration testing
**Confidence:** HIGH

## Summary

Phase 33 closes AKEY-01, AKEY-02, and AKEY-03 by activating the complete API key auth chain in a real, production endpoint. All infrastructure already exists from Phase 28: `ApiKeyAuth`, `RequireScope`, `ApiKeyRateLimitMiddleware`, and usage tracking in `authenticate()` are fully implemented and unit-tested. This phase adds exactly one route (`GET /api/v1/me/api-keys/ping/`) to the existing `APIKeyController`, adds the `PingOut` schema, and writes integration tests that exercise the full chain end-to-end via the Django test client.

The endpoint is intentionally minimal (`{"status": "ok"}`) because its purpose is developer ergonomics — confirming a key is valid — and because middleware automatically injects `X-RateLimit-*` headers, making the response self-documenting about key state.

The integration tests for this phase are the primary deliverable. Unit-level coverage for `ApiKeyAuth`, `RequireScope`, and `ApiKeyRateLimitMiddleware` already exists in `tests/api_keys/test_auth.py` and `tests/api_keys/test_ratelimit.py`. What was missing was an end-to-end HTTP test going through the Django test client to a real endpoint — this phase supplies that.

**Primary recommendation:** Add `PingOut` schema, one route method in `APIKeyController`, and one new integration test file `tests/api_keys/test_ping.py`. No new files, middleware, models, or settings needed.

---

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions

- **Scope:** Use `RequireScope("read")` — matches coarse scopes in `API_KEY_SCOPES` (`read`, `write`, `admin`). No settings change.
- **Namespaced scopes:** Do NOT adopt `api:read` style — the template standard is the coarse scope catalog.
- **403 demonstration:** Wrong-scope enforcement is shown in integration tests only — no separate endpoint path or code comment needed.
- **Endpoint URL:** `GET /api/v1/me/api-keys/ping/` — added to existing `APIKeyController` in `apps/api_keys/controllers.py`.
- **Auth placement:** Use `auth=[ApiKeyAuth()]` on the route decorator (not on the controller) so management endpoints keep session auth.
- **Scaffolder markers:** Entire api_keys module (including this endpoint) sits inside `B2B_START`/`B2B_END` markers — no additional marking needed.
- **Response payload:** Returns `{"status": "ok"}` only. Schema: `PingOut` with single `status: str` field.
- **X-RateLimit-\* headers:** Middleware-injected automatically — NOT documented in OpenAPI schema; left as undocumented transport behavior.
- **Endpoint permanence:** Stays in every product built from the template.

### Claude's Discretion

- Exact `@route.get` decorator options (URL name, tags, operation_id)
- Whether to add a docstring explaining it's a key health check
- Order of `permissions=[IsAuthenticated, RequireScope("read")]` vs declaring `auth=[ApiKeyAuth()]` directly on the route

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>

## Phase Requirements

| ID      | Description                                                                             | Research Support                                                                                                                                        |
| ------- | --------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| AKEY-01 | User can create/revoke API keys with scopes; `RequireScope` enforces scope per endpoint | Ping endpoint activates `RequireScope("read")` in a real HTTP request; wrong-scope test asserts 403                                                     |
| AKEY-02 | API key requests rate-limited per key; `X-RateLimit-*` response headers returned        | `ApiKeyRateLimitMiddleware` already in `MIDDLEWARE`; integration test with `@override_settings(RATELIMIT_ENABLE=True)` asserts headers on ping response |
| AKEY-03 | `last_used_at` and `usage_count` updated on every authenticated request                 | `ApiKeyAuth.authenticate()` already performs partial UPDATE; integration test asserts both fields change after ping call                                |

</phase_requirements>

---

## Standard Stack

### Core (all already installed — no new dependencies)

| Library              | Version   | Purpose                                           | Status |
| -------------------- | --------- | ------------------------------------------------- | ------ |
| `django-ninja-extra` | installed | `@api_controller`, `@route.get`, `ControllerBase` | In use |
| `ninja`              | installed | `HttpBearer`, `Schema`                            | In use |
| `django-ratelimit`   | installed | Per-key rate limit enforcement                    | In use |

**Installation:** Nothing new. All required packages were installed in Phase 28.

---

## Architecture Patterns

### No New Files Required

The entire phase is changes to existing files plus one new test file:

```
apps/api/
├── apps/api_keys/
│   ├── schemas.py        # ADD PingOut schema (3 lines)
│   └── controllers.py    # ADD @route.get("/ping/") method
└── tests/api_keys/
    └── test_ping.py      # NEW — integration tests for the full chain
```

### Pattern 1: Route-Level Auth Override on a Controller

The `APIKeyController` uses controller-level `permissions=[IsAuthenticated]` (session auth). To add a route that accepts API key Bearer tokens instead of session cookies, the auth backend is overridden at the route level:

```python
# Source: apps/api_keys/controllers.py (existing pattern in Phase 28 decisions)
@route.get(
    "/ping/",
    auth=[ApiKeyAuth()],
    permissions=[IsAuthenticated, RequireScope("read")],
    response={200: PingOut},
    url_name="api_key_ping",
)
def ping(self, request: HttpRequest) -> Any:
    """Verify the API key is valid and has read scope. Returns {"status": "ok"}.

    X-RateLimit-* headers are injected by ApiKeyRateLimitMiddleware automatically.
    """
    return 200, {"status": "ok"}
```

**Why `auth=[ApiKeyAuth()]` on the route, not the controller:** The three management endpoints (POST, GET, DELETE) use session auth because they are called from the web UI with a session cookie. The ping endpoint is for API consumers who send `Authorization: Bearer <token>`. Django Ninja Extra resolves auth per-route when `auth=` is specified on the decorator; the controller-level `permissions=[IsAuthenticated]` is still evaluated after auth resolves.

**Why `IsAuthenticated` appears before `RequireScope`:** Ninja Extra evaluates the `permissions` list in order. `IsAuthenticated` confirms a user object was resolved (by `ApiKeyAuth`). `RequireScope` then checks `request.api_key.scopes`. If `IsAuthenticated` were absent and the key was invalid, `RequireScope` would raise `PermissionDenied` on an unauthenticated request rather than the correct 401.

### Pattern 2: PingOut Schema

```python
# Source: apps/api_keys/schemas.py (add at end of file)
class PingOut(Schema):
    """Response for GET /me/api-keys/ping/ — confirms the key is valid."""
    status: str = "ok"
```

This follows the existing schema pattern in the file (`APIKeyIn`, `APIKeyCreateOut`, `APIKeyOut` all use `class Foo(Schema):`).

### Pattern 3: Integration Test Using Django Test Client

All existing api_keys controller tests use `django.test.Client` (not `RequestFactory`) for HTTP-level tests. Integration tests for the ping endpoint follow the same approach:

```python
# Source: pattern from tests/api_keys/test_controllers.py
def test_ping_with_valid_key_returns_200(self, client, api_key):
    response = client.get(
        "/api/v1/me/api-keys/ping/",
        HTTP_AUTHORIZATION=f"Bearer {api_key._raw_key}",
    )
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

**Key point:** `api_key._raw_key` is attached by the `api_key` fixture in `conftest.py` — it is available without fixture changes.

### Pattern 4: Rate Limit Tests Require @override_settings

The global `test_isolation_settings` autouse fixture sets `RATELIMIT_ENABLE=False`. Any test asserting rate limit behavior must override this:

```python
# Source: tests/api_keys/test_ratelimit.py (established pattern)
@override_settings(RATELIMIT_ENABLE=True)
def test_rate_limit_returns_429(self, client, api_key, settings):
    settings.API_KEY_RATE_LIMIT = "1/m"  # pragma: allowlist secret
    # ... test body
```

Both `@override_settings(RATELIMIT_ENABLE=True)` and `settings.API_KEY_RATE_LIMIT` set to `"1/m"` are needed: the decorator re-enables rate limiting globally, and the `settings` fixture (pytest-django) overrides the limit to something triggerable in a test.

### Anti-Patterns to Avoid

- **Do not add `auth=[ApiKeyAuth()]` to the controller-level decorator** — this would break the management endpoints (POST, GET, DELETE) which require session auth.
- **Do not test rate limit behavior without `@override_settings(RATELIMIT_ENABLE=True)`** — the autouse fixture silences it and the test will pass vacuously.
- **Do not assert `X-RateLimit-*` headers without `RATELIMIT_ENABLE=True`** — middleware calls `get_usage()` which returns `None` when disabled; `_inject_headers()` is never called.
- **Do not use `client.force_login()` for ping tests** — the ping endpoint requires Bearer token auth, not session auth. A session-only request should return 403 (tested explicitly).
- **Do not import `PingOut` in the controller before adding it to `schemas.py`** — the import will fail at Django startup.

---

## Don't Hand-Roll

| Problem                        | Don't Build                                     | Use Instead                                         | Why                                                                                      |
| ------------------------------ | ----------------------------------------------- | --------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| Usage tracking on authenticate | Custom update logic in the route handler        | `ApiKeyAuth.authenticate()` already does it         | Already implemented; adding it to the route handler would double-increment               |
| Rate limit enforcement         | Custom counter in middleware or view            | `ApiKeyRateLimitMiddleware` already in `MIDDLEWARE` | Already fires on all requests with `request.api_key` set                                 |
| Rate limit response headers    | Manual `response["X-RateLimit-*"]` in the view  | `_inject_headers()` in `ApiKeyRateLimitMiddleware`  | Already called by middleware; manual injection in the view would cause duplicate headers |
| Scope enforcement              | Custom `if scope in api_key.scopes` in the view | `RequireScope("read")` in permissions list          | Already handles session-request rejection, missing scope, and raises `PermissionDenied`  |

**Key insight:** The ping endpoint itself has zero business logic. It exists solely to route a request through the already-built infrastructure chain. Every line of logic it would otherwise contain is already handled by `ApiKeyAuth`, `RequireScope`, and `ApiKeyRateLimitMiddleware`.

---

## Common Pitfalls

### Pitfall 1: Wrong-Scope Test Asserts 429 Instead of 403

**What goes wrong:** Success criterion 2 reads "A request with a valid key but wrong scope returns HTTP 429." This is a slightly misleading phrasing — the correct behavior is HTTP 403 (PermissionDenied from `RequireScope`), not 429 (rate limit). The middleware enforces rate limits only after auth succeeds; if `RequireScope` raises `PermissionDenied`, Ninja converts it to 403 and middleware never executes.

**Confirmed behavior:** `RequireScope.has_permission()` raises `PermissionDenied` (not returns False) when the scope is missing — this is documented in `apps/api_keys/auth.py` line 77 and confirmed by `test_require_scope_rejects_wrong_scope` in `test_auth.py`.

**How to avoid:** Assert `status_code == 403` in the wrong-scope integration test. The success criterion description appears to conflate 403 (wrong scope) with 429 (rate limit). Verify by reading the auth.py source — `raise PermissionDenied` maps to 403 in Django Ninja.

**Note:** The CONTEXT.md decision says "403 enforcement for wrong scope is demonstrated in integration tests only." This confirms 403 is the correct assertion.

### Pitfall 2: Cache State Leaks Between Rate Limit Tests

**What goes wrong:** Rate limit tests using `settings.API_KEY_RATE_LIMIT` set to `"1/m"` can leak counter state between test methods if the cache is not cleared. The second test method that runs sees a non-zero counter from the first.

**How to avoid:** Call `cache.clear()` at the start of any test that manipulates rate limit state. Pattern established in `test_ratelimit.py::test_rate_limit_returns_429_with_headers`.

**Warning signs:** Rate limit tests fail intermittently depending on test execution order.

### Pitfall 3: N+1 Query on Usage Tracking

**What goes wrong:** `ApiKeyAuth.authenticate()` calls `api_key.refresh_from_db(fields=["last_used_at", "usage_count"])` after the partial UPDATE. Integration tests run with the `_nplusone_guard` autouse fixture. If the guard is overly strict, the `refresh_from_db` call (which is a deliberate N+1 by design) may trigger `NPlusOneError`.

**How to avoid:** Check if `refresh_from_db` in `authenticate()` is inside the auth resolution phase (before the view runs). The nplusone guard wraps the test body, not the auth backend, so this should be safe. If a guard error appears, use `@allow_lazy_load` with a comment.

**Warning signs:** `NPlusOneError` on `api_keys_key` table in ping integration tests.

### Pitfall 4: Missing `url_name` Causes Django Reverse Failure

**What goes wrong:** Not specifying `url_name="api_key_ping"` on the route causes `reverse("api_key_ping")` to fail if any other code or test tries to resolve it. This is a latent issue, not an immediate test failure.

**How to avoid:** Always specify `url_name` on routes in `APIKeyController` — existing routes all have it (`api_key_create`, `api_key_list`, `api_key_revoke`).

---

## Code Examples

Verified patterns from existing codebase:

### Full Ping Route Method

```python
# Source: apps/api_keys/controllers.py — new method added to APIKeyController
@route.get(
    "/ping/",
    auth=[ApiKeyAuth()],
    permissions=[IsAuthenticated, RequireScope("read")],
    response={200: PingOut},
    url_name="api_key_ping",
    tags=["api-keys"],
)
def ping(self, request: HttpRequest) -> Any:
    """Verify the API key is valid and has read scope.

    Returns {"status": "ok"} when the full chain passes:
    ApiKeyAuth (token lookup + usage tracking) → RequireScope (scope check) →
    ApiKeyRateLimitMiddleware (rate limit + X-RateLimit-* headers).
    """
    return 200, {"status": "ok"}
```

### PingOut Schema

```python
# Source: apps/api_keys/schemas.py — append after APIKeyOut
class PingOut(Schema):
    """Response for GET /me/api-keys/ping/."""
    status: str = "ok"
```

### Integration Test File Structure

```python
# Source: pattern from tests/api_keys/test_controllers.py and test_ratelimit.py
"""Integration tests for GET /api/v1/me/api-keys/ping/.

Exercises the full auth chain end-to-end:
ApiKeyAuth -> RequireScope -> ApiKeyRateLimitMiddleware -> usage tracking.

Requirements: AKEY-01, AKEY-02, AKEY-03.
"""

import pytest
from django.core.cache import cache
from django.test import Client, override_settings


@pytest.mark.django_db
class TestApiKeyPingEndpoint:
    URL = "/api/v1/me/api-keys/ping/"

    def test_valid_key_with_read_scope_returns_200(self, client, api_key):
        # AKEY-01: valid key with correct scope succeeds
        response = client.get(
            self.URL,
            HTTP_AUTHORIZATION=f"Bearer {api_key._raw_key}",
        )
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_valid_key_updates_usage_tracking(self, client, api_key):
        # AKEY-03: last_used_at and usage_count updated
        assert api_key.usage_count == 0
        client.get(self.URL, HTTP_AUTHORIZATION=f"Bearer {api_key._raw_key}")
        api_key.refresh_from_db()
        assert api_key.last_used_at is not None
        assert api_key.usage_count == 1

    def test_wrong_scope_returns_403(self, client, db):
        # AKEY-01: wrong scope enforcement (key has no "admin" scope)
        from apps.api_keys.models import APIKey
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.create_user(email="scopetest@example.com", password="x")
        raw_key, prefix, key_hash = APIKey.generate_key()
        key = APIKey.objects.create(
            user=user, prefix=prefix, key_hash=key_hash,
            scopes=["write"],  # no "read" scope
            is_active=True,
        )
        key._raw_key = raw_key
        response = client.get(self.URL, HTTP_AUTHORIZATION=f"Bearer {key._raw_key}")
        assert response.status_code == 403

    @override_settings(RATELIMIT_ENABLE=True)
    def test_rate_limit_headers_on_success(self, client, api_key):
        # AKEY-02: X-RateLimit-* headers present on successful response
        response = client.get(
            self.URL,
            HTTP_AUTHORIZATION=f"Bearer {api_key._raw_key}",
        )
        assert response.status_code == 200
        assert "X-RateLimit-Limit" in response
        assert "X-RateLimit-Remaining" in response
        assert "X-RateLimit-Reset" in response

    @override_settings(RATELIMIT_ENABLE=True)
    def test_rate_limit_exceeded_returns_429(self, client, api_key, settings):
        # AKEY-02: per-key rate limit enforcement
        settings.API_KEY_RATE_LIMIT = "1/m"  # pragma: allowlist secret
        cache.clear()
        client.get(self.URL, HTTP_AUTHORIZATION=f"Bearer {api_key._raw_key}")
        response = client.get(
            self.URL,
            HTTP_AUTHORIZATION=f"Bearer {api_key._raw_key}",
        )
        assert response.status_code == 429
        assert "X-RateLimit-Remaining" in response
        assert response["X-RateLimit-Remaining"] == "0"

    def test_session_auth_rejected(self, client, api_user):
        # AKEY-01 (success criterion 4): session-only request must fail
        client.force_login(api_user)
        response = client.get(self.URL)
        assert response.status_code in (401, 403)

    def test_invalid_key_returns_401(self, client):
        # Auth failure: invalid token
        response = client.get(
            self.URL,
            HTTP_AUTHORIZATION="Bearer ft_notarealkey",
        )
        assert response.status_code == 401

    def test_no_auth_returns_401(self, client):
        # Auth failure: no Authorization header
        response = client.get(self.URL)
        assert response.status_code in (401, 403)
```

---

## State of the Art

| Area                        | Existing State (Phase 28)                     | After Phase 33                                 |
| --------------------------- | --------------------------------------------- | ---------------------------------------------- |
| `ApiKeyAuth`                | Implemented, unit-tested                      | Activated on a real production route           |
| `RequireScope`              | Implemented, unit-tested                      | Activated on a real production route           |
| `ApiKeyRateLimitMiddleware` | Implemented, unit-tested, wired in MIDDLEWARE | Demonstrated on a real endpoint with HTTP test |
| Usage tracking              | Implemented in `authenticate()`, unit-tested  | Integration-tested via HTTP request            |
| AKEY-01/02/03               | Infrastructure built, no activating endpoint  | Closed — all three requirements met            |

**Nothing deprecated or removed in this phase.**

---

## Open Questions

1. **Does `RequireScope` raise 403 or return 403 when scope is missing?**
   - What we know: `RequireScope.has_permission()` raises `PermissionDenied` (line 77 of `auth.py`)
   - What's clear: Django Ninja maps `PermissionDenied` to HTTP 403 — confirmed by existing `test_require_scope_rejects_wrong_scope` test which asserts `pytest.raises(PermissionDenied)`
   - Recommendation: Assert `status_code == 403` in wrong-scope integration test (not 429 as the success criteria ambiguously states)

2. **Does `auth=[ApiKeyAuth()]` on the route override the controller-level `permissions=[IsAuthenticated]`?**
   - What we know: From CONTEXT.md and Phase 28 decisions: "Management controller (APIKeyController) uses session auth only; ApiKeyAuth is for product endpoints only" — the pattern is explicitly documented
   - What's clear: Django Ninja Extra evaluates route-level `auth=` first, then evaluates `permissions=`. The permissions list `[IsAuthenticated, RequireScope("read")]` is applied after the route-level `auth=[ApiKeyAuth()]` resolves the token.
   - Recommendation: Use `permissions=[IsAuthenticated, RequireScope("read")]` with `IsAuthenticated` first — matches the established RBAC pattern (Phase 25).

---

## Validation Architecture

### Test Framework

| Property           | Value                                                               |
| ------------------ | ------------------------------------------------------------------- |
| Framework          | pytest + pytest-django                                              |
| Config file        | `apps/api/pyproject.toml` (`[tool.pytest.ini_options]`)             |
| Quick run command  | `cd apps/api && python -m pytest tests/api_keys/test_ping.py -x -q` |
| Full suite command | `cd apps/api && python -m pytest tests/api_keys/ -x -q`             |

### Phase Requirements to Test Map

| Req ID  | Behavior                               | Test Type   | Automated Command                                                                                           | File Exists? |
| ------- | -------------------------------------- | ----------- | ----------------------------------------------------------------------------------------------------------- | ------------ |
| AKEY-01 | Valid key + read scope returns 200     | integration | `pytest tests/api_keys/test_ping.py::TestApiKeyPingEndpoint::test_valid_key_with_read_scope_returns_200 -x` | Wave 0       |
| AKEY-01 | Wrong scope returns 403                | integration | `pytest tests/api_keys/test_ping.py::TestApiKeyPingEndpoint::test_wrong_scope_returns_403 -x`               | Wave 0       |
| AKEY-01 | Session-only request rejected          | integration | `pytest tests/api_keys/test_ping.py::TestApiKeyPingEndpoint::test_session_auth_rejected -x`                 | Wave 0       |
| AKEY-02 | X-RateLimit-\* headers on success      | integration | `pytest tests/api_keys/test_ping.py::TestApiKeyPingEndpoint::test_rate_limit_headers_on_success -x`         | Wave 0       |
| AKEY-02 | 429 when rate limit exceeded           | integration | `pytest tests/api_keys/test_ping.py::TestApiKeyPingEndpoint::test_rate_limit_exceeded_returns_429 -x`       | Wave 0       |
| AKEY-03 | `last_used_at` + `usage_count` updated | integration | `pytest tests/api_keys/test_ping.py::TestApiKeyPingEndpoint::test_valid_key_updates_usage_tracking -x`      | Wave 0       |

### Sampling Rate

- **Per task commit:** `cd apps/api && python -m pytest tests/api_keys/test_ping.py -x -q`
- **Per wave merge:** `cd apps/api && python -m pytest tests/api_keys/ -x -q`
- **Phase gate:** Full api_keys suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `apps/api/tests/api_keys/test_ping.py` — covers all 6 test cases above (AKEY-01, AKEY-02, AKEY-03)

_(All other test infrastructure — conftest.py, fixtures, pytest config — exists and is reusable without modification.)_

---

## Sources

### Primary (HIGH confidence)

- Direct code read: `apps/api/apps/api_keys/auth.py` — `ApiKeyAuth.authenticate()` and `RequireScope.has_permission()` implementations
- Direct code read: `apps/api/apps/api_keys/controllers.py` — `APIKeyController` structure and existing route patterns
- Direct code read: `apps/api/apps/api_keys/middleware.py` — `ApiKeyRateLimitMiddleware` implementation
- Direct code read: `apps/api/apps/api_keys/schemas.py` — existing schema patterns
- Direct code read: `apps/api/apps/api_keys/models.py` — `APIKey` model fields and `generate_key()`
- Direct code read: `apps/api/tests/api_keys/conftest.py` — `api_key` and `api_user` fixtures
- Direct code read: `apps/api/tests/api_keys/test_controllers.py` — integration test patterns
- Direct code read: `apps/api/tests/api_keys/test_ratelimit.py` — `@override_settings(RATELIMIT_ENABLE=True)` pattern
- Direct code read: `apps/api/tests/conftest.py` — `test_isolation_settings` autouse fixture
- Direct code read: `apps/api/config/settings/base.py` — `API_KEY_SCOPES`, `API_KEY_RATE_LIMIT`, middleware ordering

### Secondary (MEDIUM confidence)

- `.planning/phases/33-apikey-auth-example-endpoint/33-CONTEXT.md` — locked decisions from discussion session
- `.planning/STATE.md` — Phase 28 decisions log confirming patterns

### Tertiary (LOW confidence)

None — all findings are grounded in existing codebase code reads.

---

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — all libraries installed and in use; no new dependencies
- Architecture: HIGH — patterns read directly from existing codebase; route-level auth override documented in Phase 28 decisions
- Pitfalls: HIGH — sourced from existing test files and STATE.md decision log
- Integration test design: HIGH — copied from established patterns in test_controllers.py and test_ratelimit.py

**Research date:** 2026-03-13
**Valid until:** 2026-06-13 (stable — Django Ninja Extra API is stable; no moving targets)
