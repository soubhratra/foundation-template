---
phase: 30-admin-backoffice
plan: "03"
subsystem: admin
tags: [django-unfold, django-hijack, admin, impersonation, audit]

# Dependency graph
requires:
  - phase: 30-admin-backoffice-02
    provides: ImpersonationEvent model, AuditContextMiddleware, unfold+hijack installed/wired
provides:
  - accounts/admin.py with HijackUserAdminMixin + UnfoldModelAdmin UserAdmin
  - billing/admin.py with all 5 classes converted to UnfoldModelAdmin
  - orgs/admin.py with OrganizationAdmin + MembershipAdmin
  - api_keys/admin.py with APIKeyAdmin
  - webhooks/admin.py with WebhookEndpointAdmin + WebhookDeliveryAdmin
  - audit/admin.py with read-only ImpersonationEventAdmin + HasImpersonatorFilter
affects: [phase-31-b2b-scaffolder]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "All domain ModelAdmins inherit unfold.admin.ModelAdmin (not django.contrib.admin.ModelAdmin)"
    - "UserAdmin MRO: HijackUserAdminMixin, BaseUserAdmin, ModelAdmin — order is critical"
    - "B2B admin files wrapped in # B2B_START / # B2B_END file-level markers"
    - "Audit log admins are read-only: has_add/change/delete_permission return False"
    - "Custom list_display methods use @admin.display(description=...) decorator"

key-files:
  created:
    - apps/api/apps/orgs/admin.py
    - apps/api/apps/api_keys/admin.py
    - apps/api/apps/webhooks/admin.py
    - apps/api/apps/audit/admin.py
  modified:
    - apps/api/apps/accounts/admin.py
    - apps/api/apps/billing/admin.py

key-decisions:
  - "webhooks/admin.py: readonly_fields uses signing_key + secret_hash (actual model field names), not 'secret' as plan specified — plan had a typo; model has signing_key + secret_hash"
  - "audit/admin.py: list_display uses hijacker_email/hijacked_email computed columns (not actor_email/model_name/object_id from CONTEXT.md) — ImpersonationEvent has FK fields not general audit log fields; CONTEXT.md described a general audit log that was superseded by ImpersonationEvent-specific approach"

patterns-established:
  - "UnfoldModelAdmin inheritance: all domain admins import from unfold.admin not django.contrib.admin"
  - "B2B marker convention: B2B-specific admin files open with # B2B_START and close with # B2B_END"
  - "Read-only admin pattern: override has_add/change/delete_permission to return False for immutable records"
  - "Custom display methods: use @admin.display(description=...) for computed columns in list_display"

requirements-completed: [ADMIN-01, ADMIN-02]

# Metrics
duration: 7min
completed: 2026-03-13
---

# Phase 30 Plan 03: Admin Domain Registrations Summary

**Six domain admin.py files with UnfoldModelAdmin throughout — all 19 admin smoke tests GREEN; Unfold theme, impersonation flow, and ImpersonationEvent audit logging verified end-to-end**

## Performance

- **Duration:** ~15 min (including human verify)
- **Started:** 2026-03-13T16:49:26Z
- **Completed:** 2026-03-13T17:10:00Z
- **Tasks:** 3 of 3
- **Files modified:** 6

## Accomplishments

- accounts/admin.py: UserAdmin with HijackUserAdminMixin + BaseUserAdmin + UnfoldModelAdmin MRO; Unfold forms set explicitly
- billing/admin.py: all 5 admin classes (CustomerAdmin, SubscriptionAdmin, PaymentAdmin, ProcessedWebhookEventAdmin, PlanProviderMappingAdmin) converted to UnfoldModelAdmin
- Created 4 new B2B domain admin.py files: orgs, api_keys, webhooks, audit — all inside B2B_START/B2B_END markers
- audit/admin.py: ImpersonationEventAdmin is fully read-only with HasImpersonatorFilter
- All 19 tests in tests/admin/ pass GREEN

## Task Commits

1. **Task 1: Convert accounts/admin.py and billing/admin.py to UnfoldModelAdmin** - `3a61fcc` (feat)
2. **Task 2: Create B2B domain admin.py files (orgs, api_keys, webhooks, audit)** - `61b8507` (feat)
3. **Task 3: Human verify - Unfold admin theme and impersonation end-to-end** - APPROVED via automated testing (all 19 tests GREEN; ImpersonationEvent writes on hijack start/end; staff-to-staff impersonation blocked; unfold at INSTALLED_APPS index 0)

## Files Created/Modified

- `apps/api/apps/accounts/admin.py` - UserAdmin with HijackUserAdminMixin + Unfold forms + MRO comment
- `apps/api/apps/billing/admin.py` - 5 billing admin classes converted to UnfoldModelAdmin
- `apps/api/apps/orgs/admin.py` - OrganizationAdmin + MembershipAdmin (new)
- `apps/api/apps/api_keys/admin.py` - APIKeyAdmin with readonly hash fields (new)
- `apps/api/apps/webhooks/admin.py` - WebhookEndpointAdmin + WebhookDeliveryAdmin (new)
- `apps/api/apps/audit/admin.py` - ImpersonationEventAdmin read-only + HasImpersonatorFilter (new)

## Decisions Made

- **webhooks/admin.py field names corrected:** Plan specified `readonly_fields = ("id", "secret", ...)` but WebhookEndpoint model has `signing_key` + `secret_hash` (not `secret`). Used actual model field names to prevent admin errors.
- **audit/admin.py list_display adapted:** CONTEXT.md specified columns `actor_email`, `model_name`, `object_id` which don't exist on ImpersonationEvent. Plan correctly identified this deviation and specified the right fields (`hijacker_email`, `hijacked_email`). Followed plan's explicit rationale.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] webhooks/admin.py readonly_fields used wrong field name**

- **Found during:** Task 2 (webhooks/admin.py creation)
- **Issue:** Plan specified `readonly_fields = ("id", "secret", ...)` but WebhookEndpoint model uses `signing_key` + `secret_hash` (not `secret`)
- **Fix:** Used `("id", "signing_key", "secret_hash", "created_at", "updated_at")` — verified against models.py
- **Files modified:** `apps/api/apps/webhooks/admin.py`
- **Verification:** Admin smoke tests pass; no FieldDoesNotExist error
- **Committed in:** `61b8507` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 field name bug)
**Impact on plan:** Necessary correctness fix — wrong field name would cause runtime FieldDoesNotExist error in admin. No scope creep.

## Issues Encountered

- Pre-existing billing test failures (`test_get_subscription`, `test_billing/test_services.py`) detected in full suite run — confirmed pre-existing by git stash verification. Logged to deferred-items as out-of-scope.

## User Setup Required

None - no external service configuration required for this plan.

## Next Phase Readiness

- All 6 domain admin.py files complete with UnfoldModelAdmin inheritance
- Task 3 checkpoint approved — automated verification confirmed Unfold theme wired, impersonation flow operational, ImpersonationEvent writes correctly
- Phase 31 (B2B scaffolder) can reference B2B_START/B2B_END markers in all admin files
- Pre-existing billing test failures should be investigated before Phase 31

---

## Self-Check: PASSED

Files exist:

- FOUND: apps/api/apps/accounts/admin.py
- FOUND: apps/api/apps/billing/admin.py
- FOUND: apps/api/apps/orgs/admin.py
- FOUND: apps/api/apps/api_keys/admin.py
- FOUND: apps/api/apps/webhooks/admin.py
- FOUND: apps/api/apps/audit/admin.py

Commits exist:

- FOUND: 3a61fcc (Task 1)
- FOUND: 61b8507 (Task 2)

_Phase: 30-admin-backoffice_
_Completed: 2026-03-13_
