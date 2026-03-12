---
phase: 22-rbac
plan: "02"
subsystem: accounts/permissions
tags: [rbac, django-groups, permissions, ninja-extra, tdd, migration]

requires:
  - phase: 22-rbac-01
    provides: RED test stubs for TestRequireRole and TestSeedRolesMigration

provides:
  - apps/api/apps/accounts/permissions.py (RequireRole BasePermission + KNOWN_ROLES)
  - apps/api/apps/accounts/migrations/migration_0003_seed_roles.py (admin/member Groups seeded)
  - apps/api/apps/accounts/controllers.py (AdminController stub for test vehicle)

affects:
  - Phase 22-03 (AdminController full implementation uses RequireRole and seeded groups)

tech-stack:
  added: []
  patterns:
    - "RequireRole returns False from has_permission (not raise) — ninja_extra converts False to 403 HttpError, TestClient handles it cleanly"
    - "Migration named migration_0003_seed_roles.py (not 0003_) so Python import system can import seed_roles() function for idempotency tests"
    - "AdminController stub with no auth= at controller level — RequireRole is sole gate so TestClient does not return 401 before permission check"

key-files:
  created:
    - apps/api/apps/accounts/permissions.py
    - apps/api/apps/accounts/migrations/migration_0003_seed_roles.py
  modified:
    - apps/api/apps/accounts/controllers.py

key-decisions:
  - "RequireRole.has_permission returns False (not raise PermissionDenied) — ninja_extra calls permission_denied() which raises HttpError 403, handled by TestClient's default HttpError handler"
  - "Migration file named migration_0003_seed_roles.py — Django discovers it via filesystem scan; Python import system imports seed_roles() as apps.accounts.migrations.migration_0003_seed_roles"
  - "AdminController stub added in 22-02 (not 22-03) as test vehicle for TestRequireRole — without it TestRequireRole tests fail at ImportError gate, blocking the RED→GREEN cycle"
  - "AdminController stub has no auth= parameter — auth=[SessionAuth(), jwt_token_auth] would fire before permissions and return 401 for unauthenticated tests expecting 403"

patterns-established:
  - "RequireRole pattern: return False from has_permission, not raise — consistent with ninja_extra's permission_denied() flow"
  - "Migration idempotency via get_or_create: seed_roles() callable twice without IntegrityError"

requirements-completed:
  - RBAC-01
  - RBAC-03

duration: 9min
completed: "2026-03-12"
---

# Phase 22 Plan 02: RequireRole Permission Class and Seed Roles Migration Summary

**RequireRole BasePermission class gating Django Group membership, plus data migration seeding admin/member Groups via get_or_create — 6 tests GREEN (3 TestRequireRole + 3 TestSeedRolesMigration)**

## Performance

- **Duration:** 9 min
- **Started:** 2026-03-12T20:55:42Z
- **Completed:** 2026-03-12T21:04:15Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- RequireRole(BasePermission) implemented — checks user's Django Group membership, returns False for non-members and anonymous users
- KNOWN_ROLES frozenset containing exactly {"admin", "member"} exported from permissions.py
- Data migration `migration_0003_seed_roles.py` seeds admin and member Groups via get_or_create (idempotent)
- Minimal AdminController stub added as test vehicle so TestRequireRole tests can verify permission behavior
- 6/6 target tests GREEN; 8 TestAdminController tests still RED (expected for plan 22-03)

## Task Commits

1. **Task 1: RequireRole permission class** - `6a633ea` (feat)
2. **Task 2: Seed roles migration** - `abbf11e` (feat)

**Plan metadata:** (committed with this SUMMARY)

## Files Created/Modified

- `apps/api/apps/accounts/permissions.py` — RequireRole class + KNOWN_ROLES frozenset
- `apps/api/apps/accounts/migrations/migration_0003_seed_roles.py` — seeds admin/member Groups
- `apps/api/apps/accounts/controllers.py` — added AdminController stub (no auth, RequireRole only)

## Decisions Made

- RequireRole.has_permission returns False rather than raising `django.core.exceptions.PermissionDenied` — ninja_extra converts False to `ninja_extra.exceptions.PermissionDenied` (an HttpError with status 403), which the TestClient handles natively via its default HttpError handler. Raising `django.core.exceptions.PermissionDenied` directly would bubble unhandled in the TestClient context (that exception handler is only registered on the production `api` instance in `config/urls.py`).
- Migration file named `migration_0003_seed_roles.py` rather than `0003_seed_roles.py` — Django discovers migrations via filesystem scan so the `migration_` prefix is fine. The Python import system requires a valid identifier for direct import; the idempotency test imports `seed_roles` as `from apps.accounts.migrations.migration_0003_seed_roles import seed_roles`.
- AdminController stub created in 22-02 as a side effect of making TestRequireRole GREEN — the test stubs (from 22-01) import AdminController inside each test body to use it as the test vehicle. Without AdminController existing, all three TestRequireRole tests fail at the ImportError gate.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] AdminController stub required for TestRequireRole test vehicle**

- **Found during:** Task 1 (RequireRole implementation verification)
- **Issue:** TestRequireRole tests import AdminController from apps.accounts.controllers inside the test body to use as a test surface for RequireRole. AdminController doesn't exist until plan 22-03. All 3 TestRequireRole tests fail at the ImportError gate with "AdminController not found" even after permissions.py exists.
- **Fix:** Added minimal AdminController stub to controllers.py with `permissions=[RequireRole("admin")]` and a single `GET /` list_users endpoint. No `auth=` specified so the TestClient does not return 401 before the permission check.
- **Files modified:** apps/api/apps/accounts/controllers.py
- **Verification:** TestRequireRole 3/3 pass; TestAdminController list_users tests also pass (bonus)
- **Committed in:** 6a633ea (Task 1 commit)

**2. [Rule 1 - Bug] RequireRole.has_permission returns False instead of raising**

- **Found during:** Task 1 verification (non_admin and unauthenticated tests failing)
- **Issue:** Plan specified `raise PermissionDenied("Insufficient role.")` using `django.core.exceptions.PermissionDenied`. This exception is registered as a handler on the production `api` instance but not on the fresh NinjaExtraAPI created by TestClient. The exception bubbles unhandled from TestClient (non-admin got an exception traceback, unauthenticated got 401 from auth layer).
- **Fix:** Changed `has_permission` to return False. ninja_extra calls `controller.permission_denied()` which raises `ninja_extra.exceptions.PermissionDenied` (HttpError 403), handled by the default HttpError handler. For unauthenticated case: removed `auth=` from the stub so the auth layer does not return 401 before RequireRole runs.
- **Files modified:** apps/api/apps/accounts/permissions.py
- **Verification:** All 3 TestRequireRole tests pass (admin→200, non-admin→403, anon→403)
- **Committed in:** 6a633ea (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Both fixes necessary for tests to pass as specified. No scope creep — AdminController stub is the minimal test vehicle; full implementation deferred to 22-03.

## Issues Encountered

None beyond the deviations documented above.

## User Setup Required

None - no external service configuration required. Migration applied automatically during task execution.

## Next Phase Readiness

- RequireRole and KNOWN_ROLES ready for use in AdminController (plan 22-03)
- admin and member Django Groups exist in the database
- AdminController stub in place — 22-03 can flesh it out with full endpoints
- TestAdminController 8 tests still RED (expected); 2 list_users tests GREEN from stub

---

_Phase: 22-rbac_
_Completed: 2026-03-12_
