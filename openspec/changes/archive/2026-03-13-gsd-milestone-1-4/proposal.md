## Why

Milestone v1.4 (B2B Module) shipped an optional enterprise layer across phases 26–31 — organizations with team membership, per-org billing, outbound webhooks, API key authentication, audit logging, and an admin backoffice. All of this is behind a `--with b2b` scaffolder flag so solo/B2C products don't carry the overhead. These capabilities have no OpenSpec specs yet; the implementation decisions and patterns need to be documented so scaffolded products start from accurate, self-contained specs.

## What Changes

- New: Organization model, membership, roles, invitation flow, ownership transfer (ORG-01–05)
- New: Per-org Stripe billing with org-level entitlement resolution and `has_org_feature()` (BILL-01–02)
- New: Outbound webhook registry with HMAC-signed Celery delivery, backoff, circuit breaker (HOOK-01–04)
- New: API key authentication with SHA-256 hash storage, scopes, rate limiting, usage tracking (AKEY-01–03)
- New: Automatic audit logging via pghistory triggers with org-scoped read API (AUDIT-01–02)
- New: Admin backoffice with django-unfold theme and django-hijack impersonation (ADMIN-01–02)
- Modified: CLI scaffolder gains `--with b2b` flag with B2B_START/B2B_END markers (SCAFF-01)

## Capabilities

### New Capabilities

- `organization-model`: Organizations, team membership (owner/admin/member roles), email invitations (72h expiry), ownership transfer, cross-org access enforcement, per-org Stripe billing, `has_org_feature()` org-level entitlement resolution
- `outbound-webhooks`: Webhook endpoint registry, HMAC-SHA256 signed deliveries via Celery, exponential backoff (7 retries), delivery history, manual retry, auto-disable circuit breaker with admin email notification
- `api-key-authentication`: API key create/revoke with scopes, raw key shown once at creation, prefix + SHA-256 hash storage, `RequireScope` permission class, per-key rate limiting, `last_used_at` / `usage_count` tracking
- `audit-logging`: pghistory triggers on Organization/Membership/APIKey/WebhookEndpoint models, AuditContextMiddleware for automatic actor+org context, org-scoped paginated audit log API, impersonation entry visibility rules
- `admin-backoffice`: django-unfold theme across all ModelAdmins, navigation sidebar with B2B sections, django-hijack staff impersonation, impersonation banner, audit log integration

### Modified Capabilities

- `cli-scaffolder`: Add `--with b2b` flag (opt-in, not default); all B2B code fenced with `# B2B_START` / `# B2B_END` markers; `removeb2bModule()` strips all B2B artifacts cleanly; `manage.py check` passes post-removal

## Impact

- `openspec/specs/organization-model/` — new spec (does not exist)
- `openspec/specs/outbound-webhooks/` — new spec (does not exist)
- `openspec/specs/api-key-authentication/` — new spec (does not exist)
- `openspec/specs/audit-logging/` — new spec (does not exist)
- `openspec/specs/admin-backoffice/` — new spec (does not exist)
- `openspec/specs/cli-scaffolder/spec.md` — existing spec, `--with b2b` requirement added
- No application code changes — documentation sync only
