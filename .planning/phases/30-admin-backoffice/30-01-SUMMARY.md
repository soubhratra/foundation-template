---
phase: 30-admin-backoffice
plan: 01
subsystem: testing
tags: [django-unfold, django-hijack, admin, tdd, red-green, impersonation, audit]

# Dependency graph
requires:
  - phase: 29-audit-logging
    provides: AuditContextMiddleware with get_context(), apps/audit/middleware.py pattern
  - phase: 26-organization-model-per-org-billing
    provides: orgs.Organization, orgs.Membership models for admin smoke tests
  - phase: 27-outbound-webhooks
    provides: WebhookEndpoint, WebhookDelivery models for admin smoke tests
  - phase: 28-api-key-authentication
    provides: APIKey model for admin smoke tests
provides:
  - RED test scaffold (19 tests) for ADMIN-01 unfold theme + sidebar (Plans 02+03)
  - RED test scaffold for ADMIN-02 impersonation permissions + signals + middleware (Plans 02+03)
  - tests/admin/ package with staff_user, regular_user, superuser, staff_client fixtures
affects: [30-02, 30-03]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Lazy imports inside test bodies for B2B model fixtures (not top-level) — mirrors tests/audit/conftest.py pattern"
    - "RED-before-GREEN TDD scaffold: all tests fail ImportError before production code ships"

key-files:
  created:
    - apps/api/tests/admin/__init__.py
    - apps/api/tests/admin/conftest.py
    - apps/api/tests/admin/test_admin_smoke.py
    - apps/api/tests/admin/test_unfold_config.py
    - apps/api/tests/admin/test_hijack.py
  modified: []

key-decisions:
  - "No __init__.py RED trigger for tests/admin/ — conftest.py fixtures use direct imports; RED state achieved via lazy imports inside test bodies that reference not-yet-existing modules"
  - "test_unfold_config.py uses AssertionError (not ImportError) for UNFOLD settings — settings.UNFOLD key is missing, not an import failure"
  - "AuditContextMiddleware.get_context() method called directly in middleware test — avoids full Django request/response cycle, tests the context logic in isolation"

patterns-established:
  - "Admin test fixtures pattern: staff_user (is_staff=True), regular_user (is_staff=False, is_superuser=False), superuser (create_superuser), staff_client (force_login with staff_user)"
  - "Hijack signal test pattern: .send(sender=None, hijacker=..., hijacked=..., request=None) to simulate signal without full HTTP lifecycle"

requirements-completed: [ADMIN-01, ADMIN-02]

# Metrics
duration: 3min
completed: 2026-03-13
---

# Phase 30 Plan 01: Admin Backoffice RED Test Scaffold Summary

**19-test TDD scaffold covering ADMIN-01 (unfold theme + sidebar) and ADMIN-02 (impersonation permissions/signals/middleware) — all fail RED before any production code ships**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-03-13T16:33:11Z
- **Completed:** 2026-03-13T16:36:00Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments

- Created `tests/admin/` package with four targeted fixtures (staff_user, regular_user, superuser, staff_client)
- Created 7-test ADMIN-01 smoke suite verifying UnfoldModelAdmin inheritance for accounts, billing, orgs, api_keys, webhooks, and audit domains plus readonly ImpersonationEventAdmin
- Created 5-test ADMIN-01 config suite verifying UNFOLD settings sidebar structure (B2B, Users & Auth, Billing, System sections)
- Created 7-test ADMIN-02 suite covering permission function (staff_can_hijack_regular_users), signal handlers (hijack_started/ended write ImpersonationEvent), and middleware context injection (impersonator_id in hijack session)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create tests/admin package and conftest fixtures** - `3b40538` (test)
2. **Task 2: Create RED stubs for ADMIN-01 unfold theme and sidebar** - `569a9fe` (test)
3. **Task 3: Create RED stubs for ADMIN-02 impersonation permissions and signals** - `7a8f982` (test)

## Files Created/Modified

- `apps/api/tests/admin/__init__.py` - Package marker (empty)
- `apps/api/tests/admin/conftest.py` - staff_user, regular_user, superuser, staff_client fixtures
- `apps/api/tests/admin/test_admin_smoke.py` - 7 tests: UnfoldModelAdmin inheritance for all domain admins + ImpersonationEventAdmin readonly
- `apps/api/tests/admin/test_unfold_config.py` - 5 tests: UNFOLD sidebar sections (B2B, Users & Auth, Billing, System)
- `apps/api/tests/admin/test_hijack.py` - 7 tests: permission function, signal handlers, middleware context injection

## Decisions Made

- No `__init__.py` RED trigger for `tests/admin/` — the tests themselves provide the RED state through lazy imports inside test bodies that reference not-yet-existing modules (`unfold`, `apps.accounts.permissions`, `apps.audit.models.ImpersonationEvent`, `hijack`). This is consistent with Phase 29's approach where individual tests import lazily.
- `test_unfold_config.py` tests use `AssertionError` path (missing `settings.UNFOLD` key) rather than `ImportError` — the Django settings module loads fine, but the UNFOLD dict is absent until Plan 02 adds it.
- `AuditContextMiddleware.get_context()` tested directly rather than through full request/response cycle — this tests the context logic in isolation and matches the method signature expected by Plans 02+03.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Ruff auto-fixed import ordering (E402/I001) in `test_admin_smoke.py` and `test_hijack.py` on first commit attempt. Restaged the ruff-modified files and committed successfully on second attempt. No code logic was changed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- RED scaffold complete; Plans 02 and 03 can use `uv run pytest tests/admin/ -q` as their primary feedback loop
- Plan 02 needs to: install `django-unfold` + `django-hijack`, add UNFOLD settings to base.py, create ImpersonationEvent model, wire hijack signals, add `staff_can_hijack_regular_users` to apps/accounts/permissions.py
- Plan 03 needs to: create admin.py files for all 6 domains with UnfoldModelAdmin subclasses
- Blocker from STATE.md still applies: verify Django version compat with django-hijack 3.7.6 (lists 5.2 as supported) at Plan 02 start

---

_Phase: 30-admin-backoffice_
_Completed: 2026-03-13_
