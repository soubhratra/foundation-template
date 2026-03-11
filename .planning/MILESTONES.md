# Milestones

## v1.1 Billing & Payments Module (Shipped: 2026-03-11)

**Phases completed:** 4 phases, 17 plans | **Phases:** 9–12
**Files:** ~60 files modified/created | **Timeline:** 2026-03-07 → 2026-03-11 (4 days) | **Commits:** ~87
**Verifications:** Phase 9 (9/9) + Phase 10 (13/13) + Phase 11 (8/8) + Phase 12 (10/10) = 40/40 truths

**Key accomplishments:**

1. Provider-agnostic `PaymentAdapter` ABC with `StripeClient` v14 `StripeAdapter` — billing backend swappable with one `BILLING_ADAPTER` Django setting change
2. Full subscription lifecycle: Stripe Checkout for new subscriptions, upgrade/downgrade with proration preview, cancel at period end, reactivate — all via `BillingService` testable with `StubAdapter`
3. Async webhook infrastructure: plain Django view with HMAC verification returns HTTP 200 immediately, Celery dispatch, idempotent `ProcessedWebhookEvent` guard, 6 Tier-1 Stripe event handlers
4. Complete billing frontend: Next.js `/billing` page with current plan, payment history, upgrade/downgrade modals, cancel flow, past-due banner in dashboard
5. Async invoice PDF generation: WeasyPrint + Jinja2 A4 template, `generate_invoice_pdf` Celery task, polling endpoint — PDF generation never blocks HTTP request cycle
6. CLI scaffolder integration: billing included by default in `create-foundation-app`, `--without billing` flag removes all billing files cleanly; SCAFF-04 pytest verifies `manage.py check` passes post-removal

**Archive:** `.planning/milestones/v1.1-ROADMAP.md` | `.planning/milestones/v1.1-REQUIREMENTS.md`

---

## v1.0 Foundation Template (Shipped: 2026-03-07)

**Phases completed:** 8 phases, 36 plans
**Files:** 504 files, 88,908 insertions | **LOC:** ~162k Python, ~27k TypeScript
**Timeline:** 2026-02-08 → 2026-02-21 (13 days) | **Commits:** 185

**Key accomplishments:**

1. Turborepo monorepo with pnpm workspaces, shared ESLint/TypeScript config packages, hybrid `turbo dev` orchestration with Docker Compose (Postgres 16 + PGVector + Redis)
2. Django Ninja Extra REST API with dual auth strategy (session cookies + JWT) via Django Allauth headless, auto-generated OpenAPI 3.1 spec
3. Type-safe integration layer — auto-generated TypeScript types from OpenAPI, shared API client, Zod validation schemas, UI primitives (React Native Web)
4. Next.js 15 App Router web app with complete auth flow (signup/login/logout/password reset), dashboard shell, user management
5. React Native Expo mobile app with auth screens, JWT token management, Expo Router navigation, shared package consumption
6. Optional AI module (PGVector + LangGraph), full test suites (pytest/vitest/Detox), GitHub Actions CI/CD, pre-commit hooks, and interactive `create-foundation-app` CLI scaffolder

**Known Gaps:**

- 71 REQUIREMENTS.md items were built but not individually checked off during execution (all phases complete on disk)
- Billing/payments explicitly out of scope — each product adds its own

**Archive:** `.planning/milestones/v1.0-ROADMAP.md` | `.planning/milestones/v1.0-REQUIREMENTS.md`

---
