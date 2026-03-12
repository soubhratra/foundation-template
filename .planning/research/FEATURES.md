# Feature Research

**Domain:** Full-stack SaaS template — v1.3 functional baseline features
**Researched:** 2026-03-11
**Confidence:** HIGH (stack decisions fixed; research focused on implementation patterns and pitfalls)

---

## Context

This research covers the five v1.3 features being added to an existing template that already ships:
email/password auth (Django Allauth headless), billing (Stripe adapter), observability
(PostHog + OTel + structlog), health probes, rate limiting, security headers, Celery, Redis.

Stack is non-negotiable: Django Ninja Extra, Django Allauth, Next.js 15 App Router, Expo managed,
Celery + Redis, pnpm/uv, Turborepo.

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features that developers and end-users expect in any production SaaS. Missing these = product
feels half-built or legally risky.

| Feature                                 | Why Expected                                                                      | Complexity | Notes                                                                                       |
| --------------------------------------- | --------------------------------------------------------------------------------- | ---------- | ------------------------------------------------------------------------------------------- |
| Transactional email (account lifecycle) | Password reset, email verification, billing receipts — users expect email         | MEDIUM     | Django already sends some via Allauth; this formalizes the pattern with a queue and adapter |
| Social login (Google at minimum)        | Reduces signup friction; users expect "Sign in with Google" in 2025               | MEDIUM     | Django Allauth has providers built in; wiring headless + Expo adds surface area             |
| Account hard delete (GDPR Art. 17)      | EU legal requirement; users expect to be able to leave                            | MEDIUM     | Django ORM cascade handles most; need explicit audit of all FK relations                    |
| Data export (GDPR Art. 20)              | EU legal requirement; right to portability                                        | LOW-MEDIUM | Django serialization + a Celery task; must gather all user-owned tables                     |
| Cookie consent banner                   | EU legal requirement (ePrivacy Directive + GDPR) for analytics/tracking cookies   | LOW        | Only required when the product sets non-essential cookies (PostHog, GA)                     |
| Role-based access (admin vs member)     | Any multi-user product needs at minimum an admin role                             | LOW-MEDIUM | Django Groups are built-in; decorator wrapping is the main implementation task              |
| Plan-gated features                     | Users expect premium tiers to unlock features; billing module is already in place | MEDIUM     | Must integrate with existing Billing module; config-driven approach keeps it maintainable   |

### Differentiators (Competitive Advantage)

For a SaaS _template_, differentiators mean what makes this template more valuable to the
developer using it compared to building it themselves or using a competing starter kit.

| Feature                                                 | Value Proposition                                                                               | Complexity | Notes                                                                                            |
| ------------------------------------------------------- | ----------------------------------------------------------------------------------------------- | ---------- | ------------------------------------------------------------------------------------------------ |
| Email adapter ABC (EmailAdapter)                        | Swappable providers via one Django setting — same pattern as PaymentAdapter; avoids SDK lock-in | LOW        | Custom ABC with ResendAdapter as default; Celery queue baked in from day one                     |
| Apple Sign In on mobile                                 | Required by App Store if any social auth is present; most templates skip this                   | HIGH       | Unique Apple OAuth: POST not GET, bundle ID vs Services ID, p8 key expires every 6 months        |
| GDPR deletion as async Celery task                      | Deletion can trigger large cascade + downstream cleanup; blocking HTTP would time out           | LOW-MEDIUM | Hard delete is simpler than soft delete; async pattern mirrors PDF invoice approach from v1.1    |
| `has_feature(user, key)` vs PostHog flags               | Entitlements are billing-linked and server-side enforced; PostHog flags are deployment-centric  | MEDIUM     | Clear separation: PostHog = feature rollout/A-B testing; entitlements = plan gates; both coexist |
| `--without social-auth` and `--without email` CLI flags | Matches existing `--without billing` / `--without observability` pattern; keeps template lean   | LOW        | Scaffolder work; both features designed to be optional from day one                              |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature                                                        | Why Requested                              | Why Problematic                                                                                                           | Alternative                                                                                        |
| -------------------------------------------------------------- | ------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| SendGrid as default email provider                             | Most tutorials use SendGrid; familiar name | django-anymail dropped official SendGrid support June 2025 (Twilio blocked their test account); future bugs unverifiable  | Resend via django-anymail — fully supported in v14, modern API, generous free tier                 |
| Soft delete for GDPR                                           | Seems safer than hard delete; recoverable  | Creates orphaned data, breaks GDPR Article 17 (data must actually be gone), anonymization acceptable but must be rigorous | Hard delete with cascade; keep only what is legally required (billing records for tax), anonymized |
| Fine-grained object-level permissions in template              | Feels thorough                             | Requires product-specific data model knowledge; Django Guardian adds complexity without template value                    | Group-based RBAC (admin/member/viewer); each product adds object permissions per their model       |
| Social auth for every provider (Facebook, Twitter/X, LinkedIn) | "More options" seems better                | Each provider has its own quirks, consent screens, App Review processes; maintenance burden                               | Ship Google + GitHub (web) + Apple (mobile); template users add more providers per-product         |
| Storing email open/click tracking in the template              | Useful for product analytics               | Adds GDPR complexity, requires consent, varies by ESP                                                                     | Use ESP's built-in tracking dashboards; template does not store tracking events                    |
| Multi-factor auth (TOTP/SMS) in v1.3                           | Natural auth extension                     | Allauth has MFA module but it adds significant UX surface area; belongs in a dedicated milestone                          | Future milestone; Allauth headless MFA is available when the time comes                            |
| Attribute-based access control (ABAC)                          | More flexible than RBAC                    | Needs product-specific attribute model; over-engineering for a template                                                   | Group-based RBAC covers 95% of SaaS needs; each product layers ABAC on top                         |

---

## Feature Dependencies

```
[Billing module (v1.1)]
    └──required by──> [Feature Entitlements]
                          (has_feature reads plan from Subscription model)

[Celery + Redis (v1.2)]
    └──required by──> [Transactional Email]
                          (email tasks enqueued via Celery)
    └──required by──> [GDPR Account Delete]
                          (deletion dispatched as async Celery task)
    └──required by──> [GDPR Data Export]
                          (export assembled async, then stored/emailed)

[Django Allauth headless (v1.0)]
    └──required by──> [Social Auth — Google, GitHub, Apple]
                          (Allauth manages social account tokens and user linking)
    └──enhances──> [Transactional Email]
                          (Allauth sends verification/reset; adapter replaces Django email backend)

[Auth (v1.0)]
    └──required by──> [RBAC]
                          (User.groups is Django built-in; requires auth app)

[RBAC]
    └──enhances──> [Feature Entitlements]
                          (admin role can manage plan assignments and overrides)

[Social Auth — any iOS social login]
    └──requires──> [Apple Sign In on mobile]
                          (App Store policy: any social login on iOS = Apple Sign In mandatory)

[Observability/PostHog (v1.2)]
    └──requires consent from──> [GDPR Cookie Consent Banner]
                          (PostHog analytics cookies require user consent under ePrivacy Directive)
```

### Dependency Notes

- **Feature Entitlements requires Billing:** `has_feature(user, key)` reads the user's active `Subscription` and maps it to plan config in settings. Without the Billing module, there is no subscription to read. If a project uses `--without billing`, entitlements fall back to returning `True` for all features (developer mode). Document this clearly.

- **Transactional Email requires Celery:** Email must never block an HTTP response. The EmailAdapter sends all emails via Celery tasks. Celery is already present from v1.2.

- **Social Auth on iOS requires Apple:** Apple App Store Review policy — if a native iOS app offers any third-party social login (Google, GitHub, etc.), it MUST also offer "Sign in with Apple." Shipping Google without Apple on mobile is an App Store rejection risk. This is not optional.

- **Cookie Consent requires Observability context:** The consent banner is only necessary when non-essential cookies are set. PostHog sets analytics cookies in the browser. The banner must gate PostHog initialization in `apps/web/`. This means the banner is directly dependent on the v1.2 observability module being present.

- **RBAC enhances Feature Entitlements:** Admins need a way to manually override plan features for individual users (e.g. grant trial access). RBAC provides the `admin` role check needed to protect those override endpoints.

---

## MVP Definition (v1.3 Scope)

### Launch With (all five features are the v1.3 scope)

- [ ] **Transactional Email (EmailAdapter ABC + ResendAdapter + Celery queue + HTML templates)** — Replaces ad-hoc Django email sends with a consistent, testable, provider-swappable pattern. Required for every SaaS.
- [ ] **Social Auth (Google + GitHub via Allauth headless on web; Apple via Expo on mobile)** — Reduces signup friction on web; Apple is legally required for iOS App Store if any social login exists.
- [ ] **GDPR Baseline (hard delete + data export + cookie consent banner)** — Minimum viable legal compliance for EU users. Can ship without to non-EU markets but adds legal risk.
- [ ] **RBAC (Django Groups + `@require_role` decorator + assignment API)** — Minimum multi-user access control. Even solo-user products need an admin role for internal tooling.
- [ ] **Feature Entitlements (`has_feature(user, key)` + plan config in settings)** — Closes the billing loop: plan gates determine what features each subscriber sees.

### Add After Validation (future milestones)

- [ ] **MFA (TOTP via Django Allauth MFA module)** — When product has users requesting it; Allauth has headless MFA support ready.
- [ ] **Additional social providers (Facebook, LinkedIn)** — When a product's target audience uses them; not worth template complexity for all products.
- [ ] **Object-level permissions (Django Guardian)** — When a product needs row-level access control; requires product-specific models.
- [ ] **GDPR consent management platform integration (CookieYes, Cookiebot)** — When cookie categories grow beyond a simple analytics/necessary split.

### Future Consideration (v2+)

- [ ] **ABAC / policy engines (Casbin, OPA)** — For enterprise multi-tenant products with complex authorization rules.
- [ ] **Right to data rectification UI** — Users self-service correct their personal data; requires per-product field mapping.
- [ ] **Automated DPA workflow** — GDPR data processing agreements for B2B SaaS; niche requirement.

---

## Feature Prioritization Matrix

| Feature                           | Developer Value                                          | Implementation Cost | Priority                 |
| --------------------------------- | -------------------------------------------------------- | ------------------- | ------------------------ |
| Transactional Email               | HIGH — every SaaS needs it; ad-hoc sends cause tech debt | MEDIUM              | P1                       |
| Social Auth (Google + GitHub web) | HIGH — reduces signup friction; expected by users        | MEDIUM              | P1                       |
| Apple Sign In (mobile)            | HIGH — App Store rejection risk without it               | HIGH                | P1 (blocking for mobile) |
| GDPR Account Delete               | HIGH — legal requirement for EU; user trust              | MEDIUM              | P1                       |
| GDPR Data Export                  | MEDIUM — legal requirement, less frequently used         | LOW-MEDIUM          | P1                       |
| Cookie Consent Banner             | HIGH — legal; PostHog already in v1.2                    | LOW                 | P1                       |
| RBAC (groups + decorator)         | HIGH — needed for any multi-user product                 | LOW-MEDIUM          | P1                       |
| Feature Entitlements              | HIGH — closes billing loop; expected in tiered products  | MEDIUM              | P1                       |

All eight sub-features are P1 for v1.3. None can be deferred without compromising the
"functional baseline" goal of the milestone.

---

## Feature Implementation Notes

### 1. Transactional Email

**EmailAdapter ABC pattern (mirrors PaymentAdapter from v1.1):**

- `EmailAdapter` ABC defines `send(to, subject, html_body, text_body, template_name, context)`.
- `ResendAdapter` is the default — django-anymail v14, Resend fully supported. SendGrid was dropped from django-anymail in June 2025 (Twilio blocked their test account; future bugs cannot be verified). Do not use SendGrid as default.
- `SMTPAdapter` wraps Django's built-in backend for local dev / fallback.
- All sends go through a Celery task: `send_email_task.delay(...)` — never synchronous in production.
- HTML templates: Django template engine (`render_to_string`), stored in `apps/api/emails/templates/`.
- Allauth's own email sends (verification, password reset) route through the new adapter by setting `EMAIL_BACKEND` in Django settings to the adapter's backend.

**Minimum templates to ship:** welcome, email-verify, password-reset, password-changed, subscription-created, subscription-cancelled.

**`--without email` scaffolder flag:** removes adapter, Celery email tasks, templates; Allauth falls back to `django.core.mail.backends.console.EmailBackend` in dev.

### 2. Social Auth

**Web (Google + GitHub):**

- Config via `SOCIALACCOUNT_PROVIDERS` in settings (not Django admin — secrets backed by environment variables, not the database, which is the correct production pattern).
- `AUTH_PARAMS: {'access_type': 'offline'}` for Google to receive refresh tokens on first login and reauthentication.
- Headless mode: Allauth headless already wired from v1.0; social providers extend the same flow.
- OAuth credentials per environment: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET` in `.env`.

**Mobile (Apple):**

- `expo-apple-authentication` (Expo managed workflow, iOS-only native module).
- Apple issues two distinct client IDs: Bundle ID (native iOS app) and Services ID (web OAuth flow). Both are required; configure as separate entries in Allauth `APPS` list. Mark the mobile Bundle ID entry with `"hidden": True` to prevent it appearing in web flows.
- **Critical gotcha — POST not GET:** Apple Sign In uses POST for the OAuth redirect, unlike all other providers. The session cookie is not sent on a cross-origin POST (SameSite=Lax). Any middleware that creates new sessions on this POST disrupts the original session after auth completes. Must handle session continuity explicitly.
- **Critical gotcha — Expo Go:** Apple Sign In does not work in Expo Go. Development builds (EAS Build or `expo run:ios`) are required for local testing. Account for this in developer setup docs.
- **Critical gotcha — JWT audience:** In development (Expo Go / dev build), the `aud` claim in Apple's identityToken is `host.exp.Exponent`. In production builds, it is the app bundle ID. Backend token validation must handle both.
- **Critical maintenance item — p8 key expiry:** The Apple private key used to sign tokens must be rotated every 6 months. This is a non-obvious operational requirement. Add a reminder / documentation note; failure causes silent auth breakage.
- **App Store policy:** Any native iOS app offering social login of any kind must also offer Apple Sign In. Non-negotiable.

**`--without social-auth` flag:** removes provider configs, OAuth env vars, `expo-apple-authentication` module; email/password auth via Allauth remains fully functional.

### 3. GDPR Baseline

**Account Hard Delete:**

- Django's `User.delete()` cascades via `ON DELETE CASCADE` or `SET_NULL` on all FK relations automatically.
- Audit required: every model in every app (billing, observability events, content) must be checked for FK to User; non-obvious relations (e.g. Celery task results, PostHog identities) need explicit cleanup.
- Async: `delete_account_task.delay(user_id)` — deletion can be slow for users with large data footprints; must never block HTTP.
- Keep (anonymized): billing records required for tax/accounting (strip name/email, retain amounts and dates).
- Flow: user requests deletion → `HTTP 202 Accepted` → confirmation email sent → Celery task executes after short grace period (e.g. 24h) → account gone.

**Data Export:**

- `POST /api/v1/account/export` → returns `202 Accepted`, kicks off Celery task.
- Task serializes all user-owned data to JSON (Django serializer or manual dict assembly covering: profile, subscription history, billing events).
- Result delivered via email as attachment or a signed S3/storage URL valid for 24h.
- Must complete within the GDPR 30-day response window; async delivery is acceptable.

**Cookie Consent Banner:**

- Client component (`"use client"`) in Next.js App Router — must not run on server (localStorage unavailable server-side; hydration errors if read in RSC).
- Stores consent in `localStorage` key `cookie_consent` with categories: `{necessary: true, analytics: boolean}`.
- Gates PostHog initialization: only call `posthog.init()` after `analytics: true` consent is confirmed.
- Pattern: check consent in `useEffect`, re-initialize or shut down PostHog on consent changes.
- No third-party consent library needed — simple enough to build inline for a template; avoids adding a SaaS dependency.
- Show on first visit; remember choice; provide link to revoke from account settings.

### 4. RBAC

**Django Groups as roles:**

- Three default roles seeded via data migration: `admin`, `member`, `viewer`.
- `@require_role("admin")` decorator for Django Ninja Extra controllers — checks `user.groups.filter(name=role).exists()`.
- Decorator raises `HttpError(403)` if role check fails; must handle unauthenticated users (401 before 403 check).
- Role assignment API: `POST /api/v1/admin/users/{id}/roles` — admin-only endpoint.
- Django's built-in `user.has_perm()` system sits alongside groups and is not replaced; object permissions left to individual products.
- Groups seeded in migration (not Django admin UI) — ensures groups exist in automated deployments and CI.

### 5. Feature Entitlements

**`has_feature(user, key)` pattern:**

- Pure function in `apps/api/entitlements/services.py`.
- Reads `PLAN_FEATURES` dict from Django settings: `{'pro': ['ai', 'exports', 'api_access'], 'free': ['exports']}`.
- Fetches user's active plan from `Subscription` model (Billing module).
- Returns `bool`; raises no exceptions — defaults to `False` if plan unknown or subscription inactive.
- Server-side only — never expose the raw `PLAN_FEATURES` config to clients; expose only the evaluated result.

**Entitlement check endpoint:** `GET /api/v1/entitlements` returns `{feature_key: bool}` for the current user — lets the frontend gate UI elements without leaking plan config or billing internals.

**Distinction from PostHog flags (v1.2):** PostHog flags control _when_ a feature rolls out (gradual release, A/B testing). Entitlements control _who_ can access a feature based on their billing plan. Both can coexist — a feature might require both Pro plan AND being in the 50% rollout group.

**`--without billing` interaction:** If the billing module is excluded, `has_feature()` returns `True` for all features by default (no subscription to check, assume development mode). This must be explicitly documented so developers know template scaffolds without billing have open entitlements.

---

## Competitor Feature Analysis

Template competitors: SaaSPegasus, Bedrock, Bullet Train, various Next.js/Django starter kits.

| Feature              | SaaSPegasus (Django)           | Bedrock (Next.js)        | Our v1.3 Approach                                               |
| -------------------- | ------------------------------ | ------------------------ | --------------------------------------------------------------- |
| Transactional email  | django-anymail + Mailgun       | Resend or Postmark       | EmailAdapter ABC + ResendAdapter default; swappable via setting |
| Social auth          | Google + GitHub via Allauth    | Next-Auth providers      | Google + GitHub (web) + Apple (mobile) via Allauth headless     |
| GDPR                 | Manual / not standard          | Varies                   | Hard delete + export + consent banner; async Celery pattern     |
| RBAC                 | Built-in (teams + roles model) | Role middleware          | Django Groups + `@require_role` decorator; 3 seeded roles       |
| Feature entitlements | Plan-based flags               | Feature flag integration | `has_feature()` + plan config in settings; billing-linked       |

**Key gap vs competitors:** Most Django starters do not include Apple Sign In on mobile (web-only focus) and do not ship an explicit async GDPR deletion workflow. These are genuine differentiators for this template.

---

## Sources

- [django-anymail — SendGrid status (dropped June 2025)](https://anymail.dev/en/v14.0/esps/sendgrid/)
- [django-anymail — GitHub (Resend + all supported providers)](https://github.com/anymail/django-anymail)
- [django-anymail — SendGrid drop issue #432](https://github.com/anymail/django-anymail/issues/432)
- [django-allauth — Apple provider docs](https://docs.allauth.org/en/dev/socialaccount/providers/apple.html)
- [django-allauth — Google provider docs](https://docs.allauth.org/en/dev/socialaccount/providers/google.html)
- [django-allauth — Provider configuration patterns](https://docs.allauth.org/en/dev/socialaccount/provider_configuration.html)
- [Expo — AppleAuthentication module](https://docs.expo.dev/versions/latest/sdk/apple-authentication/)
- [Expo — Authentication overview](https://docs.expo.dev/develop/authentication/)
- [Apple Sign In with Expo 2025 (Medium)](https://medium.com/@meszmate/apple-sign-in-with-expo-golang-complete-2025-guide-to-server-side-oauth-jwt-validation-and-01677dc27e08)
- [GDPR for SaaS — Feroot 2026 action plan](https://www.feroot.com/blog/gdpr-saas-compliance-2025/)
- [GDPR for SaaS — CookieYes 8-step guide](https://www.cookieyes.com/blog/gdpr-for-saas/)
- [GDPR right to erasure — Comply Dog](https://complydog.com/blog/right-to-be-forgotten-gdpr-erasure-rights-guide)
- [Next.js cookie consent banner — PostHog tutorial](https://posthog.com/tutorials/nextjs-cookie-banner)
- [Next.js cookie consent — Build with Matija 2025](https://www.buildwithmatija.com/blog/build-cookie-consent-banner-nextjs-15-server-client)
- [SaaS entitlements — Orb](https://www.withorb.com/blog/what-are-entitlements-in-saas)
- [Feature gating patterns — Orb](https://www.withorb.com/blog/feature-gating)
- [Entitlements vs feature flags — LaunchDarkly](https://launchdarkly.com/blog/how-to-manage-entitlements-with-feature-flags/)
- [Django RBAC full guide — Permit.io](https://www.permit.io/blog/how-to-implement-role-based-access-control-rbac-into-a-django-application)
- [Django GDPR compliance — CloudDevs](https://clouddevs.com/django/gdpr-compliance-for-privacy/)

---

_Feature research for: Foundation Template v1.3 — SaaS Functional Baseline_
_Researched: 2026-03-11_
