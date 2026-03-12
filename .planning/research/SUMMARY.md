# Project Research Summary

**Project:** Foundation Template — v1.3 SaaS Functional Baseline
**Domain:** SaaS template — transactional email, social auth, GDPR baseline, RBAC, feature entitlements
**Researched:** 2026-03-11
**Confidence:** HIGH

## Executive Summary

The v1.3 milestone adds five cross-cutting features to an already-shipping Django Ninja Extra + Next.js 15 + Expo SDK 53 monorepo. These features are universally required in production SaaS products: transactional email, social login, GDPR compliance, role-based access control, and plan-gated feature entitlements. The research conclusion is clear — all five belong in v1.3, all are achievable without new architectural risk, and the majority require zero new library dependencies because the existing stack already provides the building blocks.

The recommended approach follows the Adapter ABC pattern already established by `PaymentAdapter` and `ObservabilityAdapter` in the codebase. Transactional email gets `EmailAdapter` + `django-anymail` v14 with Resend as the default ESP (SendGrid was officially dropped by anymail in June 2025 and must not be used as default). Social auth extends the already-installed Django Allauth 65.x by activating provider subpackages in `INSTALLED_APPS` — no new Python package is required. GDPR hard delete uses `user.delete()` via a `UserDeletionService` orchestrator that handles Stripe and PostHog cleanup before the ORM cascade fires. RBAC uses Django Groups (already present via `django.contrib.auth`) with a 30-line `require_role` decorator. Feature entitlements are a pure function that reads the existing `BILLING_PLANS` settings dict against the user's active `Subscription` — no new model, no new migration.

The critical risks are concentrated in two features. Apple Sign In on mobile requires a dedicated server-side native token verification endpoint because Expo's `expo-apple-authentication` produces a JWT with a different audience claim than Allauth's standard social token flow expects — using the standard flow will fail silently with an audience mismatch error. GDPR deletion will leave orphaned data in Stripe, PostHog, and Allauth tables if `user.delete()` is called directly without the `UserDeletionService` orchestrator. Both risks are well-understood and preventable with the implementation patterns documented in the research. The dependency-driven build order is: email first, then social auth, then RBAC, then GDPR, then entitlements.

## Key Findings

### Recommended Stack

The v1.3 stack additions are minimal by design. Only two new Python packages and two new mobile packages are required. GDPR, RBAC, and feature entitlements use zero new dependencies.

**Core technologies (net-new for v1.3):**

- `django-anymail >= 14.0,<15`: Django email backend abstraction for 14+ ESP providers — keeps application code provider-agnostic; install with `uv add "django-anymail>=14.0,<15"`
- `premailer >= 3.10,<4`: CSS inlining for HTML email templates — email clients strip `<style>` blocks; `premailer.transform(html, allow_network=False)` converts them to inline attributes before dispatch
- `@react-native-google-signin/google-signin @ ^16.1.2`: Native Google Sign In for Expo managed workflow — requires a development build; does not work in Expo Go
- `expo-apple-authentication @ ~55.0.8`: Native Apple Sign In — SDK 53 bundled; iOS only; mandatory if any other social login is present (App Store policy)
- Django Allauth social providers (no new install): Google, GitHub, and Apple provider apps are activated in `INSTALLED_APPS` only — allauth 65.15.0 is already installed
- Django Groups + `BasePermission` (no new install): RBAC carrier; `django.contrib.auth.models.Group` is present in every Django project by default
- Settings-driven `has_feature()` (no new install): reads existing `BILLING_PLANS` config against `PlanProviderMapping` table

**ESP default correction:** ARCHITECTURE.md was written with an earlier assumption of SendGrid as the default. FEATURES.md and STACK.md both correctly identify Resend as the default ESP. Implementation must use `RESEND_API_KEY`, not `SENDGRID_API_KEY`, in `.env.example` and settings.

See `.planning/research/STACK.md` for full rationale, version compatibility matrix, and complete environment variable inventory.

### Expected Features

All eight sub-features are P1 for v1.3. None can be deferred without compromising the "functional baseline" milestone goal.

**Must have (table stakes — expected in every production SaaS):**

- Transactional email with Celery queue — password reset, email verification, billing receipts; ad-hoc Django email sends create unmaintainable tech debt
- Social login (Google + GitHub on web) — reduces signup friction; expected as standard UX in 2025
- GDPR account hard delete (Article 17) — EU legal requirement; not optional for any EU-facing product
- GDPR data export (Article 20) — EU legal requirement; right to portability
- Cookie consent banner — ePrivacy Directive requirement when PostHog analytics cookies are set
- RBAC with admin and member roles — minimum access control for any multi-user product
- Plan-gated feature entitlements — closes the billing loop opened in v1.1

**Should have (competitive differentiators for a template):**

- EmailAdapter ABC with swappable ESPs (mirrors PaymentAdapter pattern) — developers can switch from Resend to Mailgun with one settings change
- Apple Sign In on mobile — most competing templates skip this, creating App Store rejection risk for downstream products that also ship Google Sign In
- Async Celery-based GDPR deletion — large account deletion would time out a synchronous HTTP request
- `--without email` and `--without social-auth` scaffolder flags — extends the existing modular scaffolder pattern

**Defer (future milestones):**

- MFA via Allauth MFA module — Allauth headless MFA is ready when the product needs it
- Additional social providers (Facebook, LinkedIn) — per-product decision; not worth template complexity
- Object-level permissions via Django Guardian — requires product-specific model knowledge
- ABAC / policy engines (Casbin, OPA) — enterprise multi-tenant use cases only

See `.planning/research/FEATURES.md` for full dependency graph, competitor analysis (vs. SaaSPegasus, Bedrock), anti-feature rationale, and MVP definition.

### Architecture Approach

All five v1.3 features are additive to the existing layered architecture. One new Django app (`apps/notifications/`), three new files in existing apps (`gdpr.py`, `rbac.py`, `entitlements.py`), and corresponding web and mobile components are added. No existing module is rearchitected. The Adapter ABC pattern, comment-delimited scaffolder blocks, service-layer isolation, and signal-driven side effects are each extended — not replaced.

**Major components added:**

1. `apps/api/apps/notifications/` (NEW) — EmailAdapter ABC; `django-anymail` Resend backend; Celery task with `transaction.on_commit()`; HTML + plain-text email templates
2. `apps/api/apps/accounts/gdpr.py` (NEW) — `UserDeletionService` (orchestrates Stripe + PostHog cleanup before ORM cascade); `UserDataExportService` (aggregates User, EmailAddress, SocialAccount, BillingProfile, Subscription, Invoice)
3. `apps/api/apps/accounts/rbac.py` (NEW) — `require_role()` decorator; `IsInGroup` Ninja Extra permission class; data migration seeding `admin`, `moderator`, `viewer` groups
4. `apps/api/apps/billing/entitlements.py` (NEW) — `has_feature(user, key)` utility; reads `BILLING_PLANS` settings dict against `PlanProviderMapping` table
5. Social auth provider configuration (MODIFIED) — `SOCIALACCOUNT_PROVIDERS` dict and provider apps added to `INSTALLED_APPS` in `config/settings/base.py`
6. `apps/web/src/components/consent/cookie-banner.tsx` (NEW) — `"use client"` component returning `null` on server render; `localStorage`-backed consent gates PostHog `opt_in_capturing()`
7. `apps/mobile/lib/auth/apple.ts` (NEW) — `expo-apple-authentication` native token flow; POSTs to a dedicated Django verification endpoint (not Allauth's standard social token endpoint)

**Build order (dependency-driven, confirmed by architecture research):**
Phase A (Email) → Phase B (Social Auth) → Phase C (RBAC) → Phase D (GDPR) → Phase E (Entitlements)

See `.planning/research/ARCHITECTURE.md` for full component diagrams, data flows, integration mapping table, anti-patterns, and per-phase build steps.

### Critical Pitfalls

1. **Apple Sign In native token audience mismatch** — Expo's `expo-apple-authentication` returns a JWT with `aud` = Bundle ID (App ID). Allauth's standard `/_allauth/app/v1/auth/provider/token` endpoint expects a web OAuth token with `aud` = Services ID. Passing the native token to the standard endpoint fails with `jwt.InvalidAudienceError`. Fix: build a dedicated Django endpoint that verifies the native JWT against Apple's public JWKS (`https://appleid.apple.com/auth/keys`), then uses allauth's internal socialaccount APIs to connect the account. Design this endpoint before writing any Expo-side Apple auth code. Recovery cost: HIGH.

2. **Social auth email collision creates duplicate accounts** — Allauth's default (`SOCIALACCOUNT_EMAIL_AUTHENTICATION=False`) blocks social login for an email that already has a password account, or creates a second user. Fix: set `SOCIALACCOUNT_EMAIL_AUTHENTICATION=True` and `SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT=True` for Google and GitHub; write a custom `SocialAccountAdapter.pre_social_login()` that handles the merge. Do NOT enable auto-connect for Apple (relay addresses). This must be in place before any social provider is activated in production. Recovery cost: HIGH.

3. **Celery email task dispatched before DB transaction commits** — With `ATOMIC_REQUESTS=True` (the template default), `send_welcome_email.delay(user.id)` called immediately after `User.objects.create_user()` runs before the row is committed. The Celery worker gets `User.DoesNotExist`. Fix: always wrap every email task dispatch in `transaction.on_commit(lambda: send_welcome_email.delay(...))`. This is a mandatory code pattern, not an option. Recovery cost: LOW to fix, but silent failures cause user trust damage.

4. **GDPR deletion leaves orphaned data in third-party systems** — `user.delete()` cascades Django ORM relations but does not call `stripe.Customer.delete()`, `posthog.delete()`, or clean up Celery task results. Stripe customer records containing PII persist after the Django user row is gone — a GDPR Article 17 violation. Fix: implement `UserDeletionService` that calls external service deletion APIs before the ORM cascade. Add a post-deletion assertion test. Recovery cost: HIGH.

5. **Stale feature entitlement cache after plan change** — If `has_feature()` results are cached without explicit webhook-driven invalidation, a user who downgrades continues accessing premium features until the TTL expires. Fix: call `cache.delete()` for the user's entitlement key in the Stripe webhook handler when `customer.subscription.updated` fires. Keep TTL at 5-15 minutes as a backstop. Recovery cost: LOW technically, HIGH for user trust and potential refund disputes.

See `.planning/research/PITFALLS.md` for 15 pitfalls across critical, moderate, and minor severity levels, including a security mistakes table, UX pitfalls table, performance traps table, and a "Looks Done But Isn't" verification checklist.

## Implications for Roadmap

The dependency graph drives a 5-phase structure. Each phase delivers independently testable functionality before the next phase begins.

### Phase 1: Transactional Email

**Rationale:** Zero dependencies on other v1.3 features. Establishes the email infrastructure that social auth (Phase 2) needs for welcome emails and GDPR (Phase 4) needs for deletion confirmation emails. The lowest-risk starting point.
**Delivers:** `apps/notifications/` Django app; `EmailAdapter` ABC; `django-anymail` + ResendAdapter (default) + ConsoleAdapter (dev/test); Celery task using `transaction.on_commit()`; HTML + plain-text email templates (welcome, email-verify, password-reset, password-changed, subscription-created, subscription-cancelled); `--without email` scaffolder flag.
**Addresses:** Transactional email table-stakes feature; EmailAdapter ABC differentiator.
**Avoids:** Celery task before DB commit (Pitfall 3); HTML-only email without plain-text fallback (Pitfall 12); synchronous email in request cycle (Anti-Pattern 3).
**Research flag:** Standard pattern — mirrors existing PaymentAdapter/ObservabilityAdapter. Skip `/gsd:research-phase`.

### Phase 2: Social Auth (Google + GitHub web; Apple mobile)

**Rationale:** Allauth is already installed; provider activation is additive. Must precede RBAC and GDPR so that social users are covered by the same deletion and role policies from day one. The Apple Sign In architecture decision (dedicated native token endpoint) must be locked before any Expo-side code is written.
**Delivers:** `SOCIALACCOUNT_PROVIDERS` settings for Google + GitHub; custom `FoundationSocialAccountAdapter` with email merge logic for trusted providers; `social-buttons.tsx` in web auth form; dedicated Django native Apple token verification endpoint (verifies against Apple JWKS, then connects via allauth socialaccount APIs); `expo-apple-authentication` integration on mobile; `--without social-auth` scaffolder flag.
**Addresses:** Social login table-stakes feature; Apple Sign In differentiator; App Store policy compliance.
**Avoids:** Apple native token audience mismatch (Pitfall 1); email collision creating duplicate accounts (Pitfall 2); OAuth redirect URI misconfiguration (Pitfall 8).
**Research flag:** The dedicated Apple native token endpoint is non-standard and the exact allauth 65.x internal API surface for `connect`-ing a pre-verified social account needs verification before plan committal. Recommend a 30-minute implementation spike on the allauth source code before planning this phase.

### Phase 3: RBAC (Django Groups + @require_role + Assignment API)

**Rationale:** Can be built independently of email and social auth. Placing RBAC before GDPR means the `IsAdminUser` guard is available for the data export endpoint, and the service-layer permission pattern is established before GDPR deletion code is written.
**Delivers:** `apps/accounts/rbac.py` with `require_role()` decorator and `IsInGroup` permission class; data migration seeding `admin`, `moderator`, `viewer` groups; role assignment API endpoints with role hierarchy enforcement (assigning user must hold a strictly higher role than the role being assigned); `RoleAssignmentIn` and `RoleOut` schemas.
**Addresses:** RBAC table-stakes feature.
**Avoids:** Permissions checked only at endpoint layer, not service layer (Pitfall 5); privilege escalation via unconstrained role assignment (Pitfall 11); Django Admin / application RBAC confusion (Pitfall 14).
**Research flag:** Standard pattern — mirrors `@require_active_subscription` decorator already in codebase. Skip `/gsd:research-phase`.

### Phase 4: GDPR Baseline (Hard Delete + Data Export + Cookie Consent)

**Rationale:** Session invalidation utilities are already in `accounts/services.py`; RBAC guards are available for the export endpoint (from Phase 3). Three sub-features have minimal coupling and can be developed in parallel within this phase. Cookie consent must gate PostHog before the template is considered production-ready.
**Delivers:** `UserDeletionService` orchestrating Stripe `stripe.Customer.delete()` + PostHog `posthog.delete()` + ORM `user.delete()` cascade; `DELETE /api/v1/accounts/me/` endpoint dispatching async Celery task; `UserDataExportService` with explicit sections for user profile, auth (EmailAddress, SocialAccount), billing (BillingProfile, Subscription, Invoice), and content; `GET /api/v1/accounts/me/export/` endpoint; `cookie-banner.tsx` client component with Zustand `localStorage` store; PostHog initialized with `opt_out_capturing_by_default=True`; account deletion confirmation page in web app.
**Addresses:** All three GDPR table-stakes features; async deletion differentiator.
**Avoids:** GDPR erasure missing third-party data (Pitfall 4); incomplete data export missing allauth/billing tables (Pitfall 9); Next.js App Router hydration mismatch on consent banner (Pitfall 10); soft-delete GDPR compliance trap (Anti-Pattern 5).
**Research flag:** Before planning, confirm that the existing `ObservabilityAdapter` exposes a `delete_identity(user_id)` method (or equivalent) for PostHog person deletion, and that the `BillingAdapter` exposes a `delete_customer(stripe_customer_id)` method. If not, these must be added as part of this phase scope.

### Phase 5: Feature Entitlements (has_feature + Plan Config + Cache Invalidation)

**Rationale:** Pure read-only logic layered on top of existing billing state. No schema changes. Safe to add last; requires the Billing module (`PlanProviderMapping` table) and confirmed subscription data shape.
**Delivers:** `apps/billing/entitlements.py` with `has_feature(user, key)` utility; `BILLING_PLANS` config updated in `config/settings/base.py` with explicit feature key lists per plan tier; `GET /api/v1/entitlements/` endpoint returning `{feature_key: bool}` map for the authenticated user; explicit cache invalidation wired into the Stripe webhook handler for `customer.subscription.updated`.
**Addresses:** Feature entitlements table-stakes feature; PostHog-vs-entitlements distinction.
**Avoids:** Stale entitlement cache after plan change (Pitfall 6); N+1 queries from `has_feature` in list views without `select_related` (Pitfall 15); feature flags stored in the database (Anti-Pattern 4).
**Research flag:** MEDIUM confidence on `PlanProviderMapping` price_id field name and subscription data shape. Verify that `user.billing_customer.subscription` and `PlanProviderMapping.price_id` match the actual model definitions in `apps/billing/models.py` before writing `has_feature()`. A 15-minute read of the billing models file at plan time resolves this.

### Phase Ordering Rationale

- Email before social auth: social auth's welcome email trigger requires the email adapter to be present; building email first means social auth immediately inherits working email dispatch
- Social auth before RBAC/GDPR: social users must fall under the same deletion and role policies; designing `UserDeletionService` before social auth exists risks missing `SocialAccount` table cleanup
- RBAC before GDPR: the data export endpoint benefits from the `IsAdminUser` guard; the service-layer permission pattern established in Phase 3 is the template for GDPR service functions in Phase 4
- Entitlements last: reads existing billing state as a read-only consumer; adding it after all other features are stable reduces the number of moving parts during implementation

### Research Flags

**Needs attention during `/gsd:plan-phase` (do not skip):**

- Phase 2 (Apple Sign In): The dedicated native token verification endpoint is non-standard. Verify the exact allauth 65.x internal API for connecting a pre-verified social account before committing the plan. Specifically: `allauth.socialaccount.models.SocialAccount` and the `sociallogin.connect()` method in allauth 65.x source.
- Phase 4 (GDPR): Confirm `ObservabilityAdapter` exposes a PostHog person deletion method and `BillingAdapter` exposes a Stripe customer deletion method before scoping this phase.
- Phase 5 (Entitlements): Read `apps/billing/models.py` at plan time to verify `PlanProviderMapping` field names match the `has_feature()` implementation assumptions.

**Standard patterns (safe to plan without additional research):**

- Phase 1 (Email): Adapter ABC + anymail + Celery is well-documented and the pattern is proven in the codebase.
- Phase 3 (RBAC): Django Groups + decorator mirrors `@require_active_subscription` exactly; no novel integration.
- Phase 4 cookie banner: Next.js 15 `"use client"` + `useEffect` + Zustand is a well-documented pattern per PostHog's official tutorial.

## Confidence Assessment

| Area         | Confidence  | Notes                                                                                                                                                                                                                                             |
| ------------ | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Stack        | HIGH        | Library versions verified via PyPI and npm at research time (2026-03-11); anymail 14.0, allauth 65.15.0, expo-apple-authentication 55.0.8, @react-native-google-signin 16.1.2 all confirmed current                                               |
| Features     | HIGH        | All features have clear implementation paths; scope is well-bounded; all P1 items are confirmed non-deferrable for the milestone                                                                                                                  |
| Architecture | HIGH        | Grounded in direct codebase inspection of `apps/billing/adapters.py`, `apps/billing/decorators.py`, `config/settings/base.py`; patterns are extensions of proven existing code                                                                    |
| Pitfalls     | MEDIUM-HIGH | Apple token, email account merge, Celery on_commit, and GDPR orphaned data pitfalls are HIGH confidence from official docs; PostHog and Celery task result cascade gaps are MEDIUM (API docs verified, not tested against this specific codebase) |

**Overall confidence:** HIGH

### Gaps to Address

- **Resend vs SendGrid ESP consistency**: ARCHITECTURE.md reflects an earlier SendGrid assumption; STACK.md and FEATURES.md correctly specify Resend. Implementation must use Resend. Ensure `.env.example` and all settings snippets reference `RESEND_API_KEY`.
- **Apple native token server-side verification**: The exact allauth 65.x internal API for connecting a pre-verified socialaccount needs source code verification before Phase 2 planning.
- **PostHog deletion API on ObservabilityAdapter**: `posthog.delete(distinct_id=...)` is documented as the correct call; verify this method is exposed (or needs to be added) to the existing `ObservabilityAdapter` before scoping Phase 4.
- **PlanProviderMapping price_id lookup**: `has_feature()` assumes `PlanProviderMapping.price_id` maps to the subscription's provider price ID. Verify this field name in `apps/billing/models.py` at Phase 5 plan time — MEDIUM confidence from architecture research.
- **Apple p8 key expiry**: Apple developer private keys used for Sign In with Apple expire every 6 months. This is a non-obvious operational requirement. Document it prominently in the Phase 2 implementation notes and in `apps/mobile/README.md`.

## Sources

### Primary (HIGH confidence)

- [django-anymail PyPI](https://pypi.org/project/django-anymail/) — v14.0, December 2025; SendGrid support dropped June 2025
- [django-anymail GitHub](https://github.com/anymail/django-anymail) — Resend adapter, provider list, SendGrid drop issue #432
- [django-allauth PyPI](https://pypi.org/pypi/django-allauth/json) — v65.15.0, March 9, 2026
- [django-allauth Google provider docs](https://docs.allauth.org/en/dev/socialaccount/providers/google.html) — PKCE, OAuth2 setup, scope
- [django-allauth Apple provider docs](https://docs.allauth.org/en/dev/socialaccount/providers/apple.html) — two client IDs (Bundle ID vs. Services ID), POST flow, SameSite warning
- [django-allauth headless integrations](https://docs.allauth.org/en/latest/headless/integrations.html) — x_session_token_auth, provider token flow
- [Expo Apple Authentication docs](https://docs.expo.dev/versions/latest/sdk/apple-authentication/) — managed workflow, App Store mandatory requirement
- [Expo Google Authentication guide](https://docs.expo.dev/guides/google-authentication/) — `@react-native-google-signin/google-signin` as official recommendation
- [django-ninja-extra permissions docs](https://eadwincode.github.io/django-ninja-extra/api_controller/api_controller_permission/) — BasePermission, combining operators
- Existing codebase (direct inspection): `apps/billing/adapters.py`, `apps/billing/decorators.py`, `apps/core/observability.py`, `apps/accounts/services.py`, `config/settings/base.py`, `config/urls.py`

### Secondary (MEDIUM confidence)

- [PostHog Next.js cookie banner tutorial](https://posthog.com/tutorials/nextjs-cookie-banner) — consent banner + PostHog opt-in/opt-out flow for Next.js 15
- [Mailtrap deliverability study March 2025](https://mailtrap.io/blog/sendgrid-vs-mailgun/) — ESP inbox placement comparison (Mailgun 71.4% vs SendGrid 61.0%)
- [Django RBAC guide — Permit.io](https://www.permit.io/blog/how-to-implement-role-based-access-control-rbac-into-a-django-application) — group-based RBAC pattern
- GDPR Articles 15, 17, 20 — data access, erasure, and portability requirements

### Tertiary (for awareness)

- [SaaS entitlements patterns — Orb](https://www.withorb.com/blog/what-are-entitlements-in-saas) — entitlement vs. feature flag conceptual distinction
- [LaunchDarkly: entitlements vs feature flags](https://launchdarkly.com/blog/how-to-manage-entitlements-with-feature-flags/) — when to use plan gates vs. rollout flags
- [GDPR for SaaS — CookieYes 2025 guide](https://www.cookieyes.com/blog/gdpr-for-saas/) — GDPR compliance checklist for SaaS products

---

_Research completed: 2026-03-11_
_Ready for roadmap: yes_
