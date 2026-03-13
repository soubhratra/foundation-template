---
phase: 29-audit-logging
plan: "02"
subsystem: audit
tags: [pghistory, pgtrigger, audit-logging, django-middleware, migrations, b2b]
dependency_graph:
  requires: [29-01]
  provides: [audit-infrastructure, event-tables, audit-context-middleware]
  affects: [apps/orgs, apps/api_keys, apps/webhooks, apps/audit]
tech_stack:
  added: [django-pghistory==3.9.2, django-pgtrigger==4.17.0]
  patterns: [pghistory.track decorator, HistoryMiddleware subclass, no-op context manager pattern]
key_files:
  created:
    - apps/api/apps/audit/apps.py
    - apps/api/apps/audit/context.py
    - apps/api/apps/audit/middleware.py
    - apps/api/apps/orgs/migrations/0002_membershipevent_organizationevent_and_more.py
    - apps/api/apps/api_keys/migrations/0002_apikeyevent_apikey_api_key_created_insert_and_more.py
    - apps/api/apps/webhooks/migrations/0002_webhookendpointevent_and_more.py
  modified:
    - apps/api/config/settings/base.py
    - apps/api/apps/orgs/models.py
    - apps/api/apps/api_keys/models.py
    - apps/api/apps/webhooks/models.py
    - apps/api/tests/audit/test_models.py
    - apps/api/tests/audit/test_context.py
    - apps/api/tests/audit/test_middleware.py
    - apps/api/tests/audit/conftest.py
decisions:
  - "django-pghistory 3.9.2 installs django-pgtrigger 4.17.0 as transitive dep — no separate pgtrigger install needed"
  - "pgtrigger hash= fields in migrations are SHA-1 checksums of trigger SQL — use pragma allowlist secret (not secrets.baseline) since migrations are excluded from ruff"
  - "AuditContextMiddleware.get_context() uses spec=['user', 'path'] mock in test to prevent MagicMock auto-creating .org attribute"
  - "OrganizationEvent/MembershipEvent live in orgs app_label; APIKeyEvent in api_keys; WebhookEndpointEvent in webhooks — directly importable from source model modules"
metrics:
  duration_seconds: 844
  completed_date: "2026-03-13"
  tasks_completed: 2
  files_changed: 14
---

# Phase 29 Plan 02: Install pghistory Infrastructure and Apply Track Decorators Summary

Installed django-pghistory 3.9.2, created apps/audit/ (apps.py, context.py, middleware.py), applied @pghistory.track() to all four B2B models, generated and applied migrations creating four event tables with nine PostgreSQL triggers, and verified all 8 AUDIT-01 tests pass GREEN.

## Tasks Completed

| Task | Description                                            | Commit  | Status |
| ---- | ------------------------------------------------------ | ------- | ------ |
| 1    | Install django-pghistory and create apps/audit/ app    | 76552e9 | DONE   |
| 2    | Apply @pghistory.track() decorators and run migrations | bd0bb3a | DONE   |

## Artifacts Delivered

### apps/audit/apps.py

Standard AppConfig with `label = "audit"` and `verbose_name = "Audit"`.

### apps/audit/context.py

`audit_context(user_id, org_id)` context manager. When pghistory is in INSTALLED_APPS, wraps `pghistory.context(user=user_id, org_id=str(org_id))`. When pghistory is absent, degrades to `nullcontext()` no-op. Uses lazy import to avoid circular dependency at startup.

### apps/audit/middleware.py

`AuditContextMiddleware` subclasses `pghistory.middleware.HistoryMiddleware`. Overrides `get_context(request)` to add `org_id = str(request.org.id)` when `request.org` is set. Omits org_id safely for requests with no org context.

### settings/base.py INSTALLED_APPS (inside B2B_START/B2B_END)

```python
"pghistory",  # B2B MODULE — pghistory Context model
"pgtrigger",  # B2B MODULE — trigger management
"apps.audit",  # B2B MODULE — audit context + query API
```

### settings/base.py MIDDLEWARE (inside B2B_START/B2B_END)

```python
"apps.audit.middleware.AuditContextMiddleware",  # B2B MODULE — audit context
```

### @pghistory.track() decorators applied

| Model           | App      | Events                                                                       | Excluded fields                  |
| --------------- | -------- | ---------------------------------------------------------------------------- | -------------------------------- |
| Organization    | orgs     | org.created, org.updated, org.deleted                                        | updated_at                       |
| Membership      | orgs     | membership.created, membership.updated, membership.deleted                   | updated_at                       |
| APIKey          | api_keys | api_key.created, api_key.updated, api_key.deleted                            | last_used_at, usage_count        |
| WebhookEndpoint | webhooks | webhook_endpoint.created, webhook_endpoint.updated, webhook_endpoint.deleted | updated_at, consecutive_failures |

## Event Model App Labels

Verified from migration files after makemigrations:

| Model class          | App label | across() string                 | Direct import                                           |
| -------------------- | --------- | ------------------------------- | ------------------------------------------------------- |
| OrganizationEvent    | orgs      | "orgs.OrganizationEvent"        | `from apps.orgs.models import OrganizationEvent`        |
| MembershipEvent      | orgs      | "orgs.MembershipEvent"          | `from apps.orgs.models import MembershipEvent`          |
| APIKeyEvent          | api_keys  | "api_keys.APIKeyEvent"          | `from apps.api_keys.models import APIKeyEvent`          |
| WebhookEndpointEvent | webhooks  | "webhooks.WebhookEndpointEvent" | `from apps.webhooks.models import WebhookEndpointEvent` |

Note: `Organization.history` attribute does NOT exist — pghistory 3.9.2 does not attach a `.history` accessor. Use direct imports from the source model module instead.

## Test Results

```
tests/audit/test_context.py::test_audit_context_noop          PASSED
tests/audit/test_middleware.py::test_middleware_adds_org_id   PASSED
tests/audit/test_middleware.py::test_middleware_null_org_id   PASSED
tests/audit/test_models.py::test_org_insert_event             PASSED
tests/audit/test_models.py::test_org_delete_event             PASSED
tests/audit/test_models.py::test_membership_update_event      PASSED
tests/audit/test_models.py::test_apikey_insert_event          PASSED
tests/audit/test_models.py::test_webhook_endpoint_insert_event PASSED

8 passed in 9.64s
```

Existing test suite (excluding plan 29-03 stubs and pre-existing billing errors): 199 passed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed audit conftest field name mismatches**

- **Found during:** Task 2 (when implementing test_models.py)
- **Issue:** `conftest.py` used `hashed_key=hashed` (wrong field name) and `hashed_secret=hashed, display_secret=display_secret` (wrong field names). The actual model fields are `key_hash` (APIKey) and `signing_key`/`secret_hash` (WebhookEndpoint).
- **Fix:** Updated conftest.py to use correct field names: `key_hash=hashed` and `signing_key=signing_key, secret_hash=secret_hash`
- **Files modified:** `apps/api/tests/audit/conftest.py`
- **Commit:** bd0bb3a

**2. [Rule 1 - Bug] Fixed test_middleware_null_org_id mock spec**

- **Found during:** Task 1 test execution
- **Issue:** `MagicMock(spec=[])` prevented `super().get_context()` from accessing `request.path` (pghistory HistoryMiddleware reads `request.path`). Test failed with `AttributeError: Mock object has no attribute 'path'`
- **Fix:** Changed to `MagicMock(spec=["user", "path"])` to expose only the needed attributes without exposing `org`
- **Files modified:** `apps/api/tests/audit/test_middleware.py`
- **Commit:** 76552e9

**3. [Rule 2 - False positive secrets] Added pragma allowlist secret to migration hash= fields**

- **Found during:** Task 2 pre-commit hook
- **Issue:** detect-secrets flagged pgtrigger `hash=` fields (SHA-1 trigger body checksums) as "Hex High Entropy String" secrets in 3 migration files
- **Fix:** Added `# pragma: allowlist secret` inline comments on all 9 `hash=` lines (3 per migration file). Migration files are excluded from ruff, so no line-length issues.
- **Files modified:** 3 migration files
- **Commit:** bd0bb3a

**4. [Rule 2 - False positive secrets] Fixed pre-existing detect-secrets false positives in settings/base.py**

- **Found during:** Task 1 pre-commit hook
- **Issue:** Pre-existing false positives: default DATABASE_URL and SECRET_KEY insecure placeholder string
- **Fix:** Added `# noqa: E501  # pragma: allowlist secret` to DATABASE_URL line, `# pragma: allowlist secret` to SECRET_KEY check line
- **Files modified:** `apps/api/config/settings/base.py`
- **Commit:** 76552e9

## Self-Check

Verified files exist:

- `/Users/soubhratra/workspace/foundation-template/apps/api/apps/audit/apps.py` — FOUND
- `/Users/soubhratra/workspace/foundation-template/apps/api/apps/audit/context.py` — FOUND
- `/Users/soubhratra/workspace/foundation-template/apps/api/apps/audit/middleware.py` — FOUND
- `/Users/soubhratra/workspace/foundation-template/apps/api/apps/orgs/migrations/0002_membershipevent_organizationevent_and_more.py` — FOUND
- `/Users/soubhratra/workspace/foundation-template/apps/api/apps/api_keys/migrations/0002_apikeyevent_apikey_api_key_created_insert_and_more.py` — FOUND
- `/Users/soubhratra/workspace/foundation-template/apps/api/apps/webhooks/migrations/0002_webhookendpointevent_and_more.py` — FOUND

Verified commits exist:

- `76552e9` — Task 1: feat(29-02): install django-pghistory and create apps/audit/ app — FOUND
- `bd0bb3a` — Task 2: feat(29-02): apply @pghistory.track() decorators and run migrations — FOUND

## Self-Check: PASSED
