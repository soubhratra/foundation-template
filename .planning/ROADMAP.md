# Roadmap: Foundation Template

## Milestones

- ✅ **v1.0 Foundation Template** — Phases 1–8 (shipped 2026-03-07)
- ✅ **v1.1 Billing & Payments Module** — Phases 9–12 (shipped 2026-03-11)
- ✅ **v1.2 Observability & DevEx Hardening** — Phases 13–18 (shipped 2026-03-12)
- ✅ **v1.3 SaaS Functional Baseline** — Phases 19–25 (shipped 2026-03-13)
- 🚧 **v1.4 B2B Module** — Phases 26–31 (in progress)

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

### 🚧 v1.4 B2B Module (In Progress)

**Milestone Goal:** Add an optional B2B layer — organizations, outbound webhooks, API keys, audit logging, and admin backoffice — so products targeting teams or developers can scaffold enterprise-grade infrastructure from day one.

- [x] **Phase 26: Organization Model + Per-Org Billing** - Organization, Membership, roles, invitation flow, ownership transfer, per-org Stripe billing, and entitlement resolution (completed 2026-03-13)
- [x] **Phase 27: Outbound Webhooks** - Webhook endpoint registry, HMAC-signed Celery delivery with exponential backoff, delivery log, manual retry, auto-disable circuit breaker (completed 2026-03-13)
- [ ] **Phase 28: API Key Authentication** - API key create/revoke/scopes, SHA-256 hash storage, Ninja auth backend, per-key rate limiting, usage tracking
- [ ] **Phase 29: Audit Logging** - pghistory triggers on all B2B models, AuditContextMiddleware, org-scoped paginated audit log read API
- [ ] **Phase 30: Admin Backoffice** - django-unfold theme across all ModelAdmins, django-hijack impersonation wired to AuditLog
- [ ] **Phase 31: CLI Scaffolder Integration** - `--with b2b` flag, B2B_START/B2B_END markers throughout, clean removal, `manage.py check` verified

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

### Phase 26: Organization Model + Per-Org Billing

**Goal**: Products can model teams — users belong to organizations with explicit roles, invite teammates by email, and billing entitlements resolve at the org level before falling back to personal plans
**Depends on**: Phase 25 (v1.3 complete)
**Requirements**: ORG-01, ORG-02, ORG-03, ORG-04, ORG-05, BILL-01, BILL-02
**Success Criteria** (what must be TRUE):

1. A user can create an organization (name + slug), becoming the owner automatically, and can invite members by email — invitations expire after 72 hours and can be accepted by both new signups and existing users
2. Org members see only resources scoped to their organization — a request made by a member of Org A attempting to access Org B's resources returns HTTP 403
3. An org owner can assign or change member roles (owner/admin/member) and transfer ownership to another member via a dedicated endpoint; the previous owner becomes an admin
4. When an organization has an active Stripe subscription, all org members receive entitlements from the org plan — `has_org_feature(user, org, key)` returns the org-plan result; personal plan is only consulted when no org subscription exists
5. Updating an org subscription via Stripe webhook invalidates the entitlement cache for all current org members, not just the billing contact

**Plans**: 6 plans

Plans:

- [ ] 26-01-PLAN.md — Wave 1: RED test stubs for all org requirements
- [ ] 26-02-PLAN.md — Wave 2: Organization, Membership, Invitation, OrgCustomer models + migration
- [ ] 26-03-PLAN.md — Wave 3: IsOrgMember and IsOrgAdmin permission classes
- [ ] 26-04-PLAN.md — Wave 3: OrgService, MembershipService, InvitationService, \_resolve_org_plan_id
- [ ] 26-05-PLAN.md — Wave 4: Schemas + controllers (OrgController, MembershipController, InvitationController)
- [ ] 26-06-PLAN.md — Wave 5: has_org_feature() + org member cache invalidation on webhook

### Phase 27: Outbound Webhooks

**Goal**: Org admins can register external HTTP endpoints to receive signed event notifications; failed deliveries are retried automatically and the admin is notified when an endpoint is permanently unreachable
**Depends on**: Phase 26
**Requirements**: HOOK-01, HOOK-02, HOOK-03, HOOK-04
**Success Criteria** (what must be TRUE):

1. An org admin can register a webhook endpoint URL; every delivery is signed with HMAC-SHA256 and includes a `webhook_version: "v1"` field — a recipient can verify the signature using the shared secret
2. A user can view the paginated delivery history for any endpoint they manage, including HTTP status code, attempt count, and response body for each delivery attempt
3. A failed delivery is retried automatically via Celery with exponential backoff — the delivery log shows each retry attempt as it occurs; after the maximum number of retries, the delivery is marked as permanently failed
4. After N consecutive failures across deliveries to the same endpoint, the endpoint is automatically disabled and the org admin receives an email notification identifying the endpoint and last failure reason
5. A user can manually trigger a retry for any individual failed delivery via `POST /api/v1/webhooks/deliveries/{id}/retry` without needing to re-register the endpoint

**Plans**: 4 plans

Plans:

- [ ] 27-01-PLAN.md — Wave 1: RED test stubs (test_models, test_utils, test_tasks, test_controllers, test_checks)
- [ ] 27-02-PLAN.md — Wave 2: apps/webhooks/ app — models + migration + fire_webhook_event() + WEBHOOK_EVENTS check
- [ ] 27-03-PLAN.md — Wave 3: deliver_webhook Celery task — HMAC signing, retry, circuit breaker, cleanup
- [ ] 27-04-PLAN.md — Wave 4: schemas + controllers — all 8 HTTP endpoints, auto-discovered

### Phase 28: API Key Authentication

**Goal**: Users can create scoped API keys for programmatic access; keys are rate-limited per-key and usage is tracked so products can build tiered API plans on top
**Depends on**: Phase 26
**Requirements**: AKEY-01, AKEY-02, AKEY-03
**Success Criteria** (what must be TRUE):

1. A user can create an API key with one or more scopes; the raw key is displayed exactly once at creation and cannot be retrieved again — only a non-secret prefix and SHA-256 hash are stored; the key can be revoked at any time
2. An API request authenticated with a key that lacks the required scope is rejected with HTTP 403 — a request authenticated with a valid session but submitted to a key-only endpoint is also rejected; there is no auth fallback that bypasses scope enforcement
3. API key requests that exceed the per-key rate limit receive HTTP 429 with `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset` response headers
4. Every authenticated API key request updates `last_used_at` and increments `usage_count` on the key record — these values are visible to the user managing the key

**Plans**: TBD

### Phase 29: Audit Logging

**Goal**: Every significant change to B2B models is recorded automatically with full actor and org context; org admins can query their own audit trail without exposing impersonation activity
**Depends on**: Phase 28 (all B2B models must exist before triggers are applied)
**Requirements**: AUDIT-01, AUDIT-02
**Success Criteria** (what must be TRUE):

1. Creating, updating, or deleting an Organization, Membership, APIKey, or WebhookEndpoint record automatically writes an audit entry — no manual logging call is required in application code
2. Every audit entry includes the acting user, the org context, the changed model, the before/after values, and the request URL — Celery task actions include the actor ID passed explicitly (no `request.user` inside tasks)
3. An org owner or admin can query a paginated, filterable audit log for their organization via `GET /api/v1/org/{slug}/audit-log` — entries from impersonation sessions are present in the log but the `impersonator` field is not exposed to org-level queries (staff-only)

**Plans**: TBD

### Phase 30: Admin Backoffice

**Goal**: Staff users have a polished admin interface for customer support and can temporarily impersonate any non-staff user to diagnose issues; all impersonation events are permanently recorded
**Depends on**: Phase 29 (AuditLog with impersonator FK must exist before hijack is enabled)
**Requirements**: ADMIN-01, ADMIN-02
**Success Criteria** (what must be TRUE):

1. The Django admin renders with the django-unfold theme — navigation sidebar is configured with sections for all B2B domains (organizations, API keys, webhooks, audit log); all existing domain ModelAdmins inherit from `UnfoldModelAdmin`
2. A staff user can impersonate any non-staff, non-superuser account from the admin interface; a persistent banner is visible on every page during impersonation; the session cannot impersonate another staff user or superuser
3. Every impersonation start and end event writes an AuditLog entry with the `impersonator` FK populated — the entry is visible to staff in the admin but excluded from org-level audit queries

**Plans**: TBD

### Phase 31: CLI Scaffolder Integration

**Goal**: The `--with b2b` flag in `create-foundation-app` cleanly includes or excludes the entire B2B module; a project without B2B has no orphaned imports, no failing migrations, and passes `manage.py check`
**Depends on**: Phase 30 (all B2B code must be final before wrapping in markers)
**Requirements**: SCAFF-01
**Success Criteria** (what must be TRUE):

1. Running `create-foundation-app --with b2b` produces a project that starts, migrates, and passes `manage.py check` with all B2B features active
2. Running `create-foundation-app` without `--with b2b` produces a project with zero B2B imports, no B2B migrations, and a clean `manage.py check` — no `# B2B_START` / `# B2B_END` markers remain in the output
3. A pytest test in `apps/api/tests/` verifies that `manage.py check` passes on the B2B-removed scaffold — this test is part of the standard CI suite

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
| 26. Organization + Per-Org Billing | 6/6       | Complete       | 2026-03-13  | -          |
| 27. Outbound Webhooks              | 4/4       | Complete       | 2026-03-13  | -          |
| 28. API Key Authentication         | v1.4      | 0/TBD          | Not started | -          |
| 29. Audit Logging                  | v1.4      | 0/TBD          | Not started | -          |
| 30. Admin Backoffice               | v1.4      | 0/TBD          | Not started | -          |
| 31. CLI Scaffolder Integration     | v1.4      | 0/TBD          | Not started | -          |
