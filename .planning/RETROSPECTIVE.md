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

## Cross-Milestone Trends

| Milestone | Phases | Plans | Verifications | Days | Scope Accuracy                        |
| --------- | ------ | ----- | ------------- | ---- | ------------------------------------- |
| v1.0      | 8      | 36    | n/a           | 13   | Good                                  |
| v1.1      | 4      | 17    | 40/40         | 4    | Phase 11 grew 5→8 plans               |
| v1.2      | 6      | 19    | 66/66         | 1    | Clean scope; 2 post-audit quick fixes |
