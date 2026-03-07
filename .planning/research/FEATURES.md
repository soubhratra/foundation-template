# Feature Research: Billing & Payments Module

**Domain:** Adapter-pattern billing module for full-stack SaaS template (subscriptions + one-time + usage-based)
**Researched:** 2026-03-07
**Confidence:** HIGH for Stripe specifics (official docs); MEDIUM for adapter interface patterns (community + training data cross-checked); MEDIUM for PDF generation (stable ecosystem, limited fresh sources)

---

## Context: What Already Exists

This module adds to an existing foundation. The following are pre-built and must NOT be re-implemented:

- `apps/api/` — Django Ninja Extra API, User model, auth (signup/login/logout/password reset), JWT/session tokens
- `apps/web/` — Next.js 15 App Router, dashboard shell, Shadcn/ui components, React Query, Zustand
- `apps/mobile/` — Expo SDK 53+ with auth screens, Expo Router
- `packages/shared-types/` — Auto-generated TypeScript types from Django OpenAPI spec
- `packages/api-client/` — Shared typed API client used by web and mobile

The billing module hooks into the existing `User` model (FK: `user.id` is the billing customer anchor) and the existing auth middleware (subscription gating uses the authenticated request context).

---

## Competitor Landscape: How Other Templates Handle Billing

| Template           | Approach                    | Adapter        | Swappable?           | Usage-Based   | PDF Invoices       |
| ------------------ | --------------------------- | -------------- | -------------------- | ------------- | ------------------ |
| SaaS Pegasus       | dj-stripe, direct           | No abstraction | No                   | Via dj-stripe | No (Stripe-hosted) |
| ShipFast (Next.js) | stripe-js + Stripe Checkout | No abstraction | LemonSqueezy variant | No            | No                 |
| Wasp OpenSaaS      | Direct Stripe SDK           | No abstraction | No                   | No            | No                 |
| Makerkit (Next.js) | Stripe + Lemon Squeezy      | Plugin pattern | Yes (2 providers)    | No            | No                 |
| Supastarter        | Stripe only                 | No abstraction | No                   | No            | No                 |

**Key observation:** No open-source SaaS template ships a true adapter pattern with swappable providers AND usage-based billing AND PDF invoices in the same module. This is the differentiator for this implementation.

---

## Part 1: PaymentAdapter Interface

### Design Decision: Python ABC Protocol Pattern

Use `Protocol` (structural subtyping) over `ABC` (nominal subtyping) for the adapter interface. This allows third-party adapters to satisfy the interface without inheriting from a base class — critical for swappability.

```python
# apps/api/billing/adapters/base.py
from typing import Protocol, runtime_checkable
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime


@dataclass
class CustomerResult:
    provider_customer_id: str    # e.g. "cus_ABC123"
    email: str
    metadata: dict


@dataclass
class SubscriptionResult:
    provider_subscription_id: str   # e.g. "sub_ABC123"
    provider_customer_id: str
    plan_id: str                    # internal plan identifier
    status: str                     # "active" | "trialing" | "past_due" | "canceled" | "paused"
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool
    trial_end: datetime | None
    metadata: dict


@dataclass
class PaymentResult:
    provider_payment_id: str        # e.g. "pi_ABC123" or "ch_ABC123"
    amount_cents: int
    currency: str                   # ISO 4217, e.g. "usd"
    status: str                     # "succeeded" | "pending" | "failed"
    receipt_url: str | None
    metadata: dict


@dataclass
class InvoiceResult:
    provider_invoice_id: str
    provider_customer_id: str
    provider_subscription_id: str | None
    amount_due_cents: int
    amount_paid_cents: int
    currency: str
    status: str                     # "draft" | "open" | "paid" | "uncollectible" | "void"
    invoice_url: str | None         # hosted invoice page (provider-hosted)
    pdf_url: str | None             # provider-hosted PDF (if available)
    period_start: datetime
    period_end: datetime
    line_items: list[dict]          # [{description, amount_cents, quantity}]
    created_at: datetime


@dataclass
class CheckoutSessionResult:
    session_id: str
    checkout_url: str               # redirect user here to complete payment
    expires_at: datetime | None


@dataclass
class UsageRecordResult:
    provider_usage_record_id: str
    quantity: int
    timestamp: datetime
    meter_id: str | None            # Stripe meter ID (new API) or subscription item ID (legacy)


@runtime_checkable
class PaymentAdapterProtocol(Protocol):
    """
    Defines the contract all payment provider adapters must satisfy.
    Stripe is the default implementation. LemonSqueezy, Paddle, etc. can be dropped in.
    All methods are synchronous at the interface level; async variants wrap these.
    """

    # --- Customer lifecycle ---
    def create_customer(
        self,
        user_id: str,
        email: str,
        name: str | None = None,
        metadata: dict | None = None,
    ) -> CustomerResult: ...

    def get_customer(self, provider_customer_id: str) -> CustomerResult: ...

    def update_customer(
        self,
        provider_customer_id: str,
        email: str | None = None,
        name: str | None = None,
        metadata: dict | None = None,
    ) -> CustomerResult: ...

    def delete_customer(self, provider_customer_id: str) -> bool: ...

    # --- Subscription management ---
    def create_subscription(
        self,
        provider_customer_id: str,
        plan_id: str,               # internal plan ID mapped to provider price ID
        trial_days: int = 0,
        metadata: dict | None = None,
    ) -> SubscriptionResult: ...

    def get_subscription(self, provider_subscription_id: str) -> SubscriptionResult: ...

    def upgrade_subscription(
        self,
        provider_subscription_id: str,
        new_plan_id: str,           # internal plan ID
        prorate: bool = True,
    ) -> SubscriptionResult: ...

    def downgrade_subscription(
        self,
        provider_subscription_id: str,
        new_plan_id: str,
        prorate: bool = True,
    ) -> SubscriptionResult: ...

    def cancel_subscription(
        self,
        provider_subscription_id: str,
        at_period_end: bool = True, # True = cancel at end of billing period; False = immediate
    ) -> SubscriptionResult: ...

    def reactivate_subscription(
        self,
        provider_subscription_id: str,
    ) -> SubscriptionResult: ...

    # --- Checkout sessions (hosted payment page) ---
    def create_checkout_session(
        self,
        provider_customer_id: str,
        plan_id: str | None = None,     # None for one-time payments
        amount_cents: int | None = None, # for one-time payments
        currency: str = "usd",
        success_url: str = "",
        cancel_url: str = "",
        mode: str = "subscription",     # "subscription" | "payment"
        metadata: dict | None = None,
    ) -> CheckoutSessionResult: ...

    # --- Customer portal (redirect to provider-hosted management UI) ---
    def create_customer_portal_session(
        self,
        provider_customer_id: str,
        return_url: str = "",
    ) -> str: ...                       # returns redirect URL

    # --- One-time charges ---
    def create_payment_intent(
        self,
        provider_customer_id: str,
        amount_cents: int,
        currency: str = "usd",
        description: str | None = None,
        metadata: dict | None = None,
    ) -> PaymentResult: ...

    # --- Usage-based billing (metered) ---
    def record_usage(
        self,
        provider_customer_id: str,
        meter_id: str,              # Stripe meter ID or equivalent
        quantity: int,
        timestamp: datetime | None = None,
        idempotency_key: str | None = None,
    ) -> UsageRecordResult: ...

    def get_usage_summary(
        self,
        provider_customer_id: str,
        meter_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> dict: ...                  # {total_quantity, unit_amount_cents, currency}

    # --- Invoices ---
    def list_invoices(
        self,
        provider_customer_id: str,
        limit: int = 20,
        starting_after: str | None = None,  # cursor-based pagination
    ) -> list[InvoiceResult]: ...

    def get_invoice(self, provider_invoice_id: str) -> InvoiceResult: ...

    def download_invoice_pdf(self, provider_invoice_id: str) -> bytes: ...
    # Returns raw PDF bytes. Adapter fetches from provider or generates locally.

    # --- Webhook verification ---
    def construct_webhook_event(
        self,
        payload: bytes,
        signature_header: str,
        webhook_secret: str,
    ) -> dict: ...
    # Returns parsed, verified event dict. Raises ValueError on invalid signature.
```

**Confidence:** MEDIUM. This interface is derived from community patterns and Stripe's documented API surface. The exact method signatures are opinionated choices, not established standards. They are designed to be comprehensive enough for Stripe while not being Stripe-specific.

---

## Part 2: Table Stakes vs. Differentiators by Payment Type

### 2a. Subscriptions

**Table Stakes** — Missing any of these makes the module feel incomplete.

| Feature                          | Why Expected                                                                           | Complexity | Implementation Notes                                                                                                                         |
| -------------------------------- | -------------------------------------------------------------------------------------- | ---------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| Create subscription via Checkout | Users expect a hosted, PCI-compliant payment page                                      | LOW        | Stripe Checkout in `subscription` mode. Store `checkout_session_id` until `checkout.session.completed` webhook arrives.                      |
| Active/inactive access gating    | Auth middleware must check subscription status before granting access to paid features | MEDIUM     | Django middleware or decorator reads `UserBillingProfile.subscription_status`. Must handle `trialing`, `past_due`, `active`.                 |
| Upgrade plan                     | Users can move to a higher tier                                                        | MEDIUM     | `stripe.Subscription.modify()` with `proration_behavior="create_prorations"`. Amount charged immediately or at next billing date per config. |
| Downgrade plan                   | Users can move to a lower tier                                                         | MEDIUM     | Same API as upgrade; downgrade takes effect at end of current period by convention.                                                          |
| Cancel subscription              | Users can cancel                                                                       | LOW        | `cancel_at_period_end=True` by default. User retains access until period ends.                                                               |
| Reactivate before period end     | Users who cancel can undo cancellation during grace period                             | LOW        | Remove `cancel_at_period_end` flag.                                                                                                          |
| Trial period support             | Free trials are universal SaaS onboarding                                              | LOW        | `trial_period_days` param at subscription creation. Webhook `customer.subscription.trial_will_end` fires 3 days before.                      |
| Show current plan + renewal date | Dashboard must display what tier user is on                                            | LOW        | Stored locally in `UserBillingProfile`; refreshed on webhook events.                                                                         |
| Invoice history list             | Users must be able to see past charges                                                 | LOW        | List from local `Invoice` model (synced via webhooks) or fetched from provider.                                                              |

**Differentiators** — Not universally expected; adds real value.

| Feature                                     | Value                                                        | Complexity | Notes                                                                                                                   |
| ------------------------------------------- | ------------------------------------------------------------ | ---------- | ----------------------------------------------------------------------------------------------------------------------- |
| Proration preview before confirming upgrade | Show "You will be charged $X today" before committing        | MEDIUM     | `stripe.Invoice.create_preview()` API. Frontend calls preview endpoint, user confirms, then upgrade fires.              |
| Pause subscription                          | Pause billing without canceling (Stripe: `pause_collection`) | MEDIUM     | Sets subscription to collect nothing; resumes on specified date or manual reactivation. Not all providers support this. |
| Seat-based subscription                     | N seats, each seat billed                                    | HIGH       | Requires quantity tracking on subscription items. Product-specific; template can scaffold but not pre-wire logic.       |

### 2b. One-Time Payments

**Table Stakes**

| Feature                       | Why Expected                                        | Complexity | Notes                                                                                                                     |
| ----------------------------- | --------------------------------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------- |
| Checkout for one-time product | Pay once, unlock feature or digital good            | LOW        | Stripe Checkout `payment` mode. `checkout.session.completed` webhook signals fulfillment.                                 |
| Receipt / invoice             | User expects email receipt and downloadable invoice | LOW        | Stripe generates automatically. Expose `receipt_url` from `PaymentIntent`.                                                |
| Payment history               | Show all one-time purchases                         | LOW        | Local `Payment` model records each successful `payment_intent.succeeded` event.                                           |
| Idempotency on retries        | Prevent double charges on network errors            | MEDIUM     | Pass `idempotency_key` on all charge creation calls. Key = deterministic hash of `(user_id, product_id, timestamp_hour)`. |

**Differentiators**

| Feature                         | Value                                                         | Complexity | Notes                                                                                                                                                               |
| ------------------------------- | ------------------------------------------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Refund management               | Admin can issue full or partial refunds                       | MEDIUM     | `stripe.Refund.create(payment_intent=..., amount=...)`. Webhook `charge.refunded` updates local record. Template should scaffold; product adds refund policy logic. |
| Payment link (no-code checkout) | Generate shareable payment URL without a custom checkout page | LOW        | Stripe Payment Links. Adapter exposes `create_payment_link()`. Useful for simple products.                                                                          |

### 2c. Usage-Based Billing

**Table Stakes**

| Feature                         | Why Expected                                         | Complexity | Notes                                                                                                                                 |
| ------------------------------- | ---------------------------------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| Record usage events             | Core requirement for metered billing                 | MEDIUM     | POST to Stripe Meter Events API v2 (legacy `UsageRecord` API removed in Stripe `2025-03-31.basil`). Must use new meter-backed prices. |
| Usage summary display           | Users want to know what they will be billed          | MEDIUM     | Query `stripe.billing.MeterEventSummary` or local aggregation. Show current period usage vs. included amount.                         |
| Meter ID configuration per plan | Different plans may have different meter definitions | MEDIUM     | Map `plan_id → [meter_ids]` in Django settings or a `Plan` model. Template scaffolds the config structure.                            |
| Usage invoice line items        | Invoice must show per-meter usage breakdown          | LOW        | Stripe handles this on the invoice object if meters are correctly configured. Local `Invoice` model stores `line_items`.              |

**Differentiators**

| Feature                         | Value                                                          | Complexity | Notes                                                                                                                                          |
| ------------------------------- | -------------------------------------------------------------- | ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| Hybrid pricing (flat + metered) | Charge base fee + per-unit overage                             | HIGH       | Stripe supports this via multiple subscription items (one fixed price, one metered price). Requires `subscription_item_id` tracking per meter. |
| Usage event batching            | High-volume products send millions of usage events; batch them | HIGH       | Stripe Meter Event Streams API v2 supports 10k events/sec. Template can scaffold a Celery task that batches and flushes. Out of scope for MVP. |
| Spending cap / alerts           | Warn user when usage is approaching limit                      | HIGH       | Not natively supported by Stripe as of 2025-03; requires custom aggregation logic and notification system. Out of scope for template.          |

---

## Part 3: Webhook Event Handling

### Structure in Django

The webhook endpoint must be a Django Ninja Extra view. Processing happens in two stages:

1. **Receive and verify** — fast, synchronous, returns 200 immediately
2. **Process** — async via task queue (Celery or Django-Q2), never in the request cycle

```
POST /api/billing/webhooks/stripe/
    ↓
Signature verification (adapter.construct_webhook_event)
    ↓
Store raw event in BillingWebhookEvent model (status=PENDING)
    ↓
Return HTTP 200
    ↓ (async)
Task queue picks up event
    ↓
Idempotency check: event.id already processed? → skip
    ↓
Route to handler by event.type
    ↓
Update local models (UserBillingProfile, Subscription, Invoice, Payment)
    ↓
Mark BillingWebhookEvent status=PROCESSED or FAILED
```

**Critical:** Webhook handler MUST be exempt from CSRF middleware. Use `@csrf_exempt` or configure in Django Ninja Extra router settings.

### Event Taxonomy

**Tier 1 — Essential (must handle; access control breaks without these)**

| Event                           | What to Do                                                                                                         | Notes                                                                                                                     |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------- |
| `checkout.session.completed`    | Activate subscription or fulfill one-time payment. Link Stripe customer to user. Set `subscription_status=active`. | Primary activation event. Contains `customer`, `subscription`, `payment_intent`. Always check `payment_status == "paid"`. |
| `customer.subscription.created` | Record subscription to local DB. Set `subscription_status=active` (or `trialing`).                                 | May fire after `checkout.session.completed` — idempotency required.                                                       |
| `customer.subscription.updated` | Sync plan change, status change, `cancel_at_period_end`. Update `UserBillingProfile`.                              | Fires on upgrade, downgrade, pause, reactivation, trial conversion. Check `status` and `cancel_at_period_end` fields.     |
| `customer.subscription.deleted` | Set `subscription_status=canceled`. Revoke feature access at period end or immediately.                            | Fires when subscription ends (after `cancel_at_period_end` period expires).                                               |
| `invoice.payment_succeeded`     | Mark invoice as paid locally. Extend subscription access through next period.                                      | Fires on every successful recurring charge. Update `current_period_end`.                                                  |
| `invoice.payment_failed`        | Set `subscription_status=past_due`. Trigger dunning email (product-specific).                                      | Stripe retries automatically per Smart Retries config. Template logs failure; product adds email.                         |

**Tier 2 — Important (needed for good UX; degraded experience without these)**

| Event                                  | What to Do                                                                            | Notes                                                                                                       |
| -------------------------------------- | ------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| `invoice.created`                      | Store draft invoice locally before it is finalized. Enables upcoming invoice preview. | Fires 1 hour before upcoming subscription renewal. Can be used to surface "your next invoice" in dashboard. |
| `invoice.finalized`                    | Update local invoice to `finalized` status.                                           | Invoice is now locked; cannot be modified. Safe to show to user.                                            |
| `customer.subscription.trial_will_end` | Trigger trial-expiry notification (3 days before end).                                | Product adds email; template logs the event.                                                                |
| `payment_intent.succeeded`             | Record one-time payment as succeeded. Update `Payment` model.                         | Distinct from invoice payments. Relevant for one-time charges.                                              |
| `payment_intent.payment_failed`        | Record payment failure.                                                               | Log for support purposes.                                                                                   |

**Tier 3 — Optional (nice to have; add as product requires)**

| Event                          | What to Do                                            | Notes                                                          |
| ------------------------------ | ----------------------------------------------------- | -------------------------------------------------------------- |
| `customer.updated`             | Sync email or name changes from Stripe back to local. | Useful if users update billing info in Stripe Customer Portal. |
| `charge.refunded`              | Mark payment as refunded locally.                     | Handle in refund flow.                                         |
| `billing.meter.no_meter_found` | Log error; meter misconfiguration.                    | Relevant for usage-based setups.                               |
| `invoice.upcoming`             | Future invoice preview notification (7 days ahead).   | Same as `invoice.created` but earlier signal.                  |

### Idempotency Pattern

Store processed event IDs in `BillingWebhookEvent.provider_event_id`. Before processing:

```python
if BillingWebhookEvent.objects.filter(
    provider_event_id=event["id"],
    status=WebhookEventStatus.PROCESSED
).exists():
    return  # already handled
```

A single subscription upgrade can fire 4–6 events in sequence (`customer.subscription.updated`, `invoice.created`, `invoice.finalized`, `invoice.payment_succeeded`, `payment_intent.succeeded`). All must be handled idempotently.

---

## Part 4: Minimal Billing Frontend

### Design Decision: Stripe Customer Portal for Management, Custom for Display

**Rationale:** Stripe's hosted Customer Portal handles payment method updates, cancellation, and invoice downloads with zero custom code. Building these in-house is a maintenance burden with no competitive advantage for a template. The custom frontend covers only what the portal cannot: plan display, usage display, and in-app upgrade flow.

**What to build custom:**

| Page/Component                              | Purpose                                      | Key Data                                               | Notes                                                          |
| ------------------------------------------- | -------------------------------------------- | ------------------------------------------------------ | -------------------------------------------------------------- |
| `/billing` — Billing Overview page          | Central billing hub                          | Current plan name, status, renewal date, usage summary | Single page, not a separate app section                        |
| `<PlanCard>` component                      | Show plan details and included features      | `plan_name`, `price`, `features[]`, `is_current`       | Used in both billing page and upgrade modal                    |
| `<PlanGrid>` component                      | Compare available plans side-by-side         | All plans from API                                     | Used in upgrade/downgrade flow                                 |
| `<UpgradeModal>` component                  | Confirm plan change with proration preview   | `current_plan`, `new_plan`, `proration_preview`        | Opens inline; calls `PATCH /api/billing/subscription/`         |
| `<CurrentPlanBadge>` component              | Show plan tier in nav/sidebar                | `plan_name`, `status`                                  | Small UI affordance in the existing dashboard shell            |
| `<InvoiceHistoryTable>` component           | List past invoices with download links       | `invoice[]`, paginated                                 | Reads from `/api/billing/invoices/` endpoint                   |
| Stripe Customer Portal redirect button      | "Manage billing" → redirect to Stripe portal | `portal_url` from `/api/billing/portal-session/`       | One API call + window.location redirect; zero custom portal UI |
| `<UsageMeter>` component (usage-based only) | Show current period usage vs. limit          | `meter_name`, `used`, `limit`, `unit`                  | Optional; rendered only when plan has metered component        |
| Cancel confirmation modal                   | Confirm cancellation; warn about access loss | `period_end` date                                      | Calls `DELETE /api/billing/subscription/` endpoint             |

**What NOT to build (delegate to Stripe Customer Portal):**

- Payment method update form (PCI-sensitive, Stripe handles)
- Invoice PDF download UI (Stripe Customer Portal has this)
- Billing address form
- Tax ID management
- Full cancellation flow with retention offers (unless product-specific)

**Mobile (Expo):**

Billing is NOT required on mobile in the template. The template should render a "Manage billing on web" screen that deep-links to the web `/billing` page. Building subscription management in a React Native app requires App Store / Play Store compliance (Apple/Google require in-app purchases for digital goods sold in apps), which is product-specific and outside template scope.

---

## Part 5: PDF Invoice Generation

### Data Model Requirements

The `Invoice` model must contain all data needed to render a PDF without additional API calls:

```python
# apps/api/billing/models.py (relevant fields)
class Invoice(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    provider_invoice_id = models.CharField(max_length=255, unique=True)
    provider_customer_id = models.CharField(max_length=255)

    # Amounts
    amount_due_cents = models.IntegerField()
    amount_paid_cents = models.IntegerField()
    currency = models.CharField(max_length=3, default="usd")

    # Metadata
    invoice_number = models.CharField(max_length=100, blank=True)  # human-readable
    status = models.CharField(max_length=50)
    description = models.TextField(blank=True)

    # Dates
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    created_at = models.DateTimeField()
    due_date = models.DateTimeField(null=True)

    # Line items (stored as JSON for flexibility)
    line_items = models.JSONField(default=list)
    # [{description, quantity, unit_amount_cents, amount_cents, period_start, period_end}]

    # Provider URLs (fallback if local PDF fails)
    provider_invoice_url = models.URLField(blank=True)
    provider_pdf_url = models.URLField(blank=True)

    # Local PDF cache
    pdf_generated_at = models.DateTimeField(null=True)
    # Store PDF as file OR generate on demand
```

**Business entity data** (company name, address, tax ID) for the invoice header must come from a separate `BillingSettings` model or Django settings, not from the User model. This is product-specific configuration.

### Recommended Stack: WeasyPrint + Jinja2

**Decision:** Use WeasyPrint (HTML → PDF) over ReportLab (programmatic PDF).

**Why WeasyPrint:**

- HTML/CSS templates are easier to maintain and design than programmatic PDF layout code
- Designers can style invoices without learning ReportLab's API
- Produces high-quality PDFs matching the app's visual style
- Active development in 2025; good Django integration via `django-weasyprint`

**Why not ReportLab:**

- Programmatic layout is verbose and hard to maintain for complex documents
- ReportLab's open-source version (reportlab) has commercial-use restrictions on some features
- HTML template approach is more accessible for the template's target user (solo entrepreneur)

**Why not Stripe-hosted PDF:**

- Stripe's hosted invoice PDFs don't have the company's branding
- PDF URL expires; not suitable for long-term storage
- Cannot customize line item descriptions, add custom fields, or add the user's company logo

**Implementation pattern:**

```python
# apps/api/billing/services/pdf_service.py
from django.template.loader import render_to_string
import weasyprint

def generate_invoice_pdf(invoice: Invoice) -> bytes:
    html_string = render_to_string(
        "billing/invoice.html",
        {
            "invoice": invoice,
            "line_items": invoice.line_items,
            "company_name": settings.BILLING_COMPANY_NAME,
            "company_address": settings.BILLING_COMPANY_ADDRESS,
            "company_tax_id": settings.BILLING_COMPANY_TAX_ID,
        }
    )
    pdf_bytes = weasyprint.HTML(string=html_string).write_pdf()
    return pdf_bytes
```

**Template location:** `apps/api/billing/templates/billing/invoice.html`
**CSS:** Minimal print-optimized stylesheet embedded or linked. Use `@page` CSS rule for margins.

**Caching strategy:** Generate on first download request; cache as `InvoiceFile` model (FileField) or in an S3 bucket. Do not regenerate on every request. Invalidate cache if `Invoice.line_items` changes (should not happen for finalized invoices).

---

## Part 6: Anti-Features

Features to explicitly NOT build in the billing template module.

| Anti-Feature                                                              | Why Requested                                                          | Why to Avoid                                                                                                                                                                                                                          | What to Do Instead                                                                                                                                                   |
| ------------------------------------------------------------------------- | ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Direct Stripe SDK calls in views/endpoints**                            | "Just use stripe.Subscription.create()" is the first tutorial you find | Hardwires Stripe everywhere; swapping providers requires rewriting every endpoint                                                                                                                                                     | All Stripe calls go through the `StripeAdapter` class. Views call `billing_service.create_subscription()`, not Stripe SDK directly.                                  |
| **dj-stripe as the persistence layer**                                    | dj-stripe syncs Stripe objects to Django models automatically          | dj-stripe syncs ALL Stripe objects (Products, Prices, Customers, PaymentMethods, ...) to local DB — far more than needed, adds migration complexity, and breaks the adapter pattern (dj-stripe IS the Stripe coupling)                | Custom `Invoice`, `Subscription`, `Payment` models containing only the fields the app actually needs. Webhooks keep them in sync.                                    |
| **Full custom billing management UI (payment forms, address forms)**      | "Own the billing experience"                                           | PCI compliance scope increases significantly with custom payment forms. Maintenance burden is high. Stripe Customer Portal handles this correctly for free.                                                                           | Redirect to Stripe Customer Portal for management. Build only plan display + upgrade flow in-app.                                                                    |
| **Webhook processing in the request handler (synchronous)**               | Simpler code                                                           | Webhook processing takes time; Stripe expects a 200 response within seconds; slow processing causes Stripe to retry, causing duplicate events                                                                                         | Store event in DB immediately, return 200, process via task queue (Celery/Django-Q2).                                                                                |
| **Storing raw Stripe webhook payloads in DB indefinitely**                | Debug convenience                                                      | Webhook payloads can contain PII (customer email, last 4 digits, etc.). Long-term retention of raw payloads is a GDPR/CCPA liability.                                                                                                 | Store event ID, type, and status. Store raw payload only in a TTL-limited field (e.g., `raw_payload` purged after 30 days). Log to structured logging for debugging. |
| **Building a multi-currency display without a currency conversion layer** | Looks international                                                    | Stripe amounts are in the currency the subscription was created in. Showing "€10" when the subscription is in USD requires real-time FX rates. This is a product-specific complexity.                                                 | Store and display amounts in the invoice's native currency (`invoice.currency`). Formatting is sufficient (show "USD $10.00").                                       |
| **Plan definitions hardcoded in code**                                    | Simple to start                                                        | When prices change (always), requires code deploy. Plans need to be in sync with Stripe Price IDs.                                                                                                                                    | Plan definitions in a `Plan` model or in Django settings as a dict. Map `plan_id → stripe_price_id`. Plans are configured per-product in `settings.BILLING_PLANS`.   |
| **Coupling subscription status to Django `is_active` user flag**          | "If they don't pay, deactivate the account"                            | Deactivating the user blocks login, preventing them from updating payment method and fixing past-due status                                                                                                                           | Separate `subscription_status` field on `UserBillingProfile`. Middleware checks this field; user login (auth) is unaffected.                                         |
| **Mobile in-app subscription management via Apple/Google IAP**            | "Native feel on mobile"                                                | Apple/Google mandate in-app purchases (with their 15-30% cut) for digital subscriptions sold in apps. Stripe cannot be used for App Store subscriptions on iOS. This is a legal requirement and product decision, not template scope. | Mobile app shows "Manage billing on web" and links to the web app. Template does not scaffold IAP.                                                                   |
| **Grandfathering / legacy plan migration logic**                          | "Handle existing users when pricing changes"                           | Plan migration logic is deeply product-specific (who gets grandfathered, for how long, what features change) and cannot be genericized in a template                                                                                  | Template provides no grandfathering scaffolding. Document the Stripe migration flow in `docs/billing-plans.md`.                                                      |

---

## Feature Dependencies

```
[Existing User model + Auth system]
    |
    +---> [UserBillingProfile model]  (FK: user, stores provider_customer_id, subscription_status)
    |         |
    |         +---> [PaymentAdapterProtocol] (injected at runtime via Django settings)
    |         |         |
    |         |         +---> [StripeAdapter] (default)
    |         |         +---> [LemonSqueezyAdapter] (future)
    |         |
    |         +---> [BillingService] (business logic, calls adapter)
    |                   |
    |                   +---> [Subscription model]
    |                   +---> [Invoice model]
    |                   +---> [Payment model]
    |                   +---> [BillingWebhookEvent model] (idempotency log)
    |
    +---> [Django Ninja Extra API endpoints]
    |         |
    |         +---> POST /api/billing/checkout-session/
    |         +---> POST /api/billing/portal-session/
    |         +---> GET  /api/billing/subscription/
    |         +---> PATCH /api/billing/subscription/   (upgrade/downgrade)
    |         +---> DELETE /api/billing/subscription/ (cancel)
    |         +---> POST /api/billing/usage/
    |         +---> GET  /api/billing/invoices/
    |         +---> GET  /api/billing/invoices/{id}/pdf/
    |         +---> POST /api/billing/webhooks/stripe/  (CSRF exempt)
    |
    +---> [Webhook Handler]
    |         |
    |         +---> [Task Queue] (Celery/Django-Q2)
    |                   |
    |                   +---> Updates Subscription, Invoice, Payment, UserBillingProfile
    |
    +---> [PDF Generation Service]  (WeasyPrint + Jinja2 template)
    |
    +---> [OpenAPI Spec → packages/shared-types/] (billing types auto-generated)
    |
    +---> [Frontend: apps/web/]
              |
              +---> /billing page
              +---> <PlanGrid>, <PlanCard>, <UpgradeModal>
              +---> <InvoiceHistoryTable>
              +---> <UsageMeter> (conditional)
              +---> "Manage billing" → Stripe Portal redirect
```

### Dependency Notes

- **`UserBillingProfile` is the billing anchor:** Created lazily when a user first interacts with billing (not at signup). FK to `User`. Contains `provider_customer_id`. Without this, no billing operation can proceed.
- **`PaymentAdapterProtocol` must be injectable:** Resolved at runtime from `settings.BILLING_ADAPTER_CLASS`. `BillingService` receives the adapter via constructor injection (not `from apps.billing.adapters.stripe import StripeAdapter` directly).
- **Webhook endpoint must exist before any Stripe testing:** Stripe requires a reachable webhook endpoint to deliver events. Use Stripe CLI (`stripe listen --forward-to`) in local dev to proxy events to `localhost`.
- **`packages/shared-types/` must be regenerated after adding billing endpoints:** The billing endpoints must expose typed schemas. TypeScript types flow automatically from Django Ninja schemas.
- **Task queue must be configured before webhook processing works:** Webhook handler enqueues tasks. If task queue is not running, events pile up unprocessed. Billing module docs must note this operational dependency.
- **PDF invoice depends on `Invoice.line_items` being populated:** `line_items` is populated by the `invoice.finalized` webhook event. If the webhook is not handled, `line_items` is empty, and the PDF is incomplete.

---

## MVP Definition for Billing Module

### Must Have (Milestone Launch)

- [ ] `UserBillingProfile` model + migration
- [ ] `Subscription`, `Invoice`, `Payment`, `BillingWebhookEvent` models
- [ ] `PaymentAdapterProtocol` interface
- [ ] `StripeAdapter` implementing the full protocol
- [ ] `BillingService` with business logic methods
- [ ] Django Ninja Extra endpoints: checkout session, portal session, subscription CRUD, invoice list, invoice PDF
- [ ] Webhook endpoint with signature verification + async task queue dispatch
- [ ] Tier 1 webhook event handlers (6 essential events)
- [ ] Subscription access gating middleware/decorator (`@require_active_subscription`)
- [ ] `Plan` configuration in Django settings (`BILLING_PLANS` dict)
- [ ] `/billing` page in Next.js with `<PlanGrid>`, `<CurrentPlanBadge>`, `<InvoiceHistoryTable>`
- [ ] `<UpgradeModal>` with proration preview
- [ ] Stripe Customer Portal redirect button
- [ ] PDF invoice generation via WeasyPrint + base invoice HTML template
- [ ] Stripe CLI development setup docs

### Defer to Post-MVP

- [ ] Usage-based billing endpoints and `<UsageMeter>` UI (add when first product needs it)
- [ ] Tier 2/3 webhook handlers (good UX but not blocking)
- [ ] Refund management admin UI
- [ ] PDF caching to file storage (serve on demand first)
- [ ] LemonSqueezy adapter (second adapter; validate protocol design with Stripe first)
- [ ] Pause subscription support
- [ ] Proration calculation preview (UX enhancement)

---

## Sources

- [Stripe Billing Subscriptions Webhooks — Stripe Documentation](https://docs.stripe.com/billing/subscriptions/webhooks) (HIGH confidence — official docs)
- [Record usage for billing with the API — Stripe Documentation](https://docs.stripe.com/billing/subscriptions/usage-based/recording-usage-api) (HIGH confidence — official docs)
- [Usage-based billing — Stripe Documentation](https://docs.stripe.com/billing/subscriptions/usage-based) (HIGH confidence — official docs)
- [Stripe API v2 Meter Events — Stripe API Reference](https://docs.stripe.com/api/v2/billing-meter) (HIGH confidence — official docs)
- [Removes legacy usage-based billing — Stripe Changelog 2025-03-31](https://docs.stripe.com/changelog/basil/2025-03-31/deprecate-legacy-usage-based-billing) (HIGH confidence — official changelog)
- [Stripe Customer Management / Portal — Stripe Documentation](https://docs.stripe.com/customer-management) (HIGH confidence — official docs)
- [Integrate the customer portal with the API — Stripe Documentation](https://docs.stripe.com/customer-management/integrate-customer-portal) (HIGH confidence — official docs)
- [dj-stripe — Django Stripe Integration](https://dj-stripe.dev/) (MEDIUM confidence — official library docs; decision to NOT use dj-stripe is based on adapter pattern constraints)
- [Integrating Stripe Billing with Django 6.0: Async Webhooks, Prorations, and Idempotency Best Practices — Django Journal](https://medium.com/django-journal/integrating-stripe-billing-with-django-6-0-333aa65cf1e6) (MEDIUM confidence — community article, Django 6.0 context)
- [dj-stripe GitHub — dj-stripe/dj-stripe](https://github.com/dj-stripe/dj-stripe) (MEDIUM confidence — open source repo, widely used)
- [Create An Invoice Generator Using Python, Jinja2 & WeasyPrint — Medium](https://medium.com/@hammad.ai/create-an-invoice-generator-using-python-jinja2-weasyprint-48ef1f450ac5) (MEDIUM confidence — pattern article)
- [Stripe Webhooks Complete Guide — MagicBell](https://www.magicbell.com/blog/stripe-webhooks-guide) (MEDIUM confidence — community guide)
- [Implementing Paddle Payments for Django SaaS — tkainrad.dev](https://tkainrad.dev/posts/implementing-paddle-payments-for-my-django-saas/) (MEDIUM confidence — practitioner blog)
- [Architecture Patterns for SaaS Platforms: Billing, RBAC, Onboarding — Medium/Appfoster](https://medium.com/appfoster/architecture-patterns-for-saas-platforms-billing-rbac-and-onboarding-964ea071f571) (LOW confidence — general architecture article, no specific version verification)
- Python `abc` module and `Protocol` — stdlib documentation (HIGH confidence)

---

_Feature research for: Billing & Payments Module (foundation-template, subsequent milestone)_
_Researched: 2026-03-07_
