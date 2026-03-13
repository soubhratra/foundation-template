---
phase: 26-organization-model-per-org-billing
plan: 03
subsystem: api
tags: [django, permissions, orgs, b2b, ninja-extra, multi-tenant]

# Dependency graph
requires:
  - phase: 26-organization-model-per-org-billing
    plan: 02
    provides: "Organization, Membership, Invitation, OrgCustomer models and migrations"
provides:
  - "IsOrgMember BasePermission class in apps/orgs/permissions.py"
  - "IsOrgAdmin BasePermission class in apps/orgs/permissions.py"
  - "Both permission tests in tests/orgs/test_permissions.py GREEN"
affects:
  - 26-05-controllers
  - any future plan adding org-scoped endpoints

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "IsOrgMember sets request.org on success for downstream permissions to read without re-querying"
    - "Http404 used for both org-not-found and non-member — prevents org existence leakage"
    - "IsOrgAdmin falls back to org_slug lookup when request.org is not an Organization instance (supports unit test isolation)"

key-files:
  created:
    - apps/api/apps/orgs/permissions.py
  modified: []

key-decisions:
  - "IsOrgAdmin falls back to org_slug kwargs lookup when request.org is not a real Organization instance — required by test contract (tests are authoritative)"
  - "Http404 raised for both unknown org and non-member to prevent org existence leakage to unauthenticated/unauthorized users"
  - "raise Http404 from None in except clause to satisfy ruff B904 rule without chaining the DoesNotExist exception"

patterns-established:
  - "Composition order: permissions=[IsAuthenticated, IsOrgMember, IsOrgAdmin] — IsOrgAdmin MUST follow IsOrgMember"
  - "IsOrgAdmin guard: if request.org is not an Organization instance, return False (not raise) to avoid leaking implementation details"

requirements-completed:
  - ORG-03
  - ORG-05

# Metrics
duration: 8min
completed: 2026-03-13
---

# Phase 26 Plan 03: Org Permission Classes Summary

**`IsOrgMember` and `IsOrgAdmin` Django Ninja Extra permission classes with Http404/PermissionDenied security boundaries and `request.org` propagation pattern**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-03-13T03:00:00Z
- **Completed:** 2026-03-13T03:08:00Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- `IsOrgMember` — raises Http404 for unknown orgs and non-members (prevents org existence leakage), sets `request.org` on success
- `IsOrgAdmin` — raises PermissionDenied for member-role users, composes with IsOrgMember via `request.org` pattern
- Both `test_non_member_gets_404` and `test_member_role_admin_endpoint_gets_403` pass GREEN
- Ruff B904 linting compliance (`raise Http404 from None`)

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement IsOrgMember and IsOrgAdmin, turn permission tests GREEN** - `272e239` (feat)

**Plan metadata:** (docs commit — see final commit)

## Files Created/Modified

- `apps/api/apps/orgs/permissions.py` — IsOrgMember and IsOrgAdmin BasePermission classes

## Decisions Made

- IsOrgAdmin falls back to org_slug kwargs lookup when `request.org` is not a real Organization instance. The test `test_member_role_admin_endpoint_gets_403` calls `IsOrgAdmin` directly (no prior `IsOrgMember` call), so `request.org` is a MagicMock auto-attribute. Django ORM cannot filter by a MagicMock, causing a TypeError. The fallback resolves org via `org_slug` so the test can verify the PermissionDenied path. **Tests are authoritative** — the plan noted this, and the implementation adapts to honor the test contract.
- `raise Http404 from None` in the DoesNotExist except clause to satisfy ruff B904 (exception chaining clarity). The None suppresses the original exception, which is intentional — we do not want to leak that `DoesNotExist` was raised.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] IsOrgAdmin org resolution for unit test isolation**

- **Found during:** Task 1 (running tests GREEN)
- **Issue:** `request.org` is a MagicMock auto-attribute when `IsOrgAdmin` is called without prior `IsOrgMember`. Django ORM's `Membership.objects.filter(org=MagicMock, ...)` raises `TypeError: Field 'id' expected a number but got []` instead of the expected `PermissionDenied`.
- **Fix:** Added `isinstance(org, Organization)` check; when org is not a real Organization, fall back to `org_slug` lookup from URL kwargs. This matches the test's setup which provides `org_slug` in kwargs.
- **Files modified:** apps/api/apps/orgs/permissions.py
- **Verification:** Both permission tests pass GREEN; ruff passes
- **Committed in:** `272e239` (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 — bug in initial implementation)
**Impact on plan:** Required for test contract correctness. The fallback also makes IsOrgAdmin more robust in edge cases. No scope creep.

## Issues Encountered

- Pre-commit ruff B904 hook blocked first commit attempt — fixed with `raise Http404 from None` in the except clause.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `IsOrgMember` and `IsOrgAdmin` are ready for use in org-scoped controllers (Plan 05)
- Import: `from apps.orgs.permissions import IsOrgMember, IsOrgAdmin`
- Composition rule documented in `IsOrgAdmin` class docstring: always use `[IsAuthenticated, IsOrgMember, IsOrgAdmin]`

---

_Phase: 26-organization-model-per-org-billing_
_Completed: 2026-03-13_
