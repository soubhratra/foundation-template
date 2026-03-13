# Phase 30: Admin Backoffice - Research

**Researched:** 2026-03-13
**Domain:** Django admin theming (django-unfold) + user impersonation (django-hijack) + audit log admin
**Confidence:** HIGH (core libraries), MEDIUM (unfold+hijack joint integration)

---

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions

- **Sidebar navigation structure:** Flat "B2B" section grouping all B2B models (Organizations, Memberships, API Keys, Webhooks, Audit Log). All sections configured: B2B, Users & Auth, Billing, System. Staff gets a complete organized sidebar from day one — no ungrouped default list.
- **Icons:** Heroicons (outline style) for section headers and model items [see ICON CORRECTION below]
- **Config location:** `UNFOLD = {...}` dict defined inline in `config/settings/base.py`
- **Sidebar structure:** B2B (Organizations, Memberships, API Keys, Webhooks, Audit Log), Users & Auth (Users), Billing (Customers, Subscriptions, Payments, Plan Provider Mappings, Processed Webhook Events), System (Periodic Tasks, Task Results)
- **ModelAdmin scope:** Functional but lean — list_display (4-5 columns), list_filter on status/type fields, search_fields on name/email/identifier. No inlines, no custom actions beyond impersonation.
- **One admin.py per app:** `apps/orgs/admin.py`, `apps/api_keys/admin.py`, `apps/webhooks/admin.py`, `apps/audit/admin.py` (new files). `apps/billing/admin.py` and `apps/accounts/admin.py` updated.
- **Impersonation trigger:** User change page only (`/admin/accounts/user/{id}/change/`)
- **Banner:** hijack's built-in banner injection. No custom template.
- **Restriction:** Cannot impersonate staff users or superusers
- **Post-release redirect:** `HIJACK_LOGOUT_REDIRECT_URL` points back to the impersonated user's admin change page
- **Audit log columns:** `timestamp`, `action`, `actor_email`, `model_name`, `object_id`, `impersonator_email`
- **Audit log read-only:** `has_add_permission`, `has_change_permission`, `has_delete_permission` all return `False`
- **Audit log filters:** `action` (exact), `model_name` (exact), `HasImpersonatorFilter` boolean filter
- **Audit log search:** `actor_email`, `object_id`

### Claude's Discretion

- Exact icon name choices per model/section (use contextually appropriate icons)
- Whether `impersonator_email` is a computed `list_display` column derived from `impersonator_id` FK lookup or stored directly
- Exact `can_be_hijacked` permission check implementation (inline in `accounts/admin.py` vs standalone function)
- System section contents — include/exclude based on which Celery apps are installed at build time

### Deferred Ideas (OUT OF SCOPE)

- Custom unfold banner template matching unfold theme colors
- Inlines (e.g. Memberships inline under Organization)
- GDPR erasure / superuser-only audit log deletion
- Action prefix matching filter in audit log admin
  </user_constraints>

---

<phase_requirements>

## Phase Requirements

| ID       | Description                                                                                                                                                   | Research Support                                                                                                                                                                    |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ADMIN-01 | Django admin themed with `django-unfold` across all domain `ModelAdmin` registrations; navigation sidebar configured                                          | django-unfold 0.84.0 installation, UNFOLD settings dict structure, UnfoldModelAdmin migration pattern, UserAdmin Unfold forms                                                       |
| ADMIN-02 | Staff users can impersonate any non-staff user via `django-hijack`; persistent banner shown; impersonation events written to audit log with `impersonator` FK | django-hijack 3.7.6 signals (hijack_started/hijack_ended), HIJACK_PERMISSION_CHECK custom function, HijackUserMiddleware, AuditContextMiddleware extension for impersonator context |

</phase_requirements>

---

## Summary

Phase 30 introduces two orthogonal features: (1) a polished admin UI via django-unfold, replacing the default Django admin theme and wrapping all existing ModelAdmin registrations with `UnfoldModelAdmin`; and (2) staff impersonation via django-hijack 3.7.6, restricted to non-staff/non-superuser accounts, with every start/end event recorded in the pghistory audit context.

The critical architectural insight: the project's "AuditLog" is NOT a standalone model with an `impersonator_id` FK field. It is the pghistory Context system — an in-request context dict stored in the `pghistory_context` table. The `impersonator` must be added as a key in that context dict by extending `AuditContextMiddleware`. The admin audit log view reads from pghistory event tables (OrganizationEvent, MembershipEvent, APIKeyEvent, WebhookEndpointEvent) joined to their context metadata.

**ICON CORRECTION (HIGH confidence):** The CONTEXT.md states "Heroicons (outline style)" but django-unfold uses **Material Symbols** (Google Material Icons), not Heroicons. This is confirmed by the official docs and an open GitHub issue (#1174) tracking a font file refresh. The sidebar `"icon"` field takes Material Symbols names (e.g., `"people"`, `"business"`, `"vpn_key"`). The planner should use Material Symbols icon names, not Heroicon names.

**Primary recommendation:** Install unfold first, run smoke test on admin rendering, then add hijack — wire signal handlers to extend audit context before building the full ModelAdmin suite.

---

## Standard Stack

### Core

| Library       | Version | Purpose                  | Why Standard                                                                                     |
| ------------- | ------- | ------------------------ | ------------------------------------------------------------------------------------------------ |
| django-unfold | 0.84.0  | Django admin theme       | Officially recommended by Django project (April 2025); wraps standard admin, no model migrations |
| django-hijack | 3.7.6   | Staff user impersonation | Security-first v3 rewrite; supports Django 4.2/5.2/6.0; built-in admin integration via contrib   |

### Supporting (already in project)

| Library          | Version | Purpose             | When to Use                                                    |
| ---------------- | ------- | ------------------- | -------------------------------------------------------------- |
| django-pghistory | 3.9.2   | Audit event storage | Events already tracked; Phase 30 adds impersonator context key |

### New Dependencies

Neither `django-unfold` nor `django-hijack` are in `apps/api/pyproject.toml` — both must be added.

**Installation:**

```bash
cd apps/api
uv add "django-unfold>=0.84.0" "django-hijack>=3.7.6"
```

### Alternatives Considered

| Instead of    | Could Use                        | Tradeoff                                                                                |
| ------------- | -------------------------------- | --------------------------------------------------------------------------------------- |
| django-unfold | django-jazzmin, django-grappelli | Unfold is the current officially recommended theme; others have less active maintenance |
| django-hijack | django-impersonate               | hijack has higher adoption (1.7k stars), security-first v3 design                       |

---

## Architecture Patterns

### INSTALLED_APPS Order (CRITICAL)

django-unfold **must appear before `django.contrib.admin`** in INSTALLED_APPS:

```python
INSTALLED_APPS = [
    "unfold",             # MUST be before django.contrib.admin
    "unfold.contrib.filters",   # Optional: enhanced filter widgets
    # B2B_START
    "hijack",             # B2B MODULE — impersonation
    "hijack.contrib.admin",  # B2B MODULE — admin button integration
    # B2B_END
    "django.contrib.admin",
    # ... rest of apps
]
```

The `django.contrib.admin` line currently at position 0 in INSTALLED_APPS must be relocated. This is a required change to `config/settings/base.py`.

### Middleware Order (CRITICAL)

`hijack.middleware.HijackUserMiddleware` must be placed **after** `django.contrib.auth.middleware.AuthenticationMiddleware`:

```python
MIDDLEWARE = [
    # ... existing middleware ...
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # B2B_START (add after auth middleware)
    "hijack.middleware.HijackUserMiddleware",   # B2B MODULE — impersonation session
    # B2B_END
    "allauth.account.middleware.AccountMiddleware",
    # ... rest of middleware ...
]
```

### URL Configuration

Add hijack URLs — must be inside B2B_START/B2B_END markers. No other URL changes needed (admin URL path unchanged):

```python
# config/urls.py — inside B2B_START/B2B_END block
# B2B_START
path("hijack/", include("hijack.urls")),
# B2B_END
```

### UNFOLD Settings Dict Structure

The `UNFOLD = {...}` dict goes in `config/settings/base.py` following the same pattern as `SIMPLE_JWT`, `CELERY_*`, etc. The **B2B section items** inside `SIDEBAR.navigation` are wrapped in B2B_START/B2B_END markers. The UNFOLD dict itself is NOT wrapped (it's needed for the non-B2B theme too):

```python
# config/settings/base.py
from django.templatetags.static import static
from django.urls import reverse_lazy

UNFOLD = {
    "SITE_TITLE": "Foundation Admin",
    "SITE_HEADER": "Foundation",
    "SIDEBAR": {
        "show_search": False,
        "show_all_applications": False,
        "navigation": [
            # B2B_START
            {
                "title": "B2B",
                "separator": False,
                "collapsible": False,
                "items": [
                    {
                        "title": "Organizations",
                        "icon": "business",
                        "link": reverse_lazy("admin:orgs_organization_changelist"),
                    },
                    {
                        "title": "Memberships",
                        "icon": "people",
                        "link": reverse_lazy("admin:orgs_membership_changelist"),
                    },
                    {
                        "title": "API Keys",
                        "icon": "vpn_key",
                        "link": reverse_lazy("admin:api_keys_apikey_changelist"),
                    },
                    {
                        "title": "Webhooks",
                        "icon": "webhook",
                        "link": reverse_lazy("admin:webhooks_webhookendpoint_changelist"),
                    },
                    {
                        "title": "Audit Log",
                        "icon": "history",
                        "link": reverse_lazy("admin:audit_auditlogevent_changelist"),
                    },
                ],
            },
            # B2B_END
            {
                "title": "Users & Auth",
                "separator": True,
                "collapsible": False,
                "items": [
                    {
                        "title": "Users",
                        "icon": "manage_accounts",
                        "link": reverse_lazy("admin:accounts_user_changelist"),
                    },
                ],
            },
            {
                "title": "Billing",
                "separator": True,
                "collapsible": False,
                "items": [
                    {
                        "title": "Customers",
                        "icon": "credit_card",
                        "link": reverse_lazy("admin:billing_customer_changelist"),
                    },
                    # ... Subscriptions, Payments, PlanProviderMapping, ProcessedWebhookEvent
                ],
            },
            {
                "title": "System",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Periodic Tasks",
                        "icon": "schedule",
                        "link": reverse_lazy("admin:django_celery_beat_periodictask_changelist"),
                    },
                    {
                        "title": "Task Results",
                        "icon": "task_alt",
                        "link": reverse_lazy("admin:django_celery_results_taskresult_changelist"),
                    },
                ],
            },
        ],
    },
}
```

**Note on `reverse_lazy`:** The UNFOLD dict is evaluated at module import time (settings load). `reverse_lazy` is required — `reverse()` would fail at settings load before URLs are configured.

### UnfoldModelAdmin Conversion Pattern

All admin classes must inherit from `unfold.admin.ModelAdmin` (not `django.contrib.admin.ModelAdmin`). For UserAdmin specifically, Unfold provides custom forms that must be used:

```python
# apps/accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm
from hijack.contrib.admin import HijackUserAdminMixin

from .models import User


@admin.register(User)
class UserAdmin(HijackUserAdminMixin, BaseUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    # ... existing list_display, etc.
```

MRO order matters: `HijackUserAdminMixin` must come before `BaseUserAdmin` which must come before `ModelAdmin`.

For all other domain admins:

```python
# e.g., apps/orgs/admin.py
from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Organization, Membership


@admin.register(Organization)
class OrganizationAdmin(ModelAdmin):
    list_display = ("name", "slug", "owner", "created_at")
    list_filter = ("created_at",)
    search_fields = ("name", "slug", "owner__email")
```

### django-hijack Permission Design

The built-in `hijack.permissions.superusers_and_staff` allows staff to hijack any user **including other staff** (but not superusers). This is too permissive. A custom permission function is needed:

```python
# apps/accounts/permissions.py (or inline in admin.py as a module-level function)
def staff_can_hijack_regular_users(*, hijacker, hijacked) -> bool:
    """Only staff/superusers may hijack; only non-staff, non-superuser accounts may be hijacked."""
    if not hijacked.is_active:
        return False
    if not (hijacker.is_staff or hijacker.is_superuser):
        return False
    if hijacked.is_staff or hijacked.is_superuser:
        return False
    return True
```

```python
# config/settings/base.py (inside B2B_START/B2B_END)
# B2B_START
HIJACK_PERMISSION_CHECK = "apps.accounts.permissions.staff_can_hijack_regular_users"
HIJACK_LOGOUT_REDIRECT_URL = "/admin/accounts/user/"  # returns to user list; see Note below
# B2B_END
```

**Note on HIJACK_LOGOUT_REDIRECT_URL:** The CONTEXT.md requests redirect to the specific user's change page (`/admin/accounts/user/{id}/change/`). `HIJACK_LOGOUT_REDIRECT_URL` accepts a static string — it cannot be a callable or template variable natively. The simplest approach is redirect to `/admin/accounts/user/` (the user list), which is natural for support workflows. Redirecting back to the specific change page requires either a signal handler that stores the user_id in the session before hijack starts, or a custom view wrapping the hijack release. Research did not confirm HIJACK_LOGOUT_REDIRECT_URL accepts a callable in 3.7.6 — treat as LOW confidence item needing verification.

### Audit Log: Impersonator in Context

The pghistory audit system stores per-request context as a JSON dict in `pghistory_context.metadata`. Phase 30 must:

1. **Extend `AuditContextMiddleware`** to inject the `impersonator` user ID when a hijack session is active:

```python
# apps/audit/middleware.py — extend get_context()
class AuditContextMiddleware(pghistory.middleware.HistoryMiddleware):
    def get_context(self, request):
        ctx = super().get_context(request)
        org = getattr(request, "org", None)
        if org is not None:
            ctx["org_id"] = str(org.id)
        # B2B_START — impersonator context for hijack sessions
        hijack_history = getattr(request, "hijack_history", None)
        if hijack_history:
            # hijack_history is a list of user PKs — first entry is the original hijacker
            ctx["impersonator_id"] = hijack_history[0]
        # B2B_END
        return ctx
```

2. **Wire hijack signals** to write explicit AuditLog entries for start/end events (since those events don't go through ORM model tracking — they're session operations, not model mutations):

```python
# apps/audit/signals.py (new file, B2B_START/B2B_END wrapped)
from hijack import signals as hijack_signals
import pghistory

def _on_hijack_started(sender, hijacker, hijacked, request, **kwargs):
    with pghistory.context(
        user=hijacker.pk,
        impersonator_id=hijacker.pk,
        org_id=None,
    ):
        # write a synthetic event — use a custom pghistory event or a direct Context log
        pass

hijack_signals.hijack_started.connect(_on_hijack_started)
hijack_signals.hijack_ended.connect(_on_hijack_ended)
```

**IMPORTANT DISCOVERY:** pghistory tracks ORM model mutations only. Hijack start/end are NOT model mutations — they are session operations. This means the hijack signals cannot automatically produce pghistory event rows in the normal tracked-model tables. Options:

**Option A (Recommended):** Create a dedicated `ImpersonationEvent` model using `pghistory.CreateEvent` or a plain Django model. Write one row per hijack_started and hijack_ended signal. Register it in `admin.py` as the "Audit Log" changelist item.

**Option B:** Rely solely on the `impersonator_id` in the pghistory context for subsequent ORM mutations during the session (which is what Phase 29's success criteria actually requires — "impersonation entries" means any org-level event where impersonator_id is present). The CONTEXT.md audit log columns reference `impersonator_email`, which can be derived from `impersonator_id` in the context JSON.

**Resolution:** The CONTEXT.md states "Every impersonation start and end event writes an AuditLog entry with the `impersonator` FK populated." This means explicit start/end records are required. Option A is needed. The planner must define a lightweight `ImpersonationEvent` Django model (not pghistory-tracked, just a regular model) with fields: `timestamp`, `action` (choices: start/end), `hijacker` FK, `hijacked` FK, `created_at`. This model is the admin "Audit Log" changelist. The `impersonator_email` column in the admin comes from `hijacker.email`.

### Audit Log Admin View

Since the "Audit Log" in admin shows impersonation events (not pghistory events), register `ImpersonationEvent` in `apps/audit/admin.py`:

```python
# apps/audit/admin.py  — B2B_START/B2B_END wrapped
from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import ImpersonationEvent


class HasImpersonatorFilter(admin.SimpleListFilter):
    title = "Has Impersonator"
    parameter_name = "has_impersonator"

    def lookups(self, request, model_admin):
        return [("yes", "Yes"), ("no", "No")]

    def queryset(self, qs, value):  # Note: actual signature is queryset(self, request, qs)
        if value == "yes":
            return qs.filter(hijacker__isnull=False)
        if value == "no":
            return qs.filter(hijacker__isnull=True)
        return qs


@admin.register(ImpersonationEvent)
class ImpersonationEventAdmin(ModelAdmin):
    list_display = ("timestamp", "action", "hijacker_email", "hijacked_email")
    list_filter = ("action", HasImpersonatorFilter)
    search_fields = ("hijacker__email", "hijacked__email")
    readonly_fields = ("timestamp", "action", "hijacker", "hijacked")

    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False

    @admin.display(description="Hijacker Email")
    def hijacker_email(self, obj):
        return obj.hijacker.email if obj.hijacker else "—"

    @admin.display(description="Hijacked Email")
    def hijacked_email(self, obj):
        return obj.hijacked.email if obj.hijacked else "—"
```

---

## Don't Hand-Roll

| Problem                            | Don't Build                   | Use Instead                                            | Why                                                                              |
| ---------------------------------- | ----------------------------- | ------------------------------------------------------ | -------------------------------------------------------------------------------- |
| Admin theme                        | Custom CSS/template overrides | django-unfold                                          | Maintains upgrade path; handles admin form styling, dark mode, responsive layout |
| Impersonation session handling     | Custom session manipulation   | django-hijack middleware                               | Session state, CSRF, secure release flow are handled by the library              |
| Permission check for impersonation | Complex inline conditionals   | Custom function registered via HIJACK_PERMISSION_CHECK | Single clean function, testable in isolation                                     |
| Admin banner injection             | Custom template tag           | HIJACK_INSERT_BEFORE (hijack default)                  | Library handles DOM injection safely                                             |

---

## Common Pitfalls

### Pitfall 1: INSTALLED_APPS Order for Unfold

**What goes wrong:** `unfold` added after `django.contrib.admin` causes template override failures — admin pages render without Unfold styling.
**Why it happens:** Django's template engine uses first-match wins; `unfold` must override Django's admin templates.
**How to avoid:** Always place `"unfold"` as the very first item before `"django.contrib.admin"` in INSTALLED_APPS.
**Warning signs:** Admin pages load but look like plain Django admin after Unfold installation.

### Pitfall 2: Heroicons vs Material Symbols

**What goes wrong:** Using Heroicon names (e.g., `"user-group"`) in the `"icon"` field of UNFOLD navigation items produces broken/missing icons.
**Why it happens:** django-unfold ships with Material Symbols (Google), not Heroicons. The CONTEXT.md discussion incorrectly identified the icon library.
**How to avoid:** Use Material Symbols names (e.g., `"people"`, `"business"`, `"vpn_key"`, `"history"`, `"webhook"`). Reference: [Material Symbols](https://fonts.google.com/icons).
**Warning signs:** Navigation shows empty boxes where icons should appear.

### Pitfall 3: UserAdmin UnfoldModelAdmin Requires Unfold Forms

**What goes wrong:** Extending `UserAdmin` with `UnfoldModelAdmin` but not replacing the forms causes form styling to break — password change fields, user creation fields appear unstyled.
**Why it happens:** Unfold provides replacement forms with its styling applied; the base `UserAdmin` uses Django's default forms which are incompatible.
**How to avoid:** Always set `form = UserChangeForm`, `add_form = UserCreationForm`, `change_password_form = AdminPasswordChangeForm` from `unfold.forms` on any UserAdmin subclass.
**Warning signs:** Password change form or user creation form lacks Unfold styling.

### Pitfall 4: reverse_lazy Required in UNFOLD Dict

**What goes wrong:** Using `reverse()` (not `reverse_lazy()`) in the UNFOLD sidebar `"link"` fields raises `NoReverseMatch` or `django.core.exceptions.ImproperlyConfigured` at Django startup.
**Why it happens:** `UNFOLD = {...}` is evaluated at settings module import time, before URLs are registered.
**How to avoid:** Always use `reverse_lazy()` (from `django.urls`) for all link values in the UNFOLD dict.
**Warning signs:** Django fails to start with URL-related errors.

### Pitfall 5: HijackUserMiddleware Placement

**What goes wrong:** `HijackUserMiddleware` placed before `AuthenticationMiddleware` raises `AttributeError` because `request.user` is not yet populated.
**Why it happens:** Hijack middleware reads `request.user` to manage hijack sessions.
**How to avoid:** Always place `hijack.middleware.HijackUserMiddleware` after `django.contrib.auth.middleware.AuthenticationMiddleware`.
**Warning signs:** `AttributeError: 'WSGIRequest' object has no attribute 'user'` in hijack middleware.

### Pitfall 6: Impersonation Events are Not pghistory Events

**What goes wrong:** Assuming hijack signals produce pghistory event table rows automatically.
**Why it happens:** pghistory tracks Django ORM model mutations via PostgreSQL triggers. Session-level hijack operations do not touch tracked model tables.
**How to avoid:** Create a dedicated `ImpersonationEvent` Django model; connect hijack signals to write rows to this model.
**Warning signs:** Audit log admin shows no impersonation start/end records after testing.

### Pitfall 7: CSP Blocking Unfold Admin Assets

**What goes wrong:** Unfold injects inline styles/scripts for the admin theme, which the existing CSP (`style-src: 'self' NONCE`, `script-src: 'self' NONCE`) may block.
**Why it happens:** The admin is served from the same Django app with the existing CSP. Unfold relies on some inline styling that needs nonce or unsafe-inline.
**How to avoid:** The existing CSP uses `NONCE` sentinel for both `style-src` and `script-src`. Verify Unfold's templates use `request.csp_nonce`. If not, consider adding `unsafe-inline` scoped to admin paths or disabling CSP middleware for `/admin/` prefix via a conditional.
**Warning signs:** Admin pages load with broken styling; browser console shows CSP violations.

### Pitfall 8: B2B_START/B2B_END Markers

**What goes wrong:** New hijack/unfold B2B config items added outside the markers — CLI scaffolder (Phase 31) fails to cleanly remove B2B code.
**How to avoid:** All of the following must be inside B2B_START/B2B_END:

- `"hijack"` and `"hijack.contrib.admin"` in INSTALLED_APPS
- `HijackUserMiddleware` in MIDDLEWARE
- `hijack.urls` in urlpatterns
- `HIJACK_PERMISSION_CHECK` and `HIJACK_LOGOUT_REDIRECT_URL` settings
- The B2B section of the UNFOLD SIDEBAR navigation
- All `apps/orgs/admin.py`, `apps/api_keys/admin.py`, `apps/webhooks/admin.py`, `apps/audit/admin.py` files (entire files — use file-level markers in a README note)

---

## Code Examples

### Sidebar Navigation Item with Material Symbol

```python
# Source: https://unfoldadmin.com/docs/configuration/settings/
{
    "title": "Organizations",
    "icon": "business",          # Material Symbols name
    "link": reverse_lazy("admin:orgs_organization_changelist"),
}
```

### Custom HIJACK_PERMISSION_CHECK Function

```python
# Source: https://django-hijack.readthedocs.io/en/latest/customization/
# apps/accounts/permissions.py
def staff_can_hijack_regular_users(*, hijacker, hijacked) -> bool:
    """Staff can impersonate only non-staff, non-superuser, active accounts."""
    if not hijacked.is_active:
        return False
    if not (hijacker.is_staff or hijacker.is_superuser):
        return False
    if hijacked.is_staff or hijacked.is_superuser:
        return False
    return True
```

### Hijack Signals Connection

```python
# Source: https://django-hijack.readthedocs.io/en/latest/customization/
# Signal parameters: sender, hijacker, hijacked, request, **kwargs
from hijack import signals as hijack_signals

def on_hijack_started(sender, hijacker, hijacked, request, **kwargs):
    ImpersonationEvent.objects.create(
        action="start",
        hijacker=hijacker,
        hijacked=hijacked,
    )

def on_hijack_ended(sender, hijacker, hijacked, request, **kwargs):
    ImpersonationEvent.objects.create(
        action="end",
        hijacker=hijacker,
        hijacked=hijacked,
    )

hijack_signals.hijack_started.connect(on_hijack_started)
hijack_signals.hijack_ended.connect(on_hijack_ended)
```

Connect signals in `apps/audit/apps.py` `ready()` method (standard Django signal connection pattern).

### HasImpersonatorFilter (correct SimpleListFilter signature)

```python
class HasImpersonatorFilter(admin.SimpleListFilter):
    title = "Has Impersonator"
    parameter_name = "has_impersonator"

    def lookups(self, request, model_admin):
        return [("yes", "Yes"), ("no", "No")]

    def queryset(self, request, queryset):  # request is required parameter
        if self.value() == "yes":
            return queryset.filter(hijacker__isnull=False)
        if self.value() == "no":
            return queryset.filter(hijacker__isnull=True)
        return queryset
```

### UserAdmin with Hijack + Unfold

```python
# Source: https://unfoldadmin.com/docs/installation/auth/
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm
from hijack.contrib.admin import HijackUserAdminMixin
from .models import User

@admin.register(User)
class UserAdmin(HijackUserAdminMixin, BaseUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
```

---

## State of the Art

| Old Approach                        | Current Approach                                 | When Changed                                | Impact                                                                          |
| ----------------------------------- | ------------------------------------------------ | ------------------------------------------- | ------------------------------------------------------------------------------- |
| django-jazzmin / django-grappelli   | django-unfold                                    | April 2025 (official Django recommendation) | Unfold is now the canonical modern admin theme                                  |
| django-hijack v2 (POST button only) | django-hijack v3 (security-first, admin contrib) | v3.0 release                                | Complete API rewrite; django-hijack-admin merged into contrib; dark mode native |
| Audit via Django signals            | Audit via pghistory PostgreSQL triggers          | pghistory adoption                          | Triggers capture bulk ORM + raw SQL that signals miss                           |

---

## Open Questions

1. **HIJACK_LOGOUT_REDIRECT_URL: callable vs static string?**
   - What we know: Accepts a static string. Context says redirect to specific user change page.
   - What's unclear: Whether 3.7.6 accepts a callable. Signal-based session storage approach needs investigation.
   - Recommendation: Default to `/admin/accounts/user/` (user list). Verify callable support at plan time by reading hijack source. If not supported natively, implement via `hijack_ended` signal + session redirect.

2. **CSP compatibility with Unfold admin assets**
   - What we know: Current CSP uses NONCE sentinel for scripts and styles. Unfold injects custom assets.
   - What's unclear: Whether Unfold's templates use Django's `request.csp_nonce` or rely on `unsafe-inline`.
   - Recommendation: Test in Wave 1 smoke test. If CSP blocks admin assets, exempt `/admin/` from CSP middleware using a path-based condition in `CONTENT_SECURITY_POLICY` or add admin to middleware exclusion list.

3. **ImpersonationEvent model vs pghistory Context approach**
   - What we know: pghistory tracks model mutations only — hijack start/end are session operations.
   - What's unclear: Whether the success criteria ("writes an AuditLog entry with the `impersonator` FK populated") means a standalone model or enriched pghistory context.
   - Recommendation: Create standalone `ImpersonationEvent` model. It satisfies the literal requirement ("entry with impersonator FK") cleanly without bending pghistory's design.

4. **Django version: 5.1 vs hijack 3.7.6 compatibility**
   - What we know: `pyproject.toml` has `django>=5.1,<6.0`. Hijack 3.7.6 lists Django 4.2/5.2/6.0 as tested.
   - What's unclear: Whether Django 5.1 (not 5.2) works with hijack 3.7.6 in practice. The STATE.md flagged this.
   - Recommendation: Django 5.1 is close enough to 5.2 that hijack 3.7.6 should work. Verify by installing and running the hijack test suite's imports. A Django 5.2 upgrade is NOT a prerequisite — only escalate if actual test failures emerge.

---

## Validation Architecture

### Test Framework

| Property           | Value                                                 |
| ------------------ | ----------------------------------------------------- |
| Framework          | pytest + pytest-django                                |
| Config file        | `apps/api/pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command  | `cd apps/api && python -m pytest tests/audit/ -x -q`  |
| Full suite command | `cd apps/api && python -m pytest -x -q`               |

### Phase Requirements → Test Map

| Req ID   | Behavior                                                                    | Test Type   | Automated Command                                                                                      | File Exists?         |
| -------- | --------------------------------------------------------------------------- | ----------- | ------------------------------------------------------------------------------------------------------ | -------------------- |
| ADMIN-01 | Unfold theme renders — all ModelAdmin subclasses inherit UnfoldModelAdmin   | smoke       | `cd apps/api && python -m pytest tests/admin/test_admin_smoke.py -x -q`                                | ❌ Wave 0            |
| ADMIN-01 | Sidebar navigation sections configured in UNFOLD settings                   | unit        | `cd apps/api && python -m pytest tests/admin/test_unfold_config.py -x -q`                              | ❌ Wave 0            |
| ADMIN-02 | Staff can impersonate non-staff user — session changes                      | integration | `cd apps/api && python -m pytest tests/admin/test_hijack.py::test_staff_can_hijack_regular_user -x -q` | ❌ Wave 0            |
| ADMIN-02 | Staff cannot impersonate staff user — 403                                   | integration | `cd apps/api && python -m pytest tests/admin/test_hijack.py::test_cannot_hijack_staff -x -q`           | ❌ Wave 0            |
| ADMIN-02 | Staff cannot impersonate superuser — 403                                    | integration | `cd apps/api && python -m pytest tests/admin/test_hijack.py::test_cannot_hijack_superuser -x -q`       | ❌ Wave 0            |
| ADMIN-02 | hijack_started signal writes ImpersonationEvent start row                   | unit        | `cd apps/api && python -m pytest tests/admin/test_hijack.py::test_signal_start_writes_event -x -q`     | ❌ Wave 0            |
| ADMIN-02 | hijack_ended signal writes ImpersonationEvent end row                       | unit        | `cd apps/api && python -m pytest tests/admin/test_hijack.py::test_signal_end_writes_event -x -q`       | ❌ Wave 0            |
| ADMIN-02 | AuditContextMiddleware injects impersonator_id during hijack session        | unit        | `cd apps/api && python -m pytest tests/audit/test_middleware.py::test_impersonator_context -x -q`      | ❌ Wave 0            |
| ADMIN-02 | Audit log admin excludes impersonation entries from org-level audit queries | integration | existing `tests/audit/test_controllers.py`                                                             | ✅ (verify coverage) |

### Sampling Rate

- **Per task commit:** `cd apps/api && python -m pytest tests/admin/ -x -q`
- **Per wave merge:** `cd apps/api && python -m pytest -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/admin/__init__.py` — create directory
- [ ] `tests/admin/conftest.py` — staff_user, regular_user, superuser fixtures
- [ ] `tests/admin/test_admin_smoke.py` — ADMIN-01 ModelAdmin class inheritance checks
- [ ] `tests/admin/test_unfold_config.py` — ADMIN-01 UNFOLD settings structure validation
- [ ] `tests/admin/test_hijack.py` — ADMIN-02 permission + signal tests

---

## Sources

### Primary (HIGH confidence)

- django-unfold PyPI — version 0.84.0 confirmed
- https://unfoldadmin.com/docs/installation/ — INSTALLED_APPS order, UnfoldModelAdmin requirement
- https://unfoldadmin.com/docs/installation/auth/ — UserAdmin + Unfold forms pattern
- https://unfoldadmin.com/docs/configuration/settings/ — SIDEBAR navigation structure, icon system (Material Symbols confirmed)
- https://django-hijack.readthedocs.io/en/stable/ — middleware, admin contrib, HijackUserAdminMixin
- https://django-hijack.readthedocs.io/en/latest/customization/ — HIJACK_PERMISSION_CHECK, signals
- django-hijack PyPI — version 3.7.6, Django 4.2/5.2/6.0 support confirmed

### Secondary (MEDIUM confidence)

- https://dokk.org/documentation/django-hijack/3.4.5/customization/ — signal parameter confirmation (sender, hijacker, hijacked, request, \*\*kwargs)
- GitHub issues #1174 and #761 on django-unfold — confirms Material Symbols (not Heroicons) as icon library

### Tertiary (LOW confidence)

- HIJACK_LOGOUT_REDIRECT_URL callable support — not confirmed in docs; treat as needs-verification at plan time

---

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — versions confirmed from PyPI; Django compatibility verified from release metadata
- Architecture: HIGH — INSTALLED_APPS order, middleware placement, URL config from official docs
- Icon library (CORRECTION): HIGH — confirmed Material Symbols from multiple sources including GitHub issues
- Pitfalls: HIGH for items 1-5 (documentation-sourced); MEDIUM for CSP (needs smoke test)
- Impersonation event model: MEDIUM — recommended approach based on pghistory design understanding; planner should validate

**Research date:** 2026-03-13
**Valid until:** 2026-06-13 (stable libraries; 90 days reasonable)
