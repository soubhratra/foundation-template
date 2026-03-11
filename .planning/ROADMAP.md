# Roadmap: Foundation Template

## Milestones

- ✅ **v1.0 Foundation Template** — Phases 1–8 (shipped 2026-03-07)
- ✅ **v1.1 Billing & Payments Module** — Phases 9–12 (shipped 2026-03-11)
- 🚧 **v1.2 Observability & DevEx Hardening** — Phases 13–18 (in progress)

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

<details>
<summary>✅ v1.1 Billing & Payments Module (Phases 9–12) — SHIPPED 2026-03-11</summary>

- [x] Phase 9: Billing Scaffold (3/3 plans) — `PaymentAdapter` ABC, `StripeAdapter` v14, Customer/Subscription/Payment models, post_save signal, `BILLING_PLANS` settings, migration 0001 (completed 2026-03-07)
- [x] Phase 10: Webhook Infrastructure + Service Layer (3/3 plans) — Plain Django webhook view, Celery async dispatch, idempotent `ProcessedWebhookEvent`, 6 Tier-1 event handlers, `BillingService` full lifecycle, `@require_active_subscription` decorator (completed 2026-03-08)
- [x] Phase 11: API Endpoints + Billing Frontend (8/8 plans) — Ninja Extra billing controller, 8 REST endpoints, Next.js `/billing` page, plan cards, payment history, upgrade/downgrade modals, cancel flow, past-due banner (completed 2026-03-10)
- [x] Phase 12: Invoice PDF + CLI Scaffolder Integration (3/3 plans) — WeasyPrint + Jinja2 A4 PDF template, `generate_invoice_pdf` Celery task, PDF polling endpoint, `removeBillingModule()` CLI, `--without billing` flag, SCAFF-04 pytest test (completed 2026-03-11)

Full archive: `.planning/milestones/v1.1-ROADMAP.md`

</details>

### 🚧 v1.2 Observability & DevEx Hardening (In Progress)

**Milestone Goal:** Every scaffolded product ships with full runtime visibility and dev-time security gates from day one, with zero extra configuration.

- [x] **Phase 13: Structured Logging + Distributed Tracing** — structlog JSON logs with request context auto-injected; OpenTelemetry auto-instrumentation across Django + Celery + PostgreSQL; Jaeger in Docker Compose (completed 2026-03-11)
- [x] **Phase 14: ObservabilityAdapter** — `ObservabilityAdapter` ABC with `PostHogAdapter` default covering Django + Celery + Next.js + Expo; `--without observability` removes it cleanly (completed 2026-03-11)
- [x] **Phase 15: Health Probes + Celery Infrastructure** — `/api/health/live|ready|startup` probes; Celery Beat scaffold with example periodic task; Flower dev monitoring in Docker Compose (completed 2026-03-11)
- [x] **Phase 16: Security Hardening** — Redis cache + session backend via `django-redis`; auth endpoint rate limiting via `django-ratelimit`; security headers via `django-csp` + HSTS + Next.js `headers()` (completed 2026-03-11)
- [x] **Phase 17: Dev-Time Security Gates** — `detect-secrets` + `bandit` in pre-commit + CI; `pip-audit` + `pnpm audit` as CI merge gate; `django-debug-toolbar` for local query analysis (completed 2026-03-11)
- [ ] **Phase 18: Dev-Time Quality Gates** — `nplusone` N+1 detection as pytest fixture; `schemathesis` API contract fuzzing as CI job; `commitlint` conventional commits hook; ruff McCabe complexity gate (max=10)

## Phase Details

### Phase 13: Structured Logging + Distributed Tracing

**Goal**: Developers can see structured, correlated logs and trace requests end-to-end across every service boundary
**Depends on**: Phase 12 (v1.1 complete)
**Requirements**: OBS-01, OBS-02
**Success Criteria** (what must be TRUE):

1. Every Django request log line is valid JSON and contains `request_id`, `user_id`, and `duration_ms` fields without any developer configuration
2. A developer can open Jaeger at `http://localhost:16686` and see a distributed trace that spans a Django view, a Celery task it dispatched, and the SQL queries each made
3. `docker compose up` starts Jaeger alongside Postgres and Redis — no extra steps required
4. Trace context propagates automatically: a trace started in a Django view is continued by the Celery worker that handles its async task

**Plans:** 3/3 plans complete

Plans:

- [ ] 13-01-PLAN.md — Wave 0 test stubs (test_logging, test_middleware, test_tracing)
- [ ] 13-02-PLAN.md — structlog pipeline: logging.py + middleware.py + Django settings wiring
- [ ] 13-03-PLAN.md — OTel tracing: tracing.py + Celery worker init + Jaeger in docker-compose

### Phase 14: ObservabilityAdapter

**Goal**: Every scaffolded project captures exceptions, product analytics, and session replay via a swappable adapter with PostHog as the default
**Depends on**: Phase 13
**Requirements**: OBS-03
**Success Criteria** (what must be TRUE):

1. An unhandled Django exception is automatically captured by PostHog with full context (user, request, environment) — no explicit `capture_exception` call needed in application code
2. An unhandled Celery task exception is automatically captured by PostHog with task name and arguments as context
3. The Next.js app sends PostHog page views and errors on the client side without any per-page instrumentation
4. The Expo mobile app sends PostHog events on the client side without any per-screen instrumentation
5. Running `create-foundation-app --without observability` produces a project with zero PostHog imports and `manage.py check` passes clean

**Plans:** 4/4 plans complete

Plans:

- [ ] 14-01-PLAN.md — Wave 1: RED test stubs (test_observability.py + scaffolder removal test)
- [ ] 14-02-PLAN.md — Wave 2: Django backend (observability.py + middleware + Celery signal + settings)
- [ ] 14-03-PLAN.md — Wave 1: Frontend providers (Next.js PostHogProvider + Expo PostHogProvider)
- [ ] 14-04-PLAN.md — Wave 1: CLI removal (removeObservability() + SelectedFeatures + index wiring)

### Phase 15: Health Probes + Celery Infrastructure

**Goal**: Deployments can validate app readiness via structured health endpoints, and scheduled tasks are scaffolded and visible from day one
**Depends on**: Phase 13
**Requirements**: OBS-04, OBS-05, OBS-06
**Success Criteria** (what must be TRUE):

1. `GET /api/health/live` returns HTTP 200 when the process is running and HTTP 503 if the process is wedged
2. `GET /api/health/ready` returns HTTP 200 only when Postgres, Redis, and Celery workers are all reachable; returns HTTP 503 with a JSON body identifying which dependency is failing
3. `GET /api/health/startup` returns HTTP 200 only when all Django migrations have been applied; returns HTTP 503 with the count of unapplied migrations
4. `docker compose up` starts a `celery-beat` service and the logs show it successfully scheduling the example periodic task on its configured interval
5. A developer can open Flower at `http://localhost:5555` and see Celery worker status and task history — Flower does not appear in the production Docker Compose file

**Plans:** 3/3 plans complete

Plans:

- [ ] 15-01-PLAN.md — Wave 1: Install deps + RED test stubs (test_health_probes.py + test_periodic_tasks.py)
- [ ] 15-02-PLAN.md — Wave 2: Health probe implementation (health.py + health_urls.py + URL wiring)
- [ ] 15-03-PLAN.md — Wave 2: Celery Beat + Flower Docker Compose (tasks.py + settings + docker-compose)

### Phase 16: Security Hardening

**Goal**: Every request is protected by Redis-backed rate limiting and security headers, and cache/session use Redis as the default backend
**Depends on**: Phase 13
**Requirements**: SEC-01, SEC-02, SEC-03
**Success Criteria** (what must be TRUE):

1. Sending more than the configured request limit to any auth endpoint (login, signup, password reset) within the rate window returns HTTP 429 with a `Retry-After` header
2. Rate limit counters survive a Django process restart — they are stored in Redis, not in-process memory
3. Every HTTP response from Django includes `Content-Security-Policy`, `Strict-Transport-Security`, `X-Frame-Options`, and `Referrer-Policy` headers with secure values
4. Every HTTP response from Next.js includes matching `Content-Security-Policy` and `X-Frame-Options` headers via the `headers()` config
5. Django cache operations (`cache.get`, `cache.set`) and session reads/writes hit Redis — `LocMemCache` is not used in development or production environments

**Plans:** 3/3 plans complete

Plans:

- [ ] 16-01-PLAN.md — Wave 1: RED test stubs (test_security.py covering SEC-01, SEC-02, SEC-03)
- [ ] 16-02-PLAN.md — Wave 2: Redis CACHES + session backend + AuthRateLimitMiddleware + ratelimited_error handler
- [ ] 16-03-PLAN.md — Wave 2: django-csp middleware + HSTS in production + Next.js headers() config

### Phase 17: Dev-Time Security Gates

**Goal**: Secrets, Python security issues, and known-vulnerable dependencies are blocked before they can reach the main branch
**Depends on**: Phase 12 (can run in parallel with phases 13–16)
**Requirements**: DEV-01, DEV-02, DEV-03, DEV-06
**Success Criteria** (what must be TRUE):

1. Attempting to commit a file containing a detectable secret (e.g., a hardcoded AWS key pattern) is blocked by the pre-commit hook with a clear error identifying the finding
2. The CI pipeline fails on a PR that introduces a `bandit` high-severity finding, with the finding shown in CI output
3. A PR that introduces a dependency with a known CVE fails the CI `pip-audit` or `pnpm audit` gate before merge
4. Opening the app in a browser in development mode renders the `django-debug-toolbar` panel — it is absent in test and production environments

**Plans:** 3/3 plans complete

Plans:

- [ ] 17-01-PLAN.md — Wave 1: RED test stubs (test_dev_gates.py — DEV-01, DEV-02, DEV-03, DEV-06)
- [ ] 17-02-PLAN.md — Wave 1: Pre-commit hooks (detect-secrets + bandit) + CI gates (bandit, pip-audit, pnpm audit)
- [ ] 17-03-PLAN.md — Wave 2: Install deps + generate .secrets.baseline + configure DDT + turn tests GREEN

### Phase 18: Dev-Time Quality Gates

**Goal**: N+1 query regressions, API contract violations, non-conventional commits, and excessive complexity are blocked automatically
**Depends on**: Phase 17
**Requirements**: DEV-04, DEV-05, DEV-07, DEV-08
**Success Criteria** (what must be TRUE):

1. A pytest test that introduces an N+1 query fails automatically — the developer sees which test triggered the N+1 and can add an explicit `nplusone_allow` annotation to document intentional exceptions
2. A CI job runs `schemathesis` against the live Django test server and the job fails if any property-based request causes a 5xx response or a response that violates the OpenAPI schema
3. Attempting to commit with a message that does not follow the Conventional Commits spec (e.g., `"fixed bug"`) is blocked by the pre-commit hook with the spec violation shown
4. A Python function exceeding McCabe complexity 10 is blocked by ruff in pre-commit and fails CI — the developer sees which function triggered the gate

**Plans:** 3 plans

Plans:

- [ ] 18-01-PLAN.md — Wave 1: RED test stubs (test_quality_gates.py — DEV-04, DEV-07, DEV-08)
- [ ] 18-02-PLAN.md — Wave 2: Install nplusone + conftest fixture + commitlint hook + ruff McCabe config, turn tests GREEN
- [ ] 18-03-PLAN.md — Wave 1: schemathesis dev dep + CI contract fuzzing job

## Progress

| Phase                            | Milestone | Plans Complete | Status      | Completed  |
| -------------------------------- | --------- | -------------- | ----------- | ---------- |
| 1. Monorepo Foundation           | v1.0      | 4/4            | Complete    | 2026-02-17 |
| 2. API Core + Auth Backend       | v1.0      | 5/5            | Complete    | 2026-02-17 |
| 3. Shared Packages + Types       | v1.0      | 6/6            | Complete    | 2026-02-17 |
| 4. Web Application               | v1.0      | 5/5            | Complete    | 2026-02-17 |
| 5. Mobile Application            | v1.0      | 4/4            | Complete    | 2026-02-17 |
| 6. AI Module                     | v1.0      | 5/5            | Complete    | 2026-02-17 |
| 7. DevEx + CI/CD                 | v1.0      | 4/4            | Complete    | 2026-02-17 |
| 8. CLI Scaffolder                | v1.0      | 3/3            | Complete    | 2026-02-17 |
| 9. Billing Scaffold              | v1.1      | 3/3            | Complete    | 2026-03-07 |
| 10. Webhook Infra + Service      | v1.1      | 3/3            | Complete    | 2026-03-08 |
| 11. API Endpoints + Frontend     | v1.1      | 8/8            | Complete    | 2026-03-10 |
| 12. Invoice PDF + CLI            | v1.1      | 3/3            | Complete    | 2026-03-11 |
| 13. Structured Logging + Tracing | v1.2      | 3/3            | Complete    | 2026-03-11 |
| 14. ObservabilityAdapter         | v1.2      | 4/4            | Complete    | 2026-03-11 |
| 15. Health Probes + Celery Infra | v1.2      | 3/3            | Complete    | 2026-03-11 |
| 16. Security Hardening           | 3/3       | Complete       | 2026-03-11  | -          |
| 17. Dev-Time Security Gates      | 3/3       | Complete       | 2026-03-11  | -          |
| 18. Dev-Time Quality Gates       | v1.2      | 0/3            | Not started | -          |
