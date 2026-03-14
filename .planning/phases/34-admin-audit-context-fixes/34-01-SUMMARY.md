---
phase: 34-admin-audit-context-fixes
plan: 01
subsystem: api
tags: [django-unfold, django-admin, orgs, billing, OrgCustomer]

# Dependency graph
requires:
  - phase: 30-admin-backoffice
    provides: django-unfold ModelAdmin base class and UNFOLD sidebar structure
  - phase: 26-organization-model-per-org-billing
    provides: OrgCustomer model in apps/orgs
provides:
  - OrgCustomerAdmin registered in apps/orgs/admin.py inside B2B markers
  - Org Billing UNFOLD sidebar entry for staff navigation
affects:
  - 31-cli-scaffolder-integration (B2B marker stripping removes OrgCustomerAdmin)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - OrgCustomerAdmin follows same UnfoldModelAdmin pattern as CustomerAdmin in billing app
    - Sidebar entries use Material Symbols icon names (receipt), not Heroicons

key-files:
  created: []
  modified:
    - apps/api/apps/orgs/admin.py
    - apps/api/config/settings/base.py
    - apps/api/tests/admin/test_admin_smoke.py
    - apps/api/tests/admin/test_unfold_config.py

key-decisions:
  - "OrgCustomerAdmin list_display: (org, stripe_customer_id, created_at) — org first for B2B context, stripe_customer_id editable for staff corrections"
  - "readonly_fields includes updated_at — timestamps auto-set by signals, stripe_customer_id intentionally editable"
  - "Icon is receipt (Material Symbols) — plan explicitly noted Heroicon names render as blank icons in django-unfold"

patterns-established:
  - "B2B admin registrations always placed inside B2B_START/B2B_END markers for scaffolder stripping"
  - "UNFOLD sidebar B2B items appended within the B2B_START/B2B_END block in base.py"

requirements-completed: [BILL-01]

# Metrics
duration: 12min
completed: 2026-03-13
---

# Phase 34 Plan 01: OrgCustomer Admin Registration Summary

**OrgCustomerAdmin with UnfoldModelAdmin registered in apps/orgs inside B2B markers, plus Org Billing UNFOLD sidebar entry using receipt icon — staff can now inspect and correct per-org Stripe IDs without raw DB access.**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-03-13T~09:00Z
- **Completed:** 2026-03-13
- **Tasks:** 2 (TDD: RED + GREEN)
- **Files modified:** 4

## Accomplishments

- Added three RED test stubs confirming OrgCustomerAdmin was missing (BILL-01 gap)
- Registered OrgCustomerAdmin inside B2B_START/B2B_END markers with correct list_display, search_fields, and readonly_fields
- Added "Org Billing" UNFOLD sidebar entry using Material Symbols receipt icon
- All 22 admin tests pass GREEN with no regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Add RED test stubs for OrgCustomerAdmin** - `b1e390e` (test)
2. **Task 2: Register OrgCustomerAdmin and add sidebar entry** - `e685f41` (feat)

## Files Created/Modified

- `apps/api/apps/orgs/admin.py` - Added OrgCustomerAdmin class and OrgCustomer import inside B2B markers
- `apps/api/config/settings/base.py` - Added Org Billing UNFOLD sidebar item to B2B section
- `apps/api/tests/admin/test_admin_smoke.py` - Added test_org_customer_admin_inherits_unfold and test_org_customer_admin_list_display
- `apps/api/tests/admin/test_unfold_config.py` - Added test_unfold_sidebar_has_org_billing_link

## Decisions Made

- `stripe_customer_id` is intentionally NOT in `readonly_fields` — staff must be able to correct it without raw DB access (the entire purpose of BILL-01)
- `updated_at` IS in `readonly_fields` alongside `created_at` — auto-managed by signals, should not be edited manually
- "Org Billing" naming chosen over "OrgCustomer" for sidebar clarity to non-technical staff

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Pre-commit hook (ruff) reformatted files on first commit attempt — resolved by re-staging after hook modified files, standard pre-commit behavior.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- BILL-01 gap is closed — OrgCustomer records visible and editable in admin
- Phase 34-02 (AUDIT-01 org context in API key audit log) is independent and can proceed
- B2B scaffold stripping in Phase 31 will correctly remove OrgCustomerAdmin via B2B_START/B2B_END markers

---

_Phase: 34-admin-audit-context-fixes_
_Completed: 2026-03-13_
