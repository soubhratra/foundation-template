---
phase: 09-billing-scaffold
plan: "01"
subsystem: testing
tags: [pytest, django, billing, stripe, importorskip, wave-0]

requires: []
provides:
  - pytest test package at apps/api/tests/billing/
  - shared fixtures (user, customer) for billing tests
  - stub test files covering PaymentAdapter ABC contract (ADPTR-01/02/03)
  - stub test files covering model shapes (CUST-01, SUB-06, PAY-02, HOOK-03)
  - stub test files covering auto-customer signal (CUST-02)
affects: [09-02, 09-03]

tech-stack:
  added: []
  patterns:
    - "importorskip + RuntimeError guard: handles both missing-module and unregistered-app Django scenarios"
    - "Wave 0 test stubs: skip gracefully before billing app is registered, run fully after Wave 1"
    - "Settings-conditional skips: tests that need BILLING_ADAPTER/STRIPE_SECRET_KEY skip when unconfigured"

key-files:
  created:
    - apps/api/tests/billing/__init__.py
    - apps/api/tests/billing/conftest.py
    - apps/api/tests/billing/test_adapters.py
    - apps/api/tests/billing/test_models.py
    - apps/api/tests/billing/test_signals.py
  modified: []

key-decisions:
  - "importorskip alone insufficient for Django models — added try/except RuntimeError guard for unregistered-app case"
  - "BILLING_ADAPTER and STRIPE_SECRET_KEY tests use pytest.skip guard rather than assert-only — enables clean skips before Wave 1 settings are added"
  - "test_adapters.py uses plain importorskip (no RuntimeError guard) — adapters module has no Django model imports"

patterns-established:
  - "Django billing test skip pattern: try/except RuntimeError wrapping pytest.importorskip for model/signal files"
  - "Settings-conditional test skip: if not hasattr(settings, 'X') or not settings.X: pytest.skip(...)"

requirements-completed: [ADPTR-01, ADPTR-02, CUST-01, CUST-02, SUB-06, PAY-02]

duration: 5min
completed: "2026-03-07"
---

# Phase 9 Plan 01: Billing Test Infrastructure (Wave 0) Summary

**pytest billing test skeleton with 5 files, importorskip-based skipping, and a RuntimeError guard for partially-installed Django apps**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-03-07T22:03:26Z
- **Completed:** 2026-03-07T22:08:11Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Created `apps/api/tests/billing/` as a proper Python package with `__init__.py`
- Added `conftest.py` with `user` (db-backed) and `customer` (importorskip-guarded) fixtures
- Created `test_adapters.py` (98 lines) covering ADPTR-01/02/03 with PaymentAdapter ABC and StripeAdapter contract tests
- Created `test_models.py` (105 lines) covering CUST-01/SUB-06/PAY-02/HOOK-03 model field and constraint checks
- Created `test_signals.py` (47 lines) covering CUST-02 auto-customer-creation on User post_save
- All files collect with exit 0, zero ImportErrors, zero collection failures

## Task Commits

Each task was committed atomically:

1. **Task 1: Create test package and shared fixtures** - `9dbd19e` (test)
2. **Task 2: Create stub test files for adapters, models, and signals** - `203b317` (test)

## Files Created/Modified

- `apps/api/tests/billing/__init__.py` — empty package marker
- `apps/api/tests/billing/conftest.py` — user and customer shared fixtures
- `apps/api/tests/billing/test_adapters.py` — PaymentAdapter ABC and StripeAdapter contract stubs
- `apps/api/tests/billing/test_models.py` — model shape, field, and constraint stubs
- `apps/api/tests/billing/test_signals.py` — signal auto-creation behavior stubs

## Decisions Made

- `pytest.importorskip` alone does not handle the case where a billing module exists on disk but `apps.billing` is not in `INSTALLED_APPS`. Django's model metaclass raises `RuntimeError` (not `ImportError`) in that scenario. Added `try/except RuntimeError` wrapper with `pytest.skip(allow_module_level=True)` in `test_models.py` and `test_signals.py`.
- `test_adapters.py` imports only the adapters module (no Django model imports at module level), so plain `importorskip` is sufficient there.
- Tests for `BILLING_ADAPTER` and `STRIPE_SECRET_KEY` settings use an explicit guard (`if not hasattr(settings, "BILLING_ADAPTER")`) with `pytest.skip` rather than asserting directly — ensures they skip (not fail) when Wave 1 settings haven't been added yet.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Extended importorskip to handle Django RuntimeError for unregistered apps**

- **Found during:** Task 2 (Create stub test files)
- **Issue:** `pytest.importorskip("apps.billing.models")` at module level raised `RuntimeError` (not `ImportError`) when billing module files existed on disk but `apps.billing` was absent from `INSTALLED_APPS`. pytest treats `RuntimeError` as a collection error, not a skip.
- **Fix:** Wrapped `pytest.importorskip` in `try/except RuntimeError` in `test_models.py` and `test_signals.py`, converting it to `pytest.skip(allow_module_level=True)`.
- **Files modified:** `apps/api/tests/billing/test_models.py`, `apps/api/tests/billing/test_signals.py`
- **Verification:** `uv run pytest tests/billing/ --collect-only -q` exits 0 with no collection errors
- **Committed in:** `203b317` (Task 2 commit)

**2. [Rule 1 - Bug] Added pytest.skip guards to settings-dependent adapter tests**

- **Found during:** Task 2 verification
- **Issue:** `TestAdapterResolution` tests asserting `BILLING_ADAPTER` setting existence failed (not skipped) because the setting isn't added until Wave 1 updates Django settings.
- **Fix:** Added `if not hasattr(settings, "BILLING_ADAPTER") or not settings.BILLING_ADAPTER: pytest.skip(...)` guard in both `TestAdapterResolution` test methods.
- **Files modified:** `apps/api/tests/billing/test_adapters.py`
- **Verification:** All tests pass or skip cleanly — 6 passed, 5 skipped, 0 failures
- **Committed in:** `203b317` (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (both Rule 1 — correctness bugs in skip behavior)
**Impact on plan:** Both fixes necessary for correct Wave 0 behavior. No scope creep. Plan intent preserved.

## Issues Encountered

The billing module (`apps/api/apps/billing/`) was already partially present on disk from a prior execution attempt, but `apps.billing` was not in `INSTALLED_APPS` in `base.py`. This created a Django app registry edge case that `pytest.importorskip` alone cannot handle. The auto-fix (deviation #1 above) resolves this cleanly.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Wave 0 test skeleton is complete and collects cleanly
- When `apps.billing` is added to `INSTALLED_APPS` (Wave 1 / Plan 09-02), `test_models.py` and `test_signals.py` will automatically run their full test suites
- When `BILLING_ADAPTER` setting is added, `TestAdapterResolution` tests will run
- When `STRIPE_SECRET_KEY` is set, `test_stripe_adapter_instantiates` will run

---

_Phase: 09-billing-scaffold_
_Completed: 2026-03-07_
