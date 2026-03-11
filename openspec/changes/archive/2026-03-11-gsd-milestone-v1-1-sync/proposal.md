## Why

Milestone v1.1 (Billing & Payments Module) is complete. During execution across Phases 9–12, 31 implementation decisions were made that deviate from or extend beyond the original design proposal (`2026-03-07-payment-and-billing`). These decisions live only in `.planning/STATE.md` and are not reflected in the live OpenSpec specs — meaning any new product scaffolded from this template would lack the rationale and patterns established during implementation.

## What Changes

- Add implementation patterns and decisions to `stripe-billing/spec.md` (15 decisions from Phases 10–12)
- Add implementation patterns and decisions to `billing-ui/spec.md` (9 decisions from Phase 11)
- Create new `billing-cli-scaffolder/spec.md` documenting how billing is removed via the CLI scaffolder (4 decisions from Phase 12)

## Capabilities

### New Capabilities

- `billing-cli-scaffolder`: How the `removeBillingModule()` function works in `create-foundation-app` — block regex pattern, `--without billing` flag, Node.js v24 ESM compatibility fix, and CLI invocation patterns for testing.

### Modified Capabilities

- `stripe-billing`: Add implementation decisions for BillingService DI pattern, provider name derivation, auto-Customer signal, plain Django view for webhook (not Ninja), `get_or_create` idempotency guard, `get_adapter()` placement, `cancel_at_period_end` gate behavior, ruff B904 compliance, StubAdapter module configuration, PlanProviderMapping seeding, subscribe vs. change endpoint separation, invoice PDF generation (WeasyPrint + Celery), lazy WeasyPrint import, MAX_PDF_BYTES guard, and `get_pdf_status` untyped response rationale.
- `billing-ui`: Add implementation decisions for `billing.config.ts` location and import path, server actions as props pattern, `AnyApiClient` cast, `get_status()` all-None sentinel, `createCheckoutSessionAction` origin derivation, `subscribe` vs. `upgrade` action types, free-tier `isCurrent` fallback, migration 0002 as canonical price_id source, and `reactivate_subscription` no-payload rationale.

## Impact

- `openspec/specs/stripe-billing/spec.md` — updated with 15 implementation decisions
- `openspec/specs/billing-ui/spec.md` — updated with 9 implementation decisions
- `openspec/specs/billing-cli-scaffolder/spec.md` — new file (4 decisions)
- No code changes — spec-only sync
