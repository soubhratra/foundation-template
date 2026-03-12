---
phase: 13-structured-logging-distributed-tracing
plan: 01
subsystem: testing
tags: [structlog, opentelemetry, pytest, tdd, observability]

# Dependency graph
requires: []
provides:
  - RED test stubs for OBS-01 (structlog processor + middleware) and OBS-02 (configure_otel)
  - pytest-structlog dev dependency installed
  - structlog, opentelemetry-api/sdk/exporter-otlp-proto-grpc runtime dependencies installed
  - tests/core/ package scaffolded with __init__.py
affects:
  - 13-02 (implements apps.core.logging to turn test_logging.py GREEN)
  - 13-03 (implements apps.core.middleware to turn test_middleware.py GREEN)
  - 13-04 (implements apps.core.tracing to turn test_tracing.py GREEN)

# Tech tracking
tech-stack:
  added:
    - structlog==25.5.0
    - opentelemetry-api==1.40.0
    - opentelemetry-sdk==1.40.0
    - opentelemetry-exporter-otlp-proto-grpc==1.40.0
    - pytest-structlog==1.2 (dev)
  patterns:
    - TDD Wave 0 pattern: test stubs created before any implementation exists
    - Tests import from not-yet-created modules to enforce RED state via ModuleNotFoundError

key-files:
  created:
    - apps/api/tests/core/__init__.py
    - apps/api/tests/core/test_logging.py
    - apps/api/tests/core/test_middleware.py
    - apps/api/tests/core/test_tracing.py
  modified:
    - apps/api/pyproject.toml
    - apps/api/uv.lock

key-decisions:
  - "Install structlog + opentelemetry packages as runtime deps (not dev-only) — middleware and logging modules will import them in production"
  - "pytest-structlog added as dev dependency for log capture in future implementation tests"
  - "Middleware tests use settings fixture to inject RequestContextMiddleware dynamically — avoids polluting base test configuration"

patterns-established:
  - "Wave 0 TDD: create all test stubs in RED state before any implementation task begins"
  - "Tests use inner imports (inside test function body) to defer ModuleNotFoundError to test execution rather than collection"
  - "OTel global provider cleanup: reset _trace._TRACER_PROVIDER = None after provider-setting tests to prevent pollution"

requirements-completed:
  - OBS-01
  - OBS-02

# Metrics
duration: 7min
completed: 2026-03-11
---

# Phase 13 Plan 01: Wave 0 TDD Test Stubs Summary

**10 RED test stubs scaffolded across 3 files covering OBS-01 structlog/middleware and OBS-02 OpenTelemetry tracing, with structlog + opentelemetry packages installed**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-11T18:03:40Z
- **Completed:** 2026-03-11T18:10:47Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Created `tests/core/` package with 3 test files and 10 test functions, all failing in correct RED state (ModuleNotFoundError on `apps.core.{logging,middleware,tracing}`)
- Installed structlog, opentelemetry-api, opentelemetry-sdk, and opentelemetry-exporter-otlp-proto-grpc as runtime dependencies
- Installed pytest-structlog>=1.2 as dev dependency; confirmed importable

## Task Commits

Each task was committed atomically:

1. **Task 1: Create test package and structlog + middleware test stubs** - `73fa69f` (test)
2. **Task 2: Create tracing test stubs and add pytest-structlog dev dependency** - `60e7d6f` (test)

**Plan metadata:** _(final docs commit — this summary)_

_Note: TDD tasks have test-only commits here (RED phase). GREEN commits happen in plans 13-02 through 13-04._

## Files Created/Modified

- `apps/api/tests/core/__init__.py` - Empty package init for test discovery
- `apps/api/tests/core/test_logging.py` - 4 tests: add_otel_context processor (inject/omit) + renderer selection (dev/prod)
- `apps/api/tests/core/test_middleware.py` - 4 tests: X-Request-ID header presence, UUID4 validity, duration_ms, context isolation
- `apps/api/tests/core/test_tracing.py` - 2 tests: configure_otel() no-op (no env) + real TracerProvider (env set)
- `apps/api/pyproject.toml` - Added structlog, opentelemetry deps (runtime) + pytest-structlog (dev)
- `apps/api/uv.lock` - Updated lock file

## Decisions Made

- Installed structlog and opentelemetry packages as **runtime** dependencies rather than dev-only, because the middleware and logging modules that implement OBS-01/OBS-02 will import them in production Django.
- Used inner imports (inside test functions) for `apps.core.*` modules to ensure tests fail at execution time with ModuleNotFoundError rather than at collection time, which is the correct TDD RED behavior.
- Added OTel global provider cleanup (`_trace._TRACER_PROVIDER = None`) in the tracing test to prevent state leakage between tests.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Installed structlog + opentelemetry before creating test stubs**

- **Found during:** Task 1 (test stub creation)
- **Issue:** `test_middleware.py` imports `structlog` at module level; without structlog installed, pytest collection itself failed with ModuleNotFoundError — making it impossible to even reach the correct RED failure mode
- **Fix:** Ran `uv add structlog opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp-proto-grpc` before committing test files
- **Files modified:** apps/api/pyproject.toml, apps/api/uv.lock
- **Verification:** All 10 tests now fail with `ModuleNotFoundError: No module named 'apps.core.*'` (correct RED state)
- **Committed in:** `73fa69f` (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Required for correct RED state. Installing runtime deps at test-stub time is consistent with plan intent — these packages are needed by both tests and implementation.

## Issues Encountered

- `python` command not found in API's uv venv — used `uv run python -m pytest` throughout. Expected behavior for uv-managed environments.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All 10 tests are in RED state with correct import errors — implementation plans (13-02, 13-03, 13-04) can begin
- structlog, opentelemetry-api, opentelemetry-sdk, and exporter packages are installed and importable
- pytest-structlog is available for log capture assertions in GREEN phase

---

_Phase: 13-structured-logging-distributed-tracing_
_Completed: 2026-03-11_
