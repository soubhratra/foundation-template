# Project Retrospective: Foundation Template

Living document — updated after each milestone.

---

## Milestone: v1.1 — Billing & Payments Module

**Shipped:** 2026-03-11
**Phases:** 4 (9–12) | **Plans:** 17 | **Verifications:** 40/40 truths

### What Was Built

- Provider-agnostic `PaymentAdapter` ABC with `StripeAdapter` v14 — billing backend swappable with one Django setting
- Full subscription lifecycle (create via Stripe Checkout, upgrade/downgrade with proration, cancel at period end, reactivate) via `BillingService` testable with `StubAdapter`
- Async webhook infrastructure: HMAC verification → Celery dispatch → idempotent `ProcessedWebhookEvent` → 6 Tier-1 event handlers
- Next.js `/billing` page: plan display, payment history, upgrade/downgrade modals, cancel flow, past-due banner
- Async invoice PDF generation: WeasyPrint + Jinja2, Celery task with lazy imports (fontconfig deadlock prevention), 512KB guard
- CLI scaffolder integration: billing included by default, `--without billing` removes all billing files cleanly, SCAFF-04 pytest verifies `manage.py check` passes

### What Worked

- **TDD discipline throughout**: Writing failing tests first (Phases 9–12) made refactoring safe and gave clear done criteria for each plan
- **StubAdapter pattern**: Testing BillingService without real Stripe HTTP calls dramatically sped up unit test iteration; stub promoted to proper module in development.py was a good call
- **Plain Django view for webhook**: Resisting the urge to use Ninja for the webhook endpoint (to preserve raw body bytes for HMAC) prevented a subtle correctness bug
- **Phase-by-phase dependency locking**: Phase 9 locked the adapter interface before any service code was written; this prevented leaking Stripe-specific types into BillingService
- **Phased verification**: Running automated verifications (40 truths) before human smoke test caught issues early and made the human UAT fast

### What Was Inefficient

- **Phase 11 over-scoped**: Phase 11 grew to 8 plans (originally spec'd as 5); the additional 3 plans were needed to fix test failures and complete controller implementation — better upfront scope sizing would have avoided mid-phase expansion
- **AnyApiClient cast**: The `any`-typed cast in `billing-actions.ts` for POST mutations was a workaround for stale `@repo/api-client` types; should have regenerated types earlier in the phase
- **fs-extra Node.js v24 ESM bug**: The named-export incompatibility only surfaced during SCAFF-04 pytest test (subprocess CLI invocation) — would have been caught earlier with a Node.js version matrix in CI

### Patterns Established

- **BILLING MODULE comment blocks**: Dash-delimited `# --- BILLING_START ---` / `# --- BILLING_END ---` markers in settings files enable reliable regex-based removal — extend this pattern to other optional modules
- **Lazy WeasyPrint import**: Import WeasyPrint inside the task/function body (not module level) to prevent fontconfig deadlock on Celery fork (WeasyPrint issue #684)
- **Data migration for provider mappings**: Seeding `PlanProviderMapping` rows via migration 0002 makes them the canonical source of truth for price IDs in tests — avoids fixture drift
- **fs-extra import style**: Use `import fse from 'fs-extra'; const { readFile } = fse;` (not named imports) for Node.js v24 ESM/CJS compatibility in CLI TypeScript source

### Key Lessons

- **Module isolation markers upfront**: Define `# --- BILLING_START ---` comment block markers at the start of the module build, not retroactively — the CLI scaffolder depends on them
- **Webhook needs raw body**: If an endpoint needs raw request bytes (HMAC, Stripe, etc.), use a plain Django view — don't use Ninja/DRF which may buffer/parse the body
- **Stub adapter in development.py**: Wiring `StubAdapter` in `development.py` as the default adapter for non-production environments eliminates per-test monkeypatching and makes controller tests simpler

### Cost Observations

- Sessions: ~12 subagent execution sessions across 4 phases
- Notable: Phase 11 ran 8 plans vs planned 5 — over-scoped phase is the primary cost driver; keep plans to ≤3 tasks strictly

---

## Milestone: v1.2 — Observability & DevEx Hardening

**Shipped:** 2026-03-12
**Phases:** 6 (13–18) | **Plans:** 19 | **Verifications:** 66/66 truths | **Timeline:** 1 day

### What Was Built

- structlog JSON logging pipeline — `request_id`, `user_id`, `duration_ms` auto-injected on every Django request; OTel auto-instrumentation across Django + Celery + PostgreSQL + Redis; Jaeger in Docker Compose
- `ObservabilityAdapter` ABC (PostHogAdapter default, NoOpAdapter for CI/test) across Django (middleware + Celery signal), Next.js, and Expo — swappable via one Django setting; `--without observability` removes all 7 touch points cleanly
- `/api/health/live|ready|startup` plain Django health probes; Celery Beat with `DatabaseScheduler` + example periodic task; Flower dev-only in Docker Compose
- Redis-backed rate limiting + CSP/HSTS/X-Frame-Options security headers on both Django and Next.js
- Secret scanning + Python SAST + dependency auditing as pre-commit + CI gates
- `nplusone` N+1 autouse pytest fixture; `schemathesis` API contract fuzzing CI job; `commitlint` hook; ruff McCabe complexity gate

### What Worked

- **Adapter pattern consistency**: The `ObservabilityAdapter` ABC follows the same `PaymentAdapter` pattern established in v1.1 — the pattern is now proven and generalizable to any optional module
- **Post-audit quick fixes**: The milestone audit caught 2 HIGH-priority integration breaks (stale test URL, Docker Compose Redis env vars) that individual phase verifications missed — the cross-phase audit step is essential and proved its value
- **TDD throughout**: All 6 phases used Wave 0 RED stubs (pytest.fail() with reason strings) giving clear done criteria per plan; 66/66 truths across all verifications
- **Plain Django for health probes**: Resisting the urge to use Ninja for health probes (same reasoning as webhook in v1.1) — probes work even if Ninja app is misconfigured

### What Was Inefficient

- **nplusone plugin absence**: nplusone 1.0.0 dropped its pytest plugin — discovered mid-implementation, requiring a custom `sys.modules` shim and blinker signal teardown; this would have been caught by upfront research
- **Post-audit gap closure**: The 2 HIGH-priority gaps (BREAK-1, BREAK-2) should have been caught during phase execution; they slipped through because phase verifications test in isolation, not in the composed runtime environment
- **SUMMARY frontmatter gaps**: 3 phases (13, 14-04, 18-03) had empty `requirements-completed` frontmatter — minor doc debt that required manual note in the audit; enforce this as a post-phase checklist item

### Patterns Established

- **Lazy OTel exporter import**: Lazy import of `OTLPSpanExporter` inside `configure_otel()` avoids ~100ms import overhead in CI/dev without Jaeger — apply to all optional infra deps
- **NoOpAdapter default**: Optional adapters (Observability, Payment) default to NoOp — never fail when optional config is absent; CI and local dev without API keys produce zero errors
- **OBSERVABILITY_MODULE comment delimiters**: Same `# OBSERVABILITY MODULE` / `# END OBSERVABILITY MODULE` marker pattern as `# BILLING MODULE` blocks — enables reliable regex removal in CLI scaffolder
- **DatabaseScheduler for Celery Beat**: Prefer `DatabaseScheduler` over `PersistentScheduler` — allows runtime schedule edits via Django admin without container restarts
- **pytest.fail() for RED stubs**: Using `pytest.fail("RED: [reason]")` over `assert False` in stub tests — produces cleaner FAILED output that identifies which plan implements each behavior

### Key Lessons

- **Cross-phase integration testing is non-negotiable**: Individual phase verifications test components in isolation; the audit step tests the composed system — never skip it before milestone completion
- **nplusone LazyListener only**: Activate `LazyListener` (not `EagerListener`) to avoid false positives on correct eager loads (`select_related` in billing tests); explicitly disconnect blinker signal in `__exit__` or handlers fire in subsequent tests
- **Health probes before Ninja path**: Mount health probe URL patterns before `path("api/", ninja_api.urls)` in `urls.py` — Ninja wildcard will shadow them if registered after
- **Cap schemathesis examples for CI cost**: `--hypothesis-max-examples 30` is sufficient for CI; full 100-example runs cost 3× more with marginal additional coverage for contract testing

### Cost Observations

- Sessions: ~20 subagent execution sessions across 6 phases
- Notable: All 6 phases completed in a single day — high velocity enabled by clear TDD stubs and stable adapter pattern from v1.1; post-audit gap closure added 1 quick task session

---

## Milestone: v1.3 — SaaS Functional Baseline

**Shipped:** 2026-03-13
**Phases:** 7 (19–25) | **Plans:** 23 | **Verifications:** 109/109 truths | **Timeline:** 1 day

### What Was Built

- `EmailAdapter` ABC with `ResendAdapter` default — Celery-queued via `transaction.on_commit()`, CSS inlined via `premailer`, `ConsoleAdapter` auto-activated in dev; `--without email` flag
- Google + GitHub OAuth on web (allauth headless) + Apple Sign In on iOS (native JWT endpoint with JWKS verification); email-collision auto-merge; `SocialAccountAdapter` for Apple relay exclusion
- GDPR baseline: `UserDeletionService` async cascade (Stripe + PostHog + social, HTTP 202); `AccountExportService` JSON export with accurate `plan_id`; `CookieConsentBanner` consent-gating PostHog
- `RequireRole` permission class + `@require_role("admin")` decorator; `AdminController` (4 endpoints); `admin`/`member` groups seeded via data migration `0003_seed_roles`
- `has_feature(user, key)` against `BILLING_PLANS` settings dict; Redis-cached (300s TTL); auto-invalidated on subscription webhook; returns `True` when billing absent
- Gap closure: OAuth callback/error pages at `/auth/callback` + `/auth/error` (INT-01, INT-02); GDPR export `plan_id` fix (INT-03)

### What Worked

- **Post-audit gap closure pattern**: Phases 24 and 25 were added as gap-closure phases after the v1.2 audit pattern — they're small (2/1 plan) and highly targeted, closing INT-01/02/03 cleanly
- **`ConsoleAdapter` for zero-credential dev**: Auto-activating `ConsoleAdapter` when `RESEND_API_KEY` is absent means local email testing just works without any credentials
- **Apple Sign In JWT endpoint**: Discovering the `aud` mismatch (Bundle ID vs Services ID) during research and designing a dedicated endpoint prevents a runtime auth failure

### What Was Inefficient

- **GDPR cascade duplication**: `UserDeletionService` and the Celery task both implement the 4-step cascade; any future change requires updating both places — should consolidate
- **No frontend data export UI**: The `GET /api/v1/account/export` endpoint works but has no `/settings` "Download my data" button; ships as backend-only

### Patterns Established

- **`on_commit()` for email dispatch**: All `send_email_task.delay()` calls go inside `transaction.on_commit()` — prevents orphaned email tasks if DB transaction rolls back
- **Gap-closure phases as small decimal-free phases**: Small gap-closure phases (1–2 plans) appended after main milestone phases are better than inserting decimal phases mid-sequence

### Key Lessons

- **Confirm Apple JWT audience before building**: Apple Sign In Expo `aud` is Bundle ID (not Services ID) — design dedicated endpoint from day one, don't adapt standard social token flow
- **Data migration for seeding roles**: Using Django data migrations to seed `admin`/`member` groups eliminates fixture drift and works in both dev and production deployment

### Cost Observations

- Sessions: ~25 subagent execution sessions across 7 phases
- Notable: All 7 phases completed in a single day — GDPR cascade took the most iteration due to signal complexity and test isolation; Apple Sign In required careful JWKS cache handling

---

## Milestone: v1.4 — B2B Module

**Shipped:** 2026-03-14
**Phases:** 9 (26–34) | **Plans:** 29 | **Verifications:** 236/236 truths | **Timeline:** 2 days

### What Was Built

- `Organization` model with membership/roles (owner/admin/member), 72h invitation flow, ownership transfer, `IsOrgMember`/`IsOrgAdmin` Ninja permissions, cross-org 403 enforcement
- `OrgCustomer` for per-org Stripe billing; `has_org_feature(user, org, key)` with org-member cache invalidation on subscription update
- Outbound webhook registry — HMAC-SHA256 signed Celery delivery (7-retry exponential backoff); circuit breaker auto-disable + email notification; `fire_webhook_event()` wired to 3 event sites; delivery history + manual retry API
- `APIKey` scoped keys (SHA-256 hash, raw key shown once); `ApiKeyAuth` + `RequireScope` Ninja auth; `ApiKeyRateLimitMiddleware` with `X-RateLimit-*` headers; `last_used_at`/`usage_count` tracking
- `django-pghistory` `@track()` triggers on 4 B2B models; `AuditContextMiddleware`; org-scoped cursor-paginated audit log API; impersonation entries present but `impersonator` excluded from org queries
- `django-unfold` theme across all domain ModelAdmins; `django-hijack` impersonation with persistent banner + `ImpersonationEvent` audit entries; `OrgCustomerAdmin` in sidebar
- `--with b2b` opt-in scaffolder flag; `B2B_START`/`B2B_END` markers throughout; `removeB2BModule()` clean removal verified by pytest CI test
- 3 gap-closure phases (32, 33, 34) added post-audit to wire `fire_webhook_event()` to callers, add demonstrator endpoint activating full API key auth chain, and fix missing audit context for APIKey events

### What Worked

- **Milestone audit as gap-detector**: The v1.4 audit (first pass with `gaps_found`) caught HOOK-04 (missing `.html` extension) as a critical blocker — fixed via quick task before re-audit; audit value clearly proven
- **`@track()` decorator on models**: pghistory trigger-based approach works without any manual logging call — auto-captures bulk ORM + raw SQL that signal-based auditlog misses
- **`AuditContextMiddleware` + service-layer audit_context()**: Two-level attribution — middleware for HTTP requests, `audit_context()` context manager for Celery tasks — clean separation of sync vs async actor attribution
- **Static route before parametric**: Declaring `ping` before `/{key_id}/` in `APIKeyController` prevents route shadowing — simple ordering rule that prevents subtle 404 bugs
- **Gap-closure sprint phases**: Phases 32, 33, 34 (small, 2 plans each) are more precise than trying to include wiring in earlier phases; they start from RED stubs and close specific integration gaps

### What Was Inefficient

- **`_resolve_org_plan_id()` shipped as stub**: The org-plan lookup function was deferred during Phase 26 — structurally present but always returns None; per-org billing is not functional until a Subscription is linked to OrgCustomer
- **ORG-04 permission scope**: Used `IsOrgAdmin` on `transfer-ownership` instead of `IsOwner` — admin can transfer without owner consent; should have been `IsOwner` from the start; deferred as tech debt
- **API key revoke route UUID vs prefix divergence**: Revoke endpoint uses `{key_id}` (UUID) instead of `{prefix}` per spec — discovered post-implementation; spec and code diverge; needs alignment
- **Phase 34 VALIDATION.md in draft**: Gap-closure sprint was not formally validated (VALIDATION.md never promoted from draft); all 64 tests pass but formality missing; run `/gsd:validate-phase 34`

### Patterns Established

- **`B2B_START`/`B2B_END` opt-in marker convention**: B2B markers (not opt-out) signal that the feature is additive; scaffolder strips blocks atomically; `django-unfold` kept unconditional (admin theme is not B2B-only)
- **`AppConfig.ready()` with try/except ImportError for optional deps**: `AuditConfig.ready()` wraps hijack import — allows non-B2B scaffolds to remove hijack without breaking audit app startup
- **Module-level fire_webhook_event inside B2B block**: Placing the import inside B2B markers ensures scaffolder strips both the import and the caller in one atomic block

### Key Lessons

- **Confirm PyPI package existence before designing**: `django-pgaudit` → 404; `django-auditlog` uses signals (misses bulk/raw SQL); pghistory triggers are the right choice but validate before spec-writing
- **Opt-in vs opt-out for B2B**: B2B marked as `--with b2b` (not `--without b2b`) correctly signals that it's an enterprise add-on, not a baseline feature; sets the right default expectation for new products
- **Ninja @paginate incompatibility with controller methods**: The `@paginate` decorator from ninja_extra doesn't work with controller class methods — use manual pagination (page/page_size query params + dict response)
- **Static routes before parametric in same controller**: Always declare static path segments (`/ping`) before parametric ones (`/{id}/`) within the same Ninja controller; Django/Ninja routing is first-match

### Cost Observations

- Sessions: ~35 subagent execution sessions across 9 phases + 2 quick tasks + 1 re-audit
- Notable: Phase 29 (pghistory) was the most complex — 848 test count reflects pghistory's cross-model `across()` union queries; gap-closure phases added ~3 sessions after audit

---

## Cross-Milestone Trends

| Milestone | Phases | Plans | Verifications | Days | Scope Accuracy                                                         |
| --------- | ------ | ----- | ------------- | ---- | ---------------------------------------------------------------------- |
| v1.0      | 8      | 36    | n/a           | 13   | Good                                                                   |
| v1.1      | 4      | 17    | 40/40         | 4    | Phase 11 grew 5→8 plans                                                |
| v1.2      | 6      | 19    | 66/66         | 1    | Clean scope; 2 post-audit quick fixes                                  |
| v1.3      | 7      | 23    | 109/109       | 1    | Clean scope; 2 gap-closure phases                                      |
| v1.4      | 9      | 29    | 236/236       | 2    | 3 gap-closure phases; 13 tech debt items; 1 re-audit after HOOK-04 fix |
