---
phase: 31-cli-scaffolder-integration
plan: 01
subsystem: testing
tags: [pytest, scaffolder, b2b, tdd, subprocess, django]

# Dependency graph
requires:
  - phase: 30-admin-backoffice
    provides: Full B2B stack (orgs, api_keys, webhooks, audit, hijack, pghistory) installed in template
provides:
  - RED test stubs for SCAFF-01 B2B scaffold contract
  - pytest subdirectory scaffolder/ with __init__.py for discovery
  - TestB2BScaffoldViaCLI class with two test methods defining removal contract
affects: [31-02, 31-03]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "sys.executable used instead of 'python' literal for cross-env subprocess invocation"
    - "TDD RED stubs: test_scaffold_without_b2b fails because removeB2BModule not yet exported; test_scaffold_with_b2b passes on real source"

key-files:
  created:
    - apps/api/tests/scaffolder/__init__.py
    - apps/api/tests/scaffolder/test_b2b_scaffold.py
  modified: []

key-decisions:
  - "sys.executable used in test_scaffold_with_b2b instead of 'python' — ensures correct venv Python is used regardless of PATH (auto-fixed Rule 1)"
  - "test_scaffold_with_b2b runs manage.py check against real template source (not tmp_path copy) — full Django project tree is required for check to succeed without missing-file errors"
  - "parents[4] resolves PROJECT_ROOT from tests/scaffolder/ — one level deeper than tests/ which uses parents[3]"

patterns-established:
  - "Pattern: scaffolder/ subdirectory under tests/ requires __init__.py for pytest discovery"
  - "Pattern: inline Node.js script via node --input-type=module exercises compiled dist/remove.js without TTY"

requirements-completed: [SCAFF-01]

# Metrics
duration: 2min
completed: 2026-03-13
---

# Phase 31 Plan 01: B2B Scaffold RED Tests Summary

**pytest RED test stubs for B2B scaffolder contract — two tests define SCAFF-01 removal assertions, one fails RED (removeB2BModule not yet exported), one passes on real B2B source**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-13T19:34:29Z
- **Completed:** 2026-03-13T19:36:30Z
- **Tasks:** 1
- **Files modified:** 2

## Accomplishments

- Created `apps/api/tests/scaffolder/__init__.py` enabling pytest subdirectory discovery
- Created `tests/scaffolder/test_b2b_scaffold.py` with `TestB2BScaffoldViaCLI` class defining the full SCAFF-01 removal contract
- `test_scaffold_without_b2b` is RED: fails with SyntaxError "does not provide an export named 'removeB2BModule'" — exactly the expected RED state before Plan 02 ships
- `test_scaffold_with_b2b` passes: `manage.py check` returns 0 on real template source confirming B2B stack is correctly installed

## Task Commits

Each task was committed atomically:

1. **Task 1: Write RED test stubs for B2B scaffold (SCAFF-01)** - `722fb69` (test)

**Plan metadata:** (see final_commit below)

## Files Created/Modified

- `apps/api/tests/scaffolder/__init__.py` — empty file, enables pytest to discover scaffolder/ as a package
- `apps/api/tests/scaffolder/test_b2b_scaffold.py` — integration test: two methods in TestB2BScaffoldViaCLI, skipif guard on CLI_DIST_REMOVE existence, subprocess pattern from test_scaffolder_billing_removal.py

## Decisions Made

- `sys.executable` used instead of `'python'` for `manage.py check` subprocess — ensures the correct venv Python binary runs regardless of PATH configuration; `'python'` caused FileNotFoundError in this environment.
- `test_scaffold_with_b2b` runs against real template source (`PROJECT_ROOT / "apps/api"`) not a tmp_path copy — manage.py check requires the full Django project tree (migrations, templates, all app modules).
- `parents[4]` used for PROJECT*ROOT (not `parents[3]`) — test file is at `tests/scaffolder/test_b2b_scaffold.py` which is one level deeper than the other scaffolder tests at `tests/test*\*.py`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Used sys.executable instead of 'python' literal**

- **Found during:** Task 1 (during test verification run)
- **Issue:** Plan specified `["python", "manage.py", "check", ...]` but `python` is not on PATH in this environment (only `python3` via `/usr/bin/python3`). Test raised `FileNotFoundError: No such file or directory: 'python'`.
- **Fix:** Changed to `sys.executable` which always resolves to the running Python interpreter (the venv Python at `.venv/bin/python3`). Added `import sys` to imports.
- **Files modified:** `apps/api/tests/scaffolder/test_b2b_scaffold.py`
- **Verification:** `test_scaffold_with_b2b` passes after fix (1 passed, 1 failed for expected reasons)
- **Committed in:** `722fb69` (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - Bug)
**Impact on plan:** Required for test_scaffold_with_b2b to be runnable. No scope creep.

## Issues Encountered

- pre-commit ruff E501 (line too long) fired on the PROJECT_ROOT comment. ruff-format rewrote the assignment to wrap the comment. File was restaged after reformatting and commit succeeded on second attempt.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- RED test contract is established: Plan 02 must implement `removeB2BModule()` in `dist/remove.js` to turn `test_scaffold_without_b2b` GREEN
- Plan 02 must also fix the unmatched `# B2B_START` marker at `base.py:670` (confirmed in RESEARCH.md) for the without-b2b assertions to pass
- `test_scaffold_with_b2b` is already GREEN — no Plan 02 action needed for it

---

_Phase: 31-cli-scaffolder-integration_
_Completed: 2026-03-13_
