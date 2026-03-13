---
phase: 32-webhook-wiring-invite-url
plan: 01
subsystem: testing
tags: [pytest, tdd, red-green, webhooks, orgs, billing, django]

# Dependency graph
requires:
  - phase: 27-outbound-webhooks
    provides: fire_webhook_event() utility and WEBHOOK_EVENTS settings
  - phase: 26-organization-model-per-org-billing
    provides: MembershipService, InvitationService, OrgService, Membership model
  - phase: 26-organization-model-per-org-billing
    provides: billing tasks _handle_subscription_updated, Customer/Subscription models

provides:
  - "5 RED test stubs defining the call-site contract for Phase 32 webhook wiring"
  - "4 stubs in tests/orgs/test_services.py: user.created, org.member_added, second-org guard, FRONTEND_URL regression"
  - "1 stub in tests/billing/test_tasks.py: subscription.updated fires webhook for member orgs"

affects:
  - 32-02-PLAN (must make all 5 stubs GREEN)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "patch('apps.orgs.services.fire_webhook_event') at caller module level — tests call-site behavior not implementation internals"
    - "patch('apps.billing.tasks.fire_webhook_event') — patch target is the future lazy import location in _fire_subscription_updated_webhooks"
    - "Customer.objects.get_or_create(user=user) in transaction=True tests — post_save signal auto-creates Customer for every new User"

key-files:
  created: []
  modified:
    - apps/api/tests/orgs/test_services.py
    - apps/api/tests/billing/test_tasks.py

key-decisions:
  - "Use get_or_create + update_fields for Customer setup in billing webhook test — post_save signal on User model auto-creates Customer records, so Customer.objects.create() raises UniqueViolation"
  - "RED failures are AttributeError (add_member not yet defined / fire_webhook_event not imported in tasks) and AssertionError (hardcoded URL) — not import errors or syntax errors; test collection succeeds cleanly"
  - "Patch target apps.billing.tasks.fire_webhook_event uses create=False — will become valid when Plan 32-02 lazy-imports fire_webhook_event inside _fire_subscription_updated_webhooks"

patterns-established:
  - "RED stubs for add_member tests fail at patch() entry because add_member() doesn't exist yet — no AttributeError on MembershipService itself since it is importable, only fire_webhook_event attr is missing from services module"

requirements-completed:
  - HOOK-01
  - ORG-02

# Metrics
duration: 4min
completed: 2026-03-13
---

# Phase 32 Plan 01: Webhook Wiring + Invite URL Summary

**5 RED TDD test stubs for webhook call-sites in add_member() and \_handle_subscription_updated(), plus FRONTEND_URL regression for invite accept_url**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-13T23:31:26Z
- **Completed:** 2026-03-13T23:35:29Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- 4 RED stubs in `tests/orgs/test_services.py` asserting fire_webhook_event call-site behavior for the not-yet-existing `MembershipService.add_member()` method
- 1 RED stub in `tests/billing/test_tasks.py` asserting `_handle_subscription_updated()` fires subscription.updated webhook for member orgs
- All 15 pre-existing tests in both files continue to pass

## Task Commits

Each task was committed atomically:

1. **Task 1 + Task 2: Add RED test stubs (orgs + billing)** - `d1144d1` (test)

_Note: Both tasks committed together as one atomic logical unit — both files were edited before verification and both required the same fix for Customer setup._

## Files Created/Modified

- `apps/api/tests/orgs/test_services.py` - Appended 4 RED test stubs for add_member() webhook behavior and FRONTEND_URL regression
- `apps/api/tests/billing/test_tasks.py` - Appended 1 RED test stub for subscription.updated webhook in billing tasks

## Decisions Made

- Used `Customer.objects.get_or_create(user=user)` then `update_fields` instead of `Customer.objects.create()` in the billing webhook test — the `post_save` signal on `AUTH_USER_MODEL` auto-creates a `Customer` for every new User, so `create()` raises `UniqueViolation`. Using get_or_create is the correct pattern throughout the test suite.
- Patch target `apps.billing.tasks.fire_webhook_event` will raise `AttributeError` until Plan 32-02 adds the import. This is valid RED behavior — the test cannot be collected-and-passed until the implementation exists.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Changed Customer.objects.create to get_or_create in billing test**

- **Found during:** Task 2 (billing RED test stub)
- **Issue:** `Customer.objects.create(user=user, ...)` raised `UniqueViolation` because the `post_save` signal on `AUTH_USER_MODEL` auto-creates a blank `Customer` for every new User before the test runs
- **Fix:** Changed to `Customer.objects.get_or_create(user=user)` + `customer.stripe_customer_id = "cus_test_webhook"; customer.save(update_fields=["stripe_customer_id"])`; used `Subscription.objects.get_or_create` for consistency
- **Files modified:** `apps/api/tests/billing/test_tasks.py`
- **Verification:** Test now fails with `AttributeError` (correct RED) instead of `IntegrityError` (setup crash)
- **Committed in:** d1144d1 (task commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug in test setup)
**Impact on plan:** Fix necessary for correct RED state. No scope creep.

## Issues Encountered

None beyond the auto-fixed Customer creation conflict.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- 5 RED tests provide the exact contract Plan 32-02 must satisfy
- Tests verify: `add_member()` fires `user.created` (first-org only) and `org.member_added` (every add)
- Tests verify: `_handle_subscription_updated()` fires `subscription.updated` for member orgs
- Tests verify: `InvitationService.invite()` uses `settings.FRONTEND_URL` for accept_url (not hardcoded)

---

_Phase: 32-webhook-wiring-invite-url_
_Completed: 2026-03-13_
