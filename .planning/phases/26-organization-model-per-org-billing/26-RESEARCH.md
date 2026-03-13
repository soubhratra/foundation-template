# Phase 26: Organization Model + Per-Org Billing - Research

**Researched:** 2026-03-12
**Domain:** Django multi-tenancy (organizations, membership, invitations), Django Ninja Extra permissions, per-org Stripe billing entitlements
**Confidence:** HIGH — all findings grounded in existing codebase patterns that are directly reused

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions

**Module structure:**

- All org code lives in `apps/api/apps/orgs/` with files: `models.py`, `schemas.py`, `controllers.py`, `services.py`, `permissions.py`, `migrations/`
- B2B_START/B2B_END markers isolate `apps/orgs/` for `--with b2b` scaffolder flag

**OrgCustomer model:**

- Separate model in `apps/orgs/` with `OneToOne` to `Organization` and its own `stripe_customer_id`
- Mirrors existing `Customer(user=OneToOne)` shape exactly — parallel structure
- `billing/` references `OrgCustomer` via FK only; no circular imports
- Do NOT add an org FK to the existing `Customer` model

**Invitation flow:**

- URL token in email — link format `/accept-invite?token=xxx`
- Token sent via existing `send_email()` from `apps.notifications.utils`
- Token stored in `Invitation` model with 72-hour expiry
- Token bound to invited email — validated on accept
- Existing user with matching email: invite accepted immediately on link click, redirect to org dashboard
- New user: token stored in session before redirect to signup; consumed after signup completes
- Email mismatch: HTTP 400 `{"detail": "This invitation was sent to a different email address."}`
- Default role on accept: member always

**Org permission class design:**

- `IsOrgAdmin` and `IsOrgMember` are Ninja Extra `BasePermission` classes
- Org resolution: extract `org_slug` from `request.resolver_match.kwargs` (endpoints at `/api/v1/org/{org_slug}/...`)
- After resolving, set `request.org = organization` — available to all downstream controllers
- User not a member → **404** (avoids leaking org existence)
- User is a member but lacks required role → **403**
- Compose as: `permissions=[IsAuthenticated, IsOrgMember]` or `permissions=[IsAuthenticated, IsOrgAdmin]`

**`has_org_feature()` API shape:**

- Signature: `has_org_feature(user, org, key: str) -> bool`
- Checks org subscription first; falls back to `has_feature(user, key)` if no active org subscription
- Returns `True` if billing is not installed
- Location: `apps/core/entitlements.py` — same file as `has_feature()`
- Org plan resolution: separate `_resolve_org_plan_id(org)` function in `apps/orgs/`; called first; falls back to `_resolve_plan_id(user)` from `billing/`

**Entitlement cache design:**

- Cache key: `entitlements:org:{org_pk}:{user_pk}` — per-membership key
- Cache TTL: 300 seconds (consistent with personal entitlement TTL)
- Invalidation: iterate `Membership.objects.filter(org=org)` and delete each member's org cache key
- Triggered in same `_handle_subscription_updated` webhook handler path (extended for `OrgCustomer.stripe_customer_id`)

### Claude's Discretion

- Exact slug uniqueness validation (globally unique vs case-insensitive unique)
- Invitation resend logic (whether resending re-uses same token or issues new one)
- Pagination style for member listings (follow existing pagination patterns in codebase)
- Whether `OrgController` and `MembershipController` are separate classes or one controller
- Exact ownership transfer: whether previous owner's role becomes admin or member

### Deferred Ideas (OUT OF SCOPE)

- Per-org SSO enforcement (requires SSO infrastructure)
- Sub-organizations / org hierarchy (ORG-F02)
- Custom roles beyond owner/admin/member (ORG-F01)
- Org-level audit log (Phase 29)
- Org admin backoffice views (Phase 30)
  </user_constraints>

<phase_requirements>

## Phase Requirements

| ID      | Description                                                                                                                                                              | Research Support                                                                                           |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------- |
| ORG-01  | User can create an organization with a name and slug; becomes owner automatically                                                                                        | Organization model with slug field + OrgService.create_org(); mirrors accounts/ app pattern                |
| ORG-02  | Org owner can invite members by email (72h token expiry); accepted via new signup or existing login using existing EmailAdapter                                          | Invitation model + send_email() from notifications + session-stored pending token for new signup flow      |
| ORG-03  | Org members have owner/admin/member roles; `IsOrgAdmin`/`IsOrgMember` Ninja permission classes enforce access                                                            | BasePermission pattern from accounts/permissions.py RequireRole — direct template                          |
| ORG-04  | Org owner can transfer ownership to another member via dedicated endpoint                                                                                                | Membership role field update in single DB transaction — documented below                                   |
| ORG-05  | All service methods validate org membership before any ORM access; cross-org resource access returns 403                                                                 | IsOrgMember sets request.org; services receive org from controller — boundary enforced at permission layer |
| BILL-01 | System creates OrgCustomer linked to Organization for per-org Stripe billing, parallel to existing user Customer model                                                   | Customer model in billing/models.py is exact structural template; OrgCustomer goes in orgs/                |
| BILL-02 | `_resolve_plan_id` checks org plan before personal plan; entitlement cache invalidated for all org members on subscription update; `has_org_feature()` utility available | billing/entitlements.py pattern + billing/tasks.py \_handle_subscription_updated extension                 |

</phase_requirements>

---

## Summary

Phase 26 builds the B2B foundation: an `apps/orgs/` Django app containing Organization, Membership, Invitation, and OrgCustomer models along with their service, controller, and permission layers. All decisions are locked. No library research is needed for the org model itself (custom as decided) — the work is implementation against known patterns in the existing codebase.

The codebase already contains every template needed. `RequireRole` in `accounts/permissions.py` is a direct copy-paste-adapt for `IsOrgAdmin`/`IsOrgMember`. The `Customer`/`Subscription` pair in `billing/models.py` is the structural template for `OrgCustomer`. The `_has_feature()` pattern in `billing/entitlements.py` is the template for `has_org_feature()`. The `_handle_subscription_updated` function in `billing/tasks.py` is extended (not replaced) to also detect `OrgCustomer` lookups.

The one non-trivial implementation area is the invitation flow: the "token survives signup" path requires storing a pending invite token in the Django session before redirecting to the signup page, then consuming it in a post-signup signal or in the invitation-accept endpoint after signup completes. This is the only novel pattern without an existing codebase template.

**Primary recommendation:** Implement in three sequential waves — (1) models + migrations, (2) permission classes + service + controllers, (3) entitlement extension. Keep `_handle_subscription_updated` extension as the final step to avoid any intermediate state where org models exist but org billing is incomplete (per STATE.md correctness decision).

---

## Standard Stack

### Core — No New Dependencies Required

All implementation uses libraries already installed in `apps/api/pyproject.toml`.

| Library            | Current Version | Purpose                                                       | Status            |
| ------------------ | --------------- | ------------------------------------------------------------- | ----------------- |
| Django             | >=5.1,<6.0      | ORM, migrations, session storage                              | Already installed |
| django-ninja-extra | >=0.21          | `BasePermission`, `api_controller`, `route`, `ControllerBase` | Already installed |
| celery[redis]      | >=5.6.2         | Async webhook event processing                                | Already installed |
| django-redis       | 6.0.0           | Cache backend for entitlement caching                         | Already installed |
| stripe             | >=14.4,<15      | Per-org Stripe customer management                            | Already installed |

**No new packages to install.** Phase 26 is pure implementation against the existing stack.

### Supporting Patterns Already in Codebase

| Pattern                                                     | Location                                                    | Reuse                                                    |
| ----------------------------------------------------------- | ----------------------------------------------------------- | -------------------------------------------------------- |
| `BasePermission` subclass                                   | `apps/accounts/permissions.py:RequireRole`                  | Template for `IsOrgAdmin`, `IsOrgMember`                 |
| `has_feature()` / `_has_feature()`                          | `apps/core/entitlements.py`, `apps/billing/entitlements.py` | Template for `has_org_feature()`                         |
| `Customer` + `Subscription` models                          | `apps/billing/models.py`                                    | Structural template for `OrgCustomer`                    |
| `_handle_subscription_updated`                              | `apps/billing/tasks.py`                                     | Extended (not replaced) for org billing                  |
| `send_email()` via `transaction.on_commit`                  | `apps/notifications/utils.py`                               | Used for invitation email dispatch                       |
| `ServiceError`, `NotFoundError`, `PermissionDeniedError`    | `apps/core/exceptions.py`                                   | Used in OrgService, MembershipService, InvitationService |
| `process_stripe_event` Celery task + `_TIER1_HANDLERS` dict | `apps/billing/tasks.py`                                     | Extended to detect OrgCustomer in updated handler        |

---

## Architecture Patterns

### Recommended Project Structure

```
apps/api/apps/orgs/
├── __init__.py
├── apps.py
├── models.py          # Organization, Membership, Invitation, OrgCustomer
├── schemas.py         # Request/response schemas for all org endpoints
├── controllers.py     # OrgController, MembershipController, InvitationController
├── services.py        # OrgService, MembershipService, InvitationService
├── permissions.py     # IsOrgAdmin, IsOrgMember
└── migrations/
    ├── __init__.py
    └── 0001_initial.py

apps/api/apps/notifications/templates/email/
└── org_invitation.html    # New: invitation email template

apps/api/tests/orgs/
├── __init__.py
├── conftest.py
├── test_models.py
├── test_services.py
├── test_controllers.py
└── test_permissions.py
```

### Pattern 1: IsOrgMember Permission Class

**What:** Resolves `org_slug` from URL kwargs, fetches `Membership`, sets `request.org`, and controls 404 vs 403 response codes.

**When to use:** All endpoints under `/api/v1/org/{org_slug}/` that require any org membership.

```python
# Source: adapted from apps/accounts/permissions.py RequireRole
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpRequest
from ninja_extra import ControllerBase
from ninja_extra.permissions import BasePermission

from apps.orgs.models import Membership, Organization


class IsOrgMember(BasePermission):
    """Gate: user must be a member of the org identified by {org_slug} in the URL.

    On success: sets request.org = organization.
    User not a member → Http404 (avoids leaking org existence).
    """

    def has_permission(self, request: HttpRequest, controller: ControllerBase) -> bool:
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False

        org_slug = request.resolver_match.kwargs.get("org_slug", "")
        try:
            org = Organization.objects.get(slug=org_slug)
        except Organization.DoesNotExist:
            raise Http404

        membership = Membership.objects.filter(org=org, user=user).first()
        if membership is None:
            # Return 404 — org doesn't exist from unauthenticated member's perspective.
            raise Http404

        request.org = org
        return True


class IsOrgAdmin(BasePermission):
    """Gate: user must be owner or admin in the org.

    Must be composed AFTER IsOrgMember so request.org is already set.
    """

    def has_permission(self, request: HttpRequest, controller: ControllerBase) -> bool:
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False

        org = getattr(request, "org", None)
        if org is None:
            return False  # IsOrgMember not in chain — programming error

        membership = Membership.objects.filter(
            org=org, user=user, role__in=["owner", "admin"]
        ).first()
        if membership is None:
            raise PermissionDenied
        return True
```

### Pattern 2: Organization + Membership Models

**What:** Core models for org identity, team membership, and invitation management.

```python
# Source: codebase analysis of apps/billing/models.py + accounts/models.py
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Organization(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "orgs_organization"

    def __str__(self) -> str:
        return f"Organization({self.slug})"


class Membership(models.Model):
    class Role(models.TextChoices):
        OWNER = "owner", _("Owner")
        ADMIN = "admin", _("Admin")
        MEMBER = "member", _("Member")

    org = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="org_memberships"
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "orgs_membership"
        unique_together = [("org", "user")]

    def __str__(self) -> str:
        return f"Membership({self.user.email} → {self.org.slug} as {self.role})"


INVITATION_EXPIRY_HOURS = 72


class Invitation(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        ACCEPTED = "accepted", _("Accepted")
        EXPIRED = "expired", _("Expired")
        REVOKED = "revoked", _("Revoked")

    org = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="invitations")
    invited_email = models.EmailField()
    token = models.CharField(max_length=64, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sent_invitations",
    )
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "orgs_invitation"
        indexes = [
            models.Index(fields=["token"]),
            models.Index(fields=["invited_email", "status"]),
        ]

    def is_valid(self) -> bool:
        return self.status == self.Status.PENDING and self.expires_at > timezone.now()

    @staticmethod
    def generate_token() -> str:
        return secrets.token_urlsafe(48)

    @staticmethod
    def make_expiry() -> "datetime":
        return timezone.now() + timedelta(hours=INVITATION_EXPIRY_HOURS)


class OrgCustomer(models.Model):
    """Per-org Stripe customer record. Mirrors apps/billing/models.py Customer exactly."""

    org = models.OneToOneField(
        Organization, on_delete=models.CASCADE, related_name="billing_customer"
    )
    stripe_customer_id = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "orgs_orgcustomer"

    def __str__(self) -> str:
        return f"OrgCustomer({self.org.slug})"
```

### Pattern 3: has_org_feature() in apps/core/entitlements.py

**What:** Adds org-scoped entitlement check to the existing `has_feature()` public API file.

```python
# Source: Extension of apps/core/entitlements.py pattern
def has_org_feature(user, org, key: str) -> bool:
    """Return True if org's plan (or user's personal plan) includes the named feature.

    Checks org subscription first. Falls back to user's personal plan if no active
    org subscription exists. Returns True when billing module is not installed.

    Args:
        user: Django user instance (needed for personal plan fallback).
        org: Organization instance.
        key: Feature flag key (e.g. "advanced_analytics").
    """
    try:
        from apps.orgs.services import _resolve_org_plan_id
        from apps.billing.entitlements import _flags_for_plan
        from django.core.cache import cache

        cache_key = f"entitlements:org:{org.pk}:{user.pk}"
        cached = cache.get(cache_key)

        if cached is None:
            org_plan_id = _resolve_org_plan_id(org)
            if org_plan_id is not None:
                cached = _flags_for_plan(org_plan_id)
            else:
                # No active org subscription — fall back to personal plan
                from apps.billing.entitlements import _resolve_plan_id
                personal_plan_id = _resolve_plan_id(user)
                cached = _flags_for_plan(personal_plan_id)

            from django.conf import settings
            ENTITLEMENT_CACHE_TTL = getattr(settings, "ENTITLEMENT_CACHE_TTL", 300)
            cache.set(cache_key, cached, timeout=ENTITLEMENT_CACHE_TTL)

        return cached.get(key, False)
    except ImportError:
        return True
```

### Pattern 4: Extending \_handle_subscription_updated for OrgCustomer

**What:** Extend existing webhook handler to detect OrgCustomer by stripe_customer_id and invalidate org member caches.

```python
# Source: Extension of apps/billing/tasks.py _handle_subscription_updated
# Add at bottom of existing function after personal cache invalidation:

# B2B_START
def _try_invalidate_org_member_caches(stripe_customer_id: str) -> None:
    """Invalidate entitlement caches for all members of an org if OrgCustomer matches.

    Called from _handle_subscription_updated after the personal cache is cleared.
    """
    try:
        from apps.orgs.models import OrgCustomer, Membership
        from django.core.cache import cache

        org_customer = OrgCustomer.objects.get(stripe_customer_id=stripe_customer_id)
        org = org_customer.org
        member_ids = Membership.objects.filter(org=org).values_list("user_id", flat=True)
        for user_id in member_ids:
            cache.delete(f"entitlements:org:{org.pk}:{user_id}")
    except Exception:
        # OrgCustomer not found — this was a personal subscription, not org.
        pass
# B2B_END
```

### Pattern 5: Invitation "Token Survives Signup" Flow

**What:** Pending invite token stored in Django session; consumed in post-accept service call after signup.

**When to use:** New user accepting invite — no existing account at invite email.

```python
# Source: Standard Django session pattern
PENDING_INVITE_SESSION_KEY = "pending_org_invite_token"

# Step 1: GET /api/v1/org/invitations/accept?token=xxx
# If user is NOT logged in: store token in session, redirect to /signup
request.session[PENDING_INVITE_SESSION_KEY] = token
request.session.save()
return redirect("/signup?invite_pending=1")

# Step 2: After allauth signup completes (use allauth post-signup signal or
# InvitationService.consume_pending_invite() called from a signal receiver):
def consume_pending_invite(request, user):
    token = request.session.pop(PENDING_INVITE_SESSION_KEY, None)
    if token:
        InvitationService().accept(token=token, user=user)
```

**Caution:** The post-signup hook integration point must be evaluated at plan time. Two options:

1. `allauth.account.signals.user_signed_up` signal (clean, recommended)
2. Custom allauth adapter `save_user()` override

Option 1 is recommended as it does not require modifying the existing `CustomAccountAdapter`.

### Pattern 6: Ownership Transfer — Atomic Role Swap

**What:** Transfer org ownership atomically, making previous owner an admin.

```python
# Source: Django atomic transaction pattern
from django.db import transaction

def transfer_ownership(self, org, current_owner, new_owner_user) -> None:
    with transaction.atomic():
        # Demote current owner
        Membership.objects.filter(org=org, user=current_owner).update(
            role=Membership.Role.ADMIN
        )
        # Elevate new owner
        Membership.objects.filter(org=org, user=new_owner_user).update(
            role=Membership.Role.OWNER
        )
```

### Org Controller URL Structure

All org endpoints are namespaced under `{org_slug}` path param:

```
GET    /api/v1/org/{org_slug}/                        # org detail
PATCH  /api/v1/org/{org_slug}/                        # update org name (owner only)
DELETE /api/v1/org/{org_slug}/                        # delete org (owner only)
GET    /api/v1/org/{org_slug}/members/                # list members
PATCH  /api/v1/org/{org_slug}/members/{user_id}/role  # change member role (admin only)
DELETE /api/v1/org/{org_slug}/members/{user_id}/      # remove member (admin only)
POST   /api/v1/org/{org_slug}/transfer-ownership/     # transfer ownership (owner only)
POST   /api/v1/org/                                   # create org (authenticated user)
GET    /api/v1/org/invitations/accept/                # accept invite (any authenticated or anon)
POST   /api/v1/org/{org_slug}/invitations/            # send invite (admin only)
DELETE /api/v1/org/{org_slug}/invitations/{id}/       # revoke invite (admin only)
```

### Anti-Patterns to Avoid

- **Querying Organization inside services without going through permission layer:** Services receive `org` from controllers (which got it from `request.org`), never fetch by slug themselves. This guarantees membership was verified.
- **Circular import between orgs/ and billing/:** `orgs/` may import from `billing/` (for `_flags_for_plan`, `_resolve_plan_id`). `billing/` must never import from `orgs/`. The OrgCustomer lookup in the webhook handler uses a lazy import inside `_try_invalidate_org_member_caches()`.
- **Using `cache.delete_many()` with pattern matching:** Django's cache API (including django-redis) does not support key-pattern deletion via `delete_many`. Iterate `Membership` queryset and delete keys individually. Acceptable for typical team sizes.
- **Token generated with `random` module:** Always use `secrets.token_urlsafe()` for invitation tokens — cryptographically random. Never use `random` for security tokens.
- **Checking `Invitation.expires_at > now()` outside a transaction:** Invitation `is_valid()` check and marking it `ACCEPTED` must happen in the same `transaction.atomic()` to prevent double-accept race conditions.

---

## Don't Hand-Roll

| Problem                    | Don't Build          | Use Instead                                                                    | Why                                                                         |
| -------------------------- | -------------------- | ------------------------------------------------------------------------------ | --------------------------------------------------------------------------- |
| Secure invitation tokens   | Custom random string | `secrets.token_urlsafe(48)`                                                    | stdlib cryptographic RNG, already used in core middleware for uuid          |
| Email delivery with retry  | Custom SMTP caller   | `apps.notifications.utils.send_email()`                                        | Already wrapped in `transaction.on_commit`, Celery retry with backoff       |
| Cache invalidation pattern | Custom cache wrapper | `django.core.cache.cache.delete()` per key                                     | LocMemCache in tests, django-redis in prod — already overridden in conftest |
| ServiceError hierarchy     | Custom exceptions    | `apps.core.exceptions.ServiceError`, `NotFoundError`, `PermissionDeniedError`  | Global handler in config/urls.py converts them to JSON error responses      |
| Stripe org customer        | Custom Stripe calls  | Reuse `BillingService` adapter pattern with `OrgCustomer` as the lookup anchor | Adapter already handles Stripe error edge cases                             |

**Key insight:** Every pattern needed in Phase 26 has a proven implementation in the existing codebase. The discipline is replication-not-reinvention.

---

## Common Pitfalls

### Pitfall 1: Invitation Double-Accept Race Condition

**What goes wrong:** Two concurrent requests (two browser tabs, or user and admin both clicking) accept the same invitation, creating two `Membership` rows.

**Why it happens:** `Invitation.is_valid()` check and `Membership.objects.create()` are not atomic by default.

**How to avoid:** Wrap the entire accept flow in `transaction.atomic()`. The `unique_together = [("org", "user")]` constraint on `Membership` will raise `IntegrityError` on the second request, which should be caught and returned as a 409 conflict.

**Warning signs:** Two memberships for same user in same org in DB.

### Pitfall 2: Circular Import Between orgs/ and billing/

**What goes wrong:** `billing/tasks.py` importing `from apps.orgs.models import OrgCustomer` at module top level causes circular import because `apps/orgs/` may also import from `billing/`.

**Why it happens:** Both modules are loaded during Django startup; circular dependency at module level causes `ImportError`.

**How to avoid:** The `_try_invalidate_org_member_caches()` function uses a lazy import inside a try/except block (same pattern as existing handlers in `billing/tasks.py`). Never add top-level `apps.orgs` imports in `billing/`.

**Warning signs:** `ImportError` or `AppRegistryNotReady` at Django startup.

### Pitfall 3: IsOrgMember and IsOrgAdmin Composition Order

**What goes wrong:** `permissions=[IsAuthenticated, IsOrgAdmin]` bypasses membership check if `IsOrgMember` is not in the chain, leaving `request.org` unset.

**Why it happens:** `IsOrgAdmin` assumes `request.org` is already set by `IsOrgMember`.

**How to avoid:** Always compose as `permissions=[IsAuthenticated, IsOrgMember, IsOrgAdmin]` for admin-only endpoints. Never use `IsOrgAdmin` alone. Document this constraint in the class docstring.

**Warning signs:** `AttributeError: 'WSGIRequest' object has no attribute 'org'` in admin endpoints.

### Pitfall 4: Session-Based Invite Token Lost After Allauth Signup

**What goes wrong:** The `pending_org_invite_token` is stored in session before redirect to signup. After allauth creates the user and session, the pre-signup session may be regenerated (session fixation prevention), losing the token.

**Why it happens:** `django-allauth` calls `request.session.cycle_key()` on login to prevent session fixation attacks. This preserves session data but changes the session key.

**How to avoid:** `cycle_key()` preserves data — the token should survive. Verify in testing that the session key after signup still contains `PENDING_INVITE_SESSION_KEY`. If data is lost, store token in a short-lived `Invitation`-linked session variable OR rely on `user_signed_up` signal receiving the request object.

**Warning signs:** New user redirected to org dashboard but no `Membership` row created.

### Pitfall 5: N+1 on Member Listing

**What goes wrong:** Listing org members triggers one query per member to fetch user data.

**Why it happens:** `Membership` FK to User is lazy by default.

**How to avoid:** Use `Membership.objects.filter(org=org).select_related("user")` in `MembershipService.list_members()`. The codebase has an nplusone guard in conftest that will catch this in tests automatically.

**Warning signs:** `NPlusOneError` from conftest autouse fixture during test run.

### Pitfall 6: OrgCustomer Created After Org Subscription Exists in Stripe

**What goes wrong:** Webhook arrives for an org subscription but `OrgCustomer` does not yet exist in the database — org was subscribed before `OrgCustomer` was created.

**Why it happens:** Race between org creation and Stripe checkout completion.

**How to avoid:** Create `OrgCustomer` immediately when `Organization` is created (via `post_save` signal or in `OrgService.create_org()`), not lazily. Mirror the `Customer` auto-creation signal pattern in `apps/billing/signals.py`.

**Warning signs:** `OrgCustomer.DoesNotExist` errors in webhook handler logs.

---

## Code Examples

Verified patterns from existing codebase:

### Existing RequireRole — Direct Template for IsOrgMember/IsOrgAdmin

```python
# Source: apps/api/apps/accounts/permissions.py (verified)
from django.http import HttpRequest
from ninja_extra import ControllerBase
from ninja_extra.permissions import BasePermission

class RequireRole(BasePermission):
    def __init__(self, role: str) -> None:
        self.role = role

    def has_permission(self, request: HttpRequest, controller: ControllerBase) -> bool:
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        if not user.groups.filter(name=self.role).exists():
            return False
        return True
```

### Existing has_feature() — Template for has_org_feature()

```python
# Source: apps/api/apps/core/entitlements.py (verified)
def has_feature(user, key: str) -> bool:
    try:
        from apps.billing.entitlements import _has_feature
        return _has_feature(user, key)
    except ImportError:
        return True
```

### Existing send_email() — Used Verbatim for Invitation Emails

```python
# Source: apps/api/apps/notifications/utils.py (verified)
from apps.notifications.utils import send_email

send_email(
    to=invitation.invited_email,
    template_name="org_invitation.html",
    context={
        "org_name": org.name,
        "accept_url": f"https://app.example.com/accept-invite?token={invitation.token}",
        "expires_hours": 72,
    },
)
```

### Existing Entitlement Cache Pattern — Template for Org Cache

```python
# Source: apps/api/apps/billing/entitlements.py (verified)
ENTITLEMENT_CACHE_TTL = 300

cache_key = f"entitlements:{user.pk}"
cached = cache.get(cache_key)
if cached is None:
    plan_id = _resolve_plan_id(user)
    cached = _flags_for_plan(plan_id)
    cache.set(cache_key, cached, timeout=ENTITLEMENT_CACHE_TTL)
return cached.get(key, False)
```

### Existing Cache Delete Pattern — Template for Org Member Cache Invalidation

```python
# Source: apps/api/apps/billing/tasks.py line 155 (verified)
cache.delete(f"entitlements:{customer.user.pk}")
# Extension for org: iterate members and delete per-membership key
for user_id in member_ids:
    cache.delete(f"entitlements:org:{org.pk}:{user_id}")
```

### Existing Billing Controller Auth Setup — Template for OrgController

```python
# Source: apps/api/apps/billing/controllers.py (verified)
from allauth.headless.contrib.ninja.security import jwt_token_auth
from ninja.security import SessionAuth
from ninja_extra import ControllerBase, api_controller, route
from ninja_extra.permissions import IsAuthenticated

@api_controller(
    "/org",
    tags=["Organizations"],
    permissions=[IsAuthenticated],
    auth=[SessionAuth(), jwt_token_auth],
)
class OrgController(ControllerBase):
    ...
```

### INSTALLED_APPS Registration Pattern

```python
# Source: apps/api/config/settings/base.py lines 115-121 (verified)
# Current:
"apps.billing",  # BILLING MODULE — remove this line to exclude billing

# Add (inside B2B_START/B2B_END markers):
# B2B_START
"apps.orgs",  # B2B MODULE — remove this line to exclude B2B
# B2B_END
```

---

## State of the Art

| Old Approach                       | Current Approach                           | Impact for Phase 26                                                                               |
| ---------------------------------- | ------------------------------------------ | ------------------------------------------------------------------------------------------------- |
| `django-organizations` library     | Custom orgs app (decided in STATE.md)      | Build from scratch — binary is_admin model incompatible with owner/admin/member three-level roles |
| Manual `cache.keys()` pattern scan | Iterate queryset, delete keys individually | Django cache API has no wildcard delete; per-key iteration is the correct approach                |
| allauth 64.x token handling        | allauth >=65.14.3 headless                 | `user_signed_up` signal fires reliably; session data survives `cycle_key()`                       |

---

## Open Questions

1. **Controller class split vs single controller**
   - What we know: CONTEXT.md leaves this to discretion; billing uses one controller class per domain
   - What's unclear: Whether org CRUD + membership management + invitations in one controller is too large
   - Recommendation: Use three separate `@api_controller` classes (`OrgController`, `MembershipController`, `InvitationController`) each with focused responsibility. Registration via `api.auto_discover_controllers()` handles them all automatically.

2. **Slug uniqueness — global unique or case-insensitive unique**
   - What we know: CONTEXT.md leaves to discretion
   - What's unclear: Whether `unique=True` on SlugField is sufficient or whether case-insensitive uniqueness (`iexact` check at service layer) is needed
   - Recommendation: Use `unique=True` on the model for DB enforcement + normalize to lowercase in `OrgService.create_org()` before saving. Reject uppercase slugs at schema validation layer with a `SlugField` regex validator.

3. **Invitation resend behavior**
   - What we know: CONTEXT.md leaves to discretion
   - What's unclear: Re-use same token or issue new one
   - Recommendation: Issue a new token on resend; mark the old invitation as `REVOKED`; create a new `Invitation` with fresh `expires_at`. Avoids confusion if old token link is still in email client.

4. **OrgController pagination style**
   - What we know: No existing paginated list endpoint in the current codebase to reference (billing lists invoices without pagination)
   - What's unclear: Whether to use Django Ninja built-in `paginate` decorator or manual limit/offset
   - Recommendation: Use Django Ninja's built-in `@route.get(..., response=list[MemberOut])` with `limit` and `offset` query params, consistent with how `list_invoices` handles `limit: int = 10`. Full cursor pagination is not needed for member lists at this scale.

---

## Validation Architecture

### Test Framework

| Property           | Value                                                   |
| ------------------ | ------------------------------------------------------- |
| Framework          | pytest + pytest-django (already installed)              |
| Config file        | `apps/api/pyproject.toml` — `[tool.pytest.ini_options]` |
| Quick run command  | `cd apps/api && uv run pytest tests/orgs/ -x -q`        |
| Full suite command | `cd apps/api && uv run pytest tests/ -q`                |

### Phase Requirements → Test Map

| Req ID  | Behavior                                              | Test Type | Automated Command                                                                           | File Exists? |
| ------- | ----------------------------------------------------- | --------- | ------------------------------------------------------------------------------------------- | ------------ |
| ORG-01  | User creates org, becomes owner                       | unit      | `pytest tests/orgs/test_services.py::test_create_org_creates_owner_membership -x`           | Wave 0       |
| ORG-01  | Slug uniqueness enforced                              | unit      | `pytest tests/orgs/test_models.py::test_org_slug_unique -x`                                 | Wave 0       |
| ORG-02  | Invite sends email with token                         | unit      | `pytest tests/orgs/test_services.py::test_invite_sends_email -x`                            | Wave 0       |
| ORG-02  | Token expires after 72h                               | unit      | `pytest tests/orgs/test_services.py::test_invite_token_expiry -x`                           | Wave 0       |
| ORG-02  | Email mismatch returns 400                            | unit      | `pytest tests/orgs/test_services.py::test_invite_accept_email_mismatch -x`                  | Wave 0       |
| ORG-02  | New user invite survives signup                       | unit      | `pytest tests/orgs/test_services.py::test_invite_accept_new_user_session_flow -x`           | Wave 0       |
| ORG-03  | IsOrgMember returns 404 for non-member                | unit      | `pytest tests/orgs/test_permissions.py::test_non_member_gets_404 -x`                        | Wave 0       |
| ORG-03  | IsOrgAdmin returns 403 for member-role user           | unit      | `pytest tests/orgs/test_permissions.py::test_member_role_admin_endpoint_gets_403 -x`        | Wave 0       |
| ORG-04  | Ownership transfer demotes old owner to admin         | unit      | `pytest tests/orgs/test_services.py::test_transfer_ownership -x`                            | Wave 0       |
| ORG-05  | Cross-org resource access returns 403                 | unit      | `pytest tests/orgs/test_controllers.py::test_cross_org_access_forbidden -x`                 | Wave 0       |
| BILL-01 | OrgCustomer created on org creation                   | unit      | `pytest tests/orgs/test_models.py::test_org_customer_auto_created -x`                       | Wave 0       |
| BILL-02 | has_org_feature checks org plan first                 | unit      | `pytest tests/core/test_entitlements.py::test_has_org_feature_org_plan_takes_precedence -x` | Wave 0       |
| BILL-02 | has_org_feature falls back to personal plan           | unit      | `pytest tests/core/test_entitlements.py::test_has_org_feature_personal_fallback -x`         | Wave 0       |
| BILL-02 | Org subscription update invalidates all member caches | unit      | `pytest tests/billing/test_tasks.py::test_subscription_updated_invalidates_org_caches -x`   | Wave 0       |

### Sampling Rate

- **Per task commit:** `cd apps/api && uv run pytest tests/orgs/ -x -q`
- **Per wave merge:** `cd apps/api && uv run pytest tests/ -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `apps/api/tests/orgs/__init__.py` — new test package
- [ ] `apps/api/tests/orgs/conftest.py` — org/membership/invitation fixtures
- [ ] `apps/api/tests/orgs/test_models.py` — covers ORG-01, BILL-01 (model level)
- [ ] `apps/api/tests/orgs/test_services.py` — covers ORG-01, ORG-02, ORG-04
- [ ] `apps/api/tests/orgs/test_permissions.py` — covers ORG-03
- [ ] `apps/api/tests/orgs/test_controllers.py` — covers ORG-05
- [ ] `apps/api/apps/notifications/templates/email/org_invitation.html` — invitation email template

---

## Sources

### Primary (HIGH confidence)

- Codebase: `apps/api/apps/accounts/permissions.py` — `RequireRole` is direct `BasePermission` template
- Codebase: `apps/api/apps/billing/entitlements.py` — `_has_feature()`, `_resolve_plan_id()`, `_flags_for_plan()` patterns
- Codebase: `apps/api/apps/billing/tasks.py` — `_handle_subscription_updated()` extension point and cache invalidation pattern
- Codebase: `apps/api/apps/billing/models.py` — `Customer`/`Subscription` structural template for `OrgCustomer`
- Codebase: `apps/api/apps/notifications/utils.py` — `send_email()` transaction-safe dispatch
- Codebase: `apps/api/config/urls.py` — `api.auto_discover_controllers()` registration pattern
- Codebase: `apps/api/config/settings/base.py` — `INSTALLED_APPS` and B2B marker pattern
- Codebase: `apps/api/tests/conftest.py` — nplusone guard, test isolation pattern

### Secondary (MEDIUM confidence)

- Django docs: `secrets.token_urlsafe()` for cryptographic tokens — stdlib, version-stable
- Django docs: `transaction.atomic()` for race condition prevention on invite accept
- allauth 65.x: `user_signed_up` signal fires after user and EmailAddress are created — confirmed via allauth headless integration in codebase

### Tertiary (LOW confidence)

- allauth session `cycle_key()` behavior: session data preserved through key cycling — standard Django behavior; verify in integration test

---

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — no new dependencies; all patterns from verified codebase files
- Architecture: HIGH — direct adaptation of existing patterns (RequireRole, has_feature, Customer model)
- Pitfalls: HIGH for most; MEDIUM for session token survival (cycle_key behavior)

**Research date:** 2026-03-12
**Valid until:** 2026-06-12 (stable domain — Django + ninja-extra patterns change slowly)
