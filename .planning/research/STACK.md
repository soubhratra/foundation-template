# Stack Research: Billing & Payments Module (v1.1)

**Project:** Foundation Template — billing/payments milestone
**Domain:** SaaS billing — subscriptions, one-time charges, usage-based billing, PDF invoices
**Researched:** 2026-03-07
**Overall confidence:** HIGH for library choices; MEDIUM for exact patch versions (verify at install time)

> **Scope note:** This document covers ONLY the net-new libraries needed for the billing/payments
> module. The core stack (Django Ninja Extra, Next.js 15+, Expo SDK 53+, LangGraph, Django Allauth,
> Turborepo, pnpm, pytest, Vitest, etc.) is already decided and is NOT re-researched here.
> The v1.0 foundation stack research is archived in `.planning/phases/` phase CONTEXT files.

---

## Decision Summary

| Concern                       | Chosen Library                       | Version Pin                | Confidence |
| ----------------------------- | ------------------------------------ | -------------------------- | ---------- |
| Stripe Python SDK             | `stripe`                             | `>=14.4,<15`               | HIGH       |
| Django Stripe sync layer      | raw `stripe` SDK only (no dj-stripe) | —                          | HIGH       |
| PDF invoice generation        | `weasyprint`                         | `>=68.1,<69`               | HIGH       |
| Django template to PDF bridge | `django-weasyprint`                  | `>=2.4,<3`                 | MEDIUM     |
| Stripe JS (web)               | `@stripe/stripe-js`                  | `^8.9.0`                   | HIGH       |
| Stripe React components (web) | `@stripe/react-stripe-js`            | `^5.6.0`                   | HIGH       |
| Stripe React Native (mobile)  | `@stripe/stripe-react-native`        | Expo-SDK-53-compatible pin | MEDIUM     |

**One-liner:** `stripe` (Python v14) + `weasyprint` + `@stripe/react-stripe-js` v5 — no dj-stripe,
no server-side invoice rendering via Stripe's hosted portal.

---

## Python / Backend

### Core Stripe SDK

| Technology | Version      | Purpose                                                                     | Why                                                                                                                                                                                                                                                                                                                                          |
| ---------- | ------------ | --------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `stripe`   | `>=14.4,<15` | All Stripe API calls — subscriptions, charges, meters, webhook verification | Official Stripe Python SDK, maintained by Stripe. v14.4 pins API version `2026-02-25.clover` (confirmed via stripe-python releases, March 6, 2026). v8+ introduced `StripeClient` — the modern object-oriented pattern replacing legacy module-level calls. Async support available via `pip install stripe[async]` (uses httpx internally). |

**Why not dj-stripe:**
dj-stripe mirrors Stripe's object graph into Django models (Subscription, Invoice, Customer, etc.)
and auto-syncs them via webhooks. This creates three concrete problems for this module:

1. **Adapter pattern conflict.** The requirement is a `PaymentAdapter` ABC with Stripe as one
   implementation. dj-stripe is itself an opinionated Stripe-specific layer — wrapping it behind
   a generic adapter produces an adapter around an adapter, with dj-stripe's model assumptions
   leaking through. Any second payment provider would need its own dj-stripe-equivalent, which
   defeats the abstraction.

2. **Removal coupling.** dj-stripe's migrations live in Django's migration graph. When the billing
   module is removed via the CLI scaffolder, dj-stripe's ~40 migration files and all their
   ForeignKey references to your User model must be surgically cleaned. dj-stripe 2.10.0 reset
   its entire migration history (requiring a two-step upgrade via 2.9.x) — a signal that the
   migration graph is not stable. Raw `stripe` + our own thin models means we control exactly
   which tables exist and can drop them cleanly.

3. **Version constraints.** dj-stripe 2.10+ requires Django >=5.0 exclusively. This imposes a
   hard Django version floor on every product using this template, even if the product has no
   payments feature.

**Why not django-payments (jazzband):**
django-payments provides a provider ABC but does not support Stripe's Meter API (usage-based
billing). Subscription lifecycle (upgrade/downgrade/cancel with proration) requires custom code
against the Stripe SDK regardless, so the abstraction buys little while adding a dependency.

### PDF Invoice Generation

| Technology          | Version      | Purpose                                            | Why                                                                                                                                                                                                                                                                                                  |
| ------------------- | ------------ | -------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `weasyprint`        | `>=68.1,<69` | Render HTML+CSS Django templates to PDF bytes      | Actively maintained (latest release February 2026, Production/Stable on PyPI). Supports Python 3.10-3.13. HTML+CSS input means invoice templates use standard Django templates — no proprietary layout DSL. Pure Python (no external browser process). WeasyPrint 68.x is the current stable series. |
| `django-weasyprint` | `>=2.4,<3`   | `WeasyTemplateResponseMixin` for class-based views | Thin wrapper (single mixin class). Wires Django's template renderer directly into WeasyPrint's HTML class. Returns `application/pdf` responses from CBVs. v2.4 is current. No additional abstraction beyond what we need.                                                                            |

**System dependencies (Docker image must include):**
WeasyPrint requires Cairo, Pango, and GDK-PixBuf native libraries. Add to `apps/api/Dockerfile`
before the Python install step:

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*
```

This is the primary operational complexity WeasyPrint adds — native libs in Docker. It is a
known, well-documented requirement and does not add a new service or external process.

**Why not ReportLab:**
ReportLab uses a Python-code layout API (Platypus/canvas), not HTML/CSS. Invoice templates would
be written in ReportLab's proprietary drawing primitives, creating a second templating system
alongside Django templates. WeasyPrint with HTML+CSS is faster to develop and universally
understood by anyone with web skills.

**Why not Stripe-hosted invoices:**
The requirement explicitly states vendor-agnostic, server-side PDF generation. Stripe-hosted
invoices are provider-locked and cannot be reused if the payment adapter switches to a different
provider.

**Why not wkhtmltopdf / PDFKit:**
wkhtmltopdf requires a headless browser binary in Docker (much heavier image). The project is
effectively unmaintained since 2023. WeasyPrint is pure Python and actively maintained.

### Webhook Infrastructure (no additional library)

No library beyond `stripe` is needed for webhook handling. The pattern for Django Ninja Extra:

```python
# apps/api/billing/api.py  (illustrative -- exact code written during implementation)
from django.http import HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from ninja_extra import api_controller, route
import stripe

@api_controller("/webhooks", tags=["billing"])
class BillingWebhookController:
    @route.post("/stripe", auth=None)  # auth=None bypasses Ninja JWT auth
    @csrf_exempt
    def stripe_webhook(self, request: HttpRequest):
        payload = request.body          # raw bytes -- do NOT parse before verification
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except stripe.error.SignatureVerificationError:
            return HttpResponse(status=400)
        # dispatch to signal/handler...
        return HttpResponse(status=200)
```

Critical constraint: `request.body` must be read before any JSON body parsing. If Django Ninja's
default body parsing is invoked on this endpoint (e.g., by declaring a Ninja schema parameter),
the raw bytes stream is consumed and `construct_event` will fail with a signature mismatch. Use
`HttpRequest` directly and return `HttpResponse` (not a Ninja schema response) for this endpoint.

---

## JavaScript / TypeScript — Web (apps/web/)

### Stripe Frontend Libraries

| Technology                | Version  | Purpose                                                                                    | Why                                                                                                                                                                                                              |
| ------------------------- | -------- | ------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `@stripe/stripe-js`       | `^8.9.0` | Load Stripe.js, create Elements instance                                                   | Required peer dep for react-stripe-js. v8.9.0 confirmed current (npm, published March 3, 2026). The `loadStripe` helper loads the hosted Stripe.js script — the npm package contributes TypeScript types only.   |
| `@stripe/react-stripe-js` | `^5.6.0` | React `<Elements>` provider, `<PaymentElement>` component, `useStripe`/`useElements` hooks | Official Stripe React bindings. v5.6.1 published March 4, 2026. `PaymentElement` is the current component (replaces deprecated `CardElement`) and supports 18+ global payment methods from a single integration. |

**Integration constraint — server vs. client components:**
`loadStripe` and all Elements components must run client-side. In Next.js 15 App Router, billing
pages must split into:

- **Server component** — fetch subscription data from `apps/api` (plan tier, status, invoice
  list). No Stripe imports.
- **Client component** (`"use client"`) — render `<Elements>` and `<PaymentElement>`. Import
  `@stripe/react-stripe-js` here only.

The `publishableKey` is passed as a prop from server to client (safe — it is a public key).

**What NOT to add on the web side:**

- Do NOT install the `stripe` npm package (Node.js server SDK) in `apps/web/`. All Stripe API
  calls requiring the secret key must route through `apps/api/`. Next.js Server Actions that call
  `stripe` directly risk secret key leakage into the client bundle and violate the single-backend
  architecture rule.
- Do NOT use the Stripe Customer Portal as the primary billing management UI. A custom Next.js
  page is required per the feature spec. The Stripe Customer Portal may be used as a fallback
  escape hatch for edge cases (e.g., updating payment methods during an active dispute) but must
  not be the primary surface.

---

## JavaScript / TypeScript — Mobile (apps/mobile/)

### Stripe React Native

| Technology                    | Version                    | Purpose                                                    | Why                                                                                                                                                                                                                                                                  |
| ----------------------------- | -------------------------- | ---------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `@stripe/stripe-react-native` | Expo-SDK-53-compatible pin | `<StripeProvider>`, `usePaymentSheet`, `useConfirmPayment` | Official Stripe React Native SDK. Expo SDK 53 requires a specific pinned version — check stripe-react-native CHANGELOG at install time for the Expo-SDK-53 mapping row. Uses Expo config plugin (add to `plugins` in `app.json`; no ejecting from managed workflow). |

**Scope boundary for mobile billing:**
The mobile app handles one-time purchases and displays current subscription status. Full
subscription lifecycle management (upgrade/downgrade/cancel) should direct users to the web app
or open a WebView pointing to the web billing page. Do not reimplement subscription management UI
natively — it duplicates logic and diverges from the web surface.

Native in-app-purchase (Apple IAP / Google Play Billing) is explicitly out of scope for this
module. Those require separate entitlements, App Store review processes, and revenue share rules
that are orthogonal to the Stripe integration.

**Expo Go limitation:**
Google Pay does not work in Expo Go. Use a development build (`eas build --profile development`)
when testing Google Pay or Apple Pay flows.

---

## Infrastructure / Environment

### Net-New Environment Variables

| Variable                 | Where                                     | Notes                                                  |
| ------------------------ | ----------------------------------------- | ------------------------------------------------------ |
| `STRIPE_SECRET_KEY`      | `apps/api/.env`                           | Never exposed to frontend. `sk_live_` or `sk_test_`.   |
| `STRIPE_PUBLISHABLE_KEY` | `apps/web/.env.local`, `apps/mobile/.env` | Public key, safe for client. `pk_live_` or `pk_test_`. |
| `STRIPE_WEBHOOK_SECRET`  | `apps/api/.env`                           | From Stripe Dashboard > Webhooks. `whsec_`.            |
| `STRIPE_PRICE_ID_<TIER>` | `apps/api/.env`                           | One var per plan tier (e.g., `STRIPE_PRICE_ID_PRO`).   |
| `BILLING_ENABLED`        | `apps/api/.env`                           | Feature flag controlling INSTALLED_APPS inclusion.     |

### Docker Compose

No new services. Billing runs within the existing `api` container. WeasyPrint native libs are
added to the `api` Dockerfile (see above). No separate queue worker is required for synchronous
webhook processing; if event handling becomes slow, route to the existing task queue (already
decided in the core stack).

### Stripe CLI (development tooling only)

```bash
brew install stripe/stripe-cli/stripe
stripe login
stripe listen --forward-to localhost:8000/api/webhooks/stripe
```

The Stripe CLI is a development convenience for local webhook forwarding. It is not a production
dependency and must not appear in `pyproject.toml` or `package.json`. Document its use in
`apps/api/README.md` only.

---

## Alternatives Considered

| Category             | Recommended                              | Alternative                   | Why Not                                                                                  |
| -------------------- | ---------------------------------------- | ----------------------------- | ---------------------------------------------------------------------------------------- |
| Django Stripe sync   | Raw `stripe` SDK                         | `dj-stripe`                   | Conflicts with PaymentAdapter ABC; migration coupling; hard CLI-removal; Django 5+ floor |
| PDF generation       | `weasyprint`                             | ReportLab                     | Proprietary layout DSL; no HTML/CSS templates                                            |
| PDF generation       | `weasyprint`                             | wkhtmltopdf / PDFKit          | Unmaintained; headless browser binary in Docker                                          |
| PDF generation       | `weasyprint`                             | Stripe-hosted invoices        | Provider-locked; violates vendor-agnostic requirement                                    |
| Frontend payment UI  | `@stripe/react-stripe-js` PaymentElement | Stripe Checkout (hosted page) | Requirement is custom Next.js UI                                                         |
| Mobile billing       | `@stripe/stripe-react-native`            | RevenueCat                    | RevenueCat wraps IAP -- not applicable to web subscriptions billed via Stripe            |
| Webhook verification | `stripe.Webhook.construct_event`         | dj-stripe webhook signals     | dj-stripe not used; raw verification is 10 lines with zero additional dependencies       |

---

## Adapter Pattern Notes (for requirements team)

The `PaymentAdapter` ABC lives in `apps/api/billing/adapters/base.py`. The Stripe implementation
lives in `apps/api/billing/adapters/stripe_adapter.py`. Minimum interface methods:

- `create_customer(user)` -> `str` (external ID)
- `create_subscription(customer_id, price_id)` -> subscription dict
- `cancel_subscription(subscription_id)` -> `None`
- `change_subscription_plan(subscription_id, new_price_id)` -> `None`
- `create_one_time_charge(customer_id, amount_cents, currency, description)` -> charge dict
- `record_usage(subscription_item_id, quantity, timestamp)` -> `None` (metered billing)
- `create_billing_portal_session(customer_id, return_url)` -> `str` (session URL, escape hatch)
- `construct_webhook_event(payload_bytes, sig_header, secret)` -> event dict

This interface is narrow enough that a second provider (Paddle, LemonSqueezy) could implement it
without importing any Stripe-specific types.

---

## Module Removability (CLI Scaffolder Contract)

For the billing module to be cleanly removable — same pattern as the AI module:

1. All billing models live in `apps/api/billing/` (single Django app).
2. App registered in `INSTALLED_APPS` conditionally via `BILLING_ENABLED` settings flag.
3. App URL routes included conditionally in `urls.py`.
4. `weasyprint` and `django-weasyprint` listed in a `[billing]` extras group in
   `pyproject.toml` (or a separate `requirements-billing.txt`).
5. Frontend: billing pages live in `apps/web/app/(billing)/`. Removing the module means deleting
   that route group and removing `@stripe/stripe-js` + `@stripe/react-stripe-js` from
   `apps/web/package.json`.
6. CLI scaffolder `--without billing` removes: Django app directory, env var stubs, Docker apt
   packages, frontend route group, mobile StripeProvider wrapper.

---

## Installation Commands

```bash
# Python -- inside apps/api/
uv add "stripe>=14.4,<15"
uv add "weasyprint>=68.1,<69"
uv add "django-weasyprint>=2.4,<3"
# Optional: async Stripe calls (only if using ASGI async views)
uv add "stripe[async]>=14.4,<15"

# Web -- from monorepo root
pnpm --filter web add @stripe/stripe-js@^8.9.0 @stripe/react-stripe-js@^5.6.0

# Mobile -- verify Expo SDK 53 compatible version in stripe-react-native CHANGELOG first
pnpm --filter mobile add @stripe/stripe-react-native
# Then add to apps/mobile/app.json plugins:
# ["@stripe/stripe-react-native", { "merchantIdentifier": "merchant.com.yourapp" }]
```

---

## Sources

- [stripe PyPI](https://pypi.org/project/stripe/) — v14.4.0, API version 2026-02-25.clover, release March 6, 2026 (MEDIUM — PyPI page metadata)
- [stripe-python GitHub releases](https://github.com/stripe/stripe-python/releases) — StripeClient in v8+, async in v13+, changelog (HIGH — official Stripe repo)
- [Stripe webhook docs Python](https://docs.stripe.com/webhooks?lang=python) — `Webhook.construct_event` pattern, raw body requirement (HIGH — official Stripe docs)
- [dj-stripe 2.10.0 release notes](https://dj-stripe.dev/docs/dev/changes/2_10_0) — migration reset, Django 5+ only, architecture shift (HIGH — official dj-stripe docs)
- [WeasyPrint PyPI](https://pypi.org/project/weasyprint/) — v68.1, Python 3.10-3.13, February 2026 release (HIGH — PyPI metadata)
- [WeasyPrint 68.1 docs](https://doc.courtbouillon.org/weasyprint/stable/) — system dependency list (HIGH — official docs)
- [django-weasyprint PyPI](https://pypi.org/project/django-weasyprint/) — v2.4.0, WeasyTemplateResponseMixin (MEDIUM — PyPI metadata)
- [@stripe/stripe-js npm](https://www.npmjs.com/package/@stripe/stripe-js) — v8.9.0, March 3, 2026 (HIGH — npm registry)
- [@stripe/react-stripe-js npm](https://www.npmjs.com/package/@stripe/react-stripe-js) — v5.6.1, March 4, 2026 (HIGH — npm registry)
- [React Stripe.js reference](https://docs.stripe.com/sdks/stripejs-react) — PaymentElement, Elements provider (HIGH — official Stripe docs)
- [Stripe React Native Expo docs](https://docs.expo.dev/versions/latest/sdk/stripe/) — Expo managed workflow config plugin (MEDIUM — Expo docs; SDK-53 pin requires verification at install time)
- [Stripe usage-based billing docs](https://docs.stripe.com/billing/subscriptions/usage-based/recording-usage-api) — Meter API, usage recording pattern (HIGH — official Stripe docs)
- [Stripe versioning policy](https://docs.stripe.com/sdks/versioning) — SDK major version cadence (HIGH — official Stripe docs)
