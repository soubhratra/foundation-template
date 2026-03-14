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

### Validated (v1.2)

- ✓ Structured JSON logging via `structlog` with `request_id`, `user_id`, `duration_ms` on every request — v1.2
- ✓ Distributed tracing via OpenTelemetry auto-instrumentation (Django + Celery + DB), OTLP exporter, Jaeger in Docker Compose — v1.2
- ✓ Error tracking + product analytics via `ObservabilityAdapter` ABC with `PostHogAdapter` default (Django + Celery + Next.js + Expo) — `--without observability` removes it — v1.2
- ✓ Enhanced health probes: `/api/health/live`, `/api/health/ready`, `/api/health/startup` (plain Django, no Ninja/auth) — v1.2
- ✓ Rate limiting on auth endpoints via `django-ratelimit`, Redis-backed (HTTP 429 + `Retry-After`) — v1.2
- ✓ Security headers via `django-csp` 4.0 (nonce API), HSTS (production only), X-Frame-Options (Django + Next.js `headers()`) — v1.2
- ✓ Redis cache backend via `django-redis` as default cache + session store — v1.2
- ✓ Celery Beat scaffold with `DatabaseScheduler` + example periodic task in Docker Compose — v1.2
- ✓ Flower dev-only monitoring in Docker Compose — v1.2
- ✓ Secret scanning via `detect-secrets` in pre-commit + CI — v1.2
- ✓ Python SAST via `bandit` in pre-commit + CI — v1.2
- ✓ Dependency auditing via `pip-audit` + `pnpm audit` as CI gate — v1.2
- ✓ N+1 detection via `nplusone` as autouse pytest fixture (blinker signal with explicit teardown) — v1.2
- ✓ API contract fuzzing via `schemathesis` as CI job (30 examples, 5s timeout, auth/billing paths excluded) — v1.2
- ✓ `django-debug-toolbar` for local query analysis (dev only) — v1.2
- ✓ `commitlint` pre-commit hook for conventional commit enforcement — v1.2
- ✓ ruff McCabe complexity gate (max=10) in pre-commit — v1.2

### Validated (v1.3)

- ✓ Transactional email via `EmailAdapter` ABC (`ResendAdapter` default, Celery-queued via `on_commit`, CSS inlined via `premailer`, `ConsoleAdapter` in dev) — `--without email` removes — v1.3
- ✓ Social auth: Google + GitHub OAuth (web) + Apple Sign In (iOS, native JWT endpoint); email-collision auto-merge (Google/GitHub); `SocialAccountAdapter` overrides for Apple relay exclusion — `--without social-auth` removes — v1.3
- ✓ GDPR baseline: `UserDeletionService` async cascade (Stripe + PostHog + social accounts, HTTP 202); `AccountExportService` JSON export with accurate `plan_id`; `CookieConsentBanner` consent-gating PostHog init — v1.3
- ✓ RBAC: `RequireRole` permission class + `@require_role("admin")` decorator; `AdminController` (4 endpoints); `admin`/`member` groups seeded via data migration `0003_seed_roles` — v1.3
- ✓ Feature entitlements: `has_feature(user, key)` against `BILLING_PLANS` settings dict; Redis-cached (300s TTL, per-user key); invalidated on `customer.subscription.updated` webhook; returns `True` when billing absent — v1.3

### Validated (v1.4)

- ✓ `Organization` model with membership/roles (owner/admin/member); email invitation flow (72h token); ownership transfer; `IsOrgMember`/`IsOrgAdmin` Ninja permission classes; cross-org access returns 403 — v1.4
- ✓ `OrgCustomer` for per-org Stripe billing; `has_org_feature(user, org, key)` with org-member cache invalidation on subscription update — v1.4
- ✓ Outbound webhook registry — HMAC-SHA256 signed delivery via Celery (7-retry exponential backoff); circuit breaker auto-disables after N failures + emails org admin; `fire_webhook_event()` wired to user.created, org.member_added, subscription.updated — v1.4
- ✓ `APIKey` model — scoped keys with SHA-256 hash storage; `ApiKeyAuth` + `RequireScope` Ninja auth; `ApiKeyRateLimitMiddleware` with `X-RateLimit-*` headers; `last_used_at`/`usage_count` tracking — v1.4
- ✓ Audit logging via `django-pghistory` — `@track()` triggers on Organization, Membership, APIKey, WebhookEndpoint; `AuditContextMiddleware`; org-scoped cursor-paginated audit log API — v1.4
- ✓ `django-unfold` admin theme + `django-hijack` impersonation + `ImpersonationEvent` audit log entries; `OrgCustomerAdmin` for per-org billing inspection — v1.4
- ✓ `--with b2b` scaffolder flag (opt-in); `B2B_START`/`B2B_END` markers; `removeB2BModule()` clean removal; `manage.py check` verified post-removal — v1.4

### Active (v1.5)

### Out of Scope

- Billing/payments as product-specific logic — the v1.1 module provides infrastructure and adapter pattern; each project configures plans, pricing, and provider credentials
- Multi-tenancy — each project decides its own tenancy model
- Product-specific business logic — template provides infrastructure, not features
- Specific cloud provider lock-in — Docker-first, deploy anywhere
- Admin dashboard — Django admin is sufficient for template
- Real-time features (WebSockets) — product-specific, add per-project
- Email open/click tracking, MailgunAdapter, SESAdapter — beyond template scope; Resend is the default, swap via one setting
- Google Sign In on mobile — requires dev build + Android/iOS credentials; high complexity; deferred
- SSO/SAML, SMS/2FA — product-specific; OpenSpec guide only
- Object-level permissions (`django-guardian`) — product-specific
- Multi-tenancy — product-specific tenancy model

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

| Decision                                                                       | Rationale                                                                                                                                                                 | Outcome                                                                                                                              |
| ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| Django Allauth for auth                                                        | Native Django, full control, no external auth service dependency                                                                                                          | ✓ Good — headless mode + dual auth (session+JWT) works cleanly                                                                       |
| AI as optional module                                                          | Not every SaaS needs AI; pluggable avoids bloat                                                                                                                           | ✓ Good — CLI scaffolder removes AI module cleanly via feature flag                                                                   |
| Billing module in template (v1.1)                                              | Products need billing fast; adapter pattern keeps it swappable, not coupled                                                                                               | ✓ Good — PaymentAdapter ABC + StripeAdapter; swappable with one Django setting                                                       |
| No multi-tenancy in template                                                   | Tenancy model depends on product; template shouldn't constrain                                                                                                            | ✓ Good — confirmed valid                                                                                                             |
| CLI scaffolder for new projects                                                | Better than GitHub template — can customize features, names, configs                                                                                                      | ✓ Good — `create-foundation-app` with validation + rollback shipped                                                                  |
| Auto-generated TS from OpenAPI                                                 | Single source of truth for API types; Django Ninja generates OpenAPI natively                                                                                             | ✓ Good — but Allauth headless endpoints missing from spec; manual fetch workaround applied                                           |
| Docker-first deployment                                                        | Maximum flexibility across cloud providers; no vendor lock-in                                                                                                             | ✓ Good — multi-stage Dockerfiles ship in Phase 7                                                                                     |
| React Native Web for shared UI                                                 | Share component primitives across web and mobile in monorepo                                                                                                              | ✓ Good — packages/ui ships shared primitives consumed by both apps                                                                   |
| Tailwind CSS 3.4 (not 4)                                                       | Tailwind 4 preview crashes Next.js PostCSS pipeline                                                                                                                       | ⚠️ Revisit — upgrade to Tailwind 4 when stable release ships                                                                         |
| HS256 JWT (not RSA)                                                            | Avoids RSA key provisioning complexity in template scaffolding                                                                                                            | ✓ Good — appropriate for template; each product can upgrade                                                                          |
| PaymentAdapter ABC (not dj-stripe)                                             | dj-stripe adds ~40 migrations coupling to User model, forces provider lock-in                                                                                             | ✓ Good — domain-centric adapter with StripeAdapter as default; swappable in one setting                                              |
| Plain Django view for webhook                                                  | Raw body bytes required for Stripe HMAC; Ninja may buffer/parse body                                                                                                      | ✓ Good — reliable HMAC verification, HTTP 200 + Celery dispatch pattern works cleanly                                                |
| PlanProviderMapping table                                                      | No `stripe_price_id` on models; internal plan IDs stay provider-agnostic                                                                                                  | ✓ Good — price IDs seeded via migration 0002 for dev/test; no hardcoding in service code                                             |
| Async PDF via Celery + WeasyPrint                                              | Never block HTTP request cycle; WeasyPrint has fontconfig deadlock on fork                                                                                                | ✓ Good — lazy import inside task body prevents deadlock; 512KB MAX_PDF_BYTES guard added                                             |
| Billing in template (v1.1)                                                     | High-leverage addition; every SaaS product needs billing infrastructure                                                                                                   | ✓ Good — 36 requirements delivered, 40/40 verification truths passed, human-verified                                                 |
| PostHog over Sentry (v1.2)                                                     | Single SDK covers errors + analytics + feature flags + session replay; generous free tier; self-hostable; adapter pattern lets projects swap to Sentry if they outgrow it | ✓ Good — PostHogAdapter ships; SentryAdapter stub with migration guide included                                                      |
| ObservabilityAdapter ABC (v1.2)                                                | Same pattern as PaymentAdapter — PostHogAdapter default, NoOpAdapter for tests; swappable via one Django setting; avoids SDK lock-in across web/mobile/backend            | ✓ Good — NoOpAdapter is default (zero overhead when POSTHOG_API_KEY absent); all 7 touch points cleaned by `--without observability` |
| Plain Django views for health probes (v1.2)                                    | Health probes must work even if Ninja app is misconfigured; no auth/middleware overhead                                                                                   | ✓ Good — probes mounted before Ninja path to prevent URL shadowing; internal helpers mockable as module-level functions              |
| nplusone blinker signal (not plugin) (v1.2)                                    | nplusone 1.0.0 has no pytest plugin; synthetic `nplusone.ext.pytest` module registered in sys.modules for import compatibility                                            | ✓ Good — LazyListener only (not EagerListener) avoids false positives on correct eager loads                                         |
| Resend over SendGrid for email (v1.3)                                          | anymail dropped official SendGrid support June 2025; Resend is the community-recommended default                                                                          | ✓ Good — `ConsoleAdapter` auto-activates in dev when `RESEND_API_KEY` absent; zero-credential local setup                            |
| Apple Sign In native JWT endpoint (v1.3)                                       | Expo JWT audience (`aud` = Bundle ID) differs from allauth standard endpoint expectation (`aud` = Services ID) — standard social token flow cannot be reused              | ✓ Good — dedicated `POST /api/v1/auth/apple/` with JWKS cache-bust on key rotation; handles test isolation correctly                 |
| `RequireRole` returns `False` not exception (v1.3)                             | ninja_extra converts `False` to `HttpError 403`; `raise PermissionDenied` would return 500 in some middleware configs                                                     | ✓ Good — consistent 403 behavior for both unauthenticated and non-admin users                                                        |
| Entitlement cache key per-user (v1.3)                                          | `entitlements:{user.pk}` with 300s TTL; invalidated unconditionally on `customer.subscription.updated` (even when PlanProviderMapping has no entry)                       | ✓ Good — covers unmapped plan downgrades; targeted invalidation avoids cache stampede on global invalidation                         |
| `UserDeletionService` orchestrator (v1.3)                                      | `user.delete()` alone leaves orphaned Stripe customer + PostHog person (Article 17 violation); dedicated service cascades third-party deletion before ORM delete          | ✓ Good — tech debt: Celery task duplicates the 4-step cascade; consolidate in future milestone                                       |
| Custom `Organization` model (not `django-organizations`) (v1.4)                | Binary is_admin model incompatible with owner/admin/member roles; ships unused view layer                                                                                 | ✓ Good — custom OrgService/MembershipService with @classmethod pattern; clean separation of concerns                                 |
| Custom `APIKey` model (not `djangorestframework-api-key`) (v1.4)               | DRF-specific `BasePermission`; incompatible with Django Ninja Extra                                                                                                       | ✓ Good — `ApiKeyAuth` + `RequireScope` native Ninja auth; SHA-256 hash only, `hmac.compare_digest`                                   |
| `django-pghistory` for audit (not `django-pgaudit` / `django-auditlog`) (v1.4) | `django-pgaudit` → 404 on PyPI; `django-auditlog` uses signals (misses bulk ORM + raw SQL); pghistory uses DB triggers                                                    | ✓ Good — `@track()` on models; `AuditContextMiddleware` + pghistory context for actor/org attribution                                |
| `django-unfold` for admin theme (v1.4)                                         | Officially recommended by Django project April 2025; wraps standard admin with no model migrations                                                                        | ✓ Good — all domain ModelAdmins converted; sidebar configured; backward-compatible with future admin changes                         |
| B2B as opt-in `--with b2b` (not opt-out) (v1.4)                                | Enterprise feature not needed in every project; opt-in reduces default template surface area                                                                              | ✓ Good — `B2B_START`/`B2B_END` markers throughout; `removeB2BModule()` strips cleanly; `django-unfold` kept unconditional            |
| `_resolve_org_plan_id()` stub deferred (v1.4)                                  | Per-org `Subscription` model not yet linked to `OrgCustomer`; org-plan path structurally present but non-functional                                                       | ⚠️ Revisit — wire `Subscription → OrgCustomer` in next milestone that needs per-org billing to activate                              |

## Current State (v1.4)

- **Version shipped:** v1.4 (2026-03-14)
- **Stack:** Django Ninja Extra + Next.js 15 + Expo SDK 53 + Turborepo + pnpm + Stripe SDK v14 + Celery + WeasyPrint + structlog + OpenTelemetry + PostHog + django-redis + django-ratelimit + django-csp + schemathesis + django-anymail (Resend) + premailer + expo-apple-authentication + django-pghistory + django-unfold + django-hijack
- **CLI:** `create-foundation-app` — feature flags: `--without billing`, `--without ai`, `--without mobile`, `--without observability`, `--without email`, `--without social-auth`, `--with b2b` (opt-in)
- **Auth:** Email/password + Google OAuth + GitHub OAuth (web) + Apple Sign In (iOS) — all via Django Allauth headless; email-collision merge for Google/GitHub
- **B2B:** `Organization` + `Membership` + `OrgCustomer`; `IsOrgMember`/`IsOrgAdmin` Ninja permissions; outbound webhook registry with HMAC + Celery delivery; `APIKey` with scopes + rate limiting; pghistory audit log; django-unfold admin + django-hijack impersonation
- **GDPR:** `DELETE /api/v1/account/` cascades Stripe + PostHog + social; `GET /api/v1/account/export` returns full JSON; cookie consent banner gates PostHog
- **RBAC:** `@require_role("admin")` decorator + `AdminController`; `admin`/`member` groups seeded on first deploy
- **Entitlements:** `has_feature(user, key)` Redis-cached; `has_org_feature(user, org, key)` org-plan-aware (org-Subscription lookup stubbed)
- **Known tech debt:** `_resolve_org_plan_id()` returns None (org plan not yet linked); `IsOrgAdmin` on transfer-ownership should be `IsOwner`; API key revoke route uses UUID not prefix; no composite DB index on audit log cursor fields; 4 admin browser verification items pending; `UserDeletionService` + Celery task duplicate GDPR cascade; no `/settings` "Download my data" UI
- **Next milestone:** to be defined with `/gsd:new-milestone`

---

_Last updated: 2026-03-14 after v1.4 milestone_
