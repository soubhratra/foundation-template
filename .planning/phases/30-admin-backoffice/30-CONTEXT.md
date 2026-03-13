# Phase 30: Admin Backoffice - Context

**Gathered:** 2026-03-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Staff users get a polished django-unfold admin interface for customer support, with django-hijack impersonation restricted to non-staff/non-superuser accounts. Every impersonation start and end event is permanently recorded in AuditLog with the `impersonator` FK populated. All existing ModelAdmins are converted to `UnfoldModelAdmin`.

Not in scope: custom unfold widgets, custom admin actions beyond impersonation, mobile admin responsiveness tuning, external audit log shipping.

</domain>

<decisions>
## Implementation Decisions

### Sidebar navigation structure

- **Flat B2B section** — one "B2B" section grouping all B2B models: Organizations, Memberships, API Keys, Webhooks, Audit Log
- **All sections configured** — UNFOLD sidebar defines all sections: B2B, Users & Auth, Billing, System (Celery beat/results if installed). Staff gets a complete organized sidebar from day one — no ungrouped default list
- **Icons** — Heroicons (outline style) for section headers and model items; django-unfold ships with Heroicons natively
- **Config location** — `UNFOLD = {...}` dict defined inline in `config/settings/base.py`, consistent with SIMPLE*JWT, CELERY*\*, and other third-party configs in this codebase
- Sidebar structure:

  ```
  B2B
    Organizations
    Memberships
    API Keys
    Webhooks
    Audit Log

  Users & Auth
    Users

  Billing
    Customers
    Subscriptions
    Payments
    Plan Provider Mappings
    Processed Webhook Events

  System
    Periodic Tasks (Celery Beat)
    Task Results (Celery Results)
  ```

### ModelAdmin scope

- **Functional but lean** — each domain ModelAdmin gets list_display (4-5 most useful columns), list_filter for status/type fields, search_fields on name/email/identifier. No inlines, no custom actions beyond impersonation
- **One admin.py per app** — `apps/orgs/admin.py`, `apps/api_keys/admin.py`, `apps/webhooks/admin.py`, `apps/audit/admin.py`. New files following the existing per-domain pattern
- **All existing admins converted** — `apps/billing/admin.py` and `apps/accounts/admin.py` updated to inherit from `UnfoldModelAdmin`. Success criteria requires all existing domain ModelAdmins to use UnfoldModelAdmin

### Impersonation UX

- **Trigger: user detail page only** — Impersonate button on the User change page (`/admin/accounts/user/{id}/change/`). Intentional friction prevents accidental impersonation — staff must navigate to a specific user first
- **Banner: django-hijack default** — Use hijack's built-in banner injection (`HIJACK_INSERT_BEFORE`). Contains impersonated user info + "Release" button. No custom template needed
- **Trigger: admin-initiated only** — Staff must initiate from `/admin/`. `HIJACK_PERMISSION_CHECK` ensures only staff can trigger impersonation. After start, staff lands on the main web app as the impersonated user
- **Post-release redirect** — `HIJACK_LOGOUT_REDIRECT_URL` points back to the impersonated user's admin change page. Staff is returned to the admin context they came from — natural for support workflows
- **Restriction** — Cannot impersonate staff users or superusers (enforced by django-hijack's `can_be_hijacked` check + custom permission)

### Staff audit log view (admin)

- **Columns:** `timestamp`, `action`, `actor_email`, `model_name`, `object_id`, `impersonator_email` — impersonator surfaced directly in list view for at-a-glance identification of impersonation-triggered events
- **Read-only enforcement:** `has_add_permission`, `has_change_permission`, `has_delete_permission` all return `False` — audit logs are an immutable record; no staff can add, edit, or delete entries
- **Filters:** `action` (exact), `model_name` (exact), and a custom `HasImpersonatorFilter` boolean filter — covers the most common staff queries; impersonation events filterable without manual search
- **Search fields:** `actor_email`, `object_id` — basic lookup by who made the change and what object was affected

### Claude's Discretion

- Exact Heroicon name choices per model/section (use contextually appropriate icons)
- Whether `impersonator_email` is a computed `list_display` column derived from `impersonator_id` FK lookup or stored directly
- Exact `can_be_hijacked` permission check implementation (inline in `accounts/admin.py` vs standalone function)
- System section contents — include/exclude based on which Celery apps are installed at build time

</decisions>

<specifics>
## Specific Ideas

- The sidebar "B2B" section wraps all B2B models — consistent with B2B_START/B2B_END marker strategy; section config in settings must also be wrapped so non-B2B scaffolds get a clean admin
- `UNFOLD` dict in `base.py` uses B2B_START/B2B_END around the B2B section items specifically, not the entire UNFOLD dict (which is needed for the non-B2B theme too)
- Post-release redirect to user detail page: hijack provides `HIJACK_LOGOUT_REDIRECT_URL` — use a callable or template string that resolves to `/admin/accounts/user/{user_id}/change/`

</specifics>

<code_context>

## Existing Code Insights

### Reusable Assets

- `apps/billing/admin.py`: 5 existing `admin.ModelAdmin` subclasses — direct conversion target for `UnfoldModelAdmin`; list_display patterns can be reused as reference for B2B admin scope
- `apps/accounts/admin.py`: bare `UserAdmin` — needs `UnfoldModelAdmin` + impersonation button; hijack provides a mixin (`HijackUserAdminMixin`) that adds the button
- Phase 29 `AuditLog` model (apps/audit/): has `timestamp`, `action`, `actor_id`, `actor_email`, `model_name`, `object_id`, `impersonator_id` fields — all needed columns already exist

### Established Patterns

- Per-domain app structure (`apps/orgs/`, `apps/api_keys/`, `apps/webhooks/`): new `admin.py` files follow the same pattern
- `config/settings/base.py` third-party config dicts (SIMPLE*JWT, CELERY*\*): `UNFOLD = {...}` follows the same inline pattern
- B2B_START/B2B_END markers: all new B2B ModelAdmin registrations, the B2B sidebar section in UNFOLD config, and `apps/audit/admin.py` must be wrapped

### Integration Points

- `django.contrib.admin` in INSTALLED_APPS → replace with `unfold.admin` (unfold requires its app before `django.contrib.admin`)
- `apps/accounts/admin.py` → add `HijackUserAdminMixin` + impersonation button on change page
- `config/settings/base.py` → add `UNFOLD = {...}` + `hijack` to INSTALLED_APPS (B2B_START/B2B_END for hijack)
- `config/urls.py` → include `hijack.urls` (required by django-hijack)
- `apps/audit/admin.py` → new file, wrapped in B2B_START/B2B_END

</code_context>

<deferred>
## Deferred Ideas

- Custom unfold banner template matching unfold theme colors — template work not worth the effort at this stage; default hijack banner works fine
- Inlines (e.g. Memberships inline under Organization) — functional-but-lean scope decision; add in product code if needed
- GDPR erasure / superuser-only audit log deletion — immutable record is the right default; products that need erasure add it themselves
- Action prefix matching filter in audit log admin (e.g. filter all `org.*` events) — exact match is sufficient for Phase 30

</deferred>

---

_Phase: 30-admin-backoffice_
_Context gathered: 2026-03-13_
