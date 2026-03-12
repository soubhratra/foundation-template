---
phase: 25-gdpr-export-plan-id-accuracy
plan: "01"
subsystem: api
tags: [gdpr, export, billing, subscription, django, pytest]

# Dependency graph
requires:
  - phase: 23-feature-entitlements
    provides: Subscription.plan_id field added via migration 0004
  - phase: 21-gdpr-baseline
    provides: AccountExportService, GET /api/v1/account/export endpoint

provides:
  - GDPR data export returns accurate plan_id from Subscription.plan_id
  - TDD round-trip test covering billing.plan_id accuracy (GDPR-02)

affects: [gdpr, billing, export, data-accuracy]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - TDD RED/GREEN for data accuracy regression fix
    - ORM field read replacing hardcoded None in export service

key-files:
  created: []
  modified:
    - apps/api/tests/accounts/test_export.py
    - apps/api/apps/accounts/services.py

key-decisions:
  - "plan_id read directly from sub.plan_id ORM field; no Stripe IDs exposed in export"
  - "Except fallback left unchanged — correctly returns None when no Subscription row exists"

patterns-established:
  - "Export service reads plan_id from Subscription.plan_id, not hardcoded None"

requirements-completed: [GDPR-02]

# Metrics
duration: 3min
completed: 2026-03-12
---

# Phase 25 Plan 01: GDPR Export plan_id Accuracy Summary

**Single-line ORM fix in AccountExportService.export() so billing.plan_id reflects Subscription.plan_id instead of hardcoded None (GDPR Article 20 accuracy)**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-12T23:47:02Z
- **Completed:** 2026-03-12T23:49:21Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Added TDD RED test `test_export_billing_plan_id_round_trip` verifying billing.plan_id round-trip for a subscribed user
- Fixed `AccountExportService.export()`: replaced `plan_id = None` with `plan_id = sub.plan_id`
- All 8 export tests pass GREEN; 28 accounts suite tests pass with no regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Add RED test for plan_id round-trip** - `a7f5070` (test)
2. **Task 2: Fix AccountExportService to read sub.plan_id** - `5786fdd` (fix)

_Note: TDD tasks have two commits (test RED → fix GREEN)_

## Files Created/Modified

- `apps/api/tests/accounts/test_export.py` - Added `export_user_with_plan` fixture and `test_export_billing_plan_id_round_trip` test method
- `apps/api/apps/accounts/services.py` - Replaced hardcoded `plan_id = None` with `plan_id = sub.plan_id`

## Decisions Made

- Read `sub.plan_id` directly from the ORM — Subscription.plan_id (CharField, nullable) was added in Phase 23 migration 0004; no Stripe IDs are exposed
- The `except Exception` fallback block was left unchanged — it correctly returns `plan_id = None` when no Subscription row exists for a user

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- GDPR-02 data accuracy requirement closed
- Export billing section now returns accurate plan_id for all subscribed users
- No blockers for subsequent phases

---

_Phase: 25-gdpr-export-plan-id-accuracy_
_Completed: 2026-03-12_
