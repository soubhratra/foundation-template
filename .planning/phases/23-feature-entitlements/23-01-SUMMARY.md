---
phase: 23-feature-entitlements
plan: 01
subsystem: testing
tags: [pytest, entitlements, billing, caching, tdd]

# Dependency graph
requires:
  - phase: 22-rbac
    provides: import gate pattern (pytest.fail inside try/except ImportError) established for RED stubs

provides:
  - 9 RED test stubs covering ENT-01 (has_feature logic), ENT-02 (caching + invalidation), ENT-03 (billing-off fallback)
  - tests/billing/test_entitlements.py with TestHasFeature (5), TestCaching (1), TestCacheInvalidation (1)
  - tests/core/test_entitlements.py with TestBillingOffFallback (2)

affects: [23-02, 23-03]

# Tech tracking
tech-stack:
  added: []
  patterns: [import gate pattern for RED stubs, noqa F401 suppression for inline import gates]

key-files:
  created:
    - apps/api/tests/billing/test_entitlements.py
    - apps/api/tests/core/test_entitlements.py
  modified: []

key-decisions:
  - "noqa F401 added to all inline import gate stubs — ruff F401 fires on unused imports in try/except blocks; noqa preserves intent without removing the gate"

patterns-established:
  - "Import gate pattern with noqa F401: `from apps.x import symbol  # noqa: F401` inside try/except ImportError — prevents collection ERRORs while giving actionable failure message when module missing"

requirements-completed: [ENT-01, ENT-02, ENT-03]

# Metrics
duration: 7min
completed: 2026-03-12
---

# Phase 23 Plan 01: Feature Entitlements RED Stubs Summary

**9 failing test stubs (import-gate pattern) covering ENT-01/ENT-02/ENT-03 — Wave 1 plans can now turn them GREEN**

## Performance

- **Duration:** ~7 min
- **Started:** 2026-03-12T22:17:34Z
- **Completed:** 2026-03-12T22:25:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- 7 RED stubs in `tests/billing/test_entitlements.py` covering `_has_feature()` logic and cache behavior
- 2 RED stubs in `tests/core/test_entitlements.py` covering billing-off fallback (`has_feature()` returns True)
- All 9 stubs fail with `pytest.fail("not implemented")` — no collection ERRORs, no accidental PASSes
- Pre-existing test_services.py errors confirmed out-of-scope (pre-existed before this plan)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create RED stubs — billing entitlements (ENT-01, ENT-02)** - `d8ee22d` (test)
2. **Task 2: Create RED stubs — core entitlements (ENT-03)** - `9ca74aa` (test)

## Files Created/Modified

- `apps/api/tests/billing/test_entitlements.py` - 7 stubs: TestHasFeature (5), TestCaching (1), TestCacheInvalidation (1)
- `apps/api/tests/core/test_entitlements.py` - 2 stubs: TestBillingOffFallback

## Decisions Made

- Added `# noqa: F401` to all inline import gates — ruff F401 fires on imports used only for their side-effect of raising ImportError; the noqa comment preserves the import gate pattern established in Phase 20/21 without ruff auto-removing the imports.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Added noqa F401 to inline import gate stubs**

- **Found during:** Task 1 (commit hook failure)
- **Issue:** ruff F401 flagged `_has_feature` and `_handle_subscription_updated` as unused imports inside `try/except ImportError` blocks; pre-commit hook blocked commit
- **Fix:** Added `# noqa: F401` to all 9 inline import statements; also removed the top-level `from django.core.cache import cache` that ruff auto-removed (was unused at stub stage)
- **Files modified:** apps/api/tests/billing/test_entitlements.py
- **Verification:** Pre-commit hook passes; all 9 stubs still FAIL with "not implemented"
- **Committed in:** d8ee22d (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 — ruff linting)
**Impact on plan:** Minimal fix to satisfy ruff; import gate intent fully preserved.

## Issues Encountered

- ruff F401 linting conflict with import gate pattern — resolved via noqa suppression (same approach will apply to all future stub files using this pattern)

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All 9 RED stubs in place — Wave 1 plans (23-02, 23-03) can proceed to turn them GREEN
- Wave 1 will need to add `plan_id` to `Subscription`, create `apps/billing/entitlements.py`, create `apps/core/entitlements.py`, and add `feature_flags` to `BILLING_PLANS`

---

_Phase: 23-feature-entitlements_
_Completed: 2026-03-12_

## Self-Check: PASSED

- `apps/api/tests/billing/test_entitlements.py` — FOUND
- `apps/api/tests/core/test_entitlements.py` — FOUND
- `.planning/phases/23-feature-entitlements/23-01-SUMMARY.md` — FOUND
- Commit `d8ee22d` — FOUND (Task 1: billing stubs)
- Commit `9ca74aa` — FOUND (Task 2: core stubs)
