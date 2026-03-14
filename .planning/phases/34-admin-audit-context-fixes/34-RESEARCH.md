# Phase 34: Admin + Audit Context Fixes - Research

**Researched:** 2026-03-13
**Domain:** Django admin registration (django-unfold) + pghistory audit context injection
**Confidence:** HIGH

## Summary

Phase 34 closes two v1.4 audit gaps with targeted, surgical changes. All infrastructure already exists — this phase wires it together correctly rather than building anything new.

**Plan 34-01** adds `OrgCustomerAdmin` to `apps/orgs/admin.py` and a sidebar entry to the UNFOLD B2B section. The pattern is identical to `OrganizationAdmin` and `MembershipAdmin` already in that file. `OrgCustomer` exists in `apps/orgs/models.py` with a OneToOneField to Organization, `stripe_customer_id`, `created_at`, and `updated_at`. The admin mirrors `CustomerAdmin` in `apps/billing/admin.py` with an org-scoped column shape.

**Plan 34-02** adds an `org` FK to `APIKey`, updates `APIKeyIn`/`APIKeyOut` schemas, and wraps `APIKeyService.create()` and `APIKeyService.revoke()` in `audit_context()`. The `audit_context()` helper in `apps/audit/context.py` already accepts `user_id` and `org_id` and degrades gracefully in non-B2B mode. The existing `get_audit_log_page()` selector filters by `org_id` in the pghistory Context row — once `audit_context()` injects `org_id` during create/revoke, APIKey events become visible in the org audit log without any selector changes.

**Primary recommendation:** Read the existing code in this order before planning each task — orgs/admin.py, billing/admin.py, base.py UNFOLD sidebar, api_keys/models.py, api_keys/schemas.py, api_keys/services.py, api_keys/controllers.py, audit/context.py. Every pattern needed is already implemented; this is wiring work.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions

**OrgCustomerAdmin — location and shape**

- File: `apps/orgs/admin.py` — co-located with the model. No cross-app imports required.
- Columns: `list_display = ("org", "stripe_customer_id", "created_at")`
- Search: `search_fields = ("org__name", "org__slug", "stripe_customer_id")`
- Read-only fields: `readonly_fields = ("created_at", "updated_at")`
- Permissions: Fully editable — not read-only. Staff can correct `stripe_customer_id`.
- Sidebar placement: B2B section, appended after Audit Log. Order: Organizations, Memberships, API Keys, Webhooks, Audit Log, **Org Billing**.
- B2B markers: `OrgCustomerAdmin` registration and its `OrgCustomer` import wrapped in `B2B_START`/`B2B_END`. Sidebar entry also wrapped.

**APIKey org FK (schema change)**

- Add `org = models.ForeignKey("orgs.Organization", on_delete=models.SET_NULL, null=True, blank=True, related_name="api_keys")` to `APIKey`.
- Migration required — nullable, no data migration needed; existing keys get `org=None`.

**Create endpoint — org association**

- `POST /api/v1/me/api-keys/` request body gains optional `org_slug: str | None` field in `APIKeyIn`.
- `APIKeyService.create()` accepts `org: Organization | None`. Service resolves org and verifies membership (raise 403 if not member).
- Existing callers omitting `org_slug` continue to work — personal keys stay personal (org=None).

**Audit context injection — service layer**

- `APIKeyService.create()` and `APIKeyService.revoke()` wrap their DB mutations in `audit_context(user_id=user.pk, org_id=str(org.id) if org else None)`.
- Injection in service layer (not controller or middleware) — consistent with Phase 29's pattern for Celery tasks.

**List endpoint — no org filter**

- `GET /api/v1/me/api-keys/` returns all keys for the user regardless of org. No `?org_slug=` filter.

**APIKeyOut schema update**

- `APIKeyOut` gains optional `org_slug: str | None` field. When org is None, field is null in response.

### Claude's Discretion

- Whether `org_slug` or `org_id` (UUID) is exposed in `APIKeyOut` — prefer `org_slug` for human readability.
- Exact field order in `APIKeyIn` schema.
- Index strategy for the new `org` FK on `APIKey` (Django default index is fine; composite index not needed for Phase 34 query patterns).

### Deferred Ideas (OUT OF SCOPE)

- `?org_slug=` filter on `GET /api/v1/me/api-keys/` for multi-org users — future follow-up
- Org-scoped API key endpoint (`POST /api/v1/org/{slug}/api-keys/`) — separate phase if needed
- Read-only mode for OrgCustomerAdmin — not needed
  </user_constraints>

<phase_requirements>

## Phase Requirements

| ID       | Description                                                                                                                                                                      | Research Support                                                                                                                                                                                                                                                                                                                                                         |
| -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| BILL-01  | System creates `OrgCustomer` (linked to `Organization`) for per-org Stripe billing                                                                                               | OrgCustomer model confirmed in `apps/orgs/models.py`; admin registration gap confirmed in `apps/orgs/admin.py` — model exists, admin class does not. Sidebar gap confirmed in `base.py` UNFOLD config (no `orgs_orgcustomer_changelist` link).                                                                                                                           |
| AUDIT-01 | System records changes to `Organization`, `Membership`, `APIKey`, `WebhookEndpoint` via pghistory triggers; `AuditContextMiddleware` attaches user and org context automatically | APIKey tracking confirmed with `@pghistory.track` in `api_keys/models.py`. Audit log selector confirmed filtering by `pgh_context__org_id`. Gap: `/me/api-keys/` routes are not org-scoped — `AuditContextMiddleware` sets `org_id` only when `request.org` is populated (requires `/{org_slug}/` routes). Service-layer `audit_context()` injection is the correct fix. |

</phase_requirements>

## Standard Stack

### Core

| Library          | Version              | Purpose                            | Why Standard                                                           |
| ---------------- | -------------------- | ---------------------------------- | ---------------------------------------------------------------------- |
| django-unfold    | installed (Phase 30) | Admin theming + ModelAdmin base    | Project standard — all admins inherit `UnfoldModelAdmin`               |
| django-pghistory | 3.9.2 (Phase 29)     | Event tracking + context injection | Project standard for audit; `pghistory.context()` is the injection API |
| Django ORM       | Django 5.2.11        | Model FK, migration                | All DB access via ORM — no raw SQL                                     |

### No New Libraries

Phase 34 installs no new packages. All tools are in `pyproject.toml` from Phases 29–30.

## Architecture Patterns

### Pattern 1: UnfoldModelAdmin Registration (Plan 34-01)

**What:** Add `OrgCustomerAdmin` to `apps/orgs/admin.py` — exact same structure as `OrganizationAdmin` and `MembershipAdmin` already in that file.

**Key detail:** `OrgCustomer` has a `OneToOneField` to `Organization`. `list_display` uses `"org"` (calls `__str__` = `Organization(slug)`) — this is readable. If more readable, use `"org__name"` but note that requires `list_select_related = True` on the admin to avoid N+1 queries.

**Pattern from billing/admin.py:**

```python
# Source: apps/api/apps/billing/admin.py (CustomerAdmin)
@admin.register(Customer)
class CustomerAdmin(ModelAdmin):
    list_display = ("user", "stripe_customer_id", "created_at")
    search_fields = ("user__email", "stripe_customer_id")
    raw_id_fields = ("user",)
```

**OrgCustomerAdmin equivalent:**

```python
# B2B_START
from .models import Membership, OrgCustomer, Organization

@admin.register(OrgCustomer)
class OrgCustomerAdmin(ModelAdmin):
    list_display = ("org", "stripe_customer_id", "created_at")
    search_fields = ("org__name", "org__slug", "stripe_customer_id")
    readonly_fields = ("created_at", "updated_at")
# B2B_END
```

**Important:** `OrgCustomer` import goes into the existing `from .models import ...` line — do not create a second import statement.

### Pattern 2: UNFOLD Sidebar Entry (Plan 34-01)

The UNFOLD B2B sidebar block currently has 5 items: Organizations, Memberships, API Keys, Webhooks, Audit Log. The new entry is appended as the 6th item inside the same `B2B_START`/`B2B_END` block.

```python
# Source: apps/api/config/settings/base.py (lines 523-556)
# Add after Audit Log item, still inside B2B_START/B2B_END:
# B2B_START
{
    "title": "Org Billing",
    "icon": "receipt",          # Material Symbols name — NOT heroicon
    "link": reverse_lazy("admin:orgs_orgcustomer_changelist"),
},
# B2B_END
```

**CRITICAL ICON NOTE:** django-unfold uses **Material Symbols** (Google), NOT Heroicons. The project comment in base.py (line 518-522) already documents this pitfall from Phase 30 research. Valid icon names: `receipt`, `business`, `credit_card`, etc. Heroicon names render as blank icons.

**Admin URL pattern:** Django auto-generates the changelist URL as `admin:{app_label}_{model_name_lower}_changelist`. For `OrgCustomer` in `apps/orgs`: `admin:orgs_orgcustomer_changelist`.

### Pattern 3: APIKey org FK Migration (Plan 34-02)

**Model change:**

```python
# apps/api/apps/api_keys/models.py — add to APIKey class:
org = models.ForeignKey(
    "orgs.Organization",
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="api_keys",
)
```

**Migration:** Run `python manage.py makemigrations api_keys` — Django generates a nullable AddField migration. No `data_migration` needed; existing rows get `org=NULL`.

**Migration number:** Will be `0003_apikey_org.py` (0001 = initial, 0002 = pghistory triggers).

**Existing index on `["user", "is_active"]` is sufficient.** The `org` FK will get Django's auto-generated index (`api_keys_ke_org_id_XXXXXX_idx`). No composite index needed for Phase 34 query patterns (which are create/revoke, not bulk queries by org).

**`@pghistory.track` exclude list:** The existing decorator `exclude=["last_used_at", "usage_count"]` does NOT exclude `org`. Adding `org` FK means org changes are tracked. This is correct — a key being re-associated to an org is an auditable event.

### Pattern 4: Schema Updates (Plan 34-02)

**APIKeyIn — add org_slug:**

```python
# apps/api/apps/api_keys/schemas.py
class APIKeyIn(Schema):
    name: str = ""
    org_slug: str | None = None    # NEW — optional; None = personal key
    scopes: list[str]
    # ... existing validator unchanged
```

**APIKeyOut — add org_slug:**

```python
class APIKeyOut(Schema):
    id: str
    name: str
    org_slug: str | None           # NEW — None when key has no org
    scopes: list[str]
    prefix: str
    is_active: bool
    last_used_at: datetime | None
    usage_count: int
    created_at: datetime
```

**APIKeyCreateOut** — also needs `org_slug: str | None` for consistency (the create response should reflect the org association immediately). This mirrors what `list_keys` returns.

**Controller list_keys serialization:** The `list_keys` method manually constructs `APIKeyOut(...)` from `result["results"]`. After adding `org_slug` to `APIKeyOut`, the constructor call must include `org_slug=k.org.slug if k.org_id else None`. This requires either `select_related("org")` on the queryset or lazy attribute access (since `org_id` is set, `k.org` is a deferred FK — accessing `.slug` hits the DB per row). **Use `select_related("org")` in `list_for_user()` to avoid N+1.**

### Pattern 5: Service Layer audit_context Injection (Plan 34-02)

**What:** Wrap the DB mutation inside `create()` and `revoke()` with `audit_context()`. The helper already exists at `apps/audit/context.py` and uses `pghistory.context()` internally.

**create() — with org resolution:**

```python
# apps/api/apps/api_keys/services.py
from apps.audit.context import audit_context

@classmethod
def create(cls, user, name: str, scopes: list[str], org=None) -> tuple[APIKey, str]:
    raw_key, stored_prefix, key_hash = APIKey.generate_key()
    with audit_context(user_id=user.pk, org_id=str(org.id) if org else None):
        api_key = APIKey.objects.create(
            user=user,
            org=org,
            prefix=stored_prefix,
            key_hash=key_hash,
            scopes=scopes,
            name=name,
            is_active=True,
        )
    return api_key, raw_key
```

**revoke() — org resolved from the key:**

```python
@classmethod
def revoke(cls, user, key_id: str) -> None:
    try:
        api_key = APIKey.objects.select_related("org").get(id=key_id, user=user)
    except APIKey.DoesNotExist:
        raise Http404 from None
    with audit_context(user_id=user.pk, org_id=str(api_key.org.id) if api_key.org_id else None):
        api_key.is_active = False
        api_key.save(update_fields=["is_active"])
```

**Note on `update_fields`:** pghistory tracks `UpdateEvent` on `save()`. Using `update_fields=["is_active"]` means only `is_active` changes are recorded — this is correct. The event label is `api_key.updated` (not revoked). The audit log query in `get_audit_log_page` filters by `pgh_label` — existing behavior unchanged.

### Pattern 6: Controller org Resolution (Plan 34-02)

**create_key — resolve org from slug:**

```python
# apps/api/apps/api_keys/controllers.py
def create_key(self, request: HttpRequest, body: APIKeyIn) -> Any:
    org = None
    if body.org_slug:
        from apps.orgs.models import Membership, Organization
        try:
            org = Organization.objects.get(slug=body.org_slug)
        except Organization.DoesNotExist:
            from ninja_extra.exceptions import NotFound
            raise NotFound()  # or Http404
        if not Membership.objects.filter(org=org, user=request.user).exists():
            from ninja_extra.exceptions import PermissionDenied
            raise PermissionDenied()
    api_key, raw_key = APIKeyService.create(
        user=request.user,
        name=body.name,
        scopes=body.scopes,
        org=org,
    )
    return 201, {
        ...
        "org_slug": org.slug if org else None,
    }
```

**Raise pattern:** Check what the project uses for 403/404 in other controllers. `Http404` from `django.http` is already used in `services.py`. For membership check, raising `PermissionDenied` (Django's) maps to 403. The planner should verify the existing orgs controller pattern.

### Anti-Patterns to Avoid

- **Adding OrgCustomer to billing/admin.py:** OrgCustomer lives in the `orgs` app — its admin belongs in `apps/orgs/admin.py` to avoid cross-app imports.
- **Wrapping audit_context in the controller:** Pattern from Phase 29 is service-layer injection. Controller layer doesn't know about org context for background tasks.
- **Using Heroicon names in UNFOLD sidebar:** They render as blank icons. Use Material Symbols names.
- **N+1 on org_slug in list_keys:** Access `k.org.slug` without `select_related("org")` causes one extra query per key. Add `select_related("org")` in `list_for_user()`.
- **Forgetting APIKeyCreateOut org_slug:** The create endpoint response should also include `org_slug` for consistency with `APIKeyOut`. Easy to miss since it's a separate schema class.

## Don't Hand-Roll

| Problem                  | Don't Build                                                      | Use Instead                                                                             | Why                                                                |
| ------------------------ | ---------------------------------------------------------------- | --------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| Audit context population | Custom signal or middleware hook for /me/ routes                 | `audit_context()` in service layer                                                      | Already exists; degrades gracefully in non-B2B mode                |
| Admin sidebar config     | New UNFOLD sidebar section                                       | Append to existing B2B items list                                                       | Sidebar structure already parsed correctly by unfold               |
| Org membership check     | Inline membership query in controller with custom error handling | Pattern from orgs controllers: `Membership.objects.filter(org=org, user=user).exists()` | Consistent with project patterns; same query shape used everywhere |

## Common Pitfalls

### Pitfall 1: Duplicate Import in orgs/admin.py

**What goes wrong:** Adding a new `from .models import OrgCustomer` statement when `Organization` and `Membership` are already imported from `.models`.
**Why it happens:** Easy to overlook that a single `from .models import ...` is already present.
**How to avoid:** Read the file first (confirmed: `from .models import Membership, Organization`). Extend the existing import to `from .models import Membership, OrgCustomer, Organization`.
**Warning signs:** `ImportError: cannot import name 'OrgCustomer' from 'apps.orgs.models'` would mean OrgCustomer was not in models (it is — confirmed).

### Pitfall 2: B2B_START/B2B_END Marker Placement

**What goes wrong:** Adding OrgCustomerAdmin code outside the B2B markers, or the sidebar entry outside the B2B block.
**Why it happens:** The existing B2B_END in orgs/admin.py is on line 26 (last line). New code added after it is not wrapped.
**How to avoid:** Place `OrgCustomerAdmin` registration INSIDE the existing `# B2B_START` / `# B2B_END` block in orgs/admin.py. The sidebar entry goes INSIDE the existing B2B navigation block in base.py.

### Pitfall 3: pghistory context not committed for /me/ routes

**What goes wrong:** Assuming `AuditContextMiddleware` sets `org_id` for `/me/api-keys/` routes.
**Why it happens:** `AuditContextMiddleware.get_context()` reads `request.org` — only set on `/{org_slug}/` routes by the `IsOrgMember` permission class. `/me/api-keys/` routes don't have this permission class.
**How to avoid:** Phase 34's approach is correct — inject `org_id` directly in the service layer via `audit_context()`. No middleware change needed.
**Warning signs:** Running the test `test_apikey_events_in_audit_log` without `audit_context()` wrapping — events appear but `org_id` is NULL in pgh_context, so `get_audit_log_page(org=org)` returns 0 items.

### Pitfall 4: Migration pghistory hash in detect-secrets baseline

**What goes wrong:** Migration files containing `hash=` strings (SHA-1 of trigger SQL) trigger detect-secrets.
**Why it happens:** Phase 29 documented this — pgtrigger migration fields contain hash= values.
**How to avoid:** Add `# pragma: allowlist secret` inline on the migration hash lines. This was established in Phase 29.

### Pitfall 5: N+1 on org_slug serialization in list_keys

**What goes wrong:** `list_keys` accesses `k.org.slug` for each result row without `select_related`, causing one extra SQL query per API key.
**Why it happens:** The FK `org_id` is set but `org` object is not fetched. Django defers FK traversal.
**How to avoid:** In `APIKeyService.list_for_user()`, change `APIKey.objects.filter(user=user)` to `APIKey.objects.filter(user=user).select_related("org")`.

### Pitfall 6: admin URL name for OrgCustomer

**What goes wrong:** Using `admin:orgs_org_customer_changelist` (wrong) instead of `admin:orgs_orgcustomer_changelist` (correct).
**Why it happens:** Django lowercases the model name as a single token (`orgcustomer`), not split by camelcase.
**How to avoid:** URL pattern is `admin:{app_label}_{model_name_lower}_changelist`. `OrgCustomer.__name__.lower()` = `orgcustomer`. Confirmed: `reverse_lazy("admin:orgs_orgcustomer_changelist")`.

## Code Examples

### Existing audit_context Usage (Phase 29 Pattern)

```python
# Source: apps/api/apps/audit/context.py
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

### Existing test that proves audit_context + APIKey works

```python
# Source: apps/api/tests/audit/test_controllers.py (test_apikey_events_in_audit_log)
with pghistory.context(user=org_admin.pk, org_id=str(org.id)):
    APIKey.objects.create(...)
items, _ = get_audit_log_page(org=org)
assert "api_key.created" in [item.action for item in items]
```

This test already passes — confirming the selector infrastructure works. Phase 34 just wires `audit_context()` into the service layer so the HTTP path achieves the same result.

### Existing UNFOLD B2B sidebar block (lines 523-556 in base.py)

```python
# B2B_START
{
    "title": "B2B",
    "separator": False,
    "collapsible": False,
    "items": [
        {"title": "Organizations", "icon": "business", "link": reverse_lazy("admin:orgs_organization_changelist")},
        {"title": "Memberships",   "icon": "people",   "link": reverse_lazy("admin:orgs_membership_changelist")},
        {"title": "API Keys",      "icon": "vpn_key",  "link": reverse_lazy("admin:api_keys_apikey_changelist")},
        {"title": "Webhooks",      "icon": "webhook",  "link": reverse_lazy("admin:webhooks_webhookendpoint_changelist")},
        {"title": "Audit Log",     "icon": "history",  "link": reverse_lazy("admin:audit_impersonationevent_changelist")},
        # ADD HERE:
        # {"title": "Org Billing", "icon": "receipt",  "link": reverse_lazy("admin:orgs_orgcustomer_changelist")},
    ],
},
# B2B_END
```

## State of the Art

| Old Approach                  | Current Approach                                          | When Changed            | Impact                                                               |
| ----------------------------- | --------------------------------------------------------- | ----------------------- | -------------------------------------------------------------------- |
| Middleware-only audit context | Service-layer `audit_context()` for non-org-scoped routes | Phase 29 (Celery tasks) | Enables correct org attribution for background/non-org-URL mutations |
| No admin for OrgCustomer      | Register `OrgCustomerAdmin` (Phase 34)                    | Now                     | Staff can inspect/correct per-org Stripe IDs without raw DB          |

## Open Questions

1. **Should `APIKeyCreateOut` also gain `org_slug`?**
   - What we know: `APIKeyOut` (list/management) is getting `org_slug`. `APIKeyCreateOut` is a separate schema class used only for the create response.
   - What's unclear: Spec says `APIKeyOut` gains the field; `APIKeyCreateOut` is not mentioned explicitly.
   - Recommendation: Yes — add `org_slug: str | None` to `APIKeyCreateOut` too. The create response is the first place a client sees which org the key belongs to. Consistent with the list schema.

2. **How should the controller signal a 403 for org membership check?**
   - What we know: `services.py` currently raises `Http404` for not-found. Orgs controllers use `Http404` for user not found.
   - What's unclear: The project doesn't have a consistent "403 from service" pattern — services raise 404, not 403.
   - Recommendation: Raise `PermissionDenied` (from `django.core.exceptions`) in the **controller** (not the service) after the membership check fails. This keeps the service unaware of HTTP semantics.

## Validation Architecture

### Test Framework

| Property           | Value                                                                |
| ------------------ | -------------------------------------------------------------------- |
| Framework          | pytest + pytest-django                                               |
| Config file        | `apps/api/pyproject.toml`                                            |
| Quick run command  | `cd apps/api && python -m pytest tests/admin/ tests/api_keys/ -x -q` |
| Full suite command | `cd apps/api && python -m pytest -x -q`                              |

### Phase Requirements → Test Map

| Req ID   | Behavior                                                                            | Test Type   | Automated Command                                             | File Exists?                                    |
| -------- | ----------------------------------------------------------------------------------- | ----------- | ------------------------------------------------------------- | ----------------------------------------------- |
| BILL-01  | `OrgCustomerAdmin` inherits `UnfoldModelAdmin`                                      | unit        | `pytest tests/admin/test_admin_smoke.py -x -q -k orgcustomer` | ❌ Wave 0 — add test to `test_admin_smoke.py`   |
| BILL-01  | `OrgCustomerAdmin` list_display has correct columns                                 | unit        | `pytest tests/admin/test_admin_smoke.py -x -q -k orgcustomer` | ❌ Wave 0                                       |
| BILL-01  | Sidebar link `admin:orgs_orgcustomer_changelist` resolves                           | unit        | `pytest tests/admin/test_unfold_config.py -x -q`              | ❌ Wave 0 — add test to `test_unfold_config.py` |
| AUDIT-01 | APIKey create event appears in org audit log after POST /me/api-keys/ with org_slug | integration | `pytest tests/api_keys/test_controllers.py -x -q -k audit`    | ❌ Wave 0                                       |
| AUDIT-01 | APIKey revoke event appears in org audit log after DELETE /me/api-keys/{id}/        | integration | `pytest tests/api_keys/test_controllers.py -x -q -k audit`    | ❌ Wave 0                                       |
| AUDIT-01 | `APIKeyOut` response includes `org_slug` field                                      | unit        | `pytest tests/api_keys/test_controllers.py -x -q`             | ✅ (modify existing `test_list_keys`)           |

### Sampling Rate

- **Per task commit:** `cd apps/api && python -m pytest tests/admin/ tests/api_keys/ -x -q`
- **Per wave merge:** `cd apps/api && python -m pytest -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/admin/test_admin_smoke.py` — add `test_org_customer_admin_inherits_unfold` and `test_org_customer_admin_list_display` for BILL-01
- [ ] `tests/admin/test_unfold_config.py` — add sidebar link test for `admin:orgs_orgcustomer_changelist` for BILL-01
- [ ] `tests/api_keys/test_controllers.py` — add audit log integration tests for AUDIT-01 (create + revoke emit events in org audit log)
- [ ] Migration `apps/api/apps/api_keys/migrations/0003_apikey_org.py` — generated via `makemigrations` in Wave 1

_(No new test files needed — existing test files cover all domains; tests are additions to existing files)_

## Sources

### Primary (HIGH confidence)

- Direct code inspection — `apps/api/apps/orgs/admin.py` — confirmed existing B2B_START/B2B_END markers, Organization/Membership pattern
- Direct code inspection — `apps/api/apps/billing/admin.py` — confirmed CustomerAdmin column shape used as reference
- Direct code inspection — `apps/api/apps/audit/context.py` — confirmed `audit_context()` signature and pghistory.context() wrapping
- Direct code inspection — `apps/api/apps/api_keys/models.py` — confirmed `@pghistory.track` decorator, field list, missing `org` FK
- Direct code inspection — `apps/api/apps/api_keys/services.py` — confirmed `create()`, `revoke()`, `list_for_user()` method signatures
- Direct code inspection — `apps/api/apps/api_keys/schemas.py` — confirmed `APIKeyIn`, `APIKeyOut`, `APIKeyCreateOut` schemas
- Direct code inspection — `apps/api/apps/api_keys/controllers.py` — confirmed `create_key`, `revoke_key`, `list_keys` method shapes
- Direct code inspection — `apps/api/config/settings/base.py` (lines 507–620) — confirmed UNFOLD sidebar B2B block structure and icon system
- Direct code inspection — `apps/api/apps/audit/middleware.py` — confirmed `AuditContextMiddleware` only reads `request.org` (not set for /me/ routes)
- Direct code inspection — `apps/api/apps/audit/selectors.py` — confirmed `get_audit_log_page()` filters by `pgh_context__org_id`
- Direct code inspection — `apps/api/tests/audit/test_controllers.py` — confirmed `test_apikey_events_in_audit_log` as proof the selector works when org context is injected
- Direct code inspection — `apps/api/tests/admin/test_admin_smoke.py` — confirmed test pattern for future OrgCustomerAdmin test

### Secondary (MEDIUM confidence)

- STATE.md Decisions log — Phase 29/30 decisions confirm pghistory 3.9.2, django-unfold, and Material Symbols icon system
- STATE.md — Phase 29 decision: `# pragma: allowlist secret` inline on migration hash fields

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — all libraries confirmed installed and in use from prior phases
- Architecture: HIGH — all patterns are direct copies/extensions of existing code; no new patterns introduced
- Pitfalls: HIGH — all pitfalls identified from direct code inspection and STATE.md decision log
- Test gaps: HIGH — all existing test files inspected; gaps are additions not new infrastructure

**Research date:** 2026-03-13
**Valid until:** 2026-04-13 (stable — no fast-moving dependencies)
