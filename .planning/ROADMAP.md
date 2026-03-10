# Roadmap: Foundation Template

## Milestones

- ✅ **v1.0 Foundation Template** — Phases 1–8 (shipped 2026-03-07)
- 🚧 **v1.1 Billing & Payments Module** — Phases 9–12 (in progress)

## Phases

<details>
<summary>✅ v1.0 Foundation Template (Phases 1–8) — SHIPPED 2026-03-07</summary>

- [x] Phase 1: Monorepo Foundation (4/4 plans) — Turborepo + pnpm workspaces, Docker Compose (Postgres 16 + PGVector + Redis), shared ESLint/TS config packages, hybrid `turbo dev` orchestration
- [x] Phase 2: API Core + Auth Backend (5/5 plans) — Django Ninja Extra API, dual auth strategy (session + JWT), Django Allauth headless, auto-generated OpenAPI 3.1 spec
- [x] Phase 3: Shared Packages + Type Generation (6/6 plans) — Auto-generated TypeScript types from OpenAPI, shared API client, Zod validation schemas, UI primitives (React Native Web)
- [x] Phase 4: Web Application (5/5 plans) — Next.js 15 App Router, complete auth flow (signup/login/logout/password reset), dashboard shell, user management
- [x] Phase 5: Mobile Application (4/4 plans) — React Native Expo managed workflow, auth screens, JWT token management, Expo Router navigation, shared package consumption
- [x] Phase 6: AI Module (5/5 plans) — Optional PGVector + LangGraph module, embedding pipeline, vector search API, tool agent scaffold
- [x] Phase 7: DevEx + CI/CD (4/4 plans) — GitHub Actions CI, pre-commit hooks (ruff + eslint), pytest/vitest/Detox test suites, production multi-stage Dockerfiles
- [x] Phase 8: CLI Scaffolder (3/3 plans) — Interactive `create-foundation-app` CLI, template generation engine, feature removal, post-generation validation, rollback

Full archive: `.planning/milestones/v1.0-ROADMAP.md`

</details>

### 🚧 v1.1 Billing & Payments Module (In Progress)

**Milestone Goal:** Add an optional, adapter-based billing and payments module — Stripe-backed by default, swappable by changing one Django setting, cleanly removable via the CLI scaffolder.

#### Phase Checklist

- [x] **Phase 9: Billing Scaffold** — Data models, PaymentAdapter interface, StripeAdapter, settings configuration, and module isolation markers (completed 2026-03-07)
- [x] **Phase 10: Webhook Infrastructure + Service Layer** — BillingService business logic, Stripe webhook receiver, Tier-1 event handlers, async dispatch, subscription lifecycle, metered billing (completed 2026-03-08)
- [x] **Phase 11: API Endpoints + Billing Frontend** — Ninja Extra billing controller, invoice list endpoint, Next.js /billing page with plan display, history, upgrade/downgrade/cancel flows (completed 2026-03-08)
- [x] **Phase 12: Invoice PDF + CLI Scaffolder Integration** — Async PDF generation via WeasyPrint + Celery, invoice download endpoint, CLI scaffolder opt-out, removal verification test (completed 2026-03-10)

## Phase Details

### Phase 9: Billing Scaffold

**Goal**: The billing module's foundational layer is locked — data models, adapter interface, Stripe implementation, and settings configuration are complete and stable before any service or HTTP code is written
**Depends on**: Phase 8 (existing CLI scaffolder, app module pattern)
**Requirements**: ADPTR-01, ADPTR-02, ADPTR-03, ADPTR-04, ADPTR-05, CUST-01, CUST-02, SUB-06, PAY-02
**Success Criteria** (what must be TRUE):

1. `PaymentAdapter` ABC exists with domain-centric method signatures — the word "stripe" does not appear in any abstract method signature or return type
2. `StripeAdapter` concretely implements the full protocol using `StripeClient` v14 and is wired as the default via `BILLING_ADAPTER` in Django settings
3. `Customer`, `Subscription`, `Payment` models exist with initial migration applied — `Subscription` uses `SubscriptionStatus` enum (not raw strings), has `cancel_at_period_end` and timestamp audit fields
4. A new `User` creation triggers auto-creation of a linked `Customer` record via `post_save` signal
5. `PlanProviderMapping` table exists and `BILLING_PLANS` dict in settings defines plan structure — no `stripe_price_id` field exists on any model
   Plans:

- [ ] 09-01: Wave 0 — Test infrastructure stubs (pytest package, conftest, test_adapters, test_models, test_signals)
- [ ] 09-02: Wave 1 — Billing module implementation (models, adapters, signals, apps, admin, migration 0001)
- [ ] 09-03: Wave 2 — Settings wiring (INSTALLED_APPS, BILLING_ADAPTER, BILLING_PLANS, urls.py markers, pyproject.toml, .env.example)

### Phase 10: Webhook Infrastructure + Service Layer

**Goal**: Billing business logic is fully testable via a stub adapter, the webhook receiver handles all Tier-1 Stripe events idempotently with async dispatch, and the complete subscription lifecycle is implemented in the service layer
**Depends on**: Phase 9
**Requirements**: HOOK-01, HOOK-02, HOOK-03, HOOK-04, SUB-01, SUB-02, SUB-03, SUB-04, SUB-05, PAY-01, USAGE-01, USAGE-02, CUST-03
**Plans**: 3 plans
**Success Criteria** (what must be TRUE):

1. A POST to the Stripe webhook endpoint with a valid HMAC signature returns HTTP 200 immediately — processing is dispatched to an async task queue, not executed in the request cycle
2. Sending the same Stripe event ID twice does not create duplicate subscription records — `ProcessedWebhookEvent` table with `unique_together(provider, event_id)` prevents double-processing
3. All 6 Tier-1 events (`checkout.session.completed`, `customer.subscription.created/updated/deleted`, `invoice.payment_succeeded/failed`) update `Subscription` and `Payment` model state correctly
4. `BillingService` can be unit-tested with a stubbed adapter — no HTTP calls to Stripe are required to verify subscription create/upgrade/downgrade/cancel/reactivate logic
5. API endpoints exist to record a metered usage event and retrieve current period usage, both delegating to the adapter

Plans:

- [ ] 10-01-PLAN.md — Webhook receiver (plain Django view), Celery dispatch task, Tier-1 event handlers, URL registration
- [ ] 10-02-PLAN.md — PaymentAdapter ABC extension (preview_proration, get_usage_summary), BillingService with full subscription lifecycle
- [ ] 10-03-PLAN.md — @require_active_subscription decorator, conftest fixtures expansion

### Phase 11: API Endpoints + Billing Frontend

**Goal**: Developers scaffolding a new project have a working billing UI out of the box — the /billing page displays current plan and payment history, and users can upgrade, downgrade, cancel, and manage payment methods without any custom backend code
**Depends on**: Phase 10
**Requirements**: INV-01, BILL-01, BILL-02, BILL-03, BILL-04, BILL-05, BILL-06, BILL-07
**Plans**: 5 plans
**Success Criteria** (what must be TRUE):

1. The `/billing` page shows the authenticated user's current plan name, billing period, and next renewal date pulled from the `Subscription` model
2. The `/billing` page shows a paginated payment history table with invoice status and a download link for each invoice
3. A user can initiate a plan upgrade or downgrade from the billing page — a proration preview modal appears before the change is confirmed
4. A user can cancel their subscription from the billing page — the subscription transitions to `cancel_at_period_end=True`, not immediate deletion
5. A `past_due` banner is visible in the dashboard when the authenticated user's subscription payment has failed

Plans:

- [ ] 11-01-PLAN.md — TDD scaffold: Ninja schemas, controller skeleton (RED), test_controllers.py with 8 failing tests
- [ ] 11-02-PLAN.md — Controller implementation: all 8 routes GREEN, BillingService.get_subscription_detail()
- [ ] 11-03-PLAN.md — Frontend data layer: billing.config.ts, getServerApi() billing methods, server actions, sidebar nav
- [ ] 11-04-PLAN.md — Billing UI: /billing page, billing-client.tsx, past-due banner, layout wiring, /billing/return
- [ ] 11-05-PLAN.md — Verification: automated test sweep + human smoke test checkpoint

### Phase 12: Invoice PDF + CLI Scaffolder Integration

**Goal**: Invoice PDFs are server-generated and downloadable on demand without blocking the request cycle, and the billing module can be excluded cleanly from any new project via a single scaffolder flag
**Depends on**: Phase 11
**Requirements**: INV-02, INV-03, SCAFF-01, SCAFF-02, SCAFF-03, SCAFF-04
**Plans**: 3 plans
**Success Criteria** (what must be TRUE):

1. A user can download any invoice as a PDF — the PDF is generated server-side by WeasyPrint using a Jinja2 template, not a Stripe-hosted link
2. PDF generation never blocks an HTTP request — it runs as an async Celery task; the API returns a task ID or polling URL immediately
3. Running `create-foundation-app --without billing` produces a project where `manage.py check` passes with no billing app errors and no billing files present
4. The billing module is included by default when no exclusion flag is provided — new projects are billing-ready without any manual steps

Plans:

- [ ] 12-01-PLAN.md — TDD: pdf.py (WeasyPrint + Jinja2), generate_invoice_pdf Celery task, PDF controller endpoints (INV-02, INV-03)
- [ ] 12-02-PLAN.md — CLI scaffolder: removeBillingModule(), billing prompt option, index.ts wiring (SCAFF-01–04)
- [ ] 12-03-PLAN.md — Verification: SCAFF-04 pytest test + human smoke test checkpoint

## Progress

| Phase                        | Milestone | Plans Complete | Status     | Completed  |
| ---------------------------- | --------- | -------------- | ---------- | ---------- |
| 1. Monorepo Foundation       | v1.0      | 4/4            | Complete   | 2026-02-17 |
| 2. API Core + Auth Backend   | v1.0      | 5/5            | Complete   | 2026-02-17 |
| 3. Shared Packages + Types   | v1.0      | 6/6            | Complete   | 2026-02-17 |
| 4. Web Application           | v1.0      | 5/5            | Complete   | 2026-02-17 |
| 5. Mobile Application        | v1.0      | 4/4            | Complete   | 2026-02-17 |
| 6. AI Module                 | v1.0      | 5/5            | Complete   | 2026-02-17 |
| 7. DevEx + CI/CD             | v1.0      | 4/4            | Complete   | 2026-02-17 |
| 8. CLI Scaffolder            | v1.0      | 3/3            | Complete   | 2026-02-17 |
| 9. Billing Scaffold          | v1.1      | 3/3            | Complete   | 2026-03-07 |
| 10. Webhook Infra + Service  | v1.1      | 3/3            | Complete   | 2026-03-08 |
| 11. API Endpoints + Frontend | v1.1      | 8/8            | Complete   | 2026-03-10 |
| 12. Invoice PDF + CLI        | 3/3       | Complete       | 2026-03-10 | -          |
