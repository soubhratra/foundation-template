---
phase: 34-admin-audit-context-fixes
plan: 02
subsystem: api
tags: [pghistory, audit, api-keys, django-orm, select_related, nplusone]

# Dependency graph
requires:
  - phase: 29-audit-logging
    provides: audit_context() context manager + get_audit_log_page selector
  - phase: 28-api-key-authentication
    provides: APIKey model, APIKeyService, APIKeyController
  - phase: 26-organization-model-per-org-billing
    provides: Organization model + Membership model

provides:
  - Nullable APIKey.org FK (SET_NULL, to orgs.Organization)
  - Migration 0003_apikey_org (pgtrigger-aware, with pragma comments)
  - APIKey events appear in org audit log when key created/revoked with org_slug
  - org_slug field in APIKeyIn (input), APIKeyOut (list), APIKeyCreateOut (create response)
  - Backward-compatible: callers omitting org_slug get personal key (org=None)

affects:
  - future api-key management UI (web/mobile — expects org_slug in list responses)
  - any future phase reading APIKey model schema
  - nplusone whitelist pattern for nullable FK eager loads

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Service-layer audit_context() wrapping for non-org-routed endpoints (extends Phase 29 Celery pattern to HTTP service layer)
    - select_related("org") + org_id guard (k.org.slug if k.org_id else None) — N+1-safe nullable FK serialization
    - nplusone Profiler whitelist entry for select_related on nullable FK fields to suppress false-positive eager load detection in tests

key-files:
  created:
    - apps/api/apps/api_keys/migrations/0003_apikey_org.py
  modified:
    - apps/api/apps/api_keys/models.py
    - apps/api/apps/api_keys/schemas.py
    - apps/api/apps/api_keys/services.py
    - apps/api/apps/api_keys/controllers.py
    - apps/api/tests/api_keys/conftest.py
    - apps/api/tests/api_keys/test_controllers.py
    - apps/api/tests/conftest.py

key-decisions:
  - "APIKey.org FK is nullable (SET_NULL) — personal keys (org=None) are a valid use case, not an error state"
  - "audit_context() wrapping in service layer (not controller) matches Phase 29 Celery task pattern — controller stays thin"
  - "Membership check in controller (not service) — controllers own HTTP authorization; services are domain-agnostic"
  - "nplusone Profiler whitelist for APIKey.org: select_related is correct for production paths with org keys; false positive only fires in tests using personal-key fixtures"
  - "pragma allowlist secret on pgtrigger hash= lines after ruff reformatts migration to multi-line style (not inline)"

patterns-established:
  - "Service-layer audit_context() injection: use for any HTTP endpoint NOT routed through /{org_slug}/ that mutates org-owned resources"
  - "Nullable FK serialization: k.related.field if k.related_id else None (avoids AttributeError on NULL FK without extra query)"
  - "nplusone whitelist entry format: {label: unused_eager_load, model: ModelName, field: field_name} in tests/conftest.py _NPLUSONE_WHITELIST"

requirements-completed: [AUDIT-01]

# Metrics
duration: 25min
completed: 2026-03-14
---

# Phase 34 Plan 02: Admin Audit Context Fixes — APIKey Org Audit Integration Summary

**Nullable APIKey.org FK + service-layer audit_context() injection closes AUDIT-01: /me/api-keys/ create and revoke events now appear in the org audit log when an org_slug is provided**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-03-14T01:03:00Z
- **Completed:** 2026-03-14T01:23:00Z
- **Tasks:** 2 (TDD: RED stubs + GREEN implementation)
- **Files modified:** 8

## Accomplishments

- Added nullable `APIKey.org` FK to Organization with migration 0003 (pgtrigger-aware, with pragma comments on hash= lines)
- Updated `APIKeyService.create()` and `revoke()` to wrap DB mutations in `audit_context(user_id, org_id)` so events appear in org audit log
- Added `select_related("org")` to `list_for_user()` and `org_slug` to all 3 schemas — backward compatible, no breaking change
- Controller resolves org from `org_slug` with membership authorization check (Http404/PermissionDenied)
- All 4 new AUDIT-01 integration tests GREEN; full suite (324 passed, 1 skipped) GREEN

## Task Commits

Each task was committed atomically:

1. **Task 1: Add RED test stubs for audit context integration** - `71a7b06` (test)
2. **Task 2: Add org FK, update schemas/service/controller, run migration** - `17e2313` (feat)

**Plan metadata:** (docs commit follows)

_Note: TDD — Task 1 wrote 4 failing tests, Task 2 made them all pass_

## Files Created/Modified

- `apps/api/apps/api_keys/migrations/0003_apikey_org.py` — Nullable AddField for APIKey.org + pgtrigger remove/re-add cycle (correct for trigger SQL update)
- `apps/api/apps/api_keys/models.py` — Added `org = models.ForeignKey("orgs.Organization", SET_NULL, null=True, blank=True)`
- `apps/api/apps/api_keys/schemas.py` — Added `org_slug: str | None` to APIKeyIn (optional input), APIKeyOut, APIKeyCreateOut
- `apps/api/apps/api_keys/services.py` — Added `audit_context` import; `create()` + `revoke()` wrapped in `audit_context(user_id, org_id)`; `list_for_user()` uses `select_related("org")`
- `apps/api/apps/api_keys/controllers.py` — `create_key()` resolves org from org_slug + membership check; 201 response includes org_slug; `list_keys()` passes `org_slug=k.org.slug if k.org_id else None`
- `apps/api/tests/api_keys/conftest.py` — Added `org_for_apikey` fixture (lazy imports pattern)
- `apps/api/tests/api_keys/test_controllers.py` — Added 4 AUDIT-01 integration tests
- `apps/api/tests/conftest.py` — Added `_NPLUSONE_WHITELIST` with `APIKey.org` entry; Profiler now uses whitelist

## Decisions Made

- Service-layer `audit_context()` wrapping (not controller) follows Phase 29 Celery task pattern — controllers own HTTP auth/authorization, services own domain mutations with audit context
- Membership check stays in controller because it's an HTTP authorization concern (PermissionDenied maps to 403); service stays domain-agnostic
- `APIKey.org` FK is nullable by design — personal API keys (no org) remain valid and backward-compatible
- nplusone `Profiler` whitelist added for `APIKey.org` because `select_related("org")` is the correct production optimization (prevents N+1 when listing org-associated keys), but tests that use personal-key fixtures trigger a false-positive "unused eager load"

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] nplusone false-positive eager load on APIKey.org**

- **Found during:** Task 2 (running api_keys test suite)
- **Issue:** `tests/conftest.py` uses `Profiler()` (full profiler with EagerListener). `select_related("org")` on a queryset where all keys have `org_id=NULL` triggers an "unused eager load" error because `k.org` is never accessed (guarded by `k.org_id`). This is a false positive — the eager load IS correct for production paths with org-associated keys.
- **Fix:** Added `_NPLUSONE_WHITELIST = [{"label": "unused_eager_load", "model": "APIKey", "field": "org"}]` to `tests/conftest.py` and passed it to `Profiler(whitelist=_NPLUSONE_WHITELIST)`
- **Files modified:** `apps/api/tests/conftest.py`
- **Verification:** All 42 api_keys tests and 324-test full suite pass with no NPlusOneError
- **Committed in:** `17e2313` (Task 2 commit)

**2. [Rule 3 - Blocking] pragma allowlist secret placement after ruff reformatting**

- **Found during:** Task 2 (detect-secrets pre-commit hook)
- **Issue:** Initial `# pragma: allowlist secret` comments were placed at end of multi-line pgtrigger.AddTrigger() calls. Ruff reformatted the migration to expand the inline dict into multi-line form, putting `hash=` on its own line. detect-secrets hooks check per-line, so pragmas needed to be on the exact `hash=` lines.
- **Fix:** Moved pragma comments to the `hash="..."` lines directly
- **Files modified:** `apps/api/apps/api_keys/migrations/0003_apikey_org.py`
- **Verification:** detect-secrets pre-commit hook passes; migration file clean
- **Committed in:** `17e2313` (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 Rule 1 bug fix, 1 Rule 3 blocking fix)
**Impact on plan:** Both auto-fixes necessary for test suite correctness and commit integrity. No scope creep.

## Issues Encountered

- ruff reformatted migration file from inline to multi-line style between first and second commit attempt — required pragma comment relocation to hash= lines
- git stash pop after Task 2 commit caused a merge conflict in the migration file (stash held pre-ruff version); resolved by checking out HEAD version

## User Setup Required

None — migration runs automatically via `python manage.py migrate api_keys` (applied during execution). No external service configuration required.

## Next Phase Readiness

- AUDIT-01 closed: APIKey create/revoke events appear in org audit log when org_slug provided
- Remaining plans in Phase 34 can proceed independently
- Any future APIKey management UI should include org_slug field from the create/list responses

---

_Phase: 34-admin-audit-context-fixes_
_Completed: 2026-03-14_
