# Phase 28: API Key Authentication - Research

**Researched:** 2026-03-13
**Domain:** Django Ninja Extra auth backends, django-ratelimit 4.1.0, SHA-256 key storage
**Confidence:** HIGH

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions

- API keys are **user-owned only** — not org-owned; org context is derived from user membership downstream if products need it
- Key management endpoints live at **`/api/v1/me/api-keys/`** — consistent with user-owned resource convention under `/me/`
- When an API key authenticates a request, the auth backend resolves it to the owner `User` and sets **`request.user = user`** — same Django User object as session auth; all existing `IsAuthenticated` and user-based logic works transparently; `RequireScope` adds on top of this
- APIKey model lives in a **new `apps/api_keys/` app** — mirrors the orgs/ and webhooks/ pattern; clean B2B_START/B2B_END marker boundary for the scaffolder; Phase 29 audit logging references `APIKey` by model name
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
- Rate limit value is a **global settings value**: `API_KEY_RATE_LIMIT = "1000/h"` — applies to all keys equally; products override per their tier by modifying the setting; default 1000/hour matches common API tier defaults <!-- pragma: allowlist secret -->
- X-RateLimit-\* headers computed from **the same Redis counter that `django-ratelimit` uses** — a middleware reads the cache key populated by django-ratelimit post-auth to derive `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`; one source of truth, no counter drift
- Rate limit key is the API key's stored prefix (`ft_a1b2c3d4`) — unique per key, not per user
- **`API_KEY_PREFIX = "ft_"`** in Django settings — products override to match their brand; single prefix type, no live/test distinction <!-- pragma: allowlist secret -->
- Random part: **`secrets.token_hex(32)`** — 64 lowercase hex characters, 256 bits of entropy; same approach as Phase 27 webhook secrets
- Full key shown once: `ft_<64 hex chars>` (e.g. `ft_a1b2c3d4e5f6...`)
- Stored in DB: `prefix = API_KEY_PREFIX + first 8 chars of random` (e.g. `ft_a1b2c3d4`); `key_hash = sha256(full_key)`; raw key never persisted

### Claude's Discretion

- Exact DB index strategy on `APIKey` (prefix + user compound index likely needed for key lookup)
- Middleware ordering for usage tracking (`last_used_at` / `usage_count` updates) — sync in auth backend or async via `transaction.on_commit()`
- Exact `manage.py check` validator implementation for `API_KEY_SCOPES`
- Pagination style for key list endpoint (follow existing pagination patterns)
- Whether key name/label field is required or optional at creation

### Deferred Ideas (OUT OF SCOPE)

- **Org-level API keys** — keys owned by an org rather than a user; natural next step for B2B products but not in v1.4 scope; future phase
- **Per-key rate limit overrides** — setting a different rate limit per key at creation time; products needing tiered API access build this on top of the settings baseline
- **Live/test key distinction** (`ft_live_` / `ft_test_`) — useful for payments-adjacent products; requires endpoint routing logic; future phase
- **Billing-integrated rate tiers** — `has_org_feature(user, 'api_rate_limit_tier')` driving rate limit lookup from plan; products build this on top of `API_KEY_RATE_LIMIT` baseline
  </user_constraints>

<phase_requirements>

## Phase Requirements

| ID      | Description                                                                                                                                                                 | Research Support                                                                                                                                                        |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| AKEY-01 | User can create/revoke API keys with scopes; raw key shown once at creation; prefix + SHA-256 hash stored only; `RequireScope` permission class enforces scope per endpoint | APIKey model design, `generate_key()` pattern from webhook model, `RequireScope` patterned after `RequireRole` in `apps/accounts/permissions.py`                        |
| AKEY-02 | API key requests are rate-limited per key via `django-ratelimit`; `X-RateLimit-*` response headers returned                                                                 | `get_usage()` return dict (`count`, `limit`, `should_limit`, `time_left`) maps directly to header values; middleware approach patterned after `AuthRateLimitMiddleware` |
| AKEY-03 | System tracks `last_used_at` and `usage_count` on each API key, updated on every authenticated request                                                                      | Updated in `ApiKeyAuth.authenticate()` return path; `update_fields` partial save avoids lock contention on unrelated fields                                             |

</phase_requirements>

---

## Summary

Phase 28 adds a custom API key system to the Django backend. The codebase already ships every supporting primitive: `RequireRole` (template for `RequireScope`), `AuthRateLimitMiddleware` and `apps/core/ratelimit.py` (template for key-based rate limit middleware), `WebhookEndpoint.generate_secret()` (template for key generation), and the `WEBHOOK_EVENTS` settings-check pattern (template for `API_KEY_SCOPES` validation).

The one genuinely new primitive is `ApiKeyAuth` — a Django Ninja `HttpBearer` subclass. `HttpBearer.__call__` extracts the token from `Authorization: Bearer <token>`, calls `authenticate(request, token)`, and returns the user on success or `None` on failure. The `authenticate` method computes `sha256(token)`, queries `APIKey` by hash, sets `request.user` and `request.api_key`, then updates `last_used_at`/`usage_count`. Ninja resolves auth backends left-to-right; whichever succeeds first wins.

The X-RateLimit-\* header challenge is solved by `django-ratelimit 4.1.0`'s `get_usage()` function, which returns `{"count": N, "limit": L, "should_limit": bool, "time_left": S}`. A middleware checks `request.api_key` post-auth and calls `get_usage(increment=False)` to read the current counter without incrementing again, then injects `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset` response headers. The rate-limit enforcement itself (increment + block) lives in `ApiKeyAuth.authenticate()`.

**Primary recommendation:** Build `apps/api_keys/` as a direct clone of `apps/webhooks/` app structure, implement `ApiKeyAuth` as `HttpBearer`, drive rate-limit both enforcement and header population from `get_usage()`, and pattern `RequireScope` exactly after `RequireRole`.

---

## Standard Stack

### Core

| Library              | Version     | Purpose                                                             | Why Standard                                                                |
| -------------------- | ----------- | ------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| `django-ratelimit`   | 4.1.0       | Per-key rate limiting + counter reads                               | Already in pyproject.toml; `get_usage()` returns all header data needed     |
| `django-ninja-extra` | >=0.21      | Auth backend (`HttpBearer`) and permission class (`BasePermission`) | Project framework; `HttpBearer` is the canonical Ninja auth extension point |
| `secrets` (stdlib)   | Python 3.12 | `secrets.token_hex(32)` for 64-char hex key                         | Used identically in Phase 27 webhook secret generation                      |
| `hashlib` (stdlib)   | Python 3.12 | `hashlib.sha256(key.encode()).hexdigest()`                          | Used in `WebhookEndpoint.generate_secret()` — exact same pattern            |
| `hmac` (stdlib)      | Python 3.12 | `hmac.compare_digest(stored_hash, computed_hash)`                   | Timing-safe comparison; prevents timing attacks on key lookup               |

### Supporting

| Library        | Version  | Purpose                                     | When to Use                                                       |
| -------------- | -------- | ------------------------------------------- | ----------------------------------------------------------------- |
| `django-redis` | existing | Redis cache backend for rate limit counters | Already configured; `RATELIMIT_USE_CACHE = "default"` points here |

### Alternatives Considered

| Instead of                       | Could Use                     | Tradeoff                                                                                                                                                               |
| -------------------------------- | ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Custom `ApiKeyAuth` (HttpBearer) | `djangorestframework-api-key` | DRF-specific `BasePermission` — incompatible with Django Ninja Extra; already rejected in STATE.md                                                                     |
| SHA-256 hash storage             | HMAC-SHA256 (secret key)      | HMAC adds a server-side secret but makes key theft from DB less exploitable; SHA-256 is simpler, established practice (GitHub, Stripe), and STATE.md locked to SHA-256 |
| `get_usage()` for header reading | Custom Redis counter          | Two counters would drift; `get_usage()` is the single source of truth                                                                                                  |

**Installation:** No new packages required. All dependencies already in `pyproject.toml`.

---

## Architecture Patterns

### Recommended Project Structure

```
apps/api_keys/
├── __init__.py          # Module-level import triggers RED state before implementation
├── apps.py              # AppConfig — imports checks in ready()
├── models.py            # APIKey model
├── schemas.py           # APIKeyCreateOut, APIKeyOut, APIKeyIn
├── controllers.py       # APIKeyController at /api/v1/me/api-keys/
├── services.py          # APIKeyService (create, revoke logic)
├── auth.py              # ApiKeyAuth(HttpBearer) + RequireScope permission
├── checks.py            # manage.py check for API_KEY_SCOPES + API_KEY_PREFIX
├── middleware.py        # ApiKeyRateLimitHeaderMiddleware
└── migrations/
    ├── __init__.py
    └── 0001_initial.py
```

### Pattern 1: APIKey Model

**What:** `APIKey` stores `prefix` (non-secret), `key_hash` (SHA-256 of full key), `user` FK, `scopes` (JSONField list), `name`, `is_active`, `last_used_at`, `usage_count`, `created_at`.
**When to use:** Foundation for all API key operations.

```python
# Source: modeled after apps/webhooks/models.py + WebhookEndpoint.generate_secret()
import hashlib
import secrets
import uuid
from django.conf import settings
from django.db import models

class APIKey(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="api_keys",
    )
    prefix = models.CharField(max_length=32, unique=True, db_index=True)
    key_hash = models.CharField(max_length=64)  # SHA-256 hex
    scopes = models.JSONField(default=list)
    name = models.CharField(max_length=255, blank=True, default="")
    is_active = models.BooleanField(default=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    usage_count = models.PositiveBigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "api_keys_key"
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["prefix"]),  # Fast auth backend lookup
        ]

    @staticmethod
    def generate_key() -> tuple[str, str, str]:
        """Return (raw_key, prefix, key_hash).

        raw_key: full key shown once to user — never stored
        prefix: API_KEY_PREFIX + first 8 chars of random portion (e.g. ft_a1b2c3d4)
        key_hash: SHA-256 hex of raw_key — stored for auth lookup
        """
        prefix_setting = getattr(settings, "API_KEY_PREFIX", "ft_")
        random_part = secrets.token_hex(32)  # 64 hex chars
        raw_key = f"{prefix_setting}{random_part}"
        stored_prefix = f"{prefix_setting}{random_part[:8]}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        return raw_key, stored_prefix, key_hash
```

### Pattern 2: ApiKeyAuth HttpBearer Backend

**What:** Ninja auth backend that resolves a Bearer token to a `User`, sets `request.api_key`, and updates usage stats.
**When to use:** Register alongside `SessionAuth()` on any controller that accepts API key auth.

```python
# Source: ninja.security.HttpBearer (verified via uv run python -c "...")
import hashlib
import hmac
from ninja.security import HttpBearer
from django.http import HttpRequest
from django.utils import timezone

class ApiKeyAuth(HttpBearer):
    """Resolve Bearer token to User; set request.api_key for downstream middleware."""

    def authenticate(self, request: HttpRequest, token: str) -> object | None:
        key_hash = hashlib.sha256(token.encode()).hexdigest()
        # Look up by hash first — prefix is for display only
        # Use hmac.compare_digest to prevent timing attacks
        try:
            api_key = APIKey.objects.select_related("user").get(
                key_hash=key_hash, is_active=True
            )
        except APIKey.DoesNotExist:
            return None

        # Constant-time comparison (redundant given DB lookup but defense-in-depth)
        if not hmac.compare_digest(api_key.key_hash, key_hash):
            return None

        # Update usage tracking (AKEY-03)
        APIKey.objects.filter(pk=api_key.pk).update(
            last_used_at=timezone.now(),
            usage_count=models.F("usage_count") + 1,
        )
        api_key.refresh_from_db(fields=["last_used_at", "usage_count"])

        # Set on request for RequireScope and rate-limit middleware
        request.api_key = api_key  # type: ignore[attr-defined]
        request.user = api_key.user  # Ninja reads this; IsAuthenticated passes
        return api_key.user
```

### Pattern 3: RequireScope Permission Class

**What:** Ninja Extra `BasePermission` that (a) rejects session-only requests and (b) checks the API key has the required scope.
**When to use:** Any endpoint that must be API-key-only with a specific scope.

```python
# Source: apps/accounts/permissions.py RequireRole — direct template
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest
from ninja_extra import ControllerBase
from ninja_extra.permissions import BasePermission

class RequireScope(BasePermission):
    """Gate access to API key requests that include the required scope.

    CRITICAL: Rejects session-authenticated requests even if IsAuthenticated passes.
    There is NO auth fallback for scope-gated endpoints.

    Usage:
        permissions=[IsAuthenticated, RequireScope("read")]

    IsAuthenticated MUST appear first. RequireScope raises PermissionDenied (→ 403)
    if request.api_key is absent (session-only) or lacks the required scope.
    """

    def __init__(self, scope: str) -> None:
        self.scope = scope

    def has_permission(self, request: HttpRequest, controller: ControllerBase) -> bool:
        api_key = getattr(request, "api_key", None)
        if api_key is None:
            # Session-authenticated request — no API key Bearer token present
            raise PermissionDenied
        if self.scope not in (api_key.scopes or []):
            raise PermissionDenied
        return True
```

### Pattern 4: X-RateLimit-\* Middleware

**What:** Django middleware that enforces per-key rate limiting (returning 429) and injects `X-RateLimit-*` headers on all API key authenticated responses.
**When to use:** Insert after `AuthRateLimitMiddleware` in `MIDDLEWARE`.

The key insight: `get_usage()` returns `{"count": N, "limit": L, "should_limit": bool, "time_left": S}` where `time_left` is seconds until window reset. Use `increment=True` on the auth path (enforces) and `increment=False` in middleware (reads current state without double-counting).

```python
# Source: apps/core/middleware.py AuthRateLimitMiddleware + django_ratelimit.core.get_usage()
import time
from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django_ratelimit.core import get_usage

class ApiKeyRateLimitMiddleware:
    """Enforce per-key rate limiting and inject X-RateLimit-* response headers.

    Only activates when request.api_key is set (API key authenticated requests).
    Rate limit is enforced here (not in auth backend) so that:
    - 429 response includes X-RateLimit-* headers
    - get_usage() increment happens once per request (not per auth attempt)

    Rate limit key: api_key.prefix (e.g. "ft_a1b2c3d4") — unique per key.
    """

    def __init__(self, get_response) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        api_key = getattr(request, "api_key", None)
        if api_key is None:
            return self.get_response(request)

        rate = getattr(settings, "API_KEY_RATE_LIMIT", "1000/h")
        usage = get_usage(
            request,
            group="api_key",
            key=lambda g, r: api_key.prefix,  # per-key, not per-IP
            rate=rate,
            increment=True,
        )

        if usage and usage["should_limit"]:
            from apps.core.ratelimit import ratelimited_error
            response = ratelimited_error(request)
            self._inject_headers(response, usage, rate)
            return response

        response = self.get_response(request)
        if usage:
            self._inject_headers(response, usage, rate)
        return response

    def _inject_headers(self, response: HttpResponse, usage: dict, rate: str) -> None:
        limit = usage["limit"]
        count = usage["count"]
        remaining = max(0, limit - count)
        reset_ts = int(time.time()) + max(0, usage["time_left"])
        response["X-RateLimit-Limit"] = str(limit)
        response["X-RateLimit-Remaining"] = str(remaining)
        response["X-RateLimit-Reset"] = str(reset_ts)
```

**IMPORTANT — middleware ordering:** `ApiKeyRateLimitMiddleware` must come AFTER `AuthenticationMiddleware` and `allauth.account.middleware.AccountMiddleware` (so `request.user` is populated), and AFTER `RequestContextMiddleware`. Add it between `AuthRateLimitMiddleware` and `MessageMiddleware`:

```python
MIDDLEWARE = [
    ...
    "apps.core.middleware.AuthRateLimitMiddleware",
    "apps.api_keys.middleware.ApiKeyRateLimitMiddleware",  # NEW — after auth RL
    "django.contrib.messages.middleware.MessageMiddleware",
    ...
]
```

### Pattern 5: Settings and Checks

**What:** Settings-based scope catalog with `manage.py check` validation — mirrors `WEBHOOK_EVENTS` / `apps/webhooks/checks.py`.

```python
# In config/settings/base.py (inside B2B_START/B2B_END)
API_KEY_PREFIX: str = "ft_"  # Products override to brand their keys (e.g. "gh_", "sk_")
API_KEY_RATE_LIMIT: str = "1000/h"  # Global per-key limit; products override per tier
API_KEY_SCOPES: dict = {
    "read": {"description": "Read-only access to all resources"},
    "write": {"description": "Create and update resources"},
    "admin": {"description": "Full access including destructive operations"},
}
```

Check implementation mirrors `apps/webhooks/checks.py`:

```python
# apps/api_keys/checks.py
from django.conf import settings
from django.core.checks import Warning, register

@register()
def check_api_key_scopes(app_configs, **kwargs):
    errors = []
    scopes = getattr(settings, "API_KEY_SCOPES", None)
    if scopes is None:
        errors.append(Warning("API_KEY_SCOPES setting is not defined.", id="api_keys.W001"))
        return errors
    if not isinstance(scopes, dict):
        errors.append(Warning("API_KEY_SCOPES must be a dict.", id="api_keys.W002"))
        return errors
    for scope_name, config in scopes.items():
        if not isinstance(config, dict) or "description" not in config:
            errors.append(Warning(
                f"API_KEY_SCOPES['{scope_name}'] must be a dict with a 'description' key.",
                id="api_keys.W003",
            ))
    return errors
```

### Pattern 6: Controller

**What:** `APIKeyController` with create/list/revoke under `/api/v1/me/api-keys/`. Patterned after `WebhookEndpointController` but user-scoped (no `org_slug` in URL).

```python
# Source: apps/webhooks/controllers.py pattern
@api_controller(
    "/me/api-keys",
    tags=["api-keys"],
    auth=[SessionAuth(), jwt_token_auth],  # management endpoints use session auth
    permissions=[IsAuthenticated],
)
class APIKeyController(ControllerBase):
    @route.post("", response={201: APIKeyCreateOut})
    def create_key(self, request: HttpRequest, body: APIKeyIn) -> Any: ...

    @route.get("", response={200: dict})
    def list_keys(self, request: HttpRequest, page: int = 1, page_size: int = 20) -> Any: ...

    @route.delete("/{key_id}", response={204: None})
    def revoke_key(self, request: HttpRequest, key_id: str) -> Any: ...
```

Note: Management endpoints (`create_key`, `list_keys`, `revoke_key`) use **session auth** — users manage keys via the web UI with a session. The `ApiKeyAuth` backend is registered on product endpoints that accept key-based access, not on the key management controller itself.

### Pattern 7: Scope Validation at Key Creation

**What:** Validate that requested scopes exist in `API_KEY_SCOPES` at key creation time.

```python
# In schemas.py — APIKeyIn validator
from django.conf import settings
from pydantic import field_validator
from ninja import Schema

class APIKeyIn(Schema):
    name: str = ""
    scopes: list[str]

    @field_validator("scopes")
    @classmethod
    def scopes_must_be_valid(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("scopes must contain at least one scope.")
        valid = set(getattr(settings, "API_KEY_SCOPES", {}).keys())
        invalid = set(v) - valid
        if invalid:
            raise ValueError(f"Unknown scopes: {sorted(invalid)}. Valid: {sorted(valid)}")
        return v
```

### Anti-Patterns to Avoid

- **Storing the raw key at rest:** Never store `raw_key` — only `prefix` and `key_hash`. The `generate_key()` method returns raw key, prefix, and hash; the raw key is returned in the response body only and never saved.
- **Using `==` for hash comparison:** Always use `hmac.compare_digest(a, b)` to prevent timing-based enumeration of hashes.
- **Double-incrementing the rate limit counter:** Do NOT call `get_usage(increment=True)` in both `ApiKeyAuth.authenticate()` and the middleware. Pick ONE location — the middleware owns rate-limit enforcement; the auth backend owns user resolution and usage tracking.
- **No `from __future__ import annotations` in controllers/schemas:** The existing Phase 27 DECISION confirmed this breaks Pydantic's `model_rebuild()` at runtime with `ninja_extra`. Do not add it.
- **Session auth bypass via RequireScope misconfiguration:** `permissions=[RequireScope("read")]` without `IsAuthenticated` first — Ninja would still serve the endpoint to unauthenticated requests if `ApiKeyAuth` returns `None`. Always compose: `permissions=[IsAuthenticated, RequireScope("read")]`.

---

## Don't Hand-Roll

| Problem                                          | Don't Build                           | Use Instead                                    | Why                                                                                                                |
| ------------------------------------------------ | ------------------------------------- | ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| Rate limit counter storage and window management | Custom Redis key with TTL             | `django_ratelimit.core.get_usage()`            | Sliding window jitter, multi-backend support, `RATELIMIT_FAIL_OPEN`, `RATELIMIT_ENABLE` test override all included |
| HTTP 429 response format                         | New JSON response builder             | Extend `apps/core/ratelimit.ratelimited_error` | Existing handler returns correct `RATE_001` error code; just add `X-RateLimit-*` headers                           |
| Bearer token extraction                          | Manual `Authorization` header parsing | `ninja.security.HttpBearer`                    | Handles scheme validation, splits `Bearer <token>`, returns `None` on malformed headers                            |

---

## Common Pitfalls

### Pitfall 1: `get_usage()` Requires Either `group` or `fn` — Not Both

**What goes wrong:** `get_usage(request, key=..., rate=..., increment=True)` raises `ImproperlyConfigured: get_usage must be called with either 'group' or 'fn' arguments`.
**Why it happens:** The function signature is `get_usage(request, group=None, fn=None, key=None, rate=None, method=ALL, increment=False)` — group and fn both default to None but one is required.
**How to avoid:** Always pass `group="api_key"` (or any stable string) when calling `get_usage()` from middleware where no function handle exists.
**Warning signs:** `ImproperlyConfigured` exception on first API key request.

### Pitfall 2: `key` Parameter Must Be Callable or a Known Simple Key String

**What goes wrong:** Passing `key=api_key.prefix` (a string value) causes `ImproperlyConfigured: Could not understand ratelimit key: ft_a1b2c3d4` — django-ratelimit interprets the string as a key-type identifier, not a literal value.
**Why it happens:** `is_ratelimited` / `get_usage` resolve the `key` argument: if it's callable it calls it; if it's in `_SIMPLE_KEYS` (`ip`, `user`, `header`) it uses the built-in resolver; if it contains `:` it uses an accessor; if it contains `.` it imports it. A raw prefix string matches none of these.
**How to avoid:** Use `key=lambda g, r: api_key.prefix` — a callable that returns the literal prefix value.

### Pitfall 3: Rate Limit Headers Not Present on Non-Rate-Limited Responses

**What goes wrong:** `X-RateLimit-*` headers only appear on 429 responses, not on normal 200 responses.
**Why it happens:** Middleware only injects headers in the 429 branch.
**How to avoid:** Inject headers unconditionally when `usage` is not None — both on the normal response path and the 429 path (as shown in `_inject_headers` method).

### Pitfall 4: `test_isolation_settings` Fixture Disables Rate Limiting Globally

**What goes wrong:** `get_usage()` returns `None` when `settings.RATELIMIT_ENABLE = False` (set by the `test_isolation_settings` autouse fixture in `conftest.py`). Tests for rate limiting headers find no headers on responses.
**Why it happens:** `get_usage()` short-circuits to `return None` when `RATELIMIT_ENABLE` is falsy — so `usage` is None, no headers injected.
**How to avoid:** Rate limit tests must override the setting: `settings.RATELIMIT_ENABLE = True`. Use `LocMemCache` as the counter backend (already configured by `test_isolation_settings`). Add a dedicated test that re-enables rate limiting and verifies headers are present.

### Pitfall 5: `request.api_key` Not Set for Session-Auth Requests — Middleware Must Guard

**What goes wrong:** `ApiKeyRateLimitMiddleware` accesses `request.api_key` but session-authenticated requests never set it, causing an `AttributeError`.
**Why it happens:** `request.api_key` is only set by `ApiKeyAuth.authenticate()`. Session-authenticated requests go through a different auth path.
**How to avoid:** Always guard with `api_key = getattr(request, "api_key", None)` and early-return if `None` (as shown in the middleware pattern).

### Pitfall 6: N+1 on `api_key.user` Access

**What goes wrong:** `APIKey.objects.get(key_hash=key_hash)` + `api_key.user` triggers a second query per request, caught by the `_nplusone_guard` autouse fixture.
**Why it happens:** `user` FK is not pre-fetched.
**How to avoid:** Use `APIKey.objects.select_related("user").get(key_hash=key_hash, is_active=True)`.

---

## Code Examples

### Key Generation (Verified Pattern)

```python
# Source: apps/webhooks/models.py WebhookEndpoint.generate_secret() — identical approach
import hashlib
import secrets
from django.conf import settings

def generate_key() -> tuple[str, str, str]:
    """Return (raw_key, stored_prefix, key_hash)."""
    prefix_setting = getattr(settings, "API_KEY_PREFIX", "ft_")
    random_part = secrets.token_hex(32)            # 64 hex chars, 256 bits entropy
    raw_key = f"{prefix_setting}{random_part}"     # full key shown once
    stored_prefix = f"{prefix_setting}{random_part[:8]}"  # e.g. ft_a1b2c3d4
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    return raw_key, stored_prefix, key_hash
```

### get_usage Return Shape (Verified by Source Inspection)

```python
# Source: django_ratelimit.core.get_usage() — verified 2026-03-13
# Returns dict when rate limit is active:
{
    "count": 42,          # current counter value in this window
    "limit": 1000,        # rate limit (from rate string "1000/h")
    "should_limit": False,  # True when count > limit
    "time_left": 1847,    # seconds until window resets (use for X-RateLimit-Reset)
}
# Returns None when RATELIMIT_ENABLE=False or method doesn't match
```

### HttpBearer Interface (Verified)

```python
# Source: ninja.security.HttpBearer — verified 2026-03-13
# Subclass must implement authenticate(request, token) -> Optional[Any]
# Return None to fail auth (Ninja tries next backend)
# Return any truthy value to succeed; Ninja sets request.auth to the return value
# For Django compatibility, also set request.user directly in authenticate()
```

### Schemas Pattern (No `from __future__ import annotations`)

```python
# Source: STATE.md Phase 27 decision — confirmed deferred type eval breaks Pydantic
# schemas.py — do NOT add "from __future__ import annotations"
from datetime import datetime
from ninja import Schema

class APIKeyCreateOut(Schema):
    """Returned ONLY from POST /me/api-keys — includes raw_key shown once."""
    id: str
    name: str
    scopes: list[str]
    prefix: str       # e.g. "ft_a1b2c3d4" — human-visible identifier
    is_active: bool
    created_at: datetime
    key: str          # Raw key shown once — copy and store immediately

class APIKeyOut(Schema):
    """Returned for list — NO key field."""
    id: str
    name: str
    scopes: list[str]
    prefix: str
    is_active: bool
    last_used_at: datetime | None
    usage_count: int
    created_at: datetime
```

---

## State of the Art

| Old Approach                                  | Current Approach                                               | When Changed                               | Impact                                                     |
| --------------------------------------------- | -------------------------------------------------------------- | ------------------------------------------ | ---------------------------------------------------------- |
| Store full API key in DB (hashed with bcrypt) | Store only SHA-256 hex hash; prefix for display                | Standard since ~2018 (GitHub, Stripe)      | Cannot retrieve key after creation; enforced by DB schema  |
| IP-based rate limiting only                   | Per-resource rate limiting (`key=lambda g, r: api_key.prefix`) | django-ratelimit 3.x+ callable key support | True per-key limits independent of caller IP               |
| `is_ratelimited()` returns bool only          | `get_usage()` returns dict with count/limit/time_left          | django-ratelimit 3.0+                      | `X-RateLimit-*` headers derivable without separate counter |

**Deprecated/outdated:**

- `RATELIMIT_CACHE_PREFIX` setting: Defaults to `"rl:"` — matches what `_make_cache_key()` produces. No need to set explicitly unless collision risk.
- `from __future__ import annotations` in Ninja controllers/schemas: Explicitly breaks Pydantic at runtime in this project (STATE.md Phase 27 decision).

---

## Open Questions

1. **Middleware placement vs. auth backend for rate limiting enforcement**
   - What we know: The middleware pattern keeps 429 + header injection in one place. The auth backend pattern would prevent user resolution on over-limit requests (desirable for counting) but makes header injection harder.
   - What's unclear: Which to pick is Claude's Discretion per CONTEXT.md.
   - Recommendation: Enforce in middleware (as shown above). Reason: `ApiKeyAuth.authenticate()` does not have access to the HTTP response object, so headers cannot be injected there. Middleware owns both enforcement and header injection — single responsibility, no awkward threading of response objects.

2. **`last_used_at` / `usage_count` update — sync vs. async**
   - What we know: Synchronous `update()` in `authenticate()` adds a DB write to every API key request. `transaction.on_commit()` defers it but requires an open transaction.
   - What's unclear: At what request volume is sync update problematic? This is Claude's Discretion.
   - Recommendation: Synchronous `F("usage_count") + 1` update in the middleware (not auth backend) using `update_fields=["last_used_at", "usage_count"]` — this is a direct partial UPDATE on the PK, sub-millisecond. Use `update()` (not `save()`) to avoid locking unrelated fields. Defer to async only if profiling shows contention in a future phase.

3. **DB index strategy**
   - What we know: Auth lookup is `APIKey.objects.get(key_hash=key_hash, is_active=True)`. `key_hash` is a 64-char hex string — high cardinality.
   - Recommendation: Single index on `key_hash` is sufficient for the auth lookup (unique by design). Compound index `(user, is_active)` covers `list_keys(request.user)`. `prefix` unique constraint + index covers display lookups. Three indexes total.

---

## Validation Architecture

### Test Framework

| Property           | Value                                                   |
| ------------------ | ------------------------------------------------------- |
| Framework          | pytest + pytest-django (existing)                       |
| Config file        | `apps/api/pytest.ini` or `pyproject.toml [tool.pytest]` |
| Quick run command  | `uv run pytest apps/api/tests/api_keys/ -x -q`          |
| Full suite command | `uv run pytest apps/api/tests/ -x -q`                   |

### Phase Requirements → Test Map

| Req ID  | Behavior                                                                    | Test Type   | Automated Command                                                                                      | File Exists? |
| ------- | --------------------------------------------------------------------------- | ----------- | ------------------------------------------------------------------------------------------------------ | ------------ |
| AKEY-01 | Key creation returns raw key once; subsequent list does not include raw key | integration | `uv run pytest apps/api/tests/api_keys/test_controllers.py::test_create_key_returns_raw_key_once -x`   | Wave 0       |
| AKEY-01 | Revoke sets `is_active=False`; revoked key auth returns 401                 | integration | `uv run pytest apps/api/tests/api_keys/test_controllers.py::test_revoke_key -x`                        | Wave 0       |
| AKEY-01 | `RequireScope` rejects session-only request with 403                        | integration | `uv run pytest apps/api/tests/api_keys/test_auth.py::test_require_scope_rejects_session -x`            | Wave 0       |
| AKEY-01 | `RequireScope` rejects key missing required scope with 403                  | unit        | `uv run pytest apps/api/tests/api_keys/test_auth.py::test_require_scope_rejects_wrong_scope -x`        | Wave 0       |
| AKEY-02 | Requests exceeding rate limit return HTTP 429 with `X-RateLimit-*` headers  | integration | `uv run pytest apps/api/tests/api_keys/test_ratelimit.py::test_rate_limit_returns_429_with_headers -x` | Wave 0       |
| AKEY-02 | Normal requests include `X-RateLimit-*` headers with correct values         | integration | `uv run pytest apps/api/tests/api_keys/test_ratelimit.py::test_headers_on_normal_response -x`          | Wave 0       |
| AKEY-03 | `last_used_at` updated on authenticated request                             | integration | `uv run pytest apps/api/tests/api_keys/test_auth.py::test_last_used_at_updated -x`                     | Wave 0       |
| AKEY-03 | `usage_count` incremented on each authenticated request                     | integration | `uv run pytest apps/api/tests/api_keys/test_auth.py::test_usage_count_incremented -x`                  | Wave 0       |

### Sampling Rate

- **Per task commit:** `uv run pytest apps/api/tests/api_keys/ -x -q`
- **Per wave merge:** `uv run pytest apps/api/tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `apps/api/tests/api_keys/__init__.py` — module-level import RED trigger (mirrors `tests/webhooks/__init__.py`)
- [ ] `apps/api/tests/api_keys/conftest.py` — user + api_key fixtures
- [ ] `apps/api/tests/api_keys/test_models.py` — covers key generation, hash storage
- [ ] `apps/api/tests/api_keys/test_auth.py` — covers `ApiKeyAuth`, `RequireScope`, AKEY-01, AKEY-03
- [ ] `apps/api/tests/api_keys/test_ratelimit.py` — covers AKEY-02 (rate limit headers); must re-enable `RATELIMIT_ENABLE = True`
- [ ] `apps/api/tests/api_keys/test_controllers.py` — covers create/list/revoke HTTP endpoints
- [ ] `apps/api/tests/api_keys/test_checks.py` — covers `API_KEY_SCOPES` validator warnings

---

## Sources

### Primary (HIGH confidence)

- `apps/api/apps/webhooks/models.py` — `generate_secret()` pattern used verbatim for key generation
- `apps/api/apps/accounts/permissions.py` — `RequireRole` pattern used verbatim for `RequireScope`
- `apps/api/apps/core/middleware.py` — `AuthRateLimitMiddleware` + `is_ratelimited()` call pattern
- `apps/api/apps/core/ratelimit.py` — existing 429 handler to extend
- `apps/api/apps/webhooks/checks.py` — `check_webhook_events` pattern for `check_api_key_scopes`
- `apps/api/apps/webhooks/controllers.py` — controller structure pattern
- `apps/api/config/settings/base.py` — `RATELIMIT_*` settings, `MIDDLEWARE` order, `B2B_START/B2B_END` markers
- `apps/api/config/urls.py` — `auto_discover_controllers()` pattern; no manual URL registration needed
- `django_ratelimit.core.get_usage` source (verified via `uv run python`) — return dict shape confirmed: `{count, limit, should_limit, time_left}`
- `django_ratelimit.core._make_cache_key` source (verified) — cache key format confirmed
- `ninja.security.HttpBearer` source (verified) — `authenticate(request, token)` interface confirmed
- `apps/api/tests/conftest.py` — `test_isolation_settings` autouse sets `RATELIMIT_ENABLE=False`; rate limit tests must override

### Secondary (MEDIUM confidence)

- `apps/api/.planning/STATE.md` — locked decisions: SHA-256 storage, `hmac.compare_digest`, no `from __future__ import annotations` in Ninja code
- `apps/api/pyproject.toml` — `django-ratelimit==4.1.0`, `django-ninja-extra>=0.21` confirmed

---

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — all dependencies already installed; no new packages
- Architecture: HIGH — all patterns verified from existing codebase source code
- Rate limit header implementation: HIGH — `get_usage()` return shape verified by source inspection
- Pitfalls: HIGH — most derived from direct source inspection, not training data

**Research date:** 2026-03-13
**Valid until:** 2026-06-13 (stable libraries; django-ratelimit 4.1.0 is pinned)
