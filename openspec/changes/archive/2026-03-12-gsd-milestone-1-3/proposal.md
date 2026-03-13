## Why

GSD milestone v1.3 (SaaS Functional Baseline) shipped 5 new capabilities across phases 19–25: transactional email, social authentication, GDPR compliance, role-based access control, and plan-gated feature entitlements. None of these have corresponding OpenSpec specs, so every new product scaffolded from this template would have undocumented behavior. This sync captures all decisions, patterns, and rationale before the milestone is archived.

## What Changes

- **New spec: `transactional-email`** — EmailAdapter ABC pattern, Celery async dispatch via `transaction.on_commit`, HTML templates with premailer inline CSS, ConsoleAdapter for dev, ResendAdapter when `RESEND_API_KEY` is set, `--without email` scaffolder flag
- **New spec: `social-auth`** — Google + GitHub OAuth for web (django-allauth), Apple Sign In for iOS (Expo), automatic email-collision account merge, OAuth callback pages pattern, `--without social-auth` scaffolder flag
- **New spec: `gdpr-compliance`** — Async account deletion cascade (cancel subscription → delete Stripe customer → delete PostHog person → delete user), JSON data export endpoint with `Content-Disposition: attachment`, consent tracking fields, known tech debt (cascade duplication, missing "Download my data" UI button)
- **New spec: `rbac`** — `UserRole` model with `owner`/`admin`/`member` levels, `@require_role` decorator, role-aware frontend hooks, `AdminController` auth pattern note (known tech debt)
- **New spec: `feature-entitlements`** — `Entitlement` model keyed to `Plan` slug, `EntitlementService.has_feature()` check, `require_feature` decorator, frontend `useEntitlement` hook

## Capabilities

### New Capabilities

- `transactional-email`: Pluggable email system with adapter pattern, async delivery, HTML templates, and scaffolder opt-out
- `social-auth`: OAuth login for Google/GitHub (web) and Apple (iOS), account merge, callback page architecture, scaffolder opt-out
- `gdpr-compliance`: Account deletion cascade, data export API, consent fields, known gaps and tech debt inventory
- `rbac`: Role-based access control across API and frontend, decorator-based gating, AdminController pattern
- `feature-entitlements`: Plan-gated feature flags system linking Stripe plans to in-app capabilities

### Modified Capabilities

- `auth`: Social auth adds `allauth.socialaccount` and provider-specific apps (`google`, `github`, `apple`) to `INSTALLED_APPS`; `SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True` enables email-collision account merge; no requirement changes to core session/JWT auth flow

## Impact

- `apps/api/` — new Django apps: `email_service`, `social_auth` additions to allauth config, `gdpr` app, `accounts` app extended with roles + entitlements
- `apps/web/` — new OAuth callback pages at `/auth/callback/google` and `/auth/callback/github`, settings page extended with DangerZone (account deletion), entitlement-aware components
- `apps/mobile/` — Apple Sign In via `expo-apple-authentication`, Google/GitHub OAuth via Expo WebBrowser + deep links
- `packages/shared-types/` — new types for roles, entitlements, GDPR export payload
- `apps/api/foundation_template/cli/` — `--without email` and `--without social-auth` scaffolder flags added
- **Tech debt documented:** 3 items (GDPR cascade duplication, missing "Download my data" UI button, AdminController missing explicit `auth=` parameter)
