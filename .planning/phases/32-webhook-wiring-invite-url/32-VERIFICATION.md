---
phase: 32-webhook-wiring-invite-url
verified: 2026-03-13T23:55:00Z
status: passed
score: 6/6 must-haves verified
re_verification: false
---

# Phase 32: Webhook Wiring + Invite URL Verification Report

**Phase Goal:** Wire subscription webhooks and fix the hardcoded invitation URL — ensure MembershipService.add_member() centralises membership creation with correct event firing, InvitationService routes through it, billing tasks fire subscription.updated on Stripe events, and the invite URL reads from settings.
**Verified:** 2026-03-13T23:55:00Z
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| #   | Truth                                                                                              | Status   | Evidence                                                                                                                                                       |
| --- | -------------------------------------------------------------------------------------------------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | A user joining their first org triggers a user.created webhook event                               | VERIFIED | `add_member()` checks `is_first_org` before create; fires `fire_webhook_event(org, "user.created", ...)` conditionally (services.py:86-91); test passes        |
| 2   | Every membership addition triggers an org.member_added webhook event                               | VERIFIED | `add_member()` unconditionally fires `fire_webhook_event(org, "org.member_added", ...)` (services.py:93-97); test passes                                       |
| 3   | user.created does NOT fire when a user joins a second or subsequent org                            | VERIFIED | `is_first_org` guard at services.py:82 checks existence before create; `test_add_member_no_user_created_for_second_org` PASSED                                 |
| 4   | Stripe subscription.updated fires a subscription.updated webhook for every org the user belongs to | VERIFIED | `_fire_subscription_updated_webhooks()` iterates `Membership.objects.filter(user=user)` and calls `fire_webhook_event` per org (tasks.py:252-259); test passes |
| 5   | An invitation email contains accept_url using settings.FRONTEND_URL, not app.example.com           | VERIFIED | `InvitationService.invite()` uses `f"{settings.FRONTEND_URL}/accept-invite?token=..."` (services.py:256); `test_invite_accept_url_uses_frontend_url` PASSED    |
| 6   | All 5 RED tests from Plan 32-01 now pass                                                           | VERIFIED | pytest run: 5 passed in 8.95s; full files: 20 passed in 23.35s                                                                                                 |

**Score:** 6/6 truths verified

---

### Required Artifacts

| Artifact                               | Expected                                                                                                                   | Status           | Details                                                                                                                                                                                                               |
| -------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- | ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `apps/api/apps/orgs/services.py`       | MembershipService.add_member() classmethod; InvitationService.accept() delegating to it; settings.FRONTEND_URL in invite() | VERIFIED         | add_member() at line 65; accept() calls MembershipService.add_member() at line 308; settings.FRONTEND_URL at line 256; from django.conf import settings at line 13; fire_webhook_event module-level import at line 22 |
| `apps/api/apps/billing/tasks.py`       | \_fire_subscription_updated_webhooks() helper; called from \_handle_subscription_updated() inside B2B markers              | VERIFIED         | Helper defined at line 242 inside B2B block (lines 238-295); called at line 158 inside call-site B2B block (lines 156-159)                                                                                            |
| `apps/api/tests/orgs/test_services.py` | 4 RED stubs: user.created, org.member_added, second-org guard, FRONTEND_URL regression                                     | VERIFIED (GREEN) | All 4 functions exist at lines 144-233; all pass                                                                                                                                                                      |
| `apps/api/tests/billing/test_tasks.py` | 1 RED stub: subscription.updated fires webhook for member orgs                                                             | VERIFIED (GREEN) | Function at line 383; passes                                                                                                                                                                                          |

---

### Key Link Verification

| From                             | To                                       | Via                                              | Status | Details                                                                                                                                                             |
| -------------------------------- | ---------------------------------------- | ------------------------------------------------ | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `apps/api/apps/orgs/services.py` | `apps.webhooks.utils.fire_webhook_event` | Module-level import at line 22                   | WIRED  | `from apps.webhooks.utils import fire_webhook_event` at module top; used in add_member() at lines 87 and 93                                                         |
| `apps/api/apps/billing/tasks.py` | `apps.webhooks.utils.fire_webhook_event` | Module-level import inside B2B block at line 239 | WIRED  | `from apps.webhooks.utils import fire_webhook_event  # noqa: E402` at line 239; used in `_fire_subscription_updated_webhooks()` at line 259                         |
| `apps/api/apps/orgs/services.py` | `django.conf.settings.FRONTEND_URL`      | Module-level import + string interpolation       | WIRED  | `from django.conf import settings` at line 13; `settings.FRONTEND_URL` used in f-string at services.py:256                                                          |
| `InvitationService.accept()`     | `MembershipService.add_member()`         | Direct call replacing Membership.objects.create  | WIRED  | services.py:308 calls `MembershipService.add_member(org=invitation.org, user=user, role=Membership.Role.MEMBER)`; no direct `Membership.objects.create` in accept() |
| `_handle_subscription_updated()` | `_fire_subscription_updated_webhooks()`  | Call inside B2B_START/B2B_END block              | WIRED  | tasks.py:158 calls `_fire_subscription_updated_webhooks(customer.user, subscription)`                                                                               |

---

### Requirements Coverage

| Requirement | Source Plan  | Description                                                                                         | Status    | Evidence                                                                                                                                                                    |
| ----------- | ------------ | --------------------------------------------------------------------------------------------------- | --------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| HOOK-01     | 32-01, 32-02 | Org admin can register webhook endpoints; deliveries sent via Celery with HMAC-SHA256               | SATISFIED | Phase 32 adds the call-site wiring: user.created, org.member_added, subscription.updated all fire through the existing fire_webhook_event() utility established in Phase 27 |
| ORG-02      | 32-01, 32-02 | Org owner can invite members by email (72h token expiry); accepted via new signup or existing login | SATISFIED | InvitationService.invite() now uses settings.FRONTEND_URL; accept_url regression test passes                                                                                |

Both requirement IDs declared in both plans are satisfied. No orphaned requirements found for Phase 32 in REQUIREMENTS.md.

---

### Anti-Patterns Found

None. No TODOs, FIXMEs, empty implementations, or placeholder stubs found in any modified file.

---

### B2B Marker Structure

Two balanced B2B marker pairs exist in tasks.py:

1. **Call-site block** (lines 156-159, inside `_handle_subscription_updated`): contains the two helper calls `_try_invalidate_org_member_caches` and `_fire_subscription_updated_webhooks`. This is the runtime invocation point — stripped per-function when B2B is not selected.

2. **Definition block** (lines 238-295, module-level): contains the `fire_webhook_event` import, `_fire_subscription_updated_webhooks` definition, and `_try_invalidate_org_member_caches` definition. Both definitions are stripped atomically together when B2B is not selected.

This structure is intentional per the plan's design decision and is correct for the scaffolder.

---

### Human Verification Required

None. All behaviors are verified programmatically through the test suite.

---

### Commits Verified

All task commits from the summaries exist in the repository:

- `d1144d1` — test(32-01): add RED test stubs for webhook wiring and invite URL
- `c30ee89` — feat(32-02): add MembershipService.add_member() and fix InvitationService
- `732522a` — feat(32-02): wire subscription.updated webhook in billing tasks

---

### Summary

Phase 32 achieved its goal. The outbound webhook delivery system (established in Phase 27) is now fully wired to fire events at all three specified call sites:

1. `MembershipService.add_member()` fires `user.created` (first-org only) and `org.member_added` (every add), centralising membership creation so the webhook logic cannot be bypassed.
2. `InvitationService.accept()` routes through `add_member()`, eliminating the direct `Membership.objects.create` call and ensuring webhook events fire on invitation acceptance.
3. `_handle_subscription_updated()` calls `_fire_subscription_updated_webhooks()`, which iterates all orgs the user belongs to and fires `subscription.updated` for each.
4. The hardcoded `app.example.com` domain in `InvitationService.invite()` is replaced with `settings.FRONTEND_URL`, making the invite URL environment-configurable.

All 5 TDD tests are GREEN. Full 20-test suites across both files pass with no regressions.

---

_Verified: 2026-03-13T23:55:00Z_
_Verifier: Claude (gsd-verifier)_
