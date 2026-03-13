# Phase 32: Webhook Wiring + Invitation URL Fix - Context

**Gathered:** 2026-03-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Wire `fire_webhook_event()` to production callers for the three events defined in `WEBHOOK_EVENTS` (`user.created`, `subscription.updated`, `org.member_added`), and fix `InvitationService.invite()` to use `settings.FRONTEND_URL` instead of the hardcoded `https://app.example.com` domain.

Not in scope: Adding new event types, changing the delivery infrastructure (Celery/HMAC), OrgCustomer-level subscription webhooks (BILL-02 is deferred), or making the invitation path configurable.

</domain>

<decisions>
## Implementation Decisions

### user.created — where and when to fire

- Fire inside `MembershipService.add_member()` when the user joins their first org (not at signup, where there is no org context)
- No guard needed for "first org ever" — fire for the specific org being joined, scoped to that org
- Fire `user.created` first, then `org.member_added` (both async via `transaction.on_commit()` — ordering is best-effort)
- **Payload:** minimal — `{user_id, email}` matching the `WEBHOOK_EVENTS` example_payload defined in Phase 27

### subscription.updated — org resolution

- Fire inside `_handle_subscription_updated()` in `apps/billing/tasks.py` after the DB update, via `transaction.on_commit()`
- Fire for **all orgs where the subscribed user is a member** — simple rule, no OrgCustomer filter
- **Payload:** `{user_id, plan, status}` matching the `WEBHOOK_EVENTS` example_payload defined in Phase 27

### org.member_added — wiring location

- Fire inside `MembershipService.add_member()` after `user.created` (when first-time user) or instead of it (when existing user joins org)
- Payload: Claude's discretion (consistent with org context available in add_member)

### Invitation URL fix

- Replace only the hardcoded domain in `InvitationService.invite()` line 217:
  - `f"https://app.example.com/accept-invite?token={invitation.token}"`
  - → `f"{settings.FRONTEND_URL}/accept-invite?token={invitation.token}"`
- The path `/accept-invite` stays hardcoded — products can subclass if they need a different path
- Add a regression test: override `FRONTEND_URL` to a test value and assert the generated `accept_url` starts with it

### Claude's Discretion

- `org.member_added` payload fields (user_id, org_slug, role — infer from what's available in add_member)
- Test approach for webhook wiring (mock `fire_webhook_event` at the caller level to avoid Celery in unit tests)

</decisions>

<code_context>

## Existing Code Insights

### Reusable Assets

- `fire_webhook_event(org, event_type, payload)` in `apps/webhooks/utils.py` — the dispatch function; enqueues Celery tasks via `transaction.on_commit()`
- `MembershipService.add_member()` in `apps/orgs/services.py` — wiring point for both `user.created` and `org.member_added`
- `_handle_subscription_updated()` in `apps/billing/tasks.py:99` — wiring point for `subscription.updated`
- `FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:3000")` in `config/settings/base.py:312` — already defined, just unused in InvitationService

### Established Patterns

- `fire_webhook_event()` uses `transaction.on_commit()` internally — callers just call the function, no need to wrap in `on_commit` themselves
- Phase 27 established that `WEBHOOK_EVENTS` example payloads are canonical — implementation should match them
- Existing tests mock at the task level (see `test_utils.py`) — new tests should mock `fire_webhook_event` itself when testing callers

### Integration Points

- `apps/orgs/services.py` — `MembershipService.add_member()` is the single wiring point for user + member events
- `apps/billing/tasks.py` — `_handle_subscription_updated()` is the single wiring point for subscription events
- `apps/orgs/services.py` — `InvitationService.invite()` line 217 is the single-line fix location
- `apps/api/tests/orgs/test_services.py` — existing InvitationService tests to add regression to

</code_context>

<specifics>
## Specific Ideas

- The audit evidence is precise: `InvitationService.invite()` line 217 has the hardcoded URL — single-line fix
- `WEBHOOK_EVENTS` already defines `org.member_added` as the third event (Phase 27 context confirmed three events: `user.created`, `subscription.updated`, `org.member_added`)
- Both 32-01 and 32-02 plans are pre-defined in the roadmap — planner should map decisions onto those two plan boundaries

</specifics>

<deferred>
## Deferred Ideas

- OrgCustomer-level `subscription.updated` (only fire when org has a linked billing subscription) — deferred with BILL-02
- Making `/accept-invite` path configurable via settings — not needed, products can subclass InvitationService

</deferred>

---

_Phase: 32-webhook-wiring-invite-url_
_Context gathered: 2026-03-13_
