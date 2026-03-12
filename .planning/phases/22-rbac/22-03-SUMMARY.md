---
phase: 22-rbac
plan: "03"
subsystem: accounts/rbac
tags: [rbac, django-groups, ninja-extra, permissions, admin-api, tdd]

requires:
  - phase: 22-rbac-02
    provides: RequireRole permission class, KNOWN_ROLES frozenset, AdminController stub, seeded admin/member Groups

provides:
  - apps/api/apps/accounts/schemas.py (AdminUserOut, RoleAssignIn, UserRoleOut schemas)
  - apps/api/apps/accounts/services.py (list_users, get_user_roles, assign_role, remove_role on UserService)
  - apps/api/apps/accounts/controllers.py (full AdminController with 4 endpoints)

affects:
  - Future phases using admin role management endpoints

tech-stack:
  added: []
  patterns:
    - "AdminController GET /{id}/roles returns list[str] directly (not UserRoleOut) — test asserts isinstance(data, list) on the JSON response body"
    - "UserService role methods use prefetch_related('groups') in list_users to avoid N+1 — nplusone guard would catch violations in tests"
    - "assign_role and remove_role are idempotent — add/remove via Django Groups with silent DoesNotExist handling"

key-files:
  created: []
  modified:
    - apps/api/apps/accounts/schemas.py
    - apps/api/apps/accounts/services.py
    - apps/api/apps/accounts/controllers.py

key-decisions:
  - "GET /admin/users/{id}/roles returns list[str] (not UserRoleOut) — test_get_user_roles asserts isinstance(response.json(), list); UserRoleOut dict would fail that check"
  - "AdminController keeps no auth= at controller level (consistent with 22-02 stub pattern) — RequireRole is sole gate; production auth happens via Django middleware before ninja processes the request"
  - "list_users uses prefetch_related('groups') in UserService.list_users — required by nplusone guard in tests/conftest.py"

patterns-established:
  - "Role management via Django Groups: assign = user.groups.add(group), remove = user.groups.remove(group) — idempotent by default"
  - "400 guards on role endpoints: unknown role and self-modify checks before any service call — fail fast before DB round-trip"

requirements-completed:
  - RBAC-02

duration: 6min
completed: "2026-03-12"
---

# Phase 22 Plan 03: AdminController — Role Management Endpoints Summary

**AdminController with 4 REST endpoints for admin role management via Django Groups — all 14 RBAC tests GREEN completing RBAC-01, RBAC-02, and RBAC-03**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-12T21:05:55Z
- **Completed:** 2026-03-12T21:11:49Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- AdminUserOut, RoleAssignIn, UserRoleOut schemas added to accounts/schemas.py
- list_users, get_user_roles, assign_role, remove_role methods added to UserService
- Full AdminController replaces Plan 02 stub — 4 endpoints at /admin/users
- All 14 test_rbac.py tests GREEN (3 TestRequireRole + 8 TestAdminController + 3 TestSeedRolesMigration)
- Full regression suite passes (29 tests, no regressions from RBAC changes)

## Task Commits

1. **Task 1: Add AdminUserOut, RoleAssignIn, UserRoleOut schemas and role service methods** - `9361d2e` (feat)
2. **Task 2: Implement AdminController with 4 endpoints** - `8cd4795` (feat)

**Plan metadata:** (committed with this SUMMARY)

## Files Created/Modified

- `apps/api/apps/accounts/schemas.py` — AdminUserOut, RoleAssignIn, UserRoleOut schemas added
- `apps/api/apps/accounts/services.py` — list_users, get_user_roles, assign_role, remove_role added to UserService
- `apps/api/apps/accounts/controllers.py` — AdminController stub replaced with full 4-endpoint implementation

## Decisions Made

- GET `/admin/users/{id}/roles` returns `list[str]` directly rather than `UserRoleOut` — the test at `test_get_user_roles` calls `isinstance(response.json(), list)` expecting a bare JSON array; `UserRoleOut` would return a dict which would fail. The plan spec and test were inconsistent; test is source of truth.
- AdminController retains no `auth=` parameter (consistent with the 22-02 stub decision) — `RequireRole` handles both unauthenticated (anonymous users return `is_authenticated=False`) and non-admin cases. Production Django middleware sets `request.user` before ninja processes the request.
- `UserService.list_users` uses `prefetch_related("groups")` — required by the nplusone guard in `tests/conftest.py`; also used when constructing `UserRoleOut` in assign/remove endpoints via `user.groups.all()` (post-mutation, single query).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] GET roles endpoint returns list[str] not UserRoleOut**

- **Found during:** Task 2 (reading test assertions before implementing)
- **Issue:** Plan specifies `response=UserRoleOut` for `GET /{user_id}/roles`, but `test_get_user_roles` asserts `isinstance(response.json(), list)` — a dict (`UserRoleOut`) would fail this check
- **Fix:** Changed response type to `list[str]` and returns `self.service.get_user_roles(user_id=user_id)` directly
- **Files modified:** apps/api/apps/accounts/controllers.py
- **Verification:** `test_get_user_roles` passes — response is JSON array
- **Committed in:** 8cd4795 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug — plan/test inconsistency)
**Impact on plan:** Fix required to satisfy test assertions. No scope creep — all other endpoints follow the plan exactly.

## Issues Encountered

- Ruff pre-commit hook reformatted line-too-long errors (>100 chars) in two commits — required re-staging after auto-format. Not a code issue.
- Pre-existing `billing/test_controllers.py::test_get_subscription` nplusone failure is unrelated to RBAC — documented in `deferred-items.md`.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- RBAC complete: RequireRole (RBAC-01), AdminController (RBAC-02), Seed migration (RBAC-03) all satisfied
- Phase 22 fully complete — all 14 RBAC tests GREEN
- Phase 23 (Entitlements) can begin

---

_Phase: 22-rbac_
_Completed: 2026-03-12_

## Self-Check: PASSED

- apps/api/apps/accounts/schemas.py — FOUND
- apps/api/apps/accounts/services.py — FOUND
- apps/api/apps/accounts/controllers.py — FOUND
- .planning/phases/22-rbac/22-03-SUMMARY.md — FOUND
- commit 9361d2e (feat: AdminUserOut/RoleAssignIn/UserRoleOut schemas + role service methods) — FOUND
- commit 8cd4795 (feat: AdminController with 4 endpoints) — FOUND
- 14/14 test_rbac.py tests GREEN
