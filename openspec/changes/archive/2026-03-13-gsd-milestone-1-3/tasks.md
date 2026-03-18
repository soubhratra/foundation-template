## 1. Sync transactional-email spec

- [x] 1.1 Append `## Implementation Decisions` section to `openspec/specs/transactional-email/spec.md` with rationale for Resend-as-default, ConsoleAdapter dev fallback, `transaction.on_commit()` dispatch, and `premailer` CSS inlining

## 2. Sync social-auth spec

- [x] 2.1 Append `## Implementation Decisions` section to `openspec/specs/social-auth/spec.md` with rationale for Apple JWT verification endpoint, per-provider auto-merge settings, base64/PEM key flexibility, and unified `/auth/callback` route

## 3. Sync gdpr-compliance spec

- [x] 3.1 Append `## Implementation Decisions` section to `openspec/specs/gdpr-compliance/spec.md` with rationale for UserDeletionService orchestrator, async Celery cascade, cookie consent gating PostHog init, and alias-import pattern for task patchability

## 4. Sync rbac spec

- [x] 4.1 Append `## Implementation Decisions` section to `openspec/specs/rbac/spec.md` with rationale for `has_permission()` returning False, Django Groups over custom model, data migration seeding, and AdminController auth= tech debt explanation

## 5. Sync feature-entitlements spec

- [x] 5.1 Append `## Implementation Decisions` section to `openspec/specs/feature-entitlements/spec.md` with rationale for cache key format, 300s TTL, unconditional webhook invalidation, billing-absent returns True, free-plan fallback, and never-raises contract

## 6. Archive change

- [x] 6.1 Run `/opsx:archive gsd-milestone-1-3` to merge delta specs into main specs and close this change
