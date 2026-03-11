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

## Cross-Milestone Trends

| Milestone | Phases | Plans | Verifications | Days | Scope Accuracy          |
| --------- | ------ | ----- | ------------- | ---- | ----------------------- |
| v1.0      | 8      | 36    | n/a           | 13   | Good                    |
| v1.1      | 4      | 17    | 40/40         | 4    | Phase 11 grew 5→8 plans |
