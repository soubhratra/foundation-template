# Milestones

## v1.4 B2B Module (Shipped: 2026-03-14)

**Phases completed:** 9 phases (26–34), 29 plans | **Requirements:** 19/19
**Timeline:** 2026-03-13 → 2026-03-14 (2 days) | **Verifications:** Phase 26 (15/15) + Phase 27 (32/32) + Phase 28 (30/30) + Phase 29 (16/16) + Phase 30 (19/19 auto) + Phase 31 (2/2 TTY approved) + Phase 32 (20/20) + Phase 33 (38/38) + Phase 34 (64/64) = 236/236 truths

**Key accomplishments:**

1. `Organization` model with membership/roles (owner/admin/member), email invitation flow (72h token), ownership transfer; `IsOrgMember`/`IsOrgAdmin` Ninja permission classes; `OrgCustomer` for per-org Stripe billing; `has_org_feature(user, org, key)` with org-member cache invalidation on subscription update; `--with b2b` scaffolder flag (opt-in)
2. Outbound webhook registry — `WebhookEndpoint` CRUD + HMAC-SHA256 signed delivery via Celery (7-retry exponential backoff); circuit breaker auto-disables endpoint after N consecutive failures + emails org admin; `fire_webhook_event()` wired to user.created, org.member_added, subscription.updated event sites; delivery history + manual retry API
3. `APIKey` model — scoped keys with SHA-256 hash storage (raw key shown once); `ApiKeyAuth` Ninja auth backend + `RequireScope` permission class; `ApiKeyRateLimitMiddleware` with `X-RateLimit-*` response headers; `last_used_at`/`usage_count` tracking; `/me/api-keys/ping` demonstrator endpoint activating full auth chain
4. Audit logging via `django-pghistory` — `@track()` triggers on Organization, Membership, APIKey, WebhookEndpoint; `AuditContextMiddleware` attaches `user_id` + `org_id` automatically; org-scoped cursor-paginated `GET /api/v1/org/{slug}/audit-log`; impersonation entries present but `impersonator` field excluded from org-level queries
5. `django-unfold` theme across all domain ModelAdmins; `django-hijack` staff impersonation with persistent banner; `ImpersonationEvent` model + hijack signals → audit log with `impersonator` FK; `OrgCustomerAdmin` in unfold sidebar for per-org billing inspection
6. Full B2B scaffolder integration — `B2B_START`/`B2B_END` markers throughout; `removeB2BModule()` CLI strips module cleanly; `manage.py check` verified post-removal; pytest test in CI suite confirms clean removal on every push

**Known Tech Debt:**

- `_resolve_org_plan_id()` stub always returns None — per-org Subscription lookup deferred (BILL-02 structurally present but non-functional until Subscription is linked to OrgCustomer)
- `IsOrgAdmin` on transfer-ownership endpoint (should be IsOwner — admin can transfer without owner consent)
- API key revoke route uses `{key_id}` UUID (spec says `{prefix}`) — spec divergence deferred
- No composite DB index on `(org_id, pgh_created_at, pgh_id)` for audit log cursor pagination
- 4 browser verification items for Admin Backoffice (Unfold theme, hijack button/banner/redirect) — automated tests pass; requires live dev server
- Phase 34 VALIDATION.md in draft state (run `/gsd:validate-phase 34` to close formality)

**Archive:** `.planning/milestones/v1.4-ROADMAP.md` | `.planning/milestones/v1.4-REQUIREMENTS.md`

---

## v1.3 SaaS Functional Baseline (Shipped: 2026-03-13)

**Phases completed:** 7 phases, 23 plans | **Phases:** 19–25
**Timeline:** 2026-03-12 (1 day) | **Verifications:** Phase 19 (9/9) + Phase 20 (30/30) + Phase 21 (30/30) + Phase 22 (14/14) + Phase 23 (9/9) + Phase 24 (9/9) + Phase 25 (8/8) = 109/109 truths

**Key accomplishments:**

1. `EmailAdapter` ABC with `ResendAdapter` default — Celery-queued async dispatch via `transaction.on_commit()`, CSS inlined via `premailer`, `ConsoleAdapter` auto-activated in dev (no credentials needed); `--without email` removes module cleanly
2. Google + GitHub OAuth on web (allauth headless) + Apple Sign In on iOS with native JWT verification endpoint; email-collision auto-merge for Google/GitHub; `SocialAccountAdapter` overridden to exclude Apple relay addresses; `--without social-auth` flag
3. Account hard delete cascading Stripe + PostHog + social accounts via `UserDeletionService` + async Celery task (HTTP 202 immediately); JSON personal data export via `AccountExportService` with billing plan accuracy; `CookieConsentBanner` consent-gating PostHog init (GDPR Article 17/20)
4. `RequireRole` permission class + `@require_role("admin")` decorator returning HTTP 403; `AdminController` with 4 role endpoints; `admin`/`member` groups seeded via data migration `0003_seed_roles` — zero manual fixture loading
5. `has_feature(user, key)` checked against `BILLING_PLANS` settings dict; Redis-cached (300s TTL, `entitlements:{user.pk}` key); auto-invalidated on `customer.subscription.updated` webhook; returns `True` for all features when billing module absent
6. Gap closure: OAuth callback/error pages at `/auth/callback` + `/auth/error` (INT-01, INT-02); GDPR export `plan_id` reads from `Subscription.plan_id` ORM instead of hard-coded `None` (INT-03)

**Known Tech Debt:**

- No "Download my data" button in `/settings` UI — `GET /api/v1/account/export` works but has no frontend trigger
- `UserDeletionService` + Celery task both implement the 4-step GDPR cascade (future changes must be applied in two places)
- `AdminController` uses Django middleware auth rather than ninja auth stack (documented, functional)

**Archive:** `.planning/milestones/v1.3-ROADMAP.md` | `.planning/milestones/v1.3-REQUIREMENTS.md`

---

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
