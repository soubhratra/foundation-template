# Architecture Patterns: Billing & Payments Module

**Domain:** Billing and payments integration for Foundation Template monorepo
**Researched:** 2026-03-07
**Milestone context:** Subsequent milestone — adding billing module to existing system (apps/api/ Django Ninja Extra + apps/web/ Next.js 15 + apps/mobile/ Expo + packages/api-client/ auto-generated types)
**Overall confidence:** HIGH — grounded in actual codebase inspection (accounts/models.py, ai/controllers.py, config/urls.py, config/settings/base.py, cli-scaffolder.md) plus Stripe official documentation patterns

---

## How This Module Fits the Existing System

The billing module is a new Django app at `apps/api/apps/billing/` following the exact same structural pattern as `apps/api/apps/ai/`. It registers via `api.auto_discover_controllers()` (already present in `config/urls.py`), gets added to `INSTALLED_APPS` in `config/settings/base.py`, and is designed for clean removal by the CLI scaffolder — just like the AI module.

The module introduces:

- **2 new Django models:** `Customer` (OneToOne to User), `Subscription` (FK to Customer)
- **1 payment adapter ABC** with a Stripe concrete implementation
- **6–8 new API endpoints** under `/api/v1/billing/`
- **1 webhook endpoint** registered as a plain Django view (not a Ninja controller — raw body required)
- **4 new billing pages** in `apps/web/app/(dashboard)/billing/`
- **New types** automatically propagated through the OpenAPI pipeline to `packages/api-client/`

---

## 1. Directory Structure: `apps/api/apps/billing/`

```
apps/api/apps/billing/
├── __init__.py
├── apps.py                    # BillingConfig: name = "apps.billing"
├── admin.py                   # CustomerAdmin, SubscriptionAdmin
├── models.py                  # Customer (OneToOne → User), Subscription
├── schemas.py                 # Pydantic request/response schemas
├── controllers.py             # BillingController (Ninja Extra) — CSRF-protected routes
├── services.py                # BillingService — all business logic, no HTTP
├── adapters.py                # PaymentAdapter ABC + StripeAdapter concrete class
├── webhooks.py                # Raw Django view for Stripe webhook (NOT a Ninja controller)
├── signals.py                 # post_save signal: create Customer when User created
└── migrations/
    └── 0001_initial.py
```

### Why `webhooks.py` is a separate plain Django view, not a Ninja controller

Stripe webhook signature verification (`stripe.Webhook.construct_event()`) requires the **raw, unmodified request body bytes**. Django Ninja parses the request body as part of its request processing, which can corrupt the raw bytes. Registering the webhook as a plain `@csrf_exempt` function view in `config/urls.py` with `request.body` gives guaranteed access to the raw bytes.

Source: [Stripe webhook signature documentation](https://docs.stripe.com/webhooks/signature), [Stripe Django integration 2025](https://www.paritydeals.com/blog/how-to-integrate-stripe-with-django-a-step-by-step-guide-2025/)

---

## 2. PaymentAdapter ABC Pattern

### Abstract Base Class (`apps/billing/adapters.py`)

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class CheckoutResult:
    session_id: str
    checkout_url: str


@dataclass
class PortalResult:
    portal_url: str


@dataclass
class WebhookEvent:
    event_type: str          # e.g. "customer.subscription.updated"
    stripe_event_id: str
    data: dict[str, Any]


class PaymentAdapter(ABC):
    """
    Abstract interface for payment processor integration.

    Concrete implementations: StripeAdapter (shipped), others possible.
    The adapter is never imported by controllers directly — BillingService
    resolves it via settings (BILLING_ADAPTER setting).
    """

    @abstractmethod
    def create_customer(self, email: str, name: str) -> str:
        """Create a customer in the payment processor. Returns external customer ID."""
        ...

    @abstractmethod
    def create_checkout_session(
        self,
        customer_external_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
    ) -> CheckoutResult:
        """Create a hosted checkout session. Returns session_id + redirect URL."""
        ...

    @abstractmethod
    def create_portal_session(
        self,
        customer_external_id: str,
        return_url: str,
    ) -> PortalResult:
        """Create a self-serve billing portal session. Returns redirect URL."""
        ...

    @abstractmethod
    def cancel_subscription(self, subscription_external_id: str) -> None:
        """Cancel a subscription immediately or at period end."""
        ...

    @abstractmethod
    def construct_webhook_event(
        self,
        payload: bytes,
        signature_header: str,
        webhook_secret: str,
    ) -> WebhookEvent:
        """
        Verify and parse an inbound webhook payload.
        Raises ValueError on invalid signature.
        """
        ...
```

### Stripe Concrete Implementation (`StripeAdapter`)

```python
import stripe
from django.conf import settings


class StripeAdapter(PaymentAdapter):
    """
    Stripe implementation of PaymentAdapter.

    Uses stripe.StripeClient (v8+ API). Configured via STRIPE_SECRET_KEY setting.
    """

    def __init__(self) -> None:
        self._client = stripe.StripeClient(api_key=settings.STRIPE_SECRET_KEY)

    def create_customer(self, email: str, name: str) -> str:
        customer = self._client.customers.create({"email": email, "name": name})
        return customer.id

    def create_checkout_session(
        self,
        customer_external_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
    ) -> CheckoutResult:
        session = self._client.checkout.sessions.create({
            "customer": customer_external_id,
            "mode": "subscription",
            "line_items": [{"price": price_id, "quantity": 1}],
            "success_url": success_url,
            "cancel_url": cancel_url,
        })
        return CheckoutResult(session_id=session.id, checkout_url=session.url)

    def create_portal_session(
        self,
        customer_external_id: str,
        return_url: str,
    ) -> PortalResult:
        session = self._client.billing_portal.sessions.create({
            "customer": customer_external_id,
            "return_url": return_url,
        })
        return PortalResult(portal_url=session.url)

    def cancel_subscription(self, subscription_external_id: str) -> None:
        self._client.subscriptions.cancel(subscription_external_id)

    def construct_webhook_event(
        self,
        payload: bytes,
        signature_header: str,
        webhook_secret: str,
    ) -> WebhookEvent:
        # stripe.WebhookSignature.verify_header raises SignatureVerificationError
        # if signature is invalid — propagate as ValueError per ABC contract.
        try:
            event = stripe.WebhookSignature.verify_header(
                payload.decode("utf-8"),
                signature_header,
                webhook_secret,
            )
        except stripe.error.SignatureVerificationError as exc:
            raise ValueError("Invalid Stripe webhook signature") from exc

        return WebhookEvent(
            event_type=event["type"],
            stripe_event_id=event["id"],
            data=event["data"]["object"],
        )
```

### Adapter Registration (settings-driven)

```python
# config/settings/base.py (additions for billing module)
BILLING_ADAPTER = "apps.billing.adapters.StripeAdapter"
STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY", default="")
STRIPE_PUBLISHABLE_KEY = env("STRIPE_PUBLISHABLE_KEY", default="")
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET", default="")
```

```python
# apps/billing/services.py
from django.conf import settings
from django.utils.module_loading import import_string
from .adapters import PaymentAdapter

def get_payment_adapter() -> PaymentAdapter:
    """Resolve adapter from settings. Instantiated fresh per call (stateless)."""
    adapter_class = import_string(settings.BILLING_ADAPTER)
    return adapter_class()
```

This lets a future payment processor swap in by changing one settings value, without touching controllers or services. It also makes unit testing trivial: mock `get_payment_adapter()` to return a stub.

---

## 3. Frontend Route Structure (`apps/web/`)

### App Router pages

```
apps/web/app/
└── (dashboard)/
    └── billing/
        ├── page.tsx                   # Billing overview (current plan, usage, next renewal)
        ├── checkout/
        │   └── page.tsx               # Plan selection → Stripe Checkout redirect
        ├── success/
        │   └── page.tsx               # Post-checkout confirmation (Stripe redirects here)
        └── portal/
            └── page.tsx               # Redirect to Stripe Customer Portal (server component)
```

### Next.js API route for Stripe webhook

```
apps/web/app/
└── api/
    └── billing/
        └── webhook/
            └── route.ts               # POST /api/billing/webhook — proxy to Django
```

The Next.js webhook route exists as a stable public URL that Stripe can target. It reads the raw body and the `Stripe-Signature` header and proxies both to Django's webhook endpoint (`/api/v1/billing/webhook/`). This separation means Stripe always sends to a Next.js URL, and Django handles verification and processing — consistent with the "Next.js API routes as thin proxies" constraint in the foundation architecture.

**Alternative considered:** Register webhook directly with Django (`/api/v1/billing/webhook/`). This is also valid but requires the Django server to be publicly accessible from Stripe. Both patterns are acceptable; the Next.js proxy is preferred when using Vercel (which naturally exposes a public URL) with Railway/Fly for Django (which may be internal-only). If Django is publicly exposed, skip the proxy and register the Django URL directly with Stripe.

### Component locations

```
apps/web/
├── app/(dashboard)/billing/
│   └── [pages as above]
├── components/billing/
│   ├── plan-card.tsx                  # Displays a pricing plan
│   ├── subscription-status.tsx        # Badge: active / past_due / canceled
│   ├── billing-overview.tsx           # Current plan summary card
│   └── upgrade-button.tsx             # Initiates checkout session
└── lib/billing/
    └── hooks.ts                       # useSubscription(), useCheckout() React Query hooks
```

---

## 4. Customer Model — Relation to Existing User Model

### Decision: OneToOne extension via separate `Customer` model

```python
# apps/billing/models.py
from django.conf import settings
from django.db import models


class Customer(models.Model):
    """
    Billing profile for a user. Created automatically via post_save signal.

    Relationship: One User → One Customer (always exists after User creation).
    The User model itself is NOT modified. This preserves the accounts app's
    auth-only responsibility and keeps billing cleanly removable.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="billing_customer",
    )
    stripe_customer_id = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
        help_text="Stripe customer ID (cus_xxx). Empty until first billing interaction.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "billing_customers"

    def __str__(self) -> str:
        return f"Customer({self.user.email})"


class Subscription(models.Model):
    """
    Active subscription record. Kept in sync with Stripe via webhooks.
    """

    STATUS_ACTIVE = "active"
    STATUS_PAST_DUE = "past_due"
    STATUS_CANCELED = "canceled"
    STATUS_TRIALING = "trialing"
    STATUS_INCOMPLETE = "incomplete"

    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_PAST_DUE, "Past Due"),
        (STATUS_CANCELED, "Canceled"),
        (STATUS_TRIALING, "Trialing"),
        (STATUS_INCOMPLETE, "Incomplete"),
    ]

    customer = models.OneToOneField(
        Customer,
        on_delete=models.CASCADE,
        related_name="subscription",
        help_text="One active subscription per customer.",
    )
    stripe_subscription_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
    )
    stripe_price_id = models.CharField(
        max_length=255,
        help_text="Stripe Price ID (price_xxx) for the active plan.",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_INCOMPLETE,
        db_index=True,
    )
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "billing_subscriptions"

    def __str__(self) -> str:
        return f"Subscription({self.customer.user.email}, {self.status})"
```

### Why OneToOne and not AbstractUser subclass

- The existing `apps/accounts/models.py` already defines a minimal `User(AbstractUser)`. Django requires the custom user model to be set before the first migration — changing it after is a database recreation. Subclassing again is not possible without replacing accounts entirely.
- OneToOne keeps billing completely isolated. Removing the billing module requires only deleting `apps/billing/` and the `"apps.billing"` INSTALLED_APPS entry — no schema changes to the users table.
- The `related_name="billing_customer"` avoids naming collision with any future `profile` or other OneToOne extensions.
- `stripe_customer_id` is initially blank. It is populated lazily on first billing interaction via `BillingService.get_or_create_stripe_customer()`. This avoids unnecessary Stripe API calls for users who never touch billing.

### Auto-creation via signal (`apps/billing/signals.py`)

```python
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_billing_customer(sender, instance, created, **kwargs):
    """
    Auto-create a Customer record whenever a new User is created.
    The Stripe customer ID is populated lazily on first billing interaction.
    """
    if created:
        from apps.billing.models import Customer
        Customer.objects.get_or_create(user=instance)
```

Signal registered in `BillingConfig.ready()` in `apps.py`:

```python
# apps/billing/apps.py
from django.apps import AppConfig


class BillingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.billing"

    def ready(self) -> None:
        import apps.billing.signals  # noqa: F401
```

---

## 5. Webhook Endpoint Registration in Django Ninja Extra

### Why the webhook is NOT a Ninja controller

Stripe requires the **raw, unmodified request body bytes** for HMAC verification. Django Ninja parses the request body during its processing pipeline, which breaks `request.body` access for raw bytes. The webhook must be a plain Django view exempted from CSRF.

### Registration pattern

```python
# config/urls.py (additions — alongside existing urlpatterns)
from django.views.decorators.csrf import csrf_exempt
from apps.billing.webhooks import stripe_webhook_view

urlpatterns = [
    # ... existing patterns ...
    path("api/v1/billing/webhook/", csrf_exempt(stripe_webhook_view)),
]
```

This is added BEFORE `path("api/v1/", api.urls)` to ensure it is matched first.

### Webhook view (`apps/billing/webhooks.py`)

```python
import json
import logging

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_POST

from apps.billing.services import BillingService

logger = logging.getLogger(__name__)


@require_POST
def stripe_webhook_view(request: HttpRequest) -> HttpResponse:
    """
    Receives Stripe webhook events.

    - Must NOT be a Ninja controller (raw body required for signature verification).
    - Registered with @csrf_exempt in urls.py.
    - Signature verification happens inside BillingService.handle_webhook_event().
    - Returns 200 immediately after dispatching. Idempotent: duplicate events are no-ops.
    """
    payload: bytes = request.body
    sig_header: str = request.headers.get("Stripe-Signature", "")

    if not sig_header:
        logger.warning("Stripe webhook received without Stripe-Signature header")
        return HttpResponse(status=400)

    service = BillingService()
    try:
        service.handle_webhook_event(
            payload=payload,
            signature_header=sig_header,
            webhook_secret=settings.STRIPE_WEBHOOK_SECRET,
        )
    except ValueError:
        logger.warning("Stripe webhook signature verification failed")
        return HttpResponse(status=400)
    except Exception:
        logger.exception("Stripe webhook processing error")
        return HttpResponse(status=500)

    return HttpResponse(status=200)
```

### Webhook event routing inside `BillingService`

```python
# apps/billing/services.py (partial)
HANDLED_EVENTS = {
    "customer.subscription.created",
    "customer.subscription.updated",
    "customer.subscription.deleted",
    "invoice.payment_succeeded",
    "invoice.payment_failed",
}

def handle_webhook_event(self, payload: bytes, signature_header: str, webhook_secret: str) -> None:
    adapter = get_payment_adapter()
    event = adapter.construct_webhook_event(payload, signature_header, webhook_secret)

    if event.event_type not in HANDLED_EVENTS:
        logger.debug(f"Ignoring unhandled Stripe event: {event.event_type}")
        return

    handler = getattr(self, f"_handle_{event.event_type.replace('.', '_')}", None)
    if handler:
        handler(event.data)
```

### Nginx header forwarding (production pitfall)

Nginx drops headers containing underscores by default. The `Stripe-Signature` header uses a hyphen (not underscore) and is safe. However, verify nginx config does not set `underscores_in_headers off` globally — this would affect custom headers. The header name itself is safe, but document this in PITFALLS.

---

## 6. Removable Module Pattern — CLI Scaffolder Compatibility

The billing module follows the exact same isolation pattern as the AI module. The CLI scaffolder spec defines `removeAIModule()` as the template. A parallel `removeBillingModule()` function removes billing with the same four steps.

### Isolation requirements (mirrors AI module spec)

1. All billing code resides in `apps/api/apps/billing/`. No other Django app imports from `apps.billing`.
2. `"apps.billing"` is conditionally present in `INSTALLED_APPS` — the scaffolder strips the line.
3. Billing Python dependencies (`stripe`) are in a dedicated optional group in `pyproject.toml`.
4. Billing env vars (`STRIPE_SECRET_KEY`, etc.) are in a `# BILLING MODULE` section in `.env.example` — the scaffolder strips the section.
5. The billing webhook URL registration in `config/urls.py` is wrapped in a comment block that the scaffolder can identify and remove.
6. Frontend billing pages in `apps/web/app/(dashboard)/billing/` are in a self-contained directory — the scaffolder deletes the directory.

### Scaffolder function pattern

```typescript
// packages/create-foundation-app/src/features/removeBillingModule.ts
async function removeBillingModule(outputDir: string): Promise<void> {
  // 1. Delete Django app directory
  await remove(join(outputDir, "apps/api/apps/billing"));

  // 2. Remove from INSTALLED_APPS
  const settingsPath = join(outputDir, "apps/api/config/settings/base.py");
  let settings = await readFile(settingsPath, "utf-8");
  settings = settings.replace(/^\s*"apps\.billing",?\s*$/gm, "");
  await writeFile(settingsPath, settings, "utf-8");

  // 3. Remove Python dependency
  const pyprojectPath = join(outputDir, "apps/api/pyproject.toml");
  let pyproject = await readFile(pyprojectPath, "utf-8");
  pyproject = pyproject.replace(/^stripe.*$/gm, "");
  await writeFile(pyprojectPath, pyproject, "utf-8");

  // 4. Remove webhook URL from urls.py (comment-delimited block)
  const urlsPath = join(outputDir, "apps/api/config/urls.py");
  let urls = await readFile(urlsPath, "utf-8");
  urls = urls.replace(/# BILLING_START[\s\S]*?# BILLING_END\n?/gm, "");
  await writeFile(urlsPath, urls, "utf-8");

  // 5. Remove billing env vars from .env.example
  const envPath = join(outputDir, "apps/api/.env.example");
  let env = await readFile(envPath, "utf-8");
  env = env.replace(/# BILLING MODULE[\s\S]*?# END BILLING MODULE\n?/gm, "");
  await writeFile(envPath, env, "utf-8");

  // 6. Remove frontend billing pages
  await remove(join(outputDir, "apps/web/app/(dashboard)/billing"));
}
```

### URL registration template block (in `config/urls.py`)

```python
# BILLING_START
from django.views.decorators.csrf import csrf_exempt
from apps.billing.webhooks import stripe_webhook_view
# BILLING_END

urlpatterns = [
    # ... existing ...
    # BILLING_START
    path("api/v1/billing/webhook/", csrf_exempt(stripe_webhook_view)),
    # BILLING_END
    path("api/v1/", api.urls),
]
```

The `BILLING_START` / `BILLING_END` comment delimiters are the scaffolder's surgical removal markers, identical in spirit to how the AI module uses `"apps.ai"` as its identifier.

---

## 7. Impact on `packages/api-client/` and Shared Types

### How billing types propagate automatically

The billing module's Pydantic schemas in `apps/billing/schemas.py` are exposed through Ninja Extra controllers. `api.auto_discover_controllers()` in `config/urls.py` picks them up automatically. Running the existing type generation pipeline produces billing types with zero extra configuration:

```bash
# No new steps needed — existing pipeline handles billing
turbo generate:api-types
```

### New schemas that become TypeScript types

```python
# apps/billing/schemas.py (new file)
from pydantic import BaseModel
from datetime import datetime


class CustomerOut(BaseModel):
    id: int
    stripe_customer_id: str
    created_at: datetime


class SubscriptionOut(BaseModel):
    id: int
    stripe_subscription_id: str
    stripe_price_id: str
    status: str                          # "active" | "past_due" | "canceled" | ...
    current_period_start: datetime | None
    current_period_end: datetime | None
    cancel_at_period_end: bool


class CheckoutSessionOut(BaseModel):
    checkout_url: str


class PortalSessionOut(BaseModel):
    portal_url: str


class CreateCheckoutIn(BaseModel):
    price_id: str
    success_url: str
    cancel_url: str
```

### Generated TypeScript types (from OpenAPI pipeline)

After running `turbo generate:api-types`, `packages/api-client/gen/v1/types.d.ts` will contain:

```typescript
// Auto-generated — do not edit
export interface CustomerOut { ... }
export interface SubscriptionOut { ... }
export interface CheckoutSessionOut { checkout_url: string }
export interface PortalSessionOut { portal_url: string }
```

### `packages/schemas/` additions (Zod validation schemas)

The existing `packages/schemas/src/` contains Zod schemas for cross-platform form validation. Add:

```
packages/schemas/src/billing.ts    # Zod schemas matching billing Pydantic schemas
```

These are used by `apps/web/` and `apps/mobile/` for client-side form validation (e.g., validating that a price_id is non-empty before initiating checkout). They are maintained separately from the generated OpenAPI types because they encode client-side business rules (e.g., acceptable price IDs) that are not expressible in the OpenAPI spec.

---

## 8. Component Boundaries and Data Flow

### Complete data flow: User upgrades to paid plan

```
[Browser: /billing/checkout?plan=pro]
    |
    v
[apps/web/app/(dashboard)/billing/checkout/page.tsx]
    |  Server Component: calls GET /api/v1/billing/plans/
    |  (or static price config from env — preferred to avoid round-trip)
    |
    v
[Client Component: upgrade-button.tsx]
    |  onClick → POST /api/v1/billing/checkout/
    |  body: { price_id: "price_xxx", success_url, cancel_url }
    |
    v
[apps/api/apps/billing/controllers.py: BillingController.create_checkout_session()]
    |  IsAuthenticated permission
    |  delegates to BillingService
    |
    v
[apps/api/apps/billing/services.py: BillingService]
    |  1. get_or_create_stripe_customer(user)
    |     → if Customer.stripe_customer_id is empty:
    |         call adapter.create_customer()
    |         save stripe_customer_id to Customer
    |  2. adapter.create_checkout_session(...)
    |  3. return CheckoutSessionOut(checkout_url=...)
    |
    v
[Stripe API]
    |  Returns hosted checkout URL
    |
    v
[Browser: redirected to Stripe checkout URL]
    |
    v
[User completes payment on Stripe]
    |
    v
[Stripe POSTs webhook to /api/v1/billing/webhook/]
    |
    v
[apps/api/apps/billing/webhooks.py: stripe_webhook_view()]
    |  1. Reads request.body (raw bytes)
    |  2. adapter.construct_webhook_event() — verifies HMAC signature
    |  3. service.handle_webhook_event() routes to handler
    |     _handle_customer_subscription_created():
    |       - Creates/updates Subscription record
    |       - Sets status = "active"
    |
    v
[Browser: redirected to /billing/success?session_id=xxx]
    |
    v
[apps/web/app/(dashboard)/billing/success/page.tsx]
    |  Server Component: GET /api/v1/billing/subscription/
    |  Displays confirmation (subscription may already be active via webhook)
```

### Component responsibilities

| Component                         | Responsibility                                               | Does NOT do                                      |
| --------------------------------- | ------------------------------------------------------------ | ------------------------------------------------ |
| `apps/billing/models.py`          | Customer and Subscription data persistence                   | Any Stripe API calls                             |
| `apps/billing/adapters.py`        | Stripe API calls, webhook signature verification             | Business rules, DB writes                        |
| `apps/billing/services.py`        | Business rules, orchestrates adapter + models                | HTTP request/response handling                   |
| `apps/billing/controllers.py`     | HTTP layer: auth, request validation, response serialization | Business logic                                   |
| `apps/billing/webhooks.py`        | Raw webhook ingestion, signature verification dispatch       | Processing webhook events (delegates to service) |
| `apps/billing/signals.py`         | Auto-create Customer on User creation                        | Any billing business logic                       |
| `apps/web/.../billing/` pages     | UI for billing management                                    | Any Stripe API calls or business logic           |
| `packages/schemas/src/billing.ts` | Client-side form validation for billing inputs               | API calls, rendering                             |

---

## 9. Suggested Build Order

Dependencies drive the sequence. Each step requires all prior steps.

```
Step 1: Django models + migration
  - Customer model (OneToOne → User)
  - Subscription model (FK → Customer)
  - Initial migration: 0001_initial.py
  WHY FIRST: All other billing components depend on these tables existing.

Step 2: PaymentAdapter ABC + StripeAdapter
  - adapters.py (ABC + StripeAdapter class)
  - Add stripe to pyproject.toml (uv add stripe)
  - Add STRIPE_* settings to base.py + .env.example
  WHY SECOND: Services and webhooks depend on the adapter interface.

Step 3: BillingService (core logic, no HTTP)
  - services.py
  - get_or_create_stripe_customer()
  - create_checkout_session()
  - create_portal_session()
  - handle_webhook_event() dispatcher
  - Individual webhook handlers (_handle_customer_subscription_*)
  WHY THIRD: Can be unit-tested in isolation before HTTP layer exists.

Step 4: Pydantic schemas
  - schemas.py
  - CustomerOut, SubscriptionOut, CheckoutSessionOut, PortalSessionOut
  - CreateCheckoutIn
  WHY FOURTH: Ninja controllers require schemas. Schemas can reference models.

Step 5: BillingController (Ninja Extra)
  - controllers.py
  - GET /billing/customer/ → current customer
  - GET /billing/subscription/ → current subscription
  - POST /billing/checkout/ → create checkout session
  - POST /billing/portal/ → create portal session
  - DELETE /billing/subscription/ → cancel subscription
  WHY FIFTH: Controllers depend on schemas (Step 4) and services (Step 3).

Step 6: Webhook view registration
  - webhooks.py (stripe_webhook_view)
  - config/urls.py addition (comment-delimited block)
  WHY SIXTH: Depends on BillingService (Step 3) and adapter (Step 2).

Step 7: Auto-create signal
  - signals.py (post_save → create Customer)
  - apps.py BillingConfig.ready() registers signal
  WHY SEVENTH: Depends on Customer model (Step 1). Can be done after Step 1
    but placed here to avoid confusion with initial migration state.

Step 8: INSTALLED_APPS + auto_discover
  - Add "apps.billing" to INSTALLED_APPS
  - Run makemigrations + migrate
  WHY EIGHTH: Signals and controllers only need registration after all code exists.

Step 9: OpenAPI type regeneration
  - turbo generate:api-types
  - Commit updated openapi.json + gen/v1/types.d.ts
  WHY NINTH: Requires the Django API to be running with billing endpoints registered.

Step 10: Frontend billing pages
  - apps/web/app/(dashboard)/billing/page.tsx
  - apps/web/app/(dashboard)/billing/checkout/page.tsx
  - apps/web/app/(dashboard)/billing/success/page.tsx
  - apps/web/app/(dashboard)/billing/portal/page.tsx
  - apps/web/components/billing/*.tsx
  - packages/schemas/src/billing.ts
  WHY TENTH: Requires generated types (Step 9) and working API endpoints (Steps 5-8).

Step 11: CLI scaffolder integration
  - removeBillingModule() in create-foundation-app
  - Add billing to feature selection prompt
  WHY LAST: Scaffolder should only be extended after the module is stable.
```

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Stripe API calls in controllers

**What goes wrong:** Controllers import `stripe` directly and call `stripe.Customer.create()` inline.

**Why bad:** Cannot be unit-tested without real Stripe credentials. Cannot swap payment processor. Business logic leaks into the HTTP layer.

**Instead:** All Stripe calls go through `PaymentAdapter`. Controllers call `BillingService`, which calls the adapter. Controllers never import `stripe`.

### Anti-Pattern 2: Modifying the User model for billing fields

**What goes wrong:** Adding `stripe_customer_id` directly to `apps/accounts/models.py User(AbstractUser)`.

**Why bad:** Accounts app is auth-only. Billing fields in the User model make the billing module non-removable. The CLI scaffolder cannot cleanly strip fields from an AbstractUser subclass without risk.

**Instead:** OneToOne Customer model in `apps/billing/models.py`. Auto-created via signal.

### Anti-Pattern 3: Parsing request.body in a Ninja controller for webhooks

**What goes wrong:** Registering the webhook as a `@api_controller` endpoint and accessing `request.body`.

**Why bad:** Django Ninja processes the request body for JSON parsing. After Ninja reads it, `request.body` may be empty or already-decoded. Stripe signature verification requires raw bytes, causing `SignatureVerificationError` for all valid events.

**Instead:** Register as a plain Django view in `config/urls.py` with `@csrf_exempt`. Access `request.body` (raw bytes) directly. Delegate signature verification to the adapter.

### Anti-Pattern 4: Processing webhook events synchronously in the view

**What goes wrong:** Running all business logic (database updates, email sends) synchronously in `stripe_webhook_view()`. If this takes more than ~5 seconds, Stripe retries the webhook, causing duplicate processing.

**Instead:** For heavy webhook processing, dispatch a Celery task from the view and return 200 immediately. For lightweight operations (simple DB updates), synchronous processing in the service is fine. Add idempotency checks using `stripe_event_id` if needed.

### Anti-Pattern 5: Storing plan metadata in the Subscription model

**What goes wrong:** Adding fields like `plan_name`, `monthly_price`, `feature_limits` to the Subscription model.

**Why bad:** Plan metadata belongs in configuration (environment variables or a static `BILLING_PLANS` dict in settings), not in the database. Storing it creates synchronization problems when plans are updated in Stripe.

**Instead:** Keep Subscription lean: only `stripe_subscription_id`, `stripe_price_id`, `status`, and period dates. Resolve plan name and features at query time by mapping `stripe_price_id` to a `BILLING_PLANS` settings dict.

---

## Integration Points with Existing Codebase

| Existing element                        | How billing touches it                                         | Change required                               |
| --------------------------------------- | -------------------------------------------------------------- | --------------------------------------------- |
| `config/urls.py`                        | Adds webhook URL path + imports                                | ADD comment-delimited block before `api.urls` |
| `config/settings/base.py`               | Adds `"apps.billing"` to INSTALLED*APPS + 4 STRIPE*\* settings | ADD                                           |
| `apps/accounts/models.py`               | No changes                                                     | NONE — OneToOne from billing side             |
| `api.auto_discover_controllers()`       | Picks up BillingController automatically                       | NONE — already works                          |
| `packages/api-client/openapi.json`      | New billing endpoints appear after type regen                  | REGENERATE after Step 8                       |
| `packages/api-client/gen/v1/types.d.ts` | New billing types auto-generated                               | REGENERATE after Step 8                       |
| `apps/web/app/(dashboard)/layout.tsx`   | May need billing nav link                                      | ADD nav link                                  |
| CLI scaffolder feature selection        | New "Billing Module" checkbox                                  | ADD in Step 11                                |

---

## Sources

- Stripe webhook signature verification: [docs.stripe.com/webhooks/signature](https://docs.stripe.com/webhooks/signature) — HIGH confidence (official Stripe documentation)
- Stripe Python SDK v8 (StripeClient API): [github.com/stripe/stripe-python](https://github.com/stripe/stripe-python) — HIGH confidence (official SDK)
- Stripe webhook CSRF exemption requirement: [Django CSRF docs](https://docs.djangoproject.com/en/6.0/howto/csrf/), [Django Ninja CSRF docs](https://django-ninja.dev/reference/csrf/) — HIGH confidence
- Django OneToOne profile pattern for User extension: [Django documentation on customizing auth](https://docs.djangoproject.com/en/4.2/topics/auth/customizing/) — HIGH confidence
- Existing codebase: `apps/api/apps/ai/controllers.py`, `config/urls.py`, `config/settings/base.py`, `openspec/specs/foundation/cli-scaffolder.md` — HIGH confidence (direct inspection)
- Adam Johnson — building webhook receivers in Django: [adamj.eu/tech/2021/05/09/how-to-build-a-webhook-receiver-in-django/](https://adamj.eu/tech/2021/05/09/how-to-build-a-webhook-receiver-in-django/) — MEDIUM confidence (well-regarded, patterns are stable)

---

_Billing & Payments Architecture — Foundation Template_
_Researched: 2026-03-07_
