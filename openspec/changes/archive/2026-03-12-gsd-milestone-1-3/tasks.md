## 1. Verify Spec Files Against Codebase

- [ ] 1.1 Verify `transactional-email/spec.md` — confirm `apps/api/apps/notifications/` structure, `EMAIL MODULE` sentinel comments in `base.py`, and `removeEmailModule()` in `packages/create-foundation-app/src/remove.ts` match the spec
- [ ] 1.2 Verify `social-auth/spec.md` — confirm `_configure_social_providers()` in `config/settings/base.py`, `SOCIAL AUTH MODULE` fence, OAuth callback pages at `apps/web/app/auth/callback/`, and `removeSocialAuthModule()` in scaffolder match the spec
- [ ] 1.3 Verify `gdpr-compliance/spec.md` — confirm `DELETE /api/v1/account/` returns 202, `delete_user_account` Celery task exists in `apps/accounts/tasks.py`, and `GET /api/v1/account/export` returns JSON attachment
- [ ] 1.4 Verify `rbac/spec.md` — confirm `RequireRole` in `apps/accounts/permissions.py`, `migration_0003_seed_roles.py`, and `AdminController` in `apps/accounts/controllers.py` match the spec
- [ ] 1.5 Verify `feature-entitlements/spec.md` — confirm `has_feature()` in `apps/core/entitlements.py`, `_has_feature()` in `apps/billing/entitlements.py`, `Subscription.plan_id` field, and cache invalidation in `apps/billing/tasks.py` match the spec
- [ ] 1.6 Verify `auth/spec.md` delta — confirm `allauth.socialaccount` and provider apps in `INSTALLED_APPS` with `# SOCIAL AUTH MODULE` comments, and `SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True` in `base.py`

## 2. Archive Change to Main Specs

- [ ] 2.1 Run `/opsx:archive gsd-milestone-1-3` to merge all delta specs into `openspec/specs/` and archive the change
- [ ] 2.2 Confirm new spec directories exist: `openspec/specs/transactional-email/`, `openspec/specs/social-auth/`, `openspec/specs/gdpr-compliance/`, `openspec/specs/rbac/`, `openspec/specs/feature-entitlements/`
- [ ] 2.3 Confirm `openspec/specs/auth/spec.md` includes the social auth ADDED requirements

## 3. Complete Milestone

- [ ] 3.1 Run `/gsd:complete-milestone` to archive `.planning/` for v1.3 and prepare for v1.4
