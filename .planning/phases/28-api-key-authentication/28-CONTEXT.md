# Phase 28: API Key Authentication - Context

**Gathered:** 2026-03-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Users can create scoped API keys for programmatic access to the API. Keys are rate-limited per-key and usage is tracked so products can build tiered API plans on top.

Scope: APIKey model + migration, key generation (prefix + SHA-256 hash storage, raw key shown once), key create/revoke/list endpoints under `/api/v1/me/api-keys/`, `API_KEY_SCOPES` settings-based scope catalog, `RequireScope` Ninja Extra permission class, Ninja auth backend for Bearer token key resolution, per-key rate limiting via `django-ratelimit` with `X-RateLimit-*` response headers, `last_used_at` + `usage_count` tracking on every authenticated request.

Not in scope: Org-level API keys (all keys are user-owned in v1.4), live/test key distinction, per-key rate limit overrides, billing-integrated rate tiers.

</domain>

<decisions>
## Implementation Decisions

### Key ownership model

- API keys are **user-owned only** — not org-owned; org context is derived from user membership downstream if products need it
- Key management endpoints live at **`/api/v1/me/api-keys/`** — consistent with user-owned resource convention under `/me/`
- When an API key authenticates a request, the auth backend resolves it to the owner `User` and sets **`request.user = user`** — same Django User object as session auth; all existing `IsAuthenticated` and user-based logic works transparently; `RequireScope` adds on top of this
- APIKey model lives in a **new `apps/api_keys/` app** — mirrors the orgs/ and webhooks/ pattern; clean B2B_START/B2B_END marker boundary for the scaffolder; Phase 29 audit logging references `APIKey` by model name

### Scope catalog design

- Available scopes defined in **`API_KEY_SCOPES` settings-based dict** — same pattern as `BILLING_PLANS` and `WEBHOOK_EVENTS`; validated at startup via `manage.py check`; product developers extend the dict without touching template code
- Template ships **3 coarse example scopes** (`read`, `write`, `admin`):
  ```python
  API_KEY_SCOPES = {
      "read": {"description": "Read-only access to all resources"},
      "write": {"description": "Create and update resources"},
      "admin": {"description": "Full access including destructive operations"},
  }
  ```
- **`RequireScope` rejects session-authenticated requests entirely** — a request carrying a valid session cookie but no API key Bearer token is rejected with HTTP 403 if the endpoint uses `RequireScope`; there is no auth fallback; this matches success criteria AKEY-01 exactly

### Rate limit configuration

- Rate limit value is a **global settings value**: `API_KEY_RATE_LIMIT = "1000/h"` — applies to all keys equally; products override per their tier by modifying the setting; default 1000/hour matches common API tier defaults <!-- pragma: allowlist secret -->
- X-RateLimit-\* headers computed from **the same Redis counter that `django-ratelimit` uses** — a middleware reads the cache key populated by django-ratelimit post-auth to derive `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`; one source of truth, no counter drift
- Rate limit key is the API key's stored prefix (`ft_a1b2c3d4`) — unique per key, not per user

### Key format and prefix

- **`API_KEY_PREFIX = "ft_"`** in Django settings — products override to match their brand (e.g. `"gh_"`, `"sk_"`); single prefix type, no live/test distinction <!-- pragma: allowlist secret -->
- Random part: **`secrets.token_hex(32)`** — 64 lowercase hex characters, 256 bits of entropy; same approach as Phase 27 webhook secrets; effectively unguessable
- Full key shown once: `ft_<64 hex chars>` (e.g. `ft_a1b2c3d4e5f6...`)
- Stored in DB: `prefix = API_KEY_PREFIX + first 8 chars of random` (e.g. `ft_a1b2c3d4`); `key_hash = sha256(full_key)`; raw key never persisted
- 8-char stored prefix is long enough to distinguish keys in a list, short enough to be non-guessable — standard approach (GitHub, Stripe use 8–12 chars)

### Claude's Discretion

- Exact DB index strategy on `APIKey` (prefix + user compound index likely needed for key lookup)
- Middleware ordering for usage tracking (`last_used_at` / `usage_count` updates) — sync in auth backend or async via `transaction.on_commit()`
- Exact `manage.py check` validator implementation for `API_KEY_SCOPES`
- Pagination style for key list endpoint (follow existing pagination patterns)
- Whether key name/label field is required or optional at creation

</decisions>

<specifics>
## Specific Ideas

- `RequireScope` composition pattern: `permissions=[IsAuthenticated, RequireScope("read")]` — stacks on top of existing permission chain, same as `RequireRole` and `IsOrgAdmin`. The auth backend populates `request.user`; `RequireScope` checks that the request also carried an API key with the required scope (session-only requests fail).
- Stored prefix (`ft_a1b2c3d4`) doubles as the human-visible key identifier in list views — users see "ft_a1b2..." and recognize which key is which. Consistent with GitHub's PAT display and Stripe's publishable key display.
- The "shown once" philosophy is consistent across Phase 27 (webhook secret) and Phase 28 (API key raw value) — users are expected to copy and store immediately; template UI should reflect this with a copy-to-clipboard affordance and a warning banner.

</specifics>

<code_context>

## Existing Code Insights

### Reusable Assets

- `apps/accounts/permissions.py` (`RequireRole`): Direct template for `RequireScope` — same `BasePermission` shape, same `PermissionDenied` → 403 flow; `RequireScope` takes a scope string instead of a role name
- `apps/orgs/permissions.py` (`IsOrgMember`, `IsOrgAdmin`): Permission class composition pattern — `RequireScope` follows same composition rules; must appear after `IsAuthenticated` in the permission list
- `apps/core/ratelimit.py` (`ratelimited_error`): Existing 429 handler wired via `RATELIMIT_VIEW` setting — extend or reuse for key-based rate limit 429 response; current handler returns `Retry-After` but not `X-RateLimit-*` headers; needs extension
- `apps/webhooks/` app structure: Template for `apps/api_keys/` app — same file layout (`models.py`, `schemas.py`, `controllers.py`, `services.py`, `migrations/`)
- `apps/billing/` settings patterns (`BILLING_PLANS`, startup validation): Template for `API_KEY_SCOPES` dict and `manage.py check` validator

### Established Patterns

- Settings-based feature config with `manage.py check` validation — `API_KEY_SCOPES` and `API_KEY_PREFIX` and `API_KEY_RATE_LIMIT` follow same pattern as `BILLING_PLANS` and `WEBHOOK_EVENTS`
- Ninja Extra `BasePermission` composition: `permissions=[IsAuthenticated, RequireRole("admin")]` — `RequireScope` slots into same chain
- Secret shown once: Phase 27 webhook secrets stored as SHA-256 hash; `secret` field returned only in POST response — identical pattern for APIKey raw value
- `apps/orgs/`: B2B_START/B2B_END markers isolate entire app — `apps/api_keys/` uses same marker pattern

### Integration Points

- `apps/api/config/settings/base.py`: Register `apps.api_keys` in `INSTALLED_APPS` (inside B2B_START/B2B_END markers); add `API_KEY_SCOPES`, `API_KEY_PREFIX`, `API_KEY_RATE_LIMIT` settings
- `apps/api/config/urls.py`: Register `APIKeyController` at `/api/v1/me/api-keys/`
- Ninja router auth: Register `ApiKeyAuth` as an additional auth backend alongside the existing session auth — Ninja resolves whichever backend succeeds first; `RequireScope` distinguishes further
- `apps/core/ratelimit.py`: Extend 429 handler to emit `X-RateLimit-*` headers on API key rate-limited responses
- B2B_START/B2B_END markers: Entire `apps/api_keys/` app is B2B-gated — same scaffolder `--with b2b` flag as orgs/ and webhooks/

</code_context>

<deferred>
## Deferred Ideas

- **Org-level API keys** — keys owned by an org rather than a user; natural next step for B2B products but not in v1.4 scope; future phase
- **Per-key rate limit overrides** — setting a different rate limit per key at creation time; products needing tiered API access build this on top of the settings baseline
- **Live/test key distinction** (`ft_live_` / `ft_test_`) — useful for payments-adjacent products; requires endpoint routing logic; future phase
- **Billing-integrated rate tiers** — `has_org_feature(user, 'api_rate_limit_tier')` driving rate limit lookup from plan; products build this on top of `API_KEY_RATE_LIMIT` baseline

</deferred>

---

_Phase: 28-api-key-authentication_
_Context gathered: 2026-03-13_
