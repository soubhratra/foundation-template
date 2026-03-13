# Requirements: Foundation Template

**Defined:** 2026-03-13
**Core Value:** A new SaaS product goes from zero to running full-stack app (web + mobile + API + auth) in under 5 minutes with one command.

## v1.4 Requirements

Requirements for the B2B Module milestone. Each maps to a roadmap phase.

### Organizations & Membership

- [x] **ORG-01**: User can create an organization with a name and slug; becomes owner automatically
- [x] **ORG-02**: Org owner can invite members by email (72h token expiry); accepted via new signup or existing login using existing EmailAdapter
- [x] **ORG-03**: Org members have owner/admin/member roles; `IsOrgAdmin`/`IsOrgMember` Ninja permission classes enforce access
- [x] **ORG-04**: Org owner can transfer ownership to another member via dedicated endpoint
- [x] **ORG-05**: All service methods validate org membership before any ORM access; cross-org resource access returns 403

### Per-Org Billing

- [x] **BILL-01**: System creates `OrgCustomer` (linked to `Organization`) for per-org Stripe billing, parallel to existing user `Customer` model
- [x] **BILL-02**: `_resolve_plan_id` checks org plan before personal plan; entitlement cache invalidated for all org members on subscription update; `has_org_feature()` utility available

### Outbound Webhooks

- [x] **HOOK-01**: Org admin can register webhook endpoints; deliveries are sent via Celery with exponential backoff (7 retries), HMAC-SHA256 signed, payload versioned
- [x] **HOOK-02**: User can view paginated delivery history for a webhook endpoint (`GET /api/v1/webhooks/endpoints/{id}/deliveries`)
- [x] **HOOK-03**: User can manually retry a failed delivery (`POST /api/v1/webhooks/deliveries/{id}/retry`)
- [x] **HOOK-04**: System auto-disables endpoint after N consecutive failures and notifies org admin by email

### API Keys

- [x] **AKEY-01**: User can create/revoke API keys with scopes; raw key shown once at creation; prefix + SHA-256 hash stored only; `RequireScope` permission class enforces scope per endpoint
- [x] **AKEY-02**: API key requests are rate-limited per key via `django-ratelimit`; `X-RateLimit-*` response headers returned
- [x] **AKEY-03**: System tracks `last_used_at` and `usage_count` on each API key, updated on every authenticated request

### Audit Logging

- [x] **AUDIT-01**: System records changes to `Organization`, `Membership`, `APIKey`, `WebhookEndpoint` via pghistory triggers; `AuditContextMiddleware` attaches user and org context automatically
- [x] **AUDIT-02**: Org owner and admins can query paginated audit log filtered by actor/date/action (`GET /api/v1/org/{slug}/audit-log`); impersonation entries not exposed to org admins

### Admin Backoffice

- [x] **ADMIN-01**: Django admin themed with `django-unfold` across all domain `ModelAdmin` registrations; navigation sidebar configured
- [x] **ADMIN-02**: Staff users can impersonate any non-staff user via `django-hijack`; persistent banner shown; impersonation events written to audit log with `impersonator` FK

### CLI Scaffolder

- [ ] **SCAFF-01**: `--with b2b` flag in `create-foundation-app`; all B2B code uses `# B2B_START`/`# B2B_END` markers; `--without b2b` removes module cleanly; `manage.py check` passes post-removal

## Future Requirements

### v2+ Considerations

- **ORG-F01**: Custom org roles beyond owner/admin/member — extend `Membership.role` choices per product for enterprise use cases
- **ORG-F02**: Hierarchical orgs (sub-orgs/departments) — `parent_org` FK; only for large-enterprise products
- **SSO-F01**: Per-org SSO/SAML enforcement — requires allauth SAML support; product-specific
- **AUDIT-F01**: Audit log external shipping (Splunk, Datadog Logs) — template provides the foundation; products add exporters
- **HOOK-F01**: Webhook event catalog UI — browsable event types with example payloads

## Out of Scope

| Feature                                                     | Reason                                                                                    |
| ----------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| Row-level multi-tenancy (automatic query rewriting)         | Breaks Django admin, hard to audit; ship Organization FK and let each product add scoping |
| Webhook secret auto-rotation updating existing integrations | Impossible without breaking integrations silently                                         |
| Per-org SSO enforcement                                     | Requires SSO infrastructure as prerequisite                                               |
| Custom org roles (beyond owner/admin/member)                | Product-specific; extend Membership.role choices per product                              |
| Google Sign In on mobile (org flow)                         | Already out of scope from v1.3                                                            |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase    | Status   |
| ----------- | -------- | -------- |
| ORG-01      | Phase 26 | Complete |
| ORG-02      | Phase 26 | Complete |
| ORG-03      | Phase 26 | Complete |
| ORG-04      | Phase 26 | Complete |
| ORG-05      | Phase 26 | Complete |
| BILL-01     | Phase 26 | Complete |
| BILL-02     | Phase 26 | Complete |
| HOOK-01     | Phase 27 | Complete |
| HOOK-02     | Phase 27 | Complete |
| HOOK-03     | Phase 27 | Complete |
| HOOK-04     | Phase 27 | Complete |
| AKEY-01     | Phase 28 | Complete |
| AKEY-02     | Phase 28 | Complete |
| AKEY-03     | Phase 28 | Complete |
| AUDIT-01    | Phase 29 | Complete |
| AUDIT-02    | Phase 29 | Complete |
| ADMIN-01    | Phase 30 | Complete |
| ADMIN-02    | Phase 30 | Complete |
| SCAFF-01    | Phase 31 | Pending  |

**Coverage:**

- v1.4 requirements: 19 total
- Mapped to phases: 19 (100% coverage)
- Unmapped: 0

---

_Requirements defined: 2026-03-13_
_Last updated: 2026-03-13 after roadmap creation_
