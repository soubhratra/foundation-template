# Domain Pitfalls: Billing & Payments Module

**Domain:** Adding a billing/payments module to an existing Django + Next.js SaaS template
**Researched:** 2026-03-07
**Confidence:** MEDIUM-HIGH (WebSearch verified; training data corroborated by current community sources. Stripe-specific claims verified against Stripe documentation patterns. WeasyPrint specifics corroborated by GitHub issues and 2025 community posts.)

---

## Critical Pitfalls

Mistakes that cause rewrites, incorrect billing, or irreversible data loss.

---

### Pitfall 1: PaymentAdapter Abstraction That Leaks Stripe Concepts

**What goes wrong:**
The adapter ABC is designed to hide provider details, but Stripe-specific concepts bleed into the shared interface. The most common forms:

1. **Stripe status strings in the interface.** The abstract method returns a `status` field typed as `Literal["requires_payment_method", "requires_action", "succeeded"]` — these are Stripe PaymentIntent statuses. When you add a second provider, these literals are meaningless.

2. **Stripe customer ID on the user model.** `user.stripe_customer_id` is added to the User model directly. A second provider would require `user.paypal_customer_id`. The model cannot be cleaned up without a migration.

3. **Provider webhook payload exposed to service layer.** The webhook handler calls `adapter.process_webhook(stripe_event)` and passes the raw Stripe event object downstream. The service layer ends up `isinstance`-checking for Stripe types.

4. **Price/Plan IDs are Stripe price IDs.** The adapter interface has `create_subscription(price_id: str)` where `price_id` means a Stripe price ID (`price_abc123`). No other provider uses the same ID format.

**Why it happens:**
The first implementation is Stripe. It is tempting to write the interface to match what Stripe needs, then "abstract it later." Later never comes.

**Prevention:**
Define the interface in terms of your domain, not Stripe's:

```python
# GOOD: Domain-centric adapter interface
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

class PaymentStatus(Enum):
    PENDING = "pending"
    REQUIRES_ACTION = "requires_action"   # SCA/3DS
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"

@dataclass
class PaymentResult:
    status: PaymentStatus
    provider_reference: str            # Opaque to the service layer
    client_secret: str | None = None   # For frontend action (3DS, etc.)
    action_url: str | None = None      # Redirect URL if required

class PaymentAdapter(ABC):
    @abstractmethod
    def create_customer(self, user_id: int, email: str) -> str:
        """Returns an opaque provider_customer_id string."""
        ...

    @abstractmethod
    def create_subscription(
        self,
        provider_customer_id: str,
        plan_key: str,           # Your internal plan key, NOT a Stripe price ID
        trial_days: int = 0,
    ) -> PaymentResult:
        ...

    @abstractmethod
    def cancel_subscription(
        self,
        provider_subscription_id: str,
        at_period_end: bool = True,
    ) -> None:
        ...

    @abstractmethod
    def parse_webhook(self, payload: bytes, signature: str) -> "WebhookEvent":
        """Returns a provider-agnostic WebhookEvent, NOT a raw Stripe object."""
        ...
```

Keep `stripe_customer_id` in a separate `BillingProfile` model (not on `User`). The `BillingProfile` model is part of the billing module; removing the module removes this model cleanly.

**Warning signs:**

- The word "stripe" appears in a method signature on the abstract base class
- Service layer code imports `stripe` directly (not via the adapter)
- A `stripe_*` field on the User model or any model outside `apps/billing/`
- `isinstance(event, stripe.Event)` anywhere outside `StripeAdapter`

**Phase to address:** Billing Phase 1 (Adapter scaffolding). The interface must be locked before any implementation begins.

**Recovery cost:** HIGH — changing the interface after both adapter and service layers are built requires touching every call site.

**Confidence:** HIGH

---

### Pitfall 2: Webhook Processing Without Idempotency Guard

**What goes wrong:**
Stripe retries webhooks when your endpoint returns a non-2xx response or times out (up to 3 days, exponential backoff). Without an idempotency guard:

1. A slow database write causes a timeout. Stripe retries. The subscription is created twice.
2. A deploy restarts the server mid-webhook. Stripe retries. The user is double-charged or their plan is toggled off then on.
3. Two concurrent webhook deliveries for the same event arrive due to Stripe's at-least-once guarantee. Both handlers run simultaneously and create duplicate records.

The race condition in case 3 is subtle: both handlers check "has this event been processed?" at the same moment, both get `False`, both proceed, and both write.

**Prevention:**

Use a `ProcessedWebhookEvent` model with a unique constraint on `stripe_event_id`, and use `get_or_create` in an atomic transaction:

```python
# apps/billing/models.py
class ProcessedWebhookEvent(models.Model):
    provider = models.CharField(max_length=50, default="stripe")
    event_id = models.CharField(max_length=255)
    event_type = models.CharField(max_length=255)
    processed_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[("processing", "Processing"), ("done", "Done"), ("failed", "Failed")],
        default="processing",
    )

    class Meta:
        unique_together = [("provider", "event_id")]
        indexes = [models.Index(fields=["provider", "event_id"])]
```

```python
# apps/billing/webhooks.py
from django.db import transaction, IntegrityError

def handle_stripe_webhook(payload: bytes, sig_header: str) -> None:
    event = stripe.Webhook.construct_event(
        payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
    )

    # Atomic idempotency guard — unique constraint races go to IntegrityError
    try:
        with transaction.atomic():
            webhook_record, created = ProcessedWebhookEvent.objects.get_or_create(
                provider="stripe",
                event_id=event["id"],
                defaults={"event_type": event["type"]},
            )
            if not created:
                return  # Already processed or in-flight

        # Process OUTSIDE the initial transaction to avoid long-held locks
        _dispatch_webhook_event(event)

        webhook_record.status = "done"
        webhook_record.save(update_fields=["status"])

    except IntegrityError:
        # Race condition: another process won the insert. Skip.
        return
```

The two-transaction pattern (create record → process → mark done) keeps the idempotency lock narrow. Do not run all webhook processing inside one giant transaction, as long-running processing + a held row lock = deadlocks.

**Warning signs:**

- Webhook handler has no check for already-processed events
- Subscription created twice for the same user (duplicate rows detectable in admin)
- Users reporting being charged twice on flaky network days
- `stripe_subscription_id` lacks a `unique=True` constraint on the model

**Phase to address:** Billing Phase 2 (Webhook infrastructure). This must be the first thing implemented before any webhook handler logic.

**Recovery cost:** HIGH — duplicate billing records require manual reconciliation. Data integrity issues compound over time.

**Confidence:** HIGH (Stripe documentation + community pattern)

---

### Pitfall 3: Wrong Webhook Events Listened To (Event Confusion)

**What goes wrong:**
Stripe has overlapping events that seem interchangeable but are not. Three common mistakes:

**Mistake A: Using `payment_intent.succeeded` for subscriptions instead of `invoice.payment_succeeded`.**
For one-time payments via Checkout: listen to `checkout.session.completed`.
For subscriptions: listen to `invoice.payment_succeeded` (and `invoice.payment_failed`). Subscriptions create invoices automatically each period. `payment_intent.succeeded` fires on the underlying PaymentIntent, but it fires for EVERY invoice, including upcoming ones that happen during the life of a subscription. Developers accidentally activate accounts before the first invoice settles, or re-activate accounts on renewal invoices they didn't intend to handle.

**Mistake B: Using `customer.subscription.updated` to grant/revoke access.**
`customer.subscription.updated` fires on ANY change: metadata updates, trial extensions, payment method changes. If you grant access on this event, trial extensions re-trigger access grants. Use `customer.subscription.updated` only to sync local state. Grant access based on the `status` field value transitions (e.g., `trialing` → `active`), not the event itself.

**Mistake C: Using `checkout.session.completed` for subscriptions AND one-time payments, but not distinguishing the mode.**
`checkout.session.completed` fires for both `mode: "payment"` and `mode: "subscription"` sessions. If a single handler handles both, fulfillment logic runs twice or incorrectly.

**Prevention:**

```python
# Minimum event set for subscription billing:
SUBSCRIPTION_EVENTS = {
    "checkout.session.completed",            # Initial subscription signup via Checkout
    "invoice.payment_succeeded",             # Recurring payment success → renew access
    "invoice.payment_failed",                # Payment failure → send dunning email
    "customer.subscription.updated",         # Sync status (cancel_at_period_end, etc.)
    "customer.subscription.deleted",         # Hard cancellation → revoke access
    "customer.subscription.trial_will_end",  # Upcoming trial end notification
}

def handle_checkout_session_completed(session):
    # ALWAYS check mode before acting
    if session["mode"] == "subscription":
        _handle_subscription_checkout(session)
    elif session["mode"] == "payment":
        _handle_one_time_payment(session)
    # Do not fall through without an explicit check
```

**Warning signs:**

- Users whose access is revoked on plan metadata changes
- Users with `status=active` in the DB but a Stripe subscription with `status=past_due`
- Handling `payment_intent.succeeded` for subscription renewal — this fires for many more events than expected

**Phase to address:** Billing Phase 2 (Webhook infrastructure). The event routing table must be explicit and documented.

**Recovery cost:** MEDIUM — fixing event routing doesn't lose data, but requires reconciling any incorrect state transitions that already occurred.

**Confidence:** HIGH (Stripe documentation patterns + community experience)

---

### Pitfall 4: Billing Data Model Decisions That Cause Pain Later

**What goes wrong, specifically:**

**A. Storing Stripe price IDs directly on Plan/Product models.**

```python
# FRAGILE: ties your data model to Stripe's ID format
class Plan(models.Model):
    stripe_price_id = models.CharField(max_length=255, unique=True)
    stripe_price_id_monthly = models.CharField(...)
    stripe_price_id_yearly = models.CharField(...)
```

When you add another billing provider, or when Stripe price IDs change (e.g., migrating from legacy Plans API to Products/Prices API), every row in this table must be updated. Instead, store provider-specific IDs in a separate `PlanProviderMapping` table keyed by `(plan_id, provider)`.

**B. Storing subscription status as a free-form string copied from Stripe.**
`subscription.status = "active"` mirrors Stripe's status enum. This creates an implicit dependency: if Stripe adds a new status (they have in the past), your code breaks on unhandled values. Define your own `SubscriptionStatus` enum with only the statuses you act on, and map Stripe statuses to yours in the adapter.

**C. No `cancel_at_period_end` flag — using `status` alone to determine access.**
A user who cancels is still `active` until period end. If you revoke access on `customer.subscription.updated` when status is not `active`, you revoke access immediately. You need both `status` and `cancel_at_period_end` to correctly determine access.

**D. Storing plan feature flags directly on the Subscription model.**
When plan features change, historical subscriptions reference the old feature set. Features should be on the `Plan` model (or a separate `PlanFeature` table), not on `Subscription`.

**E. No audit log for subscription status transitions.**
Billing disputes require proof of when a subscription was active. A soft `status` field with no history makes it impossible to reconstruct timeline. At minimum, keep `started_at`, `cancelled_at`, `trial_ends_at`, `current_period_end` as explicit timestamp fields.

**Recommended minimal schema:**

```python
class BillingProfile(models.Model):
    """One per user. Lives in billing app. Removed when billing module is removed."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="billing_profile",
    )
    provider_customer_id = models.CharField(max_length=255, blank=True)
    # provider is which adapter is active; allows multi-provider in future
    provider = models.CharField(max_length=50, default="stripe")

class Subscription(models.Model):
    billing_profile = models.ForeignKey(BillingProfile, on_delete=models.PROTECT)
    plan = models.ForeignKey("Plan", on_delete=models.PROTECT)
    provider_subscription_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(
        max_length=30,
        choices=SubscriptionStatus.choices,    # Your enum, not Stripe's
    )
    cancel_at_period_end = models.BooleanField(default=False)
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()
    cancelled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class PlanProviderMapping(models.Model):
    """Maps your internal Plan to provider-specific price IDs."""
    plan = models.ForeignKey("Plan", on_delete=models.CASCADE)
    provider = models.CharField(max_length=50)
    provider_price_id = models.CharField(max_length=255)
    billing_interval = models.CharField(
        max_length=20,
        choices=[("month", "Monthly"), ("year", "Yearly")],
    )

    class Meta:
        unique_together = [("plan", "provider", "billing_interval")]
```

**Warning signs:**

- `stripe_price_id` field directly on Plan or Subscription model
- `subscription.status == "active"` used as the sole access gate
- No `cancel_at_period_end` field
- Subscription status stored as `CharField` without a choices constraint or enum

**Phase to address:** Billing Phase 1 (Data model design). Changing schema after webhooks are live requires a migration AND a data backfill.

**Recovery cost:** HIGH for schema changes on a live system. Adding `cancel_at_period_end` retroactively requires backfilling from Stripe's API for every active subscription.

**Confidence:** HIGH

---

### Pitfall 5: Plan Upgrade/Downgrade Logic Using Direct Subscription Updates Instead of Subscription Schedules

**What goes wrong:**
Upgrades (higher tier) should take effect immediately with proration. Downgrades (lower tier) should typically take effect at period end to avoid immediate loss of paid access.

Developers implement this by calling `stripe.Subscription.modify()` with `proration_behavior="none"` for downgrades and `"create_prorations"` for upgrades. This works until the edge case: a customer upgrades, then downgrades within the same billing period. The interim proration credit from the upgrade is lost or double-applied because the proration calculation runs against a subscription that was already partially prorated.

The correct tool for deferred downgrades is `subscription_schedule`, which queues phase changes at period boundaries. However, `subscription_schedule` adds complexity: once a subscription is managed by a schedule, ALL future modifications must go through the schedule API, or you get a `subscription_already_has_schedule` error.

**Prevention — simple but correct approach:**

- **Upgrades:** `stripe.Subscription.modify(sub_id, items=[...], proration_behavior="always_invoice")`. This immediately invoices the prorated difference, giving the user access to the higher tier now.
- **Downgrades:** Set `cancel_at_period_end=False`, modify items with `proration_behavior="none"`, and set `billing_cycle_anchor="unchanged"`. Store a `pending_plan_change` on the local Subscription model and apply it on the next `invoice.payment_succeeded` event.

Do NOT mix subscription schedule and non-schedule approaches within the same codebase. Pick one pattern and document it.

**Warning signs:**

- `stripe.SubscriptionSchedule` imported alongside `stripe.Subscription.modify` with no clear rule for which to use when
- Proration credits disappearing after upgrade-then-downgrade flows
- `stripe.error.InvalidRequestError: subscription_already_has_schedule` appearing in logs

**Phase to address:** Billing Phase 3 (Plan management). Must be designed before the plan-change endpoint is built.

**Recovery cost:** MEDIUM — incorrect proration requires issuing manual Stripe credits to affected customers.

**Confidence:** MEDIUM (based on Stripe documentation + community reports; verify current subscription schedules API behavior)

---

### Pitfall 6: Webhook Endpoint Timing Out Because Processing Is Synchronous

**What goes wrong:**
The Stripe webhook endpoint runs all processing synchronously within the HTTP request. If the processing involves:

- Sending a confirmation email
- Generating a PDF invoice
- Calling another external API (Mailchimp, Slack, etc.)
- Creating downstream records across multiple models

...the total time can exceed Stripe's 30-second timeout. When Stripe receives no response within 30 seconds, it marks the delivery as failed and retries. Your idempotency guard (Pitfall 2) prevents double-processing, but the original event is marked "failed" in Stripe's dashboard, creating false alarms.

**Prevention:**
Return a `200 OK` immediately after signature verification and idempotency guard, then process asynchronously:

```python
# apps/billing/views.py (Django Ninja endpoint)
@router.post("/webhooks/stripe/", auth=None)  # No auth — Stripe signs the payload
def stripe_webhook(request: HttpRequest):
    payload = request.body
    sig_header = request.headers.get("Stripe-Signature", "")

    # Step 1: Verify signature (fast — milliseconds)
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        raise HttpError(400, "Invalid payload or signature")

    # Step 2: Idempotency guard (fast — single DB lookup with unique constraint)
    _, created = ProcessedWebhookEvent.objects.get_or_create(
        provider="stripe",
        event_id=event["id"],
        defaults={"event_type": event["type"]},
    )
    if not created:
        return {"status": "already_processed"}

    # Step 3: Dispatch to Celery task — return 200 immediately
    process_stripe_webhook.delay(event_id=event["id"], event_type=event["type"])

    return {"status": "accepted"}
```

The Celery task fetches the event from Stripe by ID (rather than storing the full payload, which avoids PII in the task queue) or processes the locally stored event data.

**Warning signs:**

- `WebhookError: Timed out` appearing in Stripe dashboard webhook delivery logs
- Webhook handler that imports `send_mail` or `generate_pdf` at the top level
- Webhook endpoint response time > 5 seconds in any monitoring tool

**Phase to address:** Billing Phase 2 (Webhook infrastructure). Async dispatch must be part of the initial webhook design, not added later.

**Recovery cost:** LOW-MEDIUM — refactoring sync to async is straightforward, but you must replay any events that timed out in Stripe's delivery logs.

**Confidence:** HIGH

---

## Moderate Pitfalls

Mistakes that create bugs, user confusion, or significant debugging time.

---

### Pitfall 7: PDF Invoice Generation Blocking the Request Thread

**What goes wrong:**
WeasyPrint (the recommended Python HTML-to-PDF library) has two production problems:

1. **Memory leak per generation.** Each PDF generated increases the process RSS by 17-40MB. This memory is not released until the worker is restarted. Django workers serving PDF endpoints will exhaust memory over hours, causing OOM kills and downtime.

2. **Font resolution failures in Docker.** WeasyPrint resolves fonts from the OS. In a minimal Docker image (`python:3.12-slim`), system fonts are not installed. Custom fonts loaded via `@font-face` with relative paths in CSS fail silently (the font falls back to a default) or raise `URLFetchingError`. The PDF looks wrong in production but correct in local dev (where fonts are installed).

3. **WeasyPrint v53+ breaking change.** Version 53 switched from Cairo to pydyf as the PDF generator. This dropped PNG output and changed how some CSS properties are rendered. If your template was tested on WeasyPrint < 53, it may produce different output on v53+.

**Prevention:**

Always generate PDFs in a Celery task, never in the request cycle:

```python
@celery_app.task(bind=True, max_retries=3)
def generate_invoice_pdf(self, invoice_id: int) -> str:
    """Returns S3/storage URL of generated PDF."""
    invoice = Invoice.objects.select_related("subscription__billing_profile__user").get(
        id=invoice_id
    )
    # Render HTML template
    html_content = render_to_string("billing/invoice.html", {"invoice": invoice})

    # WeasyPrint import inside the task function (not at module level)
    # This avoids issues with WeasyPrint's global state in forked Celery workers
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration

    font_config = FontConfiguration()
    pdf_bytes = HTML(string=html_content, base_url=settings.STATIC_ROOT).write_pdf(
        font_config=font_config,
    )

    # Upload to storage and return URL — don't return raw bytes through Celery
    url = upload_to_storage(pdf_bytes, f"invoices/{invoice.id}.pdf")
    return url
```

**Docker font setup** — install fonts in your Dockerfile:

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-liberation \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*
```

Pin WeasyPrint to a specific minor version and test PDF output visually on every upgrade.

**Warning signs:**

- Django worker memory growing monotonically over hours (check with `docker stats`)
- PDF fonts different between local and staging environments
- `weasyprint.urls.URLFetchingError` in logs

**Phase to address:** Billing Phase 4 (Invoice generation). Design for async from the start.

**Recovery cost:** LOW — switching to Celery task is a straightforward refactor, but memory OOM kills in production require immediate attention.

**Confidence:** HIGH (WeasyPrint memory issue confirmed in Django ticket #34356 and WeasyPrint GitHub issues)

---

### Pitfall 8: Usage-Based Billing Reporting Timing Errors

**What goes wrong:**
Usage-based (metered) billing requires reporting usage to Stripe via the Meter Event API. Two common mistakes:

1. **Reporting usage at the moment of consumption rather than aggregating first.** Stripe's Meter Event endpoint allows 1,000 calls per second in live mode. An application with 500 concurrent users each making 10 actions per second would need 5,000 API calls per second — 5x the limit. At scale, this causes rate limiting errors that silently drop usage events, undercharging customers.

2. **Not accounting for Stripe's 35-day lookback window.** Stripe processes meter events asynchronously and truncates event timestamps to the nearest 15 minutes for analytics. If your reporting job is delayed (e.g., a Celery queue backup), you have a 35-day window to report late usage. But if your local aggregation table doesn't persist usage for that long before marking it "reported," late events are unrecoverable.

**Prevention:**

- Store usage events locally first (`UsageRecord` model in your DB with `reported_to_provider: bool`).
- A periodic Celery beat task aggregates and reports hourly, not per-event.
- Keep unreported records for at least 36 days before cleanup.

```python
# Celery beat task — runs every hour
@celery_app.task
def report_metered_usage():
    cutoff = timezone.now() - timedelta(hours=1)
    unreported = UsageRecord.objects.filter(
        reported_to_provider=False,
        created_at__lte=cutoff,
    ).values("subscription__provider_subscription_id").annotate(
        total=models.Sum("quantity")
    )
    for row in unreported:
        stripe.billing.MeterEvent.create(
            event_name="api_calls",
            payload={"value": str(row["total"]), "stripe_customer_id": ...},
            timestamp=int(cutoff.timestamp()),
        )
        UsageRecord.objects.filter(...).update(reported_to_provider=True)
```

**Warning signs:**

- Stripe rate limit errors (`429`) in billing-related API calls
- Usage reports called synchronously in the API request handler
- `UsageRecord` table with no `reported_to_provider` flag

**Phase to address:** Billing Phase 3 (Plan management). Usage reporting architecture must be designed with the metered billing plan type.

**Recovery cost:** MEDIUM — undercharging customers requires identifying affected billing periods and issuing manual adjustments. Stripe cannot backfill usage reports older than 35 days.

**Confidence:** MEDIUM (Stripe Meter API documentation + community rate-limit reports)

---

### Pitfall 9: Frontend Billing UX — Missing Failure and 3DS Handling

**What goes wrong:**
Minimal implementations of the billing frontend miss three critical flows:

1. **No handling for `requires_action` status (3DS/SCA).** Under PSD2 in Europe (and increasingly globally), many card payments require 3D Secure authentication. Stripe's Payment Element handles this automatically when you call `stripe.confirmPayment()`. If you navigate away from the payment page before the 3DS modal resolves, the payment is abandoned. Many React implementations use `router.push('/dashboard')` immediately after `confirmPayment()` resolves without checking the status, leaving users in a `requires_action` limbo.

   ```typescript
   // WRONG: Navigates away before checking 3DS result
   await stripe.confirmPayment({ elements, confirmParams: { return_url: "..." } });
   router.push("/dashboard");

   // CORRECT: confirmPayment redirects automatically for 3DS;
   // only run local code if the method does NOT require redirect
   const { error } = await stripe.confirmPayment({
     elements,
     confirmParams: { return_url: `${window.location.origin}/billing/return` },
     redirect: "if_required",
   });
   if (error) {
     setErrorMessage(error.message ?? "Payment failed.");
   } else {
     // No redirect needed — payment succeeded without 3DS
     router.push("/dashboard");
   }
   ```

2. **No return URL handler for post-3DS redirect.** When `confirmPayment` redirects to the `return_url`, the user lands on your page with `?payment_intent=pi_xxx&payment_intent_client_secret=xxx&redirect_status=succeeded` in the URL. If the page has no handler for these query params, users land on a blank dashboard with no confirmation of whether payment succeeded.

3. **No retry flow for failed payments.** `invoice.payment_failed` is sent by Stripe on subscription renewal failure. The default behavior sends Stripe's own dunning emails. If you override dunning, your app must surface a "Update payment method" flow. Many implementations show the error but don't link to a page where the customer can fix their card, so the subscription silently lapses.

**Prevention:**

- Always use `redirect: 'if_required'` in `confirmPayment` unless you explicitly want redirect-only behavior.
- Create a `/billing/return` page that reads query params, calls your backend to verify payment status, and renders success/failure UI.
- On `invoice.payment_failed`, set `subscription.payment_failed = True` in your model and surface a banner in the dashboard until the customer updates their payment method via a portal link.

**Warning signs:**

- No `/billing/return` route in the Next.js app
- `stripe.confirmPayment` call not followed by `if (error)` check
- Subscription status stuck in `past_due` with no visible UI affordance

**Phase to address:** Billing Phase 3 (Frontend billing UI). Test with Stripe's 3DS test cards (`4000000000003063`) during development.

**Recovery cost:** LOW — these are frontend-only changes, but users who encountered silent failures may have abandoned.

**Confidence:** HIGH (Stripe documentation + Next.js GitHub discussions)

---

### Pitfall 10: Making the Billing Module Hard to Remove

**What goes wrong:**
The CLI scaffolder promises billing is removable. In practice, integration points accumulate:

1. **Direct import of billing models in non-billing apps.**

   ```python
   # apps/accounts/services.py — WRONG
   from apps.billing.models import Subscription
   def is_user_subscribed(user): return Subscription.objects.filter(user=user).exists()
   ```

   When billing is removed, `accounts` breaks immediately.

2. **URL patterns included unconditionally in `urls.py`.**

   ```python
   # config/urls.py — WRONG
   from apps.billing.urls import router as billing_router  # ImportError if billing removed
   ```

3. **Django signals registered in `billing/apps.py` that modify non-billing models.** If the signal handler adds a `BillingProfile` on `User.post_save`, removing the billing app leaves a dangling signal registration reference that Django can't resolve.

4. **Template tags or context processors from billing in base templates.** `{% load billing_tags %}` in `base.html` raises `TemplateSyntaxError` when billing is removed.

5. **Settings that other apps depend on.** `settings.ACTIVE_PLAN_FEATURES` computed from billing models, read by the auth middleware for feature gating.

**Prevention — architectural rules for clean removability:**

- **No cross-app model imports.** All references from non-billing code to billing state must go through a service function or a `billing_enabled` check:

  ```python
  # apps/core/billing_utils.py — thin bridge, cleared when billing removed
  def get_user_subscription_status(user) -> str | None:
      if not apps.is_installed("apps.billing"):
          return None
      from apps.billing.services import get_subscription_status
      return get_subscription_status(user)
  ```

- **Conditional URL registration:**

  ```python
  # config/urls.py
  if apps.is_installed("apps.billing"):
      from apps.billing.api import billing_router
      api.add_router("/billing/", billing_router)
  ```

- **Billing signals registered only within billing's `AppConfig.ready()`**, never connecting to models in other apps via post-save signals that other apps rely on.

- **Feature gating via a dedicated service, not billing models directly.** The feature gate service checks `BILLING_ENABLED` from settings first; if False, returns a no-op grant.

- **CLI scaffolder test:** The test suite must include a step that removes billing from `INSTALLED_APPS`, runs `manage.py check`, and verifies zero errors.

**Warning signs:**

- `from apps.billing.models import` in any file outside `apps/billing/`
- `billing` in `INSTALLED_APPS` without a conditional check in `urls.py`
- Django system check warnings about missing relations after billing is removed

**Phase to address:** Billing Phase 1 (Module design). Boundaries must be established before the first model is written.

**Recovery cost:** HIGH — decoupling after tight integration requires touching every integration point individually and verifying system checks pass.

**Confidence:** HIGH

---

### Pitfall 11: Testing Strategy That Misses the Hard Parts

**What goes wrong:**
Billing tests are either too narrow (unit tests with everything mocked, no real Stripe interaction) or too broad (every test hits Stripe's test mode API, making the suite slow and flaky). Three specific gaps:

1. **Webhook signature verification not tested.** Tests skip signature verification by mocking `stripe.Webhook.construct_event`. This means the actual signature checking path (the most likely place for a security regression) is never exercised.

2. **Idempotency guard not tested.** Tests don't simulate the same webhook being delivered twice. When a developer changes the idempotency guard, they have no regression test.

3. **Status state machine not tested.** The transitions `pending → active → cancel_at_period_end → cancelled` are not tested as a sequence. Individual event handlers are tested in isolation. A developer changes the `cancelled` state handler and doesn't realize it needs a prior `cancel_at_period_end` state to be correct.

**Prevention — testing strategy:**

```
Layer 1 — Unit tests (no Stripe, no DB):
  - Test adapter's parse_webhook() mapping from Stripe event → WebhookEvent
  - Test plan/status mapping functions
  - Run fast, no mocks except for the adapter interface

Layer 2 — Integration tests (real DB, mocked Stripe API):
  - Use stripe-mock (official Stripe Docker image) for local + CI
  - Test full webhook handler with real signature verification:
    use stripe.WebhookSignature to sign your test payload with a known secret
  - Test idempotency: POST the same event_id twice, assert second is a no-op
  - Test status state machine as a sequence

Layer 3 — Contract tests (Stripe test mode, CI only):
  - Run against real Stripe test API monthly or on billing code changes
  - Verify that your adapter's assumptions about Stripe's API are still correct
  - Never run in the main fast test suite
```

**Signing test payloads correctly:**

```python
# tests/billing/conftest.py
import time
import stripe

@pytest.fixture
def signed_stripe_payload(settings):
    settings.STRIPE_WEBHOOK_SECRET = "whsec_test_secret"
    def _make_payload(event_type: str, data: dict) -> tuple[bytes, str]:
        payload = json.dumps({"id": "evt_test", "type": event_type, "data": data}).encode()
        timestamp = int(time.time())
        signed_payload = f"{timestamp}.{payload.decode()}"
        signature = hmac.new(
            b"test_secret", signed_payload.encode(), hashlib.sha256
        ).hexdigest()
        sig_header = f"t={timestamp},v1={signature}"
        return payload, sig_header
    return _make_payload
```

**Warning signs:**

- Webhook tests that patch `stripe.Webhook.construct_event` to return a fixture
- No test that submits the same event_id twice
- Test suite passes with `STRIPE_WEBHOOK_SECRET` unset (should fail loudly)

**Phase to address:** Billing Phase 2 (Webhook infrastructure). Testing patterns must be established alongside the handlers.

**Recovery cost:** LOW-MEDIUM — adding tests retroactively is possible but often reveals latent bugs.

**Confidence:** HIGH (Simon Willison's TIL on pytest Stripe signature, dj-stripe test patterns)

---

## Minor Pitfalls

Annoyances that are easy to fix but easy to overlook.

---

### Pitfall 12: Stripe Secret Key Leaking via OpenAPI Spec

**What goes wrong:**
Django Ninja Extra generates an OpenAPI spec served at `/api/openapi.json`. If any billing endpoint leaks `STRIPE_PUBLISHABLE_KEY` (or worse, `STRIPE_SECRET_KEY`) in a response schema or endpoint description, the spec becomes a security leak. Even the publishable key should not be in the spec — it should be an environment variable accessed client-side.

**Prevention:**
Never embed Stripe keys in schema examples or response bodies. Serve `STRIPE_PUBLISHABLE_KEY` via a dedicated `/config` endpoint that requires authentication, or inject it via Next.js environment variables on the server side. Restrict OpenAPI spec access to non-production environments (see existing PITFALLS.md, Security Mistakes section).

**Confidence:** HIGH

---

### Pitfall 13: Stripe Customer Portal vs. Custom Subscription Management UI

**What goes wrong:**
Teams build a full custom subscription management UI (plan selection, payment method update, invoice history) that partially replicates Stripe's hosted Customer Portal. The custom UI handles 80% of cases correctly and misses edge cases (coupon application, tax handling, multi-currency). Support tickets spike.

**Prevention:**
Use Stripe's hosted Customer Portal for subscription management (cancel, update payment method, view invoices). Only build custom UI for the initial checkout flow. Integrate the portal via:

```python
session = stripe.billing_portal.Session.create(
    customer=billing_profile.provider_customer_id,
    return_url=f"{settings.FRONTEND_URL}/billing",
)
return {"url": session.url}
```

Then redirect the user to `session.url`. This is the 80/20 choice for a template — full custom UI is a product decision, not a template responsibility.

**Confidence:** HIGH

---

### Pitfall 14: Hardcoded Currency Assumptions

**What goes wrong:**
`amount` stored as an integer (Stripe's format: cents/minor units) gets displayed directly as a dollar amount. `1099` is rendered as `$1099` instead of `$10.99`. International pricing in JPY (no minor units, `amount=1000` = ¥1000) is displayed as `¥10.00`.

**Prevention:**
Store `amount` and `currency` together. Use a `Money` type or at minimum a display formatter that is currency-aware:

```python
def format_money(amount: int, currency: str) -> str:
    zero_decimal_currencies = {"jpy", "krw", "vnd", "bif", "clp"}
    if currency.lower() in zero_decimal_currencies:
        return f"{amount} {currency.upper()}"
    return f"{amount / 100:.2f} {currency.upper()}"
```

**Confidence:** HIGH

---

## Phase-Specific Warnings

| Phase Topic            | Likely Pitfall                                              | Mitigation                                                              |
| ---------------------- | ----------------------------------------------------------- | ----------------------------------------------------------------------- |
| Adapter design         | Stripe concepts leaking into ABC (Pitfall 1)                | Define interface in domain terms first; write Stripe adapter second     |
| Data model             | Provider-specific IDs hardcoded on Plan model (Pitfall 4)   | Use PlanProviderMapping table; no `stripe_*` fields outside billing app |
| Webhook infrastructure | Duplicate processing on retry (Pitfall 2)                   | ProcessedWebhookEvent table with unique constraint before any handler   |
| Webhook infrastructure | Wrong events mapped to business actions (Pitfall 3)         | Explicit event routing table; reviewed and documented                   |
| Webhook infrastructure | Synchronous processing timing out (Pitfall 6)               | Return 200 immediately; dispatch to Celery                              |
| Plan management        | Upgrade/downgrade proration errors (Pitfall 5)              | Decide on direct modify vs schedule; document the rule                  |
| Plan management        | Usage-based reporting rate limits (Pitfall 8)               | Local `UsageRecord` table; hourly Celery beat job                       |
| Invoice generation     | WeasyPrint memory leak (Pitfall 7)                          | Celery task; pin WeasyPrint version; install fonts in Dockerfile        |
| Frontend billing UI    | Missing 3DS / return URL handler (Pitfall 9)                | Use `redirect: 'if_required'`; build `/billing/return` page             |
| CLI scaffolder         | Tight coupling making removal hard (Pitfall 10)             | `apps.is_installed()` guards; no cross-app model imports                |
| Testing                | Webhook tests that skip signature verification (Pitfall 11) | Sign test payloads using real HMAC; use stripe-mock in CI               |

---

## Billing-Specific "Looks Done But Isn't" Checklist

- [ ] **Webhook idempotency:** Does the handler check `ProcessedWebhookEvent` before processing? Does CI have a test that submits the same event ID twice?
- [ ] **Stripe signature verification:** Is the signature verified on EVERY webhook request, not just in production?
- [ ] **`cancel_at_period_end` tracked:** Is there a flag distinct from `status` to determine if a subscription is in a grace period?
- [ ] **3DS handling:** Does `confirmPayment` use `redirect: 'if_required'`? Does the `/billing/return` page exist?
- [ ] **PDF generation async:** Is invoice PDF generation dispatched to Celery, not run in the request cycle?
- [ ] **System fonts in Docker:** Does the API Dockerfile install `fonts-liberation` or equivalent?
- [ ] **Removability test:** Does `manage.py check` pass with billing removed from `INSTALLED_APPS`?
- [ ] **No cross-app billing imports:** Does `grep -r "from apps.billing" apps/ --include="*.py" | grep -v "apps/billing/"` return zero results?
- [ ] **Currency-aware amount display:** Is `amount` always paired with `currency` before display?
- [ ] **Stripe keys not in OpenAPI spec:** Is `STRIPE_SECRET_KEY` absent from all schema examples and response bodies?

---

## Sources

- Stripe documentation — webhook idempotency, event types, subscription lifecycle, meter events, Customer Portal API (confidence: HIGH — stable official docs, current as of 2026)
- [Stripe Webhooks: Solving Race Conditions](https://www.pedroalonso.net/blog/stripe-webhooks-solving-race-conditions/) — Pedro Alonso (confidence: MEDIUM)
- [Medium — Integrating Stripe Billing with Django 6.0](https://medium.com/django-journal/integrating-stripe-billing-with-django-6-0-333aa65cf1e6) (confidence: MEDIUM)
- WeasyPrint GitHub — [Memory leak issue #34356 (Django ticket)](https://code.djangoproject.com/ticket/34356), WeasyPrint Celery threading issues (confidence: HIGH — confirmed issues)
- [WeasyPrint v53 pydyf migration](https://doc.courtbouillon.org/weasyprint/stable/common_use_cases.html) — official docs (confidence: HIGH)
- [Mocking Stripe signature in pytest — Simon Willison's TIL](https://til.simonwillison.net/pytest/pytest-stripe-signature) (confidence: HIGH)
- [stripe-mock official GitHub](https://github.com/stripe/stripe-mock) — mock Stripe API server (confidence: HIGH)
- [Mastering Stripe Subscription Upgrades — Engineering Journal](https://engineeringjournal.substack.com/p/mastering-stripe-subscription-upgrades) (confidence: MEDIUM)
- [Modeling SaaS subscriptions in Postgres — Axel Larsson](https://axellarsson.com/blog/modeling-saas-subscriptions-in-postgres/) (confidence: MEDIUM)
- [dj-stripe — Django Stripe integration library](https://dj-stripe.dev/) — reference for webhook handling patterns (confidence: HIGH)
- [SaaS Pegasus guide — Django Stripe integration](https://www.saaspegasus.com/guides/django-stripe-integrate/) (confidence: MEDIUM)
- Training data — adapter pattern, leaky abstractions, Django modular architecture (confidence: MEDIUM — corroborated by search results)

---

_Pitfalls research for: Billing & Payments Module (Django Ninja Extra + Next.js 15 + Stripe adapter pattern)_
_Researched: 2026-03-07_
_Supersedes: Foundation template PITFALLS.md (2026-02-08) for billing-specific concerns only. Foundation pitfalls remain valid for non-billing phases._
