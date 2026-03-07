# Phase 9: Billing Scaffold - Context

**Gathered:** 2026-03-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Create the billing module's foundational layer: Django data models (Customer, Subscription, Payment, ProcessedWebhookEvent), the PaymentAdapter ABC with full method set, the StripeAdapter concrete implementation, settings configuration, and module isolation markers. No HTTP endpoints, no webhook processing logic, no frontend in this phase. The goal is to lock the interface and data model before any service or HTTP code is written.

</domain>

<decisions>
## Implementation Decisions

### Adapter Pattern Style

- **Use ABC (abstract base class), not Protocol** — explicit inheritance enforces the contract at class definition; missing methods raise TypeError immediately
- `StripeAdapter(PaymentAdapter)` — enforces contract via inheritance, easier for developers to discover and implement
- The word "stripe" must never appear in any abstract method signature or return type (domain-centric interface)

### Adapter Method Set

- Define the **full method set upfront** in Phase 9 — do not stub and expand later
- Full set: `create_customer`, `create_checkout_session` (handles both subscription and one-time mode), `create_portal_session`, `cancel_subscription`, `modify_subscription` (for upgrade/downgrade), `construct_webhook_event`, `record_usage`, `list_invoices`
- `StripeAdapter` implements all methods against `stripe.StripeClient` v14 pattern
- Adapter resolved via settings: `BILLING_ADAPTER = "apps.billing.adapters.StripeAdapter"` using `import_string()`

### BILLING_PLANS Settings Structure

- Full plan tier dict with provider price mapping + feature lists + trial config
- Structure:
  ```python
  BILLING_PLANS = {
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
  }
  ```
- `PlanProviderMapping` table in DB maps internal plan IDs to provider price IDs (runtime resolution, not hardcoded)
- Template ships with example free/pro/enterprise keys as placeholders

### Models in Phase 9 Migration

- **All 4 models ship in the initial migration** (`0001_initial.py`):
  1. `Customer` — OneToOne → User, `stripe_customer_id` (blank until first billing interaction), timestamps
  2. `Subscription` — FK → Customer (OneToOne), `stripe_subscription_id`, `status` (TextChoices), `cancel_at_period_end`, period timestamps
  3. `Payment` — FK → Customer, `stripe_payment_intent_id`, `amount` (DecimalField), `currency`, `status`, timestamps
  4. `ProcessedWebhookEvent` — `provider`, `event_id`, `unique_together(provider, event_id)`, `processed_at`
- Avoids a second migration in Phase 10 just for ProcessedWebhookEvent

### SubscriptionStatus Enum

- **Django TextChoices** — integrates natively with ORM, readable in admin, auto-validates on assignment
- **Full set matching Stripe statuses** (no translation layer needed in webhook handlers):
  - `active`, `past_due`, `canceled`, `trialing`, `incomplete`, `incomplete_expired`, `unpaid`

### Settings Configuration

- `BILLING_ADAPTER = "apps.billing.adapters.StripeAdapter"` — swappable by changing one setting
- `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET` — in `.env.example` under `# BILLING MODULE` / `# END BILLING MODULE` delimiters
- `BILLING_PLANS` dict in `config/settings/base.py`

### Module Isolation (Scaffolder Markers)

- All billing code in `apps/api/apps/billing/` — no other Django app imports from `apps.billing`
- `"apps.billing"` in `INSTALLED_APPS` (stripped by scaffolder)
- Webhook URL in `config/urls.py` wrapped in `# BILLING_START` / `# BILLING_END` markers (done in Phase 9 even though webhook view comes in Phase 10 — markers go around the import block)
- `stripe` in a dedicated `[billing]` extras group in `pyproject.toml`

### Auto-Create Signal

- `signals.py` — `post_save` on User → `Customer.objects.get_or_create(user=instance)`
- Registered in `BillingConfig.ready()` in `apps.py`

### Claude's Discretion

- `PlanProviderMapping` model field names and indexing strategy
- Admin registration (CustomerAdmin, SubscriptionAdmin) — register all models in `admin.py`
- Migration field ordering and index choices
- `.env.example` comment formatting for billing vars
- Whether to add a `stripe_price_id` field to `PlanProviderMapping` vs resolving via the settings dict at service layer

</decisions>

<code_context>

## Existing Code Insights

### Reusable Assets

- `apps/api/apps/ai/` — exact structural template: `__init__.py`, `apps.py`, `models.py`, `schemas.py`, `controllers.py`, `services.py`, `tasks.py`, `migrations/`
- `apps/api/apps/accounts/models.py` — existing `User(AbstractUser)` — billing Customer uses `OneToOneField(settings.AUTH_USER_MODEL)` to avoid any modification to this file
- `config/settings/base.py` — existing `env()` pattern for env vars, existing `INSTALLED_APPS` list to extend

### Established Patterns

- Django app structure: `apps.py` with `AppConfig.ready()` for signal registration (same as accounts app)
- `api.auto_discover_controllers()` in `config/urls.py` — billing controller auto-discovered with zero URL conf changes
- Optional module removal: comment-delimited blocks in `config/urls.py` + `INSTALLED_APPS` line + extras dep group (AI module pattern)

### Integration Points

- `config/settings/base.py` — add `"apps.billing"` to `INSTALLED_APPS`, add `BILLING_*` settings
- `config/urls.py` — add `# BILLING_START` / `# BILLING_END` delimited import block (webhook registration comes Phase 10, but markers go in now)
- `apps/api/pyproject.toml` — add `stripe>=14.4,<15` to `[billing]` extras group

</code_context>

<specifics>
## Specific Ideas

- Template should demonstrate patterns, not solve specific use cases (same philosophy as AI module)
- Document extension points clearly — future developers extending for a specific product should be able to follow instructions for agentic development
- Example plan tiers (free/pro/enterprise) are illustrative placeholders — template users replace with their own Stripe price IDs

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within Phase 9 scope.

</deferred>

---

_Phase: 09-billing-scaffold_
_Context gathered: 2026-03-07_
