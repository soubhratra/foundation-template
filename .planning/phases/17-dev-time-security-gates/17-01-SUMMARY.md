---
phase: 17-dev-time-security-gates
plan: "01"
subsystem: testing
tags: [pytest, tdd, detect-secrets, bandit, pip-audit, django-debug-toolbar, security]

# Dependency graph
requires: []
provides:
  - 8 RED pytest.fail() test stubs covering DEV-01 (detect-secrets), DEV-02 (bandit), DEV-03 (pip-audit), DEV-06 (DDT)
  - Automated verification contracts for Plan 17-03 to turn GREEN
affects:
  - 17-02-PLAN (bandit CI gate — test_bandit_available, test_bandit_clean turn GREEN)
  - 17-03-PLAN (implements all 8 stubs)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - pytest.fail() RED stubs with descriptive reason strings identifying which plan turns them GREEN
    - Section comments grouping tests by requirement ID (DEV-01, DEV-02, DEV-03, DEV-06)

key-files:
  created:
    - apps/api/tests/core/test_dev_gates.py
  modified: []

key-decisions:
  - "pytest.fail() with RED reason strings used for all 8 dev-gate test stubs — cleaner FAILED output that identifies which plan implements each behavior (mirrors Phase 16-01 pattern)"

patterns-established:
  - "Wave 0 TDD: test stubs created before any implementation begins — Plan 17-01 RED, Plans 17-02/17-03 GREEN"
  - "Requirement traceability in test file: section comments group tests by DEV-XX requirement ID"

requirements-completed:
  - DEV-01
  - DEV-02
  - DEV-03
  - DEV-06

# Metrics
duration: 5min
completed: 2026-03-11
---

# Phase 17 Plan 01: Dev-Time Security Gates — RED Test Stubs Summary

**8 pytest.fail() RED stubs for detect-secrets, bandit, pip-audit, and django-debug-toolbar gate verification — Wave 0 TDD contracts for Plans 17-02 and 17-03**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-11T22:20:53Z
- **Completed:** 2026-03-11T22:26:00Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Created `apps/api/tests/core/test_dev_gates.py` with 8 test stubs, all in RED state via `pytest.fail()`
- Each stub includes a descriptive reason string identifying the requirement it covers and that "Plan 17-03" turns it GREEN
- Confirmed output: 8 FAILED, 0 passed, 0 errors when run with `uv run pytest tests/core/test_dev_gates.py -v`

## Task Commits

1. **Task 1: Write RED test stubs for DEV-01, DEV-02, DEV-03, DEV-06** - `34d8e74` (test)

**Plan metadata:** _(final metadata commit follows)_

## Files Created/Modified

- `apps/api/tests/core/test_dev_gates.py` - 8 RED pytest.fail() stubs covering all four Phase 17 requirements

## Decisions Made

- pytest.fail() with RED reason strings used for all 8 stubs — mirrors Phase 16-01 pattern for consistency; cleaner FAILED output identifies which plan implements each behavior

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- All 8 GREEN targets are defined; Plan 17-03 can use these stubs as acceptance criteria
- The stubs export the exact function names listed in the plan frontmatter (all 8 verified)
- Existing test suite unaffected (all prior tests still pass)

---

_Phase: 17-dev-time-security-gates_
_Completed: 2026-03-11_
