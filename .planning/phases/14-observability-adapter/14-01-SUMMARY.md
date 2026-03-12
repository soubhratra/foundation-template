---
phase: 14-observability-adapter
plan: "01"
subsystem: testing
tags: [observability, posthog, tdd, pytest, celery, django-middleware, scaffolder]

# Dependency graph
requires:
  - phase: 13-structured-logging-distributed-tracing
    provides: RequestContextMiddleware in apps/core/middleware.py — ObservabilityMiddleware will be added alongside it in Plan 02
provides:
  - RED test stubs for ObservabilityAdapter ABC, PostHogAdapter, NoOpAdapter, ObservabilityMiddleware, Celery task_failure signal
  - RED stub for CLI removeObservability() integration test
affects:
  - 14-02 (implements production code to make these stubs GREEN)
  - 14-04 (implements removeObservability() TypeScript function to make scaffolder test GREEN)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Deferred imports inside test bodies — pytest collects file without ImportError; tests fail RED until module exists"
    - "subprocess + inline ESM node script pattern — tests real compiled TypeScript, not a Python reimplementation"

key-files:
  created:
    - apps/api/tests/core/test_observability.py
    - apps/api/tests/test_scaffolder_observability_removal.py
  modified: []

key-decisions:
  - "Deferred import pattern (import inside function body) chosen over try/except ImportError at top — gives cleaner failure messages per test"
  - "Scaffolder removal test mirrors test_scaffolder_billing_removal.py exactly — subprocess call to dist/remove.js with inline ESM, no TTY"

patterns-established:
  - "TDD RED wave: all test stubs written before any production code — matches Phase 13 Wave 0 approach"
  - "Scaffolder integration tests invoke compiled dist/remove.js via node --input-type=module inline script"

requirements-completed:
  - OBS-03

# Metrics
duration: 3min
completed: 2026-03-11
---

# Phase 14 Plan 01: RED Test Stubs for ObservabilityAdapter Summary

**7 RED TDD stubs created covering ObservabilityAdapter ABC, PostHogAdapter, NoOpAdapter, ObservabilityMiddleware, Celery signal handler, and CLI removeObservability() integration test**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-11T19:02:41Z
- **Completed:** 2026-03-11T19:06:04Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Created `tests/core/test_observability.py` with 6 failing tests covering the full adapter contract (NoOpAdapter, PostHogAdapter, get_observability_adapter, middleware process_exception, middleware user context, Celery signal)
- Created `tests/test_scaffolder_observability_removal.py` with 1 failing test that asserts all 9 observability touch points are cleaned by `removeObservability()`
- All 7 tests collect cleanly (no syntax/import errors) and fail RED — ready to guide Plan 02 and Plan 04 implementation

## Task Commits

Each task was committed atomically:

1. **Task 1: Create test_observability.py stubs (RED)** - `4ec0da0` (test)
2. **Task 2: Create test_scaffolder_observability_removal.py stub (RED)** - `b056a06` (test)

## Files Created/Modified

- `apps/api/tests/core/test_observability.py` — 6 test stubs for OBS-03 adapter contract; deferred imports so collection succeeds RED
- `apps/api/tests/test_scaffolder_observability_removal.py` — Integration stub for CLI removeObservability(); mirrors billing removal test pattern

## Decisions Made

- Deferred import pattern (import inside test function body) over top-level try/except — produces cleaner per-test failure messages and better RED/GREEN clarity
- Scaffolder test exactly mirrors `test_scaffolder_billing_removal.py` pattern: subprocess + inline ESM script targeting `dist/remove.js`, no TTY required
- `test_celery_signal_handler` verifies `task_failure.receivers` is non-empty after app load — simplest assertion that CoreConfig.ready() wired the handler

## Deviations from Plan

None — plan executed exactly as written.

Minor: ruff pre-commit hook auto-formatted one import (multi-line grouping) and flagged one docstring too long; fixed inline before final commit. Not a deviation — normal formatting compliance.

## Issues Encountered

Ruff pre-commit hook flagged one docstring line exceeding 100 chars on first commit attempt. Shortened docstring and re-committed cleanly.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All 7 test stubs in RED state — Plan 02 can immediately start writing production code to turn them GREEN
- Test contract fully specifies the `ObservabilityAdapter` ABC interface: `capture_exception(exc, context)` and `capture_event(event, properties)`, both on `NoOpAdapter` and `PostHogAdapter`
- Scaffolder removal test contract specifies all 9 touch points `removeObservability()` must clean — Plan 04 can implement against this spec

---

_Phase: 14-observability-adapter_
_Completed: 2026-03-11_

## Self-Check: PASSED

- FOUND: apps/api/tests/core/test_observability.py
- FOUND: apps/api/tests/test_scaffolder_observability_removal.py
- FOUND: .planning/phases/14-observability-adapter/14-01-SUMMARY.md
- FOUND: commit 4ec0da0 (test_observability.py stubs)
- FOUND: commit b056a06 (scaffolder removal stub)
