# Phase 29: Audit Logging - Research

**Researched:** 2026-03-13
**Domain:** Django audit logging with PostgreSQL triggers (django-pghistory)
**Confidence:** HIGH

## Summary

Phase 29 adds automatic audit logging to four B2B models: `Organization`, `Membership`, `APIKey`, and `WebhookEndpoint`. The locked library is `django-pghistory` — which uses PostgreSQL triggers to capture every insert, update, and delete, including bulk ORM operations and raw SQL that Django signals miss. This is the right tool for the job.

The implementation has two distinct halves. The first is infrastructure: decorating the four models with `@pghistory.track()`, installing `AuditContextMiddleware` to bind user and org context automatically on every request, and registering `pghistory` + `pgtrigger` in INSTALLED_APPS. The second is the query API: a Django Ninja Extra endpoint at `GET /api/v1/org/{slug}/audit-log` that queries the aggregate `pghistory.models.Events` (or `pghistory.models.MiddlewareEvents`) CTE, applies org-scoping, supports pagination and filtering, and strips the `impersonator` context key before returning results to non-staff callers.

The primary constraint is impersonation data isolation: every audit entry stores full context including an `impersonator` field (written by Phase 30's `django-hijack` integration), but org-level queries must silently omit that field. The field is stored; it is just not serialised in the non-staff response schema.

**Primary recommendation:** Decorate all four models in-place, install a custom `AuditContextMiddleware` that extends `pghistory.middleware.HistoryMiddleware` to add `org_id` + `impersonator` to context, and query via `pghistory.models.MiddlewareEvents` with a `references()` filter scoped to org objects.

---

<user_constraints>

## User Constraints (from CONTEXT.md)

No CONTEXT.md exists for Phase 29 yet. All decisions below come from the accumulated STATE.md decisions log and are therefore treated as locked.

### Locked Decisions

- Audit library: `django-pghistory` (NOT `django-pgaudit` — 404 on PyPI; NOT signal-based `django-auditlog` — triggers capture bulk ORM + raw SQL that signals miss)
- Impersonation library (Phase 30): `django-hijack` 3.7.6 — impersonation events must include `impersonator` FK in audit context
- Impersonation field NOT exposed to org admins: stored in context JSON, excluded from org-level response schema; staff-only
- All B2B code uses `# B2B_START` / `# B2B_END` markers; new middleware, INSTALLED_APPS entries, and settings must follow this convention

### Claude's Discretion

- How to structure the `AuditLog` app: create a new `apps/audit` app vs. adding to `apps/orgs` — recommend new `apps/audit` for B2B_START/B2B_END cleanness
- Exact name of the middleware class and where to register it in the MIDDLEWARE stack
- Which fields to include in the paginated response schema (`AuditEntryOut`)
- Whether to use `pghistory.models.MiddlewareEvents` or a custom proxy model for the query layer

### Deferred Ideas (OUT OF SCOPE)

- AUDIT-F01: External audit log shipping (Splunk, Datadog Logs) — template provides foundation; products add exporters
- Audit logging for `Invitation` model — not listed in AUDIT-01 requirements
- Per-field diff exposure in the API — store it internally, don't expose in Phase 29 API
  </user_constraints>

<phase_requirements>

## Phase Requirements

| ID       | Description                                                                                                                                                                      | Research Support                                                                                                                            |
| -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| AUDIT-01 | System records changes to `Organization`, `Membership`, `APIKey`, `WebhookEndpoint` via pghistory triggers; `AuditContextMiddleware` attaches user and org context automatically | `@pghistory.track()` decorator on each model + custom HistoryMiddleware subclass that adds `org_id` to context                              |
| AUDIT-02 | Org owner and admins can query paginated audit log filtered by actor/date/action (`GET /api/v1/org/{slug}/audit-log`); impersonation entries not exposed to org admins           | `pghistory.models.Events.objects.references(org)` as base queryset; `AuditEntryOut` schema omits `impersonator`; IsOrgAdmin permission gate |

</phase_requirements>

---

## Standard Stack

### Core

| Library          | Version                  | Purpose                                | Why Standard                                                                                   |
| ---------------- | ------------------------ | -------------------------------------- | ---------------------------------------------------------------------------------------------- |
| django-pghistory | 3.9.2                    | PostgreSQL-trigger-based audit logging | Locked project decision; captures bulk ORM + raw SQL; no app-code changes required after setup |
| pgtrigger        | (installed by pghistory) | Low-level trigger management           | pghistory is built on pgtrigger; auto-installed as dependency                                  |

### Supporting

| Library                                | Version  | Purpose                                             | When to Use                                                    |
| -------------------------------------- | -------- | --------------------------------------------------- | -------------------------------------------------------------- |
| pghistory.middleware.HistoryMiddleware | built-in | Wraps requests with user + url context              | Subclass it to add `org_id`; don't use it bare                 |
| pghistory.models.Events                | built-in | Cross-model CTE that aggregates all event tables    | Base for audit log queries; use `references()` for org-scoping |
| pghistory.models.MiddlewareEvents      | built-in | Events with pre-attached `user` + `url` ProxyFields | Use when the response schema needs `user` as a navigable FK    |

### Alternatives Considered

| Instead of         | Could Use                         | Tradeoff                                                                                        |
| ------------------ | --------------------------------- | ----------------------------------------------------------------------------------------------- |
| django-pghistory   | django-auditlog                   | Auditlog uses Django signals — misses bulk ORM + raw SQL. Rejected.                             |
| django-pghistory   | django-pgaudit                    | 404 on PyPI as of research date. Rejected.                                                      |
| Custom proxy model | pghistory.models.MiddlewareEvents | MiddlewareEvents is simpler; only need proxy if adding extra ProxyFields beyond user/url/org_id |

**Installation:**

```bash
uv add django-pghistory
```

Both `pghistory` and `pgtrigger` must be added to `INSTALLED_APPS`. Run `python manage.py migrate` after adding — pghistory creates a `pghistory_context` table.

---

## Architecture Patterns

### Recommended Project Structure

The cleanest B2B scaffold is a new `apps/audit` app. This keeps audit code fully wrapped in `# B2B_START` / `# B2B_END` markers and avoids adding Phase-29-only endpoints to the already-large `apps/orgs` controllers.

```
apps/api/apps/audit/
├── __init__.py
├── apps.py           # AuditConfig (no ready() hook needed for Phase 29)
├── middleware.py     # AuditContextMiddleware (extends HistoryMiddleware)
├── controllers.py    # AuditLogController — GET /org/{slug}/audit-log
├── schemas.py        # AuditEntryOut (impersonator field excluded)
└── migrations/       # Empty (no new Django models in Phase 29)
tests/audit/
├── __init__.py       # module-level import → RED before app exists
├── conftest.py       # lazy imports in fixtures
├── test_middleware.py
└── test_controllers.py
```

No new Django ORM model is introduced. The `pghistory_context` and auto-generated `*Event` tables are managed entirely by pghistory migrations.

### Pattern 1: Decorating Tracked Models

Add `@pghistory.track()` to each of the four B2B models. The decorator must be applied to the existing model class in-place; no new model files are created.

```python
# apps/orgs/models.py
import pghistory

@pghistory.track(
    pghistory.InsertEvent("org.created"),
    pghistory.UpdateEvent("org.updated"),
    pghistory.DeleteEvent("org.deleted"),
)
class Organization(models.Model):
    ...
```

```python
# apps/orgs/models.py (continued — Membership)
@pghistory.track(
    pghistory.InsertEvent("membership.created"),
    pghistory.UpdateEvent("membership.updated"),
    pghistory.DeleteEvent("membership.deleted"),
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
)
class WebhookEndpoint(models.Model):
    ...
```

Each decorated model gets a dynamically-generated `{ModelName}Event` table (e.g. `OrganizationEvent`, `MembershipEvent`) created by `makemigrations`.

**Important:** `pgh_label` values (the strings like `"org.created"`) are what the API exposes as `action`. Choose them now; changing them later invalidates existing audit records.

### Pattern 2: AuditContextMiddleware

Extend `pghistory.middleware.HistoryMiddleware` to inject `org_id` and (for Phase 30 compatibility) `impersonator` into context. The built-in middleware already captures `user` (the authenticated user's PK) and `url`.

```python
# apps/audit/middleware.py
import pghistory.middleware


class AuditContextMiddleware(pghistory.middleware.HistoryMiddleware):
    """Wraps every request in a pghistory context, adding org_id.

    Built-in HistoryMiddleware adds: user (PK of request.user), url.
    We extend it to add: org_id (from request.org, if set by IsOrgMember).

    impersonator is added by Phase 30 (django-hijack signal handler).
    It is stored in the shared pgh_context metadata JSON but is never
    serialised into AuditEntryOut (org-level schema excludes it).
    """

    def get_context(self, request):
        ctx = super().get_context(request)
        # request.org is set by IsOrgMember/IsOrgAdmin permission classes
        # when an org-scoped endpoint is hit. May be None on non-org endpoints.
        org = getattr(request, "org", None)
        if org is not None:
            ctx["org_id"] = org.pk
        return ctx
```

Register it in `MIDDLEWARE` inside the `# B2B_START` block, immediately after `ApiKeyRateLimitMiddleware`:

```python
# config/settings/base.py — inside # B2B_START block
"apps.audit.middleware.AuditContextMiddleware",  # B2B MODULE — audit context
```

**Position matters:** Place it after `AuthenticationMiddleware` and `AccountMiddleware` so `request.user` is already populated when `get_context()` runs.

### Pattern 3: Celery Task Context (no request.user)

For tasks that modify audit-tracked models (e.g. bulk operations in webhooks or billing), pass the acting user ID explicitly as a task argument and wrap the task body with `pghistory.context()`:

```python
# Example: a task that modifies an org on behalf of a user
from celery import shared_task
import pghistory

@shared_task
def some_org_task(org_id: int, actor_user_id: int) -> None:
    with pghistory.context(user=actor_user_id, task="some_org_task"):
        # changes to tracked models here will reference this context
        ...
```

Never use `request.user` inside Celery tasks — there is no request. Pass actor ID explicitly as a task argument.

### Pattern 4: Audit Log Query API

```python
# apps/audit/controllers.py
import pghistory.models
from ninja_extra import ControllerBase, api_controller, route
from ninja_extra.permissions import IsAuthenticated
from apps.orgs.permissions import IsOrgAdmin
from apps.audit.schemas import AuditEntryOut, AuditLogResponse

@api_controller(
    "/org/{org_slug}/audit-log",
    tags=["audit"],
    auth=[SessionAuth(), jwt_token_auth],
    permissions=[IsAuthenticated, IsOrgAdmin],
)
class AuditLogController(ControllerBase):
    @route.get("/", response={200: AuditLogResponse}, url_name="audit-log-list")
    def list_audit_log(
        self,
        request,
        org_slug: str,
        page: int = 1,
        page_size: int = 50,
        actor: int | None = None,
        action: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ):
        from apps.orgs.models import Organization
        org = request.org  # set by IsOrgAdmin/IsOrgMember

        # references() returns all events that have any FK to org
        # This covers Organization, Membership, APIKey, WebhookEndpoint events
        qs = pghistory.models.Events.objects.references(org).order_by("-pgh_created_at")

        if actor is not None:
            qs = qs.filter(pgh_context__metadata__user=actor)
        if action is not None:
            qs = qs.filter(pgh_label=action)
        # date filters use pgh_created_at
        if date_from:
            qs = qs.filter(pgh_created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(pgh_created_at__date__lte=date_to)

        count = qs.count()
        offset = (page - 1) * page_size
        results = list(qs[offset:offset + page_size])
        return 200, {"count": count, "results": [AuditEntryOut.from_event(e) for e in results]}
```

### Pattern 5: AuditEntryOut — Impersonator Exclusion

The `impersonator` field in `pgh_context.metadata` is written by Phase 30. In Phase 29, the schema simply never reads it, which means org admins cannot see it even after Phase 30 ships. Staff endpoints (Phase 30 admin) can expose it separately.

```python
# apps/audit/schemas.py
from ninja import Schema
from typing import Any

class AuditEntryOut(Schema):
    pgh_id: int
    pgh_created_at: Any  # datetime
    pgh_label: str        # e.g. "org.updated"
    pgh_obj_model: str    # e.g. "orgs.Organization"
    pgh_obj_id: str
    actor_id: int | None  # from pgh_context.metadata["user"]
    url: str | None       # from pgh_context.metadata["url"]
    # impersonator intentionally omitted — staff-only, Phase 30

    @classmethod
    def from_event(cls, event) -> "AuditEntryOut":
        metadata = {}
        if event.pgh_context:
            metadata = event.pgh_context  # JSON dict on MiddlewareEvents
        return cls(
            pgh_id=event.pgh_id,
            pgh_created_at=event.pgh_created_at,
            pgh_label=event.pgh_label,
            pgh_obj_model=event.pgh_obj_model,
            pgh_obj_id=str(event.pgh_obj_id),
            actor_id=metadata.get("user"),
            url=metadata.get("url"),
        )
```

### Pattern 6: Impersonator Field (Phase 30 prep)

Phase 30 will add a `django-hijack` signal handler that calls `pghistory.context(impersonator=request.user.pk)` when an impersonation session is active. This Phase 29 research documents that the field name is `impersonator` so Phase 30 can write it consistently.

The `AuditContextMiddleware` does NOT need to handle this — `django-hijack` provides signals (`hijack_started`, `hijack_ended`) that Phase 30 uses to push context.

### Anti-Patterns to Avoid

- **Do not track `Invitation`, `WebhookDelivery`, `WebhookDeliveryAttempt`, or `OrgCustomer`:** these are high-write, low-audit-value models. AUDIT-01 names only four models.
- **Do not use bare `pghistory.middleware.HistoryMiddleware`:** it does not attach `org_id`; use the custom subclass.
- **Do not filter Events by `pgh_model` string directly:** use `across()` or `references()` — they use proper indexes.
- **Do not expose `pgh_diff` in the org-level API for Phase 29:** before/after diffs bloat the response and are not in the AUDIT-02 spec. Store them; don't expose them yet.
- **Do not pass `request.user` into Celery tasks:** always pass `actor_user_id` as an explicit integer argument.
- **Do not put `@pghistory.track()` on any model that has `auto_now_add` or `auto_now` fields without listing `exclude=["updated_at"]`:** every save() on a model with `auto_now=True` triggers an `UpdateEvent` even if no application field changed. This creates noise. Use `exclude=["updated_at"]` to suppress timestamp-only events, or accept the noise.

---

## Don't Hand-Roll

| Problem                                   | Don't Build                         | Use Instead                   | Why                                                                                                     |
| ----------------------------------------- | ----------------------------------- | ----------------------------- | ------------------------------------------------------------------------------------------------------- |
| Capturing bulk QuerySet.update()          | Custom signals or post_save         | `@pghistory.track()` triggers | Signals fire per-instance; bulk update bypasses them entirely. Triggers fire at the Postgres row level. |
| Capturing raw SQL changes                 | Manual logging                      | Triggers                      | Raw SQL bypasses ORM layer; only triggers see it.                                                       |
| Before/after diff calculation             | Window functions, manual comparison | `pgh_diff` on Events CTE      | pghistory computes diffs using Postgres window functions automatically.                                 |
| Cross-model unified audit query           | UNION ALL query                     | `pghistory.models.Events`     | Already a CTE UNION ALL; use `references()` for FK-based scoping.                                       |
| Context grouping across middleware → task | Thread locals                       | `pghistory.context()`         | pghistory context uses `contextvars` — safe across async and properly scoped per request.               |

**Key insight:** The entire value of django-pghistory over signal-based libraries is that triggers fire unconditionally at the database level. Any hand-rolled solution will have a gap for bulk operations.

---

## Common Pitfalls

### Pitfall 1: auto_now / auto_now_add Field Noise

**What goes wrong:** Every `model.save()` also updates `updated_at` (auto_now=True). This creates an `UpdateEvent` with `pgh_diff: {"updated_at": [...]}` even when no user-facing field changed. The audit log fills with meaningless timestamp events.
**Why it happens:** Postgres triggers fire on every row write; they don't know which fields the application considers "significant."
**How to avoid:** Add `exclude=["updated_at"]` to each `@pghistory.track()` call. The `Organization`, `Membership`, and `WebhookEndpoint` models all have `updated_at = models.DateTimeField(auto_now=True)`. `APIKey` does not have `updated_at` but has `last_used_at` and `usage_count` which update on every API key authentication — definitely exclude these from audit tracking.
**Warning signs:** High event table row counts after a short time; many events with only `pgh_diff: {"updated_at": [...]}`.

### Pitfall 2: Missing org_id in Context for Non-Org Endpoints

**What goes wrong:** `AuditContextMiddleware.get_context()` reads `request.org`. But `request.org` is only set by `IsOrgMember`/`IsOrgAdmin` permission classes on org-scoped endpoints. Requests to non-org endpoints (e.g. creating an API key via `/me/api-keys/`) do not set `request.org`, so the audit context has no `org_id`.
**Why it happens:** Middleware runs before permission classes, so `request.org` is not yet set when middleware `get_context()` is called. However, `HistoryMiddleware` wraps the full request — so the context is open during the entire request, including after permissions run.
**How to avoid:** In `get_context()`, only add `org_id` if `request.org` is already set (guard with `getattr(request, "org", None)`). Alternatively, use `pghistory.context(org_id=org.pk)` inside the org-scoped service methods as a nested context call to overlay `org_id` after permission checks.
**Warning signs:** Audit entries for Membership changes that have no `org_id` in their context.

### Pitfall 3: references() Scope — Only One FK Level Deep

**What goes wrong:** `Events.objects.references(org)` returns events for objects that have a direct FK to `Organization`. `Organization` itself has no FK to itself. `Membership` and `WebhookEndpoint` have `org` FK. `APIKey` has a `user` FK, not an `org` FK — it is not directly connected to Organization.
**Why it happens:** `references()` only traverses one FK hop. `APIKey` is not scoped to an org in the data model.
**How to avoid:** Use `across()` to explicitly name which event models to include, rather than relying solely on `references()`. Combine: `Events.objects.references(org).across("orgs.OrganizationEvent", "orgs.MembershipEvent", "webhooks.WebhookEndpointEvent") | Events.objects.across("api_keys.APIKeyEvent").filter(pgh_data__user__in=org_user_ids)`. Alternatively, scope the `APIKeyEvent` query by filtering `pgh_data__user__in=org.memberships.values("user_id")`. Confirm via test that APIKey events show up in the audit log.
**Warning signs:** API key create/revoke events missing from the org audit log.

### Pitfall 4: makemigrations Creates Event Model Migrations in the Wrong App

**What goes wrong:** When `@pghistory.track()` is applied to `Organization` (in `apps.orgs`), the auto-generated `OrganizationEvent` migration is created inside `apps/orgs/migrations/`. This is correct. But pghistory also creates a migration for the shared `pghistory_context` table in the `pghistory` app itself.
**Why it happens:** pghistory uses a shared `Context` model registered under the `pghistory` app.
**How to avoid:** Run `makemigrations` normally; inspect the diff. Expect new migrations in: `pghistory`, `pgtrigger`, `apps.orgs` (2 event models), `apps.api_keys` (1 event model), `apps.webhooks` (1 event model).

### Pitfall 5: pgh_context Is None for Unauthenticated Requests

**What goes wrong:** Queries on `Events` that assume `pgh_context` is never None will raise `AttributeError` or produce unexpected nulls for changes made outside a request context (e.g. data migrations, management commands, test fixtures).
**Why it happens:** pghistory context is nullable — it requires `pghistory.context()` to be active.
**How to avoid:** Always guard: `metadata = event.pgh_context or {}`. In tests, wrap fixture setup in `pghistory.context(user=0)` if you want test events to have context, or accept null context and ensure `from_event()` handles it.

### Pitfall 6: ruff migration exclusion

**What goes wrong:** Auto-generated pghistory/pgtrigger migration files may contain lines that exceed ruff's line length limit.
**Why it happens:** pghistory generates trigger SQL inline in migrations; SQL strings can be very long.
**How to avoid:** The project already has a `ruff.toml` exclusion pattern for migrations (added in Phase 27). Verify it covers `apps/*/migrations/*.py` — it should already apply.

---

## Code Examples

Verified patterns from official sources:

### Installing pghistory (INSTALLED_APPS)

```python
# config/settings/base.py — inside # B2B_START block
# Source: https://django-pghistory.readthedocs.io/en/stable/installation/
INSTALLED_APPS = [
    ...
    # B2B_START
    "apps.orgs",
    "apps.webhooks",
    "apps.api_keys",
    "pghistory",    # B2B MODULE — audit event storage
    "pgtrigger",    # B2B MODULE — trigger management (pghistory dependency)
    "apps.audit",   # B2B MODULE — audit context middleware + query API
    # B2B_END
    ...
]
```

### Basic track decorator with labels

```python
# Source: https://django-pghistory.readthedocs.io/en/stable/event_tracking/
import pghistory

@pghistory.track(
    pghistory.InsertEvent("org.created"),
    pghistory.UpdateEvent("org.updated"),
    pghistory.DeleteEvent("org.deleted"),
    exclude=["updated_at"],  # suppress auto_now noise
)
class Organization(models.Model):
    ...
```

### Extending HistoryMiddleware

```python
# Source: https://django-pghistory.readthedocs.io/en/stable/context/
import pghistory.middleware

class AuditContextMiddleware(pghistory.middleware.HistoryMiddleware):
    def get_context(self, request):
        ctx = super().get_context(request)
        org = getattr(request, "org", None)
        if org is not None:
            ctx["org_id"] = org.pk
        return ctx
```

### Using context() in Celery tasks

```python
# Source: https://django-pghistory.readthedocs.io/en/stable/context/
import pghistory

@shared_task
def org_task(org_id: int, actor_user_id: int) -> None:
    with pghistory.context(user=actor_user_id, task="org_task"):
        ...  # changes here have context
```

### Querying the audit log with references()

```python
# Source: https://django-pghistory.readthedocs.io/en/stable/aggregating_events/
import pghistory.models

qs = pghistory.models.Events.objects.references(org).order_by("-pgh_created_at")

# Filter by actor
qs = qs.filter(pgh_context__metadata__user=actor_id)

# Filter by label/action
qs = qs.filter(pgh_label="org.updated")
```

### Reading context metadata safely

```python
# pgh_context is None if change happened outside a request/context manager
metadata = getattr(event, "pgh_context", None) or {}
actor_id = metadata.get("user")
url = metadata.get("url")
impersonator = metadata.get("impersonator")  # Phase 30 only — don't expose in Phase 29
```

---

## State of the Art

| Old Approach                                  | Current Approach                            | When Changed            | Impact                                        |
| --------------------------------------------- | ------------------------------------------- | ----------------------- | --------------------------------------------- |
| Signal-based audit (`pre_save` / `post_save`) | Postgres trigger-based (`django-pghistory`) | Locked in v1.4 planning | Captures bulk `QuerySet.update()` and raw SQL |
| Shared event model per app                    | Per-model `{ModelName}Event` tables         | pghistory v2+           | Clean isolation; query via `Events` CTE       |
| Custom context thread locals                  | `pghistory.context()` / `contextvars`       | pghistory v2            | Safe across async and request boundaries      |
| django-pgaudit                                | Not available (404 on PyPI)                 | —                       | Use django-pghistory                          |

**Deprecated/outdated:**

- `django-pgaudit`: 404 on PyPI, not available.
- Signal-based audit (`django-auditlog`): misses bulk ORM operations. Not used.

---

## Open Questions

1. **APIKey org-scoping for audit log**
   - What we know: `APIKey` has `user` FK only, not `org` FK. `references(org)` won't catch it.
   - What's unclear: The most efficient join path — query `org.memberships.values("user_id")` and filter `pgh_data__user__in=...` OR use `across("api_keys.APIKeyEvent")` with a subquery.
   - Recommendation: At plan time, implement as `Events.objects.across("api_keys.APIKeyEvent").filter(pgh_data__user__in=org.memberships.values("user_id"))` and UNION with `references(org)` covering the other three models. Write a test to confirm APIKey create/revoke events appear in the org audit log.

2. **Phase 30 impersonator context injection point**
   - What we know: `django-hijack` emits `hijack_started` / `hijack_ended` signals. The `AuditContextMiddleware` does not handle this yet.
   - What's unclear: Whether to write a Phase 29 placeholder signal receiver or leave it entirely to Phase 30.
   - Recommendation: Leave impersonator context injection entirely to Phase 30. Phase 29 only guarantees the field is absent (not present) in the org-level response schema.

3. **pgh_diff exposure in audit API**
   - What we know: `pgh_diff` is available on every `Events` row as a JSON dict of `{field: [old, new]}`.
   - What's unclear: Whether the response schema should expose `pgh_diff` for Phase 29.
   - Recommendation: Exclude from Phase 29 API — not specified in AUDIT-02. Can be added in a later phase without a breaking change (additive schema field).

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

| Req ID   | Behavior                                                                     | Test Type   | Automated Command                                                                     | File Exists? |
| -------- | ---------------------------------------------------------------------------- | ----------- | ------------------------------------------------------------------------------------- | ------------ |
| AUDIT-01 | `@pghistory.track()` on Organization — create writes OrganizationEvent       | integration | `pytest tests/audit/test_middleware.py::test_org_create_writes_event -x`              | Wave 0       |
| AUDIT-01 | `@pghistory.track()` on Membership — delete writes MembershipEvent           | integration | `pytest tests/audit/test_middleware.py::test_membership_delete_writes_event -x`       | Wave 0       |
| AUDIT-01 | `@pghistory.track()` on APIKey — revoke writes APIKeyEvent                   | integration | `pytest tests/audit/test_middleware.py::test_apikey_revoke_writes_event -x`           | Wave 0       |
| AUDIT-01 | `@pghistory.track()` on WebhookEndpoint — update writes WebhookEndpointEvent | integration | `pytest tests/audit/test_middleware.py::test_webhook_endpoint_update_writes_event -x` | Wave 0       |
| AUDIT-01 | AuditContextMiddleware attaches user and org_id to pgh_context               | integration | `pytest tests/audit/test_middleware.py::test_context_attaches_user_and_org_id -x`     | Wave 0       |
| AUDIT-02 | GET /api/v1/org/{slug}/audit-log returns paginated entries                   | integration | `pytest tests/audit/test_controllers.py::test_list_audit_log_paginated -x`            | Wave 0       |
| AUDIT-02 | Audit log filtered by actor returns only that user's changes                 | integration | `pytest tests/audit/test_controllers.py::test_filter_by_actor -x`                     | Wave 0       |
| AUDIT-02 | Audit log response never contains impersonator field                         | unit        | `pytest tests/audit/test_controllers.py::test_impersonator_not_in_response -x`        | Wave 0       |
| AUDIT-02 | Non-admin org member cannot access audit log (403)                           | integration | `pytest tests/audit/test_controllers.py::test_member_cannot_access_audit_log -x`      | Wave 0       |
| AUDIT-02 | APIKey audit events appear in org audit log                                  | integration | `pytest tests/audit/test_controllers.py::test_apikey_events_in_org_audit_log -x`      | Wave 0       |

### Sampling Rate

- **Per task commit:** `cd apps/api && python -m pytest tests/audit/ -x -q`
- **Per wave merge:** `cd apps/api && python -m pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/audit/__init__.py` — module-level import triggers RED state (matches project pattern)
- [ ] `tests/audit/conftest.py` — lazy imports in fixture bodies; org + user fixtures
- [ ] `tests/audit/test_middleware.py` — AUDIT-01 trigger coverage
- [ ] `tests/audit/test_controllers.py` — AUDIT-02 endpoint coverage

_(No test framework gaps — pytest + pytest-django already installed and configured)_

---

## Sources

### Primary (HIGH confidence)

- [django-pghistory PyPI](https://pypi.org/project/django-pghistory/) — current version 3.9.2, supported Django versions
- [django-pghistory event tracking docs](https://django-pghistory.readthedocs.io/en/stable/event_tracking/) — `@pghistory.track()` decorator options, tracker types, labels
- [django-pghistory context docs](https://django-pghistory.readthedocs.io/en/stable/context/) — `pghistory.context()` manager, HistoryMiddleware extension, Celery pattern
- [django-pghistory event models docs](https://django-pghistory.readthedocs.io/en/stable/event_models/) — auto-generated fields, pgh_diff, custom event models
- [django-pghistory aggregating events docs](https://django-pghistory.readthedocs.io/en/stable/aggregating_events/) — `Events` CTE, `references()`, `across()`, `tracks()`, `pgh_diff` structure
- [django-pghistory settings docs](https://django-pghistory.readthedocs.io/en/stable/settings/) — PGHISTORY_MIDDLEWARE_METHODS, PGHISTORY_JSON_ENCODER, admin settings

### Secondary (MEDIUM confidence)

- [Caktus Group blog — tips for django-pghistory (April 2025)](https://www.caktusgroup.com/blog/2025/04/07/tips-tracking-django-model-changes-django-pghistory/) — selective tracking, initial snapshots pattern
- [Collecting Context — pghistory 3.0 docs](https://django-pghistory.readthedocs.io/en/3.0.0/context/) — verified against current stable docs

### Tertiary (LOW confidence)

- STATE.md accumulated decisions — locked choices for audit library confirmed here

---

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — django-pghistory 3.9.2, locked decision, docs verified
- Architecture: HIGH — patterns drawn from official docs; Pitfall 3 (APIKey scoping) is confirmed by `references()` one-hop limitation from official docs
- Pitfalls: HIGH for pitfalls 1, 2, 5; MEDIUM for pitfall 3 (APIKey org-scope workaround needs test validation)

**Research date:** 2026-03-13
**Valid until:** 2026-04-13 (django-pghistory is stable; 30-day window is safe)
