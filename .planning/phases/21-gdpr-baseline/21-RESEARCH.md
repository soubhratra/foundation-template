# Phase 21: GDPR Baseline - Research

**Researched:** 2026-03-12
**Domain:** GDPR compliance — account deletion, data export, cookie consent
**Confidence:** HIGH

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions

**Account deletion — confirmation**

- User must re-enter their current password to confirm deletion
- Implemented as a modal with a password input field and a destructive "Delete my account" button

**Account deletion — cascade order**

- Cascade in `UserDeletionService` Celery task:
  1. Cancel active Stripe subscription immediately (cancel_at_period_end=False)
  2. Delete Stripe customer object
  3. Delete PostHog person record via `ObservabilityAdapter.delete_person()`
  4. Call `user.delete()` — Django ORM cascades all related tables
- Returns HTTP 202 immediately; cascade runs async in Celery

**Account deletion — UI placement**

- Web app: `/settings` page with a Danger Zone section at the bottom
- Mobile: out of scope for this phase
- After deletion: session invalidated, redirect to `/`

**Data export — scope**

- `profile`: email, first_name, last_name, date_joined, last_login
- `social_accounts`: list of connected providers with provider UID
- `billing`: subscription_status, plan_id, payment history (amount, currency, date — no raw card data)
- Auth event logs NOT included
- Nested JSON object (not flat)

**Data export — delivery**

- Synchronous: `GET /api/v1/account/export` returns JSON directly
- `Content-Disposition: attachment; filename="my-data.json"` header
- No async task, no email, no time-limited link

**Cookie consent — banner design**

- Fixed bottom bar (not modal)
- Two buttons: Accept Analytics / Decline
- Short copy: "We use analytics to improve the app." with Privacy Policy link
- Clicking outside does NOT count as consent

**Cookie consent — storage**

- `localStorage` key: `analytics_consent` = `'granted'` | `'denied'`
- Banner re-appears if localStorage cleared or key absent
- No server-side consent record

**Cookie consent — PostHog gating**

- PostHog NOT initialized on page load — current unconditional `posthog.init()` in `providers.tsx` must be refactored
- On Accept: `posthog.init(...)` with full config
- On Decline: `posthog.opt_out_capturing()`
- On page load: read localStorage; `'granted'` → init immediately; `'denied'` → opt-out; absent → show banner

### Claude's Discretion

- Exact `UserDeletionService` error handling if Stripe cancel fails (log + continue, or abort?)
- Whether to send a "your account has been deleted" email before deletion
- Exact styling of the consent banner (colors, typography — cohesive with Shadcn/ui theme)
- Whether `/settings` page uses server or client component layout

### Deferred Ideas (OUT OF SCOPE)

- Account deletion on mobile
- Data export on mobile
- Full privacy preference center (granular per-cookie-category toggles)
- "Your account has been scheduled for deletion" grace-period flow
- Server-side consent logging for audit trail

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID      | Description                                                                                                                                                                                                  | Research Support                                                                                                                                                          |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| GDPR-01 | Authenticated user can permanently delete account via `DELETE /api/v1/account/` — triggers async Celery task cascading through all user data, cleans up Stripe customer and PostHog person, returns HTTP 202 | Celery task pattern documented; Stripe delete_customer and PostHog REST delete API researched; cascade order and error handling patterns established                      |
| GDPR-02 | Authenticated user can export all personal data as JSON via `GET /api/v1/account/export`                                                                                                                     | Data sources mapped to existing model fields; billing payment history via `Customer.payments`; social accounts via allauth; Content-Disposition header pattern documented |
| GDPR-03 | User sees cookie consent banner on first visit; PostHog initialises only after consent is granted                                                                                                            | PostHog consent gating pattern documented; `providers.tsx` refactor approach established; localStorage pattern confirmed                                                  |

</phase_requirements>

## Summary

Phase 21 implements three discrete GDPR compliance features that together satisfy Article 17 (right to erasure), Article 20 (data portability), and ePrivacy/cookie consent requirements. The implementation spans the Django backend (new endpoints + Celery task) and the Next.js web frontend (settings page Danger Zone + cookie consent banner).

The most technically complex element is the account deletion cascade. The `UserDeletionService` must orchestrate three external systems: Stripe (cancel subscription then delete customer), PostHog (delete person via REST API), and Django ORM (`user.delete()` cascades allauth + billing). The critical discovery is that the **PostHog Python SDK has no `delete_person` method** — deletion requires a direct HTTP call to PostHog's management REST API using a `personal_api_key` (a separate credential from the write-only `POSTHOG_API_KEY`). This requires two new env vars: `POSTHOG_PROJECT_ID` and `POSTHOG_PERSONAL_API_KEY`.

The cookie consent banner requires refactoring `providers.tsx` to gate `posthog.init()` behind localStorage consent state. The `Dialog` Shadcn/ui component is not currently installed and must be added via `npx shadcn add dialog` for the delete confirmation modal.

**Primary recommendation:** Split into three plans: (1) backend deletion cascade + export endpoints, (2) settings page Danger Zone with delete modal, (3) cookie consent banner + PostHog gating refactor.

## Standard Stack

### Core

| Library                 | Version           | Purpose                         | Why Standard                                |
| ----------------------- | ----------------- | ------------------------------- | ------------------------------------------- |
| celery (shared_task)    | installed         | Async deletion cascade          | Established pattern in billing/tasks.py     |
| posthog (Python SDK)    | installed         | Event capture only              | SDK used for capture; deletion is REST-only |
| stripe (Python SDK v14) | installed         | Cancel + delete customer        | StripeClient pattern established            |
| django-ninja-extra      | installed         | New AccountController endpoints | All API controllers use this                |
| posthog-js              | installed         | Frontend analytics              | Already in providers.tsx                    |
| react-hook-form + zod   | installed         | Password confirm input in modal | Established pattern in settings-client.tsx  |
| Shadcn/ui Dialog        | NOT YET INSTALLED | Delete confirmation modal       | Must `npx shadcn add dialog`                |

### Supporting

| Library                 | Version          | Purpose                         | When to Use                               |
| ----------------------- | ---------------- | ------------------------------- | ----------------------------------------- |
| httpx or requests       | stdlib/installed | PostHog management REST API     | delete_person needs direct HTTP call      |
| allauth SocialAccount   | installed        | Social accounts data for export | GDPR-02 export payload                    |
| django.contrib.sessions | installed        | Session invalidation pre-delete | invalidate_user_sessions() already exists |

### Alternatives Considered

| Instead of                     | Could Use              | Tradeoff                                                    |
| ------------------------------ | ---------------------- | ----------------------------------------------------------- |
| Direct REST for PostHog delete | SDK (no method)        | SDK has no delete method — REST is the only option          |
| Dialog component               | AlertDialog            | Either works; Dialog allows richer content (password input) |
| `Content-Disposition` header   | File download endpoint | Direct header is simpler for inline JSON                    |

**Installation:**

```bash
# Shadcn Dialog (web):
npx shadcn add dialog

# No new Python packages needed — httpx is already present via existing deps
# Verify: grep httpx apps/api/uv.lock || uv add httpx
```

## Architecture Patterns

### Recommended Project Structure

```
apps/api/apps/accounts/
├── controllers.py          # Add AccountController (DELETE /account/, GET /account/export)
├── services.py             # Add UserDeletionService; data_export() helper
├── tasks.py                # NEW: delete_user_account task
└── tests/                  # New test files for deletion + export

apps/api/apps/core/
└── observability.py        # Add delete_person() to ObservabilityAdapter ABC

apps/web/app/
├── providers.tsx           # Refactor: gate posthog.init() behind consent check
├── layout.tsx              # Add <CookieConsentBanner /> render
└── (dashboard)/settings/
    └── settings-client.tsx  # Add DangerZone section + DeleteAccountModal

apps/web/src/
├── components/ui/dialog.tsx  # ADD via: npx shadcn add dialog
├── components/cookie-consent-banner.tsx  # NEW client component
└── actions/account-actions.ts           # NEW server action: deleteAccountAction
```

### Pattern 1: Celery Task with Log-and-Continue Error Handling

**What:** The deletion Celery task wraps each external service call in try/except, logs failures, and continues. The goal is that `user.delete()` always runs even if Stripe or PostHog calls fail (data must be purged from our database regardless of third-party errors).

**When to use:** When external service failures must not block GDPR compliance (deleting the Django row is the legally required step).

**Example:**

```python
# Source: apps/api/apps/billing/tasks.py (established pattern)
@shared_task(
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    default_retry_delay=2,
    name="apps.accounts.tasks.delete_user_account",
)
def delete_user_account(self, user_id: int) -> None:
    from django.contrib.auth import get_user_model
    from apps.accounts.services import UserDeletionService
    User = get_user_model()
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.warning("delete_user_account: user %s already deleted", user_id)
        return
    UserDeletionService().execute(user)
```

### Pattern 2: ObservabilityAdapter ABC Extension

**What:** Add `delete_person(distinct_id: str) -> None` as abstract method to `ObservabilityAdapter`. `PostHogAdapter` implements via REST API call. `NoOpAdapter` is a no-op. `SentryAdapter` raises `NotImplementedError`.

**When to use:** Any new observability action that has a provider-specific implementation.

**Example:**

```python
# Source: apps/api/apps/core/observability.py (existing ABC pattern)
@abc.abstractmethod
def delete_person(self, distinct_id: str) -> None:
    """Delete a person record from the observability provider.

    Required for GDPR Article 17 compliance. Called by UserDeletionService
    before user.delete(). Must be a no-op when no provider is configured.

    Args:
        distinct_id: The user identifier used when capturing events.
                     For Django users, this is str(user.pk).
    """
```

### Pattern 3: PostHog Person Deletion via REST API

**What:** PostHog Python SDK has no delete method. Must call PostHog management API directly. Requires finding the person UUID by distinct_id first, then DELETE.

**Critical:** Uses `POSTHOG_PERSONAL_API_KEY` (a "Personal API key" from PostHog project settings) — NOT the same as `POSTHOG_API_KEY` (which is the project write key).

**When to use:** Only in `PostHogAdapter.delete_person()`.

**Example:**

```python
# Source: PostHog API docs (MEDIUM confidence — verified via WebSearch)
# Step 1: Find person UUID by distinct_id
# GET /api/projects/{project_id}/persons/?distinct_id={distinct_id}
# Step 2: Delete by UUID
# DELETE /api/projects/{project_id}/persons/{person_uuid}/?delete_events=true

import httpx

def delete_person(self, distinct_id: str) -> None:
    headers = {"Authorization": f"Bearer {settings.POSTHOG_PERSONAL_API_KEY}"}
    host = settings.POSTHOG_HOST.rstrip("/")
    project_id = settings.POSTHOG_PROJECT_ID

    # Find person UUID
    resp = httpx.get(
        f"{host}/api/projects/{project_id}/persons/",
        params={"distinct_id": distinct_id},
        headers=headers,
        timeout=10,
    )
    resp.raise_for_status()
    results = resp.json().get("results", [])
    if not results:
        logger.info("PostHog delete_person: no person found for distinct_id=%s", distinct_id)
        return

    person_uuid = results[0]["id"]
    del_resp = httpx.delete(
        f"{host}/api/projects/{project_id}/persons/{person_uuid}/",
        params={"delete_events": "true"},
        headers=headers,
        timeout=10,
    )
    del_resp.raise_for_status()
```

### Pattern 4: HTTP 202 for Async Deletion

**What:** Controller returns `202 Accepted` immediately after enqueueing the Celery task. Session is invalidated server-side at the point of request (not in the Celery task) to prevent further authenticated requests while deletion is pending.

**When to use:** Any destructive async operation.

**Example:**

```python
# Source: apps/api/apps/billing/controllers.py (202 pattern established)
@route.delete("/account/", response={202: MessageSchema}, url_name="account-delete")
def delete_account(self, request, payload: DeleteAccountIn):
    """Initiate permanent account deletion. Returns 202 immediately."""
    # Verify password first
    if not request.user.check_password(payload.password):
        raise HttpError(400, "Incorrect password.")
    # Invalidate sessions synchronously (security — prevent further access)
    from apps.accounts.services import invalidate_user_sessions
    invalidate_user_sessions(request.user.id)
    # Enqueue cascade deletion
    from apps.accounts.tasks import delete_user_account
    delete_user_account.delay(request.user.id)
    return 202, {"message": "Account deletion initiated."}
```

### Pattern 5: Data Export — Synchronous JSON Response

**What:** `GET /api/v1/account/export` assembles a dict from multiple model sources and returns it with `Content-Disposition: attachment` header.

**When to use:** Data volume is small enough to be synchronous (no large files, no media).

**Example:**

```python
# Source: GDPR Article 20 standard practice (HIGH confidence)
from django.http import JsonResponse
import json, datetime

@route.get("/account/export", url_name="account-export")
def export_account_data(self, request):
    """Export all personal data as a downloadable JSON file."""
    data = AccountExportService().export(request.user)
    response = JsonResponse(data)
    response["Content-Disposition"] = 'attachment; filename="my-data.json"'
    return response
```

### Pattern 6: Cookie Consent Banner with PostHog Gating

**What:** `providers.tsx` unconditionally calls `posthog.init()` — this must be refactored. The banner is a separate client component rendered in `layout.tsx`. On mount, it reads `localStorage`; if absent it shows the banner.

**When to use:** Any analytics tool that must not fire before consent.

**Example:**

```typescript
// Source: posthog-js docs (MEDIUM confidence)
// In providers.tsx — remove the unconditional posthog.init() block
// Replace with:
useEffect(() => {
  const consent = localStorage.getItem("analytics_consent");
  if (consent === "granted") {
    posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY ?? "", { ... });
  } else if (consent === "denied") {
    posthog.opt_out_capturing();
  }
  // else: show banner (banner component handles this)
}, []);

// CookieConsentBanner.tsx
const handleAccept = () => {
  localStorage.setItem("analytics_consent", "granted");
  posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY ?? "", {
    api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST ?? "https://eu.i.posthog.com",
    capture_pageview: false,
    capture_pageleave: true,
    session_recording: { maskAllInputs: true },
  });
  setVisible(false);
};

const handleDecline = () => {
  localStorage.setItem("analytics_consent", "denied");
  posthog.opt_out_capturing();
  setVisible(false);
};
```

### Anti-Patterns to Avoid

- **Deleting Stripe customer before cancelling subscription:** The subscription must be cancelled first (immediately, cancel_at_period_end=False) — deleting the customer without cancelling the subscription first may leave Stripe in an inconsistent state and triggers final invoice generation unexpectedly.
- **Calling `user.delete()` in the Celery task before invalidating sessions:** Sessions should be invalidated synchronously at the HTTP request layer (not in Celery) to prevent any new requests between 202 response and task execution.
- **Using `POSTHOG_API_KEY` for management API calls:** The write key (`POSTHOG_API_KEY`) is project-scoped and cannot authenticate management API reads/deletes. Must use a `POSTHOG_PERSONAL_API_KEY` (Personal API key from PostHog project settings → Personal API keys).
- **Calling `posthog.init()` multiple times:** Calling `init()` more than once on the same `posthog` instance causes duplicate events. Use `posthog.has_opted_in_capturing()` or the `loaded` callback to guard.
- **Swallowing exceptions in export endpoint:** The export must succeed completely or return a clear error — partial exports violate GDPR Article 20 (must provide complete data).

## Don't Hand-Roll

| Problem                          | Don't Build                    | Use Instead                                                            | Why                                                       |
| -------------------------------- | ------------------------------ | ---------------------------------------------------------------------- | --------------------------------------------------------- |
| Session invalidation on delete   | Custom session-clearing loop   | `invalidate_user_sessions()` in accounts/services.py                   | Already implemented, handles all session types            |
| Stripe subscription cancellation | Direct stripe API call in task | `BillingService.cancel_subscription(user, cancel_at_period_end=False)` | Encapsulated, testable, updates local DB state            |
| Password verification            | Custom crypto comparison       | `user.check_password(payload.password)`                                | Django's constant-time comparison prevents timing attacks |
| allauth social accounts query    | ORM join query                 | `SocialAccount.objects.filter(user=user)`                              | Standard allauth ORM access                               |
| Payment history query            | Complex join                   | `user.billing_customer.payments.all()`                                 | Established related_name from billing models              |

**Key insight:** The existing service and adapter layers absorb almost all the complexity — `UserDeletionService` is mostly orchestration, not new logic.

## Common Pitfalls

### Pitfall 1: PostHog SDK Has No Delete Method

**What goes wrong:** Developer expects `self._client.delete_person(distinct_id)` or similar to exist on the `posthog.Posthog` instance.
**Why it happens:** The PostHog Python SDK is write-only (capture/identify/flags). Management operations require the REST API.
**How to avoid:** `PostHogAdapter.delete_person()` must use `httpx.get()` to find the person UUID, then `httpx.delete()` to delete. Requires `POSTHOG_PERSONAL_API_KEY` and `POSTHOG_PROJECT_ID` in settings. These are new env vars not currently in `.env.example`.
**Warning signs:** `AttributeError: 'Posthog' object has no attribute 'delete_person'` — or worse, silently never deleting.

### Pitfall 2: Missing POSTHOG_PERSONAL_API_KEY vs POSTHOG_API_KEY Confusion

**What goes wrong:** Using `POSTHOG_API_KEY` (project API key) to authenticate management API calls returns 401 or 403.
**Why it happens:** PostHog has two distinct key types: project write keys (for capture) and personal API keys (for management/admin). They are NOT interchangeable.
**How to avoid:** Add two new settings: `POSTHOG_PROJECT_ID` (numeric, from PostHog project URL) and `POSTHOG_PERSONAL_API_KEY` (from PostHog Settings → Personal API keys). Both default to `""` — `NoOpAdapter` is used when not set so tests still pass.
**Warning signs:** HTTP 401 from PostHog management API even though capture works fine.

### Pitfall 3: Dialog Component Not Installed

**What goes wrong:** Import of `@/components/ui/dialog` fails at build time — Dialog is not in the installed Shadcn/ui components list.
**Why it happens:** This project has a curated Shadcn/ui install (not all components). Current install: accordion, alert, avatar, badge, button, card, dropdown-menu, form, input, label, separator, sheet, sidebar, skeleton, sonner, switch, table, tooltip. No `dialog`.
**How to avoid:** Run `npx shadcn add dialog` in `apps/web/` before building any component that imports Dialog.
**Warning signs:** `Module not found: Can't resolve '@/components/ui/dialog'`.

### Pitfall 4: posthog.init() Called Multiple Times

**What goes wrong:** If consent banner is shown and user clicks Accept, and providers.tsx also calls `posthog.init()` on mount (e.g., if key is present), the init runs twice. This causes event deduplication issues and may trigger session recording twice.
**Why it happens:** The current `providers.tsx` calls `posthog.init()` unconditionally if `typeof window !== "undefined"`. This block MUST be removed entirely.
**How to avoid:** Remove the top-level `posthog.init()` call in `providers.tsx`. The `CookieConsentBanner` is the sole initializer. The `PostHogProvider` still wraps the tree (it can receive an uninitialized posthog instance).
**Warning signs:** Duplicate `$pageview` events in PostHog dashboard. Two session recordings starting simultaneously.

### Pitfall 5: Stripe Customer Delete Leaves Orphaned Subscription

**What goes wrong:** Calling `stripe.customers.delete(customer_id)` immediately cancels the subscription at Stripe but does NOT trigger the `customer.subscription.deleted` webhook in time. The local `Subscription` model row still shows `status=active` until Django's `user.delete()` cascade removes it — but if Django deletion fails, the DB has an orphaned Stripe record.
**Why it happens:** Webhook delivery is asynchronous and may arrive after the local cascade.
**How to avoid:** The cascade already calls `BillingService.cancel_subscription()` before `delete_customer` — this updates the local `Subscription.status` to `canceled` synchronously. The subsequent `user.delete()` then cascades `Customer` → `Subscription` → `Payment` rows cleanly.
**Warning signs:** Subscription.objects.get(customer=...) returns ACTIVE status after deletion task completes but before the cascade webhook fires.

### Pitfall 6: Export Leaks Sensitive Billing Data

**What goes wrong:** Exporting raw card data, full Stripe customer ID, or raw payment intent IDs into the export JSON.
**Why it happens:** `Payment` model has `stripe_payment_intent_id` — including this in export exposes provider internals.
**How to avoid:** Export only: amount, currency, date, status from `Payment`. Exclude `stripe_payment_intent_id`, `stripe_customer_id`, and `stripe_subscription_id`. GDPR Article 20 requires providing data in a "structured, commonly used, machine-readable format" — not provider identifiers.
**Warning signs:** Code reviewer spots Stripe IDs in test output.

### Pitfall 7: Cookie Consent Banner SSR Hydration Mismatch

**What goes wrong:** The banner's visibility state is computed from `localStorage` which doesn't exist server-side. This causes a React hydration error: server renders banner visible, client immediately hides it (or vice versa).
**Why it happens:** `localStorage` is client-only. Server-side render has no knowledge of it.
**How to avoid:** The banner component must be a pure client component (`"use client"`). Initial render state should be `visible = false` (hidden). In a `useEffect`, read `localStorage`; if absent, set `visible = true`. This causes a brief flicker on first render but avoids hydration mismatch.
**Warning signs:** React hydration warning: "Text content does not match server-rendered HTML."

## Code Examples

Verified patterns from existing codebase:

### Celery Task Registration (accounts/tasks.py)

```python
# Source: apps/api/apps/billing/tasks.py (existing pattern)
from celery import shared_task
import logging

logger = logging.getLogger(__name__)

@shared_task(
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    default_retry_delay=2,
    name="apps.accounts.tasks.delete_user_account",
)
def delete_user_account(self, user_id: int) -> None:
    """Cascade-delete a user account asynchronously after HTTP 202 response."""
    from django.contrib.auth import get_user_model
    from apps.accounts.services import UserDeletionService

    User = get_user_model()
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.warning("delete_user_account: user %s already deleted — skipping", user_id)
        return

    UserDeletionService().execute(user)
```

### AccountController — DELETE endpoint

```python
# Source: apps/api/apps/accounts/controllers.py (existing controller pattern)
from ninja_extra import api_controller, route
from ninja_extra.permissions import IsAuthenticated
from ninja import Schema
from allauth.headless.contrib.ninja.security import jwt_token_auth
from ninja.security import SessionAuth

class DeleteAccountIn(Schema):
    password: str

class MessageOut(Schema):
    message: str

@api_controller(
    "/account",
    tags=["Account"],
    permissions=[IsAuthenticated],
    auth=[SessionAuth(), jwt_token_auth],
)
class AccountController(ControllerBase):

    @route.delete("/", response={202: MessageOut, 400: dict}, url_name="account-delete")
    def delete_account(self, request, payload: DeleteAccountIn):
        if not request.user.check_password(payload.password):
            return 400, {"detail": "Incorrect password."}
        from apps.accounts.services import invalidate_user_sessions
        invalidate_user_sessions(request.user.id)
        from apps.accounts.tasks import delete_user_account
        delete_user_account.delay(request.user.id)
        return 202, {"message": "Account deletion initiated."}
```

### AccountController — GET export endpoint

```python
# Source: GDPR Article 20 implementation pattern
from django.http import HttpResponse

    @route.get("/export", url_name="account-export")
    def export_account_data(self, request):
        from apps.accounts.services import AccountExportService
        data = AccountExportService().export(request.user)
        import json
        from datetime import datetime, timezone
        data["exported_at"] = datetime.now(timezone.utc).isoformat()
        response = HttpResponse(
            json.dumps(data, default=str),
            content_type="application/json",
        )
        response["Content-Disposition"] = 'attachment; filename="my-data.json"'
        return response
```

### AccountExportService — data assembly

```python
# Source: existing billing model relationships (billing/models.py)
from allauth.socialaccount.models import SocialAccount
from apps.billing.models import Customer, Subscription, Payment

class AccountExportService:
    def export(self, user) -> dict:
        profile = {
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "date_joined": user.date_joined.isoformat() if user.date_joined else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
        }

        social_accounts = [
            {"provider": sa.provider, "uid": sa.uid}
            for sa in SocialAccount.objects.filter(user=user)
        ]

        billing: dict = {"subscription_status": None, "plan_id": None, "payments": []}
        try:
            customer = user.billing_customer
            try:
                sub = customer.subscription
                billing["subscription_status"] = sub.status
            except Subscription.DoesNotExist:
                pass
            billing["payments"] = [
                {
                    "amount": float(p.amount),
                    "currency": p.currency,
                    "status": p.status,
                    "date": p.created_at.isoformat(),
                }
                for p in customer.payments.all()
            ]
        except Customer.DoesNotExist:
            pass

        return {
            "profile": profile,
            "social_accounts": social_accounts,
            "billing": billing,
        }
```

### UserDeletionService — orchestration

```python
# Source: apps/api/apps/billing/services.py (BillingService pattern)
import logging
from apps.core.observability import get_observability_adapter
from apps.billing.services import BillingService

logger = logging.getLogger(__name__)

class UserDeletionService:
    def execute(self, user) -> None:
        """Cascade-delete a user: Stripe → PostHog → Django ORM."""
        # Step 1: Cancel and delete Stripe customer (log errors, continue)
        try:
            billing = BillingService()
            billing.cancel_subscription(user, cancel_at_period_end=False)
        except Exception as exc:
            logger.warning("delete: Stripe cancel_subscription failed for user=%s: %s", user.pk, exc)

        try:
            self._delete_stripe_customer(user)
        except Exception as exc:
            logger.warning("delete: Stripe delete_customer failed for user=%s: %s", user.pk, exc)

        # Step 2: Delete PostHog person (log errors, continue)
        try:
            adapter = get_observability_adapter()
            adapter.delete_person(str(user.pk))
        except Exception as exc:
            logger.warning("delete: PostHog delete_person failed for user=%s: %s", user.pk, exc)

        # Step 3: Delete Django user row (cascades all related tables)
        user.delete()
        logger.info("delete: user %s permanently deleted", user.pk)

    def _delete_stripe_customer(self, user) -> None:
        from apps.billing.models import Customer
        from apps.billing.utils import get_adapter
        try:
            customer = user.billing_customer
            if customer.stripe_customer_id:
                adapter = get_adapter()
                adapter.delete_customer(customer.stripe_customer_id)
        except Customer.DoesNotExist:
            pass  # No billing customer — skip
```

### Stripe delete_customer — PaymentAdapter extension

```python
# Source: apps/api/apps/billing/adapters.py (existing ABC pattern)
# Must add to PaymentAdapter ABC:
@abc.abstractmethod
def delete_customer(self, customer_id: str) -> dict[str, Any]:
    """Permanently delete a customer from the payment provider.

    Called as part of GDPR account deletion cascade.
    Returns {"deleted": True} on success.
    """

# StripeAdapter implementation:
def delete_customer(self, customer_id: str) -> dict[str, Any]:
    result = self._client.customers.delete(customer_id)
    return {"deleted": result.deleted}

# StubAdapter implementation:
def delete_customer(self, customer_id: str) -> dict[str, Any]:
    return {"deleted": True}
```

### New env vars for PostHog management API

```bash
# apps/api/.env.example additions:
POSTHOG_PROJECT_ID=              # Numeric project ID from PostHog URL
POSTHOG_PERSONAL_API_KEY=        # Personal API key (Settings → Personal API keys)
```

### Cookie consent banner (TypeScript)

```typescript
// Source: posthog-js docs + localStorage pattern
"use client";

import { useEffect, useState } from "react";
import posthog from "posthog-js";
import { Button } from "@/components/ui/button";

export function CookieConsentBanner() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const consent = localStorage.getItem("analytics_consent");
    if (!consent) setVisible(true);
    else if (consent === "granted") initPostHog();
    else posthog.opt_out_capturing();
  }, []);

  const initPostHog = () => {
    if (!posthog.__loaded) {
      posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY ?? "", {
        api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST ?? "https://eu.i.posthog.com",
        capture_pageview: false,
        capture_pageleave: true,
        session_recording: { maskAllInputs: true },
        loaded: (ph) => { if (!process.env.NEXT_PUBLIC_POSTHOG_KEY) ph.opt_out_capturing(); },
      });
    }
  };

  const handleAccept = () => {
    localStorage.setItem("analytics_consent", "granted");
    initPostHog();
    setVisible(false);
  };

  const handleDecline = () => {
    localStorage.setItem("analytics_consent", "denied");
    posthog.opt_out_capturing();
    setVisible(false);
  };

  if (!visible) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 border-t bg-background p-4">
      <div className="mx-auto flex max-w-4xl items-center justify-between gap-4">
        <p className="text-sm text-muted-foreground">
          We use analytics to improve the app.{" "}
          <a href="/privacy" className="underline">Privacy Policy</a>
        </p>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={handleDecline}>Decline</Button>
          <Button size="sm" onClick={handleAccept}>Accept Analytics</Button>
        </div>
      </div>
    </div>
  );
}
```

### providers.tsx refactor

```typescript
// Remove this block entirely from providers.tsx:
// if (typeof window !== "undefined") {
//   posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY ?? "", { ... });
// }
//
// The CookieConsentBanner component is now the sole posthog.init() call site.
// PostHogProvider still wraps the tree — it accepts an uninitialized instance.
```

## State of the Art

| Old Approach                   | Current Approach      | When Changed              | Impact                                                             |
| ------------------------------ | --------------------- | ------------------------- | ------------------------------------------------------------------ |
| Soft-delete users for GDPR     | Hard delete + cascade | GDPR came into force 2018 | Soft delete violates Article 17 unless combined with anonymization |
| posthog.init() unconditionally | Consent-gated init    | ePrivacy Directive + GDPR | Analytics must not run before consent                              |
| Email-delivered data exports   | Inline JSON download  | GDPR Article 20 standard  | Simpler for small data; inline download acceptable                 |

**Deprecated/outdated:**

- **Soft-delete for GDPR compliance:** REQUIREMENTS.md explicitly marks this as out-of-scope and incorrect. Hard delete is the only correct approach for Article 17 unless anonymization is rigorously applied.

## Open Questions

1. **`httpx` availability in `apps/api/`**
   - What we know: `httpx` is commonly installed as a dependency of other packages (LangGraph, etc.)
   - What's unclear: Is `httpx` in `uv.lock`? If not, needs `uv add httpx` or use stdlib `urllib.request`
   - Recommendation: At plan time, run `grep httpx apps/api/uv.lock` — if absent, add to pyproject.toml. Alternative: use `requests` which is more universally available.

2. **PostHog EU host vs. US host for management API**
   - What we know: `POSTHOG_HOST` defaults to `https://eu.i.posthog.com` (EU cloud). The management API endpoint may differ for EU vs US.
   - What's unclear: EU management API base URL — may be `https://eu.posthog.com` not `https://eu.i.posthog.com`
   - Recommendation: At implementation, use `POSTHOG_HOST.replace("i.posthog", "posthog")` or document that `POSTHOG_HOST` for management API may need separate env var.

3. **`posthog.__loaded` guard in frontend**
   - What we know: PostHog JS has internal state to prevent double-initialization
   - What's unclear: The exact public API to check if PostHog is already initialized
   - Recommendation: Use `posthog.has_opted_in_capturing()` or check if `posthog._isIdentified()` — or simply use a React ref to track whether init was called in this session.

## Validation Architecture

### Test Framework

| Property           | Value                                         |
| ------------------ | --------------------------------------------- |
| Framework          | pytest 8.x + pytest-django                    |
| Config file        | `apps/api/pytest.ini`                         |
| Quick run command  | `cd apps/api && pytest tests/accounts/ -x -q` |
| Full suite command | `cd apps/api && pytest -x -q`                 |

### Phase Requirements → Test Map

| Req ID  | Behavior                                                                  | Test Type | Automated Command                                                       | File Exists?               |
| ------- | ------------------------------------------------------------------------- | --------- | ----------------------------------------------------------------------- | -------------------------- |
| GDPR-01 | DELETE /api/v1/account/ returns 202                                       | unit      | `pytest tests/accounts/test_deletion.py -x`                             | Wave 0                     |
| GDPR-01 | Password mismatch returns 400                                             | unit      | `pytest tests/accounts/test_deletion.py::test_delete_wrong_password -x` | Wave 0                     |
| GDPR-01 | Celery task calls Stripe cancel + delete + PostHog delete + user.delete() | unit      | `pytest tests/accounts/test_deletion.py::test_deletion_task_cascade -x` | Wave 0                     |
| GDPR-01 | ObservabilityAdapter.delete_person() ABC + PostHogAdapter + NoOpAdapter   | unit      | `pytest tests/core/test_observability.py -x`                            | Partial (extends existing) |
| GDPR-01 | PaymentAdapter.delete_customer() ABC + StripeAdapter + StubAdapter        | unit      | `pytest tests/billing/test_adapters.py -x`                              | Partial (extends existing) |
| GDPR-02 | GET /api/v1/account/export returns 200 with correct JSON structure        | unit      | `pytest tests/accounts/test_export.py -x`                               | Wave 0                     |
| GDPR-02 | Export includes profile, social_accounts, billing keys                    | unit      | `pytest tests/accounts/test_export.py::test_export_schema -x`           | Wave 0                     |
| GDPR-02 | Export has Content-Disposition: attachment header                         | unit      | `pytest tests/accounts/test_export.py::test_export_download_header -x`  | Wave 0                     |
| GDPR-03 | posthog.init() not called until consent granted                           | manual    | browser devtools network tab                                            | N/A                        |
| GDPR-03 | analytics_consent localStorage key set on Accept/Decline                  | manual    | browser console                                                         | N/A                        |

### Sampling Rate

- **Per task commit:** `cd apps/api && pytest tests/accounts/ -x -q`
- **Per wave merge:** `cd apps/api && pytest -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `apps/api/tests/accounts/__init__.py` — new test package
- [ ] `apps/api/tests/accounts/test_deletion.py` — covers GDPR-01
- [ ] `apps/api/tests/accounts/test_export.py` — covers GDPR-02
- [ ] No frontend test gaps — GDPR-03 (cookie consent) is manually tested via browser devtools; Vitest setup exists but cookie consent banner is a thin UI-only component

## Sources

### Primary (HIGH confidence)

- PostHog/posthog-python GitHub (master branch client.py) — confirmed no `delete` method in Python SDK
- `apps/api/apps/core/observability.py` — ObservabilityAdapter ABC pattern (direct code read)
- `apps/api/apps/billing/tasks.py` — Celery task patterns with autoretry (direct code read)
- `apps/api/apps/billing/adapters.py` — PaymentAdapter ABC extension pattern (direct code read)
- `apps/api/apps/accounts/services.py` — `invalidate_user_sessions()` already exists (direct code read)
- `apps/web/app/providers.tsx` — unconditional `posthog.init()` that must be refactored (direct code read)
- `apps/web/src/components/ui/` — Dialog component NOT present (confirmed via directory listing)

### Secondary (MEDIUM confidence)

- PostHog REST API (WebSearch verified): `DELETE /api/projects/{project_id}/persons/{person_uuid}/?delete_events=true` — requires personal API key
- PostHog REST API (WebSearch verified): `GET /api/projects/{project_id}/persons/?distinct_id={id}` — lookup person by distinct_id
- Stripe customer delete (WebSearch verified): `StripeClient.customers.delete(customer_id)` — returns `{"deleted": True}`

### Tertiary (LOW confidence)

- PostHog EU management API base URL — may differ from `eu.i.posthog.com` for management calls

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — all core libraries are pre-existing; only Dialog component addition is new
- Architecture: HIGH — all patterns are direct extensions of established project patterns
- Pitfalls: HIGH — PostHog SDK limitation confirmed via direct code inspection; others from project-specific codebase analysis
- PostHog management REST API: MEDIUM — endpoint shape confirmed via WebSearch, implementation details need validation at runtime

**Research date:** 2026-03-12
**Valid until:** 2026-04-12 (stable APIs; PostHog/Stripe unlikely to change delete endpoints)
