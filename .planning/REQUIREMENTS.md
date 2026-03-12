# Requirements: Foundation Template

**Defined:** 2026-03-11
**Core Value:** A new SaaS product goes from zero to running full-stack app (web + mobile + API + auth) in under 5 minutes with one command.

## v1.3 Requirements — SaaS Functional Baseline

Requirements for v1.3. Each maps to roadmap phases starting at phase 19.

### Email (Transactional)

- [x] **EMAIL-01**: Application can send a transactional email via `EmailAdapter` ABC with `ResendAdapter` as the default backend, swappable via one Django setting
- [x] **EMAIL-02**: Emails are dispatched asynchronously via Celery tasks (never blocking HTTP) using `transaction.on_commit()` to prevent race conditions
- [x] **EMAIL-03**: HTML email templates are rendered server-side with inline CSS (via `premailer`) for email client compatibility
- [x] **EMAIL-04**: A `ConsoleAdapter` is the default in development (no credentials needed); `ResendAdapter` activates when `RESEND_API_KEY` is set
- [x] **EMAIL-05**: Running `create-foundation-app --without email` removes all email module files cleanly; `manage.py check` passes

### Social Auth

- [x] **SOCIAL-01**: User can sign up and log in via Google OAuth on the web app
- [x] **SOCIAL-02**: User can sign up and log in via GitHub OAuth on the web app
- [x] **SOCIAL-03**: User can sign up and log in via Apple Sign In on the iOS mobile app
- [x] **SOCIAL-04**: Social login with an email matching an existing password account auto-connects the accounts (per-provider: Google/GitHub auto-merge, Apple relay addresses excluded)
- [x] **SOCIAL-05**: Running `create-foundation-app --without social-auth` removes all social auth configuration cleanly

### GDPR

- [x] **GDPR-01**: Authenticated user can permanently delete their account via `DELETE /api/v1/account/` — triggers async Celery task that cascades through all user data, cleans up Stripe customer and PostHog person, returns HTTP 202
- [x] **GDPR-02**: Authenticated user can export all their personal data as JSON via `GET /api/v1/account/export`
- [x] **GDPR-03**: User sees a cookie consent banner on first visit to the web app; PostHog initialises only after consent is granted

### RBAC

- [ ] **RBAC-01**: API endpoints can be protected with a `@require_role("admin")` decorator that returns HTTP 403 for users without the role
- [ ] **RBAC-02**: Authenticated admin user can assign or remove roles from other users via `POST /api/v1/users/{id}/roles`
- [ ] **RBAC-03**: Default roles (`admin`, `member`) are seeded via data migration on first deploy

### Entitlements

- [ ] **ENT-01**: Application code can check `has_feature(user, "feature_key")` which returns True/False based on the user's active billing plan and the `BILLING_PLANS` settings dict
- [ ] **ENT-02**: Entitlement results are cached in Redis and invalidated automatically when a billing plan-change webhook is processed
- [ ] **ENT-03**: When `--without billing` is used, `has_feature()` returns `True` for all keys (no billing = no gating)

## Future Requirements

### Email

- **EMAIL-F01**: Support for `MailgunAdapter` and `SESAdapter` as documented swap-ins
- **EMAIL-F02**: Email open/click tracking per provider

### Social Auth

- **SOCIAL-F01**: Google Sign In on mobile (requires dev build + Android complexity — deferred)
- **SOCIAL-F02**: SSO/SAML for enterprise B2B (OpenSpec guide only)

### GDPR

- **GDPR-F01**: Async data export delivered via email link for large datasets

### RBAC

- **RBAC-F01**: Object-level permissions via `django-guardian` (product-specific)

### Entitlements

- **ENT-F01**: Runtime feature flag override via PostHog flags (layered on top of plan entitlements)

## Out of Scope

| Feature                            | Reason                                                                                        |
| ---------------------------------- | --------------------------------------------------------------------------------------------- |
| SendGrid as email default          | django-anymail dropped official SendGrid support June 2025; Resend is the recommended default |
| Soft delete for GDPR               | Violates Article 17 unless combined with rigorous anonymisation — hard delete is correct      |
| Google Sign In on mobile           | Requires dev build + separate Android/iOS credentials; high complexity; deferred to future    |
| SMS / 2FA                          | Product-specific; OpenSpec guide only                                                         |
| django-guardian object permissions | Too product-specific for template                                                             |
| Multi-tenancy                      | v1.4 scope                                                                                    |

## Traceability

| Requirement | Phase    | Status   |
| ----------- | -------- | -------- |
| EMAIL-01    | Phase 19 | Complete |
| EMAIL-02    | Phase 19 | Complete |
| EMAIL-03    | Phase 19 | Complete |
| EMAIL-04    | Phase 19 | Complete |
| EMAIL-05    | Phase 19 | Complete |
| SOCIAL-01   | Phase 20 | Complete |
| SOCIAL-02   | Phase 20 | Complete |
| SOCIAL-03   | Phase 20 | Complete |
| SOCIAL-04   | Phase 20 | Complete |
| SOCIAL-05   | Phase 20 | Complete |
| GDPR-01     | Phase 21 | Complete |
| GDPR-02     | Phase 21 | Complete |
| GDPR-03     | Phase 21 | Complete |
| RBAC-01     | Phase 22 | Pending  |
| RBAC-02     | Phase 22 | Pending  |
| RBAC-03     | Phase 22 | Pending  |
| ENT-01      | Phase 23 | Pending  |
| ENT-02      | Phase 23 | Pending  |
| ENT-03      | Phase 23 | Pending  |

**Coverage:**

- v1.3 requirements: 19 total
- Mapped to phases: 19
- Unmapped: 0 ✓

---

_Requirements defined: 2026-03-11_
_Last updated: 2026-03-11 after initial definition_
