# Foundation Template

## What This Is

A reusable full-stack SaaS starter kit for a solo technical entrepreneur building multiple products. Clone the repo, run a CLI scaffolder to set project name and features, `docker compose up`, and you have a running web app + mobile app + API + database with authentication already working. Every new SaaS product starts from this template.

## Core Value

A new SaaS product goes from zero to running full-stack app (web + mobile + API + auth) in under 5 minutes with one command.

## Requirements

### Validated (v1.0)

- ✓ Turborepo monorepo with Django backend, Next.js frontend, Expo mobile app, and shared packages — v1.0
- ✓ Django Ninja Extra API with auto-generated OpenAPI 3.1 spec — v1.0
- ✓ Next.js 15 App Router frontend with Shadcn/ui and Tailwind CSS — v1.0
- ✓ React Native Expo (managed workflow) mobile app with navigation and auth screens — v1.0
- ✓ Django Allauth authentication with email/password, session management — v1.0
- ✓ Auth flow wired end-to-end: signup, login, logout, password reset across web and mobile — v1.0
- ✓ Postgres 16+ via Docker for local development — v1.0
- ✓ PGVector extension configured (optional AI module) — v1.0
- ✓ Auto-generated TypeScript types from Django Ninja OpenAPI spec — v1.0
- ✓ Shared monorepo packages: API client, Zod validation schemas, UI primitives (React Native Web), business logic/hooks/utils — v1.0
- ✓ One-command local setup: `docker compose up` runs everything — v1.0
- ✓ Hot reload for frontend (Next.js), backend (Django), and mobile (Expo) — v1.0
- ✓ CI/CD with GitHub Actions: lint, test, build on every push — v1.0
- ✓ Code quality gates: pre-commit hooks, ruff (Python), eslint + prettier (JS/TS), type checking — v1.0
- ✓ pytest test suite for backend, vitest for frontend, detox for mobile — v1.0
- ✓ Optional AI module: LangGraph agent scaffold, embedding pipeline, vector search API — removable if not needed — v1.0
- ✓ CLI scaffolder: run a command that asks project name and optional features, generates a new project from the template — v1.0
- ✓ Docker-first deployment: Docker Compose for local, Dockerfiles ready for any cloud provider — v1.0
- ✓ User management: basic user model, profile, account settings pages — v1.0

### Validated (v1.1)

- ✓ Billing & Payments optional module — adapter pattern, Stripe default, swappable per project — v1.1
- ✓ Subscription lifecycle: create via Stripe Checkout, upgrade/downgrade with proration preview, cancel at period end, reactivate — v1.1
- ✓ One-time charge support via Stripe Checkout in `payment` mode — v1.1
- ✓ Usage-based (metered) billing support via Stripe Meter Events v2 API — v1.1
- ✓ Webhook receiver + event processors: HMAC verification, async Celery dispatch, 6 Tier-1 Stripe events, idempotent processing — v1.1
- ✓ Server-side PDF invoice generation via WeasyPrint + Jinja2, async Celery task, never blocks HTTP — v1.1
- ✓ Billing frontend: `/billing` page with plan display, payment history, upgrade/downgrade modals, cancel flow, past-due banner — v1.1
- ✓ CLI scaffolder integration — billing included by default, `--without billing` removes module cleanly, `manage.py check` verified — v1.1

### Active (v1.2)

<!-- Observability & DevEx Hardening — runtime visibility + dev-time quality gates -->

- [ ] Structured JSON logging via `structlog` with `request_id`, `user_id`, `duration_ms` on every request
- [ ] Distributed tracing via OpenTelemetry auto-instrumentation (Django + Celery + DB), OTLP exporter, Jaeger in Docker Compose
- [ ] Error tracking + product analytics via `ObservabilityAdapter` ABC with `PostHogAdapter` default (Django + Celery + Next.js + Expo) — `--without observability` removes it
- [ ] Enhanced health probes: `/api/health/live`, `/api/health/ready`, `/api/health/startup`
- [ ] Rate limiting on auth endpoints via `django-ratelimit`, Redis-backed
- [ ] Security headers via `django-csp`, HSTS, X-Frame-Options (Django middleware + Next.js `headers()`)
- [ ] Redis cache backend via `django-redis` as default cache + session store
- [ ] Celery Beat scaffold with example recurring tasks in Docker Compose
- [ ] Flower dev-only monitoring in Docker Compose
- [ ] Secret scanning via `detect-secrets` in pre-commit + CI
- [ ] Python SAST via `bandit` in pre-commit + CI
- [ ] Dependency auditing via `pip-audit` + `pnpm audit` as CI gate
- [ ] N+1 detection via `nplusone` as pytest fixture
- [ ] API contract fuzzing via `schemathesis` as CI job
- [ ] `django-debug-toolbar` for local query analysis (dev only)
- [ ] `commitlint` pre-commit hook for conventional commit enforcement
- [ ] ruff McCabe complexity gate (max=10) in pre-commit

### Out of Scope

- Billing/payments as product-specific logic — the v1.1 module provides infrastructure and adapter pattern; each project configures plans, pricing, and provider credentials
- Multi-tenancy — each project decides its own tenancy model
- Product-specific business logic — template provides infrastructure, not features
- Specific cloud provider lock-in — Docker-first, deploy anywhere
- Admin dashboard — Django admin is sufficient for template
- Real-time features (WebSockets) — product-specific, add per-project
- Email service integration — template stubs email, each project configures provider

## Context

- Solo technical entrepreneur building multiple SaaS products
- Template is the highest-leverage investment — every hour here saves hours across every future project
- Stack decisions are permanent and non-negotiable (Django Ninja Extra, Next.js, Expo, etc.)
- Django Allauth chosen for auth: native Django, full control, no external auth dependency
- AI is optional because not every SaaS product needs it, but when needed it should be ready
- Shared packages across web and mobile reduce duplication: API client, validation, UI primitives, business logic
- Type safety across the stack via auto-generated TypeScript from Django Ninja OpenAPI
- Developer experience is critical — this template will be used repeatedly, friction compounds

## Constraints

- **Package managers**: pnpm for JS/TS, uv/pip for Python — no alternatives
- **Monorepo tool**: Turborepo for JS/TS workspaces
- **Database**: Postgres 16+ with PGVector extension
- **Python framework**: Django Ninja Extra (not DRF, not FastAPI)
- **Frontend framework**: Next.js 15+ with App Router (not Pages Router)
- **Mobile framework**: React Native with Expo managed workflow
- **UI library**: Shadcn/ui + Tailwind CSS (not Material UI, not Chakra)
- **AI orchestration**: LangGraph (not LangChain agents, not custom)
- **Testing**: pytest (backend), vitest (frontend), detox (mobile) — non-negotiable

## Key Decisions

| Decision                           | Rationale                                                                                                                                                                 | Outcome                                                                                    |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| Django Allauth for auth            | Native Django, full control, no external auth service dependency                                                                                                          | ✓ Good — headless mode + dual auth (session+JWT) works cleanly                             |
| AI as optional module              | Not every SaaS needs AI; pluggable avoids bloat                                                                                                                           | ✓ Good — CLI scaffolder removes AI module cleanly via feature flag                         |
| Billing module in template (v1.1)  | Products need billing fast; adapter pattern keeps it swappable, not coupled                                                                                               | ✓ Good — PaymentAdapter ABC + StripeAdapter; swappable with one Django setting             |
| No multi-tenancy in template       | Tenancy model depends on product; template shouldn't constrain                                                                                                            | ✓ Good — confirmed valid                                                                   |
| CLI scaffolder for new projects    | Better than GitHub template — can customize features, names, configs                                                                                                      | ✓ Good — `create-foundation-app` with validation + rollback shipped                        |
| Auto-generated TS from OpenAPI     | Single source of truth for API types; Django Ninja generates OpenAPI natively                                                                                             | ✓ Good — but Allauth headless endpoints missing from spec; manual fetch workaround applied |
| Docker-first deployment            | Maximum flexibility across cloud providers; no vendor lock-in                                                                                                             | ✓ Good — multi-stage Dockerfiles ship in Phase 7                                           |
| React Native Web for shared UI     | Share component primitives across web and mobile in monorepo                                                                                                              | ✓ Good — packages/ui ships shared primitives consumed by both apps                         |
| Tailwind CSS 3.4 (not 4)           | Tailwind 4 preview crashes Next.js PostCSS pipeline                                                                                                                       | ⚠️ Revisit — upgrade to Tailwind 4 when stable release ships                               |
| HS256 JWT (not RSA)                | Avoids RSA key provisioning complexity in template scaffolding                                                                                                            | ✓ Good — appropriate for template; each product can upgrade                                |
| PaymentAdapter ABC (not dj-stripe) | dj-stripe adds ~40 migrations coupling to User model, forces provider lock-in                                                                                             | ✓ Good — domain-centric adapter with StripeAdapter as default; swappable in one setting    |
| Plain Django view for webhook      | Raw body bytes required for Stripe HMAC; Ninja may buffer/parse body                                                                                                      | ✓ Good — reliable HMAC verification, HTTP 200 + Celery dispatch pattern works cleanly      |
| PlanProviderMapping table          | No `stripe_price_id` on models; internal plan IDs stay provider-agnostic                                                                                                  | ✓ Good — price IDs seeded via migration 0002 for dev/test; no hardcoding in service code   |
| Async PDF via Celery + WeasyPrint  | Never block HTTP request cycle; WeasyPrint has fontconfig deadlock on fork                                                                                                | ✓ Good — lazy import inside task body prevents deadlock; 512KB MAX_PDF_BYTES guard added   |
| Billing in template (v1.1)         | High-leverage addition; every SaaS product needs billing infrastructure                                                                                                   | ✓ Good — 36 requirements delivered, 40/40 verification truths passed, human-verified       |
| PostHog over Sentry (v1.2)         | Single SDK covers errors + analytics + feature flags + session replay; generous free tier; self-hostable; adapter pattern lets projects swap to Sentry if they outgrow it | — Pending                                                                                  |
| ObservabilityAdapter ABC (v1.2)    | Same pattern as PaymentAdapter — PostHogAdapter default, NoOpAdapter for tests; swappable via one Django setting; avoids SDK lock-in across web/mobile/backend            | — Pending                                                                                  |

## Current Milestone: v1.2 — Observability & DevEx Hardening

**Goal:** Every scaffolded product ships with full runtime visibility and dev-time security gates from day one, with zero extra configuration.

**Target features:**

- Structured logging (structlog), distributed tracing (OpenTelemetry + Jaeger), error tracking + analytics (PostHog via ObservabilityAdapter, optional)
- Security hardening: rate limiting, security headers, Redis cache/session
- Celery Beat scaffold + Flower dev monitoring
- Dev-time gates: detect-secrets, bandit, pip-audit, nplusone, schemathesis, commitlint, complexity linting

## Current State (v1.1)

- **Version shipped:** v1.1 (2026-03-11)
- **Codebase:** ~552k LOC total (Python + TypeScript) across the monorepo
- **Stack:** Django Ninja Extra + Next.js 15 + Expo SDK 53 + Turborepo + pnpm + Stripe SDK v14 + Celery + WeasyPrint
- **CLI:** `create-foundation-app` — interactive scaffolder with feature removal (billing, AI, mobile), validation, rollback
- **Billing module:** `apps/api/apps/billing/` — adapter-based, Stripe default, removable via `--without billing`
- **Next milestone:** v1.2 — Observability & DevEx Hardening (requirements defined 2026-03-11)

---

_Last updated: 2026-03-11 after v1.2 milestone start_
