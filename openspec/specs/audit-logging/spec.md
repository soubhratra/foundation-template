## Requirements

### Requirement: Automatic Audit Logging via pghistory Triggers

The system SHALL automatically record changes to four B2B models (`Organization`, `Membership`, `APIKey`, `WebhookEndpoint`) via PostgreSQL triggers with no manual logging call required in application code.

#### Scenario: Model change writes audit entry automatically

- **WHEN** an `Organization`, `Membership`, `APIKey`, or `WebhookEndpoint` record is created, updated, or deleted
- **THEN** a pghistory event record SHALL be written automatically via PostgreSQL trigger
- **AND** no explicit `AuditLog.objects.create()` call SHALL be required in application code

#### Scenario: Audit entry includes actor and org context

- **WHEN** an audit entry is written for a request in `AuditContextMiddleware`'s scope
- **THEN** the entry SHALL include the acting user's id and email
- **AND** the entry SHALL include the org id if derived from the URL path (`/org/{slug}/...`)
- **AND** the entry SHALL include the request URL

#### Scenario: Celery task writes audit entry with explicit context

- **WHEN** a Celery task wraps its logic in `audit_context(user_id=..., org_id=...)`
- **THEN** audit entries written within the context manager SHALL include the provided user and org context
- **AND** the context manager SHALL be a no-op when pghistory is not in `INSTALLED_APPS`

#### Scenario: Unauthenticated requests produce null-actor entries

- **WHEN** an unauthenticated request triggers a model change
- **THEN** `actor_id` and `org_id` in the audit entry SHALL be `null`
- **AND** no error SHALL be raised

### Requirement: Org-Scoped Audit Log Read API

Org owners and admins SHALL be able to query a paginated, filterable audit log for their organization.

#### Scenario: Org admin queries audit log

- **WHEN** an org owner or admin calls `GET /api/v1/org/{slug}/audit-log`
- **THEN** the response SHALL return a cursor-paginated list of audit entries for that org
- **AND** each entry SHALL include: `id`, `timestamp`, `action`, `model_name`, `object_id`, `actor_id`, `actor_email`, `url`
- **AND** entries SHALL be ordered newest first (`timestamp DESC`)

#### Scenario: Audit log filtered by actor

- **WHEN** `GET /api/v1/org/{slug}/audit-log?actor_id=42` is called
- **THEN** only entries where `actor_id = 42` SHALL be returned

#### Scenario: Audit log filtered by date range

- **WHEN** `GET /api/v1/org/{slug}/audit-log?from=2026-01-01T00:00:00Z&to=2026-02-01T00:00:00Z` is called
- **THEN** only entries with `timestamp` within the range SHALL be returned

#### Scenario: Audit log filtered by action

- **WHEN** `GET /api/v1/org/{slug}/audit-log?action=org.updated` is called
- **THEN** only entries matching that action string exactly SHALL be returned

#### Scenario: Impersonation entries hidden from org-level queries

- **WHEN** an org admin queries the audit log
- **THEN** entries where `impersonator` is populated SHALL NOT be returned
- **AND** impersonation audit entries SHALL only be visible to staff via the admin interface

### Requirement: AuditContextMiddleware

The system SHALL automatically attach user and org context to pghistory for all HTTP requests without requiring controller-level code.

#### Scenario: Middleware attaches context for org-scoped requests

- **WHEN** an HTTP request to `/api/v1/org/{slug}/...` is processed
- **THEN** `AuditContextMiddleware` SHALL extract the org from the URL and set it in pghistory context
- **AND** this SHALL occur after `AuthenticationMiddleware` so `request.user` is already resolved

#### Scenario: Middleware attaches null org context for non-org requests

- **WHEN** an HTTP request to `/api/v1/me/...` or other non-org URL is processed
- **THEN** `AuditContextMiddleware` SHALL set `org_id = null` in pghistory context
- **AND** no error SHALL be raised

## Implementation Decisions

### Why pghistory triggers (not application-layer logging)

PostgreSQL triggers fire at the database level regardless of how the write occurs — ORM, raw SQL, admin actions, and Celery tasks all produce audit entries without any callsite changes. Application-layer logging (e.g., `post_save` signals) can be bypassed by `bulk_update()`, raw SQL, or missing signal connections.

**Alternative rejected:** `django-simple-history` — stores history in a shadow table per model, requires per-model opt-in, and doesn't provide the pghistory middleware context system.

### Why only 4 models are tracked (not all models)

`Organization`, `Membership`, `APIKey`, `WebhookEndpoint` are the models org admins have operational interest in. Tracking all models (including billing, auth, etc.) would produce excessive volume that obscures relevant audit events. Products with stricter compliance needs can extend pghistory tracking to additional models.

### Why `AuditEntryOut` is summary-only (no before/after diffs)

pghistory stores full row snapshots internally, but exposing raw before/after diffs in the API requires careful schema design to avoid leaking sensitive fields (e.g., `APIKey.key_hash`). Summary-only (`action`, `model_name`, `object_id`, `actor_*`) covers the common audit query patterns (who changed what and when). A diff endpoint is a future phase.

### Why cursor pagination (not offset pagination)

The audit log is append-only. Offset pagination produces inconsistent results when new entries are inserted mid-query (page 2 shifts to include entries that were on page 1 when it was fetched). Cursor pagination on `(timestamp DESC, id DESC)` is stable regardless of new inserts. Default page size 50, max 200.

### Why `audit_context()` is a no-op when pghistory is absent

Product code that wraps Celery task bodies with `audit_context()` should survive `--without b2b` scaffolder removal without requiring conditional imports or try/except blocks. The no-op behaviour means developers can adopt the context manager pattern in their task bodies without coupling task code to the B2B module's presence.

### Why actor fields (`actor_id`, `actor_email`) are nullable without FK constraints

An FK constraint on audit entries referencing `User.pk` would prevent deleting users whose actions are in the audit log — a GDPR conflict (right to erasure vs audit retention). Storing `actor_id` and `actor_email` as plain nullable fields allows user deletion to proceed without cascade-deleting audit history. Both fields become `null` after the actor is deleted.

### Why org context is derived from the URL path (not a request header or body)

URL-based org resolution is the canonical approach in this codebase — `IsOrgMember` resolves the org from `org_slug` in `request.resolver_match.kwargs`, and `AuditContextMiddleware` follows the same approach. Headers and body fields are mutable by clients and inappropriate for security-sensitive context.
