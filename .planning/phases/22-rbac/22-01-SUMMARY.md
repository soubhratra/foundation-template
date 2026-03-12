---
phase: 22-rbac
plan: "01"
subsystem: accounts/tests
tags: [rbac, tdd, red-tests, permissions, django-groups]
dependency_graph:
  requires: []
  provides:
    - tests/accounts/test_rbac.py (14 RED test stubs)
    - admin_user fixture in tests/accounts/conftest.py
    - member_user fixture in tests/accounts/conftest.py
  affects:
    - Phase 22 Plans 02 and 03 (implementation will turn these GREEN)
tech_stack:
  added: []
  patterns:
    - Import-gate pattern (pytest.fail inside try/except ImportError) for RED stubs
    - Inline user creation helpers (_get_or_fail_admin_user) to avoid fixture ERROR on Group.DoesNotExist
key_files:
  created:
    - apps/api/tests/accounts/test_rbac.py
  modified:
    - apps/api/tests/accounts/conftest.py
decisions:
  - Inline helper functions instead of pytest fixtures for admin_user/member_user in test bodies — fixture-level Group.DoesNotExist produces ERROR not FAIL; inline helpers catch DoesNotExist and call pytest.fail() for readable RED output
  - Import-gate pattern applied to RequireRole and AdminController imports inside each test body — consistent with Phase 20/21 conventions
  - pytest.mark.django_db on each test method (not class) — matches existing test_deletion.py and test_export.py style
metrics:
  duration_seconds: 252
  completed_date: "2026-03-12"
  tasks_completed: 1
  files_modified: 2
---

# Phase 22 Plan 01: RBAC RED Test Stubs Summary

RED test stubs for all Phase 22 RBAC behaviors — 14 failing tests across 3 classes proving contracts before implementation.

## What Was Built

Created `apps/api/tests/accounts/test_rbac.py` with three test classes:

**TestRequireRole (3 tests — RBAC-01)**

- `test_admin_user_passes` — admin group member gets 200 from RequireRole("admin")
- `test_non_admin_gets_403` — member-only user gets 403
- `test_unauthenticated_gets_403` — anonymous request gets 403

**TestAdminController (8 tests — RBAC-02)**

- `test_list_users_admin` — GET /admin/users returns 200 for admin
- `test_list_users_non_admin` — GET /admin/users returns 403 for member
- `test_assign_role` — POST /{user_id}/roles returns 200
- `test_assign_unknown_role` — POST with bad role name returns 400
- `test_assign_role_to_self` — POST with own user_id returns 400
- `test_remove_role` — DELETE /{user_id}/roles/{role} returns 200
- `test_remove_role_non_admin` — DELETE by non-admin returns 403
- `test_get_user_roles` — GET /{user_id}/roles returns 200 + list

**TestSeedRolesMigration (3 tests — RBAC-03)**

- `test_admin_group_exists` — Group "admin" present after migrations
- `test_member_group_exists` — Group "member" present after migrations
- `test_migration_idempotent` — seed_roles() callable twice without error

Added `admin_user` and `member_user` fixtures to `apps/api/tests/accounts/conftest.py`.

## Verification

All 14 tests fail with `pytest.fail()` (no collection ERRORs):

```
======================== 14 failed, 1 warning in 2.18s =========================
```

Existing test suite unaffected (pre-existing billing test error is unrelated).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixture-level Group.DoesNotExist produces ERROR not FAIL**

- **Found during:** Task 1 verification
- **Issue:** When `admin_user` and `member_user` fixtures call `Group.objects.get(name="admin")` before migration 0003 exists, pytest reports `ERROR at setup` (not `FAILED`). The plan must_haves require FAIL not ERROR.
- **Fix:** Converted fixture usage to inline helper functions (`_get_or_fail_admin_user`, `_get_or_fail_member_user`) inside each test body. Each helper catches `Group.DoesNotExist` and calls `pytest.fail()` with an actionable message.
- **Files modified:** `apps/api/tests/accounts/test_rbac.py`
- **Commit:** c7771a8

The `admin_user` and `member_user` fixtures were still added to `conftest.py` as the plan specifies (they will be usable once migration 0003 exists and the groups are seeded).

## Self-Check

Files created:

- apps/api/tests/accounts/test_rbac.py — FOUND
- apps/api/tests/accounts/conftest.py (modified) — FOUND

Commits:

- c7771a8 test(22-01): add RED test stubs for RBAC-01, RBAC-02, RBAC-03 — FOUND

## Self-Check: PASSED
