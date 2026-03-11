# Phase 9: Billing Scaffold - Research

**Researched:** 2026-03-07
**Domain:** Django billing module foundation — ABC adapter pattern, data models, settings configuration, module isolation
**Confidence:** HIGH

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions

- **Adapter Pattern:** ABC (abstract base class), not Protocol — explicit inheritance enforces contract at class definition; missing methods raise TypeError immediately
- **Adapter Method Set (full, upfront):** `create_customer`, `create_checkout_session` (handles subscription AND one-time mode), `create_portal_session`, `cancel_subscription`, `modify_subscription`, `construct_webhook_event`, `record_usage`, `list_invoices`
- **StripeAdapter target:** `stripe.StripeClient` v14 pattern — no legacy module-level `stripe.Customer.create()` calls
- **"stripe" word rule:** Never appears in any abstract method signature or return type — interface is domain-centric
- **All 4 models in 0001_initial.py:** Customer, Subscription, Payment, ProcessedWebhookEvent (avoids a second migration in Phase 10)
- **SubscriptionStatus:** Django TextChoices with full Stripe-matching set: `active`, `past_due`, `canceled`, `trialing`, `incomplete`, `incomplete_expired`, `unpaid`
- **BILLING_PLANS dict** in `config/settings/base.py` with `name`, `stripe_price_id_monthly`, `stripe_price_id_annual`, `trial_days`, `features[]` keys
- **PlanProviderMapping table** in DB — maps internal plan IDs to provider price IDs; prevents price ID on Plan rows
- **Adapter resolution:** `import_string(settings.BILLING_ADAPTER)` — swappable via one settings value
- **Module isolation markers:** `# BILLING_START` / `# BILLING_END` in `config/urls.py`; `"apps.billing"` in INSTALLED_APPS (scaffolder strips it); `stripe` in `[billing]` extras group in `pyproject.toml`
- **Auto-create signal:** `signals.py` — `post_save` on User → `Customer.objects.get_or_create(user=instance)`; registered in `BillingConfig.ready()`
- **No HTTP endpoints, no webhook processing logic, no frontend in this phase**

### Claude's Discretion

- `PlanProviderMapping` model field names and indexing strategy
- Admin registration (CustomerAdmin, SubscriptionAdmin) — register all models in `admin.py`
- Migration field ordering and index choices
- `.env.example` comment formatting for billing vars
- Whether to add a `stripe_price_id` field to `PlanProviderMapping` vs resolving via the settings dict at service layer

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within Phase 9 scope.
</user_constraints>

<phase_requirements>

## Phase Requirements

| ID       | Description                                                                                                 | Research Support                             |
| -------- | ----------------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| ADPTR-01 | `PaymentAdapter` ABC defined with domain-centric method signatures                                          | ABC pattern section; "stripe" word rule      |
| ADPTR-02 | `StripeAdapter(PaymentAdapter)` concrete implementation using `StripeClient` v14                            | Stripe SDK v14 section; StripeClient pattern |
| ADPTR-03 | All abstract methods implemented in StripeAdapter (full method set, no stubs)                               | Full method set locked in decisions          |
| ADPTR-04 | Adapter resolved via `import_string(settings.BILLING_ADAPTER)`                                              | Settings configuration section               |
| ADPTR-05 | Abstract method signatures contain no Stripe-specific types or names                                        | Domain-centric interface rule                |
| CUST-01  | `Customer` model with OneToOne → User, `stripe_customer_id` (blank until interaction), timestamps           | Data model section                           |
| CUST-02  | `post_save` signal auto-creates Customer on User creation, registered in `BillingConfig.ready()`            | Signal pattern section                       |
| SUB-06   | `SubscriptionStatus` Django TextChoices with full Stripe-matching statuses                                  | TextChoices section                          |
| PAY-02   | All 4 models in single `0001_initial.py` migration (Customer, Subscription, Payment, ProcessedWebhookEvent) | Migration strategy section                   |

</phase_requirements>

---

## Summary

Phase 9 establishes the billing module's foundational layer: four Django models, the `PaymentAdapter` ABC with its complete method set, the `StripeAdapter` concrete implementation, settings wiring, a User→Customer auto-create signal, and module isolation markers. No HTTP layer, no webhook processing, and no frontend are delivered in this phase.

All decisions are locked from CONTEXT.md and grounded in prior milestone-level research (SUMMARY.md, ARCHITECTURE.md, STACK.md — all confidence HIGH, researched 2026-03-07). This phase does not require new external research. The structural template is the existing `apps/api/apps/ai/` module, which must be mirrored exactly.

The single highest-risk decision — the adapter interface's domain-centric method signatures — is already locked. The implementation challenge is faithfully executing the locked design without letting Stripe concepts leak upward into the ABC.

**Primary recommendation:** Mirror `apps/api/apps/ai/` directory structure verbatim. Define the ABC first with stub `raise NotImplementedError` bodies, then implement `StripeAdapter`, then wire settings and signal. Never reference `stripe.*` types in the ABC layer.

---

## Standard Stack

### Core (Phase 9 only — backend Python)

| Library                                     | Version         | Purpose                                 | Why Standard                                                                                                                          |
| ------------------------------------------- | --------------- | --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| `stripe`                                    | `>=14.4,<15`    | All Stripe API calls in `StripeAdapter` | Official Stripe Python SDK; v14.4 pins API version `2026-02-25.clover`; v8+ `StripeClient` pattern replaces legacy module-level calls |
| Django ABC (`abc` stdlib)                   | stdlib          | `PaymentAdapter` abstract base class    | No external dep; `ABCMeta` + `@abstractmethod` enforces contract at class definition time                                             |
| Django TextChoices                          | Django built-in | `SubscriptionStatus` enum               | Native ORM integration, admin-readable, auto-validates on assignment                                                                  |
| `django.utils.module_loading.import_string` | Django built-in | Adapter resolution from settings string | Same pattern used by `AUTHENTICATION_BACKENDS`, `DEFAULT_AUTO_FIELD`, etc.                                                            |

### Supporting

| Library         | Version      | Purpose                  | When to Use                                                                         |
| --------------- | ------------ | ------------------------ | ----------------------------------------------------------------------------------- |
| `stripe[async]` | `>=14.4,<15` | Async StripeClient calls | If Phase 10 uses async Django views or async Celery tasks; not required for Phase 9 |

### Alternatives Considered

| Instead of | Could Use         | Tradeoff                                                                                                                                    |
| ---------- | ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `abc.ABC`  | `typing.Protocol` | Protocol allows structural subtyping (duck typing) — rejected because missing methods are not caught at class definition, only at call time |
| `abc.ABC`  | `dj-stripe`       | dj-stripe is itself an opinionated Stripe layer — breaks the adapter pattern, adds ~40 User-coupled migrations, imposes Django 5+ floor     |

**Installation (Phase 9 addition):**

```bash
# In apps/api/pyproject.toml [billing] extras group:
stripe = ">=14.4,<15"

# Install for dev:
uv pip install "stripe>=14.4,<15"
```

---

## Architecture Patterns

### Recommended Project Structure

```
apps/api/apps/billing/
├── __init__.py
├── apps.py           # BillingConfig — name="apps.billing", ready() registers signal
├── admin.py          # CustomerAdmin, SubscriptionAdmin, PaymentAdmin, ProcessedWebhookEventAdmin
├── models.py         # Customer, Subscription, Payment, ProcessedWebhookEvent, PlanProviderMapping
├── schemas.py        # (Phase 9: empty or stubs only — schemas needed in Phase 10+)
├── controllers.py    # (Phase 9: empty stub — auto-discover finds it, no routes yet)
├── services.py       # (Phase 9: empty stub — service layer comes in Phase 10)
├── adapters.py       # PaymentAdapter ABC + StripeAdapter concrete implementation
├── signals.py        # post_save User → Customer.objects.get_or_create
├── webhooks.py       # (Phase 9: empty placeholder — plain view comes in Phase 10)
└── migrations/
    └── 0001_initial.py  # All 4 models + PlanProviderMapping in one migration
```

### Pattern 1: PaymentAdapter ABC

**What:** Abstract base class defining the full billing interface in domain terms.
**When to use:** Always — never call `stripe.*` directly from services or controllers.

```python
# apps/api/apps/billing/adapters.py
# Source: Python stdlib abc docs + CONTEXT.md method set decision
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class CheckoutSessionResult:
    session_url: str
    session_id: str


@dataclass
class PortalSessionResult:
    portal_url: str


@dataclass
class WebhookEvent:
    event_type: str
    event_id: str
    data: dict[str, Any]


class PaymentAdapter(ABC):
    """Domain-centric payment adapter interface. No provider names in signatures."""

    @abstractmethod
    def create_customer(self, email: str, name: str, metadata: dict[str, str]) -> str:
        """Create a billing customer. Returns provider customer ID."""
        ...

    @abstractmethod
    def create_checkout_session(
        self,
        customer_id: str,
        price_id: str,
        mode: str,  # "subscription" | "payment"
        success_url: str,
        cancel_url: str,
        trial_days: int = 0,
    ) -> CheckoutSessionResult:
        """Create a hosted checkout session."""
        ...

    @abstractmethod
    def create_portal_session(
        self, customer_id: str, return_url: str
    ) -> PortalSessionResult:
        """Create a billing portal session for self-service management."""
        ...

    @abstractmethod
    def cancel_subscription(
        self, subscription_id: str, at_period_end: bool = True
    ) -> None:
        """Cancel a subscription. at_period_end=True is the safe default."""
        ...

    @abstractmethod
    def modify_subscription(
        self, subscription_id: str, new_price_id: str, proration_behavior: str
    ) -> None:
        """Upgrade or downgrade a subscription to a new price."""
        ...

    @abstractmethod
    def construct_webhook_event(
        self, payload: bytes, signature: str, secret: str
    ) -> WebhookEvent:
        """Verify webhook signature and parse event. Raises ValueError on invalid sig."""
        ...

    @abstractmethod
    def record_usage(
        self, subscription_item_id: str, quantity: int, timestamp: int
    ) -> None:
        """Record a usage event for metered billing."""
        ...

    @abstractmethod
    def list_invoices(
        self, customer_id: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """List invoices for a customer. Returns provider-agnostic dict list."""
        ...
```

### Pattern 2: StripeAdapter Implementation

**What:** Concrete implementation using `stripe.StripeClient` (v14 object-oriented pattern).
**When to use:** Default adapter; swapped by changing `BILLING_ADAPTER` setting.

```python
# apps/api/apps/billing/adapters.py (continued)
# Source: stripe-python v14 StripeClient docs
from django.conf import settings
import stripe


class StripeAdapter(PaymentAdapter):
    """Stripe implementation of PaymentAdapter."""

    def __init__(self) -> None:
        self._client = stripe.StripeClient(api_key=settings.STRIPE_SECRET_KEY)

    def create_customer(self, email: str, name: str, metadata: dict[str, str]) -> str:
        customer = self._client.customers.create(
            params={"email": email, "name": name, "metadata": metadata}
        )
        return customer.id

    def construct_webhook_event(
        self, payload: bytes, signature: str, secret: str
    ) -> WebhookEvent:
        try:
            event = self._client.construct_event(
                payload=payload, sig_header=signature, secret=secret
            )
        except stripe.error.SignatureVerificationError as exc:
            raise ValueError("Invalid webhook signature") from exc
        return WebhookEvent(
            event_type=event["type"],
            event_id=event["id"],
            data=event["data"]["object"],
        )

    # ... remaining methods implemented similarly
```

### Pattern 3: Adapter Resolution via import_string

**What:** Settings-driven adapter injection — the only place `StripeAdapter` is instantiated.
**When to use:** In service layer (Phase 10) — Phase 9 establishes the settings key.

```python
# config/settings/base.py addition:
BILLING_ADAPTER = env(
    "BILLING_ADAPTER",
    default="apps.billing.adapters.StripeAdapter",
)

# Usage in services.py (Phase 10):
from django.utils.module_loading import import_string
from django.conf import settings

def get_payment_adapter() -> "PaymentAdapter":
    adapter_class = import_string(settings.BILLING_ADAPTER)
    return adapter_class()
```

### Pattern 4: Django Models

**What:** All 4 models + PlanProviderMapping in a single initial migration.

```python
# apps/api/apps/billing/models.py
import uuid
from django.db import models
from django.conf import settings


class SubscriptionStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    PAST_DUE = "past_due", "Past Due"
    CANCELED = "canceled", "Canceled"
    TRIALING = "trialing", "Trialing"
    INCOMPLETE = "incomplete", "Incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired", "Incomplete Expired"
    UNPAID = "unpaid", "Unpaid"


class Customer(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="billing_customer",
    )
    stripe_customer_id = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Customer"

    def __str__(self) -> str:
        return f"Customer({self.user_id})"


class Subscription(models.Model):
    customer = models.OneToOneField(
        Customer, on_delete=models.CASCADE, related_name="subscription"
    )
    stripe_subscription_id = models.CharField(max_length=255, blank=True, default="")
    status = models.CharField(
        max_length=30,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.INCOMPLETE,
    )
    plan_id = models.CharField(max_length=100, blank=True, default="")
    cancel_at_period_end = models.BooleanField(default=False)
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    trial_start = models.DateTimeField(null=True, blank=True)
    trial_end = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Payment(models.Model):
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="payments"
    )
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, default="")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="usd")
    status = models.CharField(max_length=50, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ProcessedWebhookEvent(models.Model):
    provider = models.CharField(max_length=50)
    event_id = models.CharField(max_length=255)
    processed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("provider", "event_id")]


class PlanProviderMapping(models.Model):
    plan_id = models.CharField(max_length=100, db_index=True)
    provider = models.CharField(max_length=50, default="stripe")
    price_id_monthly = models.CharField(max_length=255, blank=True, default="")
    price_id_annual = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        unique_together = [("plan_id", "provider")]
        verbose_name = "Plan Provider Mapping"

    def __str__(self) -> str:
        return f"{self.plan_id} → {self.provider}"
```

### Pattern 5: BillingConfig Signal Registration

**What:** `AppConfig.ready()` registers signals — same pattern as accounts app.
**When to use:** Always — ensures signal fires without manual import in settings.

```python
# apps/api/apps/billing/apps.py
from django.apps import AppConfig


class BillingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.billing"
    verbose_name = "Billing"

    def ready(self) -> None:
        import apps.billing.signals  # noqa: F401
```

```python
# apps/api/apps/billing/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


@receiver(post_save, sender=User)
def create_billing_customer(
    sender: type, instance: User, created: bool, **kwargs: object
) -> None:
    if created:
        from apps.billing.models import Customer
        Customer.objects.get_or_create(user=instance)
```

### Pattern 6: Module Isolation Markers

**What:** Comment delimiters enabling clean CLI scaffolder removal.
**When to use:** Must be placed in Phase 9 even though webhook view arrives in Phase 10.

```python
# config/urls.py addition:
# BILLING_START
# Billing webhook and API routes (removable — see CLI scaffolder docs)
# BILLING_END

# config/settings/base.py INSTALLED_APPS addition:
INSTALLED_APPS = [
    # ... existing apps ...
    "apps.billing",  # BILLING_MODULE — remove to strip billing
]
```

```toml
# apps/api/pyproject.toml addition:
[project.optional-dependencies]
billing = [
    "stripe>=14.4,<15",
]
```

### Anti-Patterns to Avoid

- **"stripe" in ABC signatures:** Any `stripe.Customer`, `stripe.Subscription`, or Stripe enum in the abstract method signature breaks provider-agnosticism. Use `str` for IDs, dataclasses for structured results.
- **Legacy module-level Stripe calls:** `stripe.Customer.create(...)` is the v7 pattern. Use `self._client.customers.create(params={...})` — the v14 `StripeClient` pattern.
- **Importing `stripe` in `models.py` or `services.py`:** `stripe` belongs only in `adapters.py`. Services receive the adapter via dependency injection.
- **`stripe_customer_id` on User model:** Put it on `Customer` model (OneToOne). Keeps accounts app clean and removable.
- **Calling `import_string` at module level:** Call it inside a function (or `__init__`) — module-level calls run before Django is fully initialized.

---

## Don't Hand-Roll

| Problem                     | Don't Build                    | Use Instead                                 | Why                                                      |
| --------------------------- | ------------------------------ | ------------------------------------------- | -------------------------------------------------------- |
| Adapter discovery           | Custom registry or factory     | `django.utils.module_loading.import_string` | Django built-in, same as auth backends; zero boilerplate |
| Status choices              | String constants or IntEnum    | `models.TextChoices`                        | ORM-integrated, admin-readable, validates on assignment  |
| Signal registration         | Manual `connect()` in settings | `AppConfig.ready()` import pattern          | Idiomatic Django; signals registered exactly once        |
| User→Customer lazy creation | Overriding `save()` on User    | `post_save` signal                          | No changes to accounts app; decoupled                    |
| App config                  | Manual `default_app_config`    | `default_auto_field` in `AppConfig`         | Django 3.2+ — `AppConfig` auto-discovered from `apps.py` |

**Key insight:** Django's built-in extension points (`import_string`, `TextChoices`, `AppConfig.ready`, `post_save`) handle every Phase 9 concern. No external libraries beyond `stripe` are needed for the scaffold.

---

## Common Pitfalls

### Pitfall 1: Stripe Types Leaking into ABC

**What goes wrong:** `create_customer` returns `stripe.Customer` instead of `str`. Any code touching the return value now depends on the `stripe` package.
**Why it happens:** It's the path of least resistance when implementing Stripe first.
**How to avoid:** Define ALL abstract method signatures before writing any Stripe code. Use primitive types (`str`, `int`, `dict`) or project-defined dataclasses as return types.
**Warning signs:** `import stripe` appearing anywhere outside `adapters.py`.

### Pitfall 2: Split Migration (Phase 9 + Phase 10)

**What goes wrong:** `ProcessedWebhookEvent` omitted from `0001_initial.py`, then added in Phase 10 as `0002_add_webhook_idempotency.py`. The table structure is obvious from day one; the extra migration adds noise.
**Why it happens:** Phase boundary feels like the right split point.
**How to avoid:** All 4 models + `PlanProviderMapping` in `0001_initial.py` per the locked decision.
**Warning signs:** Running `makemigrations` after Phase 9 and seeing a non-empty diff.

### Pitfall 3: StripeClient Instantiation at Module Level

**What goes wrong:** `_client = stripe.StripeClient(api_key=settings.STRIPE_SECRET_KEY)` at module level in `adapters.py` — settings not yet loaded when Django imports the module during startup.
**Why it happens:** Module-level client looks clean.
**How to avoid:** Instantiate `StripeClient` in `StripeAdapter.__init__()`, not at module level.
**Warning signs:** `django.core.exceptions.ImproperlyConfigured` or `KeyError` on `STRIPE_SECRET_KEY` during startup.

### Pitfall 4: Signal Fires on Every Save, Not Just Creation

**What goes wrong:** `Customer.objects.get_or_create` called on every User `save()`, not just creation — expensive but safe because `get_or_create` is idempotent. However, the intent is creation-only.
**Why it happens:** Forgetting `if created:` guard in signal handler.
**How to avoid:** Always gate the signal body with `if created:`.
**Warning signs:** DB logs showing `SELECT` + attempted `INSERT` on every profile update.

### Pitfall 5: Missing `unique_together` on ProcessedWebhookEvent

**What goes wrong:** Webhook retries (Stripe at-least-once delivery) create duplicate ProcessedWebhookEvent rows — idempotency guard fails silently.
**Why it happens:** `unique_together` is in models but not in the migration, or migration generated incorrectly.
**How to avoid:** Verify `0001_initial.py` contains the `UniqueConstraint` or `unique_together` entry for `("provider", "event_id")`.
**Warning signs:** `ProcessedWebhookEvent.objects.filter(event_id=...).count() > 1` in tests.

---

## Code Examples

### BILLING_PLANS Settings Structure

```python
# config/settings/base.py
# Source: CONTEXT.md locked decision
BILLING_PLANS: dict = {
    "free": {
        "name": "Free",
        "stripe_price_id_monthly": "",
        "stripe_price_id_annual": "",
        "trial_days": 0,
        "features": ["Up to 3 projects", "Community support"],
    },
    "pro": {
        "name": "Pro",
        "stripe_price_id_monthly": env("STRIPE_PRICE_PRO_MONTHLY", default=""),
        "stripe_price_id_annual": env("STRIPE_PRICE_PRO_ANNUAL", default=""),
        "trial_days": 14,
        "features": ["Unlimited projects", "Priority support", "API access"],
    },
    "enterprise": {
        "name": "Enterprise",
        "stripe_price_id_monthly": env("STRIPE_PRICE_ENTERPRISE_MONTHLY", default=""),
        "stripe_price_id_annual": env("STRIPE_PRICE_ENTERPRISE_ANNUAL", default=""),
        "trial_days": 0,
        "features": ["Everything in Pro", "SLA", "Dedicated support"],
    },
}

BILLING_ADAPTER = env(
    "BILLING_ADAPTER",
    default="apps.billing.adapters.StripeAdapter",
)

STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY", default="")
STRIPE_PUBLISHABLE_KEY = env("STRIPE_PUBLISHABLE_KEY", default="")
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET", default="")
```

### .env.example Billing Section

```bash
# BILLING MODULE
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_PRO_MONTHLY=price_...
STRIPE_PRICE_PRO_ANNUAL=price_...
STRIPE_PRICE_ENTERPRISE_MONTHLY=price_...
STRIPE_PRICE_ENTERPRISE_ANNUAL=price_...
BILLING_ADAPTER=apps.billing.adapters.StripeAdapter
# END BILLING MODULE
```

### PlanProviderMapping Discretion Recommendation

For the Claude's Discretion item on `PlanProviderMapping` field names and indexing:

- **Recommended field names:** `plan_id`, `provider`, `price_id_monthly`, `price_id_annual` — mirrors the `BILLING_PLANS` dict keys directly, making sync code obvious
- **Index strategy:** `db_index=True` on `plan_id`; `unique_together = [("plan_id", "provider")]` — covers the most common lookup (plan_id + provider) and prevents duplicates
- **No `stripe_price_id` field recommendation:** Keep `price_id_monthly` and `price_id_annual` generic (not `stripe_price_id_*`) — the model name already implies provider specificity is handled via the `provider` column

---

## Validation Architecture

### Test Framework

| Property           | Value                                                               |
| ------------------ | ------------------------------------------------------------------- |
| Framework          | pytest + pytest-django                                              |
| Config file        | `apps/api/pytest.ini` or `pyproject.toml [tool.pytest.ini_options]` |
| Quick run command  | `cd apps/api && pytest apps/billing/tests/ -x -q`                   |
| Full suite command | `cd apps/api && pytest apps/billing/ -v`                            |

### Phase Requirements → Test Map

| Req ID   | Behavior                                                                                                             | Test Type   | Automated Command                                                                    | File Exists? |
| -------- | -------------------------------------------------------------------------------------------------------------------- | ----------- | ------------------------------------------------------------------------------------ | ------------ |
| ADPTR-01 | `PaymentAdapter` is abstract; instantiating it raises `TypeError`                                                    | unit        | `pytest apps/billing/tests/test_adapters.py::test_payment_adapter_is_abstract -x`    | Wave 0       |
| ADPTR-02 | `StripeAdapter` inherits `PaymentAdapter` and instantiates without error (with mocked key)                           | unit        | `pytest apps/billing/tests/test_adapters.py::test_stripe_adapter_instantiates -x`    | Wave 0       |
| ADPTR-03 | All 8 abstract methods implemented in `StripeAdapter` (no `NotImplementedError` raised)                              | unit        | `pytest apps/billing/tests/test_adapters.py::test_stripe_adapter_full_method_set -x` | Wave 0       |
| ADPTR-04 | `import_string(settings.BILLING_ADAPTER)()` returns a `PaymentAdapter` instance                                      | unit        | `pytest apps/billing/tests/test_adapters.py::test_adapter_resolution -x`             | Wave 0       |
| ADPTR-05 | No `stripe` import in `PaymentAdapter` ABC class body                                                                | static/unit | `pytest apps/billing/tests/test_adapters.py::test_abc_has_no_stripe_import -x`       | Wave 0       |
| CUST-01  | `Customer` model fields exist: `user` (OneToOne), `stripe_customer_id` (blank), timestamps                           | unit        | `pytest apps/billing/tests/test_models.py::test_customer_model_fields -x`            | Wave 0       |
| CUST-02  | Creating a `User` auto-creates a `Customer` via signal                                                               | unit        | `pytest apps/billing/tests/test_signals.py::test_user_creation_creates_customer -x`  | Wave 0       |
| SUB-06   | `SubscriptionStatus.values` contains all 7 statuses; TextChoices validates correctly                                 | unit        | `pytest apps/billing/tests/test_models.py::test_subscription_status_choices -x`      | Wave 0       |
| PAY-02   | `0001_initial.py` creates all 5 tables (Customer, Subscription, Payment, ProcessedWebhookEvent, PlanProviderMapping) | migration   | `pytest apps/billing/tests/test_migrations.py::test_initial_migration_tables -x`     | Wave 0       |

### Sampling Rate

- **Per task commit:** `cd apps/api && pytest apps/billing/tests/ -x -q`
- **Per wave merge:** `cd apps/api && pytest apps/billing/ -v && python manage.py check`
- **Phase gate:** Full suite green + `manage.py migrate --run-syncdb` completes without error before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `apps/api/apps/billing/tests/__init__.py` — test package init
- [ ] `apps/api/apps/billing/tests/test_adapters.py` — covers ADPTR-01 through ADPTR-05
- [ ] `apps/api/apps/billing/tests/test_models.py` — covers CUST-01, SUB-06
- [ ] `apps/api/apps/billing/tests/test_signals.py` — covers CUST-02
- [ ] `apps/api/apps/billing/tests/test_migrations.py` — covers PAY-02
- [ ] `apps/api/apps/billing/tests/conftest.py` — shared fixtures (UserFactory, billing settings override)

---

## State of the Art

| Old Approach                                         | Current Approach                                        | When Changed                          | Impact                                                                             |
| ---------------------------------------------------- | ------------------------------------------------------- | ------------------------------------- | ---------------------------------------------------------------------------------- |
| `stripe.Customer.create(...)` (module-level calls)   | `StripeClient(...).customers.create(params={...})`      | stripe-python v8+                     | Must use `StripeClient`; legacy calls still work in v14 but are deprecated pattern |
| `stripe.UsageRecord.create(...)` for metered billing | Stripe Meter Events v2 API (`/v2/billing/meter_events`) | 2025-03-31 Stripe API version `basil` | Legacy `UsageRecord` removed; `record_usage` in adapter must use v2 endpoint       |
| dj-stripe as persistence layer                       | Raw `stripe` SDK + custom models                        | Ongoing architectural decision        | dj-stripe couples migrations to User model; adapter pattern incompatible           |

---

## Open Questions

1. **PlanProviderMapping: settings-dict sync strategy**
   - What we know: The `BILLING_PLANS` dict in settings and the `PlanProviderMapping` table can diverge
   - What's unclear: Should a management command or signal sync settings → DB on startup? Or is the DB the authoritative source and settings are just developer defaults?
   - Recommendation: For Phase 9, treat settings as the source of truth for plan definitions; `PlanProviderMapping` is populated by a management command (Phase 10). Phase 9 only creates the table.

2. **StripeAdapter method stubs vs. full implementations**
   - What we know: CONTEXT.md says "full method set defined upfront — do not stub and expand later"
   - What's unclear: Does "full" mean real Stripe API calls in all 8 methods, or can `record_usage` and `list_invoices` be minimal implementations given Phase 9 has no service layer to call them?
   - Recommendation: Implement real Stripe API calls in all 8 methods in Phase 9. They will not be called until Phase 10, but the contract must be exercisable by tests.

---

## Sources

### Primary (HIGH confidence)

- `.planning/research/SUMMARY.md` — Milestone-level research, all findings verified 2026-03-07
- `.planning/research/ARCHITECTURE.md` — Directory structure and adapter pattern verified against actual codebase
- `.planning/research/STACK.md` — Library versions verified against PyPI and Stripe releases
- `.planning/phases/09-billing-scaffold/09-CONTEXT.md` — Locked decisions (user-approved)
- `apps/api/apps/ai/` — Structural template (direct codebase inspection)
- [Python `abc` module docs](https://docs.python.org/3/library/abc.html) — ABC + abstractmethod pattern
- [Django TextChoices docs](https://docs.djangoproject.com/en/5.1/ref/models/fields/#enumeration-types) — TextChoices pattern
- [stripe-python v14 StripeClient](https://github.com/stripe/stripe-python) — Modern object-oriented API

### Secondary (MEDIUM confidence)

- Prior milestone research verified against Stripe changelog for 2025-03-31 basil API version

### Tertiary (LOW confidence)

- None for this phase — all patterns covered by official Django docs and prior verified research.

---

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — `stripe` v14 verified, Django ABC and TextChoices are stdlib/built-in
- Architecture: HIGH — directly mirrors existing `apps/api/apps/ai/` module structure confirmed in codebase
- Pitfalls: HIGH — adapter leakage, signal guard, StripeClient instantiation all verified patterns
- Test map: HIGH — pytest-django is established in CLAUDE.md; test file paths follow existing convention

**Research date:** 2026-03-07
**Valid until:** 2026-04-07 (stable Django/ABC patterns; verify `stripe` patch version at install time)
