# Project Research Summary

**Project:** Foundation Template — Billing & Payments Module
**Domain:** SaaS billing — subscriptions, one-time charges, usage-based billing, PDF invoices
**Researched:** 2026-03-07
**Confidence:** HIGH

## Executive Summary

This research covers the addition of a billing/payments module to the existing Foundation Template monorepo (Django Ninja Extra + Next.js 15 + Expo). The recommended approach centers on a `PaymentAdapter` ABC backed by Stripe as the first concrete implementation, with no dependency on dj-stripe. The key differentiator — and architectural constraint — is that the adapter interface is defined in domain terms rather than Stripe terms, allowing future providers (Paddle, LemonSqueezy) to be swapped in by changing a single Django settings value. No existing open-source SaaS template ships this combination of swappable adapter pattern, usage-based billing, and vendor-agnostic PDF invoice generation in the same module. That gap is the value proposition for building it correctly here.

The recommended library stack is deliberately minimal: `stripe` Python SDK v14 (raw, no dj-stripe), `weasyprint` for PDF generation, and `@stripe/react-stripe-js` v5 for the web frontend. The mobile app intentionally limits billing to a "Manage billing on web" handoff screen — Apple and Google mandate in-app purchases for digital goods sold in apps, making native Stripe billing a compliance problem rather than a technical one. Webhook infrastructure must be async-first from day one: Stripe retries on timeout, and synchronous webhook processing is the single most common cause of duplicate billing records and customer complaints.

The most dangerous pitfalls are not Stripe API mistakes — they are architectural mistakes made in Phase 1: letting Stripe concepts leak into the adapter interface, putting `stripe_customer_id` on the wrong model, or storing provider price IDs directly on Plan rows. These decisions calcify immediately once webhooks are live and cannot be fixed without a migration plus data backfill against the Stripe API. The build order specified in the architecture research — models first, adapter second, service third, HTTP layer fourth, frontend last — exists precisely to enforce that the interface is locked before any of these decisions become irreversible.

## Key Findings

### Recommended Stack

The billing module adds only 3 new Python packages and 2 new JS packages to the existing stack. Raw `stripe` SDK v14 is preferred over dj-stripe because dj-stripe conflicts with the adapter pattern (it is itself an opinionated Stripe-specific layer), introduces ~40 migrations that couple to the User model, and imposes a hard Django 5+ floor on every product using the template. WeasyPrint is chosen over ReportLab because it accepts HTML/CSS Django templates rather than a proprietary layout DSL, and over Stripe-hosted invoices because hosted PDFs expire and cannot be rebranded. No new Docker services are needed — WeasyPrint only requires native libraries (`libcairo2`, `libpango-1.0-0`, etc.) added to the existing API container Dockerfile.

**Core technologies:**

- `stripe` Python SDK `>=14.4,<15`: All Stripe API calls via the modern `StripeClient` pattern — v8+ object-oriented API, async-capable via `stripe[async]`
- `weasyprint` `>=68.1,<69`: HTML+CSS Django templates to PDF bytes — actively maintained (February 2026 release), pure Python, no headless browser
- `django-weasyprint` `>=2.4,<3`: Thin `WeasyTemplateResponseMixin` bridge for class-based views; single mixin class, no additional abstraction
- `@stripe/stripe-js` `^8.9.0`: Load Stripe.js and provide TypeScript types (npm package contributes types only; Stripe.js loads hosted)
- `@stripe/react-stripe-js` `^5.6.0`: `<Elements>` provider and `<PaymentElement>` — supports 18+ global payment methods from one integration

**Critical version notes:**

- Stripe Meter Events legacy API was removed in `2025-03-31.basil` — usage-based billing must use the new v2 Meter Events API, not legacy `UsageRecord`
- WeasyPrint v53+ replaced Cairo with pydyf as the PDF generator; pin to a specific minor version and test PDF output visually on every upgrade
- Expo SDK 53 compatible pin for `@stripe/stripe-react-native` must be verified in the CHANGELOG at install time (not resolvable at research time)

### Expected Features

Research identified a clear MVP boundary. The adapter interface is the spine that everything else hangs from; it must be designed and locked before implementation begins.

**Must have (table stakes for billing module launch):**

- `PaymentAdapterProtocol` (or ABC) interface defined in domain terms — no Stripe-specific types in the abstract class
- `StripeAdapter` concrete implementation against the full protocol, using `StripeClient` (v8+ pattern)
- `Customer` model (OneToOne to User, `stripe_customer_id` populated lazily, created via `post_save` signal)
- `Subscription` model with internal `SubscriptionStatus` enum (not Stripe status strings), `cancel_at_period_end` flag, and timestamp audit fields
- Subscription lifecycle via Checkout: create, upgrade, downgrade, cancel, reactivate, trial period support
- Access gating decorator (`@require_active_subscription`) checking both `status` and `cancel_at_period_end`
- 6 Tier-1 webhook event handlers with idempotency guard (`ProcessedWebhookEvent` table + `unique_together` constraint)
- Async webhook processing dispatched to task queue (Celery or Django-Q2); webhook view returns 200 immediately after signature verification
- PDF invoice generation via WeasyPrint dispatched as a Celery task (never in the request cycle)
- `/billing` Next.js page: `<PlanGrid>`, `<CurrentPlanBadge>`, `<InvoiceHistoryTable>`, `<UpgradeModal>` with proration preview
- Stripe Customer Portal redirect for payment method management (no custom payment form)
- `BILLING_ENABLED` feature flag; `# BILLING_START` / `# BILLING_END` comment delimiters in `config/urls.py` for CLI scaffolder

**Should have (competitive differentiators):**

- Proration preview before upgrade confirmation (call `stripe.Invoice.create_preview()`)
- `PlanProviderMapping` table mapping internal plan IDs to provider price IDs (no `stripe_price_id` on Plan model)
- Usage-based billing endpoints and `<UsageMeter>` UI (add when the first product using the template needs it)
- Tier-2 webhook handlers: `invoice.created`, `invoice.finalized`, `customer.subscription.trial_will_end`
- `/billing/return` Next.js page handling post-3DS redirect query params
- `past_due` banner in the dashboard when subscription payment fails

**Defer to post-MVP:**

- Usage event batching via Stripe Meter Event Streams API (needed only at high scale)
- LemonSqueezy or Paddle adapter (validate the protocol design with Stripe first)
- Pause subscription support (`pause_collection` on Stripe)
- Refund management admin UI
- PDF caching to file storage (serve on-demand generation first)
- Mobile in-app subscription management (requires Apple/Google IAP compliance — product decision)

**Anti-features (explicitly do not build):**

- Direct Stripe SDK calls in views — all calls must go through the `PaymentAdapter`
- dj-stripe as persistence layer — breaks the adapter pattern and adds migration coupling
- Custom payment method update form — PCI scope expansion; delegate to Stripe Customer Portal
- Synchronous webhook event processing in the HTTP handler — return 200 immediately, process async
- Coupling subscription status to `User.is_active` — blocks login when past due, prevents self-service payment method updates
- Hardcoded plan definitions in Python code — use `BILLING_PLANS` dict in Django settings

### Architecture Approach

The billing module is a self-contained Django app at `apps/api/apps/billing/` that mirrors the existing AI module pattern: registered conditionally in `INSTALLED_APPS`, auto-discovered by the Ninja Extra controller registry, and cleanly removable by the CLI scaffolder. The webhook endpoint is a plain Django view — not a Ninja controller — registered before `api.urls` in the URL conf to guarantee raw bytes access for Stripe HMAC signature verification. The `Customer` model extends User via OneToOne (not AbstractUser subclassing), so removing the billing app requires only deleting the directory and removing one `INSTALLED_APPS` entry with no schema changes to the users table.

**Major components:**

1. `apps/api/apps/billing/adapters.py` — `PaymentAdapter` ABC + `StripeAdapter`; all Stripe SDK calls live here and nowhere else
2. `apps/api/apps/billing/services.py` — `BillingService` with business rules; orchestrates adapter + models; fully unit-testable with a stub adapter (no HTTP dependency)
3. `apps/api/apps/billing/controllers.py` — Ninja Extra HTTP layer; auth, request validation, response serialization only; never imports `stripe`
4. `apps/api/apps/billing/webhooks.py` — Plain `@csrf_exempt` Django view; raw body ingestion, signature verification dispatch, returns 200 immediately
5. `apps/api/apps/billing/models.py` — `Customer`, `Subscription`, `ProcessedWebhookEvent`; all status fields use internal enums, not Stripe string literals
6. `apps/web/app/(dashboard)/billing/` — Four billing pages: overview, checkout, success, portal redirect; components in `apps/web/components/billing/`
7. `packages/api-client/` — Billing TypeScript types propagate automatically through the existing `turbo generate:api-types` pipeline; no extra configuration needed

**Complete upgrade data flow:** User clicks upgrade → `BillingController.create_checkout_session()` → `BillingService.get_or_create_stripe_customer()` → `StripeAdapter.create_checkout_session()` → Stripe hosted page → user completes payment → Stripe POSTs webhook → `stripe_webhook_view()` reads raw bytes → HMAC verification → `BillingService.handle_webhook_event()` routes to handler → `Subscription.status = "active"` → return HTTP 200 → browser redirects to `/billing/success`.

### Critical Pitfalls

1. **Leaky adapter abstraction** — Stripe status strings, Stripe customer IDs, or Stripe price IDs appearing in the ABC or service layer will require touching every call site when a second provider is added. Define the interface in domain terms first; write the Stripe adapter second. The word "stripe" must never appear in an abstract method signature. Address in Phase 1 before any implementation begins. Recovery cost: HIGH.

2. **Webhook idempotency gap** — Without a `ProcessedWebhookEvent` table with a `unique_together` constraint on `(provider, event_id)` plus an atomic `get_or_create`, a single subscription creation can be processed twice due to Stripe's at-least-once delivery guarantee. Duplicate billing records require manual reconciliation with the Stripe API. Address in Phase 2 as the first step before any handler logic. Recovery cost: HIGH.

3. **Wrong event wiring** — Three specific mistakes: using `payment_intent.succeeded` for subscription renewal (fires for ALL PaymentIntents, not just first subscription), using `customer.subscription.updated` to grant/revoke access (fires on metadata changes, trial extensions, payment method changes), and not distinguishing Checkout `mode: "subscription"` from `mode: "payment"` in a shared handler. Address in Phase 2 with an explicit documented event routing table. Recovery cost: MEDIUM.

4. **Billing data model decisions that harden too early** — Storing `stripe_price_id` directly on Plan rows, using Stripe status strings without an internal enum, omitting `cancel_at_period_end` as an explicit model field, and having no timestamp audit trail for status transitions all become painful to change once webhooks are live. Address in Phase 1 with a `PlanProviderMapping` table and an internal `SubscriptionStatus` enum. Recovery cost: HIGH.

5. **WeasyPrint memory leak and Docker font failures** — Each PDF generated in a Django worker increases process RSS by 17–40MB, unreleased until restart. System fonts are absent from `python:3.12-slim`, causing silent font fallback or `URLFetchingError` for custom fonts. Always generate PDFs in a Celery task, import `weasyprint` inside the task function (not at module level), and install `fonts-liberation` in the Dockerfile. Address in Phase 4. Recovery cost: LOW to fix, but OOM kills in production require immediate attention.

## Implications for Roadmap

Based on the architecture research's explicit build-order analysis and the pitfalls' phase-specific warnings, a 4-phase structure is recommended. Each phase is designed so its output is independently testable before the next phase begins.

### Phase 1: Billing Module Scaffold — Data Model + Adapter Interface

**Rationale:** All downstream components depend on the data model and adapter interface being locked. Changing the interface after the service and webhook layers exist requires touching every call site. This is the highest-leverage phase to get right, and also the one where mistakes are most expensive to reverse. The interface must be designed before any Stripe-specific code is written.
**Delivers:** `Customer`, `Subscription`, `ProcessedWebhookEvent` Django models + initial migration; `PaymentAdapter` ABC with full domain-centric method signatures; `StripeAdapter` concrete implementation; settings configuration (`BILLING_ADAPTER`, `STRIPE_*` env vars, `BILLING_PLANS` dict); `BillingConfig.ready()` signal auto-creating `Customer` on User creation; CLI scaffolder isolation established (comment delimiters in `urls.py`, conditional `INSTALLED_APPS`, `[billing]` extras group in `pyproject.toml`).
**Addresses features:** PaymentAdapterProtocol interface, Customer/Subscription data model, `BILLING_ENABLED` feature flag, `PlanProviderMapping` table.
**Avoids:** Pitfalls 1 (leaky abstraction), 4 (wrong data model decisions), 10 (hard-to-remove module).
**Research flag:** Standard Django and ABC patterns — no additional research needed. Build order: models → adapter → settings → signal → CLI isolation markers.

### Phase 2: Webhook Infrastructure + Service Layer

**Rationale:** The service layer (`BillingService`) is independently unit-testable with a stubbed adapter before any HTTP layer exists. Webhook infrastructure must be built and locally verified (via Stripe CLI forwarding) before any end-to-end checkout testing is possible in Phase 3. Idempotency and event routing must be established as the first act of this phase — not added after handlers exist.
**Delivers:** `BillingService` with `get_or_create_stripe_customer`, `create_checkout_session`, `create_portal_session`, `cancel_subscription`, and `handle_webhook_event` (dispatcher); `stripe_webhook_view` plain Django view registered with `# BILLING_START` delimiter; Tier-1 webhook event handlers for 6 essential events; `ProcessedWebhookEvent` idempotency guard with `unique_together` + atomic `get_or_create`; async Celery task dispatch from webhook view; 3-layer test strategy scaffolded (unit / integration with stripe-mock / contract).
**Uses:** `stripe` SDK v14 (`StripeClient` pattern), task queue (Celery or Django-Q2), `stripe-mock` Docker image for integration tests.
**Avoids:** Pitfalls 2 (no idempotency), 3 (wrong event mapping), 6 (synchronous webhook timeout), 11 (testing gaps including signature verification bypass).
**Research flag:** Standard Stripe webhook patterns — no additional research needed. One dependency to resolve before this phase: confirm which task queue (Celery vs. Django-Q2) is used in the target product, as task dispatch patterns differ slightly.

### Phase 3: API Endpoints + Plan Management + Frontend Billing UI

**Rationale:** The HTTP layer and frontend can only be built after the service layer is proven. Plan management (upgrade/downgrade proration) has the most product-specific decisions and should be designed as a unit with the frontend that surfaces those flows. 3DS/SCA handling and return URL management belong here — not as a follow-up.
**Delivers:** `BillingController` Ninja Extra endpoints (checkout session, portal session, subscription CRUD, invoice list, invoice PDF download); Pydantic schemas automatically propagated to TypeScript types via `turbo generate:api-types`; `/billing` Next.js page with `<PlanGrid>`, `<CurrentPlanBadge>`, `<InvoiceHistoryTable>`, `<UpgradeModal>` (proration preview via `stripe.Invoice.create_preview()`); Stripe Customer Portal redirect button; `/billing/return` page with 3DS result handling using `redirect: 'if_required'`; `past_due` subscription banner.
**Implements:** `BillingController` (HTTP layer) and all frontend billing components.
**Avoids:** Pitfalls 5 (upgrade/downgrade proration errors — requires explicit decision before implementation), 9 (missing 3DS / return URL handler), 12 (Stripe publishable key not embedded in OpenAPI spec), 13 (custom UI replacing what Customer Portal handles better), 14 (currency-unaware amount display).
**Research flag:** The proration strategy decision (direct `stripe.Subscription.modify()` vs. `stripe.SubscriptionSchedule`) should be made and documented before implementation of upgrade/downgrade endpoints. Mixing the two approaches causes `subscription_already_has_schedule` errors. This is a small but consequential fork that benefits from a focused pre-planning decision.

### Phase 4: Invoice Generation + CLI Scaffolder Integration

**Rationale:** PDF generation is a self-contained feature with its own infrastructure concerns (Celery task, Docker fonts, WeasyPrint version pinning) and should be treated as a separate deliverable after the core billing flow is end-to-end working. CLI scaffolder integration is last because the removal path should only be finalized and tested once the module is stable.
**Delivers:** `weasyprint` and `django-weasyprint` in a `[billing]` extras group in `pyproject.toml`; Celery task for async PDF generation (`import weasyprint` inside task function, not at module level); Django HTML template for invoice PDF (`billing/invoice.html`) with `@page` CSS margin rules; `fonts-liberation` and `fonts-dejavu-core` in API Dockerfile; `GET /api/billing/invoices/{id}/pdf/` endpoint wired to the async generation task; `removeBillingModule()` function in the CLI scaffolder; scaffolder integration test verifying `manage.py check` passes with `"apps.billing"` removed from `INSTALLED_APPS`.
**Avoids:** Pitfalls 7 (WeasyPrint memory leak and Docker font failures), 10 (hard-to-remove module — final verification that removal is clean).
**Research flag:** Standard WeasyPrint + Celery patterns — no additional research needed. Verify WeasyPrint version (currently `>=68.1,<69`) at install time before pinning in `pyproject.toml`.

### Phase Ordering Rationale

- **Models before everything** because Django migrations are the one decision that cannot be refactored without a data backfill on a live system. Phase 1 forces model and interface design under research context rather than time pressure during implementation.
- **Service before HTTP** because `BillingService` can be fully unit-tested with a stub adapter before any API endpoint exists, giving high confidence in business logic before the HTTP layer introduces noise.
- **Webhook infrastructure in Phase 2, not Phase 3** because Stripe CLI local forwarding is required to test end-to-end checkout in Phase 3. The webhook endpoint must exist and return valid 200 responses before any checkout session test is meaningful.
- **Frontend last in Phase 3** because it depends on TypeScript types generated from Ninja Extra schemas, which can only be generated after Django app registration and a running API.
- **CLI scaffolder in Phase 4** because the module must be stable before the removal path is defined and tested. Testing removal of a still-changing module produces constant rework.

### Research Flags

Phases needing a focused decision or spike before implementation:

- **Phase 3 (proration strategy):** Before implementing upgrade/downgrade endpoints, decide on `stripe.Subscription.modify()` with `proration_behavior="always_invoice"` vs. `stripe.SubscriptionSchedule` for deferred downgrades, and document the rule. Do not mix approaches. This is a 30-minute decision spike, not a multi-day research spike.

Phases with well-documented patterns (skip research-phase):

- **Phase 1:** Django OneToOne User extension, ABC pattern, settings-driven adapter injection — all have official Django documentation and established community patterns.
- **Phase 2:** Stripe webhook HMAC verification, idempotency with `get_or_create` + `unique_together`, Celery async dispatch — all covered by official Stripe and Django documentation.
- **Phase 4:** WeasyPrint + Celery — documented WeasyPrint memory issue with a known and tested mitigation; no novel integration.

## Confidence Assessment

| Area         | Confidence | Notes                                                                                                                                                                                                                                                                                             |
| ------------ | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Stack        | HIGH       | All library choices verified against PyPI, npm, and official Stripe docs as of March 2026. Stripe SDK v14.4, WeasyPrint 68.1, and @stripe/react-stripe-js v5.6.0 are confirmed current. Exact patch versions should be re-verified at install time — Stripe releases frequently.                  |
| Features     | HIGH       | Stripe-specific features sourced from official Stripe documentation (HIGH). Adapter interface method signatures are opinionated design choices (MEDIUM) grounded in multiple community sources and the actual Stripe API surface. PDF generation ecosystem is stable.                             |
| Architecture | HIGH       | Grounded in direct codebase inspection of the existing AI module pattern in `apps/api/apps/ai/`, `config/urls.py`, `config/settings/base.py`, and the CLI scaffolder spec. Build order reflects the actual dependency graph, not convention.                                                      |
| Pitfalls     | HIGH       | Webhook idempotency, event routing errors, and WeasyPrint memory leak are confirmed in official Stripe documentation, Django ticket #34356, and WeasyPrint GitHub issues respectively. Adapter leakage and removability pitfalls are grounded in architectural analysis of the existing codebase. |

**Overall confidence:** HIGH

### Gaps to Address

- **Stripe React Native Expo SDK 53 pin:** The exact compatible version of `@stripe/stripe-react-native` for Expo SDK 53 was not pinned in research — "verify in CHANGELOG at install time" is the guidance. Resolve this at the start of Phase 3 before any mobile billing work begins.
- **Proration strategy decision:** Research documented both `Subscription.modify()` and `SubscriptionSchedule` approaches and the pitfall of mixing them, but prescribing which to use requires a product decision. Resolve in Phase 3 planning, document the choice in a spec, and never deviate from it within the module.
- **Task queue selection:** The core Foundation Template stack leaves task queue choice open (Celery, Django-Q2, or Huey). Billing requires a task queue for webhook async dispatch and PDF generation. Confirm which queue is active in the target product before Phase 2 begins — the dispatch pattern differs between Celery (`task.delay()`) and Django-Q2 (`async_task()`).
- **`BILLING_PLANS` configuration schema:** Research recommends a `BILLING_PLANS` settings dict rather than hardcoded plan definitions, but does not prescribe the exact dict structure. Design the schema (keys, nested structure, meter ID mapping) in Phase 1 planning before the `Plan` model and `PlanProviderMapping` table decisions are finalized.

## Sources

### Primary (HIGH confidence)

- [Stripe Python SDK GitHub](https://github.com/stripe/stripe-python) — StripeClient v8+ API, async support via `stripe[async]`, full changelog
- [Stripe Webhook Documentation](https://docs.stripe.com/webhooks/signature) — HMAC signature verification, raw body requirement, at-least-once delivery guarantee
- [Stripe Billing Subscriptions Webhooks](https://docs.stripe.com/billing/subscriptions/webhooks) — event taxonomy, subscription lifecycle, idempotency guidance
- [Stripe Meter Events API v2](https://docs.stripe.com/api/v2/billing-meter) — usage-based billing recording via new Meter Events endpoint
- [Stripe Changelog 2025-03-31.basil](https://docs.stripe.com/changelog/basil/2025-03-31/deprecate-legacy-usage-based-billing) — legacy `UsageRecord` API removal
- [Stripe Customer Portal API](https://docs.stripe.com/customer-management/integrate-customer-portal) — `billing_portal.Session.create()` pattern
- [WeasyPrint Documentation](https://doc.courtbouillon.org/weasyprint/stable/) — system dependencies, v53 pydyf migration, Docker setup
- [@stripe/react-stripe-js npm](https://www.npmjs.com/package/@stripe/react-stripe-js) — v5.6.1, `PaymentElement`, `redirect: 'if_required'` pattern
- [dj-stripe 2.10.0 release notes](https://dj-stripe.dev/docs/dev/changes/2_10_0) — migration reset, Django 5+ floor (primary basis for NOT using dj-stripe)
- [Django Documentation — OneToOne User extension](https://docs.djangoproject.com/en/4.2/topics/auth/customizing/) — safe User model extension patterns
- Existing codebase — `apps/api/apps/ai/` module pattern, `config/urls.py`, `config/settings/base.py`, `openspec/specs/foundation/cli-scaffolder.md`

### Secondary (MEDIUM confidence)

- [Medium — Integrating Stripe Billing with Django 6.0](https://medium.com/django-journal/integrating-stripe-billing-with-django-6-0-333aa65cf1e6) — Django async webhook patterns, async view examples
- [Simon Willison's TIL — Mocking Stripe signature in pytest](https://til.simonwillison.net/pytest/pytest-stripe-signature) — HMAC test fixture pattern for signed payloads
- [stripe-mock GitHub](https://github.com/stripe/stripe-mock) — official Stripe mock API Docker image for integration tests
- [Mastering Stripe Subscription Upgrades](https://engineeringjournal.substack.com/p/mastering-stripe-subscription-upgrades) — proration edge cases and `subscription_already_has_schedule` error
- [Stripe Webhooks: Solving Race Conditions](https://www.pedroalonso.net/blog/stripe-webhooks-solving-race-conditions/) — idempotency patterns and race condition analysis
- [Expo Documentation — Stripe React Native](https://docs.expo.dev/versions/latest/sdk/stripe/) — managed workflow config plugin (Expo SDK 53 pin requires verification at install time)
- [Adam Johnson — Building webhook receivers in Django](https://adamj.eu/tech/2021/05/09/how-to-build-a-webhook-receiver-in-django/) — plain view vs. DRF/Ninja pattern rationale
- [WeasyPrint GitHub — memory issues](https://github.com/Kozea/WeasyPrint) — RSS growth per generation confirmed in issues; Celery task workaround documented

### Tertiary (LOW confidence)

- [Architecture Patterns for SaaS Platforms](https://medium.com/appfoster/architecture-patterns-for-saas-platforms-billing-rbac-and-onboarding-964ea071f571) — general adapter pattern context; no version-specific verification

---

_Research completed: 2026-03-07_
_Ready for roadmap: yes_
