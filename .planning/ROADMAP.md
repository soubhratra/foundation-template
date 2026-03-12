# Roadmap: Foundation Template

## Milestones

- ✅ **v1.0 Foundation Template** — Phases 1–8 (shipped 2026-03-07)
- ✅ **v1.1 Billing & Payments Module** — Phases 9–12 (shipped 2026-03-11)
- ✅ **v1.2 Observability & DevEx Hardening** — Phases 13–18 (shipped 2026-03-12)
- 🚧 **v1.3 SaaS Functional Baseline** — Phases 19–23 (in progress)

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

<details>
<summary>✅ v1.2 Observability & DevEx Hardening (Phases 13–18) — SHIPPED 2026-03-12</summary>

- [x] Phase 13: Structured Logging + Distributed Tracing (3/3 plans) — completed 2026-03-11
- [x] Phase 14: ObservabilityAdapter (4/4 plans) — completed 2026-03-11
- [x] Phase 15: Health Probes + Celery Infrastructure (3/3 plans) — completed 2026-03-11
- [x] Phase 16: Security Hardening (3/3 plans) — completed 2026-03-11
- [x] Phase 17: Dev-Time Security Gates (3/3 plans) — completed 2026-03-11
- [x] Phase 18: Dev-Time Quality Gates (3/3 plans) — completed 2026-03-11

Full archive: `.planning/milestones/v1.2-ROADMAP.md`

</details>

### 🚧 v1.3 SaaS Functional Baseline (In Progress)

**Milestone Goal:** Every scaffolded product starts with transactional email, social login, GDPR compliance, role-based access control, and plan-gated feature entitlements already wired in.

- [ ] **Phase 19: Transactional Email** — `EmailAdapter` ABC with `ResendAdapter` default; Celery-queued async dispatch; HTML templates with inline CSS; `ConsoleAdapter` for dev; `--without email` scaffolder flag
- [ ] **Phase 20: Social Auth** — Google + GitHub OAuth on web; Apple Sign In on iOS mobile; email-collision account merge; `--without social-auth` scaffolder flag
- [ ] **Phase 21: GDPR Baseline** — Async account hard delete cascading all third-party data; JSON personal data export; cookie consent banner gating PostHog
- [ ] **Phase 22: RBAC** — `@require_role("admin")` decorator; role assignment API; seeded `admin`/`member` groups via data migration
- [ ] **Phase 23: Feature Entitlements** — `has_feature(user, key)` utility; Redis-cached results; billing-off fallback returns `True`

## Phase Details

> Phase details for v1.2 (Phases 13–18) archived to `.planning/milestones/v1.2-ROADMAP.md`

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

- [x] 13-01-PLAN.md — Wave 0 test stubs (test_logging, test_middleware, test_tracing)
- [x] 13-02-PLAN.md — structlog pipeline: logging.py + middleware.py + Django settings wiring
- [x] 13-03-PLAN.md — OTel tracing: tracing.py + Celery worker init + Jaeger in docker-compose

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

- [x] 14-01-PLAN.md — Wave 1: RED test stubs (test_observability.py + scaffolder removal test)
- [x] 14-02-PLAN.md — Wave 2: Django backend (observability.py + middleware + Celery signal + settings)
- [x] 14-03-PLAN.md — Wave 1: Frontend providers (Next.js PostHogProvider + Expo PostHogProvider)
- [x] 14-04-PLAN.md — Wave 1: CLI removal (removeObservability() + SelectedFeatures + index wiring)

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

- [x] 15-01-PLAN.md — Wave 1: Install deps + RED test stubs (test_health_probes.py + test_periodic_tasks.py)
- [x] 15-02-PLAN.md — Wave 2: Health probe implementation (health.py + health_urls.py + URL wiring)
- [x] 15-03-PLAN.md — Wave 2: Celery Beat + Flower Docker Compose (tasks.py + settings + docker-compose)

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

- [x] 16-01-PLAN.md — Wave 1: RED test stubs (test_security.py covering SEC-01, SEC-02, SEC-03)
- [x] 16-02-PLAN.md — Wave 2: Redis CACHES + session backend + AuthRateLimitMiddleware + ratelimited_error handler
- [x] 16-03-PLAN.md — Wave 2: django-csp middleware + HSTS in production + Next.js headers() config

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

- [x] 17-01-PLAN.md — Wave 1: RED test stubs (test_dev_gates.py — DEV-01, DEV-02, DEV-03, DEV-06)
- [x] 17-02-PLAN.md — Wave 1: Pre-commit hooks (detect-secrets + bandit) + CI gates (bandit, pip-audit, pnpm audit)
- [x] 17-03-PLAN.md — Wave 2: Install deps + generate .secrets.baseline + configure DDT + turn tests GREEN

### Phase 18: Dev-Time Quality Gates

**Goal**: N+1 query regressions, API contract violations, non-conventional commits, and excessive complexity are blocked automatically
**Depends on**: Phase 17
**Requirements**: DEV-04, DEV-05, DEV-07, DEV-08
**Success Criteria** (what must be TRUE):

1. A pytest test that introduces an N+1 query fails automatically — the developer sees which test triggered the N+1 and can add an explicit `nplusone_allow` annotation to document intentional exceptions
2. A CI job runs `schemathesis` against the live Django test server and the job fails if any property-based request causes a 5xx response or a response that violates the OpenAPI schema
3. Attempting to commit with a message that does not follow the Conventional Commits spec (e.g., `"fixed bug"`) is blocked by the pre-commit hook with the spec violation shown
4. A Python function exceeding McCabe complexity 10 is blocked by ruff in pre-commit and fails CI — the developer sees which function triggered the gate

**Plans:** 3/3 plans complete

Plans:

- [x] 18-01-PLAN.md — Wave 1: RED test stubs (test_quality_gates.py — DEV-04, DEV-07, DEV-08)
- [x] 18-02-PLAN.md — Wave 2: Install nplusone + conftest fixture + commitlint hook + ruff McCabe config, turn tests GREEN
- [x] 18-03-PLAN.md — Wave 1: schemathesis dev dep + CI contract fuzzing job

### Phase 19: Transactional Email

**Goal**: Every scaffolded product can send transactional emails asynchronously via a swappable adapter, with no credentials required in development
**Depends on**: Phase 18 (v1.2 complete)
**Requirements**: EMAIL-01, EMAIL-02, EMAIL-03, EMAIL-04, EMAIL-05
**Success Criteria** (what must be TRUE):

1. Application code calls `send_email(to, template, context)` without knowing which ESP is active — swapping from `ResendAdapter` to a future `MailgunAdapter` requires changing one Django setting
2. An email triggered during an HTTP request is dispatched via Celery after the database transaction commits — no email is ever sent if the triggering transaction rolls back
3. An HTML email received in an email client renders correctly without visible broken styles — CSS is inlined before dispatch, not left in `<style>` blocks
4. Running the app locally with no `RESEND_API_KEY` set causes all outgoing emails to appear in the Django console log — no credentials, no error, no silent drop
5. Running `create-foundation-app --without email` produces a project with no `notifications` app, no anymail in `INSTALLED_APPS`, and `manage.py check` passes clean

**Plans**: 4 plans

Plans:

- [ ] 19-01-PLAN.md — Wave 1: RED test stubs for EMAIL-01 through EMAIL-05
- [ ] 19-02-PLAN.md — Wave 1: notifications app scaffold, settings auto-switch, dependencies
- [ ] 19-03-PLAN.md — Wave 2: send_email() utility, send_email_task Celery task, HTML templates
- [ ] 19-04-PLAN.md — Wave 3: removeEmailModule() scaffolder flag, prompts.ts, index.ts wiring

### Phase 20: Social Auth

**Goal**: Users can sign up and log in via Google, GitHub, or Apple without creating a password, and existing password-account users are auto-merged on email match
**Depends on**: Phase 19
**Requirements**: SOCIAL-01, SOCIAL-02, SOCIAL-03, SOCIAL-04, SOCIAL-05
**Success Criteria** (what must be TRUE):

1. A user can click "Continue with Google" on the web app sign-in page, complete the OAuth flow, and land on the dashboard as a logged-in user — no manual account creation step
2. A user can click "Continue with GitHub" on the web app sign-in page and complete sign-in — GitHub email is used as the account identifier
3. A user on iOS can tap "Sign in with Apple" in the mobile app, authorize, and be logged into the app — the Apple-issued relay email is stored without triggering account merge with an existing Google/GitHub account
4. A user who previously signed up with email/password can use "Continue with Google" with the same email and lands on their existing account — no duplicate account is created, no error shown
5. Running `create-foundation-app --without social-auth` produces a project with no `SOCIALACCOUNT_PROVIDERS` config, no social provider apps in `INSTALLED_APPS`, and `manage.py check` passes clean

**Plans**: TBD

### Phase 21: GDPR Baseline

**Goal**: Users have full control over their personal data — they can permanently erase their account or export everything they've given the app
**Depends on**: Phase 20
**Requirements**: GDPR-01, GDPR-02, GDPR-03
**Success Criteria** (what must be TRUE):

1. A user who calls `DELETE /api/v1/account/` receives HTTP 202 immediately — their Stripe customer record, PostHog person record, social accounts, and Django user row are all deleted asynchronously with no orphaned data in any system
2. A user who calls `GET /api/v1/account/export` receives a JSON document containing all personal data the app holds: profile fields, email addresses, social accounts, billing history, and subscription status
3. A first-time visitor to the web app sees a cookie consent banner — PostHog does not initialise or set any tracking cookies until the user explicitly accepts; declining consent leaves PostHog in the opted-out state for the session and future visits

**Plans**: TBD

### Phase 22: RBAC

**Goal**: API endpoints can be guarded by role and administrators can assign roles to users — with `admin` and `member` available from the first deploy
**Depends on**: Phase 21
**Requirements**: RBAC-01, RBAC-02, RBAC-03
**Success Criteria** (what must be TRUE):

1. A request to an endpoint decorated with `@require_role("admin")` from a user without the `admin` group membership returns HTTP 403 with a JSON error body — no stack trace, no 500
2. An authenticated admin user can call `POST /api/v1/users/{id}/roles` to assign or remove a role from another user — a non-admin calling this endpoint receives HTTP 403
3. On a fresh database after running migrations, Django Groups named `admin` and `member` exist without any manual fixture loading or admin UI interaction

**Plans**: TBD

### Phase 23: Feature Entitlements

**Goal**: Application code can gate features by billing plan using a single function call, with Redis-cached results and a safe fallback when billing is not installed
**Depends on**: Phase 22
**Requirements**: ENT-01, ENT-02, ENT-03
**Success Criteria** (what must be TRUE):

1. A developer can call `has_feature(user, "advanced_analytics")` anywhere in the application and receive `True` or `False` based on the user's active subscription plan and the `BILLING_PLANS` settings dict — no database query is made on the second call within the cache TTL
2. When a Stripe `customer.subscription.updated` webhook is processed (plan upgrade or downgrade), the user's cached entitlement keys are invalidated immediately — the next `has_feature()` call reflects the new plan without waiting for TTL expiry
3. In a project generated with `--without billing`, `has_feature(user, any_key)` returns `True` for every key — features are fully accessible and no import errors occur when the billing module is absent

**Plans**: TBD

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
| 16. Security Hardening           | v1.2      | 3/3            | Complete    | 2026-03-11 |
| 17. Dev-Time Security Gates      | v1.2      | 3/3            | Complete    | 2026-03-11 |
| 18. Dev-Time Quality Gates       | v1.2      | 3/3            | Complete    | 2026-03-11 |
| 19. Transactional Email          | v1.3      | 0/TBD          | Not started | -          |
| 20. Social Auth                  | v1.3      | 0/TBD          | Not started | -          |
| 21. GDPR Baseline                | v1.3      | 0/TBD          | Not started | -          |
| 22. RBAC                         | v1.3      | 0/TBD          | Not started | -          |
| 23. Feature Entitlements         | v1.3      | 0/TBD          | Not started | -          |
