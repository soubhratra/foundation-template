---
phase: 26-organization-model-per-org-billing
plan: "01"
subsystem: orgs/tests
tags: [tdd, red-tests, orgs, billing, permissions]
dependency_graph:
  requires: []
  provides:
    - tests/orgs/ test package (RED stubs for all org model tests)
    - BILL-02 stubs appended to tests/core/test_entitlements.py
    - BILL-02 stub appended to tests/billing/test_tasks.py
  affects:
    - apps/api/tests/orgs/
    - apps/api/tests/core/test_entitlements.py
    - apps/api/tests/billing/test_tasks.py
tech_stack:
  added: []
  patterns:
    - pytest fixtures with module-top-level imports for guaranteed RED collection failure
    - lazy imports in test bodies to avoid breaking existing test files
    - pragma allowlist secret comments for test passwords
key_files:
  created:
    - apps/api/tests/orgs/__init__.py
    - apps/api/tests/orgs/conftest.py
    - apps/api/tests/orgs/test_models.py
    - apps/api/tests/orgs/test_services.py
    - apps/api/tests/orgs/test_permissions.py
    - apps/api/tests/orgs/test_controllers.py
  modified:
    - apps/api/tests/core/test_entitlements.py
    - apps/api/tests/billing/test_tasks.py
decisions:
  - "Use module-top-level imports in tests/orgs/ conftest and test files so collection fails immediately with ImportError (not lazily at runtime) — produces clean RED state"
  - "Use lazy imports inside BILL-02 test bodies in existing test files (not top-level) — prevents breaking the existing 10 passing tests in those files"
  - "conftest.py defines org_owner, org, org_membership, invitation fixtures shared across all tests/orgs/ test files"
  - "test_controllers.py uses Django test client (Client) rather than ninja_extra utilities — simpler and already available"
metrics:
  duration_seconds: 277
  completed_date: "2026-03-13"
  tasks_completed: 3
  files_created: 6
  files_modified: 2
---

# Phase 26 Plan 01: RED Test Stubs for Org Model + Per-Org Billing Summary

**One-liner:** RED TDD stubs for all 7 org/billing requirement IDs across 6 new test files and 2 appended files — ImportError-based failures confirm apps.orgs does not yet exist.

## What Was Built

Created the complete test contract for Phase 26 before any implementation begins. All tests fail at collection time (ImportError: No module named 'apps.orgs') which is the correct RED state for TDD — it proves the implementation modules don't exist yet and every requirement has a failing automated check.

### Tests Created

**tests/orgs/ package (6 files):**

| File                  | Requirement             | Tests                                                                                                                                                                                             |
| --------------------- | ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `__init__.py`         | —                       | Empty package marker                                                                                                                                                                              |
| `conftest.py`         | —                       | Fixtures: org_owner, org, org_membership, invitation                                                                                                                                              |
| `test_models.py`      | ORG-01, BILL-01, ORG-02 | test_org_slug_unique, test_org_customer_auto_created, test_invitation_is_valid_false_after_expiry                                                                                                 |
| `test_services.py`    | ORG-01, ORG-02, ORG-04  | test_create_org_creates_owner_membership, test_invite_sends_email, test_invite_token_expiry, test_invite_accept_email_mismatch, test_invite_accept_new_user_session_flow, test_transfer_ownership |
| `test_permissions.py` | ORG-03                  | test_non_member_gets_404, test_member_role_admin_endpoint_gets_403                                                                                                                                |
| `test_controllers.py` | ORG-05                  | test_cross_org_access_forbidden                                                                                                                                                                   |

**Appended to existing files (BILL-02):**

| File                              | Tests Added                                                                            |
| --------------------------------- | -------------------------------------------------------------------------------------- |
| `tests/core/test_entitlements.py` | test_has_org_feature_org_plan_takes_precedence, test_has_org_feature_personal_fallback |
| `tests/billing/test_tasks.py`     | test_subscription_updated_invalidates_org_caches                                       |

### Verification Results

- `pytest tests/orgs/ -x` → fails with `ModuleNotFoundError: No module named 'apps.orgs'` (correct RED state)
- `pytest tests/core/test_entitlements.py tests/billing/test_tasks.py` → 3 new stubs fail, 10 existing tests pass
- All 6 new test files are syntactically valid Python

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Pre-commit hook: ruff E501 line-too-long in docstrings**

- **Found during:** Task 1, Task 2, Task 3 commits
- **Issue:** Docstring lines exceeded 100-character ruff limit
- **Fix:** Shortened docstring text to stay within line length limit
- **Files modified:** test_services.py, test_entitlements.py
- **Commits:** 501817e, 326a6b6

**2. [Rule 1 - Bug] Pre-commit hook: detect-secrets flagged "testpass123" as potential secret**

- **Found during:** Task 1 commit
- **Issue:** detect-secrets hook triggered on test password strings in conftest.py and test_models.py
- **Fix:** Added `# pragma: allowlist secret` comments to all test password lines (standard pattern for known-safe test credentials)
- **Files modified:** conftest.py, test_models.py, test_services.py, test_permissions.py, test_controllers.py
- **Commit:** 813605f

## Deferred Issues (Out of Scope)

Discovered during overall verification run (`pytest tests/ --ignore=tests/orgs/`):

- **tests/billing/test_services.py** — 12 pre-existing ERRORs in billing service tests
- These errors existed before this plan and are unrelated to orgs test stubs
- Logged as pre-existing technical debt; no action taken

## Self-Check: PASSED

All 8 files exist. All 3 task commits verified (813605f, 501817e, 326a6b6).
