---
phase: 18-dev-time-quality-gates
plan: 02
subsystem: testing
tags:
  [
    nplusone,
    n-plus-one,
    commitlint,
    conventional-commits,
    ruff,
    mccabe,
    complexity,
    pre-commit,
    pytest,
  ]

# Dependency graph
requires:
  - phase: 18-01
    provides: "RED test stubs for DEV-04, DEV-07, DEV-08 quality gates"
provides:
  - "nplusone N+1 detection autouse fixture active for all pytest tests"
  - "allow_lazy_load decorator for intentional N+1 suppression"
  - "conventional-pre-commit commit-msg hook in .pre-commit-config.yaml"
  - "ruff McCabe complexity gate: [tool.ruff.lint.mccabe] max-complexity = 10"
  - "All 6 quality gate tests GREEN"
affects: [future-phases-with-n+1-risks, phase-19-and-beyond]

# Tech tracking
tech-stack:
  added: ["nplusone>=1.0 (runtime dep, not dev group)"]
  patterns:
    - "_LazyLoadProfiler: custom context manager wrapping nplusone LazyListener only (not EagerListener) — avoids false positives on unused eager loads"
    - "allow_lazy_load decorator registered as synthetic nplusone.ext.pytest module for import compatibility"
    - "Blinker signal explicit disconnect in __exit__ — required because LazyListener.teardown() is a no-op"
    - "conventional-pre-commit on commit-msg stage (requires pre-commit install --hook-type commit-msg)"

key-files:
  created: []
  modified:
    - "apps/api/pyproject.toml — nplusone in [project.dependencies], [tool.ruff.lint] C90, [tool.ruff.lint.mccabe] max-complexity=10"
    - "apps/api/conftest.py — _LazyLoadProfiler, allow_lazy_load, nplusone.ext.pytest shim, _nplusone_guard autouse fixture"
    - "apps/api/tests/core/test_quality_gates.py — all 6 RED stubs replaced with GREEN assertions"
    - ".pre-commit-config.yaml — conventional-pre-commit v3.4.0 commit-msg hook added"
    - ".secrets.baseline — updated for test password false positives"

key-decisions:
  - "nplusone 1.0.0 has no pytest plugin — _LazyLoadProfiler and allow_lazy_load implemented directly in conftest.py; nplusone.ext.pytest synthetic module registered in sys.modules for import compatibility"
  - "_LazyLoadProfiler activates LazyListener only (not EagerListener) — EagerListener raises on unused eager loads which causes false positives in existing tests using select_related"
  - "LazyListener requires explicit blinker signal disconnect in __exit__ — teardown() is a no-op in the base Listener class; without explicit disconnect, listeners fire in subsequent tests"
  - "conventional-pre-commit requires pre-commit install --hook-type commit-msg — documented in .pre-commit-config.yaml comment"

patterns-established:
  - "allow_lazy_load pattern: @allow_lazy_load decorator marks intentional N+1 tests — suppresses NPlusOneError for that test only, requires code review justification"

requirements-completed: [DEV-04, DEV-07, DEV-08]

# Metrics
duration: 8min
completed: 2026-03-11
---

# Phase 18 Plan 02: Dev-Time Quality Gates Implementation Summary

**nplusone N+1 detection autouse fixture + conventional-pre-commit commit-msg hook + ruff McCabe complexity gate (max 10) — all 6 quality gate tests GREEN**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-03-11T23:31:00Z
- **Completed:** 2026-03-11T23:39:00Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- nplusone installed as runtime dep; `_nplusone_guard` autouse fixture detects N+1 queries immediately during test body (not deferred)
- `@allow_lazy_load` decorator implemented for suppressing NPlusOneError on intentional N+1 accesses
- conventional-pre-commit v3.4.0 added to `.pre-commit-config.yaml` on `commit-msg` stage
- `[tool.ruff.lint.mccabe]` with `max-complexity = 10` added to pyproject.toml; `select = ["E", "F", "C90"]` makes C90 explicit
- All 6 RED stubs from Plan 18-01 turned GREEN

## Task Commits

Each task was committed atomically:

1. **Task 1: Install nplusone, add ruff McCabe config, add commitlint pre-commit hook** - `e55a256` (chore)
2. **Task 2: Wire nplusone autouse fixture and turn all 6 tests GREEN** - `a3c8ce1` (feat)

## Files Created/Modified

- `apps/api/pyproject.toml` — nplusone in `[project.dependencies]`; `[tool.ruff.lint]` C90; `[tool.ruff.lint.mccabe]` max-complexity = 10
- `apps/api/conftest.py` — `_LazyLoadProfiler`, `allow_lazy_load` decorator, `nplusone.ext.pytest` shim, `_nplusone_guard` autouse fixture
- `apps/api/tests/core/test_quality_gates.py` — all 6 RED stubs replaced with GREEN assertions
- `.pre-commit-config.yaml` — conventional-pre-commit v3.4.0 commit-msg hook
- `.secrets.baseline` — updated for test password false positives

## Decisions Made

- **nplusone 1.0.0 has no pytest plugin** — the plan's interface comments referenced `nplusone.ext.pytest.allow_lazy_load` and an `nplusone` fixture that don't exist in v1.0.0. Both were implemented directly in conftest.py; a synthetic `nplusone.ext.pytest` module registered in `sys.modules` ensures `from nplusone.ext.pytest import allow_lazy_load` works in test files.

- **LazyListener-only profiler** — nplusone's full `Profiler` activates both `LazyListener` (N+1 detection, immediate raise) and `EagerListener` (unused eager loads, raises at teardown). The `EagerListener` caused false positives on billing controller tests that correctly use `select_related`. `_LazyLoadProfiler` uses `LazyListener` only, matching the plan's intent (N+1 detection, not eager-load policing).

- **Explicit blinker signal disconnect** — `LazyListener.teardown()` is inherited from the base `Listener` class which is a no-op. Without explicit `signal.disconnect()` calls in `__exit__`, the listener remains connected to blinker signals and fires in subsequent tests (causing the `@allow_lazy_load` test to fail when run after `test_nplusone_raises_on_n_plus_one`).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] nplusone 1.0.0 has no pytest plugin — implemented equivalents in conftest.py**

- **Found during:** Task 2 (implementation)
- **Issue:** Plan's interface comments referenced `nplusone.ext.pytest.allow_lazy_load` and an `nplusone` pytest fixture that don't exist in nplusone 1.0.0. The package only ships Django/Flask/SQLAlchemy extensions.
- **Fix:** Implemented `_LazyLoadProfiler` context manager (wrapping `LazyListener` only) and `allow_lazy_load` decorator directly in conftest.py. Registered synthetic `nplusone.ext.pytest` module in `sys.modules` for import compatibility.
- **Files modified:** `apps/api/conftest.py`, `apps/api/tests/core/test_quality_gates.py`
- **Verification:** All 6 tests pass GREEN; billing controller tests no longer error
- **Committed in:** a3c8ce1

**2. [Rule 1 - Bug] LazyListener blinker signal not disconnected on context exit**

- **Found during:** Task 2 (full test run — `test_nplusone_allow_annotation_suppresses_error` failed when preceded by `test_nplusone_raises_on_n_plus_one`)
- **Issue:** `LazyListener.teardown()` is a no-op (inherited from base `Listener`). Signal handler persisted across tests, causing the `@allow_lazy_load` test to still get `NPlusOneError` from the previous test's listener.
- **Fix:** Added explicit `signal.disconnect()` calls for `handle_load`, `handle_ignore`, and `handle_lazy` in `_LazyLoadProfiler.__exit__()`.
- **Files modified:** `apps/api/conftest.py`
- **Verification:** Tests pass in any order; run together with `tests/billing/test_controllers.py` — no errors
- **Committed in:** a3c8ce1

---

**Total deviations:** 2 auto-fixed (both Rule 1 - Bug)
**Impact on plan:** Both auto-fixes necessary for correctness. No scope creep. The functional contracts described in must_haves are fully satisfied.

## Issues Encountered

- detect-secrets baseline needed updating after ruff reformatted `password="test"` arguments onto separate lines (auto-formatted lines no longer had the inline `# pragma: allowlist secret` comment at the detected position). Updated baseline via `detect-secrets scan --baseline .secrets.baseline`.

## Deferred Items

- `tests/test_scaffolder_observability_removal.py:38` — C901 complexity 15 > 10 in `test_remove_observability_cleans_all_touch_points` (pre-existing from Phase 14, not caused by this plan). Logged to `deferred-items.md`.

## User Setup Required

**conventional-pre-commit requires additional hook-type installation:**

```bash
# In addition to the standard pre-commit install:
pre-commit install --hook-type commit-msg
```

Without this, the commit-msg stage hook will not run locally (it will still run in CI if CI uses `pre-commit run --hook-stage commit-msg`).

## Next Phase Readiness

- All 3 non-schemathesis quality gates (DEV-04, DEV-07, DEV-08) are complete
- Full test suite clean: 117 passed, 4 pre-existing failures (billing services, middleware — out of scope)
- Phase 18 is now complete (18-01 scaffolded stubs, 18-02 implemented gates, 18-03 schemathesis CI)

---

_Phase: 18-dev-time-quality-gates_
_Completed: 2026-03-11_
