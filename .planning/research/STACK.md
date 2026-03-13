# Stack Research: B2B Module (v1.4)

**Project:** Foundation Template — v1.4 milestone
**Domain:** B2B SaaS module — organizations, outbound webhooks, API keys, audit logging, admin backoffice
**Researched:** 2026-03-12
**Overall confidence:** HIGH for library choices and versions; MEDIUM for django-organizations vs custom model tradeoff (design decision, not a library question)

> **Scope note:** This document covers ONLY the net-new libraries needed for v1.4.
> The full prior stack (Django Ninja Extra, Next.js 15+, Expo SDK 53+, Django Allauth headless,
> Celery + Redis, structlog, OpenTelemetry, PostHog, Stripe, WeasyPrint, Turborepo, pnpm,
> pytest, Vitest, django-ratelimit, django-redis, django-csp, django-anymail, premailer,
> expo-apple-authentication, LangGraph, schemathesis, etc.) is already decided.
> See `.planning/research/STACK.md` (v1.3 edition) for prior decisions.

> **Critical correction:** The project brief specified `django-pgaudit` for audit logging.
> This package **does not exist on PyPI** (confirmed: 404 from PyPI JSON API).
> `pgaudit` is a raw PostgreSQL extension, not a Django package.
> The correct Python library is `django-pghistory` v3.9.2 — see section 3 below.

---

## Decision Summary

| Feature                              | Chosen Library / Approach                                 | Version Pin    | Confidence |
| ------------------------------------ | --------------------------------------------------------- | -------------- | ---------- |
| Organization + membership model      | Custom Django model (no library)                          | no new library | HIGH       |
| Outbound webhook registry + delivery | Custom Celery tasks + `httpx` (already available)         | no new library | HIGH       |
| API key model + scopes               | Custom Django model (no library)                          | no new library | HIGH       |
| Per-API-key rate limiting            | `django-ratelimit` (already installed) with custom key fn | no new library | HIGH       |
| Audit log — who changed what, when   | `django-pghistory`                                        | `>=3.9,<4`     | HIGH       |
| Admin backoffice theme               | `django-unfold`                                           | `>=0.83,<1`    | HIGH       |
| Customer support impersonation       | `django-hijack`                                           | `>=3.7,<4`     | HIGH       |

**One-liner:** Three new Python packages (`django-pghistory`, `django-unfold`, `django-hijack`);
zero new JS/TS packages; zero new mobile packages. Organization, API key, and webhook
infrastructure is custom code using the existing stack.

---

## 1. Audit Logging: django-pghistory

| Technology         | Version                        | Purpose                                                                            | Why                                                                                                                                                                                                                                             |
| ------------------ | ------------------------------ | ---------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `django-pghistory` | `>=3.9,<4`                     | Track model changes (who changed what, when, from where) using PostgreSQL triggers | Trigger-based tracking is immune to Django signal bypasses — bulk updates, raw SQL, and ORM calls all get logged. Designed for PostgreSQL (which this project mandates). Actively maintained by AmbitionEng; v3.9.2 released February 17, 2026. |
| `django-pgtrigger` | (auto-installed as dependency) | PostgreSQL trigger management — pulled in by django-pghistory                      | Do not pin separately; pghistory manages its version.                                                                                                                                                                                           |

### Why django-pghistory and NOT django-auditlog

`django-auditlog` v3.4.1 (December 18, 2025) uses Django signals (`post_save`, `pre_delete`).
Signal-based logging has a critical gap: **bulk operations and raw SQL bypass signals entirely**.
In a B2B product where "who changed org membership, when" is a compliance requirement,
a missed bulk update is an audit hole.

`django-pghistory` installs PostgreSQL triggers on migration. Every INSERT, UPDATE, and DELETE
hits the trigger regardless of how the change was made. The event models mirror the tracked
model's fields exactly — no JSON blob serialization.

Additional B2B-relevant features of django-pghistory:

- `append_only=True` on event tables makes the audit log tamper-evident (rows cannot be updated or deleted)
- Middleware context tracking: attach `request.user` and `request.path` to all events in a request automatically via `pghistory.context()`
- Event models are auto-generated Django models — queryable with standard ORM, no custom query API to learn
- Compatible with PostgreSQL 14–18, Django 4.2–6.0, Python 3.10–3.14 (confirmed via PyPI)

**Why not raw `pgaudit` PostgreSQL extension:**
`pgaudit` is a Postgres server extension that logs to the PostgreSQL log file. It cannot attach
user/request context (Django request.user is not a database concept), produces unstructured
log output, and requires log parsing infrastructure to be useful. It is appropriate for
database-level compliance (DBA access auditing) — not for application-level "who clicked what"
audit trails. `django-pghistory` solves the application-level problem.

### Usage pattern

```python
# apps/api/orgs/models.py
import pghistory

@pghistory.track(pghistory.Snapshot(), append_only=True)
class OrganizationMembership(models.Model):
    organization = models.ForeignKey("Organization", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=50)

# middleware — attach user context to all events in a request
# apps/api/core/middleware.py
import pghistory

class PGHistoryMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        with pghistory.context(user=getattr(request.user, "pk", None)):
            return self.get_response(request)
```

### Net-New Environment Variables

None. django-pghistory uses the existing Django `DATABASES["default"]` connection.

---

## 2. Admin Backoffice: django-unfold

| Technology      | Version     | Purpose                                                     | Why                                                                                                                                                                                                                                                                                                                                                                                                        |
| --------------- | ----------- | ----------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `django-unfold` | `>=0.83,<1` | Modern Tailwind-based Django admin theme for the backoffice | Built on top of `django.contrib.admin` — no model migrations, no admin code changes beyond `ModelAdmin` subclassing from `UnfoldModelAdmin`. v0.83.1 released March 5, 2026. Requires Python ≥3.11, Django 4.2–6.0. Actively maintained (~weekly releases). Provides sidebar navigation, filters, dashboards, dark/light mode. Widely used — the standard choice for Django admin theming as of 2025/2026. |

### Why django-unfold and NOT alternatives

| Alternative                | Why Not                                                          |
| -------------------------- | ---------------------------------------------------------------- |
| `django-jazzmin`           | Less actively maintained; Tailwind 3 only; no dark mode API      |
| `django-grappelli`         | Older aesthetic (Bootstrap 2 era); not actively developed        |
| Raw `django.contrib.admin` | Acceptable but visually outdated; customer support team friction |
| `django-jet-reloaded`      | Abandoned 2022                                                   |

`django-unfold` is the [Django project's own recommended choice](https://www.djangoproject.com/weblog/2025/apr/18/admin-theme-roundup/) as of April 2025 (confirmed via Django blog).

### Integration with existing stack

`django-unfold` wraps `django.contrib.admin` and requires no changes to existing models.
Existing `ModelAdmin` subclasses are updated to inherit from `UnfoldModelAdmin` instead.
The template's admin module is minimal (no existing `ModelAdmin` registrations beyond
auth/allauth defaults), so the migration surface is small.

```python
# apps/api/core/admin.py
from unfold.admin import ModelAdmin as UnfoldModelAdmin

@admin.register(Organization)
class OrganizationAdmin(UnfoldModelAdmin):
    list_display = ["name", "created_at", "member_count"]
```

### Settings requirement

```python
# settings/base.py
INSTALLED_APPS = [
    "unfold",           # must be BEFORE django.contrib.admin
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "django.contrib.admin",
    ...
]
```

### Net-New Environment Variables

None.

---

## 3. Customer Support Impersonation: django-hijack

| Technology      | Version    | Purpose                                                                                | Why                                                                                                                                                                                                     |
| --------------- | ---------- | -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `django-hijack` | `>=3.7,<4` | Allow admin users to log in as another user for support without knowing their password | v3.7.6 released January 6, 2026. Requires Python ≥3.10, supports Django 4.2, 5.2, 6.0. 63,992 weekly PyPI downloads — actively used. Maintained by the django-hijack organization (not a solo project). |

### Security model

django-hijack v3.x (compared to the older v2 branch) has a significantly improved security model:

- Impersonation is CSRF-protected (POST-only)
- A "hijack banner" is shown to the impersonating admin while in the target user's session — cannot be silently active
- The `HIJACK_PERMISSION_CHECK` setting controls who can hijack whom (default: superusers only)
- All hijack/release events are logged to Django's request log (pair with structlog for audit trail)

### Integration with django-unfold

`django-hijack` ships `hijack.contrib.admin` — a Django admin mixin that adds a "Hijack" button
to the User admin list view. This renders inside django-unfold's admin theme without additional
configuration because unfold wraps `django.contrib.admin` (the hijack contrib targets the standard
admin template extension points, which unfold preserves).

No dedicated `django-hijack-unfold` package is needed. The `hijack.contrib.admin` buttons will
render inside the unfold theme as standard admin actions.

```python
# INSTALLED_APPS addition
"hijack",
"hijack.contrib.admin",

# URLs addition (apps/api/urls.py)
path("hijack/", include("hijack.urls")),

# Settings
HIJACK_PERMISSION_CHECK = "hijack.permissions.superusers_and_staff"  # or custom callable
```

### Why not django-impersonate

`django-impersonate` v1.9.4 (May 2024) is an alternative impersonation library. django-hijack
is preferred because:

- More active maintenance cadence (3.7.6 in January 2026 vs 1.9.4 in May 2024)
- Better security model in v3.x (CSRF protection, visual banner)
- Wider adoption (~64K weekly downloads; django-impersonate has ~15K)

### Net-New Environment Variables

None. Impersonation is controlled via Django settings, not environment variables.

---

## 4. Organization Model: Custom Code (No New Library)

The project brief lists `django-organizations` as a candidate. After evaluation, the recommendation
is a **custom Django model** with no new library dependency.

### Why NOT django-organizations v2.6.0

`django-organizations` v2.6.0 (March 8, 2026) provides three models: `Organization`,
`OrganizationUser` (through model), and `OrganizationOwner`. The package is maintained and
current, but it adds constraints inappropriate for a template:

1. **Fixed role model:** `OrganizationUser` has only `is_admin` boolean. The v1.4 requirement
   specifies roles (e.g., `owner`, `admin`, `member`, `billing`) — this requires subclassing
   or replacing the through model, which is the complex part anyway.

2. **Generic views and forms:** The library ships CRUD views designed for standalone use.
   The template uses Django Ninja Extra endpoints — the views are unused bloat.

3. **No per-org billing hooks:** Per-org billing requires a FK to the Stripe customer on the
   `Organization` model. Adding it means either monkey-patching the library model or
   using the library's `base_organization_model` abstract class. The latter is fine but adds
   an abstraction layer with no benefit over writing the model directly.

4. **Migration coupling:** The library's migrations must be applied before any custom models
   that FK into `Organization`. When the template is cloned into a new project and the scaffolder
   removes the B2B module, migration cleanup is more complex with a third-party migration set.

**Custom model is 40 lines and provides full control:**

```python
# apps/api/orgs/models.py
class Organization(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    stripe_customer_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class OrgMembership(models.Model):
    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        ADMIN = "admin", "Admin"
        MEMBER = "member", "Member"
        BILLING = "billing", "Billing"

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="org_memberships")
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("organization", "user")]
```

No new library. The v1.3 `RequireRole` permission class is extended with an org-scoped variant.

---

## 5. Outbound Webhooks: Custom Celery Tasks + httpx (No New Library)

The project brief identifies `django-webhook` as a candidate. After evaluation, the recommendation
is **custom delivery infrastructure using existing Celery + httpx**.

### Why NOT django-webhook v0.0.15

`django-webhook` v0.0.15 (August 19, 2024) provides trigger-on-model-change webhooks (outbound
notifications when Django models are saved/deleted). Key issues for this template:

1. **Model-change trigger model is wrong for B2B.** The v1.4 requirement is a **registry** — users
   define webhook endpoints, and the application fires events programmatically (e.g., "org.member.added",
   "subscription.upgraded"). This is the Stripe/GitHub webhook pattern, not an ORM signal→HTTP pattern.

2. **Last release August 2024.** No releases in 7+ months. The package is in early development
   (`0.0.x`). A template shipping this in production exposes every downstream project to
   a stale dependency.

3. **httpx is already available.** The existing stack uses `httpx` for async HTTP (LangGraph
   tools, Schemathesis). Delivering an HTTP POST to a webhook URL with HMAC signing is ~50 lines
   of Celery task code.

### Custom webhook delivery design

```
apps/api/webhooks/
├── models.py       — WebhookEndpoint (url, secret, event_types[], active)
│                   — WebhookDelivery (endpoint FK, event, payload, status, attempts, next_retry_at)
├── services.py     — fire_event(org_id, event_type, payload) → enqueues Celery task
├── tasks.py        — deliver_webhook.apply_async() with exponential backoff retry
├── signing.py      — hmac_sign(secret, payload_bytes) → "sha256=<hex>"
└── api.py          — CRUD for WebhookEndpoint (org-scoped)
```

**Celery retry schedule** (matches Stripe's pattern):
`countdown = min(60 * 2 ** attempt, 86400)` — 1m, 2m, 4m, 8m, ... up to 24h, max 5 attempts.

**HMAC signing** (Standard Webhooks spec — `svix` compatible):

```python
import hashlib, hmac, time

def hmac_sign(secret: str, timestamp: int, payload_bytes: bytes) -> str:
    msg = f"{timestamp}.".encode() + payload_bytes
    sig = hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()
    return f"sha256={sig}"
```

**No new library required.** `httpx` for HTTP delivery (already in the environment via LangGraph);
`celery` for async queuing and retry (already installed v1.2); `hmac` and `hashlib` are stdlib.

---

## 6. API Key Model: Custom Code (No New Library)

`djangorestframework-api-key` v3.1.0 is a DRF-specific package. This project uses Django Ninja Extra.
The package's `HasAPIKey` permission class is a DRF `BasePermission` subclass — it does not
integrate with Ninja Extra's `BasePermission`. The package also has no scope or per-key rate
limiting support.

**Custom model is 60 lines:**

```python
# apps/api/api_keys/models.py
import secrets
from django.utils.crypto import constant_time_compare

class APIKey(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active"
        REVOKED = "revoked"

    organization = models.ForeignKey("orgs.Organization", on_delete=models.CASCADE, related_name="api_keys")
    name = models.CharField(max_length=100)
    key_prefix = models.CharField(max_length=8, db_index=True)  # for lookup (non-secret)
    key_hash = models.CharField(max_length=128)  # SHA-256 of full key
    scopes = models.JSONField(default=list)       # ["webhooks:write", "members:read"]
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    last_used_at = models.DateTimeField(null=True, blank=True)
    request_count = models.PositiveBigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
```

The full key (`sk_live_<prefix>.<random>`) is shown once at creation and never stored.
Only the prefix (for DB lookup) and SHA-256 hash (for verification) are stored.

**Ninja Extra authentication class** (replaces DRF `HasAPIKey`):

```python
# apps/api/api_keys/auth.py
from ninja.security import HttpBearer

class APIKeyAuth(HttpBearer):
    def authenticate(self, request, token: str):
        prefix = token[:8]
        key = APIKey.objects.filter(key_prefix=prefix, status="active").select_related("organization").first()
        if key and constant_time_compare(hash_key(token), key.key_hash):
            request.api_key = key
            return key
        return None
```

**Per-key rate limiting** using existing `django-ratelimit`:

```python
from django_ratelimit.decorators import ratelimit

@ratelimit(key=lambda g, r: r.api_key.key_prefix, rate="1000/h", method="ALL", block=True)
def my_endpoint(request):
    ...
```

`django-ratelimit` (already installed since v1.2) supports callable `key=` functions — passes
the API key prefix as the rate limit key, so each API key gets its own bucket backed by Redis.

---

## Alternatives Considered

| Category           | Recommended         | Alternative                      | Why Not                                                                                             |
| ------------------ | ------------------- | -------------------------------- | --------------------------------------------------------------------------------------------------- |
| Audit logging      | `django-pghistory`  | `django-auditlog`                | Signal-based; misses bulk updates and raw SQL; audit gaps unacceptable in B2B                       |
| Audit logging      | `django-pghistory`  | raw `pgaudit` Postgres extension | No Django request context; logs to Postgres log file; requires log parsing; wrong abstraction level |
| Admin theme        | `django-unfold`     | `django-jazzmin`                 | Less maintained; no active dark mode; last significant update 2024                                  |
| Admin theme        | `django-unfold`     | `django-grappelli`               | Bootstrap 2-era; not actively developed                                                             |
| Impersonation      | `django-hijack`     | `django-impersonate`             | Lower download count (~15K/week vs 64K); less active maintenance                                    |
| Organization model | Custom model        | `django-organizations`           | Fixed binary `is_admin` role model; ships unused views; harder to remove via CLI scaffolder         |
| API key model      | Custom model        | `djangorestframework-api-key`    | DRF-specific `BasePermission`; no Ninja Extra integration; no scope support                         |
| Webhook delivery   | Custom Celery tasks | `django-webhook`                 | ORM trigger model (wrong pattern for registry); `0.0.x` pre-release; stale (Aug 2024)               |

---

## What NOT to Add

| Avoid                          | Why                                                                                                      | Use Instead                                                               |
| ------------------------------ | -------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| `django-pgaudit`               | Does not exist on PyPI (404 confirmed)                                                                   | `django-pghistory`                                                        |
| `djangorestframework-api-key`  | DRF-specific; incompatible with Ninja Extra's `BasePermission`                                           | Custom `APIKey` model + `HttpBearer` auth class                           |
| `django-organizations`         | Fixed binary role model; ships unused view layer; harder to remove from CLI scaffolder                   | Custom `Organization` + `OrgMembership` models (40 lines)                 |
| `django-webhook`               | Wrong delivery model for registry pattern; `0.0.x` pre-release; 7+ months stale                          | Custom Celery task with exponential backoff + `httpx`                     |
| `django-guardian`              | Object-level row permissions — not the requirement; adds migration complexity                            | Org-scoped `RequireOrgRole` permission class extending v1.3 `RequireRole` |
| `django-tenants`               | PostgreSQL schema-per-tenant multi-tenancy — not the requirement; incompatible with shared-schema design | Custom Organization FK on resources                                       |
| `pgaudit` PostgreSQL extension | Server-level logging only; no Django request context; needs log parsing                                  | `django-pghistory`                                                        |

---

## Module Removability (CLI Scaffolder Contract)

### `--without b2b` (or `--without b2b-module`)

Remove:

- `django-pghistory` + `django-pgtrigger` from `pyproject.toml`
- `django-unfold` from `pyproject.toml` (revert admin to standard `django.contrib.admin`)
- `django-hijack` from `pyproject.toml`
- `apps/api/orgs/` directory
- `apps/api/webhooks/` directory
- `apps/api/api_keys/` directory
- `pghistory` + `pghistory.middleware` from `INSTALLED_APPS` and `MIDDLEWARE`
- `unfold` + `unfold.contrib.*` from `INSTALLED_APPS`
- `hijack` + `hijack.contrib.admin` from `INSTALLED_APPS`
- `path("hijack/", ...)` from `urls.py`
- `UnfoldModelAdmin` references in any admin modules (revert to `ModelAdmin`)

The B2B module has clean boundaries — all new code is in its own domain apps. No modifications
are made to the existing User model, billing module, or auth flows. Removal is surgical.

---

## Installation Commands

```bash
# Python — inside apps/api/
uv add "django-pghistory>=3.9,<4"
uv add "django-unfold>=0.83,<1"
uv add "django-hijack>=3.7,<4"

# django-pgtrigger is pulled in automatically as a django-pghistory dependency.
# No separate pin needed.

# No new Python packages for Organization, APIKey, or webhook delivery.
# No new JS/TS packages.
# No new mobile packages.
```

---

## Version Compatibility

| Package            | Version  | Django        | Python    | Notes                                                          |
| ------------------ | -------- | ------------- | --------- | -------------------------------------------------------------- |
| `django-pghistory` | `3.9.2`  | 4.2–6.0       | 3.10–3.14 | Released Feb 17, 2026; auto-installs `django-pgtrigger` 4.17.0 |
| `django-pgtrigger` | `4.17.0` | 4.2–6.0       | 3.10+     | Pulled as dependency; do not pin separately                    |
| `django-unfold`    | `0.83.1` | 4.2–6.0       | ≥3.11     | Released Mar 5, 2026; pre-1.0 but very stable cadence          |
| `django-hijack`    | `3.7.6`  | 4.2, 5.2, 6.0 | ≥3.10     | Released Jan 6, 2026; 63K weekly downloads                     |

**Python version note:** `django-unfold` requires Python ≥3.11. The project targets Python 3.12+
(CLAUDE.md), so this is satisfied.

**Django 5.x note:** `django-hijack` 3.7.6 lists Django 5.2 (not 5.0 or 5.1) as supported.
If the project is running Django 5.0 or 5.1, pin to a compatible version or test explicitly.
Django 5.2 is the current LTS-candidate release (April 2025) and is the recommended version.

---

## Sources

- [django-pghistory PyPI](https://pypi.org/project/django-pghistory/) — v3.9.2, February 17, 2026 (HIGH — PyPI metadata)
- [django-pghistory docs](https://django-pghistory.readthedocs.io/en/3.9.1/) — trigger-based tracking, `append_only`, context middleware (HIGH — official docs)
- [django-pghistory GitHub](https://github.com/AmbitionEng/django-pghistory) — maintained by AmbitionEng (HIGH — official repo)
- [django-pgtrigger PyPI](https://pypi.org/project/django-pgtrigger/) — v4.17.0, auto-dependency (HIGH — PyPI)
- [django-auditlog PyPI](https://pypi.org/project/django-auditlog/) — v3.4.1, December 2025; signal-based (HIGH — PyPI, used for comparison)
- [django-unfold PyPI](https://pypi.org/project/django-unfold/) — v0.83.1, March 5, 2026 (HIGH — PyPI)
- [django-unfold GitHub](https://github.com/unfoldadmin/django-unfold) — feature list, ModelAdmin integration (HIGH — official repo)
- [Django Admin Theme Roundup 2025](https://www.djangoproject.com/weblog/2025/apr/18/admin-theme-roundup/) — django-unfold recommended (HIGH — official Django blog)
- [django-hijack PyPI](https://pypi.org/project/django-hijack/) — v3.7.6, January 6, 2026; 63,992 weekly downloads (HIGH — PyPI)
- [django-hijack docs](https://django-hijack.readthedocs.io/en/latest/) — CSRF protection, banner, `HIJACK_PERMISSION_CHECK` (HIGH — official docs)
- [django-hijack GitHub](https://github.com/django-hijack/django-hijack) — Django 5.2 + 6.0 compatibility (HIGH — official repo)
- [django-organizations GitHub](https://github.com/bennylope/django-organizations) — v2.6.0, March 8, 2026; binary `is_admin` role model (HIGH — official repo; used to confirm library is insufficient)
- [djangorestframework-api-key PyPI](https://pypi.org/project/djangorestframework-api-key/) — v3.1.0, April 4, 2025; DRF-specific (HIGH — PyPI; used to confirm not usable with Ninja)
- [django-webhook PyPI](https://pypi.org/project/django-webhook/) — v0.0.15, August 19, 2024; last release 7+ months ago (MEDIUM — PyPI; used to confirm stale)
- [django-pgaudit PyPI JSON API](https://pypi.org/pypi/django-pgaudit/json) — 404 Not Found; package does not exist (HIGH — confirmed via direct API call)
- [django-ratelimit docs — custom key functions](https://django-ratelimit.readthedocs.io/en/stable/usage.html) — callable `key=` parameter for per-API-key buckets (HIGH — official docs)
- [Standard Webhooks spec](https://github.com/standard-webhooks/standard-webhooks/blob/main/spec/standard-webhooks.md) — HMAC-SHA256 signing format (MEDIUM — industry spec)

---

_Stack research for: Foundation Template v1.4 — B2B Module_
_Researched: 2026-03-12_
