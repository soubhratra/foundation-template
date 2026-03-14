# Phase 34: Admin + Audit Context Fixes - Context

**Gathered:** 2026-03-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Two targeted gap-closure fixes:

1. Register `OrgCustomerAdmin` so staff can inspect per-org Stripe billing records in the django-unfold admin without raw DB queries.
2. Add an `org` FK to `APIKey` and inject `org_id` into pghistory context during create/revoke operations so APIKey events appear in the org audit log.

Not in scope: new audit log endpoints, APIKey scope redesign, org-level key management endpoints, read-only mode for OrgCustomerAdmin, filtering /me/api-keys/ by org.

</domain>

<decisions>
## Implementation Decisions

### OrgCustomerAdmin — location and shape

- **File:** `apps/orgs/admin.py` — co-located with the model (`apps/orgs/models.py`). No cross-app imports required.
- **Columns:** `list_display = ("org", "stripe_customer_id", "created_at")` — matches the shape of `CustomerAdmin` in `apps/billing/admin.py`; the three fields that matter for staff support.
- **Search:** `search_fields = ("org__name", "org__slug", "stripe_customer_id")`
- **Read-only fields:** `readonly_fields = ("created_at", "updated_at")` — timestamps are auto-set; `stripe_customer_id` is editable so staff can manually correct it after a Stripe migration or org re-billing setup.
- **Permissions:** Fully editable — not read-only. Matches how `CustomerAdmin` (billing) works; support workflows need the ability to correct `stripe_customer_id`.
- **Sidebar placement:** B2B section, appended after Audit Log. `OrgCustomer` is B2B infrastructure, not user billing. Sidebar order: Organizations, Memberships, API Keys, Webhooks, Audit Log, **Org Billing**.
- **B2B markers:** `OrgCustomerAdmin` registration and its `OrgCustomer` import wrapped in `B2B_START`/`B2B_END` inside `apps/orgs/admin.py`. The Org Billing entry in the UNFOLD sidebar B2B section also wrapped.

### APIKey org FK (schema change)

- Add `org = models.ForeignKey("orgs.Organization", on_delete=models.SET_NULL, null=True, blank=True, related_name="api_keys")` to `APIKey`.
- Migration required — nullable, so no data migration needed; existing keys get `org=None`.
- This makes API keys org-scoped when explicitly associated with an org, and personal (org=None) when not.

### Create endpoint — org association

- `POST /api/v1/me/api-keys/` request body gains an optional `org_slug: str | None` field in `APIKeyIn` schema.
- `APIKeyService.create()` accepts `org: Organization | None`. When `org_slug` is provided, the service resolves the org and verifies the user is a member (raise 403 if not).
- The resolved `org` is stored on the APIKey and used for `audit_context()` injection.
- Existing callers omitting `org_slug` continue to work — personal keys stay personal (org=None).

### Audit context injection — service layer

- `APIKeyService.create()` and `APIKeyService.revoke()` wrap their DB mutations in:

  ```python
  from apps.audit.context import audit_context

  with audit_context(user_id=user.pk, org_id=str(org.id) if org else None):
      APIKey.objects.create(...)  # or api_key.save(...)
  ```

- Injection happens in the **service layer**, not the controller or middleware — consistent with Phase 29's pattern for Celery tasks. Reusable if the service is called from background tasks later.
- When `org` is None, `audit_context` is called with `org_id=None` (same as current middleware behavior for /me/ routes).

### List endpoint — no org filter

- `GET /api/v1/me/api-keys/` returns all keys owned by the user regardless of org — existing behavior unchanged.
- No `?org_slug=` filter in Phase 34. Multi-org filtering is a future follow-up if needed.

### APIKeyOut schema update

- `APIKeyOut` gains an optional `org_slug: str | None` field so clients can see which org a key is scoped to.
- When `org` is None, `org_slug` is null in the response.

### Claude's Discretion

- Whether `org_slug` or `org_id` (UUID) is exposed in `APIKeyOut` — prefer `org_slug` for human readability.
- Exact field order in `APIKeyIn` schema.
- Index strategy for the new `org` FK on `APIKey` (Django default index is fine; composite index is not needed for Phase 34 query patterns).

</decisions>

<code_context>

## Existing Code Insights

### Reusable Assets

- `apps/orgs/admin.py` (`OrganizationAdmin`, `MembershipAdmin`): Direct pattern for `OrgCustomerAdmin` — same `UnfoldModelAdmin` base, same `list_display`/`search_fields` shape. Import `OrgCustomer` from `.models` in the same file.
- `apps/billing/admin.py` (`CustomerAdmin`): Reference for OrgCustomerAdmin columns — `("user", "stripe_customer_id", "created_at")` maps to `("org", "stripe_customer_id", "created_at")`.
- `apps/audit/context.py` (`audit_context`): Ready to use. `with audit_context(user_id=..., org_id=...)` in service layer — no new infrastructure needed.
- `apps/api_keys/services.py` (`APIKeyService.create`, `APIKeyService.revoke`): The two methods that need `audit_context()` wrapping. `create` also gains `org` parameter.
- `apps/api_keys/schemas.py` (`APIKeyIn`, `APIKeyOut`): `APIKeyIn` gains `org_slug: str | None = None`; `APIKeyOut` gains `org_slug: str | None`. # pragma: allowlist secret

### Established Patterns

- `B2B_START`/`B2B_END` markers in `apps/orgs/admin.py`: Already present wrapping Organization/Membership admins — add OrgCustomer inside the same markers.
- UNFOLD sidebar config in `config/settings/base.py`: B2B section list needs `OrgCustomer` entry with Heroicon, wrapped in `B2B_START`/`B2B_END`.
- Service-layer `audit_context()` usage: Pattern established in Phase 29 for Celery tasks; applying the same pattern in `APIKeyService` is the correct extension.

### Integration Points

- `apps/api_keys/models.py` → add `org` FK, run `makemigrations`
- `apps/api_keys/schemas.py` → update `APIKeyIn` and `APIKeyOut`
- `apps/api_keys/services.py` → `create()` gains `org` param + `audit_context()` wrap; `revoke()` gains `audit_context()` wrap
- `apps/api_keys/controllers.py` → `create_key` passes `org_slug` to service; `revoke` resolves org from key for context
- `apps/orgs/admin.py` → add `OrgCustomerAdmin` registration
- `config/settings/base.py` (UNFOLD sidebar) → add Org Billing entry to B2B section

</code_context>

<specifics>
## Specific Ideas

- `OrgCustomerAdmin` is a direct parallel to `CustomerAdmin` in billing — keep the column shape consistent so staff has a predictable mental model across both.
- The `org_slug` in `APIKeyIn` is optional (None = personal key) — no breaking change to existing API consumers who don't send it.
- `audit_context()` in the service is the right place so it works for Celery tasks too, not just HTTP requests — future-proofing.

</specifics>

<deferred>
## Deferred Ideas

- `?org_slug=` filter on `GET /api/v1/me/api-keys/` for multi-org users — future follow-up
- Org-scoped API key endpoint (`POST /api/v1/org/{slug}/api-keys/`) — separate phase if needed
- Read-only mode for OrgCustomerAdmin — not needed; staff legitimately needs to correct Stripe IDs

</deferred>

---

_Phase: 34-admin-audit-context-fixes_
_Context gathered: 2026-03-13_
