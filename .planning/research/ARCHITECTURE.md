# Architecture Research: v1.4 B2B Module

**Domain:** B2B layer for existing full-stack SaaS monorepo — organizations, outbound webhooks, API keys, audit logging, admin backoffice
**Researched:** 2026-03-12
**Confidence:** HIGH — grounded in direct codebase inspection plus official documentation verification

---

## Standard Architecture

### System Overview (Post-v1.4 State)

```
┌──────────────────────────────────────────────────────────────────────┐
│  CLIENT LAYER                                                        │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐   │
│  │  apps/web/       │  │  apps/mobile/    │  │  /admin/         │   │
│  │  Next.js 15 AR   │  │  Expo SDK 53     │  │  django-unfold   │   │
│  │  org switcher    │  │  org context     │  │  + django-hijack │   │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘   │
└───────────┼─────────────────────┼────────────────────-┼─────────────┘
            │  session/JWT         │  JWT Bearer          │ session
┌───────────┼─────────────────────┼────────────────────-┼─────────────┐
│  API LAYER│                     │                      │             │
│  ┌────────┴─────────────────────┴──────────────────────┴────────┐   │
│  │  apps/api/  (Django Ninja Extra + Django Admin)               │   │
│  │                                                               │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────┐   │   │
│  │  │ accounts   │ │ billing    │ │organizations│ │ apikeys  │   │   │
│  │  │ (auth/RBAC)│ │ (payments) │ │ (B2B core) │ │ (prog.   │   │   │
│  │  │            │ │            │ │            │ │  access) │   │   │
│  │  └────────────┘ └────────────┘ └────────────┘ └──────────┘   │   │
│  │                                                               │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────┐   │   │
│  │  │  webhooks  │ │   core     │ │   audit    │ │    ai    │   │   │
│  │  │ (outbound) │ │ (infra)    │ │ (cross-cut)│ │(optional)│   │   │
│  │  └────────────┘ └────────────┘ └────────────┘ └──────────┘   │   │
│  │                                                               │   │
│  │  allauth headless + Celery + structlog + OTel + Redis         │   │
│  └───────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
            │
┌───────────┴──────────────────────────────────────────────────────────┐
│  DATA LAYER                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐   │
│  │  PostgreSQL  │  │    Redis     │  │  External Services        │   │
│  │  + PGVector  │  │  Celery/Cache│  │  Stripe, PostHog, Resend  │   │
│  │  + pghistory │  │  Session     │  │  Customer endpoints       │   │
│  │    triggers  │  │              │  │  (outbound webhooks)      │   │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

### Existing Component Responsibilities (Unchanged)

| Component                      | Responsibility                                             |
| ------------------------------ | ---------------------------------------------------------- |
| `apps/api/apps/accounts/`      | Auth, user model, session + JWT via allauth headless, RBAC |
| `apps/api/apps/billing/`       | Subscriptions, payments via PaymentAdapter ABC             |
| `apps/api/apps/core/`          | Infra: middleware, observability, health, rate limiting    |
| `apps/api/apps/notifications/` | Transactional email via EmailAdapter ABC                   |
| `apps/api/apps/ai/`            | Optional LangGraph agents, vector search                   |
| `config/settings/base.py`      | Central config: adapter class paths, feature flags         |
| `config/urls.py`               | URL routing: allauth, Ninja, health probes, webhooks       |

### New Components (v1.4)

| Component                      | Responsibility                                            |
| ------------------------------ | --------------------------------------------------------- |
| `apps/api/apps/organizations/` | Organization model, membership, roles, per-org billing    |
| `apps/api/apps/webhooks/`      | Outbound webhook registry, Celery delivery, delivery log  |
| `apps/api/apps/apikeys/`       | APIKey model, Ninja auth backend, scopes, rate limiting   |
| `apps/api/apps/audit/`         | AuditLog cross-cutting concern via pghistory middleware   |
| `config/urls.py` (modified)    | Add `path("admin/", ...)` pointing to unfold-themed admin |

---

## v1.4 Features: Integration Mapping

Five features are being added. Each is mapped to existing architecture — which components change, which are new, and the integration points.

---

### Feature 1: Organization Model — `apps/api/apps/organizations/`

**Pattern:** New Django app. Organization is an independent entity that owns memberships and billing. The existing `Customer` model (currently `OneToOneField` to `User`) gains a sibling: `OrgCustomer` is `OneToOneField` to `Organization`. User-level billing is unchanged.

**New components:**

```
apps/api/apps/organizations/
├── __init__.py
├── apps.py                        # OrganizationsConfig
├── models.py                      # Organization, Membership, OrgRole
├── schemas.py                     # OrgOut, OrgCreateIn, MembershipOut, InviteIn
├── controllers.py                 # OrgController (CRUD + member management)
├── services.py                    # OrgService (create, invite, remove, transfer)
├── selectors.py                   # get_user_orgs(), get_org_members() queries
├── permissions.py                 # IsOrgAdmin, IsOrgMember permission classes
├── admin.py                       # django-unfold registration
├── signals.py                     # post_save → seed owner membership
└── migrations/
    ├── 0001_initial.py
    └── 0002_seed_org_roles.py     # seeds "owner", "admin", "member" OrgRoles
```

**Core models:**

```python
# organizations/models.py

class OrgRole(models.TextChoices):
    OWNER = "owner"       # full control, cannot be removed
    ADMIN = "admin"       # manage members, billing
    MEMBER = "member"     # read/operate

class Organization(BaseModel):              # inherits created_at, updated_at, deleted_at
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    owner = models.ForeignKey(User, on_delete=models.PROTECT, related_name="owned_orgs")
    # Billing FKs — see Feature 1a below

class Membership(BaseModel):
    org = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=20, choices=OrgRole.choices, default=OrgRole.MEMBER)

    class Meta:
        unique_together = [("org", "user")]
```

**Feature 1a — Per-org billing:**

The existing `Customer` model is `OneToOneField(User)`. Org billing requires a parallel `OrgCustomer` model.

```python
# billing/models.py (MODIFICATION — additive)

class OrgCustomer(models.Model):
    org = models.OneToOneField(Organization, on_delete=models.CASCADE, related_name="billing_customer")
    stripe_customer_id = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

This parallels `Customer` exactly. `BillingService` gains an `OrgBillingService` (or an `entity` discriminator). `has_feature()` in `billing/entitlements.py` gains an `org=` kwarg to check org plan features instead of user features.

**Modified components:**

| File                           | Change                                                                                                                                     |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `apps/billing/models.py`       | ADD: `OrgCustomer(OneToOneField → Organization)`, `OrgSubscription`, `OrgPlanProviderMapping` (or reuse `PlanProviderMapping` with org FK) |
| `apps/billing/services.py`     | ADD: `OrgBillingService` mirroring `BillingService` but keyed to `OrgCustomer`                                                             |
| `apps/billing/entitlements.py` | ADD: `has_org_feature(org, key)` utility — same pattern as `has_feature(user, key)`                                                        |
| `config/settings/base.py`      | ADD: `# B2B_START` / `# B2B_END` blocks for scaffolder removal                                                                             |
| `config/urls.py`               | Automatically picked up via `api.auto_discover_controllers()`                                                                              |
| `INSTALLED_APPS`               | ADD: `"apps.organizations"` inside `# B2B_START` / `# B2B_END`                                                                             |
| `packages/shared-types/`       | REGENERATE: after org endpoints added                                                                                                      |

**Permission model:**

`IsOrgAdmin` and `IsOrgMember` are Ninja Extra `BasePermission` subclasses — same pattern as the existing `RequireRole` in `accounts/permissions.py`. They read org membership from DB and return True/False.

**Scaffolder flag:** `--with b2b` (additive; B2B is off by default, unlike billing which defaults on).

**Confidence:** HIGH — mirrors existing billing domain module structure. `BaseModel` (with soft delete) already in `apps/core/models.py`. `RequireRole` permission pattern already validated.

---

### Feature 2: Outbound Webhooks — `apps/api/apps/webhooks/`

**Pattern:** New Django app. Completely separate from the existing inbound Stripe webhook handler in `apps/billing/webhooks.py`. Outbound webhooks are customer-registered HTTP endpoints that receive event notifications from this app.

**New components:**

```
apps/api/apps/webhooks/
├── __init__.py
├── apps.py                        # WebhooksConfig
├── models.py                      # WebhookEndpoint, WebhookDelivery
├── schemas.py                     # EndpointCreateIn, EndpointOut, DeliveryOut
├── controllers.py                 # EndpointController (CRUD), DeliveryController (list)
├── services.py                    # WebhookService — register_endpoint(), dispatch_event()
├── tasks.py                       # deliver_webhook Celery task (retry + backoff)
├── signing.py                     # HMAC-SHA256 signing utility
├── admin.py
└── migrations/
    └── 0001_initial.py
```

**Core models:**

```python
# webhooks/models.py

class WebhookEndpoint(BaseModel):
    org = models.ForeignKey(Organization, on_delete=models.CASCADE,
                            related_name="webhook_endpoints", null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name="webhook_endpoints", null=True, blank=True)
    # org OR user — products decide whether webhooks are per-org or per-user
    url = models.URLField(max_length=500)
    secret = models.CharField(max_length=64)      # HMAC signing key, generated on creation
    events = models.JSONField(default=list)        # ["payment.succeeded", "user.created"]
    is_active = models.BooleanField(default=True)

class WebhookDelivery(models.Model):
    endpoint = models.ForeignKey(WebhookEndpoint, on_delete=models.CASCADE,
                                 related_name="deliveries")
    event_type = models.CharField(max_length=100)
    payload = models.JSONField()
    attempt = models.PositiveSmallIntegerField(default=1)
    status_code = models.PositiveSmallIntegerField(null=True)
    response_body = models.TextField(blank=True)
    delivered_at = models.DateTimeField(null=True)
    failed_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

**Delivery flow:**

```
Application event fires (e.g. payment succeeded, org member added)
    ↓
WebhookService.dispatch_event(event_type="payment.succeeded", payload={...})
    → queries active WebhookEndpoint records subscribed to this event_type
    → for each matching endpoint:
        deliver_webhook.delay(endpoint_id, event_type, payload)

Celery task: deliver_webhook(endpoint_id, event_type, payload)
    ↓
Load endpoint + compute HMAC-SHA256 signature over JSON payload
    ↓
POST to endpoint.url with headers:
    X-Webhook-Signature: sha256=<hmac>
    X-Webhook-Event: <event_type>
    X-Webhook-Delivery: <delivery_id>
    ↓
On success (2xx): record WebhookDelivery(status_code=200, delivered_at=now)
On failure: raise exception → Celery autoretry_for with exponential backoff
    countdown = min(2 ** attempt * 30, 3600)   # 30s, 60s, 120s … max 1h
    max_retries = 7                              # ~24h total window
On exhaustion: WebhookDelivery(failed_at=now) — dead letter, no more retries
```

**HMAC signing:**

```python
# webhooks/signing.py
import hashlib, hmac, json

def sign_payload(secret: str, payload: dict) -> str:
    """Return 'sha256=<hex>' signature for the payload."""
    body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"
```

**Separation from inbound Stripe webhooks:** The existing `apps/billing/webhooks.py` is a plain Django view that receives and verifies _inbound_ Stripe events. This new `apps/webhooks/` module dispatches _outbound_ events to customer endpoints. They share no code.

**Modified components:**

| File                     | Change                                                    |
| ------------------------ | --------------------------------------------------------- |
| `INSTALLED_APPS`         | ADD: `"apps.webhooks"` inside `# B2B_START` / `# B2B_END` |
| `config/urls.py`         | Automatic via `api.auto_discover_controllers()`           |
| `packages/shared-types/` | REGENERATE after endpoint management API added            |

**Scaffolder flag:** Included in `--with b2b` block.

**Confidence:** HIGH — pattern directly mirrors existing Stripe inbound webhook handler (Celery dispatch, HMAC, plain Django, no Ninja body parsing). Exponential backoff via Celery `autoretry_for` + `countdown` is a well-established pattern.

---

### Feature 3: API Key Authentication — `apps/api/apps/apikeys/`

**Pattern:** New Django app providing a custom Django Ninja `APIKeyHeader` auth backend. API keys are an alternative authentication path — they coexist with the existing session + JWT auth. Controllers opt in by listing `api_key_auth` alongside `SessionAuth()` in their `auth=[]` list.

**New components:**

```
apps/api/apps/apikeys/
├── __init__.py
├── apps.py                        # APIKeysConfig
├── models.py                      # APIKey model
├── schemas.py                     # APIKeyCreateIn, APIKeyOut (key only shown once)
├── controllers.py                 # APIKeyController (CRUD for key management)
├── services.py                    # APIKeyService (create, revoke, list, rotate)
├── auth.py                        # APIKeyHeader — custom Ninja auth backend
├── admin.py
└── migrations/
    └── 0001_initial.py
```

**Core model:**

```python
# apikeys/models.py

class APIKey(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="api_keys",
                             null=True, blank=True)
    org = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="api_keys",
                            null=True, blank=True)
    # user OR org — product decides whether keys are user-scoped or org-scoped
    name = models.CharField(max_length=100)         # human label for identification
    prefix = models.CharField(max_length=12, unique=True)  # first 12 chars — for display
    key_hash = models.CharField(max_length=64)      # SHA-256 hash — raw key never stored
    scopes = models.JSONField(default=list)         # ["read:billing", "write:webhooks"]
    last_used_at = models.DateTimeField(null=True)
    expires_at = models.DateTimeField(null=True)
    is_active = models.BooleanField(default=True)
```

**Key generation and storage:**

The raw key is shown to the user exactly once at creation and never stored. Only the SHA-256 hash is stored. The prefix (first 12 chars) is stored plaintext for display in key lists (`sk_live_abc123...`).

```python
# apikeys/services.py (key creation)
import hashlib, secrets

def create_key() -> tuple[str, str, str]:
    """Returns (raw_key, prefix, hash)."""
    raw = "sk_" + secrets.token_urlsafe(32)
    prefix = raw[:12]
    key_hash = hashlib.sha256(raw.encode()).hexdigest()
    return raw, prefix, key_hash
```

**Custom Ninja auth backend:**

```python
# apikeys/auth.py
from ninja.security import APIKeyHeader
from .models import APIKey

class APIKeyAuth(APIKeyHeader):
    param_name = "X-API-Key"

    def authenticate(self, request, key: str):
        import hashlib
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        try:
            api_key = APIKey.objects.select_related("user", "org").get(
                key_hash=key_hash,
                is_active=True,
                deleted_at__isnull=True,
            )
        except APIKey.DoesNotExist:
            return None

        # Check expiry
        if api_key.expires_at and api_key.expires_at < now():
            return None

        # Update last_used_at async (avoid blocking auth on DB write)
        APIKey.objects.filter(pk=api_key.pk).update(last_used_at=now())

        # Attach org context to request so controllers can scope queries
        request.api_key = api_key
        if api_key.org:
            request.org = api_key.org
        return api_key.user or api_key.org   # request.auth is User or Org
```

**Usage in controllers:**

```python
# Any controller that should accept API key auth:
from apps.apikeys.auth import APIKeyAuth

api_key_auth = APIKeyAuth()

@api_controller(
    "/data",
    auth=[SessionAuth(), jwt_token_auth, api_key_auth],   # all three accepted
    permissions=[IsAuthenticated],
)
class DataController(ControllerBase):
    ...
```

**Scopes enforcement:** Scopes are checked in a `RequireScope("write:webhooks")` permission class (same pattern as `RequireRole`). An endpoint requiring `write:webhooks` checks `request.api_key.scopes` contains that scope.

**Rate limiting:** Per-key rate limiting reuses `django-ratelimit` with `key="header:x-api-key"` — same infrastructure as the existing `AuthRateLimitMiddleware`.

**Modified components:**

| File                     | Change                                                   |
| ------------------------ | -------------------------------------------------------- |
| `INSTALLED_APPS`         | ADD: `"apps.apikeys"` inside `# B2B_START` / `# B2B_END` |
| Any controller opting in | ADD: `api_key_auth` to `auth=[]` list                    |
| `packages/shared-types/` | REGENERATE after key management endpoints added          |

**Scaffolder flag:** Included in `--with b2b` block.

**Confidence:** HIGH — `APIKeyHeader` pattern verified against official Django Ninja docs. SHA-256 hash-only storage is the industry standard (never store raw keys). Rate limiting via `django-ratelimit` is already in the codebase.

---

### Feature 4: Audit Logging — Cross-Cutting via pghistory

**Pattern:** `django-pghistory` (PostgreSQL triggers) + `pghistory.middleware.HistoryMiddleware` for automatic request context (user, URL). Applied selectively via `@pghistory.track()` decorators on models that need audit trails. Not applied to every model.

**Rationale for pghistory over django-simple-history:**

- pghistory uses DB-level PostgreSQL triggers: captures changes from raw SQL, bulk ORM operations, and Celery tasks — not just HTTP-layer ORM calls
- structlog already provides HTTP request logging; pghistory adds _who changed what data_ at the DB level
- Minimal app-layer overhead: triggers run in the same transaction, no post-save signals required
- `pghistory.context()` and `HistoryMiddleware` attach user + URL metadata automatically

**New components:**

```
apps/api/apps/audit/
├── __init__.py
├── apps.py                        # AuditConfig
└── admin.py                       # Register pghistory event models in django-unfold admin
```

No `models.py` in the audit app itself — pghistory auto-generates shadow table models via decorators on the tracked models.

**Middleware registration:**

```python
# config/settings/base.py
MIDDLEWARE = [
    ...
    "apps.core.middleware.RequestContextMiddleware",
    "apps.core.middleware.ObservabilityMiddleware",
    "apps.core.middleware.AuthRateLimitMiddleware",
    "pghistory.middleware.HistoryMiddleware",  # ADD — after auth middleware so user is set
]
```

**Model-level tracking:**

```python
# Applied to models that need audit trails — NOT all models.
# Targets: Organization, Membership, APIKey, WebhookEndpoint

import pghistory

@pghistory.track(pghistory.UpdateEvent(), pghistory.DeleteEvent())
class Membership(BaseModel):
    ...

@pghistory.track(pghistory.InsertEvent(), pghistory.UpdateEvent(), pghistory.DeleteEvent())
class APIKey(BaseModel):
    ...
```

**What pghistory.HistoryMiddleware captures automatically:**

- `user` — the authenticated Django user ID from `request.user`
- `url` — the request URL path

**Custom context extension** (if IP or org context is needed):

```python
# apps/core/middleware.py — extend existing RequestContextMiddleware
# OR create a subclass of pghistory.middleware.HistoryMiddleware

class AuditContextMiddleware(pghistory.middleware.HistoryMiddleware):
    def get_context(self, request):
        ctx = super().get_context(request)
        # Add org context if present (set by org-scoped endpoints)
        if hasattr(request, "org"):
            ctx["org_id"] = str(request.org.pk)
        return ctx
```

**Modified components:**

| File                           | Change                                                                                     |
| ------------------------------ | ------------------------------------------------------------------------------------------ |
| `config/settings/base.py`      | ADD: `"pghistory"` to INSTALLED_APPS; ADD: `HistoryMiddleware` (or subclass) to MIDDLEWARE |
| `config/settings/base.py`      | ADD: `PGHISTORY_CONTEXT_FIELD = "metadata"` if custom context fields needed                |
| `apps/organizations/models.py` | ADD: `@pghistory.track(...)` decorators on `Organization`, `Membership`                    |
| `apps/apikeys/models.py`       | ADD: `@pghistory.track(...)` on `APIKey`                                                   |
| `apps/webhooks/models.py`      | ADD: `@pghistory.track(...)` on `WebhookEndpoint`                                          |
| `INSTALLED_APPS`               | ADD: `"pghistory"`, `"pgtrigger"` (pghistory dependency) inside B2B block                  |

**Important:** pghistory `@pghistory.track()` decorators generate new migration files for the tracked model's app (not in an `audit/` app). The shadow table lives in the same database, named `<app>_<model>event`.

**Scaffolder flag:** Included in `--with b2b` block. Removing `--with b2b` removes the decorators, middleware, and `pghistory`/`pgtrigger` from INSTALLED_APPS.

**Confidence:** MEDIUM-HIGH — pghistory is well-documented, PostgreSQL-native, and actively maintained (v3.6.0, April 2025). The middleware approach is official pghistory pattern. The Django Ninja + allauth headless context: `request.user` is set by allauth middleware before `pghistory.middleware.HistoryMiddleware` runs, so user tracking works correctly with the existing middleware order.

---

### Feature 5: Admin Backoffice — django-unfold + django-hijack

**Pattern:** Drop-in replacement for Django's default admin theme (django-unfold) plus user impersonation for customer support (django-hijack). These layer on top of Django's built-in admin — no code migration required for existing `ModelAdmin` registrations in `accounts/admin.py`, `billing/admin.py`.

**New components:**

```
# No new Django apps. Modifications to existing admin registrations.

apps/api/apps/organizations/admin.py    ← NEW (register Org/Membership models)
apps/api/apps/apikeys/admin.py          ← NEW (register APIKey model)
apps/api/apps/webhooks/admin.py         ← NEW (register WebhookEndpoint/Delivery)
apps/api/apps/audit/admin.py            ← NEW (register pghistory event models)
```

**django-unfold installation:**

```python
# config/settings/base.py
INSTALLED_APPS = [
    "unfold",                              # ADD BEFORE django.contrib.admin
    "unfold.contrib.filters",              # optional: enhanced filter UI
    "unfold.contrib.forms",                # optional: enhanced form widgets
    "unfold.contrib.inlines",              # optional: tab-based inlines
    "django.contrib.admin",                # unchanged
    ...
]
```

Unfold extends, not replaces, Django admin. Each `ModelAdmin` that needs Unfold styling must inherit from `unfold.admin.ModelAdmin` instead of `django.contrib.admin.ModelAdmin`. Existing registrations in `accounts/admin.py` and `billing/admin.py` are updated.

**django-hijack installation:**

```python
# config/settings/base.py
INSTALLED_APPS = [
    ...
    "hijack",                  # ADD
    "hijack.contrib.admin",    # ADD — adds impersonate button to user list
]

HIJACK_ALLOWED_USER_EMAILS = []  # empty = all staff can hijack; restrict per-project
HIJACK_PERMISSION_CHECK = "hijack.permissions.superusers_only"  # default
```

```python
# config/urls.py
urlpatterns = [
    path("admin/", admin.site.urls),
    path("hijack/", include("hijack.urls")),  # ADD — provides hijack:acquire endpoint
    ...
]
```

**Unfold + Hijack compatibility:** django-hijack v3 has built-in Django admin support via `hijack.contrib.admin`. The hijack button renders in the admin user list automatically. Unfold's custom `ModelAdmin` base class extends Django's standard admin; the hijack contrib renders standard Django admin HTML which Unfold will style. No special integration code is required — both packages cooperate through standard Django admin extension points.

**Admin navigation (Unfold sidebar):**

```python
# config/settings/base.py — Unfold NAVIGATION config
UNFOLD = {
    "SITE_TITLE": "Foundation Admin",
    "SIDEBAR": {
        "navigation": [
            {"title": "Users", "items": [
                {"title": "Users", "url": "/admin/accounts/user/"},
                {"title": "Memberships", "url": "/admin/organizations/membership/"},
            ]},
            {"title": "Organizations", "items": [
                {"title": "Orgs", "url": "/admin/organizations/organization/"},
                {"title": "API Keys", "url": "/admin/apikeys/apikey/"},
                {"title": "Webhooks", "url": "/admin/webhooks/webhookendpoint/"},
            ]},
            {"title": "Billing", "items": [
                {"title": "Customers", "url": "/admin/billing/customer/"},
                {"title": "Subscriptions", "url": "/admin/billing/subscription/"},
            ]},
            {"title": "Audit", "items": [
                {"title": "Audit Events", "url": "/admin/audit/"},
            ]},
        ]
    },
}
```

**Modified components:**

| File                      | Change                                                                                     |
| ------------------------- | ------------------------------------------------------------------------------------------ |
| `INSTALLED_APPS`          | ADD: `"unfold"`, `"hijack"`, `"hijack.contrib.admin"` — inside `# B2B_START` / `# B2B_END` |
| `config/settings/base.py` | ADD: `UNFOLD = {...}` config dict, `HIJACK_PERMISSION_CHECK`                               |
| `config/urls.py`          | ADD: `path("hijack/", include("hijack.urls"))` inside `# B2B_START` / `# B2B_END`          |
| `apps/accounts/admin.py`  | MODIFY: change `admin.ModelAdmin` → `unfold.admin.ModelAdmin` on existing registrations    |
| `apps/billing/admin.py`   | MODIFY: same inheritance change                                                            |

**Scaffolder flag:** Included in `--with b2b` block. Removing B2B reverts `admin.ModelAdmin` base classes to standard Django and removes hijack URL + INSTALLED_APPS entries.

**Confidence:** MEDIUM — Unfold + Hijack compatibility via standard Django admin extension points is expected but not directly confirmed by a single official integration guide. Both packages target standard Django admin; their interaction is additive. Hijack v3 CSRF-based POST to `hijack:acquire` is not affected by Unfold's theme layer. Flagged for early validation during implementation.

---

## Recommended Project Structure (v1.4 additions)

```
apps/api/apps/
├── accounts/            # unchanged — user, auth, RBAC
├── billing/
│   ├── [existing files unchanged]
│   ├── models.py        # MODIFIED: add OrgCustomer, OrgSubscription
│   └── services.py      # MODIFIED: add OrgBillingService
├── core/                # unchanged — infra, middleware, health
├── notifications/       # unchanged — email adapter
├── ai/                  # unchanged — optional agents
├── organizations/       # NEW Django app
│   ├── models.py        # Organization, Membership, OrgRole
│   ├── schemas.py
│   ├── controllers.py
│   ├── services.py
│   ├── selectors.py
│   ├── permissions.py   # IsOrgAdmin, IsOrgMember
│   ├── admin.py
│   ├── signals.py
│   └── migrations/
├── webhooks/            # NEW Django app
│   ├── models.py        # WebhookEndpoint, WebhookDelivery
│   ├── schemas.py
│   ├── controllers.py
│   ├── services.py
│   ├── tasks.py         # deliver_webhook Celery task
│   ├── signing.py       # HMAC-SHA256 utility
│   ├── admin.py
│   └── migrations/
├── apikeys/             # NEW Django app
│   ├── models.py        # APIKey
│   ├── schemas.py
│   ├── controllers.py
│   ├── services.py
│   ├── auth.py          # APIKeyAuth (APIKeyHeader subclass)
│   ├── admin.py
│   └── migrations/
└── audit/               # NEW Django app (thin — no models.py)
    ├── apps.py
    └── admin.py         # register pghistory shadow tables
```

---

## Architectural Patterns

### Pattern 1: Per-Org Billing via Parallel Customer Model

**What:** A new `OrgCustomer` model mirrors the existing `Customer(OneToOneField → User)` pattern with `OrgCustomer(OneToOneField → Organization)`. The existing `BillingService` is not modified — a new `OrgBillingService` handles org billing. This avoids changing tested code and keeps billing contracts stable.

**When to use:** Any time a new entity (org, project, team) needs its own subscription.

**Trade-offs:** Two billing service classes with overlapping logic. A more DRY approach would generalize `BillingService` to accept `entity=user|org`. That optimization is premature here — the duplication is minimal and preserves testability with the existing billing test suite.

### Pattern 2: Opt-in API Key Auth

**What:** The `api_key_auth = APIKeyAuth()` authenticator is added to individual controllers' `auth=[]` list. Session + JWT auth always remains. No controller is forced to accept API keys.

**When to use:** Controllers that need to be callable by external scripts, integrations, or CI pipelines.

**Trade-offs:** Controllers must be explicitly opted in. This is intentional — not every endpoint should be accessible via long-lived API keys.

### Pattern 3: pghistory Selective Decoration

**What:** `@pghistory.track()` is applied only to models that require audit trails (Organization, Membership, APIKey, WebhookEndpoint). Core infra models (middleware state, health records) and billing models are not tracked.

**When to use:** Models where "who changed this and when" is a compliance or operational requirement.

**Trade-offs:** Selective decoration avoids audit table bloat. Products can add `@pghistory.track()` to additional models without code changes — just add the decorator and run `makemigrations`.

### Pattern 4: Outbound Webhooks as Application-Level Events

**What:** `WebhookService.dispatch_event(event_type, payload)` is called from service layer (not from controllers or signals directly). The service queries registered endpoints for that event type and fans out Celery tasks.

**When to use:** Any domain event that external systems might want to observe.

**Trade-offs:** Products must explicitly call `dispatch_event()` at the relevant service layer call site. There is no automatic "every model save triggers a webhook" behavior — that would produce excessive noise and tight coupling.

---

## Data Flow

### 1. Org-Scoped API Request

```
Client sends: GET /api/v1/orgs/{org_slug}/data/
    with X-API-Key: sk_live_abc123...
    ↓
Ninja auth chain: SessionAuth → jwt_token_auth → APIKeyAuth
    APIKeyAuth.authenticate():
        → SHA-256 hash the key
        → APIKey.objects.get(key_hash=hash, is_active=True)
        → set request.api_key, request.org = api_key.org
        → return api_key.user (request.auth = User)
    ↓
IsOrgMember permission:
    → Membership.objects.filter(org=request.org, user=request.user).exists()
    → True → proceed
    ↓
Controller → OrgService.get_data(org=request.org)
    ↓
Response + pghistory context records user + URL in audit shadow table
```

### 2. Outbound Webhook Dispatch

```
OrgBillingService processes subscription update
    ↓
WebhookService.dispatch_event(
    event_type="billing.subscription.updated",
    payload={"org_id": ..., "plan": ...},
    org=org
)
    ↓
WebhookEndpoint.objects.filter(
    org=org,
    is_active=True,
    events__contains="billing.subscription.updated"
)
    ↓
For each endpoint:
    deliver_webhook.delay(endpoint.pk, event_type, payload)
    ↓
Celery task:
    HMAC-SHA256 sign payload with endpoint.secret
    POST to endpoint.url
    On 2xx: record WebhookDelivery(status_code=200)
    On failure: autoretry with exponential backoff (max 7 attempts)
    On exhaustion: WebhookDelivery(failed_at=now)
```

### 3. Admin Impersonation Flow

```
Staff member opens /admin/accounts/user/
    → django-unfold renders Unfold-themed user list
    → django-hijack contrib adds "Impersonate" button per row
    ↓
Staff clicks "Impersonate user X"
    → POST /hijack/acquire/ (CSRF-protected)
    → hijack checks HIJACK_PERMISSION_CHECK → staff is superuser → allowed
    → hijack swaps session: staff session → user X session
    → structlog context: user_id now = X (not staff user)
    ↓
pghistory.HistoryMiddleware: records user = X for any model changes
    ← this is correct; impersonation means acting as X
    ↓
Staff finishes → POST /hijack/release/ → session restored to staff user
```

**Note:** Impersonation + audit logging: changes made during impersonation are recorded as belonging to the impersonated user. This is the expected B2B support pattern. If the product needs "this change was made by staff impersonating X", extend `AuditContextMiddleware.get_context()` to include `hijack_original_user` from the hijack session key.

---

## Build Order

Dependencies drive the sequence. Organization is the foundation for webhook endpoints, API keys, and per-org billing.

```
Phase A: Organization core (prerequisite for everything B2B)
  A1. Create apps/organizations/ (models: Organization, Membership)
  A2. Add permissions.py (IsOrgAdmin, IsOrgMember)
  A3. Add controllers, services, selectors (CRUD + member management)
  A4. Add data migration: seed "owner", "admin", "member" OrgRoles
  A5. Add signals.py: post_save → seed owner Membership
  A6. Add INSTALLED_APPS, scaffolder comment blocks
  WHY FIRST: Org FK is required by WebhookEndpoint, APIKey, OrgCustomer.
             Must exist before any other B2B model can be created.

Phase B: Per-org billing (depends on Organization)
  B1. Add OrgCustomer, OrgSubscription to apps/billing/models.py
  B2. Add OrgBillingService mirroring BillingService
  B3. Add has_org_feature(org, key) to billing/entitlements.py
  B4. Wire org billing to orgs controller (create org → auto-create OrgCustomer)
  WHY SECOND: Billing requires Organization FK. Must exist before webhooks
              can dispatch billing events.

Phase C: Outbound webhooks (depends on Organization for FK)
  C1. Create apps/webhooks/ (models: WebhookEndpoint, WebhookDelivery)
  C2. Add signing.py (HMAC-SHA256)
  C3. Add deliver_webhook Celery task (retry + backoff)
  C4. Add WebhookService.dispatch_event()
  C5. Add controllers for endpoint registration/listing
  WHY THIRD: No dependency on API keys. Can be used by session/JWT-auth
             users to register endpoints before API keys exist.

Phase D: API key auth (depends on Organization; independent of webhooks)
  D1. Create apps/apikeys/ (models: APIKey)
  D2. Add APIKeyAuth backend (APIKeyHeader subclass)
  D3. Add APIKeyService (create, revoke, rotate)
  D4. Add RequireScope permission class
  D5. Opt in org-scoped controllers to api_key_auth
  WHY FOURTH: No dependency on webhooks. Can be built in parallel with C
              but placed here to avoid merge conflicts on shared controller
              files.

Phase E: Audit logging (depends on Organization, APIKey, Webhooks models existing)
  E1. Add pghistory + pgtrigger to INSTALLED_APPS
  E2. Add HistoryMiddleware (or subclass) to MIDDLEWARE
  E3. Add @pghistory.track() decorators to Organization, Membership, APIKey,
      WebhookEndpoint models
  E4. Run makemigrations to generate shadow table migrations
  E5. Create apps/audit/admin.py to expose event tables in admin
  WHY FIFTH: pghistory decorators are additive — safe to apply after
             models are stable. Applying during model creation would force
             shadow table migrations alongside initial model migrations,
             creating unnecessary noise.

Phase F: Admin backoffice (depends on all B2B models existing)
  F1. Add "unfold", "hijack", "hijack.contrib.admin" to INSTALLED_APPS
  F2. Update existing accounts/admin.py, billing/admin.py to inherit
      from unfold.admin.ModelAdmin
  F3. Register Organization, Membership, APIKey, WebhookEndpoint,
      WebhookDelivery in their respective admin.py files
  F4. Configure UNFOLD sidebar navigation in settings
  F5. Add hijack URL to config/urls.py
  F6. Validate Unfold + Hijack compatibility (button renders correctly)
  WHY LAST: Admin is a view layer over already-built models. Safe to add
            last. No model or service code depends on admin configuration.
```

---

## Integration Points Summary

| Existing Component                       | Feature          | Change Type                                                                   |
| ---------------------------------------- | ---------------- | ----------------------------------------------------------------------------- |
| `apps/billing/models.py`                 | Per-org billing  | ADD: `OrgCustomer`, `OrgSubscription` models                                  |
| `apps/billing/services.py`               | Per-org billing  | ADD: `OrgBillingService` (parallel class, no changes to `BillingService`)     |
| `apps/billing/entitlements.py`           | Per-org billing  | ADD: `has_org_feature(org, key)` utility                                      |
| `config/settings/base.py`                | All B2B          | ADD: B2B_START/END blocks, UNFOLD config, HIJACK settings, pghistory settings |
| `INSTALLED_APPS`                         | All B2B          | ADD: 8 new entries inside B2B scaffolder block                                |
| `config/urls.py`                         | Admin backoffice | ADD: `path("hijack/", include("hijack.urls"))` inside B2B block               |
| `apps/accounts/admin.py`                 | Admin backoffice | MODIFY: change base class to `unfold.admin.ModelAdmin`                        |
| `apps/billing/admin.py`                  | Admin backoffice | MODIFY: change base class to `unfold.admin.ModelAdmin`                        |
| MIDDLEWARE list                          | Audit logging    | ADD: `pghistory.middleware.HistoryMiddleware` after auth middleware           |
| `apps/organizations/models.py`           | Audit logging    | ADD: `@pghistory.track()` decorators                                          |
| `apps/apikeys/models.py`                 | Audit logging    | ADD: `@pghistory.track()` decorators                                          |
| `apps/webhooks/models.py`                | Audit logging    | ADD: `@pghistory.track()` decorators                                          |
| `packages/shared-types/`                 | All B2B          | REGENERATE: after each set of new endpoints is stable                         |
| CLI scaffolder (`create-foundation-app`) | All B2B          | ADD: `--with b2b` flag that includes all 6 phases                             |

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Modifying BillingService for Org Billing

**What people do:** Add `entity_type` and `entity_id` parameters to the existing `BillingService` methods to handle both user and org billing through one service.

**Why it's wrong:** `BillingService` has 40+ test cases and validated behavior. Introducing an entity discriminator parameter adds branching to every method, increases test surface, and risks regressions. The existing v1.1 billing tests would need updates.

**Do this instead:** Create `OrgBillingService` as a parallel class. The overlap is 4 methods (create_customer, create_checkout_session, get_status, get_subscription_detail). Small duplication is preferable to modified tested code.

### Anti-Pattern 2: Storing Raw API Keys

**What people do:** Store the full API key string in the database to allow "re-displaying" it or for simpler lookup.

**Why it's wrong:** A database breach exposes all API keys. Industry standard (GitHub, Stripe, Vercel) is to show the key exactly once and store only the hash.

**Do this instead:** `key_hash = SHA-256(raw_key)`. Store only `key_hash` and the `prefix` (first 12 chars for display). On lookup, hash the incoming key and compare. The raw key is gone after creation.

### Anti-Pattern 3: Tracking Every Model with pghistory

**What people do:** Add `@pghistory.track()` to all models uniformly to avoid thinking about which ones need audit trails.

**Why it's wrong:** pghistory creates shadow tables for every tracked model. With many models, this doubles table count, doubles migration complexity, and produces massive audit data for high-write tables (e.g. `WebhookDelivery` has a row per delivery attempt — tracking it would double writes on an already write-heavy table).

**Do this instead:** Track only models where audit trail is a requirement: Organization, Membership, APIKey, WebhookEndpoint. Do not track WebhookDelivery (it is already an event log), Customer, Subscription (Stripe is the source of truth), or structlog-covered request events.

### Anti-Pattern 4: Inbound vs. Outbound Webhook Confusion

**What people do:** Place outbound webhook dispatch logic in `apps/billing/webhooks.py` alongside the existing Stripe inbound handler.

**Why it's wrong:** The inbound handler (`stripe_webhook`) is a plain Django view receiving Stripe events. Outbound dispatch is application code sending events to customers. Mixing them creates confusion about data direction, coupling Stripe-specific code to a general-purpose system, and making `--with b2b` scaffolder removal harder.

**Do this instead:** `apps/billing/webhooks.py` = inbound Stripe only (unchanged). `apps/webhooks/` = all outbound delivery logic.

### Anti-Pattern 5: Webhook Delivery Without Idempotency Key

**What people do:** Deliver webhooks without a `X-Webhook-Delivery` header or delivery ID, relying on the customer to handle deduplication.

**Why it's wrong:** Celery retries mean the same event can be delivered multiple times. Without a stable delivery ID, customers cannot deduplicate and may process the same event twice (double charge, duplicate resource creation).

**Do this instead:** Generate a UUID delivery ID when `WebhookDelivery` is created. Include it as `X-Webhook-Delivery: <uuid>` on every delivery attempt. Celery retries use the same delivery ID. Customers can deduplicate on this ID.

---

## Scaling Considerations

| Scale         | Architecture Adjustments                                                                                                                                                                                                                                                                                                        |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0-1k users    | All B2B features work as described. Outbound webhook fanout at this scale is negligible.                                                                                                                                                                                                                                        |
| 1k-100k users | Webhook fanout per event can become a bottleneck if an org has many endpoints. Use a dedicated Celery queue (`webhooks`) to isolate from billing and email queues. Org permission checks (`IsOrgMember`) should cache membership results in Redis (per-request TTL).                                                            |
| 100k+ users   | Outbound webhook delivery should move to a dedicated worker pool. pghistory audit tables will grow large — add Postgres table partitioning by `created_at` on high-write event models. API key lookups on `key_hash` should have a DB index (already enforced by `unique=True` on `prefix` — add explicit index on `key_hash`). |

---

## Sources

- Django Ninja authentication API — `APIKeyHeader` class and `authenticate()` override: [django-ninja.dev/guides/authentication/](https://django-ninja.dev/guides/authentication/) — HIGH confidence (official docs, verified via WebFetch)
- django-pghistory middleware and context tracking: [django-pghistory.readthedocs.io/en/2.9.0/context/](https://django-pghistory.readthedocs.io/en/2.9.0/context/) — HIGH confidence (official docs)
- django-pghistory v3.6.0, April 2025 — actively maintained, PostgreSQL trigger approach: [pypi.org/project/django-pghistory/](https://pypi.org/project/django-pghistory/) — HIGH confidence
- Caktus Group pghistory best practices (2025): [caktusgroup.com/blog/2025/04/07/tips-tracking-django-model-changes-django-pghistory/](https://www.caktusgroup.com/blog/2025/04/07/tips-tracking-django-model-changes-django-pghistory/) — MEDIUM confidence (community, verified against official docs)
- django-unfold admin theme: [unfoldadmin.com/docs/](https://unfoldadmin.com/docs/) — HIGH confidence (official docs, verified via WebFetch)
- django-hijack v3 admin integration: [django-hijack.readthedocs.io/](https://django-hijack.readthedocs.io/) — HIGH confidence (official docs, verified via WebFetch)
- Webhook HMAC signing and retry patterns: [hookdeck.com/outpost/guides/outbound-webhook-retry-best-practices](https://hookdeck.com/outpost/guides/outbound-webhook-retry-best-practices) — MEDIUM confidence (industry guide, consistent with Stripe/GitHub patterns)
- Per-org Stripe customer association best practice: [saaspegasus.com/guides/django-stripe-integrate/](https://www.saaspegasus.com/guides/django-stripe-integrate/) — MEDIUM confidence (community, consistent with Stripe official guidance)
- Existing codebase inspection: `apps/billing/adapters.py`, `apps/billing/models.py`, `apps/accounts/permissions.py`, `apps/billing/entitlements.py`, `apps/billing/webhooks.py`, `config/urls.py`, `config/settings/base.py`, `apps/core/middleware.py`, `apps/core/models.py` — HIGH confidence (direct inspection)

---

_v1.4 B2B Module — Foundation Template_
_Researched: 2026-03-12_
