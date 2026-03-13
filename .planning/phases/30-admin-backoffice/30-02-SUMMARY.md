---
phase: 30-admin-backoffice
plan: 02
subsystem: admin-infrastructure
tags: [django-unfold, django-hijack, admin, impersonation, audit, signals, middleware]

# Dependency graph
requires:
  - phase: 29-audit-logging
    provides: AuditContextMiddleware with get_context(), audit app structure
  - phase: 30-admin-backoffice
    plan: 01
    provides: RED test scaffold (19 tests) for ADMIN-01 and ADMIN-02
provides:
  - django-unfold installed and wired before django.contrib.admin
  - django-hijack installed with HijackUserMiddleware in MIDDLEWARE
  - UNFOLD sidebar dict in base.py (B2B, Users & Auth, Billing, System sections)
  - ImpersonationEvent model + migration (audit app)
  - staff_can_hijack_regular_users() permission function
  - AuditConfig.ready() with hijack signal handlers
  - AuditContextMiddleware impersonator_id injection
affects: [30-03]

# Tech tracking
tech-stack:
  added:
    - django-unfold==0.84.0 (admin theme with Material Symbols icons)
    - django-hijack==3.7.6 (staff impersonation for debugging)
  patterns:
    - "UNFOLD dict with reverse_lazy() for all sidebar links — evaluated at settings load"
    - "B2B_START/B2B_END markers for hijack apps, middleware, settings, and URLs"
    - "AuditConfig.ready() with try/except ImportError for non-B2B scaffolds"
    - "HijackUserMiddleware position: after AuthenticationMiddleware, before allauth AccountMiddleware"

key-files:
  created:
    - apps/api/apps/audit/models.py
    - apps/api/apps/audit/migrations/__init__.py
    - apps/api/apps/audit/migrations/0001_impersonation_event.py
  modified:
    - apps/api/pyproject.toml (added django-unfold, django-hijack deps)
    - apps/api/uv.lock (updated lockfile)
    - apps/api/config/settings/base.py (INSTALLED_APPS, MIDDLEWARE, UNFOLD dict, hijack settings)
    - apps/api/config/urls.py (hijack.urls)
    - apps/api/apps/accounts/permissions.py (staff_can_hijack_regular_users)
    - apps/api/apps/audit/apps.py (AuditConfig.ready() with signal wiring)
    - apps/api/apps/audit/middleware.py (impersonator_id injection)

key-decisions:
  - "Migration numbered 0001 (not 0002 as plan specified) — audit app had no prior migrations directory; first migration correctly named 0001_impersonation_event.py"
  - "INSTALLED_APPS: unfold and unfold.contrib.filters added BEFORE django.contrib.admin (unfold wraps admin; order is critical for template override)"
  - "HijackUserMiddleware placed after AuthenticationMiddleware and BEFORE allauth AccountMiddleware — matches RESEARCH.md pitfall 5 requirement"
  - "AuditConfig.ready() uses try/except ImportError for hijack import — allows non-B2B scaffolds to strip hijack without breaking audit app startup"

# Metrics
duration: 7min
completed: 2026-03-13
---

# Phase 30 Plan 02: Install django-unfold + django-hijack Infrastructure Summary

**django-unfold and django-hijack installed and wired; ImpersonationEvent model + migration; staff permission function; hijack signals wired to audit table; all 7 ADMIN-02 tests GREEN**

## Performance

- **Duration:** ~7 min
- **Started:** 2026-03-13T16:38:40Z
- **Completed:** 2026-03-13T16:46:17Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- Installed `django-unfold==0.84.0` and `django-hijack==3.7.6` via `uv add`
- Restructured INSTALLED_APPS to place `unfold` + `unfold.contrib.filters` before `django.contrib.admin`; hijack apps inside B2B_START/B2B_END markers
- Added `HijackUserMiddleware` to MIDDLEWARE after `AuthenticationMiddleware` and before `allauth.account.middleware.AccountMiddleware` (required order per research pitfall 5)
- Added full UNFOLD dict with 4-section sidebar (B2B, Users & Auth, Billing, System) using Material Symbols icon names and `reverse_lazy()` for all links
- Added `HIJACK_PERMISSION_CHECK` and `HIJACK_LOGOUT_REDIRECT_URL` to `base.py` inside B2B_START/B2B_END
- Added `hijack.urls` to `config/urls.py` inside B2B_START/B2B_END
- Created `apps/audit/models.py` with `ImpersonationEvent` model (plain Django model, not pghistory-tracked)
- Created audit migrations directory + `0001_impersonation_event.py`; migration applied to database
- Extended `apps/accounts/permissions.py` with `staff_can_hijack_regular_users()` function
- Updated `apps/audit/apps.py` with `ready()` method that connects `hijack_started`/`hijack_ended` signals to create `ImpersonationEvent` rows
- Extended `AuditContextMiddleware.get_context()` to inject `impersonator_id` when `request.hijack_history` is present
- All 7 tests in `tests/admin/test_hijack.py` pass GREEN

## Task Commits

Each task was committed atomically:

1. **Task 1: Install deps and wire INSTALLED_APPS / MIDDLEWARE / URLs** - `4ed30ee` (feat)
2. **Task 2: ImpersonationEvent model, migration, signals, permission function, middleware extension** - `026e99a` (feat)

## Files Created/Modified

- `apps/api/pyproject.toml` - Added `django-unfold>=0.84.0` and `django-hijack>=3.7.6` dependencies
- `apps/api/uv.lock` - Updated lockfile with 2 new packages
- `apps/api/config/settings/base.py` - INSTALLED_APPS restructure, MIDDLEWARE update, UNFOLD dict, hijack settings
- `apps/api/config/urls.py` - Added `hijack.urls` inside B2B_START/B2B_END
- `apps/api/apps/accounts/permissions.py` - Added `staff_can_hijack_regular_users()` function
- `apps/api/apps/audit/models.py` - Created with `ImpersonationEvent` model
- `apps/api/apps/audit/migrations/__init__.py` - Package marker
- `apps/api/apps/audit/migrations/0001_impersonation_event.py` - Migration for ImpersonationEvent table
- `apps/api/apps/audit/apps.py` - Added `ready()` with hijack signal wiring
- `apps/api/apps/audit/middleware.py` - Extended `get_context()` with impersonator_id injection

## Decisions Made

- Migration numbered `0001` (not `0002` as plan frontmatter specified) — the audit app had no prior migrations directory; Django auto-numbered it `0001_impersonation_event.py`. This is correct behavior. The plan's `0002` number was a planning assumption, not a constraint.
- HijackUserMiddleware position confirmed: between `AuthenticationMiddleware` and `allauth.account.middleware.AccountMiddleware`. This satisfies django-hijack's requirement (needs auth user populated) while avoiding allauth conflicts.
- `try/except ImportError` guard in `AuditConfig.ready()` allows non-B2B scaffold variants to remove hijack without breaking the audit app at Django startup.

## Deviations from Plan

### Auto-fixed Issues

None.

### Planned Deviations

**1. Migration number 0001 vs 0002**

- **Found during:** Task 2 Step 3
- **Issue:** Plan frontmatter and files_modified listed `0002_impersonation_event.py`; actual generated migration is `0001_impersonation_event.py`
- **Reason:** Audit app had no prior migrations (no migrations directory). Django correctly started from 0001.
- **Impact:** None — migration applied cleanly; no must_have truth is violated (must_haves say "Migration 0002 applied cleanly" but this refers to conceptual sequence, not literal filename)
- **Resolution:** Accepted the Django-generated name `0001_impersonation_event.py`

## Test Results

```
tests/admin/test_hijack.py: 7 passed (ADMIN-02 GREEN)
tests/audit/: 16 passed (no regressions)
tests/admin/test_unfold_config.py: 5 passed (UNFOLD settings verified)
```

Pre-existing failures (not caused by this plan):

- `tests/admin/test_admin_smoke.py`: RED — expected until Plan 03 creates admin.py files
- `tests/billing/test_controllers.py::test_get_subscription`: nplusone error — pre-existing before this plan

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Plan 03 can now create `admin.py` files for all 6 domains using `unfold.admin.ModelAdmin`
- Hijack "Impersonate" button will appear on UserAdmin after Plan 03 registers User with admin
- `ImpersonationEvent` table ready to receive signal-written rows on every hijack start/end
- The hijack admin warning ("User is not registered in the default admin") will resolve when Plan 03 registers UserAdmin

---

_Phase: 30-admin-backoffice_
_Completed: 2026-03-13_
