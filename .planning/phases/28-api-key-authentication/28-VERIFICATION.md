---
phase: 28-api-key-authentication
verified: 2026-03-13T14:00:00Z
status: passed
score: 9/9 must-haves verified
re_verification: false
---

# Phase 28: API Key Authentication Verification Report

**Phase Goal:** Deliver a production-ready API key authentication system for the Foundation Template's B2B module — HMAC-verified keys, scoped permissions, per-key rate limiting, and a full CRUD management API
**Verified:** 2026-03-13T14:00:00Z
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| #   | Truth                                                                                                                                   | Status   | Evidence                                                                                                                                                                                      |
| --- | --------------------------------------------------------------------------------------------------------------------------------------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | User can create API keys; raw key returned once in POST response; prefix + SHA-256 hash stored only                                     | VERIFIED | `controllers.py` returns `key: raw_key` in 201 response; `key_hash = hashlib.sha256(raw_key.encode()).hexdigest()` in `models.py`; `test_create_key_returns_raw_key_once` GREEN               |
| 2   | User can revoke API keys; revoked keys cannot authenticate                                                                              | VERIFIED | `services.py` sets `is_active=False`; `auth.py` queries `.get(key_hash=..., is_active=True)`; `test_revoke_key_sets_inactive` and `test_revoked_key_auth_returns_401` GREEN                   |
| 3   | RequireScope rejects session-only requests (no api_key fallback) with 403                                                               | VERIFIED | `auth.py` RequireScope raises `PermissionDenied` when `request.api_key is None`; `test_require_scope_rejects_session_request` GREEN                                                           |
| 4   | RequireScope enforces scope membership per endpoint                                                                                     | VERIFIED | `RequireScope.has_permission()` checks `self.scope not in api_key.scopes`; `test_require_scope_rejects_wrong_scope` and `test_require_scope_passes_with_correct_scope` GREEN                  |
| 5   | API key authenticated responses include X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset headers; 429 returned when exceeded | VERIFIED | `middleware.py` `_inject_headers()` sets all three headers; enforces with `get_usage(increment=True)`; `test_headers_on_normal_response` and `test_rate_limit_returns_429_with_headers` GREEN |
| 6   | Session-authenticated requests pass through rate limit middleware unchanged                                                             | VERIFIED | `middleware.py` guards with `getattr(request, "api_key", None)` and returns `get_response(request)` unmodified; `test_no_headers_on_session_request` GREEN                                    |
| 7   | last_used_at and usage_count updated on every successful authenticated request                                                          | VERIFIED | `auth.py` partial UPDATE via `APIKey.objects.filter(pk=).update(last_used_at=..., usage_count=F("usage_count")+1)`; `test_last_used_at_updated` and `test_usage_count_incremented` GREEN      |
| 8   | API_KEY_SCOPES validator runs at startup; warns with coded IDs for missing/malformed config                                             | VERIFIED | `checks.py` registers `check_api_key_scopes` via `@register()`; `apps.py` imports checks in `ready()`; W001/W002/W003 tested GREEN; `manage.py check` shows zero api_keys.\* warnings         |
| 9   | Full test suite passes GREEN (30 tests covering all AKEY-01/02/03 behaviors)                                                            | VERIFIED | `uv run pytest tests/api_keys/ -q` → `30 passed, 15 warnings in 17.59s`                                                                                                                       |

**Score:** 9/9 truths verified

---

### Required Artifacts

| Artifact                                            | Expected                                                    | Status   | Details                                                                                                                                                                 |
| --------------------------------------------------- | ----------------------------------------------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `apps/api/tests/api_keys/__init__.py`               | Module-level RED trigger import                             | VERIFIED | Contains `from apps.api_keys.models import APIKey` — was RED trigger before implementation                                                                              |
| `apps/api/tests/api_keys/conftest.py`               | api_user, api_key, revoked_api_key fixtures                 | VERIFIED | All three fixtures present with lazy imports and `_raw_key` attribute                                                                                                   |
| `apps/api/tests/api_keys/test_models.py`            | Key generation and hash storage tests                       | VERIFIED | 6 tests, all GREEN                                                                                                                                                      |
| `apps/api/tests/api_keys/test_auth.py`              | ApiKeyAuth, RequireScope, last_used_at, usage_count tests   | VERIFIED | 10 tests, all GREEN                                                                                                                                                     |
| `apps/api/tests/api_keys/test_ratelimit.py`         | X-RateLimit-\* header and 429 enforcement tests             | VERIFIED | 3 tests with `@override_settings(RATELIMIT_ENABLE=True)`, all GREEN                                                                                                     |
| `apps/api/tests/api_keys/test_controllers.py`       | create/list/revoke HTTP endpoint tests                      | VERIFIED | 7 tests, all GREEN                                                                                                                                                      |
| `apps/api/tests/api_keys/test_checks.py`            | API_KEY_SCOPES manage.py check validator tests              | VERIFIED | 4 tests, all GREEN                                                                                                                                                      |
| `apps/api/apps/api_keys/models.py`                  | APIKey model with generate_key()                            | VERIFIED | All required fields present; `generate_key()` returns (raw_key, stored_prefix, key_hash) with 256-bit entropy                                                           |
| `apps/api/apps/api_keys/auth.py`                    | ApiKeyAuth and RequireScope                                 | VERIFIED | Both classes exported; `hmac.compare_digest` used; `select_related("user")` present                                                                                     |
| `apps/api/apps/api_keys/middleware.py`              | ApiKeyRateLimitMiddleware                                   | VERIFIED | `get_usage(group="api_key", key=lambda g,r: api_key.prefix, increment=True)` wired correctly                                                                            |
| `apps/api/apps/api_keys/schemas.py`                 | APIKeyIn, APIKeyOut, APIKeyCreateOut                        | VERIFIED | All three schemas; `key` field only in `APIKeyCreateOut`; scope validator in `APIKeyIn`                                                                                 |
| `apps/api/apps/api_keys/services.py`                | APIKeyService.create(), revoke(), list_for_user()           | VERIFIED | All three classmethods present; `Http404 from None` for DoesNotExist                                                                                                    |
| `apps/api/apps/api_keys/controllers.py`             | APIKeyController with POST/GET/DELETE                       | VERIFIED | Routes: `POST /`, `GET /`, `DELETE /{key_id}/` with correct trailing slashes                                                                                            |
| `apps/api/apps/api_keys/checks.py`                  | check_api_key_scopes manage.py check                        | VERIFIED | W001/W002/W003 warning IDs registered                                                                                                                                   |
| `apps/api/apps/api_keys/migrations/0001_initial.py` | Initial migration creating api_keys_key table               | VERIFIED | Auto-generated; creates `api_keys_key` table with 3 indexes (key_hash, user+is_active, prefix)                                                                          |
| `apps/api/config/settings/base.py`                  | API_KEY_SCOPES, API_KEY_PREFIX, API_KEY_RATE_LIMIT settings | VERIFIED | All three settings inside B2B_START/B2B_END markers; `apps.api_keys` in INSTALLED_APPS block; `ApiKeyRateLimitMiddleware` in MIDDLEWARE after `AuthRateLimitMiddleware` |

---

### Key Link Verification

| From               | To                                      | Via                                                               | Status | Details                                                                                                     |
| ------------------ | --------------------------------------- | ----------------------------------------------------------------- | ------ | ----------------------------------------------------------------------------------------------------------- |
| `auth.py`          | `models.py` APIKey                      | `select_related("user").get(key_hash=..., is_active=True)`        | WIRED  | Line 32: `APIKey.objects.select_related("user").get(key_hash=key_hash, is_active=True)`                     |
| `auth.py`          | `request.api_key`                       | `request.api_key = api_key` in `authenticate()`                   | WIRED  | Line 48: `request.api_key = api_key` set before returning user                                              |
| `middleware.py`    | `django_ratelimit.core.get_usage`       | `get_usage(group="api_key", key=lambda ...)`                      | WIRED  | Lines 43-49: `get_usage` called with `group="api_key"`, callable `key=` lambda closure, `increment=True`    |
| `middleware.py`    | `apps.core.ratelimit.ratelimited_error` | lazy import for 429 response                                      | WIRED  | Lines 52-53: `from apps.core.ratelimit import ratelimited_error; response = ratelimited_error(request)`     |
| `controllers.py`   | `config/urls.py`                        | `api.auto_discover_controllers()`                                 | WIRED  | `urls.py` line 165: `api.auto_discover_controllers()` — `apps.api_keys` in INSTALLED_APPS enables discovery |
| `apps.py`          | `checks.py`                             | `from apps.api_keys import checks` in `ready()`                   | WIRED  | `apps.py` line 9: `from apps.api_keys import checks  # noqa: F401`                                          |
| `settings/base.py` | `apps.api_keys`                         | INSTALLED_APPS inside B2B_START/B2B_END                           | WIRED  | Line 122: `"apps.api_keys",  # B2B MODULE — API key authentication`                                         |
| `settings/base.py` | `ApiKeyRateLimitMiddleware`             | MIDDLEWARE after AuthRateLimitMiddleware inside B2B_START/B2B_END | WIRED  | Lines 140-143: entry appears directly after `AuthRateLimitMiddleware`                                       |

---

### Requirements Coverage

| Requirement | Source Plans        | Description                                                                                                                             | Status    | Evidence                                                                                                       |
| ----------- | ------------------- | --------------------------------------------------------------------------------------------------------------------------------------- | --------- | -------------------------------------------------------------------------------------------------------------- |
| AKEY-01     | 28-01, 28-02, 28-03 | User can create/revoke API keys with scopes; raw key shown once; prefix + SHA-256 hash stored; RequireScope enforces scope per endpoint | SATISFIED | `models.py` generate_key(), `controllers.py` POST/DELETE, `auth.py` RequireScope, 17 tests GREEN               |
| AKEY-02     | 28-01, 28-04        | API key requests rate-limited per key via django-ratelimit; X-RateLimit-\* headers returned                                             | SATISFIED | `middleware.py` ApiKeyRateLimitMiddleware with `get_usage(increment=True)`, `_inject_headers()`, 3 tests GREEN |
| AKEY-03     | 28-01, 28-03        | System tracks last_used_at and usage_count, updated on every authenticated request                                                      | SATISFIED | `auth.py` partial UPDATE with `F("usage_count")+1` and `timezone.now()`, 2 tests GREEN                         |

All three requirements marked Complete in REQUIREMENTS.md Phase 28 row. No orphaned requirements found.

---

### Anti-Patterns Found

None detected. Scan of all `apps/api/apps/api_keys/` files produced zero matches for TODO, FIXME, XXX, HACK, placeholder, `return null`, `return {}`, `return []`, or console.log patterns.

---

### Human Verification Required

No items require human verification. All behaviors are covered by passing automated tests.

---

### Commits Verified

All commits from SUMMARYs exist in git log:

| Commit    | Plan         | Description                                                            |
| --------- | ------------ | ---------------------------------------------------------------------- |
| `80315a0` | 28-01 Task 1 | test: create test module RED trigger and conftest fixtures             |
| `f0cec20` | 28-01 Task 2 | test: add RED test stubs for AKEY-01, AKEY-02, AKEY-03 requirements    |
| `1b407b4` | 28-02 Task 1 | feat: create apps/api_keys app with APIKey model and migration         |
| `d83e44c` | 28-02 Task 2 | feat: register api*keys in INSTALLED_APPS and add API_KEY*\* settings  |
| `8823e15` | 28-03 Task 1 | feat: implement ApiKeyAuth backend and RequireScope permission class   |
| `de09abd` | 28-03 Task 2 | feat: implement schemas, service, and controller for API key lifecycle |
| `94667f7` | 28-04 Task 1 | feat: implement ApiKeyRateLimitMiddleware with X-RateLimit-\* headers  |

---

### Notable Observations

**manage.py check warnings:** `manage.py check` reports 3 warnings — all are pre-existing `django-allauth` deprecations (`ACCOUNT_AUTHENTICATION_METHOD`, `ACCOUNT_EMAIL_REQUIRED`, `ACCOUNT_USERNAME_REQUIRED`). Zero `api_keys.*` warnings, confirming the `check_api_key_scopes` validator registers cleanly and the default `API_KEY_SCOPES` setting satisfies it.

**Deprecation warnings in tests:** 14 `DeprecationWarning` instances from `ninja_extra.operation` (`get_api_controller() is deprecated`) appear during the controller test run. These are library-internal deprecations from `django-ninja-extra` and are not caused by phase 28 code.

**Security decisions confirmed in code:**

- `hmac.compare_digest` used (not `==`) for timing-safe comparison — confirmed in `auth.py` line 37
- `select_related("user")` prevents N+1 on auth lookup — confirmed in `auth.py` line 32
- Raw key never persisted: `APIKey` model has no `raw_key` field, only `key_hash` — confirmed in `models.py`
- `secrets.token_hex(32)` for 256-bit CSPRNG entropy — confirmed in `models.py` line 49

---

## Summary

Phase 28 fully achieves its goal. All 30 tests pass GREEN across 5 test modules. All three requirements (AKEY-01, AKEY-02, AKEY-03) are satisfied with substantive implementations — no stubs, no orphaned artifacts, no broken wiring. The security-critical path (SHA-256 hash storage, HMAC comparison, raw key shown once) is correctly implemented and verified by both tests and code inspection.

---

_Verified: 2026-03-13T14:00:00Z_
_Verifier: Claude (gsd-verifier)_
