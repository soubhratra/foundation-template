# Project Research Summary

**Project:** Foundation Template — v1.4 B2B Module
**Domain:** B2B SaaS infrastructure — organizations, outbound webhooks, API keys, audit logging, admin backoffice
**Researched:** 2026-03-12
**Confidence:** HIGH

## Executive Summary

The v1.4 milestone adds a complete B2B layer to an existing full-stack SaaS template that already ships auth, billing, observability, RBAC, rate limiting, Celery, and Redis. Research confirms all five feature areas (organization model, outbound webhooks, API keys, audit logging, admin backoffice) follow well-established patterns in the Django ecosystem and can be delivered with only three net-new Python packages: `django-pghistory` (trigger-based audit), `django-unfold` (admin theme), and `django-hijack` (impersonation). Organization model, API key model, and webhook delivery infrastructure are custom code using the existing stack — no additional library dependencies are warranted. The module is designed as an opt-in `--with b2b` scaffolder block with clean removal boundaries, so products not requiring B2B can exclude the entire feature set.

The recommended implementation order is strict: Organization model must come first because every other B2B feature depends on it as a foreign key target. Within the organization phase, the billing entitlement resolution path (`_resolve_plan_id`) must be updated to prefer org plans over personal plans — failing to do this in the same phase creates a subtle integration gap where org members resolve entitlements against their personal subscription. Outbound webhooks and API keys are independent of each other and can be delivered in either order, but both must reference the Organization model established in phase 1. Audit logging is a cross-cutting concern applied via `@pghistory.track()` decorators on models created in preceding phases. Admin backoffice (unfold + hijack) is last because it depends on `AuditLog.impersonator` being present before django-hijack is enabled.

The two most dangerous pitfalls are billing attachment (org billing silently reading from the wrong Customer if `_resolve_plan_id` is not updated atomically with the org model) and API key security (plaintext storage or timing-unsafe comparison — no migration path exists from insecure to secure once keys are issued). Tenant isolation is the third critical invariant: every service method operating on org-scoped resources must validate membership before any ORM query. Getting isolation wrong requires a full endpoint audit and risks GDPR Article 33 notification obligations if personal data crossed org boundaries.

## Key Findings

### Recommended Stack

The full prior stack is non-negotiable per CLAUDE.md. This research covers only net-new additions for v1.4. Three new Python packages are required; zero new JS/TS or mobile packages are needed.

**Core technologies (net-new for v1.4):**

- `django-pghistory >=3.9,<4`: trigger-based audit logging — preferred over signal-based `django-auditlog` because PostgreSQL triggers capture bulk ORM operations and raw SQL that Django signals miss entirely; this gap is unacceptable in a compliance audit trail
- `django-unfold >=0.83,<1`: Tailwind-based Django admin theme — officially recommended by the Django project (Django blog, April 2025); wraps standard `django.contrib.admin` with no model migrations required; requires Python 3.11+
- `django-hijack >=3.7,<4`: customer support impersonation — CSRF-protected POST-only, shows a persistent banner, 64K weekly downloads; preferred over `django-impersonate` (lower adoption, less active maintenance cadence)

**Rejected libraries with rationale:**

- `django-organizations`: fixed binary `is_admin` role model incompatible with owner/admin/member requirements; ships unused view layer; complicates CLI scaffolder removal
- `djangorestframework-api-key`: DRF-specific `BasePermission` — incompatible with Django Ninja Extra's auth model; no scope support
- `django-webhook`: wrong delivery model (ORM-change trigger, not registry-based); pre-release `0.0.x`; stale since August 2024
- `django-pgaudit`: does not exist on PyPI (404 confirmed); the real `pgaudit` is a Postgres server extension with no Django request context and requires log-parsing infrastructure

### Expected Features

**Must have (table stakes — all P1 for v1.4):**

- Organization model + membership + owner/admin/member roles — the core B2B primitive; first member becomes owner; exactly one owner per org at all times
- Member invitation via email with token expiry — invite tokens expire at 72h; accepted by new signup or existing user login
- Per-org Stripe billing — `OrgCustomer` model parallel to existing `Customer`; `_resolve_plan_id` updated to check org plan before personal plan; entitlement cache invalidated for all org members on subscription update
- Outbound webhook registry with HMAC-SHA256 signing — developer table stakes; Stripe-compatible signature format; `X-Webhook-Timestamp` replay prevention
- Webhook delivery log with exponential backoff retry — `WebhookDelivery` model with status, attempt count, response code; dead-endpoint circuit breaker after N failures
- API key create/revoke with scopes — prefix + SHA-256 hash stored; raw key shown once at creation only; scope strings validated per-request
- Per-key rate limiting via Redis — existing `django-ratelimit` callable `key=` reused; `X-RateLimit-*` response headers
- Audit logging write side — `@pghistory.track()` on Organization, Membership, APIKey, WebhookEndpoint; pghistory middleware attaches user + request URL automatically
- Audit log org-scoped read API — paginated, filterable by actor/date/action; accessible to org owner and admin roles only; does not expose impersonation entries to org admins
- Admin backoffice via django-unfold — drop-in theme; `UnfoldModelAdmin` subclassing; `unfold` must appear before `django.contrib.admin` in INSTALLED_APPS
- Customer support impersonation via django-hijack — restricted to `is_staff`; CSRF-protected; impersonation events wired to AuditLog; banner always enabled

**Should have (differentiators vs. competing templates):**

- `--with b2b` CLI scaffolder flag — clean opt-in matching existing scaffolder patterns; all B2B code wrapped in `# B2B_START` / `# B2B_END` markers
- Per-key API rate limiting with `X-RateLimit-*` headers — most templates rate-limit by IP only; per-key enables tiered API plans
- API key usage tracking (`last_used_at`, `usage_count`) — feeds metered billing if enabled
- Webhook manual retry button — `POST /api/v1/webhooks/deliveries/{id}/retry`; eliminates "resend from scratch" workflow
- Impersonation events wired to AuditLog — closes compliance gap; `AuditLog.impersonator` FK required before hijack is enabled
- Org ownership transfer endpoint — owner-only operation; necessary when founding member leaves

**Defer (future milestones / v2+):**

- Custom org roles beyond owner/admin/member — extend `Membership.role` choices per product when enterprise customers require it
- SSO/SAML per org — django-allauth has SAML support; out of scope for template
- Hierarchical orgs (sub-orgs/departments) — only for large-enterprise products; trivially added as `parent_org` FK later
- Audit log external shipping (Splunk, Datadog Logs) — true tamper-evidence; template provides the foundation only
- Webhook event catalog UI — browsable event types with example payloads

**Anti-features to actively avoid:**

- Row-level multi-tenancy (automatic query rewriting) — breaks Django admin, hard to audit; ship Organization FK and let each product add scoping
- Webhook secret auto-rotation that updates existing integrations — impossible without breaking integrations silently
- Per-org SSO enforcement — requires SSO infrastructure as a prerequisite

### Architecture Approach

The v1.4 module follows the existing domain-app structure exactly: each feature area becomes a new `apps/api/apps/<domain>/` Django app with `models.py`, `schemas.py`, `controllers.py`, `services.py`, and `admin.py`. The billing app gains an additive `OrgCustomer` model and `OrgBillingService`. Audit logging uses `django-pghistory` decorators applied to targeted models rather than a standalone audit app with its own models — shadow tables are auto-generated by pghistory in the tracked model's migration files. Admin backoffice requires no new Django app: it modifies existing `admin.py` files to subclass `UnfoldModelAdmin` and adds `django-hijack` URL/INSTALLED_APPS configuration. All new code is wrapped in `# B2B_START` / `# B2B_END` comments for clean scaffolder removal.

**Major components:**

1. `apps/organizations/` — Organization, Membership models; `IsOrgAdmin`/`IsOrgMember` permission classes; invite flow via existing EmailAdapter; org ownership transfer; `OrgQuerySet` manager enforcing `.for_org(org)` at development time
2. `apps/billing/` (modified additive) — `OrgCustomer`, `OrgBillingService`, `has_org_feature()`; `_resolve_plan_id` updated to check org plan before personal plan
3. `apps/webhooks/` — WebhookEndpoint, WebhookDelivery models; Celery delivery task with exponential backoff (max 7 retries, up to 1h gap); HMAC-SHA256 signing; delivery log API; manual retry endpoint; auto-disable after N failures
4. `apps/apikeys/` — APIKey model (prefix + SHA-256 hash); custom `APIKeyHeader` Ninja auth backend; `RequireScope` permission class; per-key rate limiting via `django-ratelimit`
5. `apps/audit/` — thin app (no models); `AuditContextMiddleware` extends `pghistory.middleware.HistoryMiddleware` to attach org context; admin registrations for pghistory shadow tables

**Key patterns:**

- `APIKeyAuth.authenticate()` returns `None` (not raises) when header is absent, enabling fallback to session auth in Ninja's multi-auth resolution order
- Every service method accepting org-scoped resources validates `Membership.objects.filter(user=user, org=org).exists()` before any ORM filter; raw `org_id` from request input is never passed directly to a filter
- Webhook payloads include `webhook_version: "v1"` field from day one; payload schema is a versioned public API contract

### Critical Pitfalls

1. **Billing attachment to User not Org** — Update `_resolve_plan_id` in the Organization phase, not later. For org members, resolve entitlements from the org's plan first; fall back to personal plan. Invalidate `entitlements:{user.pk}` for all org members when the org subscription changes. No intermediate state where org members use the wrong tier should ever exist.

2. **API key plaintext storage or timing-unsafe comparison** — Store only SHA-256 hash and a non-secret prefix. Use `hmac.compare_digest` not `==`. Return raw key to the user exactly once at creation. No migration path from plaintext to hashed keys without invalidating all existing keys — must be correct from the first commit.

3. **Outbound webhook fire-and-forget (no delivery log)** — `WebhookDelivery` model must be in the initial migration for the webhooks phase; historical delivery status cannot be reconstructed. Implement circuit-breaker: auto-disable endpoint after N consecutive failures and notify the org admin.

4. **Tenant isolation gaps** — Every service method operating on org-scoped resources must validate membership before any ORM query. Queryset-level org filtering cannot be delegated to the HTTP permission layer alone. Write integration tests: two orgs, verify cross-org resource access returns 403.

5. **Impersonation session leaking into audit log** — `AuditLog` must have an `impersonator` nullable FK before django-hijack is enabled. Add middleware that reads `session["hijack_history"]` and injects impersonation context for the audit middleware to consume. Retrofitting the schema after the fact cannot backfill historical impersonation sessions.

6. **Django Ninja auth resolution order** — `APIKeyAuth.authenticate()` must return `None` when the header is absent (not raise an exception). Raising prevents fallback to session auth. API-key-only endpoints must list only `APIKeyAuth` in `auth=[]` to prevent session-authenticated browser tabs from bypassing scope enforcement.

## Implications for Roadmap

The dependency graph from FEATURES.md drives a strict 5-phase structure. Organization model is a hard prerequisite for all other phases. Audit logging must precede admin backoffice (impersonator column required). Webhooks and API keys are independent of each other and could be parallelized with separate subagents.

### Phase 1: Organization Model + Per-Org Billing

**Rationale:** Organization is a foreign key target for every other B2B feature. Must be first. Per-org billing ships in the same phase because `_resolve_plan_id` must be updated atomically — an intermediate state where org model exists but entitlement resolution is still user-only creates a correctness bug that is costly to fix post-hoc.
**Delivers:** `Organization`, `Membership`, `OrgRole` models; owner/admin/member roles; member invitation flow with 72h token expiry; `IsOrgAdmin`/`IsOrgMember` permission classes; `OrgQuerySet` manager; `OrgCustomer` billing model; `OrgBillingService`; updated `_resolve_plan_id`; `has_org_feature()` utility; org ownership transfer endpoint; `packages/shared-types/` regenerated.
**Features addressed:** Organization model, org roles, member invitation, per-org billing (all P1 table stakes)
**Pitfalls to avoid:** Billing attachment (update `_resolve_plan_id` in this phase); tenant isolation foundation (`OrgQuerySet` manager established as the pattern for all subsequent phases)
**Research flag:** No additional research needed — mirrors existing `billing` domain module structure; `BaseModel`, `RequireRole`, and `PaymentAdapter` patterns already validated in codebase.

### Phase 2: Outbound Webhooks

**Rationale:** Independent of API keys; depends only on Organization model (phase 1). `WebhookDelivery` model must be in the initial migration — cannot be added retroactively. Webhook payload schema must be versioned from day one.
**Delivers:** `WebhookEndpoint`, `WebhookDelivery` models; Celery delivery task with exponential backoff (7 retries, max 1h gap); HMAC-SHA256 signing; delivery log API (`GET /api/v1/webhooks/endpoints/{id}/deliveries`); manual retry endpoint (`POST /api/v1/webhooks/deliveries/{id}/retry`); dead-endpoint circuit breaker (auto-disable after N failures + org admin email notification); payload versioning (`webhook_version: "v1"` field on all payloads).
**Features addressed:** Outbound webhook registry, HMAC signing, delivery log + retry (P1 table stakes); manual retry button (differentiator)
**Pitfalls to avoid:** Fire-and-forget delivery (`WebhookDelivery` in first migration); unversioned payload schema; confusion with existing inbound Stripe webhook handler in `billing/webhooks.py` — these share no code
**Research flag:** No additional research needed — Celery `autoretry_for` + `countdown` pattern is well-documented; HMAC signing is stdlib `hmac`.

### Phase 3: API Key Authentication

**Rationale:** Independent of webhooks; depends only on Organization model (phase 1). Security invariants (hashing, timing-safe comparison, Ninja auth resolution order) must be correct from the first commit — no migration path exists if done wrong initially.
**Delivers:** `APIKey` model (prefix + SHA-256 hash); custom `APIKeyHeader` Ninja auth backend; `RequireScope` permission class; per-key rate limiting via `django-ratelimit` callable `key=`; API key usage tracking (`last_used_at`, `usage_count`); key management CRUD endpoints; `packages/shared-types/` regenerated.
**Features addressed:** API key create/revoke/scopes, per-key rate limiting (P1); API key usage tracking (P2)
**Pitfalls to avoid:** Plaintext storage (hash from first commit); timing-unsafe comparison (`hmac.compare_digest`); Ninja auth resolution order (`authenticate()` returns `None` not raises when header absent); API-key-only endpoints must not include `SessionAuth` in `auth=[]`
**Research flag:** No additional research needed — `APIKeyHeader` pattern verified against Django Ninja official docs; SHA-256 hash-only storage is industry standard.

### Phase 4: Audit Logging

**Rationale:** Cross-cutting concern — applies `@pghistory.track()` decorators to models created in phases 1-3. Must come after those models exist. `pghistory.middleware.HistoryMiddleware` must be registered after the allauth auth middleware so `request.user` is populated before pghistory captures it.
**Delivers:** `django-pghistory` + `django-pgtrigger` integration; `@pghistory.track()` on `Organization`, `Membership`, `APIKey`, `WebhookEndpoint`; `AuditContextMiddleware` (extends `pghistory.middleware.HistoryMiddleware` to attach org context); org-scoped audit log read API (`GET /api/v1/org/{slug}/audit-log`); `apps/audit/admin.py` registrations for pghistory shadow tables; `created_at` index on shadow tables; partitioning strategy documented. <!-- pragma: allowlist secret -->
**Features addressed:** Audit log write side, org-scoped read API (both P1 table stakes)
**Pitfalls to avoid:** Async Celery task actor attribution (pass `actor_id` explicitly; no `request.user` inside tasks); `pgaudit` Postgres extension is distinct from `django-pghistory` — do not conflate; AuditLog table bloat (`created_at` index mandatory; document partitioning path for high-volume deployments)
**Research flag:** No additional research needed — pghistory middleware approach is the official documented pattern; middleware ordering is confirmed by the existing allauth middleware analysis in ARCHITECTURE.md.

### Phase 5: Admin Backoffice (django-unfold + django-hijack)

**Rationale:** Must be last — depends on `AuditLog.impersonator` column (from phase 4 schema) being in place before django-hijack is enabled. `unfold` before `django.contrib.admin` in INSTALLED_APPS is a hard requirement; wrong order causes `AttributeError` on `AdminSite`.
**Delivers:** `django-unfold` theme applied across all domain `admin.py` files; `UnfoldModelAdmin` subclassing in `accounts/admin.py`, `billing/admin.py`, and all v1.4 domain admin files; `UNFOLD` navigation sidebar config; `django-hijack` with CSRF-protected impersonation restricted to `is_staff` users; impersonation banner always enabled (`HIJACK_INSERT_BEFORE` must not be `None`); hijack of `is_staff`/`is_superuser` accounts blocked; impersonation events wired to AuditLog via hijack signals (`AuditLog.impersonator` FK populated).
**Features addressed:** Admin backoffice, customer support impersonation (P1); impersonation-to-AuditLog integration (differentiator)
**Pitfalls to avoid:** `unfold` must precede `django.contrib.admin` in INSTALLED_APPS (verify with `manage.py check` in CI); impersonation banner must never be disabled; hijack of staff/superuser accounts must be blocked; `AuditLog.impersonator` FK must exist before enabling hijack
**Research flag:** MEDIUM confidence on unfold + hijack admin compatibility — no single official joint integration guide exists. Both target standard Django admin extension points; interaction is additive. Flag for early smoke-test validation: create a staff user, impersonate a regular user, verify banner renders inside unfold-themed admin and `AuditLog.impersonator` is populated before building out full admin registrations.

### Phase Ordering Rationale

- **Hard dependency order:** Organization model must precede webhooks, API keys, and audit logging — all three FK into `Organization`. Audit logging must precede admin backoffice (impersonator column). Webhooks vs. API keys have no mutual dependency and could run as parallel subagent tasks if desired.
- **Billing integration atomicity:** Org model and billing entitlement update ship in the same phase to prevent an intermediate state where org members resolve entitlements against their personal subscription. This is a business correctness requirement.
- **Security invariants are non-negotiable on day one:** API key hashing and webhook HMAC signing must be correct in the initial migration for their respective phases. No retrofit path exists.
- **Scaffolder boundary hygiene:** All five phases use `# B2B_START` / `# B2B_END` comment markers. Phase plans must maintain these boundaries — no B2B code leaks into existing app files without a corresponding removal marker pair.

### Research Flags

Phases needing additional validation during planning:

- **Phase 5 (Admin Backoffice):** Unfold + Hijack compatibility is MEDIUM confidence. Run a minimal smoke test (impersonate a user, check banner renders in unfold admin, check AuditLog entry) early in the phase before building out full admin registrations. If incompatibility is found, fall back to the standalone hijack banner which renders outside the admin theme.

Phases with well-documented standard patterns (no additional research needed):

- **Phase 1 (Organization + Billing):** Mirrors existing `billing` domain module structure; `BaseModel`, `RequireRole`, `PaymentAdapter` patterns already validated.
- **Phase 2 (Outbound Webhooks):** Celery `autoretry_for` + `countdown` is well-documented; signing is stdlib `hmac`; Stripe HMAC format is a known reference.
- **Phase 3 (API Keys):** `APIKeyHeader` pattern is in Django Ninja official docs; SHA-256 hash-only storage has no alternatives.
- **Phase 4 (Audit Logging):** `django-pghistory` middleware is the official documented approach; middleware ordering confirmed by existing codebase analysis.

## Confidence Assessment

| Area         | Confidence                                         | Notes                                                                                                                                                                                                                                                                                                                                           |
| ------------ | -------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Stack        | HIGH                                               | All three new packages verified via PyPI metadata, official docs, and GitHub repos at research time (2026-03-12). All rejected alternatives confirmed against actual package APIs (DRF-specificity of `djangorestframework-api-key`, `django-pgaudit` 404, `django-webhook` staleness).                                                         |
| Features     | HIGH                                               | Grounded in competitor analysis (SaaSPegasus, Bullet Train), B2B SaaS practitioner guides (WorkOS, PropelAuth, Clerk), and direct codebase inspection. Feature dependency graph explicitly mapped. Neither SaaSPegasus nor Bullet Train ships outbound webhooks or API keys — confirmed differentiator.                                         |
| Architecture | HIGH (4 of 5 features) / MEDIUM (admin backoffice) | Organization, webhooks, API keys, and audit logging architectures are direct extensions of existing validated patterns. Admin backoffice (unfold + hijack) compatibility is MEDIUM — no official joint integration guide; interaction is through standard Django admin extension points.                                                        |
| Pitfalls     | MEDIUM-HIGH                                        | Billing entitlement pitfall grounded in direct codebase analysis of `_resolve_plan_id`. Webhook anti-patterns from webhookantipatterns.com and Hookdeck guides. API key timing attack corroborated by CVE-2025-13473 and multiple security references. Impersonation audit trail gap derived from django-hijack session behavior documentation. |

**Overall confidence:** HIGH

### Gaps to Address

- **Unfold + Hijack admin compatibility:** Not confirmed by a single authoritative source. Address in Phase 5 with an early smoke test before building out full admin registrations. Fallback: use standalone hijack banner outside admin theme if incompatibility is found.
- **`_resolve_plan_id` refactor scope:** Review the actual implementation in `apps/billing/entitlements.py` during Phase 1 planning to determine whether adding an `org=` kwarg is additive or requires restructuring. Research assumes additive — confirm before finalizing Phase 1 plan.
- **Django version (5.0 vs 5.2) for django-hijack:** `django-hijack` 3.7.6 lists Django 5.2 as supported but not 5.0 or 5.1. Verify the current Django version in `apps/api/pyproject.toml` before Phase 5. If on 5.0 or 5.1, plan a Django 5.2 upgrade as a Phase 5 prerequisite.
- **`WebhookEndpoint.secret` storage:** Research recommends not storing the raw secret (write-only API response). The exact storage approach (HMAC-hashed secret vs. plaintext write-only) should be decided in Phase 2 planning. Plaintext with write-only serializer is acceptable for MVP; hashed secret is more secure but prevents future UI display.

## Sources

### Primary (HIGH confidence)

- [django-pghistory PyPI](https://pypi.org/project/django-pghistory/) — v3.9.2, February 17, 2026
- [django-pghistory docs](https://django-pghistory.readthedocs.io/en/3.9.1/) — trigger-based tracking, `append_only`, context middleware
- [django-pghistory GitHub](https://github.com/AmbitionEng/django-pghistory) — maintained by AmbitionEng
- [django-unfold PyPI](https://pypi.org/project/django-unfold/) — v0.83.1, March 5, 2026
- [django-unfold GitHub](https://github.com/unfoldadmin/django-unfold) — ModelAdmin integration
- [Django Admin Theme Roundup 2025](https://www.djangoproject.com/weblog/2025/apr/18/admin-theme-roundup/) — django-unfold officially recommended
- [django-hijack PyPI](https://pypi.org/project/django-hijack/) — v3.7.6, January 6, 2026; 63,992 weekly downloads
- [django-hijack docs](https://django-hijack.readthedocs.io/en/latest/) — CSRF protection, banner, `HIJACK_PERMISSION_CHECK`
- [Django Ninja authentication docs](https://django-ninja.dev/guides/authentication/) — multi-auth resolution order confirmed
- [django-pgaudit PyPI JSON API](https://pypi.org/pypi/django-pgaudit/json) — 404 confirmed; package does not exist on PyPI
- [djangorestframework-api-key PyPI](https://pypi.org/project/djangorestframework-api-key/) — v3.1.0; DRF-specific BasePermission confirmed
- [django-organizations GitHub](https://github.com/bennylope/django-organizations) — binary `is_admin` role model confirmed; unused view layer confirmed
- [django-webhook PyPI](https://pypi.org/project/django-webhook/) — v0.0.15; stale since August 2024 confirmed

### Secondary (MEDIUM confidence)

- [WorkOS — Model your B2B SaaS with organizations](https://workos.com/blog/model-your-b2b-saas-with-organizations) — org model patterns
- [PropelAuth — Guide to RBAC for B2B SaaS](https://www.propelauth.com/post/guide-to-rbac-for-b2b-saas) — role design
- [webhookantipatterns.com](https://webhookantipatterns.com/) — fire-and-forget and unversioned schema anti-patterns
- [Hookdeck — outbound webhook retry best practices](https://hookdeck.com/outpost/guides/outbound-webhook-retry-best-practices) — exponential backoff patterns
- [Frontegg — Audit logs for SaaS enterprise customers](https://frontegg.com/blog/audit-logs-for-saas-enterprise-customers) — enterprise audit log expectations
- [Standard Webhooks spec](https://github.com/standard-webhooks/standard-webhooks/blob/main/spec/standard-webhooks.md) — HMAC signing format
- [CVE-2025-13473](https://github.com/django/django/commit/6dc23508f3395e1254c315084c7334ef81c4c09a) — timing attack context for `hmac.compare_digest` requirement
- [Stripe billing for multi-entity business](https://docs.stripe.com/billing/multi-entity-business) — org-level Stripe Customer patterns
- [Django multi-tenancy isolation failure modes — TestDriven.io](https://testdriven.io/blog/django-multi-tenant/) — tenant isolation pitfall patterns

---

_Research completed: 2026-03-12_
_Ready for roadmap: yes_
