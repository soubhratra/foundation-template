## 1. Update stripe-billing spec

- [ ] 1.1 Append BillingService DI pattern, provider name derivation, and auto-Customer signal requirements to `openspec/specs/stripe-billing/spec.md`
- [ ] 1.2 Append webhook implementation requirements (plain Django view, get_or_create idempotency, get_adapter placement, cancel_at_period_end behavior) to `openspec/specs/stripe-billing/spec.md`
- [ ] 1.3 Append StubAdapter, PlanProviderMapping seeding, and subscribe/change endpoint separation requirements to `openspec/specs/stripe-billing/spec.md`
- [ ] 1.4 Append invoice PDF generation requirements (WeasyPrint + Celery, lazy import, MAX_PDF_BYTES, untyped response) to `openspec/specs/stripe-billing/spec.md`

## 2. Update billing-ui spec

- [ ] 2.1 Append billing.config.ts location, server actions as props, and AnyApiClient cast requirements to `openspec/specs/billing-ui/spec.md`
- [ ] 2.2 Append get_status() all-None sentinel, createCheckoutSessionAction origin, and no_subscription/subscribe action type requirements to `openspec/specs/billing-ui/spec.md`
- [ ] 2.3 Append free-tier isCurrent fallback, canonical price_id source, and reactivate no-payload requirements to `openspec/specs/billing-ui/spec.md`

## 3. Create billing-cli-scaffolder spec

- [ ] 3.1 Create `openspec/specs/billing-cli-scaffolder/spec.md` with all four requirements (block markers, --without billing flag, fs-extra Node v24 fix, CLI invocation pattern)
