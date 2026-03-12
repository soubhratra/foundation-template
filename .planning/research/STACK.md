# Stack Research: SaaS Functional Baseline (v1.3)

**Project:** Foundation Template — v1.3 milestone
**Domain:** SaaS functional baseline — transactional email, social auth, GDPR, RBAC, feature entitlements
**Researched:** 2026-03-11
**Overall confidence:** HIGH for library choices; MEDIUM for exact patch versions (verify at install time)

> **Scope note:** This document covers ONLY the net-new libraries needed for v1.3.
> The core stack (Django Ninja Extra, Next.js 15+, Expo SDK 53+, Django Allauth headless,
> Celery + Redis, structlog, OpenTelemetry, PostHog, Stripe, WeasyPrint, Turborepo, pnpm,
> pytest, Vitest, etc.) is already decided and is NOT re-researched here.
> See `.planning/research/STACK.md` (v1.1 edition) and `.planning/phases/` CONTEXT files
> for the validated prior-milestone stack decisions.

---

## Decision Summary

| Feature                              | Chosen Library / Approach                        | Version Pin                          | Confidence |
| ------------------------------------ | ------------------------------------------------ | ------------------------------------ | ---------- |
| Transactional email backend          | `django-anymail`                                 | `>=14.0,<15`                         | HIGH       |
| Default email provider               | SendGrid via anymail                             | `sendgrid` not installed directly    | HIGH       |
| Email HTML templating + CSS inlining | `premailer`                                      | `>=3.10,<4`                          | MEDIUM     |
| Social auth (web: Google + GitHub)   | `django-allauth` socialaccount providers         | already installed; add provider apps | HIGH       |
| Social auth token exchange (mobile)  | `django-allauth` headless provider token flow    | built into allauth 65.x              | HIGH       |
| Google Sign In (mobile)              | `@react-native-google-signin/google-signin`      | `^16.1.2`                            | MEDIUM     |
| Apple Sign In (mobile)               | `expo-apple-authentication`                      | `~55.0.8` (SDK 53 bundled)           | HIGH       |
| GDPR: account deletion               | Django ORM cascade (built-in) + custom service   | no new library                       | HIGH       |
| GDPR: data export                    | Django serialization framework (built-in)        | no new library                       | HIGH       |
| GDPR: cookie consent (web)           | Custom component — shadcn/ui primitives          | no new library                       | HIGH       |
| RBAC                                 | Django Groups + custom `BasePermission` subclass | built into django-ninja-extra        | HIGH       |
| Feature entitlements                 | Custom `has_feature()` — settings-driven config  | no new library                       | HIGH       |

**One-liner:** `django-anymail` v14 (SendGrid adapter) + `premailer` + allauth social providers
(already installed) + two mobile social auth packages + zero new libraries for GDPR/RBAC/entitlements.

---

## 1. Transactional Email

### Backend: django-anymail

| Technology       | Version      | Purpose                                                                                                         | Why                                                                                                                                                                                                                                                                                                                                                |
| ---------------- | ------------ | --------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `django-anymail` | `>=14.0,<15` | Django `EMAIL_BACKEND` implementation for multiple ESPs; replaces `django.core.mail.backends.smtp.EmailBackend` | Provides a single unified Django email backend interface for 14+ providers (SendGrid, Mailgun, Resend, SES, Postmark, Brevo, etc.). v14.0 released December 18, 2025. Works with standard `django.core.mail.send_mail` — no API calls to Anymail in application code. Swapping ESPs requires changing one `EMAIL_BACKEND` setting and credentials. |
| `premailer`      | `>=3.10,<4`  | Inline CSS in HTML email templates before sending                                                               | Email clients (Gmail, Outlook) strip `<style>` blocks from HTML emails. `premailer.transform()` converts CSS rules to inline `style=""` attributes before the message is handed to Anymail. v3.10.0 is the current stable release (Production/Stable on PyPI). Pure Python; no native dependencies.                                                |

**Why django-anymail over direct sendgrid SDK:**

The `sendgrid` Python SDK (v6.12.5, September 2025) is a full REST client for SendGrid's API.
Using it directly means:

1. Application code imports `sendgrid` — if the ESP changes, every call site changes.
2. Template rendering, HTML construction, and attachment handling are reimplemented per-provider.

`django-anymail` maps SendGrid (and every other supported ESP) onto Django's standard
`EmailMessage` / `EmailMultiAlternatives` interface. Application code calls
`send_mail(...)` or constructs `EmailMultiAlternatives` — the ESP is a configuration concern only.
The `EmailAdapter` ABC described in the v1.3 requirements wraps `django.core.mail` (not anymail
directly), meaning anymail fulfills the SendGrid-specific transport layer while the adapter ABC
provides the application-level interface with Celery queuing, template resolution, and retry logic.

**Why not django-sendgrid-v5 (`django-sendgrid-v5` 1.3.0, May 2025):**
SendGrid-only. Locks the backend to SendGrid at the Django settings level. If a project uses
Resend or Mailgun, the entire backend swap requires finding a different package. Anymail handles
all ESPs with one integration.

**Why not plain SMTP (`django.core.mail.backends.smtp.EmailBackend`):**
SMTP through SendGrid works but lacks transactional features: no per-message delivery tracking,
no batch send metadata, no webhook correlation IDs, no dynamic template support. Anymail exposes
these as optional attributes on `EmailMessage` via the `esp_extra` dict — accessible if needed
but not required.

**SendGrid as default ESP (not Mailgun or Resend):**
All three are viable. SendGrid chosen as the default because:

- Widest market recognition — most developers expect it as the default example
- Template system (Dynamic Templates) is well-documented
- Anymail adapter exists and is actively maintained

Mailgun and Resend are drop-in swaps via anymail — no code changes needed in the email module,
only `EMAIL_BACKEND` + credentials in settings. Per Mailtrap's March 2025 deliverability study,
Mailgun has higher inbox placement (71.4% vs 61.0%) — individual projects should evaluate and swap.

**CSS inlining with premailer:**
`premailer.transform(html_string)` is called inside the `EmailAdapter` service layer before
the message is constructed. This keeps the template files clean (standard CSS in `<style>` blocks)
while ensuring email client compatibility. The `allow_network=False` option prevents premailer
from downloading external stylesheets — always pass this in production.

### Net-New Environment Variables

| Variable             | Where           | Notes                                                        |
| -------------------- | --------------- | ------------------------------------------------------------ |
| `SENDGRID_API_KEY`   | `apps/api/.env` | Anymail reads this via `ANYMAIL["SENDGRID_API_KEY"]` setting |
| `DEFAULT_FROM_EMAIL` | `apps/api/.env` | Django standard setting; anymail passes it through           |
| `EMAIL_ENABLED`      | `apps/api/.env` | Feature flag for `--without email` CLI scaffolder removal    |

---

## 2. Social Auth

### Backend: django-allauth socialaccount providers (no new Python package)

django-allauth 65.15.0 (released March 9, 2026, verified via PyPI) is already installed. Social
authentication requires only activating the provider apps in `INSTALLED_APPS` — no additional
Python package installs.

**Providers needed:**

| Provider | INSTALLED_APPS entry                     | Notes                                                 |
| -------- | ---------------------------------------- | ----------------------------------------------------- |
| Google   | `allauth.socialaccount.providers.google` | OAuth2 + PKCE recommended; `OAUTH_PKCE_ENABLED: True` |
| GitHub   | `allauth.socialaccount.providers.github` | OAuth2; minimal scope `['user', 'email']`             |
| Apple    | `allauth.socialaccount.providers.apple`  | Apple-specific JWT signing (P8 private key)           |

**Key configuration decision — Apple requires two client IDs:**
Apple distinguishes between the "Services ID" (used by web browsers) and the "Bundle ID" (used
by iOS apps). Configure two separate `APPS` entries in `SOCIALACCOUNT_PROVIDERS['apple']`:
one for web with the Services ID, one for mobile with the Bundle ID and `"hidden": True`.
The hidden entry is excluded from web login button rendering but is active for the headless
provider token endpoint.

**Headless mobile token exchange (allauth built-in, no extra package):**
allauth 65.x ships `allauth.headless` with a "provider token" flow. The mobile app obtains an
identity token natively (via `expo-apple-authentication` or `@react-native-google-signin`) and
POSTs it to `/_allauth/app/v1/auth/provider/token`. allauth validates the token server-side,
creates or retrieves the user, and returns a session token or JWT. This flow is documented in
allauth's headless integrations page and requires no additional library.

**Django Ninja security class for headless session tokens:**
allauth 65.x ships `allauth.headless.tokens.sessions.x_session_token_auth` — a Django Ninja
security class that authenticates requests carrying the `X-Session-Token` header. Add to
Ninja API controllers where mobile-origin requests need authentication.

**Why not `social-auth-app-django` (Python Social Auth):**
PSA is a separate, full-featured social auth library unrelated to allauth. Installing it alongside
allauth creates two parallel user identity management systems. allauth is already the decided
auth framework and its social account support is production-grade — adding PSA adds complexity
and model coupling with no benefit.

**Why not Clerk or Auth0 for social auth:**
Both are external auth-as-a-service products. The template's architecture decision is to own
authentication via Django Allauth — no external auth service dependency. Social providers in
allauth are configuration (client ID + secret), not infrastructure.

### Mobile: Google Sign In

| Technology                                  | Version   | Purpose                                                     | Why                                                                                                                                                                                                                                                                                                                                                                                       |
| ------------------------------------------- | --------- | ----------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `@react-native-google-signin/google-signin` | `^16.1.2` | Native Google Sign In button + ID token for iOS and Android | Official, actively maintained Google Sign In library for React Native. Works with Expo managed workflow via config plugin (no ejecting required). Returns an ID token that is POSTed to allauth's headless provider token endpoint. v16.1.2 is the current release (npm, March 2026). Provides GoogleSignin.hasPlayServices(), signIn(), getTokens() — the token flow is well-documented. |

**Critical limitation:** Cannot be used in Expo Go. Requires a development build (`eas build --profile development`) or `npx expo run:ios` / `npx expo run:android`. Document this prominently in `apps/mobile/README.md`.

**Why not `expo-auth-session/providers/google`:**
`expo-auth-session` uses an OAuth web redirect flow (browser modal) — not a native Google Sign In
sheet. The UX is inferior (redirects to a webview) and does not use the native Google SDK. For
template-quality defaults, the native library is preferred.

### Mobile: Apple Sign In

| Technology                  | Version   | Purpose                                          | Why                                                                                                                                                                                                                                                                                              |
| --------------------------- | --------- | ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `expo-apple-authentication` | `~55.0.8` | Native Apple Sign In button + credential for iOS | First-party Expo package (SDK 53 bundled). v55.0.8 confirmed via npm. Config plugin sets `ios.usesAppleSignIn: true` automatically. Returns a credential with an `identityToken` (JWT) that is POSTed to allauth's headless provider token endpoint. iOS only — conditionally render the button. |

**App Store requirement:** Apple Sign In is mandatory in any iOS app that offers any third-party
social sign-in option. If Google Sign In ships, Apple Sign In must also ship. This is an App Store
Review guideline — not optional.

**Configuration:** Add `"ios.usesAppleSignIn": true` to `app.json`. EAS Build handles the
capability entitlement automatically.

### Net-New Environment Variables

| Variable                               | Where              | Notes                                                |
| -------------------------------------- | ------------------ | ---------------------------------------------------- |
| `GOOGLE_CLIENT_ID`                     | `apps/api/.env`    | OAuth2 client ID from Google Cloud Console           |
| `GOOGLE_CLIENT_SECRET`                 | `apps/api/.env`    | OAuth2 client secret                                 |
| `GITHUB_CLIENT_ID`                     | `apps/api/.env`    | OAuth app client ID from GitHub settings             |
| `GITHUB_CLIENT_SECRET`                 | `apps/api/.env`    | OAuth app client secret                              |
| `APPLE_CLIENT_ID`                      | `apps/api/.env`    | Services ID (web)                                    |
| `APPLE_MOBILE_CLIENT_ID`               | `apps/api/.env`    | Bundle ID (iOS)                                      |
| `APPLE_SECRET`                         | `apps/api/.env`    | Key ID from Apple Developer Console                  |
| `APPLE_KEY`                            | `apps/api/.env`    | Member ID / App ID Prefix                            |
| `APPLE_CERTIFICATE_KEY`                | `apps/api/.env`    | P8 private key (multi-line; use base64 or file path) |
| `SOCIAL_AUTH_ENABLED`                  | `apps/api/.env`    | Feature flag for `--without social-auth` CLI removal |
| `EXPO_PUBLIC_GOOGLE_CLIENT_ID_IOS`     | `apps/mobile/.env` | iOS OAuth client ID (from Google Cloud Console)      |
| `EXPO_PUBLIC_GOOGLE_CLIENT_ID_ANDROID` | `apps/mobile/.env` | Android OAuth client ID                              |

---

## 3. GDPR Baseline

No new Python or JavaScript library is needed. All three GDPR requirements are implemented
using existing capabilities in the stack.

### Account Hard Delete + Cascade

Django ORM's `on_delete=CASCADE` on all ForeignKey fields referencing `User` handles cascade
deletion of related records when `user.delete()` is called. The implementation is:

1. A `DELETE /api/v1/account/` endpoint that calls `request.user.delete()` after confirmation.
2. A Celery task for any cleanup that must happen asynchronously (e.g., canceling Stripe
   subscription before deleting the user record).
3. An allauth signal (`user_logged_out`) to invalidate sessions before deletion.

**Why not `django-gdpr-assist`:**
`django-gdpr-assist` (last meaningful release 2021, v1.4.2) provides anonymization helpers but
adds a separate middleware/mixin system on top of Django's ORM. For a template providing hard
delete (not anonymization), the ORM cascade is sufficient and cleaner. Adding a third-party GDPR
library for a feature Django already handles natively would be premature abstraction.

### JSON Data Export

Django's built-in serialization framework (`django.core.serializers.serialize('json', queryset)`)
produces JSON from any QuerySet. For a user data export, a service function collects all
user-owned model instances and serializes them into a structured JSON payload. No external library
is required. The endpoint returns a `Content-Disposition: attachment; filename=data-export.json`
response with the serialized payload.

**Pattern:**

```python
# apps/api/gdpr/services.py
import json
from django.core import serializers

def export_user_data(user) -> dict:
    return {
        "user": json.loads(serializers.serialize("json", [user])),
        "profile": json.loads(serializers.serialize("json", user.profile_set.all())),
        # Add other user-owned models here per product
    }
```

### Cookie Consent Banner (Next.js)

A custom component built from shadcn/ui primitives (`Card`, `Button`) with `localStorage`-backed
consent state. The project's PostHog integration already provides `posthog.opt_out_capturing()`
and `posthog.opt_in_capturing()` — the consent banner calls these on accept/decline.

**Why not a consent library (e.g., `shadcn-cookie-consent`, `@consent-manager`):**
Third-party consent libraries ship opinionated UI that conflicts with the project's Shadcn/ui
design system. A custom component is 60-80 lines, avoids a new dependency, and integrates
cleanly with the PostHog adapter's existing opt-out API. The shadcn/ui registry has
community examples (`shadcn-cookie-consent`) that serve as reference implementations.

---

## 4. RBAC

No new library. Django Groups + Django Ninja Extra's `BasePermission` system cover the full
requirement.

### Pattern

Django's `auth_group` and `auth_user_groups` tables are already created by `django.contrib.auth`
(always installed). Groups are the role carrier:

```python
# apps/api/core/permissions.py
from ninja_extra.permissions import BasePermission

class RequireRole(BasePermission):
    """Parameterized permission class — use as @require_role("admin")."""
    def __init__(self, *roles: str):
        self.roles = set(roles)

    def has_permission(self, request, controller) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.groups.filter(name__in=self.roles).exists()
```

Usage in controllers:

```python
@api_controller("/admin", permissions=[RequireRole("admin")])
class AdminController(ControllerBase):
    ...
```

**Built-in permission classes already in django-ninja-extra:**
`AllowAny`, `IsAuthenticated`, `IsAuthenticatedOrReadOnly`, `IsAdminUser`. The `RequireRole`
class above is the only new code — no library install.

**Role assignment API:** A `POST /api/v1/admin/users/{id}/roles` endpoint using
`user.groups.set([...])`. Requires `IsAdminUser` or `RequireRole("admin")` on the controller.

**Why not `django-rbac` or `django-guardian`:**
`django-guardian` adds row-level object permissions — not needed for role-based endpoint
access control. `django-rbac` on PyPI has not been updated since 2018. Django Groups + custom
`BasePermission` is 30 lines and has zero migration overhead beyond what `django.contrib.auth`
already provides.

**Why not `django-rules`:**
`django-rules` is excellent for complex predicate-based permissions but adds a DSL on top of
Django's permission system. For template-level RBAC, the requirement is group membership checks
— not predicates. Groups are simpler and universally understood.

---

## 5. Feature Entitlements

No new library. A settings-driven `has_feature(user, feature_key)` function checks the user's
active plan tier against a plan-feature config dict in Django settings.

### Pattern

```python
# apps/api/entitlements/services.py
from django.conf import settings

PLAN_FEATURES: dict[str, set[str]] = getattr(settings, "PLAN_FEATURES", {})

def has_feature(user, feature_key: str) -> bool:
    """Check if user's active billing plan includes feature_key."""
    plan = getattr(user, "active_plan_tier", "free")  # from billing module
    allowed_features = PLAN_FEATURES.get(plan, set())
    return feature_key in allowed_features
```

```python
# settings/base.py
PLAN_FEATURES = {
    "free": {"basic_analytics"},
    "pro": {"basic_analytics", "advanced_reports", "api_access"},
    "enterprise": {"basic_analytics", "advanced_reports", "api_access", "sso", "audit_log"},
}
```

This is pure Django settings — no database query, no migration, no new library. Invalidation
requires a settings redeploy (acceptable for a template). Individual products that need
dynamic plan features (e.g., per-customer feature flags) should add django-waffle or PostHog
feature flags on top — both are already partially available in the v1.2 stack.

**Why not django-waffle (`5.0.0`):**
django-waffle provides database-backed feature flags with per-user, per-group, and percentage
rollout controls. It is the right tool when feature availability needs to change without a
redeploy or when A/B testing is needed. For the template baseline, the requirement is
plan-tier entitlements — a static mapping that changes with billing plan changes, not runtime
toggles. The settings-driven pattern is simpler and has zero additional dependencies.

**Why not PostHog feature flags:**
PostHog feature flags are already available via the ObservabilityAdapter. They add network
latency (one HTTP call per flag evaluation or a cached SDK call) and are appropriate for
gradual rollouts. Plan-based entitlements are deterministic (user's plan → feature set) and
should be evaluated locally without a network call.

---

## Alternatives Considered

| Category                    | Recommended                                 | Alternative                          | Why Not                                                                               |
| --------------------------- | ------------------------------------------- | ------------------------------------ | ------------------------------------------------------------------------------------- |
| Transactional email backend | `django-anymail`                            | `sendgrid` SDK directly              | Direct SDK = provider lock-in in app code; anymail keeps code provider-agnostic       |
| Transactional email backend | `django-anymail`                            | `django-sendgrid-v5`                 | SendGrid-only; anymail supports 14+ providers with identical API                      |
| Email CSS inlining          | `premailer`                                 | `inlinestyler`                       | inlinestyler is unmaintained; premailer is the standard                               |
| Social auth library         | allauth (already installed)                 | `social-auth-app-django` (PSA)       | Two parallel identity systems; allauth is the decided framework                       |
| Mobile Google Sign In       | `@react-native-google-signin/google-signin` | `expo-auth-session/providers/google` | Web redirect UX (webview modal) vs native Google Sign In sheet; native is better UX   |
| GDPR data export            | Built-in Django serializers                 | `django-gdpr-assist`                 | Last updated 2021; overkill for hard-delete + JSON export; Django ORM covers the need |
| Cookie consent              | Custom shadcn/ui component                  | `shadcn-cookie-consent` npm package  | Third-party UI conflicts with design system; custom is 60-80 lines                    |
| RBAC                        | Django Groups + `BasePermission`            | `django-guardian`                    | Object-level permissions not needed; group membership is the requirement              |
| RBAC                        | Django Groups + `BasePermission`            | `django-rules`                       | Predicate DSL overkill for role membership checks                                     |
| Feature entitlements        | Settings-driven `has_feature()`             | `django-waffle`                      | Runtime toggles not needed; plan-tier mapping is deterministic                        |
| Feature entitlements        | Settings-driven `has_feature()`             | PostHog feature flags                | Network latency; not appropriate for synchronous entitlement checks                   |

---

## What NOT to Add

| Avoid                                           | Why                                                               | Use Instead                                                 |
| ----------------------------------------------- | ----------------------------------------------------------------- | ----------------------------------------------------------- |
| `sendgrid` Python SDK as a direct dependency    | Creates provider lock-in in application code; anymail wraps it    | `django-anymail` with `ANYMAIL["SENDGRID_API_KEY"]` setting |
| `dj-rest-auth` for social auth token exchange   | Not using DRF; allauth headless has native Ninja integration      | allauth headless provider token endpoint                    |
| `python-social-auth` / `social-auth-app-django` | Parallel identity system to allauth; conflicts with existing auth | allauth social providers (already installed)                |
| `django-gdpr-assist`                            | Last updated 2021; anonymization-focused, not hard-delete         | Django ORM cascade + custom service                         |
| `django-guardian`                               | Row-level object permissions — not the requirement                | Django Groups + `RequireRole(BasePermission)`               |
| `django-waffle` (for entitlements)              | Adds DB queries and admin UI overhead for a static mapping        | Settings-based `PLAN_FEATURES` dict                         |

---

## Module Removability (CLI Scaffolder Contract)

### `--without email`

Remove: `django-anymail` + `premailer` from `pyproject.toml`. Remove `apps/api/email/` directory.
Remove `EMAIL_BACKEND`, `ANYMAIL`, `DEFAULT_FROM_EMAIL` from settings. Remove email templates
from `apps/api/templates/email/`.

### `--without social-auth`

Remove: `allauth.socialaccount.providers.google`, `allauth.socialaccount.providers.github`,
`allauth.socialaccount.providers.apple` from `INSTALLED_APPS`. Remove social credential env vars.
On mobile: remove `@react-native-google-signin/google-signin` and `expo-apple-authentication`.
Remove social login buttons from `apps/web/` and `apps/mobile/` auth screens.
Note: `allauth.socialaccount` core app can remain installed (it adds the `socialaccount_*` tables
but causes no harm). Removing it would require running `migrate --prune` — leave it installed,
just remove provider-specific apps.

---

## Installation Commands

```bash
# Python — inside apps/api/
uv add "django-anymail>=14.0,<15"
uv add "premailer>=3.10,<4"

# No new Python packages for GDPR, RBAC, or feature entitlements.
# No new Python packages for social auth (allauth is already installed; add provider apps
# to INSTALLED_APPS only).

# Mobile — from monorepo root
pnpm --filter mobile add @react-native-google-signin/google-signin@^16.1.2
pnpm --filter mobile add expo-apple-authentication@~55.0.8

# No new web packages for social auth (OAuth redirects are backend-initiated).
# No new web packages for cookie consent (custom shadcn/ui component, no install).
```

---

## Version Compatibility

| Package                                     | Version   | Django  | Python | Notes                                                                        |
| ------------------------------------------- | --------- | ------- | ------ | ---------------------------------------------------------------------------- |
| `django-anymail`                            | `14.0`    | 4.0–6.0 | ≥3.8   | Verified December 2025                                                       |
| `premailer`                                 | `3.10.0`  | any     | 3.5+   | Production/Stable; last release August 2021 — no concerns for stable utility |
| `django-allauth`                            | `65.15.0` | 4.2–6.0 | ≥3.10  | Already installed; v65.15.0 March 9, 2026                                    |
| `@react-native-google-signin/google-signin` | `16.1.2`  | —       | —      | Expo SDK 53 managed workflow: requires dev build, not Expo Go                |
| `expo-apple-authentication`                 | `55.0.8`  | —       | —      | SDK 53 bundled version; iOS only                                             |

---

## Sources

- [django-anymail PyPI](https://pypi.org/project/django-anymail/) — v14.0, December 18, 2025; 14 supported ESPs (HIGH — PyPI metadata)
- [django-anymail GitHub](https://github.com/anymail/django-anymail) — provider list, backend pattern, mixing backends docs (HIGH — official repo)
- [sendgrid PyPI](https://pypi.org/project/sendgrid/) — v6.12.5, September 19, 2025 (HIGH — PyPI metadata)
- [premailer PyPI](https://pypi.org/project/premailer/) — v3.10.0, August 2021, Production/Stable (HIGH — PyPI metadata)
- [django-allauth PyPI JSON](https://pypi.org/pypi/django-allauth/json) — v65.15.0, March 9, 2026 (HIGH — PyPI JSON API)
- [django-allauth Google provider docs](https://docs.allauth.org/en/latest/socialaccount/providers/google.html) — PKCE, scope, OAuth2 setup (HIGH — official docs)
- [django-allauth GitHub provider docs](https://docs.allauth.org/en/latest/socialaccount/providers/github.html) — scope, callback URL (HIGH — official docs)
- [django-allauth Apple provider docs](https://docs.allauth.org/en/latest/socialaccount/providers/apple.html) — two client IDs (Services ID vs Bundle ID), POST flow, SameSite cookie warning (HIGH — official docs)
- [django-allauth headless integrations](https://docs.allauth.org/en/latest/headless/integrations.html) — `x_session_token_auth` Django Ninja security class (HIGH — official docs)
- [django-allauth recent release notes](https://docs.allauth.org/en/dev/release-notes/recent.html) — v65.13.1 JWT token strategy, v65.x Django Ninja support, provider token flow (HIGH — official docs)
- [expo-apple-authentication Expo docs](https://docs.expo.dev/versions/latest/sdk/apple-authentication/) — managed workflow config, App Store requirement for Apple Sign In, `ios.usesAppleSignIn` setting (HIGH — official Expo docs)
- [Expo Google authentication guide](https://docs.expo.dev/guides/google-authentication/) — `@react-native-google-signin/google-signin` as recommended library (HIGH — official Expo docs)
- [react-native-google-signin Expo setup](https://react-native-google-signin.github.io/docs/setting-up/expo) — config plugin, dev build requirement (HIGH — official library docs)
- [@react-native-google-signin/google-signin npm](https://www.npmjs.com/package/@react-native-google-signin/google-signin) — v16.1.2 current (MEDIUM — npm registry, confirmed via `npm show`)
- [expo-apple-authentication npm](https://www.npmjs.com/package/expo-apple-authentication) — v55.0.8 current (MEDIUM — confirmed via `npm show`)
- [django-ninja-extra permissions docs](https://eadwincode.github.io/django-ninja-extra/api_controller/api_controller_permission/) — `BasePermission`, `has_permission`, combining with `&`/`|`/`~` (HIGH — official docs)
- [Mailtrap deliverability study March 2025](https://mailtrap.io/blog/sendgrid-vs-mailgun/) — Mailgun 71.4% vs SendGrid 61.0% inbox placement (MEDIUM — third-party study)
- [django-gdpr-assist PyPI](https://pypi.org/project/django-gdpr-assist/) — v1.4.2, last release 2021 (HIGH — PyPI metadata; used to confirm staleness)

---

_Stack research for: Foundation Template v1.3 — SaaS Functional Baseline_
_Researched: 2026-03-11_
