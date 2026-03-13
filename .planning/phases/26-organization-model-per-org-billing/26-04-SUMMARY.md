---
phase: 26-organization-model-per-org-billing
plan: "04"
subsystem: api
tags: [django, orgs, services, invitations, celery, email, signals, allauth]

# Dependency graph
requires:
  - phase: 26-02
    provides: Organization, Membership, Invitation, OrgCustomer models
  - phase: 26-03
    provides: org permission classes (independent — same wave)

provides:
  - OrgService.create_org() — creates org + owner Membership in transaction.atomic()
  - MembershipService.list_members(), update_role(), remove_member(), transfer_ownership()
  - InvitationService.invite(), accept(), store_pending_invite(), revoke()
  - _resolve_org_plan_id() helper for entitlement resolution
  - org_invitation.html email template
  - consume_pending_invite_on_signup signal wired via OrgsConfig.ready()

affects:
  - 26-05-controllers (thin wrappers around these services)
  - 26-06-billing-integration (_resolve_org_plan_id used by has_org_feature)
  - future org-related phases (27+) that extend invitation or membership flows

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Service classes with @classmethod interface — no instantiation required from controllers"
    - "Lazy imports inside service methods to prevent circular imports between orgs and billing"
    - "transaction.atomic() for multi-row writes; Membership.objects.filter().update() for ownership transfer (avoids N+1)"
    - "on_commit_immediately conftest fixture for testing on_commit-wrapped email sends without transaction=True"

key-files:
  created:
    - apps/api/apps/orgs/services.py
    - apps/api/apps/notifications/templates/email/org_invitation.html
  modified:
    - apps/api/apps/orgs/signals.py
    - apps/api/apps/orgs/apps.py
    - apps/api/conftest.py
    - apps/api/tests/orgs/test_services.py

key-decisions:
  - "Service classes use @classmethod throughout — callers do OrgService.create_org(...) not OrgService().create_org(...)"
  - "_resolve_org_plan_id returns None when billing Subscription links to user Customer not OrgCustomer — correct until Phase 27+ adds per-org subscription"
  - "on_commit_immediately is a non-autouse conftest fixture — opt-in for mailoutbox tests; does NOT apply globally to avoid breaking TestSendEmailOnCommitRollback"
  - "consume_pending_invite_on_signup wired via OrgsConfig.ready() not @receiver — avoids importing allauth at module load time"

patterns-established:
  - "Service layer uses keyword-only args (*) for all parameters — prevents positional arg confusion at call sites"
  - "InvitationService.accept() takes an invitation object (not token string) — controller is responsible for token→invitation lookup"
  - "Concurrent accept race handled by IntegrityError on unique_together(org, user) — raises ServiceError 409 with from None"

requirements-completed: [ORG-01, ORG-02, ORG-04, BILL-01]

# Metrics
duration: 13min
completed: 2026-03-13
---

# Phase 26 Plan 04: Organization Service Layer Summary

**OrgService, MembershipService, InvitationService with 72h invitation flow, org_invitation.html template, and session-based new-user invite pickup via allauth user_signed_up signal**

## Performance

- **Duration:** 13 min
- **Started:** 2026-03-13T03:06:32Z
- **Completed:** 2026-03-13T03:19:32Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Full service layer for org management — OrgService, MembershipService, InvitationService all importable with no circular imports
- InvitationService handles the complete invitation lifecycle: invite (with revoke-and-reissue), accept (email match + anon session), revoke
- user_signed_up signal wired so pending invites stored in session are auto-accepted after allauth signup
- All 6 test_services.py tests GREEN after fixing two pre-existing test issues (missing org_membership fixture, missing on_commit test infrastructure)

## Task Commits

1. **Task 1: OrgService, MembershipService, \_resolve_org_plan_id** - `fe6dbae` (feat)
2. **Task 2: InvitationService, email template, signals, test fixes** - `66c4ebd` (feat)

## Files Created/Modified

- `apps/api/apps/orgs/services.py` — OrgService, MembershipService, InvitationService, \_resolve_org_plan_id, ServiceError re-export
- `apps/api/apps/notifications/templates/email/org_invitation.html` — Invitation email template with SUBJECT sentinel
- `apps/api/apps/orgs/signals.py` — Added consume_pending_invite_on_signup function
- `apps/api/apps/orgs/apps.py` — Wire user_signed_up signal in OrgsConfig.ready()
- `apps/api/conftest.py` — Added on_commit_immediately, \_test_email_backend, \_celery_eager fixtures
- `apps/api/tests/orgs/test_services.py` — Added on_commit_immediately fixture to mailoutbox test; added org_membership to transfer_ownership test

## Decisions Made

- Service classes use `@classmethod` throughout (not instance methods) — callers invoke `OrgService.create_org()` without instantiation
- `_resolve_org_plan_id` returns `None` when there is no org-level subscription — the billing `Subscription` model currently links to user-based `Customer`, so org billing resolution will be enabled in Phase 27+ when a per-org subscription is added
- `on_commit_immediately` conftest fixture is non-autouse (opt-in) to avoid breaking `TestSendEmailOnCommitRollback` which deliberately tests rollback behavior
- `consume_pending_invite_on_signup` connected via `OrgsConfig.ready()` rather than `@receiver` decorator to avoid importing allauth at module load time

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test_transfer_ownership missing Membership for org_owner**

- **Found during:** Task 2 (running service tests)
- **Issue:** test_transfer_ownership used `org` and `org_owner` fixtures but not `org_membership`. The `org` fixture creates an Organization with `owner=org_owner` (FK field) but no `Membership` row. After transfer, `Membership.objects.get(org=org, user=org_owner)` raised DoesNotExist.
- **Fix:** Added `org_membership` as a fixture parameter to `test_transfer_ownership`
- **Files modified:** `apps/api/tests/orgs/test_services.py`
- **Verification:** test_transfer_ownership now passes
- **Committed in:** `66c4ebd`

**2. [Rule 2 - Missing Critical] Added on_commit_immediately fixture for mailoutbox tests**

- **Found during:** Task 2 (test_invite_sends_email failing with empty mailoutbox)
- **Issue:** `send_email()` wraps Celery enqueue in `transaction.on_commit()`. In `@pytest.mark.django_db` (non-transaction) tests, the outer test transaction is rolled back — on_commit never fires, mailoutbox stays empty.
- **Fix:** Added non-autouse `on_commit_immediately` conftest fixture that patches `transaction.on_commit` to call immediately; added locmem email backend and CELERY_TASK_ALWAYS_EAGER overrides as autouse fixtures
- **Files modified:** `apps/api/conftest.py`, `apps/api/tests/orgs/test_services.py`
- **Verification:** test_invite_sends_email passes; TestSendEmailOnCommitRollback still passes (not affected — uses transaction=True)
- **Committed in:** `66c4ebd`

---

**Total deviations:** 2 auto-fixed (1 test bug, 1 missing test infrastructure)
**Impact on plan:** Both fixes required for correct test execution. No business logic scope creep.

## Issues Encountered

- Ruff F821 false-positives on string annotations for types defined inside lazy imports (e.g. `-> "Organization"`). Fixed by using `-> object` for return types where the model is imported inside the function body.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Services are complete and tested; 26-05 (controllers) can now build thin API endpoint wrappers around these methods
- `_resolve_org_plan_id` returns None until Phase 27+ adds per-org subscription — safe for Phase 26 scope
- `consume_pending_invite_on_signup` signal is wired but tested only via unit test of `store_pending_invite`; end-to-end invite signup flow will be covered in integration tests in 26-05

---

_Phase: 26-organization-model-per-org-billing_
_Completed: 2026-03-13_
