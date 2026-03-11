---
phase: 09-billing-scaffold
plan: 02
subsystem: payments
tags: [stripe, django, billing, adapter-pattern, abc, signals, migrations]

# Dependency graph
requires:
  - phase: 09-01
    provides: billing test package, shared fixtures (conftest.py), pytest infrastructure for billing tests

provides:
  - PaymentAdapter ABC with 7 provider-agnostic abstract methods
  - StripeAdapter concrete implementation using stripe.StripeClient v14 pattern
  - All 5 billing Django models (Customer, Subscription, Payment, ProcessedWebhookEvent, PlanProviderMapping)
  - SubscriptionStatus TextChoices enum with all 7 Stripe-matching status values
  - Initial migration 0001_initial.py creating all 5 tables in one operation
  - post_save signal auto-creating Customer when User is created
  - BillingConfig AppConfig with ready() signal registration
  - Admin registrations for all 5 models

affects: [09-03, 10-billing-service, 11-billing-api, 12-invoice-pdf]

# Tech tracking
tech-stack:
  added: [stripe>=14.4 (declared as billing extras dep), Django signals]
  patterns:
    - ABC-based adapter pattern (not Protocol) for payment provider abstraction
    - StripeClient instantiated per-instance (not global api_key assignment)
    - Lazy signal import in AppConfig.ready() via `from . import signals`
    - Provider-agnostic method signatures on abstract layer (no provider names in ABC)

key-files:
  created:
    - apps/api/apps/billing/__init__.py
    - apps/api/apps/billing/apps.py
    - apps/api/apps/billing/admin.py
    - apps/api/apps/billing/models.py
    - apps/api/apps/billing/signals.py
    - apps/api/apps/billing/adapters.py
    - apps/api/apps/billing/migrations/__init__.py
    - apps/api/apps/billing/migrations/0001_initial.py
  modified: []

key-decisions:
  - "PaymentAdapter uses ABC not Protocol — explicit inheritance raises TypeError immediately on missing methods"
  - "Abstract record_usage parameter renamed from stripe_customer_id to customer_id — enforces zero provider coupling in interface"
  - "StripeAdapter uses stripe.StripeClient(api_key=...) in __init__ — SDK v14 pattern, no global api_key mutation"
  - "All 5 models in single 0001_initial.py — avoids second migration in Phase 10 for ProcessedWebhookEvent"
  - "signals.py created during Task 2 (before Task 3) — required for Django setup to run makemigrations"

patterns-established:
  - "Adapter ABC: all abstract methods use domain-centric types (str, dict, list[dict]) — no provider-specific types"
  - "Signal registration: AppConfig.ready() imports signals module via 'from . import signals' (noqa F401)"
  - "Signal guard: 'if created:' in post_save handler is load-bearing — prevents duplicate Customer on User re-save"
  - "Migration: BigAutoField for all PKs, unique_together on ProcessedWebhookEvent and PlanProviderMapping"

requirements-completed: [ADPTR-01, ADPTR-02, CUST-01, CUST-02, SUB-06, PAY-02, ADPTR-05]

# Metrics
duration: 18min
completed: 2026-03-07
---

# Phase 9 Plan 02: Billing Module Core — Models, Adapter ABC, and Signal Summary

**Provider-agnostic PaymentAdapter ABC and StripeAdapter implementation, 5 Django billing models with initial migration, post_save signal for User-Customer auto-creation, and admin registrations — all in apps/api/apps/billing/**

## Performance

- **Duration:** ~18 min
- **Started:** 2026-03-07T22:04:00Z
- **Completed:** 2026-03-07T22:22:00Z
- **Tasks:** 3
- **Files modified:** 8

## Accomplishments

- PaymentAdapter ABC with 7 domain-centric abstract methods — zero provider names in interface, TypeError on direct instantiation
- StripeAdapter concrete implementation using stripe.StripeClient v14 per-instance pattern (not global api_key)
- All 5 billing models with SubscriptionStatus TextChoices (7 values matching Stripe exactly), constraints, and indexes in one migration

## Task Commits

Each task was committed atomically:

1. **Task 1: Create billing module skeleton and AppConfig** - `753fae7` (feat)
2. **Task 2: Create models and initial migration** - `59183cb` (feat)
3. **Task 3: Create PaymentAdapter ABC, StripeAdapter, and post_save signal** - `e57216a` (feat)

## Files Created/Modified

- `apps/api/apps/billing/__init__.py` - Empty module init
- `apps/api/apps/billing/apps.py` - BillingConfig with ready() registering signals
- `apps/api/apps/billing/admin.py` - Admin for all 5 models (CustomerAdmin, SubscriptionAdmin, PaymentAdmin, ProcessedWebhookEventAdmin, PlanProviderMappingAdmin)
- `apps/api/apps/billing/models.py` - All 5 billing models + SubscriptionStatus(7 values)
- `apps/api/apps/billing/migrations/__init__.py` - Empty migrations init
- `apps/api/apps/billing/migrations/0001_initial.py` - Single migration creating all 5 tables
- `apps/api/apps/billing/adapters.py` - PaymentAdapter ABC + StripeAdapter (7 methods each)
- `apps/api/apps/billing/signals.py` - post_save User -> Customer with `if created:` guard

## Decisions Made

- The abstract `record_usage` method originally had `stripe_customer_id` as a parameter name (copied directly from plan spec). This was renamed to `customer_id` to comply with the must_have constraint: "The word 'stripe' does not appear in any PaymentAdapter abstract method name, signature, or return annotation". The StripeAdapter implementation still passes `customer_id` to the Stripe-specific `stripe_customer_id` payload key internally.

- signals.py was created during Task 2 (models) rather than Task 3 as planned — Django's `app_config.ready()` runs during `django.setup()`, which is triggered by `manage.py makemigrations`. The import `from . import signals` in BillingConfig.ready() caused an ImportError without it. This is a benign ordering deviation; the final state is identical.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Renamed abstract `record_usage` parameter `stripe_customer_id` → `customer_id`**

- **Found during:** Task 3 (adapter verification)
- **Issue:** Plan spec had `stripe_customer_id` as the parameter name in the abstract method. The must_have constraint explicitly prohibits the word "stripe" in any abstract method signature. Verification script caught this: `AssertionError: stripe in record_usage signature!`
- **Fix:** Renamed abstract parameter to `customer_id`; StripeAdapter implementation updated to pass `customer_id` as the value to the `stripe_customer_id` Stripe API payload key
- **Files modified:** apps/api/apps/billing/adapters.py
- **Verification:** Re-ran verification loop — all abstract method signatures now free of "stripe"
- **Committed in:** e57216a (Task 3 commit)

**2. [Rule 3 - Blocking] Created signals.py before migration generation (Task 2, not Task 3)**

- **Found during:** Task 2 (makemigrations)
- **Issue:** `manage.py makemigrations` triggered `django.setup()` → `BillingConfig.ready()` → `from . import signals` → ImportError (signals.py didn't exist yet)
- **Fix:** Created signals.py with the complete final implementation before running makemigrations
- **Files modified:** apps/api/apps/billing/signals.py (created early)
- **Verification:** makemigrations completed successfully; signal verified importable
- **Committed in:** e57216a (committed as part of Task 3 commit)

---

**Total deviations:** 2 auto-fixed (1 bug fix in abstract spec, 1 blocking ordering issue)
**Impact on plan:** Both auto-fixes necessary for correctness. No scope creep. Final deliverables match plan exactly.

## Issues Encountered

- ruff E501 line-too-long errors in the auto-generated migration file (Django generates unformatted code). Pre-commit hook ran `ruff format` on staged files but could not auto-fix E501 without manual line breaks. Resolved by staging the formatted output and re-committing.

## User Setup Required

None - no external service configuration required for this plan. STRIPE_SECRET_KEY is referenced in StripeAdapter but not yet added to settings (handled in Plan 09-03).

## Next Phase Readiness

- Plan 09-03 can now: add `"apps.billing"` to INSTALLED*APPS, add BILLING*\* settings, run migrations, wire up BILLING_ADAPTER import_string resolution
- StripeAdapter is ready to use but requires `STRIPE_SECRET_KEY` in settings before instantiation
- All models are migration-ready and will create tables on `manage.py migrate`

---

_Phase: 09-billing-scaffold_
_Completed: 2026-03-07_
