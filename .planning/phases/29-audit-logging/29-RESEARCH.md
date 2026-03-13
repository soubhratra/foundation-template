# Phase 29: Audit Logging - Research

**Researched:** 2026-03-13 (updated from prior draft with CONTEXT.md decisions)
**Domain:** django-pghistory, PostgreSQL triggers, audit context middleware, cursor pagination
**Confidence:** HIGH

## Summary

Phase 29 implements automatic audit logging for four B2B models (`Organization`, `Membership`, `APIKey`, `WebhookEndpoint`) using `django-pghistory` 3.9.2. The library installs PostgreSQL trigger functions that fire on INSERT/UPDATE/DELETE and write row snapshots to auto-generated event tables — no per-operation logging call is required in application code. This is the only Django audit library that captures bulk ORM (`queryset.update()`) and raw SQL, which is why it was chosen (locked in STATE.md).

The implementation splits into three concerns. First, **infrastructure**: add `@pghistory.track()` decorators to the four models with domain-prefixed event labels (`org.created`, `membership.deleted`, etc.), install `pghistory`/`pgtrigger` in `INSTALLED_APPS`, and run `makemigrations`. Second, **context binding**: a custom `AuditContextMiddleware` subclasses `pghistory.middleware.HistoryMiddleware`, adding `org_id` (from `request.org` if set) and a placeholder `impersonator=None` slot (populated by Phase 30). Celery tasks use the thin `audit_context(user_id, org_id)` wrapper in `apps/audit/context.py`. Third, **query API**: `AuditLogController` at `GET /api/v1/org/{slug}/audit-log` queries across all four event tables via `pghistory.models.MiddlewareEvents` with a custom `OrgAuditEvents` proxy that surfaces `org_id` as a `ProxyField`; cursor pagination is implemented manually using a `(pgh_created_at, pgh_id)` compound key.

A critical constraint is **impersonation data isolation**: the `impersonator` key is stored in `pgh_context.metadata` but `AuditEntryOut` never serialises it — org admins cannot see it even after Phase 30 ships. The field is stored; it is not exposed.

**Primary recommendation:** Use `@pghistory.track()` with explicit InsertEvent/UpdateEvent/DeleteEvent labels and `exclude=["updated_at"]`. Subclass `HistoryMiddleware` for request context. Use `OrgAuditEvents(MiddlewareEvents)` proxy with `ProxyField("pgh_context__org_id")` for org-scoped queries. Implement cursor pagination manually (no existing helper in codebase).

---

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions

**Audit entry response schema**

- Summary-only response — no raw before/after diffs in `AuditEntryOut`; pghistory stores full row snapshots internally but Phase 29 does not expose them
- Actor fields: both `actor_id` (UUID) and `actor_email` in every entry; both become `null` if the actor was later deleted — no FK constraint on audit entries referencing users
- Object identification: `model_name` (e.g. `"Organization"`) + `object_id` (UUID/PK) — generic across all 4 tracked models; no `object_repr` in Phase 29
- Timestamp: ISO 8601 UTC string
- Impersonator field: stored in pghistory context JSON but excluded from `AuditEntryOut`; never serialised for org-level callers; staff-only (future phase)
- Minimum `AuditEntryOut` fields: `id`, `timestamp`, `action` (e.g. `org.updated`), `model_name`, `object_id`, `actor_id`, `actor_email`, `url`

**Org context resolution**

- URL-first, then null: `AuditContextMiddleware` extracts `org_id` from the URL if `request.org` is set; for non-org URLs `org_id` is `null` in context
- Unauthenticated requests: both `user_id` and `org_id` are `null` in context; triggers still fire, context is anonymous
- Middleware placement: after `SessionMiddleware` and `AuthenticationMiddleware`; before any view-level middleware

**Task / Celery context API**

- API: `audit_context(user_id, org_id)` — a context manager in `apps/audit/context.py`
- Graceful degradation: `audit_context()` is a no-op context manager when `pghistory` is not in `INSTALLED_APPS`

**Filtering interface**

- Query params (all optional, combinable): `actor_id` (UUID exact match), `from` (ISO 8601 datetime), `to` (ISO 8601 datetime), `action` (exact string match, e.g. `org.updated`)
- Pagination: cursor-based; default `page_size=50`, max 200
- Default sort: newest first (`ORDER BY timestamp DESC`)

### Claude's Discretion

- Whether to use `pghistory.models.MiddlewareEvents` or a custom proxy model — recommend `MiddlewareEvents` subclass with `ProxyField` for `org_id`
- Exact cursor implementation — implement per-field cursor on `(pgh_created_at, pgh_id)` since no existing helper exists
- DB index strategy on event tables for org-scoped + timestamp queries
- Exact `AuditConfig` app label and `apps.py` content
- Whether to expose `url` in `AuditEntryOut` — research recommends YES (already captured by HistoryMiddleware; useful for debugging)

### Deferred Ideas (OUT OF SCOPE)

- AUDIT-F01: External audit log shipping (Splunk, Datadog Logs)
- Per-field diff exposure (`before`/`after` JSON in API)
- Audit logging for `Invitation` model
- `object_repr` in `AuditEntryOut`
- Action prefix matching (e.g. `?action=org.` matches all org events)
  </user_constraints>

---

<phase_requirements>

## Phase Requirements

| ID       | Description                                                                                                                                                                      | Research Support                                                                                                                                                                                             |
| -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| AUDIT-01 | System records changes to `Organization`, `Membership`, `APIKey`, `WebhookEndpoint` via pghistory triggers; `AuditContextMiddleware` attaches user and org context automatically | `@pghistory.track(InsertEvent, UpdateEvent, DeleteEvent)` on all 4 models; `AuditContextMiddleware` subclasses `HistoryMiddleware.get_context()` to add `org_id`; `audit_context()` wrapper for Celery tasks |
| AUDIT-02 | Org owner and admins can query paginated audit log filtered by actor/date/action (`GET /api/v1/org/{slug}/audit-log`); impersonation entries not exposed to org admins           | `OrgAuditEvents` proxy with `org_id` ProxyField; cursor pagination on `(pgh_created_at, pgh_id)`; `[IsAuthenticated, IsOrgMember, IsOrgAdmin]` permission gate; `AuditEntryOut` excludes `impersonator`      |

</phase_requirements>

---

## Standard Stack

### Core

| Library          | Version                              | Purpose                                       | Why Standard                                                                                  |
| ---------------- | ------------------------------------ | --------------------------------------------- | --------------------------------------------------------------------------------------------- |
| django-pghistory | 3.9.2 (Feb 2026)                     | PostgreSQL-trigger-based model history        | Locked project decision; captures bulk ORM + raw SQL; no per-operation logging calls required |
| pgtrigger        | (transitive dep of django-pghistory) | Django abstraction over PG trigger management | Auto-installed; pghistory triggers are pgtrigger-managed                                      |

### Supporting

| Library                                | Version  | Purpose                                                       | When to Use                                                                    |
| -------------------------------------- | -------- | ------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| pghistory.middleware.HistoryMiddleware | built-in | Base middleware that captures user + url in pgh_context       | Subclass with `get_context()` override — never use bare                        |
| pghistory.models.MiddlewareEvents      | built-in | Events proxy with pre-added `user` and `url` ProxyFields      | Use as the base class for `OrgAuditEvents`; already has user/url               |
| pghistory.models.Events                | built-in | Raw CTE UNION ALL proxy across all event tables               | Used internally by MiddlewareEvents; use `across()` and `references()` methods |
| pghistory.ProxyField                   | built-in | Surfaces pgh_context metadata as typed queryset filter fields | Required to add `org_id` filter capability on `OrgAuditEvents`                 |

### Alternatives Considered

| Instead of                  | Could Use                 | Tradeoff                                                                                      |
| --------------------------- | ------------------------- | --------------------------------------------------------------------------------------------- |
| django-pghistory            | django-auditlog (signals) | Signal-based misses bulk ORM + raw SQL — rejected at project level                            |
| django-pghistory            | django-pgaudit            | 404 on PyPI — does not exist                                                                  |
| MiddlewareEvents ProxyField | Custom AuditEntry model   | Custom model duplicates data or requires 4-table UNION manually; Events CTE already does this |

**Installation:**

```bash
uv add django-pghistory
```

Both `pghistory` and `pgtrigger` must also be added to `INSTALLED_APPS`. Running `migrate` after this creates the `pghistory_context` table.

---

## Architecture Patterns

### Recommended Project Structure

```
apps/api/apps/audit/
├── __init__.py
├── apps.py              # AuditConfig — no ready() hook needed in Phase 29
├── context.py           # audit_context() context manager + no-op fallback
├── middleware.py        # AuditContextMiddleware (subclasses HistoryMiddleware)
├── schemas.py           # AuditEntryOut, AuditLogQueryParams, CursorPageOut
├── controllers.py       # AuditLogController — GET /api/v1/org/{slug}/audit-log
└── selectors.py         # build_audit_queryset(), cursor encode/decode
tests/audit/
├── __init__.py          # RED trigger: module-level import from apps.audit.context
├── conftest.py          # lazy imports in fixtures; org + admin user fixtures
├── test_models.py       # AUDIT-01 trigger coverage (events written on save/delete)
├── test_middleware.py   # AuditContextMiddleware.get_context() tests
├── test_context.py      # audit_context() no-op test
├── test_controllers.py  # AUDIT-02 endpoint tests
└── test_schemas.py      # AuditEntryOut field exclusion test
```

No `models.py` in `apps/audit/` — the app owns no DB models. All event tables are auto-generated by the `@pghistory.track()` decorators on the source models.

### Pattern 1: Model Decorators with Domain-Prefixed Labels

Apply `@pghistory.track()` in-place to all four source models. Labels must be chosen now — changing them later invalidates existing event rows in the audit table. Use domain-prefixed dot-notation matching the CONTEXT.md action format.

```python
# Source: django-pghistory readthedocs event_tracking
# apps/orgs/models.py
import pghistory

@pghistory.track(
    pghistory.InsertEvent("org.created"),
    pghistory.UpdateEvent("org.updated"),
    pghistory.DeleteEvent("org.deleted"),
    exclude=["updated_at"],  # suppress auto_now noise
)
class Organization(models.Model):
    ...

@pghistory.track(
    pghistory.InsertEvent("membership.created"),
    pghistory.UpdateEvent("membership.updated"),
    pghistory.DeleteEvent("membership.deleted"),
    exclude=["updated_at"],
)
class Membership(models.Model):
    ...
```

```python
# apps/api_keys/models.py
@pghistory.track(
    pghistory.InsertEvent("api_key.created"),
    pghistory.UpdateEvent("api_key.updated"),
    pghistory.DeleteEvent("api_key.deleted"),
    exclude=["last_used_at", "usage_count"],  # AKEY-03 fields — update on every auth request
)
class APIKey(models.Model):
    ...
```

```python
# apps/webhooks/models.py
@pghistory.track(
    pghistory.InsertEvent("webhook_endpoint.created"),
    pghistory.UpdateEvent("webhook_endpoint.updated"),
    pghistory.DeleteEvent("webhook_endpoint.deleted"),
    exclude=["updated_at", "consecutive_failures"],  # counter updates on delivery failure
)
class WebhookEndpoint(models.Model):
    ...
```

After decorating, run `python manage.py makemigrations`. Expect new migrations in: `pghistory` (Context model), `pgtrigger` (trigger registry), `apps.orgs` (OrganizationEvent + MembershipEvent tables + triggers), `apps.api_keys` (APIKeyEvent), `apps.webhooks` (WebhookEndpointEvent).

### Pattern 2: AuditContextMiddleware

Subclass `pghistory.middleware.HistoryMiddleware`. The base class automatically captures `user` (authenticated user pk) and `url` (request path) via `pghistory.context()`. Override `get_context()` to merge `org_id` and a Phase-30 placeholder `impersonator=None`.

```python
# Source: django-pghistory readthedocs context/
# apps/audit/middleware.py
import pghistory.middleware


class AuditContextMiddleware(pghistory.middleware.HistoryMiddleware):
    """Wraps every HTTP request in a pghistory context.

    Built-in HistoryMiddleware captures: user (pk), url.
    This subclass adds: org_id (from request.org, set by IsOrgMember/IsOrgAdmin).

    impersonator is injected by Phase 30 (django-hijack signal); leave as None here.
    It is stored in pgh_context.metadata JSON but never serialised in AuditEntryOut.
    """

    def get_context(self, request):
        ctx = super().get_context(request)
        org = getattr(request, "org", None)
        if org is not None:
            ctx["org_id"] = str(org.id)
        return ctx
```

**Placement in `settings/base.py`** (inside B2B_START/B2B_END block):

```python
# B2B_START
"apps.api_keys.middleware.ApiKeyRateLimitMiddleware",
"apps.audit.middleware.AuditContextMiddleware",  # B2B MODULE — audit context
# B2B_END
```

Must appear after `AuthenticationMiddleware` — `request.user` must already be resolved.

### Pattern 3: audit_context() for Celery Tasks

The `audit_context()` context manager is a thin wrapper over `pghistory.context()` that also supports `org_id`. It degrades to a no-op when `pghistory` is absent (B2B-removed projects).

```python
# apps/audit/context.py
from contextlib import contextmanager, nullcontext


@contextmanager
def audit_context(user_id=None, org_id=None):
    """Context manager for attaching audit context in Celery tasks.

    Wraps pghistory.context() with org_id support. Degrades to a no-op
    when pghistory is not in INSTALLED_APPS so B2B-removed projects compile
    cleanly without conditional imports.

    Usage:
        from apps.audit.context import audit_context

        @app.task
        def provision_org(user_id, org_id):
            with audit_context(user_id=user_id, org_id=org_id):
                org.is_active = True
                org.save()
    """
    from django.apps import apps as django_apps
    if not django_apps.is_installed("pghistory"):
        with nullcontext():
            yield
        return

    import pghistory
    org_id_str = str(org_id) if org_id is not None else None
    with pghistory.context(user=user_id, org_id=org_id_str):
        yield
```

### Pattern 4: OrgAuditEvents Proxy for Cross-Model Queries

`pghistory.models.MiddlewareEvents` already surfaces `user` and `url` as `ProxyField`s. Subclass it to add `org_id`:

```python
# Source: django-pghistory readthedocs aggregating_events
# apps/audit/selectors.py (or a module-level class in models.py if preferred)
import pghistory
from pghistory import models as pgh_models
from django.db import models as dj_models


class OrgAuditEvents(pgh_models.MiddlewareEvents):
    """Unified event view across all 4 B2B models with org_id surfaced."""
    org_id = pghistory.ProxyField("pgh_context__org_id", dj_models.TextField(null=True))

    class Meta:
        proxy = True
```

**Querying:**

```python
# Source: django-pghistory readthedocs aggregating_events
from apps.audit.selectors import OrgAuditEvents

# NOTE: verify these model label strings after makemigrations
events = (
    OrgAuditEvents.objects
    .across(
        "orgs.OrganizationEvent",
        "orgs.MembershipEvent",
        "api_keys.APIKeyEvent",
        "webhooks.WebhookEndpointEvent",
    )
    .filter(org_id=str(org.id))
    .order_by("-pgh_created_at", "-pgh_id")
)
```

**Critical note on APIKey:** `APIKey` has a `user` FK only, not an `org` FK. `references(org)` will NOT catch APIKey events. The `across()` approach above handles this — filter `org_id` from context rather than object FK.

### Pattern 5: actor_email Resolution (Bulk Lookup, Not Per-Row)

The `AuditEntryOut` requires `actor_email`. pghistory stores only `user` pk in context. Resolve emails in bulk before building the response to avoid N+1 queries (the `nplusone` guard in conftest will catch violations):

```python
# apps/audit/selectors.py
from django.contrib.auth import get_user_model

User = get_user_model()

def enrich_with_actor_emails(events: list) -> dict[int, str]:
    """Return {user_pk: email} for all actors in the event list."""
    actor_pks = {
        e.pgh_context.get("user")
        for e in events
        if e.pgh_context and e.pgh_context.get("user")
    }
    if not actor_pks:
        return {}
    return dict(
        User.objects.filter(pk__in=actor_pks).values_list("pk", "email")
    )
```

### Pattern 6: Cursor Pagination on (pgh_created_at, pgh_id)

No cursor pagination helper exists in the codebase (Phase 27 uses offset pagination). Implement in `apps/audit/selectors.py`:

```python
import base64
from datetime import datetime

def encode_cursor(ts: datetime, pgh_id: int) -> str:
    raw = f"{ts.isoformat()}:{pgh_id}"
    return base64.urlsafe_b64encode(raw.encode()).decode()

def decode_cursor(cursor: str) -> tuple[datetime, int] | None:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode()).decode()
        ts_str, id_str = raw.rsplit(":", 1)
        return datetime.fromisoformat(ts_str), int(id_str)
    except Exception:
        return None
```

**Newest-first keyset query:**

```python
# WHERE (pgh_created_at, pgh_id) < (cursor_ts, cursor_id)
if cursor_decoded:
    cursor_ts, cursor_id = cursor_decoded
    qs = qs.filter(
        pgh_created_at__lt=cursor_ts
    ) | qs.filter(
        pgh_created_at=cursor_ts, pgh_id__lt=cursor_id
    )
```

Response shape (consistent with Phase 27 `{"items": [...], "count": N}` dict response):

```python
{"items": [...], "next_cursor": "..." or None, "page_size": 50}
```

### INSTALLED_APPS and MIDDLEWARE additions

```python
# config/settings/base.py
INSTALLED_APPS = [
    ...
    # B2B_START
    "apps.orgs",
    "apps.webhooks",
    "apps.api_keys",
    "pghistory",     # B2B MODULE — pghistory Context model
    "pgtrigger",     # B2B MODULE — trigger management
    "apps.audit",    # B2B MODULE — audit context + query API
    # B2B_END
    ...
]

MIDDLEWARE = [
    ...
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "apps.core.middleware.RequestContextMiddleware",
    "apps.core.middleware.ObservabilityMiddleware",
    "apps.core.middleware.AuthRateLimitMiddleware",
    # B2B_START
    "apps.api_keys.middleware.ApiKeyRateLimitMiddleware",
    "apps.audit.middleware.AuditContextMiddleware",  # B2B MODULE
    # B2B_END
    ...
]
```

### Anti-Patterns to Avoid

- **`from __future__ import annotations` in controllers/schemas**: Phase 27 note — deferred type eval breaks Pydantic `QueryParams.model_rebuild()` at runtime. Never add this import to controller or schema files.
- **`@pghistory.track()` on Invitation, WebhookDelivery, WebhookDeliveryAttempt**: Not in AUDIT-01 requirements; high-write low-audit-value models.
- **Using `references(org)` as the only query method**: Misses `APIKey` events (no direct org FK). Must use `across()` with explicit event model labels.
- **Using `pgh_context.metadata` via FK join without ProxyField**: Use `ProxyField("pgh_context__org_id")` to expose metadata fields as filterable queryset attributes on the proxy model.
- **`@paginate` decorator on the controller**: Phase 27 confirmed it is incompatible with ninja_extra controller methods. Use manual dict response.
- **Bare `pghistory.middleware.HistoryMiddleware`**: Does not add `org_id`. Always use the custom subclass.

---

## Don't Hand-Roll

| Problem                      | Don't Build                                  | Use Instead                                 | Why                                                                                   |
| ---------------------------- | -------------------------------------------- | ------------------------------------------- | ------------------------------------------------------------------------------------- |
| INSERT/UPDATE/DELETE capture | Custom signals or post_save hooks            | `@pghistory.track()` triggers               | Signals miss `queryset.update()` and raw SQL; triggers capture all writes at DB level |
| Before/after diff            | Manual field comparison                      | `pgh_diff` on Events CTE                    | pghistory computes diffs via Postgres window functions; stored automatically          |
| Cross-model UNION query      | Manual `UNION ALL` SQL                       | `Events.objects.across(...)`                | CTE already handles UNION ALL; `ProxyField` surfaces metadata as filter fields        |
| Context grouping             | `threading.local()` / `contextvars` manually | `pghistory.context()`                       | pghistory uses `contextvars` internally; context manager is safe across async         |
| Trigger installation SQL     | Custom migration `RunSQL`                    | `makemigrations` after `@pghistory.track()` | pghistory generates correct trigger SQL with proper ON CONFLICT and cascade behaviour |

**Key insight:** The core value is triggers — they fire unconditionally at the database level. Any hand-rolled solution will have a gap for bulk operations.

---

## Common Pitfalls

### Pitfall 1: auto_now / auto_now_add Fields Create Audit Noise

**What goes wrong:** Every `model.save()` updates `updated_at` (auto_now=True), generating an `UpdateEvent` even when no user-facing field changed. The audit log fills with noise.
**Why it happens:** PostgreSQL triggers fire on every row write; they do not distinguish application-significant changes from timestamp-only changes.
**How to avoid:** `exclude=["updated_at"]` on `Organization`, `Membership`, `WebhookEndpoint`. For `APIKey`, also exclude `last_used_at` and `usage_count` (updated on every API key authentication per AKEY-03).
**Warning signs:** High event table row counts; events with only `pgh_diff: {"updated_at": [...]}`.

### Pitfall 2: Actor Email Requires Bulk User Lookup

**What goes wrong:** Fetching `actor_email` inside a serialization loop triggers the `nplusone` guard in `conftest.py`.
**Why it happens:** pghistory only stores user pk in context. Email must be resolved via a User lookup. The global `_nplusone_guard` autouse fixture raises `NPlusOneError` on lazy per-row queries.
**How to avoid:** Use a single `User.objects.filter(pk__in=unique_actor_pks).values_list("pk", "email")` before building the response list. Cache the result as a dict.
**Warning signs:** `NPlusOneError` in `test_controllers.py` audit log response tests.

### Pitfall 3: APIKey Events Missing from Org Audit Log

**What goes wrong:** `Events.objects.references(org)` returns no APIKey events.
**Why it happens:** `references()` only traverses one FK hop. `APIKey` has a `user` FK, not an `org` FK — it is not directly connected to `Organization`.
**How to avoid:** Use `across()` with explicit event model label strings for all four models rather than `references()`. Context-based `org_id` filter handles APIKey scoping since `audit_context()` stores `org_id` when the request hits an org-scoped endpoint.
**Warning signs:** API key create/revoke events absent from org audit log in controller tests.

### Pitfall 4: pgh_context is None Outside HTTP Requests

**What goes wrong:** Events created in tests, migrations, or management commands have `pgh_context=None`. Filtering on `ProxyField("pgh_context__org_id")` returns zero results.
**Why it happens:** `AuditContextMiddleware` only runs in HTTP request/response cycles.
**How to avoid:** In integration tests that verify audit log content, wrap model mutations with `pghistory.context(user=user.pk, org_id=str(org.id))` or use `audit_context()`. Always guard: `metadata = event.pgh_context or {}`.
**Warning signs:** `OrgAuditEvents.objects.filter(org_id=...).count() == 0` even after saving tracked models.

### Pitfall 5: Event Model App Label Strings Must Match After makemigrations

**What goes wrong:** `Events.objects.across("orgs.OrganizationEvent")` raises `LookupError` if the auto-generated model name differs.
**Why it happens:** pghistory names the event model `{ClassName}Event` in the same app as the tracked model. Must verify after generating migrations.
**How to avoid:** After running `makemigrations`, open the generated migration and confirm the model class names. Expected: `OrganizationEvent`, `MembershipEvent`, `APIKeyEvent`, `WebhookEndpointEvent`. Adjust `across()` calls if they differ.
**Warning signs:** `LookupError` or `ValueError` when calling `.across()` in tests.

### Pitfall 6: Cursor Stability Requires Composite Key

**What goes wrong:** Cursor based only on `pgh_created_at` breaks when multiple events share the same timestamp (batch operations, test fixtures that create events in tight loops).
**Why it happens:** `pgh_created_at` has microsecond resolution but trigger-level events in the same DB transaction can share identical timestamps.
**How to avoid:** Always use `(pgh_created_at, pgh_id)` as the compound cursor key. `pgh_id` is an auto-increment integer and is unique within each event table.
**Warning signs:** Duplicate or skipped entries in paginated responses during tests that create multiple events rapidly.

### Pitfall 7: ruff Migration Line Length

**What goes wrong:** Ruff lint fails on auto-generated pghistory migration files containing long trigger SQL strings.
**Why it happens:** pghistory embeds trigger SQL as Python strings; these exceed the 88-char line length limit.
**How to avoid:** The project already has a ruff migration exclusion in `ruff.toml` (added Phase 27). Verify it covers `apps/*/migrations/*.py` patterns.

### Pitfall 8: B2B_START/B2B_END Markers Must Wrap All Additions

**What goes wrong:** `manage.py check` fails after B2B removal if `apps.audit` or `pghistory`/`pgtrigger` remain in `INSTALLED_APPS`.
**Why it happens:** The scaffolder removes code between the B2B markers. Additions outside markers survive removal as orphan references.
**How to avoid:** Every addition to `INSTALLED_APPS`, `MIDDLEWARE`, and settings constants must be inside `# B2B_START / # B2B_END`. All code in `apps/audit/` is inherently B2B-only.

---

## Code Examples

Verified patterns from official sources:

### Minimum AuditEntryOut Schema

```python
# apps/audit/schemas.py
# Note: no `from __future__ import annotations` — breaks Pydantic in ninja_extra
from datetime import datetime
from uuid import UUID
from ninja import Schema


class AuditEntryOut(Schema):
    id: int                    # pgh_id — auto-increment within each event table
    timestamp: datetime        # pgh_created_at (ISO 8601 UTC)
    action: str                # pgh_label e.g. "org.updated"
    model_name: str            # e.g. "Organization"
    object_id: str             # pgh_obj_id as string
    actor_id: str | None       # user pk from pgh_context.metadata["user"]
    actor_email: str | None    # resolved via bulk User lookup
    url: str | None            # from pgh_context.metadata["url"]
    # impersonator intentionally omitted — staff-only; populated in Phase 30


class CursorPageOut(Schema):
    items: list[AuditEntryOut]
    next_cursor: str | None
    page_size: int
```

### Full HistoryMiddleware Subclass

```python
# Source: django-pghistory readthedocs context/
# apps/audit/middleware.py
import pghistory.middleware


class AuditContextMiddleware(pghistory.middleware.HistoryMiddleware):
    """Wraps every HTTP request in pghistory context with org_id added.

    Base HistoryMiddleware captures: user (pk), url.
    This adds: org_id (from request.org if set by org-scoped permission classes).
    impersonator: populated by Phase 30 django-hijack signal; None here.
    """

    def get_context(self, request):
        ctx = super().get_context(request)
        org = getattr(request, "org", None)
        if org is not None:
            ctx["org_id"] = str(org.id)
        return ctx
```

### audit_context() No-Op Pattern

```python
# apps/audit/context.py
from contextlib import contextmanager, nullcontext


@contextmanager
def audit_context(user_id=None, org_id=None):
    from django.apps import apps as django_apps
    if not django_apps.is_installed("pghistory"):
        with nullcontext():
            yield
        return
    import pghistory
    with pghistory.context(
        user=user_id,
        org_id=str(org_id) if org_id is not None else None,
    ):
        yield
```

### OrgAuditEvents with org_id ProxyField

```python
# Source: django-pghistory readthedocs aggregating_events
import pghistory
from pghistory import models as pgh_models
from django.db import models as dj_models


class OrgAuditEvents(pgh_models.MiddlewareEvents):
    org_id = pghistory.ProxyField("pgh_context__org_id", dj_models.TextField(null=True))

    class Meta:
        proxy = True
```

### Full get_audit_log_page Selector

```python
# apps/audit/selectors.py
import base64
from datetime import datetime
from django.contrib.auth import get_user_model

User = get_user_model()


def get_audit_log_page(org, actor_id=None, from_ts=None, to_ts=None,
                       action=None, cursor=None, page_size=50):
    qs = (
        OrgAuditEvents.objects
        .across(
            "orgs.OrganizationEvent",
            "orgs.MembershipEvent",
            "api_keys.APIKeyEvent",
            "webhooks.WebhookEndpointEvent",
        )
        .filter(org_id=str(org.id))
        .order_by("-pgh_created_at", "-pgh_id")
    )
    if actor_id:
        qs = qs.filter(user=actor_id)        # ProxyField from MiddlewareEvents
    if action:
        qs = qs.filter(pgh_label=action)
    if from_ts:
        qs = qs.filter(pgh_created_at__gte=from_ts)
    if to_ts:
        qs = qs.filter(pgh_created_at__lte=to_ts)
    if cursor:
        decoded = decode_cursor(cursor)
        if decoded:
            cur_ts, cur_id = decoded
            qs = qs.filter(pgh_created_at__lt=cur_ts) | qs.filter(
                pgh_created_at=cur_ts, pgh_id__lt=cur_id
            )

    page = list(qs[:page_size + 1])
    has_more = len(page) > page_size
    page = page[:page_size]

    actor_pks = {e.pgh_context.get("user") for e in page if e.pgh_context}
    email_map = dict(User.objects.filter(pk__in=actor_pks).values_list("pk", "email"))

    next_cursor = None
    if has_more and page:
        last = page[-1]
        next_cursor = encode_cursor(last.pgh_created_at, last.pgh_id)

    items = [_to_entry_out(e, email_map) for e in page]
    return items, next_cursor
```

---

## State of the Art

| Old Approach                            | Current Approach                                  | When Changed             | Impact                                                           |
| --------------------------------------- | ------------------------------------------------- | ------------------------ | ---------------------------------------------------------------- |
| Signal-based audit (pre_save/post_save) | PostgreSQL trigger-based (@pghistory.track)       | Locked in v1.4 planning  | Captures bulk queryset.update() and raw SQL that signals miss    |
| pghistory.SnapshotEvent                 | pghistory.InsertEvent / UpdateEvent / DeleteEvent | pghistory 3.0            | Explicit event type selection; SnapshotEvent is deprecated       |
| Context via thread locals               | pghistory.context() with contextvars              | pghistory 2.0            | Safe across async and per-request scoped                         |
| AggregateEvent                          | pghistory.models.Events                           | pghistory 3.x            | No model called AggregateEvent exists in current API             |
| Offset pagination                       | Cursor pagination (keyset)                        | Phase 29 design decision | Stable for append-only audit logs; offset breaks under insertion |

**Deprecated / outdated:**

- `pghistory.SnapshotEvent`: Removed in 3.x — use `InsertEvent`/`UpdateEvent`/`DeleteEvent`.
- `django-pgaudit`: 404 on PyPI — does not exist.
- Signal-based `django-auditlog`: Rejected — misses bulk ORM.

---

## Open Questions

1. **Exact auto-generated event model app label strings**
   - What we know: pghistory names event models `{ClassName}Event` in the same app
   - What's unclear: Whether `across("orgs.OrganizationEvent")` uses the correct casing / label
   - Recommendation: Wave 0 task — run `makemigrations`, inspect migration, confirm label strings before writing `across()` calls in selectors

2. **MiddlewareEvents.user ProxyField type vs actor_id filtering**
   - What we know: `MiddlewareEvents` exposes `user` as a `ProxyField`. The context stores `user` as the user pk integer.
   - What's unclear: Whether `qs.filter(user=actor_id)` works correctly when `actor_id` is a UUID string (from the `actor_id` query param defined as UUID in CONTEXT.md) vs an integer pk
   - Recommendation: In the selector, always cast to the correct pk type. User pks in this project are integers (BigAutoField). The `actor_id` query param should be typed `int` not `UUID`.

3. **OrgAuditEvents proxy placement**
   - What we know: Proxy models require `Meta: proxy = True` and a registered base model
   - What's unclear: Whether `OrgAuditEvents` should live in `apps/audit/` or be inline in `selectors.py`
   - Recommendation: Define it at module level in `apps/audit/selectors.py`; it does not need to be in `models.py` since it owns no migrations

---

## Validation Architecture

### Test Framework

| Property           | Value                                                   |
| ------------------ | ------------------------------------------------------- |
| Framework          | pytest 8.x + pytest-django 4.x                          |
| Config file        | `apps/api/pyproject.toml` (`[tool.pytest.ini_options]`) |
| Quick run command  | `cd apps/api && python -m pytest tests/audit/ -x -q`    |
| Full suite command | `cd apps/api && python -m pytest tests/ -x -q`          |

### Phase Requirements → Test Map

| Req ID   | Behavior                                                                 | Test Type   | Automated Command                                                            | File Exists? |
| -------- | ------------------------------------------------------------------------ | ----------- | ---------------------------------------------------------------------------- | ------------ |
| AUDIT-01 | Organization.save() creates OrganizationEvent row                        | integration | `pytest tests/audit/test_models.py::test_org_insert_event -x`                | ❌ Wave 0    |
| AUDIT-01 | Organization.delete() creates delete event with org.deleted label        | integration | `pytest tests/audit/test_models.py::test_org_delete_event -x`                | ❌ Wave 0    |
| AUDIT-01 | Membership update creates event                                          | integration | `pytest tests/audit/test_models.py::test_membership_update_event -x`         | ❌ Wave 0    |
| AUDIT-01 | APIKey create creates api_key.created event                              | integration | `pytest tests/audit/test_models.py::test_apikey_insert_event -x`             | ❌ Wave 0    |
| AUDIT-01 | WebhookEndpoint create creates webhook_endpoint.created event            | integration | `pytest tests/audit/test_models.py::test_webhook_endpoint_insert_event -x`   | ❌ Wave 0    |
| AUDIT-01 | AuditContextMiddleware.get_context() adds org_id when request.org is set | unit        | `pytest tests/audit/test_middleware.py::test_middleware_adds_org_id -x`      | ❌ Wave 0    |
| AUDIT-01 | AuditContextMiddleware.get_context() sets no org_id for non-org request  | unit        | `pytest tests/audit/test_middleware.py::test_middleware_null_org_id -x`      | ❌ Wave 0    |
| AUDIT-01 | audit_context() is a no-op when pghistory not in INSTALLED_APPS          | unit        | `pytest tests/audit/test_context.py::test_audit_context_noop -x`             | ❌ Wave 0    |
| AUDIT-02 | GET /api/v1/org/{slug}/audit-log returns 200 for org admin               | integration | `pytest tests/audit/test_controllers.py::test_audit_log_admin_200 -x`        | ❌ Wave 0    |
| AUDIT-02 | GET /api/v1/org/{slug}/audit-log returns 403 for org member (non-admin)  | integration | `pytest tests/audit/test_controllers.py::test_audit_log_member_403 -x`       | ❌ Wave 0    |
| AUDIT-02 | ?actor_id= filter returns only entries for that actor                    | integration | `pytest tests/audit/test_controllers.py::test_filter_actor_id -x`            | ❌ Wave 0    |
| AUDIT-02 | ?action=org.updated filter returns only org update events                | integration | `pytest tests/audit/test_controllers.py::test_filter_action -x`              | ❌ Wave 0    |
| AUDIT-02 | Cursor pagination: next_cursor present; second page is stable            | integration | `pytest tests/audit/test_controllers.py::test_cursor_pagination -x`          | ❌ Wave 0    |
| AUDIT-02 | AuditEntryOut does NOT contain impersonator field                        | unit        | `pytest tests/audit/test_schemas.py::test_impersonator_excluded -x`          | ❌ Wave 0    |
| AUDIT-02 | APIKey events appear in org audit log (not skipped by references())      | integration | `pytest tests/audit/test_controllers.py::test_apikey_events_in_audit_log -x` | ❌ Wave 0    |

### Sampling Rate

- **Per task commit:** `cd apps/api && python -m pytest tests/audit/ -x -q`
- **Per wave merge:** `cd apps/api && python -m pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/audit/__init__.py` — module-level import from `apps.audit.context` (RED trigger per Phase 27/28 pattern)
- [ ] `tests/audit/conftest.py` — lazy imports inside fixture bodies; org, membership (admin role), and user fixtures
- [ ] `tests/audit/test_models.py` — RED stubs for AUDIT-01 event creation
- [ ] `tests/audit/test_middleware.py` — RED stubs for AuditContextMiddleware.get_context()
- [ ] `tests/audit/test_context.py` — RED stub for audit_context() no-op
- [ ] `tests/audit/test_controllers.py` — RED stubs for AUDIT-02 endpoint tests
- [ ] `tests/audit/test_schemas.py` — RED stub for AuditEntryOut field exclusion
- [ ] Framework install: `uv add django-pghistory` — adds pghistory + pgtrigger

_(No existing test infrastructure gaps — pytest + pytest-django already configured in pyproject.toml)_

---

## Sources

### Primary (HIGH confidence)

- [django-pghistory PyPI](https://pypi.org/project/django-pghistory/) — version 3.9.2 confirmed, Django 4.2–5.2 compatibility
- [django-pghistory event tracking docs](https://django-pghistory.readthedocs.io/en/stable/event_tracking/) — `@pghistory.track()`, InsertEvent/UpdateEvent/DeleteEvent, custom labels
- [django-pghistory context docs 3.5.2](https://django-pghistory.readthedocs.io/en/3.5.2/context/) — HistoryMiddleware subclassing, get_context() override, pghistory.context() in tasks
- [django-pghistory aggregating events docs](https://django-pghistory.readthedocs.io/en/latest/aggregating_events/) — Events CTE, MiddlewareEvents, ProxyField, across(), references()
- [django-pghistory event models docs](https://django-pghistory.readthedocs.io/en/3.4.2/event_models/) — pgh_id, pgh_label, pgh_created_at, pgh_obj, pgh_context structure
- [django-pghistory installation docs](https://django-pghistory.readthedocs.io/en/latest/installation/) — INSTALLED_APPS requirement for pghistory + pgtrigger
- Project `apps/api/apps/orgs/models.py` — Organization, Membership field names confirmed
- Project `apps/api/apps/api_keys/models.py` — APIKey fields, last_used_at/usage_count exclude candidates
- Project `apps/api/apps/webhooks/models.py` — WebhookEndpoint fields, consecutive_failures exclude candidate
- Project `apps/api/config/settings/base.py` — INSTALLED_APPS structure, MIDDLEWARE order, B2B_START/B2B_END markers
- Project `apps/api/apps/webhooks/controllers.py` — confirmed @paginate incompatibility, manual dict response pattern
- Project `.planning/STATE.md` — pghistory library choice locked; B2B marker convention confirmed

### Secondary (MEDIUM confidence)

- [Caktus Group blog — tips for django-pghistory (April 2025)](https://www.caktusgroup.com/blog/2025/04/07/tips-tracking-django-model-changes-django-pghistory/) — selective tracking, exclude patterns

### Tertiary (LOW confidence)

- Exact auto-generated event model app label strings (e.g. `"orgs.OrganizationEvent"`) — must verify after running `makemigrations`

---

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — django-pghistory 3.9.2 confirmed from PyPI; library choice locked in STATE.md
- Architecture: HIGH — HistoryMiddleware subclassing, ProxyField, Events.across() all confirmed from official readthedocs; no-op pattern from Python contextlib
- Pitfalls: HIGH for pitfalls 1 (auto_now noise), 2 (N+1 actor email), 4 (null context), 7 (ruff migration), 8 (B2B markers); MEDIUM for pitfall 3 (APIKey org scoping via across() — correct approach but exact label strings unverified)

**Research date:** 2026-03-13
**Valid until:** 2026-04-13 (stable library; 30-day window)
