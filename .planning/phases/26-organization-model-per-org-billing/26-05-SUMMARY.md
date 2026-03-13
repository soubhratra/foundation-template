---
phase: 26-organization-model-per-org-billing
plan: "05"
subsystem: api
tags: [django, ninja-extra, orgs, controllers, schemas, permissions, b2b]

# Dependency graph
requires:
  - phase: 26-03
    provides: IsOrgMember, IsOrgAdmin permission classes
  - phase: 26-04
    provides: OrgService, MembershipService, InvitationService

provides:
  - schemas.py with 8 schema classes (OrgIn, OrgOut, OrgUpdateIn, MemberOut, RoleUpdateIn, TransferOwnershipIn, InviteIn, InviteOut, AcceptInviteOut)
  - OrgController — POST/GET/PATCH/DELETE /api/v1/org/{slug}/
  - MembershipController — GET/PATCH/DELETE members, POST transfer-ownership
  - InvitationController — POST/DELETE invitations, GET invitations/accept/
  - All 11 org endpoints registered via auto_discover_controllers()

affects:
  - 26-06-billing-integration (uses OrgOut schema; org endpoints available for integration testing)
  - future phases (27+) extending org management features
  - web/mobile frontend (all org endpoints now reachable)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Three @api_controller classes with prefix='/org' — auto-discovered by NinjaExtraAPI.auto_discover_controllers()"
    - "Per-route permissions override — create_org uses only IsAuthenticated; member endpoints add IsOrgMember; admin endpoints add IsOrgAdmin"
    - "Controller methods are thin wrappers — 0 ORM queries in controllers, all logic in service layer"
    - "OrgIn.slug validated at API boundary with field_validator; service also normalizes to lowercase (defence in depth)"
    - "InviteOut.invited_email maps from Invitation.email — field renaming handled in controller, not schema model_validator"

key-files:
  created:
    - apps/api/apps/orgs/schemas.py
    - apps/api/apps/orgs/controllers.py
  modified: []

key-decisions:
  - "MemberOut.joined_at maps from membership.created_at — schema field named joined_at for API clarity, not created_at"
  - "InviteOut.invited_email maps from invitation.email — name makes semantic intent clear for API consumers"
  - "accept_invite endpoint has no IsAuthenticated permission gate — unauthenticated users get session token + redirect"
  - "B904 (raise-without-from-none) enforced by ruff in except clauses — all Http404 raises in DoesNotExist handlers use from None"

patterns-established:
  - "Schema field aliasing: schema field named differently from model field — mapping done in controller return statement"
  - "Per-route permission override: @route.get(..., permissions=[...]) overrides controller-level permissions for mixed-auth endpoints"

requirements-completed: [ORG-01, ORG-02, ORG-03, ORG-04, ORG-05]

# Metrics
duration: 4min
completed: 2026-03-13
---

# Phase 26 Plan 05: Org Controllers and Schemas Summary

**Django Ninja Extra controllers for all 11 org endpoints — OrgIn/OrgOut schemas with slug validation, thin controller layer delegating to Plan 04 services, auto-discovered via NinjaExtraAPI**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-13T03:22:49Z
- **Completed:** 2026-03-13T03:27:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- 8 schema classes in schemas.py — OrgIn (slug validator), OrgOut, OrgUpdateIn, MemberOut (joined_at alias), RoleUpdateIn, TransferOwnershipIn, InviteIn, InviteOut (invited_email alias), AcceptInviteOut
- 3 controller classes implementing all 11 org endpoints; correct IsAuthenticated + IsOrgMember + IsOrgAdmin permission composition per endpoint
- All 12 orgs tests GREEN after controller implementation (model + permissions + services + controllers)
- `manage.py check` clean (warnings only — pre-existing allauth deprecation warnings unrelated to this plan)

## Task Commits

1. **Task 1: Create schemas.py** - `653599e` (feat)
2. **Task 2: Implement controllers and wire URL config** - `e5e076a` (feat)

## Files Created/Modified

- `apps/api/apps/orgs/schemas.py` — 8 schema classes; OrgIn with slug field_validator rejecting non-lowercase-alphanumeric-hyphen slugs
- `apps/api/apps/orgs/controllers.py` — OrgController, MembershipController, InvitationController; all 11 endpoints; auto-discovered by NinjaExtraAPI

## Decisions Made

- `MemberOut.joined_at` maps from `membership.created_at` — naming is more API-consumer-friendly than `created_at`
- `InviteOut.invited_email` maps from `invitation.email` — the field rename makes the invitation direction explicit
- `accept_invite` has no IsAuthenticated gate — unauthenticated users receive `{redirect: "/signup?invite_pending=1"}` and token stored in session; this matches the Plan 04 InvitationService.accept() contract
- No explicit import of `apps.orgs.controllers` needed in urls.py — `auto_discover_controllers()` imports all `controllers` submodules of installed apps, and `apps.orgs` is in INSTALLED_APPS

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed ruff B904 violations on Http404 raises in except clauses**

- **Found during:** Task 2 (pre-commit hook)
- **Issue:** Three `raise Http404` statements inside `except User.DoesNotExist:` blocks lacked `from None` — ruff B904 requires explicit chaining to distinguish from errors in exception handling
- **Fix:** Added `from None` to all three raises: `raise Http404 from None`
- **Files modified:** `apps/api/apps/orgs/controllers.py`
- **Verification:** ruff check passes; pre-commit hook passes
- **Committed in:** `e5e076a` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 linting/style fix)
**Impact on plan:** Minor style correction required by ruff linter. No logic changes.

## Issues Encountered

- `uv run python -c "from apps.orgs.schemas import ..."` failed without DJANGO_SETTINGS_MODULE — ninja imports require Django settings at module load. Fixed by setting DJANGO_SETTINGS_MODULE=config.settings.development in verification commands.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- All 11 org endpoints are registered and reachable; controllers delegate to Plan 04 services
- Phase 26-06 (billing integration) can now wire OrgCustomer to stripe using the available OrgService and org endpoint infrastructure
- Phase 27+ can extend org billing by adding per-org Subscription lookups in `_resolve_org_plan_id`

---

_Phase: 26-organization-model-per-org-billing_
_Completed: 2026-03-13_
