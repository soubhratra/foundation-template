---
phase: 20-social-auth
plan: "01"
subsystem: testing
tags: [tdd, pytest, vitest, social-auth, apple-signin, oauth, jwt, scaffolder]

# Dependency graph
requires: []
provides:
  - RED test stubs for all five Phase 20 requirements (SOCIAL-01 through SOCIAL-05)
  - 19 failing Python tests across 4 test files (backend)
  - 11 failing TypeScript tests in remove-social-auth.test.ts (scaffolder)
  - generate_test_apple_jwt() RS256 test helper for JWT-signing in apple_auth tests
  - _make_apple_jwks_mock() helper for mocking Apple JWKS endpoint
affects: [20-02, 20-03, 20-04, 20-05, 20-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Per-test import gate pattern: import inside test function with try/except ImportError -> pytest.fail() — prevents collection-time errors that would block other tests from running"
    - "SOCIAL AUTH MODULE sentinel comment: # SOCIAL AUTH MODULE — mirrors BILLING MODULE and EMAIL MODULE patterns for scaffolder removal"
    - "_configure_social_providers(env_dict) pure function pattern: accepts dict, returns dict with extra_installed_apps/providers/auto_connect — testable without Django settings reload"

key-files:
  created:
    - apps/api/tests/test_social_settings.py
    - apps/api/tests/test_apple_auth.py
    - apps/api/tests/test_social_adapter.py
    - apps/api/tests/test_scaffolder_social_removal.py
    - packages/create-foundation-app/tests/remove-social-auth.test.ts
  modified: []

key-decisions:
  - "Per-test import gate (not module-level): pytest.fail() inside test body prevents collection errors that stop other files from running — all tests show as FAILED not ERROR"
  - "Import path for _configure_social_providers: config.settings.base (not apps.api.config...) — pytest rootdir is apps/api with python_paths=['.']"
  - "test_scaffolder_social_removal.py skips when dist/remove.js not built — consistent with email/billing scaffolder test pattern"
  - "generate_test_apple_jwt() uses cryptography lib (already in pyproject.toml) to produce RS256 tokens with fresh RSA key pairs — no hardcoded keys"

patterns-established:
  - "TDD RED stubs: import gate inside each test body via try/except ImportError -> pytest.fail() — allows full pytest collection even when modules don't exist yet"
  - "Apple JWT test helper: generate_test_apple_jwt() + _make_apple_jwks_mock() pattern for testing JWT verification without live Apple servers"

requirements-completed: []

# Metrics
duration: 9min
completed: 2026-03-12
---

# Phase 20 Plan 01: Social Auth RED Test Stubs Summary

**30 RED tests across 5 files establish the Nyquist contract for SOCIAL-01 through SOCIAL-05 — no implementation task ships without a pre-existing failing test**

## Performance

- **Duration:** 9 min
- **Started:** 2026-03-12T11:54:51Z
- **Completed:** 2026-03-12T12:03:53Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- 4 Python test files with 19 RED tests covering SOCIAL-01 through SOCIAL-05 (backend)
- 1 TypeScript test file with 11 RED tests covering SOCIAL-05 (scaffolder removal)
- `generate_test_apple_jwt()` RS256 test helper using `cryptography` library (already in pyproject.toml)
- `_make_apple_jwks_mock()` helper builds JWKS mock from RSA private key for audience-validation tests

## Task Commits

Each task was committed atomically:

1. **Task 1: Backend RED test stubs** - `78f51f9` (test)
2. **Task 2: TypeScript RED test stubs** - `71601ef` (test)

## Files Created/Modified

- `apps/api/tests/test_social_settings.py` — 10 tests for \_configure_social_providers() pure function (SOCIAL-01 + SOCIAL-02)
- `apps/api/tests/test_apple_auth.py` — 5 tests for verify_apple_identity_token() and handle_apple_login() (SOCIAL-03)
- `apps/api/tests/test_social_adapter.py` — 4 tests for FoundationSocialAccountAdapter relay email suppression (SOCIAL-04)
- `apps/api/tests/test_scaffolder_social_removal.py` — 1 integration test for removeSocialAuthModule() CLI (SOCIAL-05)
- `packages/create-foundation-app/tests/remove-social-auth.test.ts` — 11 unit tests for removeSocialAuthModule() TypeScript function (SOCIAL-05)

## Decisions Made

- **Per-test import gate pattern chosen**: `pytest.fail()` inside each test body (not at module level) — module-level `pytest.fail()` causes a collection ERROR that stops pytest from running any subsequent test files; per-test placement gives FAILED status allowing all tests to run
- **Import path corrected**: Plan specified `apps.api.config.settings.base` but pytest rootdir is `apps/api` with `python_paths=["."]`, so the correct import is `config.settings.base` (Rule 1 auto-fix)
- **generate_test_apple_jwt() uses cryptography library**: already a dependency in pyproject.toml — no new deps needed; generates fresh RSA key pairs per test call for isolation

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected import path for \_configure_social_providers**

- **Found during:** Task 1 (Backend RED test stubs)
- **Issue:** Plan specified `from apps.api.config.settings.base import _configure_social_providers` which fails because pytest rootdir is `apps/api` not the workspace root — the import caused a `ModuleNotFoundError: No module named 'apps.api'` stopping all test collection
- **Fix:** Changed import to `from config.settings.base import _configure_social_providers`
- **Files modified:** apps/api/tests/test_social_settings.py
- **Verification:** `uv run pytest tests/test_social_settings.py` ran and showed FAILED (not ERROR)
- **Committed in:** 78f51f9 (Task 1 commit)

**2. [Rule 1 - Bug] Switched to per-test import gates to avoid collection ERROR**

- **Found during:** Task 1 (Backend RED test stubs)
- **Issue:** Module-level `pytest.fail()` inside try/except ImportError causes an ERROR at collection time that stops pytest from collecting/running the other three test files — violates the "test commands run without import errors" requirement
- **Fix:** Moved all import attempts inside individual test functions so each test method independently fails as FAILED rather than causing collection ERROR
- **Files modified:** apps/api/tests/test_social_settings.py, test_apple_auth.py, test_social_adapter.py
- **Verification:** All 19 tests show as FAILED in pytest summary; no ERRORs; scaffolder test (which uses skipif) shows as FAILED separately
- **Committed in:** 78f51f9 (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (both Rule 1 - Bug)
**Impact on plan:** Both fixes necessary to meet the plan's own "no import errors" correctness requirement. No scope creep.

## Issues Encountered

- Pre-commit hook `detect-secrets` flagged test credential strings (`"test-google-secret"` etc.) as potential secrets — resolved by adding `# pragma: allowlist secret` inline comments
- Pre-commit `ruff format` reformatted files multiple times before commit succeeded — expected behavior for first-commit formatting pass

## Next Phase Readiness

- All 5 test files are in RED state and committed — Wave 2 implementation plans (20-02, 20-03) can reference these test files as verification targets
- The `_configure_social_providers` import path (`config.settings.base`) is confirmed for implementation plans
- The `apps.accounts.apple_auth` and `apps.accounts.social_adapter` import paths are confirmed for Wave 2/3 implementation
- `generate_test_apple_jwt()` helper is available in `test_apple_auth.py` for reuse in GREEN implementation tests

## Self-Check: PASSED

- apps/api/tests/test_social_settings.py: FOUND
- apps/api/tests/test_apple_auth.py: FOUND
- apps/api/tests/test_social_adapter.py: FOUND
- apps/api/tests/test_scaffolder_social_removal.py: FOUND
- packages/create-foundation-app/tests/remove-social-auth.test.ts: FOUND
- Commit 78f51f9: FOUND
- Commit 71601ef: FOUND

---

_Phase: 20-social-auth_
_Completed: 2026-03-12_
