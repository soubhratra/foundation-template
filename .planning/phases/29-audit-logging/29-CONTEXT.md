# Phase 29: Audit Logging - Context

**Gathered:** 2026-03-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Every significant change to four B2B models (Organization, Membership, APIKey, WebhookEndpoint) is recorded automatically via PostgreSQL triggers with full actor and org context. Org owners and admins can query a paginated, filterable audit trail for their organization via REST API. Impersonation activity is stored but hidden from org-level queries.

Not in scope: per-field diff exposure in the API (stored internally, not returned), external audit log shipping (Splunk/Datadog), audit logging for Invitation model, audit log admin UI.

</domain>

<decisions>
## Implementation Decisions

### Audit entry response schema

- **Summary-only response** — no raw before/after diffs in `AuditEntryOut`; pghistory stores full row snapshots internally but Phase 29 does not expose them; diff endpoint is a future phase
- **Actor fields:** both `actor_id` (UUID) and `actor_email` in every entry; both become `null` if the actor was later deleted — no FK constraint on audit entries referencing users
- **Object identification:** `model_name` (e.g. `"Organization"`) + `object_id` (UUID/PK) — generic across all 4 tracked models; no `object_repr` in Phase 29
- **Timestamp:** ISO 8601 UTC string
- **Impersonator field:** stored in pghistory context JSON but excluded from `AuditEntryOut`; never serialised for org-level callers; staff-only (future phase)
- Minimum `AuditEntryOut` fields: `id`, `timestamp`, `action` (e.g. `org.updated`), `model_name`, `object_id`, `actor_id`, `actor_email`, `url`

### Org context resolution

- **URL-first, then null:** `AuditContextMiddleware` extracts `org_id` from the URL path if a `/org/{slug}/` segment is present; for non-org URLs (e.g. `/me/api-keys/`) `org_id` is set to `null` in context — API keys are user-owned (Phase 28), so null org context is correct
- **Unauthenticated requests:** both `user_id` and `org_id` are `null` in context; triggers still fire, context is just anonymous — no errors thrown
- **Middleware placement:** after `SessionMiddleware` and Django's `AuthenticationMiddleware` so `request.user` is already resolved at context-binding time; before any view-level middleware

### Task / Celery context API

- **API:** `audit_context(user_id, org_id)` — a context manager in `apps/audit/context.py`

  ```python
  from apps.audit.context import audit_context

  @app.task
  def provision_org(user_id, org_id):
      with audit_context(user_id=user_id, org_id=org_id):
          org.is_active = True
          org.save()
  ```

- **Location:** `apps/audit/context.py` — follows the `apps.webhooks.utils.fire_webhook_event()` pattern of a thin utility in the owning app
- **Graceful degradation:** `audit_context()` is a no-op context manager when `pghistory` is not in `INSTALLED_APPS` (non-B2B scaffolded projects); product code does not need conditional imports or try/except

### Filtering interface

- **Query params** (all optional, combinable): `actor_id` (UUID exact match), `from` (ISO 8601 datetime), `to` (ISO 8601 datetime), `action` (exact string match, e.g. `org.updated`)
- **Pagination:** cursor-based; default `page_size=50`, max 200; stable for append-only logs — offset pagination would break when new entries are inserted mid-query
- **Default sort:** newest first (`ORDER BY timestamp DESC`)

### Claude's Discretion

- Whether to use `pghistory.models.MiddlewareEvents` or a custom proxy model for the query layer — recommend `MiddlewareEvents` unless extra ProxyFields beyond `user`/`url` are needed
- Exact cursor implementation (use existing cursor pagination helper from codebase if present; otherwise implement per-field cursor on `timestamp` + `id`)
- DB index strategy on event tables for org-scoped + timestamp queries
- Exact `AuditConfig` app label and `apps.py` content
- Whether to expose `url` in `AuditEntryOut` or treat it as internal only

</decisions>

<specifics>
## Specific Ideas

- `audit_context()` is the developer-facing name — analogous to `pghistory.context()` but adds `org_id` support; product developers import and use it without knowing pghistory internals
- The "summary-only" decision means `AuditEntryOut` is intentionally lean for Phase 29 — if products need diffs, they extend `AuditEntryOut` or add a `/audit-log/{id}/diff` endpoint in their own codebase; the template ships the foundation, not the full feature
- No-op `audit_context()` is important for scaffolder cleanliness: product code that wraps task bodies with `audit_context()` should survive B2B removal without code changes

</specifics>

<code_context>

## Existing Code Insights

### Reusable Assets

- `apps/accounts/permissions.py` (`RequireRole`): Direct template for `IsOrgAdmin` permission gate on the audit log endpoint — same `BasePermission` shape
- `apps/orgs/permissions.py` (`IsOrgMember`, `IsOrgAdmin`): Permission composition pattern — `AuditLogController` uses `IsOrgAdmin` as its permission gate
- `apps/orgs/models.py` (Organization, Membership): These two models receive `@pghistory.track()` decorators in-place; no new model files created
- `apps/api_keys/models.py` (APIKey): Receives `@pghistory.track()` in-place
- `apps/webhooks/models.py` (WebhookEndpoint): Receives `@pghistory.track()` in-place

### Established Patterns

- Settings-based catalog (`WEBHOOK_EVENTS`, `BILLING_PLANS`, `API_KEY_SCOPES`): No equivalent catalog needed for audit events — event labels are defined inline at `@pghistory.track()` decorator; no settings dict required
- New app per domain (`apps/orgs/`, `apps/webhooks/`, `apps/api_keys/`): `apps/audit/` follows the same pattern
- B2B_START/B2B_END markers: All new middleware, INSTALLED_APPS entries, settings additions, and `apps/audit/` code must be wrapped

### Integration Points

- `apps/orgs/models.py` — add `@pghistory.track()` to `Organization` and `Membership`
- `apps/api_keys/models.py` — add `@pghistory.track()` to `APIKey`
- `apps/webhooks/models.py` — add `@pghistory.track()` to `WebhookEndpoint`
- `settings/base.py` — add `pghistory` + `pgtrigger` to `INSTALLED_APPS` (B2B_START/B2B_END); add `AuditContextMiddleware` after `AuthenticationMiddleware`
- API router config — register `AuditLogController` under `/api/v1/org/{slug}/audit-log`
- `requirements/base.txt` or `pyproject.toml` — `uv add django-pghistory`

</code_context>

<deferred>
## Deferred Ideas

- AUDIT-F01: External audit log shipping (Splunk, Datadog Logs) — template provides foundation; products add exporters
- Per-field diff exposure (`before`/`after` JSON in API) — stored by pghistory, not exposed in Phase 29; add `/audit-log/{id}/diff` endpoint in product-specific code if needed
- Audit logging for `Invitation` model — not in AUDIT-01 requirements; add in product code if needed
- `object_repr` (human-readable object name) in `AuditEntryOut` — skipped to avoid FK lookups on potentially-deleted objects; add in product code if needed
- Action prefix matching (e.g. `?action=org.` matches all org events) — start exact-match, add in a future phase

</deferred>

---

_Phase: 29-audit-logging_
_Context gathered: 2026-03-13_
