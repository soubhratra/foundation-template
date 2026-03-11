---
phase: 09-billing-scaffold
plan: "03"
subsystem: payments
tags: [stripe, django, billing, settings, migrations]

# Dependency graph
requires:
  - phase: 09-02
    provides: billing models, adapters, migrations, and test stubs created in Wave 1
provides:
  - apps.billing wired into INSTALLED_APPS — billing module is now a running Django app
  - BILLING_ADAPTER, BILLING_PLANS, and STRIPE_* settings in base.py
  - billing migration applied — all 5 models live in the database
  - stripe>=14.4,<15 installed via [dependency-groups] billing in pyproject.toml
  - BILLING_START/END scaffolder markers in config/urls.py for Phase 10
  - Stripe env vars documented in .env.example under BILLING MODULE delimiters
affects: [10-billing-webhook, 11-billing-subscription, 12-billing-invoices]

# Tech tracking
tech-stack:
  added:
    - stripe 14.4.1 (Stripe Python SDK v14, new StripeClient API)
  patterns:
    - BILLING MODULE / END BILLING MODULE comment delimiters for CLI scaffolder isolation
    - BILLING_START / BILLING_END markers in urlpatterns for future Phase 10 webhook URL
    - Stripe env vars default to empty string (safe for dev without real keys)

key-files:
  created: []
  modified:
    - apps/api/config/settings/base.py
    - apps/api/config/urls.py
    - apps/api/pyproject.toml
    - apps/api/.env.example
    - apps/api/uv.lock

key-decisions:
  - "STRIPE_SECRET_KEY defaults to empty string — StripeAdapter instantiation test skips when no real key provided, consistent with dev-safe defaults across all env vars"
  - "billing dependency group added to existing [dependency-groups] TOML table (not a new section) — TOML allows only one section per key"
  - "Pre-existing allauth deprecation warnings are W-level, not errors — manage.py check exits 0, out of scope for this plan"

patterns-established:
  - "BILLING MODULE / END BILLING MODULE comment delimiters wrap all billing-related settings for CLI scaffolder stripping"
  - "BILLING_START / BILLING_END markers in urlpatterns reserve space for Phase 10 webhook URL without registering any URL"

requirements-completed: [ADPTR-03, ADPTR-04, ADPTR-05]

# Metrics
duration: 4min
completed: 2026-03-07
---

# Phase 9 Plan 03: Billing Scaffold Wire-up Summary

**billing module wired into Django project with Stripe settings, migration applied, 22 of 23 tests passing (1 skip requires real STRIPE_SECRET_KEY)**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-07T22:11:02Z
- **Completed:** 2026-03-07T22:15:11Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments

- `apps.billing` added to INSTALLED_APPS with scaffolder comment marker — billing module is now active in Django
- BILLING*ADAPTER, BILLING_PLANS (free/pro/enterprise), and all STRIPE*\* env vars added to base.py under BILLING MODULE delimiters
- billing.0001_initial migration applied — Customer, Subscription, Payment, Invoice, ProcessedWebhookEvent tables exist in Postgres
- stripe 14.4.1 installed via `uv sync --group billing` — StripeAdapter can call Stripe v14 SDK
- BILLING_START/BILLING_END scaffolder markers added to config/urls.py for Phase 10 webhook registration

## Task Commits

Each task was committed atomically:

1. **Task 1: Wire billing settings into base.py** - `08b1e0c` (feat)
2. **Task 2: Wire urls.py markers, pyproject.toml dep group, .env.example docs** - `e0368ea` (feat)
3. **Task 3: Install stripe, apply migration, verify test suite** - `87fea14` (chore — uv.lock update)

**Plan metadata:** (final docs commit — see below)

## Files Created/Modified

- `apps/api/config/settings/base.py` — Added `apps.billing` to INSTALLED*APPS, STRIPE*\* env vars, BILLING_ADAPTER, BILLING_PLANS dict with free/pro/enterprise tiers
- `apps/api/config/urls.py` — Added BILLING_START/BILLING_END comment markers inside urlpatterns
- `apps/api/pyproject.toml` — Added `billing = ["stripe>=14.4,<15"]` to [dependency-groups]
- `apps/api/.env.example` — Documented all STRIPE*\* and BILLING*\* price ID vars under # BILLING MODULE delimiters
- `apps/api/uv.lock` — Updated with stripe 14.4.1 and transitive dependencies

## Decisions Made

- **STRIPE_SECRET_KEY defaults to `""`:** The `test_stripe_adapter_instantiates` test guards on `STRIPE_SECRET_KEY` being non-empty and skips when empty. This is correct — the test requires a real Stripe key to actually construct a `StripeClient`. Dev environments should not require a Stripe key. 22 of 23 tests pass; 1 skips legitimately.
- **Pre-existing allauth deprecation warnings:** Three W-level warnings from `ACCOUNT_AUTHENTICATION_METHOD`, `ACCOUNT_EMAIL_REQUIRED`, `ACCOUNT_USERNAME_REQUIRED` exist in the base settings. These pre-date this plan and `manage.py check` exits 0 — they are not errors and out of scope for this plan.

## Deviations from Plan

**1. [Rule 3 - Blocking] Docker daemon not running — started Docker Desktop to run migrations**

- **Found during:** Task 3 (Apply migration and run full test suite verification)
- **Issue:** `manage.py migrate billing` failed with PostgreSQL connection refused — Docker daemon was not running
- **Fix:** Started Docker Desktop, ran `docker compose up -d db`, waited for pg_isready, then ran migration
- **Files modified:** None (infrastructure action only)
- **Verification:** Migration applied: `Applying billing.0001_initial... OK`
- **Committed in:** N/A (infrastructure, no code change)

**2. [Rule 3 - Blocking] Test path mismatch — plan specified apps/tests/billing/, actual path is tests/billing/**

- **Found during:** Task 3 (Run full billing test suite)
- **Issue:** `uv run pytest apps/tests/billing/` returned exit 4 (path not found). Tests are at `apps/api/tests/billing/`, which maps to `tests/billing/` when running from `apps/api/`
- **Fix:** Used correct path `uv run pytest tests/billing/ -v` — all 22 tests passed
- **Files modified:** None (test invocation path only)
- **Verification:** 22 passed, 1 skipped (intentional — requires real STRIPE_SECRET_KEY), exit 0

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Both deviations were environment/path issues, not code issues. No scope changes.

## Issues Encountered

- Pre-existing allauth deprecation warnings in base.py settings (`ACCOUNT_AUTHENTICATION_METHOD`, `ACCOUNT_EMAIL_REQUIRED`, `ACCOUNT_USERNAME_REQUIRED`) appear in `manage.py check` output but are W-level — exit code 0. These exist before this plan and are deferred to a future settings cleanup.

## User Setup Required

**To use the billing module with real Stripe credentials**, copy `.env.example` values to `.env` and replace placeholder values:

```bash
# In apps/api/.env
STRIPE_SECRET_KEY=sk_test_YOUR_ACTUAL_KEY
STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_ACTUAL_KEY
STRIPE_WEBHOOK_SECRET=whsec_YOUR_ACTUAL_SECRET
STRIPE_PRICE_PRO_MONTHLY=price_YOUR_PRO_MONTHLY_ID
# ... etc
```

Without real keys, the billing module runs normally but `test_stripe_adapter_instantiates` will skip and no actual Stripe API calls can be made.

## Next Phase Readiness

- Phase 10 (webhook handler) can proceed — `apps.billing` is installed, migrations are applied, BILLING_START/END markers exist in urls.py for the webhook URL registration
- Phase 11 (subscription management) can proceed — Subscription, Customer models exist in DB
- Phase 12 (invoicing) can proceed — Invoice model exists in DB

## Self-Check: PASSED

All key files exist and all task commits are present in git log.

---

_Phase: 09-billing-scaffold_
_Completed: 2026-03-07_
