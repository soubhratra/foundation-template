# Milestones

## v1.2 Observability & DevEx Hardening (Shipped: 2026-03-12)

**Phases completed:** 6 phases, 19 plans | **Phases:** 13–18
**Files:** ~55 files modified/created | **Timeline:** 2026-03-11 (1 day) | **Commits:** ~30
**Verifications:** Phase 13 (12/12) + Phase 14 (13/13) + Phase 15 (12/12) + Phase 16 (9/9) + Phase 17 (11/11) + Phase 18 (9/9) = 66/66 truths

**Key accomplishments:**

1. structlog JSON logging pipeline — `request_id`, `user_id`, `duration_ms` auto-injected on every Django request; OpenTelemetry auto-instrumentation (Django + Celery + PostgreSQL + Redis); Jaeger in Docker Compose for distributed trace visualization
2. `ObservabilityAdapter` ABC with `PostHogAdapter` default — exceptions, analytics, and feature flags across Django (middleware), Celery (task_failure signal), Next.js, and Expo; `NoOpAdapter` for zero-overhead CI/test; swappable via one `OBSERVABILITY_ADAPTER` Django setting; `--without observability` removes all 7 touch points cleanly
3. `/api/health/live|ready|startup` plain Django health probes (no Ninja, no auth); Celery Beat with `DatabaseScheduler` scaffold + example periodic task; Flower dev-only monitoring in Docker Compose; celery-worker added to dev compose so beat-dispatched tasks have a consumer
4. Redis-backed rate limiting via `django-ratelimit` on all auth endpoints (HTTP 429 + `Retry-After`); Redis cache + session backend via `django-redis`; CSP (`django-csp` 4.0 nonce API) + HSTS (production only) + `X-Frame-Options` on both Django and Next.js
5. `detect-secrets` + `bandit` in pre-commit + CI; `pip-audit` + `pnpm audit` as CI merge gates; `django-debug-toolbar` for local query analysis (absent in test/prod); 2 HIGH-priority integration breaks fixed post-audit (stale test URL + Docker Compose Redis env vars)
6. `nplusone` N+1 detection as autouse pytest fixture (blinker signal with explicit teardown); `schemathesis` API contract fuzzing CI job (30 examples, 5s timeout, billing/auth excluded); `commitlint` conventional commits pre-commit hook; ruff McCabe complexity gate max=10

**Archive:** `.planning/milestones/v1.2-ROADMAP.md` | `.planning/milestones/v1.2-REQUIREMENTS.md`

---

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
