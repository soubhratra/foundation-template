---
phase: 26-organization-model-per-org-billing
plan: "02"
subsystem: orgs/models
tags: [django, models, migrations, signals, b2b, stripe, orgs]

dependency_graph:
  requires:
    - phase: 26-01
      provides: RED test stubs for all org model tests (tests/orgs/test_models.py)
  provides:
    - apps/api/apps/orgs/ Django app with Organization, Membership, Invitation, OrgCustomer models
    - 0001_initial.py migration for all 4 org models
    - post_save signal auto-creating OrgCustomer on Organization creation
    - apps.orgs registered in INSTALLED_APPS inside B2B_START/B2B_END markers
  affects:
    - 26-03 (services layer — builds on these models)
    - 26-04 (permissions layer — imports Membership from these models)
    - 26-05 (entitlements — imports OrgCustomer)
    - 26-06 (webhook extension — imports OrgCustomer and Membership)

tech-stack:
  added: []
  patterns:
    - Django post_save signal wiring in AppConfig.ready() (mirrors billing/apps.py pattern)
    - B2B_START/B2B_END INSTALLED_APPS markers for scaffolder-friendly module isolation
    - Organization.owner FK as denormalized convenience field; Membership is authoritative role source
    - Invitation.email field (not invited_email) — matches test contract from 26-01 RED stubs
    - OrgCustomer.get_or_create in signal receiver for idempotency

key-files:
  created:
    - apps/api/apps/orgs/__init__.py
    - apps/api/apps/orgs/apps.py
    - apps/api/apps/orgs/models.py
    - apps/api/apps/orgs/signals.py
    - apps/api/apps/orgs/migrations/__init__.py
    - apps/api/apps/orgs/migrations/0001_initial.py
  modified:
    - apps/api/config/settings/base.py

key-decisions:
  - "Invitation uses field name 'email' (not 'invited_email' from RESEARCH.md) — matched test contract written in 26-01; tests are the authoritative RED contract"
  - "Organization has owner FK (SET_NULL) as denormalized record of creator; Membership table is the authoritative role source and must be queried for permissions"
  - "OrgCustomer auto-created via post_save signal using get_or_create for idempotency — same pattern as billing/signals.py Customer creation"
  - "apps.orgs registered with B2B_START/B2B_END comment markers to support scaffolder --with b2b flag"

patterns-established:
  - "AppConfig.ready() wires signal import: import apps.orgs.signals (noqa F401)"
  - "INSTALLED_APPS B2B markers: # B2B_START / app entry / # B2B_END"

requirements-completed: [ORG-01, BILL-01]

duration: 4min
completed: "2026-03-13"
---

# Phase 26 Plan 02: Org Models + Migration Summary

**Django apps/orgs app with 4 models (Organization, Membership, Invitation, OrgCustomer), initial migration, and post_save OrgCustomer auto-create signal — all 3 model tests GREEN**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-13T02:54:06Z
- **Completed:** 2026-03-13T02:58:13Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- Organization, Membership, Invitation, OrgCustomer models created with correct fields, constraints, and db_table names
- 0001_initial.py migration generated and applied cleanly to PostgreSQL
- post_save signal auto-creates OrgCustomer on Organization creation (idempotent via get_or_create)
- apps.orgs registered in INSTALLED_APPS inside B2B_START/B2B_END markers
- All 3 test_models.py tests pass GREEN: slug uniqueness, OrgCustomer auto-create, Invitation.is_valid()

## Task Commits

Each task was committed atomically:

1. **Task 1: Create apps/orgs/ app skeleton and models** - `ce2cc81` (feat)
2. **Task 2: Generate migration, register app, and turn model tests GREEN** - `2a321f4` (feat)

## Files Created/Modified

- `apps/api/apps/orgs/__init__.py` - Empty package marker
- `apps/api/apps/orgs/apps.py` - OrgsConfig with ready() wiring signal import
- `apps/api/apps/orgs/models.py` - Organization, Membership, Invitation, OrgCustomer model definitions
- `apps/api/apps/orgs/signals.py` - post_save receiver auto-creating OrgCustomer on Organization creation
- `apps/api/apps/orgs/migrations/__init__.py` - Migrations package marker
- `apps/api/apps/orgs/migrations/0001_initial.py` - Initial migration for all 4 org models
- `apps/api/config/settings/base.py` - Added apps.orgs inside B2B_START/B2B_END markers

## Decisions Made

- **Invitation field name is `email` not `invited_email`:** RESEARCH.md Pattern 2 used `invited_email`, but the 26-01 RED test stubs used `email`. The test stubs from 26-01 ARE the authoritative contract; model adapted to match them. [Rule 1 - matched test contract]
- **Organization has owner FK:** RESEARCH.md Pattern 2 did not include an `owner` field on Organization, but conftest.py and test_models.py (written in 26-01) call `Organization.objects.create(..., owner=owner)`. Added owner FK (SET_NULL) to match the test contract.
- **OrgCustomer uses get_or_create in signal:** Added for idempotency in case of duplicate signals or retries. Minor enhancement over plain `create()`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Adapted Invitation.email field name to match RED test contract**

- **Found during:** Task 1 (reading test_models.py and conftest.py from 26-01)
- **Issue:** RESEARCH.md Pattern 2 specifies `invited_email` but 26-01 test stubs use `email`; using `invited_email` would make all tests fail with AttributeError
- **Fix:** Used `email` as the field name on Invitation model; this matches the authoritative test contract
- **Files modified:** apps/api/apps/orgs/models.py
- **Verification:** test_invitation_is_valid_false_after_expiry PASSED
- **Committed in:** ce2cc81 (Task 1 commit)

**2. [Rule 1 - Bug] Added owner FK to Organization to match RED test contract**

- **Found during:** Task 1 (reading conftest.py and test_models.py from 26-01)
- **Issue:** RESEARCH.md Pattern 2 omits owner field on Organization, but conftest.py fixture calls `Organization.objects.create(..., owner=org_owner)` — without the field, every test using the `org` fixture would fail
- **Fix:** Added `owner = models.ForeignKey(AUTH_USER_MODEL, SET_NULL, null=True, blank=True, related_name="owned_orgs")` on Organization
- **Files modified:** apps/api/apps/orgs/models.py
- **Verification:** All 3 model tests PASSED including test_org_slug_unique and test_org_customer_auto_created
- **Committed in:** ce2cc81 (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (both Rule 1 — model adapted to match authoritative test contract)
**Impact on plan:** Both fixes necessary to satisfy the RED test stubs from 26-01. No scope creep; all fixed work is within the model definition scope of this plan.

## Issues Encountered

- Pre-commit ruff E501 triggered on auto-generated migration file long lines; ruff-format reformatted the file automatically in the hook, then re-staged and committed. Pre-existing allauth deprecation warnings in `manage.py check` output are unrelated to this plan.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All 4 org models exist, migrate cleanly, and have GREEN unit tests
- OrgCustomer auto-creation signal is in place and verified
- apps.orgs is registered and importable throughout the Django project
- 26-03 (services) can now import Organization, Membership, Invitation, OrgCustomer directly
- 26-04 (permissions) can import Membership and Organization
- The `email` field name on Invitation (instead of `invited_email`) must be used consistently in all subsequent plans

---

_Phase: 26-organization-model-per-org-billing_
_Completed: 2026-03-13_

## Self-Check: PASSED

All 5 required files exist. Both task commits verified (ce2cc81, 2a321f4).
