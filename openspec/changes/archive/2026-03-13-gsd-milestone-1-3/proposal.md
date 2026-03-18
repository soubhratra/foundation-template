## Why

Milestone v1.3 (SaaS Functional Baseline) shipped 5 new capabilities across phases 19–25 — transactional email, social auth, GDPR compliance, RBAC, and feature entitlements. The implementation decisions and patterns made during execution need to be synced from GSD planning documents into OpenSpec specs so that every product scaffolded from this template inherits accurate, self-contained documentation.

## What Changes

- Sync transactional email adapter pattern and Resend-as-default decision (Phases 19)
- Sync social auth decisions: Apple token verification endpoint, Google/GitHub auto-merge vs Apple relay exclusion (Phase 20)
- Sync GDPR patterns: UserDeletionService orchestrator, async Celery cascade, cookie consent gating (Phase 21)
- Sync RBAC patterns: RequireRole returning False (not raising), role seeding via data migration (Phase 22)
- Sync feature entitlement patterns: has_feature() API, Redis cache key, billing-absent fallback (Phase 23)
- Document tech debt: UserDeletionService duplication, missing GDPR export UI, AdminController auth= gap, migration filename deviation

## Capabilities

### New Capabilities

<!-- None — all five capability specs already exist in openspec/specs/ -->

### Modified Capabilities

- `transactional-email`: Add Resend-as-default decision (SendGrid dropped by anymail June 2025), ConsoleAdapter dev fallback pattern, premailer inline-CSS requirement, transaction.on_commit() dispatch contract, --without email scaffolder flag behaviour
- `social-auth`: Add Apple native JWT verification endpoint pattern (POST /api/v1/auth/apple/), SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT per-provider settings, relay address exclusion for Apple, /auth/callback + /auth/error Next.js page requirements, --without social-auth flag behaviour
- `gdpr-compliance`: Add UserDeletionService orchestrator pattern (user.delete() alone leaves orphaned Stripe + PostHog data), Celery cascade contract, cookie consent → PostHog init gating pattern, AccountExportService plan_id ORM lookup (not null), documented tech debt items
- `rbac`: Add RequireRole returns False (ninja_extra converts to HttpError 403, not raise PermissionDenied), role seeding via data migration pattern, AdminController auth= omission (documented tech debt), migration naming convention deviation
- `feature-entitlements`: Add has_feature(user, key) API contract, entitlements:{user.pk} Redis cache key with 300s TTL, unconditional invalidation on customer.subscription.updated webhook, billing-absent stub returns True

## Impact

- `openspec/specs/transactional-email/` — new decisions added, no behaviour changes to spec contract
- `openspec/specs/social-auth/` — new patterns added, no breaking changes
- `openspec/specs/gdpr-compliance/` — new patterns added, tech debt documented
- `openspec/specs/rbac/` — auth= gap and migration naming noted as tech debt
- `openspec/specs/feature-entitlements/` — cache key and invalidation contract codified
- No code changes — this is a documentation sync only
