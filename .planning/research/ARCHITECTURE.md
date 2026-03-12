# Architecture Research: v1.3 SaaS Functional Baseline

**Domain:** Full-stack SaaS monorepo — five cross-cutting features layered onto an existing Django Ninja Extra + Next.js 15 + Expo template
**Researched:** 2026-03-11
**Confidence:** HIGH — grounded in direct codebase inspection plus official documentation verification

---

## Standard Architecture

### System Overview (Current v1.2 State)

```
┌──────────────────────────────────────────────────────────────────────┐
│  CLIENT LAYER                                                        │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐   │
│  │  apps/web/       │  │  apps/mobile/    │  │  apps/landing/   │   │
│  │  Next.js 15 AR   │  │  Expo SDK 53     │  │  Static Next.js  │   │
│  │  Shadcn/ui       │  │  Expo Router     │  │  No API calls    │   │
│  └────────┬─────────┘  └────────┬─────────┘  └──────────────────┘   │
│           │                     │                                    │
│           │  packages/api-client (generated TS types + fetch hooks)  │
│           │  packages/business-logic, packages/ui, packages/validation│
└───────────┼─────────────────────┼────────────────────────────────────┘
            │ REST + Session/JWT  │ REST + JWT (Bearer)
┌───────────┼─────────────────────┼────────────────────────────────────┐
│  API LAYER│                     │                                    │
│  ┌────────┴─────────────────────┴──────────────────────────────┐    │
│  │  apps/api/  (Django Ninja Extra)                             │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │    │
│  │  │ accounts │ │ billing  │ │   core   │ │   ai     │        │    │
│  │  │ (auth)   │ │ (plans)  │ │(infra)   │ │(optional)│        │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘        │    │
│  │  allauth headless + Celery + structlog + OTel + Redis cache  │    │
│  └─────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────┘
            │
┌───────────┴──────────────────────────────────────────────────────────┐
│  DATA LAYER                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐   │
│  │  PostgreSQL  │  │    Redis     │  │  External Services        │   │
│  │  + PGVector  │  │  DB 0 Celery │  │  Stripe, PostHog, SendGrid│  │
│  │              │  │  DB 1 Cache  │  │  Google OAuth, GitHub     │   │
│  │              │  │  DB 2 Sessions│  │  Apple Sign In (mobile)  │   │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

### Existing Component Responsibilities

| Component                 | Responsibility                                                         | Files                                                           |
| ------------------------- | ---------------------------------------------------------------------- | --------------------------------------------------------------- |
| `apps/api/apps/accounts/` | Auth, user model, session + JWT via allauth headless                   | models.py, headless.py, services.py, sessions.py                |
| `apps/api/apps/billing/`  | Subscriptions, payments via PaymentAdapter ABC                         | adapters.py, decorators.py, models.py, services.py, webhooks.py |
| `apps/api/apps/core/`     | Infra: middleware, observability, health, rate limiting                | middleware.py, observability.py, tracing.py, ratelimit.py       |
| `apps/api/apps/ai/`       | Optional LangGraph agents, vector search (removable)                   | models.py, controllers.py, tasks.py                             |
| `config/settings/base.py` | Central config: adapter class paths, feature flags                     | Single settings file, split dev/prod                            |
| `config/urls.py`          | URL routing: allauth, Ninja, health probes, plain Django webhook views | urlpatterns with comment-delimited removal blocks               |
| `apps/web/src/`           | Next.js App Router pages, Shadcn/ui components, React Query hooks      | Components in src/components/, pages in app/                    |
| `apps/mobile/`            | Expo SDK 53 managed workflow, Expo Router navigation                   | app/, components/, lib/                                         |
| `packages/api-client/`    | Auto-generated TypeScript types + fetch client                         | Generated from Django Ninja OpenAPI spec                        |

---

## v1.3 Features: Integration Mapping

Five features are being added. This section maps each to the existing architecture — which components change, which are new, and what the data flow looks like.

---

### Feature 1: Transactional Email — EmailAdapter ABC

**Pattern:** Mirrors existing `PaymentAdapter` and `ObservabilityAdapter` ABCs exactly.

**New components:**

```
apps/api/apps/notifications/       ← NEW Django app
├── __init__.py
├── apps.py                        # NotificationsConfig
├── adapters.py                    # EmailAdapter ABC + SendGridAdapter + ConsoleAdapter
├── tasks.py                       # Celery tasks: send_transactional_email.delay()
├── templates/email/               # Jinja2 HTML + plain-text templates
│   ├── base.html
│   ├── welcome.html
│   └── password_reset.html
└── migrations/                    # (empty — no models needed if no DB logging)
```

**Modified components:**

| File                       | Change                                                                                                                                                                       |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `config/settings/base.py`  | Add `EMAIL_ADAPTER = "apps.notifications.adapters.SendGridAdapter"` + `SENDGRID_API_KEY` env var. Add `# EMAIL_START` / `# EMAIL_END` comment blocks for scaffolder removal. |
| `INSTALLED_APPS`           | Add `"apps.notifications"`                                                                                                                                                   |
| `apps/accounts/signals.py` | Hook `post_save` signal to dispatch `send_transactional_email` Celery task after signup                                                                                      |
| `.env.example`             | Add `SENDGRID_API_KEY` in `# EMAIL MODULE` block                                                                                                                             |

**EmailAdapter ABC structure:**

```python
class EmailAdapter(abc.ABC):
    @abc.abstractmethod
    def send(self, to: str, subject: str, html_body: str, text_body: str) -> None: ...

class SendGridAdapter(EmailAdapter):
    # Uses sendgrid-python SDK; reads SENDGRID_API_KEY from settings
    ...

class ConsoleAdapter(EmailAdapter):
    # Writes to stdout — default in development and tests
    ...
```

**Data flow:**

```
User signs up
    → allauth post_save signal fires
    → send_transactional_email.delay(to=email, template="welcome") queued in Celery
    → Celery worker picks up task
    → get_email_adapter() resolves SendGridAdapter (or ConsoleAdapter in dev)
    → adapter.send(to, subject, rendered_html, rendered_text)
    → SendGrid HTTP API (or stdout)
```

**Scaffolder flag:** `--without email` — removes `apps/notifications/`, INSTALLED_APPS entry, env vars, and signal hookup.

**Confidence:** HIGH — pattern directly clones PaymentAdapter/ObservabilityAdapter structure already validated in codebase.

---

### Feature 2: Social Auth — Google + GitHub (web), Apple (mobile)

**Pattern:** Django Allauth already has `allauth.socialaccount` in INSTALLED_APPS (confirmed in `config/settings/base.py`). Social auth activates by adding provider subpackages and SOCIALACCOUNT_PROVIDERS config.

**New components:**

```
apps/api/apps/accounts/social.py   ← NEW (optional, for custom adapter overrides)
apps/mobile/lib/auth/apple.ts      ← NEW (expo-apple-authentication flow)
apps/web/src/components/auth/social-buttons.tsx  ← NEW
apps/web/src/lib/auth/social.ts    ← NEW (initiates allauth social flow)
```

**Modified components:**

| File                                         | Change                                                                                                                                         |
| -------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| `config/settings/base.py`                    | Add `allauth.socialaccount.providers.google` + `.github` to INSTALLED_APPS. Add `SOCIALACCOUNT_PROVIDERS` dict with client_id/secret from env. |
| `.env.example`                               | Add `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET` in `# SOCIAL_AUTH MODULE` block                     |
| `apps/web/src/components/auth/auth-form.tsx` | Add social login buttons below email/password form                                                                                             |
| `apps/mobile/app/(auth)/sign-in.tsx`         | Add Apple Sign In button (iOS-only, via `expo-apple-authentication`)                                                                           |

**Settings additions:**

```python
# config/settings/base.py — SOCIAL_AUTH_START
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APPS": [{"client_id": env("GOOGLE_CLIENT_ID", default=""), "secret": env("GOOGLE_CLIENT_SECRET", default="")}],
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
        "VERIFIED_EMAIL": True,
    },
    "github": {
        "APPS": [{"client_id": env("GITHUB_CLIENT_ID", default=""), "secret": env("GITHUB_CLIENT_SECRET", default="")}],
        "SCOPE": ["user:email"],
        "VERIFIED_EMAIL": False,  # GitHub may not verify email
    },
}
# SOCIAL_AUTH_END
```

**How allauth headless social auth works:** Allauth headless exposes `/_allauth/{client}/v1/auth/provider/redirect` and `/_allauth/{client}/v1/auth/provider/token` endpoints. The web client initiates the OAuth redirect through allauth, which manages the callback and creates a session. The existing `SessionAwareJWTTokenStrategy` in `apps/accounts/headless.py` applies to social logins without modification.

**Mobile Apple Sign In flow:**

```
iOS app
    → expo-apple-authentication.signInAsync()
    → Apple returns identityToken (JWT)
    → POST /_allauth/app/v1/auth/provider/token { provider: "apple", token: identityToken }
    → allauth verifies token, creates/finds User, issues session + JWT
```

This requires `allauth.socialaccount.providers.apple` in INSTALLED_APPS and Apple developer credentials (Team ID, Key ID, private key).

**Boundary: web vs. mobile social auth providers:**

- Web: Google + GitHub (OAuth2 redirect flow via allauth browser client)
- Mobile: Apple only (expo-apple-authentication native SDK; required by App Store for apps with other social logins)
- Google on mobile: deferred (expo-auth-session works, but PKCE + Android complexity; Apple is required first)

**Scaffolder flag:** `--without social-auth` — removes provider INSTALLED_APPS entries, SOCIALACCOUNT_PROVIDERS settings, env vars, social buttons from web/mobile auth forms.

**Confidence:** HIGH for web (allauth already configured, provider packages straightforward). MEDIUM for mobile Apple (requires Apple developer account credentials; flow verified via Expo docs but not tested against this codebase).

---

### Feature 3: GDPR Baseline

Three distinct components with minimal coupling.

**New backend components:**

```
apps/api/apps/accounts/gdpr.py    ← NEW (account delete + data export logic)
```

**New frontend components:**

```
apps/web/src/components/consent/cookie-banner.tsx   ← NEW (client component)
apps/web/src/lib/consent/store.ts                   ← NEW (Zustand store for consent state)
apps/web/app/(dashboard)/account/delete/page.tsx    ← NEW (delete confirmation flow)
```

**Modified components:**

| File                                    | Change                                                                                          |
| --------------------------------------- | ----------------------------------------------------------------------------------------------- |
| `apps/api/apps/accounts/controllers.py` | Add `DELETE /api/v1/accounts/me/` (hard delete) and `GET /api/v1/accounts/me/export/` endpoints |
| `apps/api/apps/accounts/services.py`    | Add `AccountDeletionService.delete_user(user)` — cascade via Django ORM, no raw SQL             |
| `apps/web/app/layout.tsx`               | Add `<CookieBanner />` client component                                                         |

**Account deletion cascade:**

Django's ORM handles cascade deletion via `on_delete=models.CASCADE` on all existing OneToOne / FK relations. The delete service calls `user.delete()` — the ORM collector removes Customer, Subscription, EmailAddress, and all other related records in the correct dependency order. No explicit cascade code is needed.

```python
# apps/accounts/services.py (addition)
class AccountDeletionService:
    def delete_user(self, user: User) -> None:
        """Hard delete user and all cascade-related data.

        Relies on Django ORM cascade (on_delete=CASCADE on all FK relations).
        Invalidates sessions before deletion to prevent stale auth state.
        """
        invalidate_user_sessions(user.id)
        user.delete()  # ORM collector handles cascade
```

**Data export endpoint:**

```python
# Returns JSON blob of all user-owned data
GET /api/v1/accounts/me/export/
→ { "user": {...}, "subscription": {...}, "payments": [...] }
```

The service aggregates data from all owned models. No new models required. Export is synchronous at this baseline level — async Celery task with email delivery is a future enhancement if exports become large.

**Cookie consent banner:**

- Client component (`"use client"`) rendered in `app/layout.tsx`
- Consent state stored in `localStorage` via Zustand with persist middleware
- On accept: sets consent flag, PostHog capture unblocked
- On reject: PostHog stays disabled; session cookie still exists (functional, not tracking)
- No third-party consent library needed — custom implementation with ~50 lines

**No new models required.** Consent preference stored client-side only (localStorage). GDPR does not require server-side consent storage for the baseline implementation.

**Scaffolder flag:** GDPR features are not behind a `--without` flag. GDPR compliance is expected for any SaaS product and should be present by default. The cookie banner is a standard pattern; deleting it would require product-level awareness.

**Confidence:** HIGH for account deletion (standard Django ORM pattern). HIGH for data export (simple aggregation). MEDIUM for cookie banner (implementation is custom; PostHog integration behavior verified via PostHog docs).

---

### Feature 4: RBAC — Django Groups + @require_role Decorator

**Pattern:** Mirrors existing `@require_active_subscription` decorator in `apps/billing/decorators.py` exactly.

**New components:**

```
apps/api/apps/accounts/rbac.py    ← NEW
├── require_role("admin") decorator
├── IsInGroup permission class (for Ninja Extra)
└── role_assignment utilities
```

**Modified components:**

| File                                    | Change                                                                                                                    |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `apps/api/apps/accounts/controllers.py` | Add `POST /api/v1/accounts/{user_id}/roles/` and `DELETE /api/v1/accounts/{user_id}/roles/{role}/` (admin-only endpoints) |
| `apps/api/apps/accounts/schemas.py`     | Add `RoleAssignmentIn`, `RoleOut` schemas                                                                                 |

**RBAC implementation strategy:**

Django Groups (built-in `django.contrib.auth.models.Group`) are the role carrier. No custom role model needed at this baseline level.

```python
# apps/accounts/rbac.py
import functools
from django.core.exceptions import PermissionDenied


def require_role(*roles: str):
    """Decorator that gates a view behind group membership.

    Usage: @require_role("admin") or @require_role("admin", "editor")
    Raises PermissionDenied (HTTP 403) if user lacks all specified roles.
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied("Authentication required.")
            user_groups = set(request.user.groups.values_list("name", flat=True))
            if not user_groups.intersection(set(roles)):
                raise PermissionDenied(f"Role required: {', '.join(roles)}")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


class IsInGroup:
    """Django Ninja Extra permission class for group-based access control.

    Usage: @api_controller(permissions=[IsInGroup("admin")])
    """
    def __init__(self, group_name: str) -> None:
        self.group_name = group_name

    def __call__(self, request) -> bool:
        if not request.user.is_authenticated:
            return False
        return request.user.groups.filter(name=self.group_name).exists()
```

**Role assignment API** (admin-only, guarded by `IsAdminUser` Ninja permission):

```
POST  /api/v1/accounts/{user_id}/roles/        # Assign role (group) to user
DELETE /api/v1/accounts/{user_id}/roles/{role}/ # Remove role from user
GET   /api/v1/accounts/{user_id}/roles/         # List user roles
```

**Group seeding:** Groups are created via a data migration (`0002_seed_default_groups.py` in `apps/accounts/migrations/`) that creates `admin`, `moderator`, and `viewer` groups at deploy time. Products add their own groups in product-specific migrations.

**No new models.** Django's built-in `Group` and `User.groups` ManyToMany are sufficient. No custom Role model is needed at this level.

**Scaffolder flag:** RBAC is not behind a `--without` flag. Groups are built into Django; the decorator adds minimal overhead and is universally useful.

**Confidence:** HIGH — Django Groups are battle-tested. Django Ninja Extra permission class pattern is verified via official docs. Decorator mirrors existing `@require_active_subscription` which is already in the codebase.

---

### Feature 5: Feature Entitlements — has_feature() + BILLING_PLANS Config

**Pattern:** Stateless utility function that reads the existing `BILLING_PLANS` dict in `config/settings/base.py` against the user's active subscription.

**New components:**

```
apps/api/apps/billing/entitlements.py   ← NEW (has_feature utility)
```

**No new models.** Feature flags are configuration, not database state. The `BILLING_PLANS` dict already exists in `config/settings/base.py` with a `"features"` list per plan. Entitlements reads this dict.

**Implementation:**

```python
# apps/billing/entitlements.py
from django.conf import settings


def has_feature(user, feature_key: str) -> bool:
    """Check if user's active subscription plan includes a feature.

    Reads BILLING_PLANS from settings. Returns False if:
    - User has no active subscription
    - User is on free plan
    - Feature key not in plan's feature list

    Usage: if has_feature(request.user, "api_access"): ...
    """
    try:
        subscription = user.billing_customer.subscription
    except Exception:
        return _free_plan_has_feature(feature_key)

    if subscription.status not in {"active", "trialing"}:
        return _free_plan_has_feature(feature_key)

    # Resolve plan from subscription's price_id via PlanProviderMapping
    from apps.billing.models import PlanProviderMapping
    mapping = PlanProviderMapping.objects.filter(
        price_id=subscription.stripe_subscription_id,  # mapped via provider
        is_active=True,
    ).first()

    if not mapping:
        return _free_plan_has_feature(feature_key)

    plan_config = settings.BILLING_PLANS.get(mapping.plan_id, {})
    return feature_key in plan_config.get("features", [])


def _free_plan_has_feature(feature_key: str) -> bool:
    free_plan = settings.BILLING_PLANS.get("free", {})
    return feature_key in free_plan.get("features", [])
```

**Note on plan resolution:** The existing `PlanProviderMapping` model (already in `apps/billing/models.py`) maps internal plan IDs to provider price IDs. The entitlements utility uses this table to resolve the user's current plan from their subscription's price ID. This avoids hardcoding Stripe price IDs in the entitlements code — consistent with the existing billing module's provider-agnostic design.

**BILLING_PLANS config** (already exists in `config/settings/base.py`, add feature keys):

```python
BILLING_PLANS = {
    "free":       {"name": "Free",       "features": ["basic_dashboard"]},
    "pro":        {"name": "Pro",        "features": ["basic_dashboard", "api_access", "priority_support"]},
    "enterprise": {"name": "Enterprise", "features": ["basic_dashboard", "api_access", "priority_support", "custom_contracts", "sla"]},
}
```

**No scaffolder flag.** Feature entitlements depend on the billing module. The `--without billing` flag in the scaffolder already removes billing; entitlements goes with it. No separate flag needed.

**Confidence:** HIGH for the utility function. MEDIUM for plan resolution via PlanProviderMapping — the mapping model is present but the price_id lookup path requires verification against actual subscription data shape during implementation.

---

## Recommended Project Structure (v1.3 additions)

```
apps/api/apps/
├── accounts/
│   ├── [existing files unchanged]
│   ├── gdpr.py          ← NEW: delete_user, export_user_data
│   └── rbac.py          ← NEW: require_role, IsInGroup
├── billing/
│   ├── [existing files unchanged]
│   └── entitlements.py  ← NEW: has_feature()
├── notifications/       ← NEW DJANGO APP
│   ├── __init__.py
│   ├── apps.py
│   ├── adapters.py      # EmailAdapter ABC, SendGridAdapter, ConsoleAdapter
│   ├── tasks.py         # send_transactional_email Celery task
│   └── templates/email/ # Jinja2 templates
└── core/
    └── [existing files unchanged]

apps/web/src/
├── components/
│   ├── auth/
│   │   ├── [existing files]
│   │   └── social-buttons.tsx     ← NEW
│   └── consent/
│       └── cookie-banner.tsx      ← NEW
├── lib/
│   ├── auth/
│   │   ├── [existing]
│   │   └── social.ts              ← NEW
│   └── consent/
│       └── store.ts               ← NEW (Zustand)
└── app/(dashboard)/account/
    └── delete/
        └── page.tsx               ← NEW

apps/mobile/lib/auth/
├── [existing files]
└── apple.ts                       ← NEW (expo-apple-authentication)
```

---

## Architectural Patterns

### Pattern 1: Adapter ABC (existing, repeated for email)

**What:** Abstract base class defines interface; concrete classes implement per-provider; settings contain the dotted-path class name; a `get_X_adapter()` factory resolves and instantiates on demand.

**When to use:** Any external service integration where the provider may change or need stubbing in tests.

**Trade-offs:** One extra indirection; trivially worth it for testability and provider independence.

```python
# Resolution factory (same pattern as get_payment_adapter, get_observability_adapter)
def get_email_adapter() -> EmailAdapter:
    adapter_class = import_string(settings.EMAIL_ADAPTER)
    return adapter_class()
```

### Pattern 2: Comment-Delimited Scaffolder Blocks (existing, extended for email + social)

**What:** Feature-specific code blocks in `config/settings/base.py`, `config/urls.py`, and `.env.example` are wrapped in `# FEATURE_START` / `# FEATURE_END` comment markers. The CLI scaffolder uses regex to strip these blocks when `--without feature` is requested.

**When to use:** Any optional module that needs to be removed by the scaffolder without breaking other modules.

**Trade-offs:** Requires discipline in code placement; implementation is straightforward and already proven in billing module.

### Pattern 3: Service-Layer Isolation (existing standard)

**What:** Controllers are thin (auth check, schema validation, response serialization). Services own business logic. Models own data persistence. No cross-layer leakage.

**When to use:** Always. Every new endpoint follows this pattern.

**Trade-offs:** More files, cleaner separation.

### Pattern 4: Signal-Driven Side Effects (existing, extended for email)

**What:** Django signals (`post_save`, `post_delete`) trigger side effects like auto-creating related records or dispatching Celery tasks. Signal handlers are registered in `AppConfig.ready()`.

**When to use:** When a side effect should always happen in response to a model event, regardless of which code path triggered the event.

**Trade-offs:** Implicit coupling; document signal connections clearly in `signals.py`.

---

## Data Flow

### New Data Flows in v1.3

**1. Social Login (web: Google):**

```
User clicks "Sign in with Google" (apps/web/src/components/auth/social-buttons.tsx)
    ↓
Browser redirects to /_allauth/browser/v1/auth/provider/redirect?provider=google
    ↓
Allauth initiates OAuth2 redirect to Google
    ↓
Google → callback → /_allauth/browser/v1/auth/provider/callback
    ↓
Allauth: find/create User, create SocialAccount record, create session
    ↓
Email notification: send_transactional_email.delay(template="welcome") (if new user)
    ↓
Browser: redirected to /dashboard with session cookie set
```

**2. Transactional Email (Celery):**

```
Trigger event (signup, password reset, etc.)
    ↓
Celery task: send_transactional_email(to, template, context)
    ↓
Load Jinja2 template → render HTML + plaintext
    ↓
get_email_adapter() → SendGridAdapter (production) or ConsoleAdapter (dev)
    ↓
adapter.send(to, subject, html, text) → SendGrid API or stdout
```

**3. Account Deletion (GDPR):**

```
User: DELETE /api/v1/accounts/me/ (authenticated)
    ↓
Controller: verify identity (re-auth or password confirmation)
    ↓
AccountDeletionService.delete_user(user)
    ↓
invalidate_user_sessions(user.id) — clears Redis session store
    ↓
user.delete() — Django ORM cascade removes: EmailAddress, Customer, Subscription,
                  Payment, ProcessedWebhookEvent, SocialAccount (if any)
    ↓
Return 204 No Content (session already invalid)
```

**4. Feature Entitlement Check:**

```
Request arrives at protected endpoint
    ↓
@require_role("admin") OR endpoint logic calls has_feature(user, "api_access")
    ↓
has_feature():
    → user.billing_customer.subscription (DB read, cached if Redis is warm)
    → PlanProviderMapping.objects.get(price_id=...) (DB read)
    → settings.BILLING_PLANS[plan_id]["features"] (in-memory dict lookup)
    ↓
Returns True/False → endpoint proceeds or raises PermissionDenied
```

---

## Build Order

Dependencies drive the sequence. Each feature group can be built semi-independently, but the ordering below minimizes rework.

```
Phase A: Transactional Email (no deps on other v1.3 features)
  A1. Create apps/notifications/ app (adapters.py, tasks.py, apps.py)
  A2. Add ConsoleAdapter (dev/test default), SendGridAdapter (production)
  A3. Add EMAIL_ADAPTER setting + SENDGRID_API_KEY to base.py + .env.example
  A4. Add "apps.notifications" to INSTALLED_APPS
  A5. Hook signup signal → send_transactional_email.delay()
  A6. CLI scaffolder: --without email flag
  WHY FIRST: No dependencies on other v1.3 features. Provides foundation
             for welcome emails that social auth (Phase B) will trigger.

Phase B: Social Auth (depends on allauth already configured + email for welcome)
  B1. Add allauth.socialaccount.providers.google + .github to INSTALLED_APPS
  B2. Add SOCIALACCOUNT_PROVIDERS to settings (env-backed client_id/secret)
  B3. Add social auth env vars to .env.example
  B4. Add social login buttons to apps/web auth form (social-buttons.tsx)
  B5. Add Apple Sign In to apps/mobile sign-in screen (expo-apple-authentication)
  B6. Add allauth.socialaccount.providers.apple + Apple credentials to settings
  B7. CLI scaffolder: --without social-auth flag
  WHY SECOND: Allauth is already present. Social providers are additive.
              Must come before RBAC and GDPR so social users are also
              subject to same deletion/role policies.

Phase C: RBAC (depends on User model + groups existing — no new v1.3 deps)
  C1. Create apps/accounts/rbac.py (require_role decorator + IsInGroup class)
  C2. Add data migration 0002_seed_default_groups.py
  C3. Add role assignment endpoints to accounts/controllers.py
  C4. Add RoleAssignmentIn/RoleOut schemas to accounts/schemas.py
  WHY THIRD: RBAC can be built independently of email and social auth.
             Placed here because GDPR (Phase D) benefits from admin role
             check on the data export endpoint.

Phase D: GDPR Baseline (depends on RBAC for admin guard on export)
  D1. Create apps/accounts/gdpr.py (AccountDeletionService, data_export)
  D2. Add DELETE /api/v1/accounts/me/ endpoint (authenticated users)
  D3. Add GET /api/v1/accounts/me/export/ endpoint (admin or self)
  D4. Create apps/web/src/components/consent/cookie-banner.tsx
  D5. Create apps/web/src/lib/consent/store.ts (Zustand)
  D6. Wire <CookieBanner /> into apps/web/app/layout.tsx
  D7. Add account deletion confirmation page to web app
  WHY FOURTH: Deletion service benefits from session invalidation utilities
              already in accounts/services.py. RBAC IsAdminUser is available.

Phase E: Feature Entitlements (depends on billing module — last because it's
         a read-only layer on top of existing billing state)
  E1. Create apps/billing/entitlements.py (has_feature utility)
  E2. Update BILLING_PLANS in settings with explicit feature key lists
  E3. Add has_feature() call to any protected endpoints (example usage)
  E4. No migration needed — reads existing PlanProviderMapping table
  WHY LAST: Pure read-only logic on top of existing billing data.
            No schema changes. Safe to add after all other features.
```

---

## Integration Points Summary

| Existing Component                           | Feature       | Change Type                                          | Notes                              |
| -------------------------------------------- | ------------- | ---------------------------------------------------- | ---------------------------------- |
| `config/settings/base.py`                    | Email         | ADD: EMAIL_ADAPTER setting, SENDGRID_API_KEY env     | Wrapped in # EMAIL_START/END       |
| `config/settings/base.py`                    | Social Auth   | ADD: SOCIALACCOUNT_PROVIDERS dict, provider env vars | Wrapped in # SOCIAL_AUTH_START/END |
| `config/settings/base.py`                    | BILLING_PLANS | MODIFY: add feature key lists to each plan           | Enhances existing dict             |
| `INSTALLED_APPS`                             | Email         | ADD: "apps.notifications"                            | Wrapped for scaffolder removal     |
| `INSTALLED_APPS`                             | Social Auth   | ADD: 3 provider packages                             | Wrapped for scaffolder removal     |
| `apps/accounts/signals.py`                   | Email         | ADD: post_save → send_transactional_email.delay()    | Existing signals.py                |
| `apps/accounts/controllers.py`               | GDPR + RBAC   | ADD: delete, export, role assignment endpoints       | Additive to existing controller    |
| `apps/accounts/services.py`                  | GDPR          | ADD: AccountDeletionService class                    | Additive                           |
| `apps/billing/models.py`                     | Entitlements  | NO CHANGE                                            | Read-only via PlanProviderMapping  |
| `apps/billing/utils.py`                      | Entitlements  | NONE — new file                                      | entitlements.py is a new file      |
| `apps/web/app/layout.tsx`                    | GDPR          | ADD: <CookieBanner /> import + render                | Single line addition               |
| `apps/web/src/components/auth/auth-form.tsx` | Social Auth   | ADD: social-buttons.tsx below form                   | Additive component                 |
| `apps/mobile/app/(auth)/sign-in.tsx`         | Social Auth   | ADD: Apple Sign In button (iOS only)                 | Platform conditional               |
| `packages/api-client/`                       | All           | REGENERATE: after each backend endpoint addition     | Standard pipeline                  |

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Social Auth State Management in the URL

**What people do:** Pass OAuth tokens or social account state through URL query parameters in the redirect flow.

**Why it's wrong:** Tokens in URLs appear in server logs, browser history, and referrer headers. PKCE mitigates some risks but URL exposure is still a vulnerability.

**Do this instead:** Let allauth manage the OAuth state entirely. The callback is handled server-side by allauth's views. The web client only needs to initiate the redirect (`/_allauth/browser/v1/auth/provider/redirect`) and handle the resulting session.

### Anti-Pattern 2: Implementing RBAC with a Custom Role Model

**What people do:** Create a `Role` model with a ManyToMany to `User`, bypassing Django's built-in `Group` system.

**Why it's wrong:** Django Groups are battle-tested, integrated with the admin, and already present. A custom Role model duplicates this with none of the built-in benefits.

**Do this instead:** Use Django Groups as roles. The `require_role("admin")` decorator checks group membership. Group names are strings — no enum or constant model needed.

### Anti-Pattern 3: Synchronous Email Sending in Request Cycle

**What people do:** Call `adapter.send()` directly in a controller or signal handler, blocking the HTTP response until the email API responds.

**Why it's wrong:** Email APIs introduce 100-500ms latency per call. Errors in the email provider cause HTTP 500s. Request timeout kills in-flight emails.

**Do this instead:** Always dispatch `send_transactional_email.delay()` as a Celery task. The HTTP response returns immediately. Failed emails are retried by Celery. Email delivery is decoupled from request success.

### Anti-Pattern 4: Storing Feature Flags in the Database

**What people do:** Create a `Feature` model with a ManyToMany to subscription plans, managed via admin.

**Why it's wrong:** Feature configuration becomes fragmented across database state and code. Deployments require database migrations to change features. Testability requires database fixtures for feature data.

**Do this instead:** `BILLING_PLANS` in settings is the single source of truth. Feature keys are strings in a list. `has_feature()` is a pure function of user subscription + settings — no extra DB models, no extra migrations.

### Anti-Pattern 5: Soft-Delete for GDPR Account Deletion

**What people do:** Add `deleted_at` field to User model and filter it in queries (soft delete).

**Why it's wrong:** GDPR Article 17 (Right to Erasure) requires actual deletion of personal data, not just hiding it. Soft-deleted records still contain PII and are subject to regulatory compliance.

**Do this instead:** Hard delete via `user.delete()`. Django ORM cascade handles all related records. If audit logging is needed, log the deletion event (timestamp, hashed user ID) before the delete — not the user data itself.

---

## Scaling Considerations

| Scale         | Architecture Adjustments                                                                                                                                                                                     |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 0-1k users    | All five features work as described. Synchronous data export is fine.                                                                                                                                        |
| 1k-100k users | Data export should become async Celery task + email delivery (avoid timeout on large accounts). Feature entitlement results should be cached in Redis (1-minute TTL) to avoid repeated DB reads per request. |
| 100k+ users   | RBAC permission checks may need caching. Social auth token exchange should use PKCE. Email volume may require SendGrid dedicated IP. Consider read replica for data export queries.                          |

---

## Sources

- Django Allauth social account provider configuration: [docs.allauth.org/en/dev/socialaccount/provider_configuration.html](https://docs.allauth.org/en/dev/socialaccount/provider_configuration.html) — HIGH confidence (official docs)
- Django Allauth Google provider: [docs.allauth.org/en/dev/socialaccount/providers/google.html](https://docs.allauth.org/en/dev/socialaccount/providers/google.html) — HIGH confidence (official docs)
- Expo Apple Authentication: [docs.expo.dev/versions/latest/sdk/apple-authentication/](https://docs.expo.dev/versions/latest/sdk/apple-authentication/) — HIGH confidence (official Expo docs)
- Django Ninja Extra permission system: [eadwincode.github.io/django-ninja-extra/api_controller/api_controller_permission/](https://eadwincode.github.io/django-ninja-extra/api_controller/api_controller_permission/) — HIGH confidence (official library docs)
- Existing codebase inspection: `apps/billing/adapters.py`, `apps/billing/decorators.py`, `apps/core/observability.py`, `apps/accounts/services.py`, `apps/accounts/headless.py`, `config/settings/base.py`, `config/urls.py` — HIGH confidence (direct inspection)
- PaymentAdapter ABC pattern (already validated v1.1): existing `apps/billing/adapters.py` — HIGH confidence
- GDPR cascade deletion via Django ORM: Django model deletion documentation, confirmed by codebase FK relationship inspection — HIGH confidence
- Cookie consent in Next.js 15 App Router: [posthog.com/tutorials/nextjs-cookie-banner](https://posthog.com/tutorials/nextjs-cookie-banner) — MEDIUM confidence (PostHog-authored tutorial, current)

---

_v1.3 SaaS Functional Baseline — Foundation Template_
_Researched: 2026-03-11_
