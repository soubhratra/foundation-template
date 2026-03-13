# Phase 33: ApiKeyAuth Example Endpoint - Context

**Gathered:** 2026-03-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Add one production endpoint (`GET /api/v1/me/api-keys/ping/`) that exercises the full API key auth chain: `ApiKeyAuth` → `RequireScope` → `ApiKeyRateLimitMiddleware` → usage tracking. All infrastructure from Phase 28 is complete. This phase closes AKEY-01/02/03 by activating the chain in a real endpoint.

Not in scope: new auth infrastructure, scope system redesign, additional management endpoints.

</domain>

<decisions>
## Implementation Decisions

### Scope naming

- Use **`RequireScope("read")`** — matches the coarse scopes shipped in Phase 28 (`read`, `write`, `admin` in `API_KEY_SCOPES`). No settings change needed.
- Do **not** adopt namespaced scope style (`api:read`) — the roadmap plan description was aspirational; the template standard is the coarse scope catalog.
- 403 enforcement for wrong scope is demonstrated in integration tests only — no separate endpoint path or code comment needed.

### Endpoint location

- Lives at **`GET /api/v1/me/api-keys/ping/`** — added to the existing `APIKeyController` in `apps/api_keys/controllers.py`.
- Uses `auth=[ApiKeyAuth()]` on the route (not on the controller) so the management endpoints (`POST /`, `GET /`, `DELETE /{id}/`) keep session auth.
- Wrapped in **`B2B_START`/`B2B_END`** scaffolder markers alongside the rest of the api_keys module — removed cleanly with `--without b2b`.

### Response payload

- Returns **`{"status": "ok"}`** only — minimal body, confirms full chain ran without exposing key internals.
- Response schema: `PingOut` with single `status: str` field.
- `X-RateLimit-*` headers are middleware-injected automatically — **not documented in OpenAPI schema** on this endpoint; left as undocumented transport behavior.

### Endpoint permanence

- **Stays in every product built from the template** — a `/ping` endpoint is a standard developer experience affordance. API consumers can verify their key works without knowing a product-specific endpoint.
- Because it lives inside the api_keys module with B2B markers, it's removed automatically when `--without b2b` strips the module.

### Claude's Discretion

- Exact `@route.get` decorator options (URL name, tags, operation_id)
- Whether to add a docstring to the ping endpoint explaining it's a key health check
- Order of `permissions=[IsAuthenticated, RequireScope("read")]` vs declaring `auth=[ApiKeyAuth()]` on the route directly

</decisions>

<code_context>

## Existing Code Insights

### Reusable Assets

- `apps/api_keys/controllers.py` (`APIKeyController`): Ping endpoint is added here as a new `@route.get` — same controller, new route. No new file needed.
- `apps/api_keys/auth.py` (`ApiKeyAuth`, `RequireScope`): Ready to use. `auth=[ApiKeyAuth()]` on the route; `permissions=[IsAuthenticated, RequireScope("read")]` for scope enforcement.
- `apps/api_keys/schemas.py`: Add `PingOut(Schema)` with `status: str = "ok"` — minimal schema, follows existing schema patterns.
- `apps/api_keys/middleware.py` (`ApiKeyRateLimitMiddleware`): Already wired in Django middleware stack from Phase 28 — fires automatically on all requests with `request.api_key` set. No changes needed.
- `apps/api/tests/api_keys/conftest.py` (`api_user`, `api_key` fixtures): Base fixtures to extend for Phase 33 tests.

### Established Patterns

- Route-level auth override: `@route.get("/ping/", auth=[ApiKeyAuth()], ...)` — overrides controller-level session auth for this route only. This is the Django Ninja Extra pattern for mixed auth on a single controller.
- Permission composition: `permissions=[IsAuthenticated, RequireScope("read")]` — same pattern as `RequireRole` usage in RBAC (Phase 25); `IsAuthenticated` must appear first.
- Usage tracking (`last_used_at`, `usage_count`): Updated inside `ApiKeyAuth.authenticate()` via partial `UPDATE` — fires automatically when `auth=[ApiKeyAuth()]` resolves the token. No ping endpoint code needed.

### Integration Points

- `APIKeyController` at `/api/v1/me/api-keys/` — ping route added to existing controller
- `ApiKeyRateLimitMiddleware` — already in `MIDDLEWARE` from Phase 28; no registration needed
- `API_KEY_SCOPES` in `settings/base.py` — no changes; `"read"` scope already defined

</code_context>

<specifics>
## Specific Ideas

- The ping endpoint's primary purpose is developer ergonomics: "Is my API key valid?" — the `{"status": "ok"}` response is intentionally minimal so it doubles as a curl health check.
- `X-RateLimit-*` headers appear in the response automatically via middleware — this is actually the most useful thing the ping endpoint demonstrates; API consumers can see their rate limit state without doing anything destructive.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

_Phase: 33-apikey-auth-example-endpoint_
_Context gathered: 2026-03-13_
