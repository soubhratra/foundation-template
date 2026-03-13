---
phase: 29-audit-logging
plan: "01"
subsystem: testing
tags: [pghistory, audit-log, tdd, pytest, django]

# Dependency graph
requires:
  - phase: 28-api-key-authentication
    provides: APIKey model with generate_key() used in api_key_instance fixture
  - phase: 27-outbound-webhooks
    provides: WebhookEndpoint model with generate_secret() used in webhook_endpoint_instance fixture
  - phase: 26-organization-model-per-org-billing
    provides: Organization, Membership, IsOrgMember, IsOrgAdmin used in controller test stubs
provides:
  - RED test contract for AUDIT-01 (pghistory trigger coverage on 4 B2B models)
  - RED test contract for AUDIT-02 (org-scoped audit-log query API with filtering + pagination)
  - Module-level ImportError trigger in tests/audit/__init__.py (collection fails until Wave 2 ships)
  - 6 shared fixtures in tests/audit/conftest.py with lazy imports
affects: [29-audit-logging]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "RED trigger pattern: __init__.py imports from non-existent module; collection fails immediately"
    - "Lazy imports in conftest.py fixture bodies prevent double-import errors while __init__.py is the trigger"
    - "raise AssertionError() used instead of assert False (ruff B011 — assert False removed by -O flag)"

key-files:
  created:
    - apps/api/apps/audit/__init__.py
    - apps/api/tests/audit/__init__.py
    - apps/api/tests/audit/conftest.py
    - apps/api/tests/audit/test_models.py
    - apps/api/tests/audit/test_middleware.py
    - apps/api/tests/audit/test_context.py
    - apps/api/tests/audit/test_controllers.py
    - apps/api/tests/audit/test_schemas.py
  modified: []

key-decisions:
  - "raise AssertionError() used for all RED stubs instead of assert False — ruff B011 flags assert False as unsafe under -O flag"
  - "apps/audit/__init__.py is intentionally empty — app directory must exist so tests/audit/__init__.py module-level import produces ModuleNotFoundError (not FileNotFoundError)"
  - "Lazy imports inside fixture bodies in conftest.py follow the same pattern as tests/webhooks/conftest.py and tests/api_keys/ — prevents double-import conflicts while __init__.py remains the RED trigger"

patterns-established:
  - "RED trigger pattern: tests/<domain>/__init__.py imports from apps.<domain>.<module> at module level, causing immediate collection failure until implementation ships"
  - "Fixture files use lazy imports inside function bodies — only pytest and get_user_model() imported at module top"
  - "B011 ruff rule: all test stubs use raise AssertionError() not assert False"

requirements-completed:
  - AUDIT-01
  - AUDIT-02

# Metrics
duration: 3min
completed: "2026-03-13"
---

# Phase 29 Plan 01: Audit Logging RED Test Stubs Summary

**16 RED test stubs covering pghistory trigger coverage (AUDIT-01) and org-scoped audit-log query API (AUDIT-02), with module-level ImportError trigger blocking collection until Wave 2 ships**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-13T14:31:00Z
- **Completed:** 2026-03-13T14:34:00Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- Created `apps/api/apps/audit/__init__.py` stub (empty directory scaffold enabling the RED trigger)
- Created `tests/audit/__init__.py` with module-level import from `apps.audit.context` — collection fails with `ModuleNotFoundError` until Wave 2 ships
- Created `tests/audit/conftest.py` with 6 fixtures (`org_owner`, `org`, `org_admin`, `org_member`, `api_key_instance`, `webhook_endpoint_instance`) — all using lazy imports inside fixture bodies
- Wrote 16 RED stubs across 5 test files covering AUDIT-01 (trigger coverage on Organization, Membership, APIKey, WebhookEndpoint) and AUDIT-02 (permission gates, filtering, cursor pagination, schema field exclusion)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create apps/audit/**init**.py stub and all test infrastructure** - `553a1c8` (test)
2. **Task 2: Write all RED test stubs (5 test files)** - `f6c80d0` (test)

## Files Created/Modified

- `apps/api/apps/audit/__init__.py` - Empty stub creating the audit app directory
- `apps/api/tests/audit/__init__.py` - Module-level import from `apps.audit.context` — RED trigger
- `apps/api/tests/audit/conftest.py` - 6 shared fixtures with lazy imports inside fixture bodies
- `apps/api/tests/audit/test_models.py` - 5 RED stubs for pghistory trigger coverage (AUDIT-01)
- `apps/api/tests/audit/test_middleware.py` - 2 RED stubs for `AuditContextMiddleware.get_context()`
- `apps/api/tests/audit/test_context.py` - 1 RED stub for `audit_context()` no-op degradation
- `apps/api/tests/audit/test_controllers.py` - 7 RED stubs for `GET /api/v1/org/{slug}/audit-log`
- `apps/api/tests/audit/test_schemas.py` - 1 RED stub for `AuditEntryOut` field exclusion

## Decisions Made

- `raise AssertionError()` used for all RED stubs instead of `assert False` — ruff B011 flags `assert False` as unsafe under Python `-O` flag; `raise AssertionError()` is the correct idiom
- `apps/audit/__init__.py` is intentionally empty — the app directory must exist so that `tests/audit/__init__.py`'s module-level import produces `ModuleNotFoundError` (not `FileNotFoundError`), confirming correct RED state
- Lazy imports inside fixture bodies in `conftest.py` follow the established pattern from `tests/webhooks/conftest.py` and `tests/api_keys/`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Replaced `assert False` with `raise AssertionError()` across all test stubs**

- **Found during:** Task 2 (pre-commit hook ran ruff linter)
- **Issue:** ruff B011 rule flags `assert False` — Python's `-O` optimization flag silently removes `assert` statements, making stubs silently pass under optimized builds
- **Fix:** Rewrote all 16 stubs to use `raise AssertionError(message)` instead of `assert False, message`
- **Files modified:** test_models.py, test_middleware.py, test_context.py, test_controllers.py, test_schemas.py
- **Verification:** ruff passed on second commit attempt; all stubs still fail RED
- **Committed in:** f6c80d0 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - Bug)
**Impact on plan:** Fix ensures test stubs cannot silently pass under `-O` flag. No scope creep.

## Issues Encountered

- Pre-commit ruff-format reformatted `conftest.py` and `__init__.py` on first Task 1 commit — required re-staging and recommitting (standard workflow, not a blocker)
- Pre-commit ruff B011 rejected `assert False` in Task 2 — rewrote all stubs to `raise AssertionError()` before second commit succeeded

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- RED test contract is fully established for AUDIT-01 and AUDIT-02
- Wave 2 (29-02) must implement `apps/audit/context.py` with `audit_context()` to unblock collection, then implement pghistory model decorators for trigger coverage
- Wave 3 (29-03) must implement the `GET /api/v1/org/{slug}/audit-log` endpoint and `AuditEntryOut` schema to satisfy the controller and schema stubs

---

## Self-Check: PASSED

All 8 created files verified on disk. Both task commits (553a1c8, f6c80d0) confirmed in git log.

---

_Phase: 29-audit-logging_
_Completed: 2026-03-13_
