# Roadmap: Foundation Template

## Milestones

- ✅ **v1.0 Foundation Template** — Phases 1–8 (shipped 2026-03-07)
- ✅ **v1.1 Billing & Payments Module** — Phases 9–12 (shipped 2026-03-11)
- ✅ **v1.2 Observability & DevEx Hardening** — Phases 13–18 (shipped 2026-03-12)
- ✅ **v1.3 SaaS Functional Baseline** — Phases 19–25 (shipped 2026-03-13)
- ✅ **v1.4 B2B Module** — Phases 26–34 (shipped 2026-03-14)
- 🚧 **v1.5 Automated Testing & Claude Automation** — Phases 35–38 (in progress)

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

<details>
<summary>✅ v1.3 SaaS Functional Baseline (Phases 19–25) — SHIPPED 2026-03-13</summary>

- [x] Phase 19: Transactional Email (4/4 plans) — `EmailAdapter` ABC with `ResendAdapter` default; Celery-queued async dispatch; HTML templates with inline CSS; `ConsoleAdapter` for dev; `--without email` scaffolder flag (completed 2026-03-12)
- [x] Phase 20: Social Auth (6/6 plans) — Google + GitHub OAuth on web; Apple Sign In on iOS mobile; email-collision account merge; `--without social-auth` scaffolder flag (completed 2026-03-12)
- [x] Phase 21: GDPR Baseline (4/4 plans) — Async account hard delete cascading all third-party data; JSON personal data export; cookie consent banner gating PostHog (completed 2026-03-12)
- [x] Phase 22: RBAC (3/3 plans) — `@require_role("admin")` decorator; role assignment API; seeded `admin`/`member` groups via data migration (completed 2026-03-12)
- [x] Phase 23: Feature Entitlements (3/3 plans) — `has_feature(user, key)` utility; Redis-cached results; billing-off fallback returns `True` (completed 2026-03-12)
- [x] Phase 24: Social Auth OAuth Callback Pages (2/2 plans) — OAuth callback/error pages at `/auth/callback` + `/auth/error`; closes INT-01, INT-02 (completed 2026-03-12)
- [x] Phase 25: GDPR Export plan_id Accuracy (1/1 plan) — `AccountExportService` reads `Subscription.plan_id` from ORM; closes INT-03 (completed 2026-03-12)

Full archive: `.planning/milestones/v1.3-ROADMAP.md`

</details>

<details>
<summary>✅ v1.4 B2B Module (Phases 26–34) — SHIPPED 2026-03-14</summary>

- [x] Phase 26: Organization Model + Per-Org Billing (6/6 plans) — Organization, Membership, roles, invitation flow, ownership transfer, per-org Stripe billing, `has_org_feature()` (completed 2026-03-13)
- [x] Phase 27: Outbound Webhooks (4/4 plans) — Webhook endpoint registry, HMAC-signed Celery delivery with exponential backoff, delivery log, manual retry, circuit breaker auto-disable (completed 2026-03-13)
- [x] Phase 28: API Key Authentication (4/4 plans) — API key create/revoke/scopes, SHA-256 hash storage, Ninja auth backend, per-key rate limiting, usage tracking (completed 2026-03-13)
- [x] Phase 29: Audit Logging (3/3 plans) — pghistory triggers on all B2B models, AuditContextMiddleware, org-scoped cursor-paginated audit log API (completed 2026-03-13)
- [x] Phase 30: Admin Backoffice (3/3 plans) — django-unfold theme across all ModelAdmins, django-hijack impersonation wired to AuditLog (completed 2026-03-13)
- [x] Phase 31: CLI Scaffolder Integration (3/3 plans) — `--with b2b` flag, B2B_START/B2B_END markers throughout, clean removal, `manage.py check` verified (completed 2026-03-13)
- [x] Phase 32: Webhook Wiring + Invitation URL Fix (2/2 plans) — Wire `fire_webhook_event()` to production callers; fix `InvitationService` hardcoded URL (gap closure: HOOK-01, ORG-02) (completed 2026-03-13)
- [x] Phase 33: ApiKeyAuth Example Endpoint (2/2 plans) — `/me/api-keys/ping` demonstrator with `ApiKeyAuth` + `RequireScope` activating full auth chain (gap closure: AKEY-01, AKEY-02, AKEY-03) (completed 2026-03-14)
- [x] Phase 34: Admin + Audit Context Fixes (2/2 plans) — Register `OrgCustomerAdmin`; add APIKey org FK for audit context injection (gap closure: BILL-01, AUDIT-01) (completed 2026-03-14)

Full archive: `.planning/milestones/v1.4-ROADMAP.md`

</details>

### 🚧 v1.5 Automated Testing & Claude Automation (In Progress)

**Milestone Goal:** Every feature in the template has automated API + E2E coverage runnable by Claude in two modes — a dev loop where Claude auto-fixes failures, and a CI mode that runs headlessly and produces structured reports tied to OpenSpec requirement IDs.

- [ ] **Phase 35: Automation Scripts + Spec Traceability** — Shell runners, orchestrator, `check-req-coverage.py`, and `@pytest.mark.req()` markers retrofitted across all existing tests
- [ ] **Phase 36: Web E2E — Core Flows** — Playwright tests for auth, settings (GDPR export button closes v1.3 audit gap), billing, and health probes; self-seeding fixtures
- [ ] **Phase 37: Web E2E — B2B & Social Flows** — Playwright tests for social auth redirects, RBAC access control, org management, API key management, webhook management, and audit log
- [ ] **Phase 38: CI Integration + Claude Automation Docs** — Nightly scheduled E2E GitHub Actions workflow, PR smoke job, FAILURES.md artifact upload, root + app-level CLAUDE.md documentation

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

> Phase details for v1.3 (Phases 19–25) archived to `.planning/milestones/v1.3-ROADMAP.md`

> Phase details for v1.4 (Phases 26–34) archived to `.planning/milestones/v1.4-ROADMAP.md`

### Phase 35: Automation Scripts + Spec Traceability

**Goal**: A developer (or Claude) can run one script to execute all tests and get a structured failure report, and `check-req-coverage.py` shows exactly which OpenSpec requirements have no test coverage across both pytest and Playwright suites
**Depends on**: Phase 34 (v1.4 complete)
**Requirements**: AUTO-01, AUTO-02, AUTO-03, AUTO-04, TRACE-01, TRACE-03
**Success Criteria** (what must be TRUE):

1. Running `scripts/run-api-tests.sh` executes the full pytest suite and writes a `test-results/FAILURES.md` containing every failed test name, the assertion that failed, and the `@pytest.mark.req()` IDs from each failing test
2. Running `scripts/run-e2e-tests.sh` executes the Playwright suite against any target URL passed as an environment variable — the same script works unchanged in local dev and CI without conditional branches
3. Running `scripts/run-all-tests.sh --mode=dev` produces `test-results/FAILURES.md` with a structured format that Claude can parse to identify which tests to fix and which requirements they cover
4. Running `scripts/check-req-coverage.py` produces a table listing every v1.1–v1.4 requirement ID with status (covered / partial / uncovered) based on `@pytest.mark.req()` markers found across all test files
5. Every existing pytest test function that exercises a specific feature has a `@pytest.mark.req("REQ-ID")` marker — `check-req-coverage.py` shows zero uncovered requirements for implemented features

**Plans**: TBD

### Phase 36: Web E2E — Core Flows

**Goal**: Claude can run Playwright tests that exercise auth, settings (including the GDPR data export button that has no existing UI test), billing, and health probes against a running web app — tests create their own data and do not depend on pre-existing database state
**Depends on**: Phase 35
**Requirements**: E2E-01, E2E-02, E2E-03, E2E-04, TRACE-02
**Success Criteria** (what must be TRUE):

1. Running the E2E auth suite produces passing tests for: signup → dashboard redirect, login with valid credentials, login with invalid credentials showing an inline error, and logout clearing the session and redirecting to the login page
2. Running the E2E settings suite produces a passing test that clicks the "Download my data" button and receives a JSON file download — this closes the v1.3 audit gap where `GET /api/v1/account/export` existed but had no frontend trigger
3. Running the E2E billing suite produces passing tests that verify: plan cards render on the billing page, the upgrade CTA is present and links to Stripe, and the current plan badge is visible in the settings sidebar
4. Running the E2E health probe suite produces passing tests that assert `GET /api/health/live`, `/api/health/ready`, and `/api/health/startup` each return HTTP 200 via direct API assertions (not browser navigation)
5. Every Playwright test that covers a specific requirement has a `// @spec: REQ-ID` comment, and `check-req-coverage.py` counts these comments as coverage evidence

**Plans**: TBD

### Phase 37: Web E2E — B2B & Social Flows

**Goal**: E2E tests exercise all B2B flows — org management, API keys, webhooks, and audit log — plus social auth redirect behavior, so that every v1.3 and v1.4 UI-facing feature has at least one browser-level test
**Depends on**: Phase 36
**Requirements**: E2E-05, E2E-06, E2E-07, E2E-08, E2E-09, E2E-10
**Success Criteria** (what must be TRUE):

1. Running the E2E social auth suite produces passing tests that verify: the Google OAuth button and GitHub OAuth button are present on the login page, and clicking either button triggers a redirect to the respective OAuth provider URL (no live credentials required)
2. Running the E2E RBAC suite produces passing tests that verify: a regular user accessing an admin-only route receives a 403 response, and a user with the admin role can access that same route successfully
3. Running the E2E org management suite produces passing tests that verify: creating an organization succeeds and the org appears in the user's org list, and the invite flow sends an invitation visible in the org member list as pending
4. Running the E2E API key suite produces passing tests that verify: creating a key displays the raw key value exactly once on the screen, the key appears masked in the key list on refresh, and deleting a key removes it from the list
5. Running the E2E webhook + audit log suite produces passing tests that verify: a registered webhook endpoint appears in the endpoint list, deleting it removes it, and an admin can view audit log entries that show actor identity, action type, and timestamp

**Plans**: TBD

### Phase 38: CI Integration + Claude Automation Docs

**Goal**: Nightly GitHub Actions runs the full E2E suite unattended and creates a GitHub issue on failure; PR CI runs a smoke test on every pull request; CLAUDE.md in root and every app documents the two-mode testing pattern so every future project scaffolded from this template inherits the automation conventions automatically
**Depends on**: Phase 37
**Requirements**: CI-01, CI-02, CI-03, DOCS-01, DOCS-02, DOCS-03
**Success Criteria** (what must be TRUE):

1. A nightly GitHub Actions workflow at 2am UTC spins up Docker Compose, runs migrations, seeds test users, executes the full Playwright suite, tears down, and — on failure — automatically opens a GitHub issue with a link to the FAILURES.md artifact
2. The existing `ci.yml` PR workflow includes an E2E smoke job that runs the auth flow and health probe tests against a Docker Compose environment and blocks merge on failure
3. CI E2E failures produce a `FAILURES.md` artifact uploaded to GitHub Actions that contains structured failure information Claude can retrieve and act on to fix failures locally
4. The root `CLAUDE.md` documents the dev auto-fix loop (`run-all-tests.sh --mode=dev` → Claude reads FAILURES.md → Claude fixes → repeat) and the CI report mode, with explicit instructions that all new feature tests must include `@pytest.mark.req()` or `// @spec:` markers before a phase can be marked complete
5. `apps/api/CLAUDE.md` and `apps/web/CLAUDE.md` each document how to add tests for new features — including which fixture patterns to follow and the requirement that spec traceability markers are added before submitting work for verification

**Plans**: TBD

## Progress

| Phase                              | Milestone | Plans Complete | Status      | Completed  |
| ---------------------------------- | --------- | -------------- | ----------- | ---------- |
| 1. Monorepo Foundation             | v1.0      | 4/4            | Complete    | 2026-02-17 |
| 2. API Core + Auth Backend         | v1.0      | 5/5            | Complete    | 2026-02-17 |
| 3. Shared Packages + Types         | v1.0      | 6/6            | Complete    | 2026-02-17 |
| 4. Web Application                 | v1.0      | 5/5            | Complete    | 2026-02-17 |
| 5. Mobile Application              | v1.0      | 4/4            | Complete    | 2026-02-17 |
| 6. AI Module                       | v1.0      | 5/5            | Complete    | 2026-02-17 |
| 7. DevEx + CI/CD                   | v1.0      | 4/4            | Complete    | 2026-02-17 |
| 8. CLI Scaffolder                  | v1.0      | 3/3            | Complete    | 2026-02-17 |
| 9. Billing Scaffold                | v1.1      | 3/3            | Complete    | 2026-03-07 |
| 10. Webhook Infra + Service        | v1.1      | 3/3            | Complete    | 2026-03-08 |
| 11. API Endpoints + Frontend       | v1.1      | 8/8            | Complete    | 2026-03-10 |
| 12. Invoice PDF + CLI              | v1.1      | 3/3            | Complete    | 2026-03-11 |
| 13. Structured Logging + Tracing   | v1.2      | 3/3            | Complete    | 2026-03-11 |
| 14. ObservabilityAdapter           | v1.2      | 4/4            | Complete    | 2026-03-11 |
| 15. Health Probes + Celery Infra   | v1.2      | 3/3            | Complete    | 2026-03-11 |
| 16. Security Hardening             | v1.2      | 3/3            | Complete    | 2026-03-11 |
| 17. Dev-Time Security Gates        | v1.2      | 3/3            | Complete    | 2026-03-11 |
| 18. Dev-Time Quality Gates         | v1.2      | 3/3            | Complete    | 2026-03-11 |
| 19. Transactional Email            | v1.3      | 4/4            | Complete    | 2026-03-12 |
| 20. Social Auth                    | v1.3      | 6/6            | Complete    | 2026-03-12 |
| 21. GDPR Baseline                  | v1.3      | 4/4            | Complete    | 2026-03-12 |
| 22. RBAC                           | v1.3      | 3/3            | Complete    | 2026-03-12 |
| 23. Feature Entitlements           | v1.3      | 3/3            | Complete    | 2026-03-12 |
| 24. Social Auth OAuth Callback     | v1.3      | 2/2            | Complete    | 2026-03-12 |
| 25. GDPR Export plan_id Accuracy   | v1.3      | 1/1            | Complete    | 2026-03-12 |
| 26. Organization + Per-Org Billing | v1.4      | 6/6            | Complete    | 2026-03-13 |
| 27. Outbound Webhooks              | v1.4      | 4/4            | Complete    | 2026-03-13 |
| 28. API Key Authentication         | v1.4      | 4/4            | Complete    | 2026-03-13 |
| 29. Audit Logging                  | v1.4      | 3/3            | Complete    | 2026-03-13 |
| 30. Admin Backoffice               | v1.4      | 3/3            | Complete    | 2026-03-13 |
| 31. CLI Scaffolder Integration     | v1.4      | 3/3            | Complete    | 2026-03-13 |
| 32. Webhook Wiring + Invite URL    | v1.4      | 2/2            | Complete    | 2026-03-13 |
| 33. ApiKeyAuth Example Endpoint    | v1.4      | 2/2            | Complete    | 2026-03-14 |
| 34. Admin + Audit Context Fixes    | v1.4      | 2/2            | Complete    | 2026-03-14 |
| 35. Automation Scripts + Tracing   | v1.5      | 0/TBD          | Not started | -          |
| 36. Web E2E — Core Flows           | v1.5      | 0/TBD          | Not started | -          |
| 37. Web E2E — B2B & Social Flows   | v1.5      | 0/TBD          | Not started | -          |
| 38. CI Integration + Claude Docs   | v1.5      | 0/TBD          | Not started | -          |
