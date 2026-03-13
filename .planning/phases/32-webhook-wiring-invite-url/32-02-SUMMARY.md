---
phase: 32-webhook-wiring-invite-url
plan: "02"
subsystem: api
tags: [webhooks, django, orgs, billing, celery, stripe]

# Dependency graph
requires:
  - phase: 32-01
    provides: RED test stubs for webhook wiring and invite URL fix
  - phase: 27-outbound-webhooks
    provides: fire_webhook_event() utility and WebhookEndpoint/WebhookDelivery models
  - phase: 26-organization-model-per-org-billing
    provides: MembershipService, InvitationService, OrgService, Membership model
  - phase: 26-billing-tasks
    provides: _handle_subscription_updated() handler and B2B marker conventions
provides:
  - MembershipService.add_member() classmethod firing user.created and org.member_added webhooks
  - InvitationService.accept() delegating Membership creation to add_member()
  - InvitationService.invite() using settings.FRONTEND_URL for accept_url
  - _fire_subscription_updated_webhooks() helper in billing/tasks.py firing subscription.updated for all user orgs
  - All 5 RED tests from Plan 32-01 now GREEN
affects:
  - any phase consuming MembershipService or InvitationService
  - webhook delivery pipeline (27-outbound-webhooks)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Module-level import of fire_webhook_event in services.py and billing/tasks.py enables patch('module.fire_webhook_event') in tests"
    - "Lazy imports of Membership model inside function bodies avoid circular imports while fire_webhook_event itself is module-level"
    - "_fire_subscription_updated_webhooks() swallows all exceptions — webhook wiring must never crash Stripe event processing"
    - "is_first_org check done BEFORE Membership.objects.create() to avoid .exclude(pk=...) complexity in add_member()"

key-files:
  created: []
  modified:
    - apps/api/apps/orgs/services.py
    - apps/api/apps/billing/tasks.py

key-decisions:
  - "fire_webhook_event imported at module level (not lazy) in both services.py and tasks.py — required for patch('apps.orgs.services.fire_webhook_event') and patch('apps.billing.tasks.fire_webhook_event') test patterns"
  - "Module-level import placed inside B2B block in tasks.py — scaffolder strips both the import and the helper function together when B2B is not selected"
  - "add_member() checks is_first_org before creating Membership (not after) — avoids pk exclusion complexity and is read-consistent within transaction"
  - "accept() keeps Membership import for Membership.Role.MEMBER reference even though Membership.objects.create() moved to add_member()"

patterns-established:
  - "Webhook firing: always import fire_webhook_event at module level; Membership model stays lazy inside function body"
  - "B2B blocks can contain module-level imports — scaffolder strips whole blocks atomically"

requirements-completed:
  - HOOK-01
  - ORG-02

# Metrics
duration: 8min
completed: "2026-03-13"
---

# Phase 32 Plan 02: Webhook Wiring + Invite URL Summary

**MembershipService.add_member() wired to fire user.created/org.member_added webhooks; subscription.updated webhook added for all user orgs on Stripe events; invite accept_url uses settings.FRONTEND_URL**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-13T23:36:31Z
- **Completed:** 2026-03-13T23:44:37Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Added `MembershipService.add_member()` classmethod that creates Membership, fires `user.created` for first-org join, and fires `org.member_added` for every add
- Routed `InvitationService.accept()` through `add_member()` so invitation acceptance fires both webhook events
- Fixed `InvitationService.invite()` hardcoded `app.example.com` domain to use `settings.FRONTEND_URL`
- Added `_fire_subscription_updated_webhooks()` in billing/tasks.py that fires `subscription.updated` for all orgs a user belongs to, called from `_handle_subscription_updated()` inside B2B markers
- All 5 RED tests from Plan 32-01 turned GREEN; full 309-test suite stays green

## Task Commits

Each task was committed atomically:

1. **Task 1: Add MembershipService.add_member() and fix InvitationService** - `c30ee89` (feat)
2. **Task 2: Wire subscription.updated webhook in billing/tasks.py** - `732522a` (feat)

**Plan metadata:** (pending docs commit)

## Files Created/Modified

- `apps/api/apps/orgs/services.py` - Added module-level imports (settings, fire_webhook_event); added add_member() classmethod; routed accept() through add_member(); fixed invite() URL
- `apps/api/apps/billing/tasks.py` - Added module-level fire_webhook_event import inside B2B block; added \_fire_subscription_updated_webhooks() helper; wired it into \_handle_subscription_updated()

## Decisions Made

- `fire_webhook_event` imported at module level (not lazy) in both files — the test patch paths `apps.orgs.services.fire_webhook_event` and `apps.billing.tasks.fire_webhook_event` require names in the module namespace. Membership model remains lazy inside function bodies to avoid circular imports.
- Module-level import placed inside the B2B block in tasks.py — the scaffolder strips whole B2B blocks atomically, so both the import and `_fire_subscription_updated_webhooks` are removed together when B2B is not selected. This avoids a dangling import in non-B2B scaffolds.
- `is_first_org` checked before `Membership.objects.create()` — simpler than post-create exclusion; reads one count before write inside the same call.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed ruff E501 line-too-long in docstring**

- **Found during:** Task 2 (pre-commit hook caught it)
- **Issue:** Docstring line "Uses lazy imports to avoid circular import: billing.tasks → webhooks.utils → orgs.models → billing.models." exceeded 100 character limit
- **Fix:** Wrapped the circular import chain description onto two lines
- **Files modified:** apps/api/apps/billing/tasks.py
- **Verification:** ruff hook passed on second commit attempt
- **Committed in:** 732522a (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking — lint)
**Impact on plan:** Minor docstring line-wrap only. No logic changes.

## Issues Encountered

None beyond the ruff line-length violation caught by pre-commit and fixed inline.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 32 is complete. All webhook events (user.created, org.member_added, subscription.updated) now fire in production paths.
- The outbound webhook delivery system (Phase 27) was already in place — this plan was the final wiring layer.
- No blockers for downstream phases.

---

_Phase: 32-webhook-wiring-invite-url_
_Completed: 2026-03-13_
