# Feature Research

**Domain:** B2B SaaS template module — Organizations, Webhooks, API Keys, Audit Logging, Admin Backoffice
**Researched:** 2026-03-12
**Confidence:** HIGH (stack decisions fixed; research focused on B2B feature patterns, table stakes vs differentiators, and implementation tradeoffs)

---

## Context

This research covers the five v1.4 B2B features being added to an existing template that already ships:
Turborepo monorepo, Django Ninja Extra API, Next.js 15 App Router, Expo mobile, Django Allauth headless
(email + Google + GitHub + Apple), Stripe billing (subscriptions, one-time, metered, webhooks, PDF invoices),
structlog + OpenTelemetry + PostHog observability, health probes, rate limiting, security headers,
Redis cache, Celery + Beat, Resend transactional email, GDPR baseline (delete + export + consent),
RBAC (admin/member groups + `@require_role`), feature entitlements (has_feature Redis-cached), CLI scaffolder.

Stack is non-negotiable: Django Ninja Extra, Django Allauth, Next.js 15 App Router, Expo managed,
Celery + Redis, pnpm/uv, Turborepo, Postgres 16+.

---

## Feature Landscape

### Table Stakes (Users Expect These)

For a B2B SaaS template, table stakes are what enterprise buyers and developer-users assume will be
present. Missing these = product feels half-built or unsuitable for team/enterprise use.

| Feature                                            | Why Expected                                                                                          | Complexity | Notes                                                                                                        |
| -------------------------------------------------- | ----------------------------------------------------------------------------------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------ |
| Organization model with membership                 | B2B users assume a "workspace" they can invite teammates into; this is the core unit of B2B           | MEDIUM     | `Organization` + `Membership` (user, org, role) + invite flow; first member becomes owner                    |
| Org-level roles (owner / admin / member)           | Every B2B product needs at least owner + member; admins expect to control who has access              | LOW-MEDIUM | 3 roles minimum; owner is immutable (cannot demote self without transfer); roles separate from platform RBAC |
| Member invitation via email                        | Admins invite new members by email; fundamental onboarding flow                                       | MEDIUM     | Invite token with expiry; invite accepted via link; new user signup or existing user login both work         |
| Per-org billing (Stripe Customer per org)          | B2B buyers pay as an organization, not as individuals; invoice must show company name                 | MEDIUM     | Stripe Customer attached to `Organization` not `User`; billing admin designates which member manages billing |
| Outbound webhook registry (register URL + events)  | Developers integrating with the product expect to receive events via webhooks                         | MEDIUM     | Create/list/delete webhook endpoints; subscribe to event types; display signing secret once                  |
| HMAC-signed webhook payloads                       | Security-conscious developers will check this before trusting the platform                            | LOW        | `X-Webhook-Signature` header; SHA-256 HMAC over `timestamp + "." + body`; timestamp prevents replay attacks  |
| Webhook delivery log (view attempts, status codes) | Developers need to debug why their endpoint didn't receive an event                                   | MEDIUM     | Per-delivery record with request body, response code, response body, timestamp, attempt number               |
| Webhook retry with exponential backoff             | Transient failures (server restart, deploy) should not cause missed events permanently                | MEDIUM     | Celery task with countdown; 3–5 retries; exponential backoff + jitter; dead-letter after exhaustion          |
| API key creation and revocation                    | Developer products require programmatic access; users expect to generate keys in account/org settings | LOW-MEDIUM | Prefix + random bytes; hash stored (never plaintext after creation); show full key once at creation only     |
| API key scopes                                     | Keys should not carry full user permissions by default; developers expect scope control               | MEDIUM     | Scopes as string list on `APIKey`; validated per-request by middleware                                       |
| Audit log (who did what, when)                     | Enterprise buyers require this for SOC 2, ISO 27001, compliance reviews; it's a procurement checkbox  | MEDIUM     | Immutable log; actor (user or API key), action, resource type, resource ID, timestamp, IP, user agent        |
| Audit log accessible to org admins                 | Admins need to see their organization's activity; not just a backend/superadmin feature               | MEDIUM     | API endpoint returning paginated log entries scoped to the org; filter by actor, date range, action          |
| Admin backoffice (Django admin replacement)        | Customer support team needs to look up accounts, see subscription status, reset things                | MEDIUM     | `django-unfold` for modern admin UI; replaces default Django admin skin; no new features, just better UX     |
| Customer support impersonation                     | Support agents need to reproduce issues in a customer's account without knowing their password        | MEDIUM     | `django-hijack`; full audit trail of who impersonated whom and when; opt-in, not default                     |

### Differentiators (Competitive Advantage)

For a SaaS _template_, differentiators mean what makes this template more valuable to the developer
building a B2B product compared to building it themselves or using a competing starter kit.

| Feature                                               | Value Proposition                                                                                   | Complexity | Notes                                                                                                                               |
| ----------------------------------------------------- | --------------------------------------------------------------------------------------------------- | ---------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `--with b2b` CLI flag (optional module)               | B2B features are not needed for all products; clean scaffolder integration matches existing pattern | LOW        | Same pattern as `--without billing`, `--without observability`; B2B module excluded from consumer apps                              |
| Per-key rate limiting for API keys                    | Most templates rate-limit by IP or user; per-key limiting enables tiered API plans                  | MEDIUM     | Redis counter per key; configurable limit per key or plan tier; 429 with `X-RateLimit-*` headers                                    |
| API key usage tracking                                | Developers want to see how their keys are being used; enables metered billing per key               | MEDIUM     | Increment counter per request; surface in account UI; feeds into usage-based billing if enabled                                     |
| Webhook delivery UI with manual retry button          | Most templates only log; a manual retry button eliminates the "resend from scratch" workflow        | LOW-MEDIUM | `POST /api/webhooks/deliveries/{id}/retry`; useful for debugging and support                                                        |
| Impersonation audit trail via `AuditLog`              | Linking impersonation events to the audit log closes a compliance gap most templates miss           | LOW        | `django-hijack` signals → write `AuditLog` entry on hijack start/end; org admins cannot see impersonation entries (superadmin only) |
| Org transfer / owner reassignment                     | Necessary when the founding member leaves the company; most templates never implement this          | MEDIUM     | Transfer ownership endpoint; only current owner can initiate; new owner must be an existing org member                              |
| `django-auditlog` for model changes vs custom signals | Automated field-level change capture without writing per-model signal handlers                      | LOW        | `django-auditlog` (jazzband, actively maintained) attaches to post_save/post_delete; captures `old_value → new_value` per field     |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature                                                              | Why Requested                                                                   | Why Problematic                                                                                                                                                                                                                                  | Alternative                                                                                                                                                                   |
| -------------------------------------------------------------------- | ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Row-level multi-tenancy (all queries scoped by org_id automatically) | Feels like the "right" architecture for B2B                                     | Requires middleware that rewrites every query; breaks Django admin; difficult to audit; product-specific data model assumptions                                                                                                                  | Template provides `Organization` model and membership; each product adds `org = ForeignKey(Organization)` to its models; scoping logic lives in product, not template         |
| Hierarchical orgs (sub-orgs, departments)                            | Enterprise customers often have business units                                  | Enormous complexity in billing, permissions, and data isolation; not needed for most early B2B products                                                                                                                                          | Flat org model; when a product needs it, `parent_org` FK is trivial to add later                                                                                              |
| Custom roles / RBAC builder UI                                       | Enterprise orgs want admin to define their own role names                       | Permissions model becomes product-specific; a UI to configure permissions is a product in itself                                                                                                                                                 | Ship owner / admin / member; document that adding custom roles requires extending `Membership.role` choices; keep it in code, not database                                    |
| Webhook secret rotation UI that auto-updates existing integrations   | Seems like good security UX                                                     | Impossible to do automatically — customer's server must be updated first; auto-rotation breaks integrations silently                                                                                                                             | Show signing secret once at creation; provide manual "regenerate secret" button that explicitly warns integrations will break; require re-copy                                |
| SSO / SAML for org login                                             | Enterprise procurement often asks for this                                      | SAML is complex (XML, IdP configuration, metadata exchange); belongs in a dedicated feature, not a template module                                                                                                                               | Document the path to add django-allauth SAML provider; out of scope for template                                                                                              |
| Event streaming (Kafka / Webhooks as event bus)                      | Developer platforms want real-time event feeds                                  | Webhook system in template is point-to-point (one org endpoint, Celery delivery); streaming event bus is infrastructure, not a template concern                                                                                                  | Celery-based webhook delivery covers 95% of B2B integration needs; streaming is a product-specific infrastructure decision                                                    |
| Per-org SSO enforcement (force all members to use SAML)              | Enterprise security teams require it                                            | Requires SSO infrastructure first; enforcement logic couples auth to org settings in complex ways                                                                                                                                                | Defer to per-product implementation; template provides the org membership model that SSO enforcement would build on                                                           |
| Audit log tampering prevention (cryptographic chaining)              | SOC 2 "immutable log" requirement sounds like it needs blockchain-style hashing | `django-pgaudit` or `django-auditlog` records are append-only in practice; Postgres-level row security can prevent application-layer deletion; true tamper-evidence requires external log shipping (Splunk, Datadog Logs), which is out of scope | Write to `AuditLog` table with `DEFAULT NOW()` timestamps; add Postgres RLS or a superuser-only delete policy; document that external log shipping provides true immutability |

---

## Feature Dependencies

```
[Auth (v1.0) — User model]
    └──required by──> [Organization membership]
                          (Membership: user + org + role)
    └──required by──> [API Key authentication]
                          (APIKey.created_by = User FK)
    └──required by──> [Audit Log]
                          (actor_user = User FK, nullable for system events)

[Organization model]
    └──required by──> [Per-org billing]
                          (Stripe Customer attached to Organization not User)
    └──required by──> [Outbound webhooks]
                          (webhooks are registered per-org)
    └──required by──> [API keys (org-scoped)]
                          (API keys owned by org; created by member)
    └──required by──> [Audit log (org-scoped)]
                          (audit log entries scoped to org for org-admin view)
    └──required by──> [Member invitation flow]
                          (invites tied to org)

[Billing module (v1.1)]
    └──enhances──> [Per-org billing]
                       (PaymentAdapter ABC already exists; change customer FK from User to Organization)
    └──enhances──> [API key usage tracking]
                       (usage counts feed metered billing if enabled)

[Celery + Redis (v1.2)]
    └──required by──> [Outbound webhook delivery]
                          (Celery tasks handle delivery + retry + backoff)
    └──required by──> [Member invitation email]
                          (invite email sent via existing EmailAdapter + Celery pattern)
    └──required by──> [API key rate limiting]
                          (Redis counters per key; TTL-based sliding window)

[RBAC (v1.3) — platform admin/member groups]
    └──distinct from──> [Org roles (owner/admin/member)]
                             (platform RBAC = who can use Django admin;
                              org roles = who can manage the org's settings and members;
                              these are separate permission axes)

[Observability (v1.2) — structlog + OTel]
    └──enhances──> [Audit Log]
                       (request_id from structlog context can be stored on AuditLog entry
                        for cross-referencing traces to audit events)

[django-hijack]
    └──requires──> [django-unfold admin]
                       (hijack ships a button in Django admin; unfold provides the admin skin)
    └──enhances──> [Audit Log]
                       (hijack signals write AuditLog entries for impersonation start/end)
```

### Dependency Notes

- **Org roles vs platform RBAC are separate axes.** Platform RBAC (`admin`/`member` Django Groups from v1.3) controls who accesses platform-level features and Django admin. Org roles (`owner`/`admin`/`member` on `Membership`) control who manages an organization. A platform `member` user can be an org `owner`. These must not be conflated.

- **Per-org billing requires Organization to exist before billing features work.** The existing `PaymentAdapter` + Stripe Customer is currently attached to `User`. For B2B, Stripe Customer must move to `Organization`. This is a data model migration concern — existing solo-user billing and org billing need to coexist (products use one or the other).

- **Webhook delivery requires Celery.** Every webhook dispatch is a Celery task. This is already present from v1.2. No new infrastructure.

- **API key rate limiting requires Redis.** Counter-per-key in Redis with sliding window or token bucket. Redis is already present from v1.2 (`django-redis`). `django-ratelimit` from v1.2 may be reusable or a custom Redis counter may be cleaner for per-key semantics.

- **Audit log scoping: two views, different data.** Org admins see their org's events (member actions, settings changes, webhook deliveries, API key usage). Platform superadmins (Django admin) see everything including impersonation. These are separate query scopes.

- **Impersonation requires both django-hijack and django-unfold.** `django-hijack` v3.x ships native Django admin integration; the "Hijack" button appears in the user change view. `django-unfold` replaces the admin skin, so the hijack button must be compatible with unfold's templates. Verify compatibility before finalizing.

---

## MVP Definition (v1.4 Scope)

### Launch With (all five feature areas are the v1.4 scope)

- [ ] **Organization model + membership + org roles + invite flow** — Core B2B primitive; everything else in this milestone builds on it. Without this, the other four features have no tenant context.
- [ ] **Per-org billing (Stripe Customer per org)** — B2B buyers expect an org-level invoice and a single subscription for the whole team. Depends on Organization model being in place.
- [ ] **Outbound webhooks (registry, HMAC signing, Celery delivery, exponential backoff, delivery log)** — Table stakes for any developer-facing B2B product. Celery already present.
- [ ] **API key authentication (scopes, per-key rate limiting, usage tracking, hash-stored)** — Required for programmatic/API-first access patterns. Redis already present.
- [ ] **Audit logging (actor, action, resource, timestamp, IP; org-scoped API)** — Compliance checkbox for enterprise buyers; frequently asked in SOC 2 / ISO 27001 audits.
- [ ] **Admin backoffice (django-unfold skin + django-hijack impersonation)** — Customer support quality-of-life; reduces support time for every product built on this template.

### Add After Validation (future milestones)

- [ ] **Custom org roles (beyond owner/admin/member)** — When a product's enterprise customers demand it; requires extending `Membership.role` beyond the three seeded choices.
- [ ] **SSO / SAML per org** — When a product lands enterprise contracts requiring IdP integration; django-allauth has SAML provider support.
- [ ] **Webhook event catalog UI** — Browsable list of all event types with example payloads; improves developer onboarding but is not blocking.
- [ ] **API key per-plan rate limit tiers** — Tie API key limits to billing plan entitlements; requires per-plan limit config in `BILLING_PLANS` settings.

### Future Consideration (v2+)

- [ ] **Hierarchical orgs (sub-orgs / departments)** — Only for products targeting large enterprises; defer until a product actually needs it.
- [ ] **Audit log external shipping (Splunk, Datadog Logs)** — True tamper-evident audit logs require external log storage; out of scope for template.
- [ ] **Real-time webhook event stream (SSE / WebSocket)** — Advanced developer tooling; product-specific infrastructure decision.

---

## Feature Prioritization Matrix

| Feature                                 | Developer Value                                                           | Implementation Cost | Priority |
| --------------------------------------- | ------------------------------------------------------------------------- | ------------------- | -------- |
| Organization model + membership         | HIGH — foundational; all other B2B features depend on it                  | MEDIUM              | P1       |
| Org roles + invite flow                 | HIGH — unusable org without it; email invite required                     | MEDIUM              | P1       |
| Per-org billing                         | HIGH — B2B billing is broken without it; enterprise procurement requires  | MEDIUM              | P1       |
| Outbound webhooks (registry + delivery) | HIGH — required for developer integrations                                | MEDIUM              | P1       |
| HMAC signing                            | HIGH — security table stakes; developers will not trust unsigned webhooks | LOW                 | P1       |
| Delivery log + retry                    | MEDIUM — strong DX; not blocking but expected                             | MEDIUM              | P1       |
| API keys (create/revoke/scopes)         | HIGH — programmatic access table stakes                                   | LOW-MEDIUM          | P1       |
| Per-key rate limiting                   | MEDIUM — important for abuse prevention; Redis already present            | MEDIUM              | P1       |
| API key usage tracking                  | MEDIUM — feeds metered billing; useful for analytics                      | MEDIUM              | P2       |
| Audit log (write side)                  | HIGH — compliance requirement; SOC 2 checkbox                             | MEDIUM              | P1       |
| Audit log (org-admin read API)          | HIGH — org admins must be able to see their own logs                      | MEDIUM              | P1       |
| django-unfold admin skin                | MEDIUM — UX improvement; not blocking support tasks                       | LOW                 | P1       |
| django-hijack impersonation             | HIGH — reduces support ticket resolution time dramatically                | MEDIUM              | P1       |
| Impersonation → AuditLog integration    | MEDIUM — compliance; closes the "who impersonated whom" gap               | LOW                 | P1       |

**Priority key:**

- P1: Must have for v1.4 launch
- P2: Should have, add when capacity allows within v1.4
- P3: Nice to have, future consideration

---

## Implementation Notes by Feature Area

### 1. Organization Model

**Data model:**

- `Organization`: `id`, `name`, `slug`, `created_at`, `stripe_customer_id` (nullable; assigned when billing set up)
- `Membership`: `user (FK)`, `organization (FK)`, `role (owner | admin | member)`, `invited_by`, `joined_at`
- `OrganizationInvite`: `email`, `organization (FK)`, `role`, `token (UUID)`, `expires_at`, `accepted_at`

**Key rules:**

- First member to create the org becomes `owner`. Exactly one `owner` per org at all times.
- Owner cannot be demoted to `admin`/`member` without first transferring ownership to another member.
- Users can belong to multiple organizations (consultant pattern); each membership is independent.
- `--with b2b` scaffolder flag creates the entire `organizations` Django app and Next.js settings section.

**Billing integration:**

- `Organization.stripe_customer_id` replaces `User.stripe_customer_id` for B2B products.
- Products using solo billing (v1.1) and products using org billing are mutually exclusive configurations; the template should not force a migration — it should be a scaffolder choice at project creation or a clear extension point.

### 2. Outbound Webhooks

**Data model:**

- `WebhookEndpoint`: `organization (FK)`, `url`, `secret (hashed)`, `events (ArrayField or JSONField)`, `is_active`, `created_at`
- `WebhookDelivery`: `endpoint (FK)`, `event_type`, `payload (JSON)`, `status_code`, `response_body`, `attempt_number`, `delivered_at`, `next_retry_at`, `status (pending | delivered | failed | dead)`

**Security:**

- Signing secret generated at endpoint creation, shown exactly once, stored as HMAC-SHA-256 hash.
- Signature: `X-Webhook-Signature: sha256=HMAC_SHA256(secret, f"{timestamp}.{body}")` — mirrors Stripe's format (familiar to developers).
- `X-Webhook-Timestamp` header sent alongside; recipient should reject events older than 5 minutes to prevent replay.

**Delivery:**

- `deliver_webhook_task(delivery_id)` Celery task; HTTP POST to endpoint URL with 10s timeout.
- On 2xx: mark delivery `delivered`.
- On non-2xx or timeout: schedule retry via Celery `countdown`; exponential backoff: 30s, 5m, 30m, 2h, 8h (5 attempts).
- After 5 failures: mark `dead`; do not disable the endpoint automatically (operator decision).
- Idempotency: include `X-Delivery-ID` header (UUID) so recipient can deduplicate.

**Developer UX:**

- Delivery log endpoint: `GET /api/v1/webhooks/endpoints/{id}/deliveries` — paginated, filterable by status and date.
- Manual retry: `POST /api/v1/webhooks/deliveries/{id}/retry` — re-enqueues the Celery task; creates a new `WebhookDelivery` record (not mutates the old one).

### 3. API Key Authentication

**Data model:**

- `APIKey`: `id`, `organization (FK, nullable for user-scoped keys)`, `user (FK)`, `name`, `prefix (8 chars, readable)`, `key_hash (SHA-256 of full key)`, `scopes (ArrayField)`, `rate_limit_per_minute`, `last_used_at`, `usage_count`, `is_active`, `created_at`, `expires_at`

**Key format:** `{prefix}_{random_32_bytes_base58}` — prefix makes keys identifiable in logs without exposing the secret. E.g. `sk_live_xxxxxx`.

**Authentication flow:**

- `Authorization: Bearer {key}` header.
- Middleware: extract key → compute SHA-256 → look up `APIKey` where `key_hash = ?` and `is_active = True`.
- Async-friendly: middleware checks are synchronous DB lookups; consider caching positive results in Redis for N seconds (trade-off: revocation latency vs lookup overhead).
- Attach `request.api_key` and `request.user` (from `api_key.user`) to request for downstream handlers.

**Rate limiting:**

- Redis sliding window counter: key `ratelimit:apikey:{key_id}` with 60s TTL.
- Increment on each request; reject with `429` if over limit.
- Response headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`.
- `django-ratelimit` (already present from v1.2) can be extended for per-key semantics, or a custom Redis decorator is simpler and more explicit.

**Scopes:**

- Scopes are strings: e.g. `read:data`, `write:data`, `admin:org`. Define a `VALID_API_SCOPES` constant.
- Scope check in permission class: `APIKeyPermission(required_scope="write:data")`.
- Scopes are additive (a key with `write:data` implicitly includes `read:data`); define hierarchy in code.

### 4. Audit Logging

**Library choice: `django-auditlog` (jazzband/django-auditlog)**

- Preferred over custom signal handlers: field-level delta capture, active maintenance, 3x query performance.
- Preferred over `django-pgaudit`: `django-pgaudit` operates at the Postgres trigger level (good for tamper-evidence, harder to query from application layer); `django-auditlog` is application-layer (queryable, exportable, org-scopable).
- `django-auditlog` does NOT capture request context (user, IP) automatically unless `AuditlogMiddleware` is used. Wire the middleware.

**Supplementary `AuditLog` model for explicit business events:**
Not every important event is a model change. Login, logout, API key creation/revocation, webhook test fire, impersonation start/end — these are not captured by `django-auditlog` (which tracks ORM changes). Write a lightweight `AuditLog` model for explicit business events:

- `actor_user (FK, nullable)`, `actor_api_key (FK, nullable)`, `organization (FK, nullable)`, `action (str)`, `resource_type (str)`, `resource_id (str)`, `metadata (JSON)`, `ip_address`, `user_agent`, `request_id (from structlog)`, `created_at`

**Org-scoped API:**

- `GET /api/v1/org/{slug}/audit-log` — paginated, filterable by actor, action, date range.
- Only accessible to org `owner` and `admin` roles.
- Does not expose impersonation entries (those are superadmin-only).

**Immutability:**

- No `UPDATE` or `DELETE` endpoints for audit log.
- Consider Postgres row security policy: `DENY DELETE ON audit_log TO app_user`.
- Document that true tamper-evidence requires external log shipping; template provides the foundation.

### 5. Admin Backoffice

**django-unfold:**

- Drop-in replacement for Django admin skin; `INSTALLED_APPS` order: `unfold` before `django.contrib.admin`.
- Customizes navigation, branding, sidebar, list filters.
- Compatible with standard Django admin registrations; no model re-registration needed.
- `django-hijack` v3.x provides a "Hijack" button in user admin — verify this button renders correctly in unfold's template context (known compatibility point; check django-hijack docs for unfold-specific configuration).

**django-hijack:**

- Adds `POST /hijack/{user_id}/` and `POST /hijack/release/` endpoints.
- Shows a persistent banner while in impersonation session ("You are impersonating X — click to release").
- Signals: `hijack_started(hijacker, hijacked, request)` and `hijack_ended(hijacker, hijacked, request)` — wire these to write `AuditLog` entries.
- Restrict to Django `is_staff=True` users; regular org admins cannot impersonate (platform-level operation only).

---

## Competitor Feature Analysis

Template competitors for B2B features: SaaSPegasus, Bullet Train (HatchBox), Supergood, Wagtail-based starters.

| Feature            | SaaSPegasus (Django)           | Bullet Train          | Our v1.4 Approach                                          |
| ------------------ | ------------------------------ | --------------------- | ---------------------------------------------------------- |
| Organization model | Yes — Teams model with invites | Yes — core feature    | Organization + Membership + OrganizationInvite             |
| Per-org billing    | Yes — Stripe Customer per team | Yes                   | PaymentAdapter extended; `Organization.stripe_customer_id` |
| Outbound webhooks  | No                             | No                    | Celery delivery + HMAC + delivery log                      |
| API keys           | No                             | No                    | Prefix + hash stored + scopes + per-key rate limit         |
| Audit log          | No                             | Basic activity log    | `django-auditlog` + supplementary `AuditLog` model         |
| Admin backoffice   | Standard Django admin          | Standard Django admin | `django-unfold` + `django-hijack`                          |

**Key gaps vs competitors:** Neither SaaSPegasus nor Bullet Train ships outbound webhooks or API key
authentication as part of the template. These are genuine differentiators. Audit logging and
modern admin UI are also absent from both. The v1.4 module makes this template the most complete
B2B infrastructure kit in the Django starter ecosystem.

---

## Sources

- [WorkOS — Model your B2B SaaS with organizations](https://workos.com/blog/model-your-b2b-saas-with-organizations)
- [Clerk — Organizations overview for multi-tenant B2B](https://clerk.com/docs/guides/organizations/overview)
- [PropelAuth — Guide to RBAC for B2B SaaS](https://www.propelauth.com/post/guide-to-rbac-for-b2b-saas)
- [Hookdeck — Outpost open source outbound webhooks](https://hookdeck.com/blog/outpost-open-source-webhooks-event-destinations-infrastructure)
- [Integrate.io — Webhook best practices](https://www.integrate.io/blog/apply-webhook-best-practices/)
- [Zuplo — 10 best practices for API rate limiting 2025](https://zuplo.com/learning-center/10-best-practices-for-api-rate-limiting-in-2025)
- [Speakeasy — Rate limiting best practices in REST API design](https://www.speakeasy.com/api-design/rate-limiting)
- [Frontegg — Audit logs for SaaS enterprise customers](https://frontegg.com/blog/audit-logs-for-saas-enterprise-customers)
- [4Spot Consulting — SaaS audit logs shared responsibility](https://4spotconsulting.com/saas-audit-logs-a-shared-responsibility-for-data-integrity/)
- [Middleware.io — Audit logs comprehensive guide](https://middleware.io/blog/audit-logs/)
- [jazzband/django-auditlog — GitHub](https://github.com/jazzband/django-auditlog)
- [Medium — Django audit logging best libraries with PostgreSQL](https://medium.com/@mariliabontempo/django-audit-logging-the-best-libraries-for-tracking-model-changes-with-postgresql-2c7396564e97)
- [django-hijack — GitHub](https://github.com/django-hijack/django-hijack)
- [Matt Layman — Hijack to help customers](https://www.mattlayman.com/blog/2020/hijack-to-help-customers/)
- [Square — Webhook event logs developer docs](https://developer.squareup.com/docs/devtools/webhook-logs)

---

_Feature research for: Foundation Template v1.4 — B2B Module_
_Researched: 2026-03-12_
