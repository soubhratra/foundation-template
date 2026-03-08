# Requirements: Foundation Template

**Defined:** 2026-03-07
**Core Value:** A new SaaS product goes from zero to running full-stack app (web + mobile + API + auth) in under 5 minutes with one command.

## v1.1 Requirements

Requirements for the Billing & Payments Module milestone. Each maps to roadmap phases (9–12).

### Adapter Pattern (ADPTR)

- [x] **ADPTR-01**: `PaymentAdapter` Protocol defined in domain terms — no provider-specific types in abstract interface
- [x] **ADPTR-02**: `StripeAdapter` concrete implementation against the full protocol using `StripeClient` v14
- [x] **ADPTR-03**: Adapter is settings-configurable (`BILLING_ADAPTER` setting) — swappable by changing one Django setting
- [x] **ADPTR-04**: `BILLING_PLANS` dict in Django settings defines plan structure (no hardcoded plans in code)
- [x] **ADPTR-05**: `PlanProviderMapping` table maps internal plan IDs to provider price IDs (no `stripe_price_id` on Plan model)

### Customer Management (CUST)

- [x] **CUST-01**: `Customer` model with OneToOne link to User, `stripe_customer_id` populated lazily on first billing interaction
- [x] **CUST-02**: Customer auto-created via `post_save` signal when a User is created
- [ ] **CUST-03**: `@require_active_subscription` access-gating decorator checks subscription status and `cancel_at_period_end`

### Subscriptions (SUB)

- [x] **SUB-01**: User can start a subscription via Stripe Checkout session
- [x] **SUB-02**: User can upgrade their subscription plan (with proration preview before confirming)
- [x] **SUB-03**: User can downgrade their subscription plan
- [x] **SUB-04**: User can cancel their subscription (cancels at period end, not immediately)
- [x] **SUB-05**: User can reactivate a cancelled subscription before period end
- [x] **SUB-06**: `Subscription` model uses internal `SubscriptionStatus` enum (not raw Stripe status strings), includes `cancel_at_period_end` and timestamp audit fields

### One-Time Payments (PAY)

- [x] **PAY-01**: User can complete a one-time payment via Stripe Checkout session
- [x] **PAY-02**: One-time payment is recorded as a `Payment` model entry with status and amount

### Usage-Based Billing (USAGE)

- [x] **USAGE-01**: API endpoint to record usage events via Stripe Meter Events v2 API
- [x] **USAGE-02**: API endpoint to retrieve current metered usage for the billing period

### Webhook Infrastructure (HOOK)

- [ ] **HOOK-01**: Plain Django view (not Ninja controller) receives Stripe webhook events with raw body for HMAC signature verification
- [ ] **HOOK-02**: Webhook view returns HTTP 200 immediately after signature verification; processing dispatched to async task queue
- [ ] **HOOK-03**: `ProcessedWebhookEvent` table with `unique_together(provider, event_id)` prevents duplicate processing
- [ ] **HOOK-04**: Tier-1 event handlers implemented: `checkout.session.completed`, `customer.subscription.created`, `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.payment_succeeded`, `invoice.payment_failed`

### Invoice & PDF (INV)

- [ ] **INV-01**: API endpoint returns paginated list of invoices for the authenticated user
- [ ] **INV-02**: User can download an invoice as a server-generated PDF (WeasyPrint + Jinja2 template)
- [ ] **INV-03**: PDF generation runs as an async Celery task (never in the request cycle)

### Billing Frontend (BILL)

- [ ] **BILL-01**: `/billing` page displays current plan, billing period, and next renewal date
- [ ] **BILL-02**: `/billing` page displays payment history table with status and invoice download links
- [ ] **BILL-03**: User can initiate plan upgrade/downgrade from the billing page (with proration preview modal)
- [ ] **BILL-04**: User can cancel their subscription from the billing page
- [ ] **BILL-05**: `/billing/return` page handles post-Stripe-Checkout redirect (including 3DS/SCA result)
- [ ] **BILL-06**: Stripe Customer Portal redirect available for payment method management
- [ ] **BILL-07**: `past_due` subscription banner displayed in dashboard when payment fails

### CLI Scaffolder Integration (SCAFF)

- [ ] **SCAFF-01**: Billing module included by default when creating a new project with `create-foundation-app`
- [ ] **SCAFF-02**: User can exclude billing module via `--without billing` flag (or interactive prompt) in the scaffolder
- [ ] **SCAFF-03**: Billing removal deletes `apps/api/apps/billing/`, frontend billing pages, billing deps, and comment-delimited config blocks
- [ ] **SCAFF-04**: CI test verifies `manage.py check` passes with billing removed from `INSTALLED_APPS`

## v2 Requirements

Deferred to future release.

### Usage-Based Billing (Advanced)

- **USAGE-03**: Usage event batching via Stripe Meter Event Streams API (needed at high scale)
- **USAGE-04**: `<UsageMeter>` frontend component showing current period consumption

### Additional Providers

- **PRVDR-01**: Paddle adapter implementing `PaymentAdapter` Protocol
- **PRVDR-02**: LemonSqueezy adapter implementing `PaymentAdapter` Protocol

### Advanced Billing Features

- **BILL-08**: Pause subscription support (`pause_collection` on Stripe)
- **BILL-09**: Refund management admin UI
- **BILL-10**: PDF invoice caching to file storage (S3/R2)
- **BILL-11**: Mobile in-app subscription management (requires Apple/Google IAP compliance decision)
- **BILL-12**: Tier-2 webhook handlers: `invoice.created`, `invoice.finalized`, `customer.subscription.trial_will_end`

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature                                          | Reason                                                                                     |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------ |
| dj-stripe as persistence layer                   | Breaks adapter pattern, adds ~40 migrations coupling to User model, forces Django 5+ floor |
| Custom payment method form                       | PCI scope expansion — delegate to Stripe Customer Portal instead                           |
| Synchronous webhook processing                   | Stripe's at-least-once delivery requires async dispatch to avoid duplicates                |
| `stripe_price_id` directly on Plan model         | Hardcodes provider coupling — use `PlanProviderMapping` table instead                      |
| Coupling subscription status to `User.is_active` | Blocks login when past due, prevents self-service recovery                                 |
| Apple IAP / Google Play Billing                  | Platform policy and compliance decision — out of scope for template                        |
| Stripe-hosted invoice PDFs                       | Expire, cannot be rebranded — server-side generation required                              |
| Admin billing dashboard                          | Django admin sufficient; no custom admin UI in template scope                              |

## Traceability

Which phases cover which requirements. Populated during roadmap creation.

| Requirement | Phase | Status   |
| ----------- | ----- | -------- |
| ADPTR-01    | 9     | Complete |
| ADPTR-02    | 9     | Complete |
| ADPTR-03    | 9     | Complete |
| ADPTR-04    | 9     | Complete |
| ADPTR-05    | 9     | Complete |
| CUST-01     | 9     | Complete |
| CUST-02     | 9     | Complete |
| SUB-06      | 9     | Complete |
| PAY-02      | 9     | Complete |
| HOOK-01     | 10    | Pending  |
| HOOK-02     | 10    | Pending  |
| HOOK-03     | 10    | Pending  |
| HOOK-04     | 10    | Pending  |
| SUB-01      | 10    | Complete |
| SUB-02      | 10    | Complete |
| SUB-03      | 10    | Complete |
| SUB-04      | 10    | Complete |
| SUB-05      | 10    | Complete |
| PAY-01      | 10    | Complete |
| USAGE-01    | 10    | Complete |
| USAGE-02    | 10    | Complete |
| CUST-03     | 10    | Pending  |
| INV-01      | 11    | Pending  |
| BILL-01     | 11    | Pending  |
| BILL-02     | 11    | Pending  |
| BILL-03     | 11    | Pending  |
| BILL-04     | 11    | Pending  |
| BILL-05     | 11    | Pending  |
| BILL-06     | 11    | Pending  |
| BILL-07     | 11    | Pending  |
| INV-02      | 12    | Pending  |
| INV-03      | 12    | Pending  |
| SCAFF-01    | 12    | Pending  |
| SCAFF-02    | 12    | Pending  |
| SCAFF-03    | 12    | Pending  |
| SCAFF-04    | 12    | Pending  |

**Coverage:**

- v1.1 requirements: 36 total
- Mapped to phases: 36
- Unmapped: 0 ✓

---

_Requirements defined: 2026-03-07_
_Last updated: 2026-03-07 — traceability populated after roadmap creation_
