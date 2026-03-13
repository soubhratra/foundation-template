# Phase 32: Webhook Wiring + Invitation URL Fix - Research

**Researched:** 2026-03-13
**Domain:** Django service wiring — connecting existing `fire_webhook_event()` to production callers; one-line settings fix
**Confidence:** HIGH

---

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions

**user.created — where and when to fire**

- Fire inside `MembershipService.add_member()` when the user joins their first org (not at signup, where there is no org context)
- No guard needed for "first org ever" — fire for the specific org being joined, scoped to that org
- Fire `user.created` first, then `org.member_added` (both async via `transaction.on_commit()` — ordering is best-effort)
- Payload: minimal — `{user_id, email}` matching the `WEBHOOK_EVENTS` example_payload defined in Phase 27

**subscription.updated — org resolution**

- Fire inside `_handle_subscription_updated()` in `apps/billing/tasks.py` after the DB update, via `transaction.on_commit()`
- Fire for all orgs where the subscribed user is a member — simple rule, no OrgCustomer filter
- Payload: `{user_id, plan, status}` matching the `WEBHOOK_EVENTS` example_payload defined in Phase 27

**org.member_added — wiring location**

- Fire inside `MembershipService.add_member()` after `user.created` (when first-time user) or instead of it (when existing user joins org)
- Payload: Claude's discretion (consistent with org context available in add_member)

**Invitation URL fix**

- Replace only the hardcoded domain in `InvitationService.invite()` line 217:
  - `f"https://app.example.com/accept-invite?token={invitation.token}"`
  - → `f"{settings.FRONTEND_URL}/accept-invite?token={invitation.token}"`
- The path `/accept-invite` stays hardcoded — products can subclass if they need a different path
- Add a regression test: override `FRONTEND_URL` to a test value and assert the generated `accept_url` starts with it

### Claude's Discretion

- `org.member_added` payload fields (user_id, org_slug, role — infer from what's available in add_member)
- Test approach for webhook wiring (mock `fire_webhook_event` at the caller level to avoid Celery in unit tests)

### Deferred Ideas (OUT OF SCOPE)

- OrgCustomer-level `subscription.updated` (only fire when org has a linked billing subscription) — deferred with BILL-02
- Making `/accept-invite` path configurable via settings — not needed, products can subclass InvitationService
  </user_constraints>

---

<phase_requirements>

## Phase Requirements

| ID      | Description                                                                                                                                          | Research Support                                                                                                                                                                           |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| HOOK-01 | Org admin can register webhook endpoints; deliveries are sent via Celery with exponential backoff (7 retries), HMAC-SHA256 signed, payload versioned | Infrastructure shipped in Phase 27. This phase wires callers: `MembershipService.add_member()` and `_handle_subscription_updated()` call `fire_webhook_event()` to produce real deliveries |
| ORG-02  | Org owner can invite members by email (72h token expiry); accepted via new signup or existing login using existing EmailAdapter                      | Invitation flow already works end-to-end. This phase fixes the hardcoded `https://app.example.com` domain in `InvitationService.invite()` line 217 to use `settings.FRONTEND_URL`          |

</phase_requirements>

---

## Summary

Phase 32 is purely wiring work — the delivery infrastructure (`fire_webhook_event`, Celery tasks, HMAC signing) was built in Phase 27 and is fully functional. The only gap is that no production code ever calls `fire_webhook_event()`. This phase adds those call sites and patches one hardcoded URL.

The two plans map cleanly to the two change surfaces: Plan 32-01 wires webhook events from `MembershipService.add_member()` (new method) and `_handle_subscription_updated()`; Plan 32-02 is a single-line fix to `InvitationService.invite()` plus a regression test.

The key architectural insight is that `MembershipService.add_member()` does not exist yet — the current `services.py` has `InvitationService.accept()` which creates `Membership` directly. The CONTEXT.md decision means the planner must introduce `add_member()` as a new `@classmethod` on `MembershipService`, then route `InvitationService.accept()` through it. This is the most significant structural change in the phase.

**Primary recommendation:** Introduce `MembershipService.add_member()` as the canonical membership creation point, route `InvitationService.accept()` through it, and call `fire_webhook_event()` from within it. Tests mock `fire_webhook_event` at the call-site level using `unittest.mock.patch`.

---

## Standard Stack

### Core

| Library                                  | Version             | Purpose                                    | Why Standard                                                                                       |
| ---------------------------------------- | ------------------- | ------------------------------------------ | -------------------------------------------------------------------------------------------------- |
| `apps.webhooks.utils.fire_webhook_event` | existing (Phase 27) | Dispatch webhook events                    | Already implemented; enqueues Celery tasks via `transaction.on_commit()`                           |
| `unittest.mock.patch`                    | stdlib              | Mock `fire_webhook_event` in tests         | Project pattern: mock at caller level to avoid Celery in unit tests (confirmed by `test_utils.py`) |
| `django.test.override_settings`          | stdlib              | Override `FRONTEND_URL` in regression test | Standard Django test pattern used throughout existing test suite                                   |

### Supporting

| Library                             | Version                | Purpose                          | When to Use                                                                                                  |
| ----------------------------------- | ---------------------- | -------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| `django.conf.settings.FRONTEND_URL` | existing (base.py:312) | Frontend base URL                | Already defined as `env("FRONTEND_URL", default="http://localhost:3000")` — just unused in InvitationService |
| `django.db.transaction.on_commit`   | Django built-in        | Defer webhook dispatch to commit | `fire_webhook_event()` already handles this internally — callers do NOT wrap in `on_commit` themselves       |

**Installation:** None. All dependencies are already installed.

---

## Architecture Patterns

### Recommended Project Structure

No new files needed for Plan 32-01. Changes are additions to existing files:

```
apps/api/
├── apps/orgs/services.py           # Add MembershipService.add_member(); route accept() through it; call fire_webhook_event()
├── apps/billing/tasks.py           # Add fire_webhook_event() call in _handle_subscription_updated()
└── tests/orgs/test_services.py     # Add webhook wiring tests + FRONTEND_URL regression test
```

For Plan 32-02, only one line changes in `apps/orgs/services.py`.

### Pattern 1: Introducing `MembershipService.add_member()`

**What:** New `@classmethod` on `MembershipService` that creates a `Membership` record and fires the two webhook events. `InvitationService.accept()` delegates membership creation to it.

**When to use:** Any time a user joins an org — currently only via invitation acceptance.

**Example:**

```python
# Source: CONTEXT.md decisions + existing MembershipService pattern in services.py
@classmethod
def add_member(cls, *, org, user, role: str = "member") -> object:
    """Create Membership and fire webhook events for the joining user."""
    from apps.orgs.models import Membership
    from apps.webhooks.utils import fire_webhook_event

    membership = Membership.objects.create(org=org, user=user, role=role)

    # Determine if this is user's first org membership
    is_first_org = not Membership.objects.filter(user=user).exclude(pk=membership.pk).exists()

    if is_first_org:
        fire_webhook_event(org, "user.created", {"user_id": user.pk, "email": user.email})

    fire_webhook_event(
        org,
        "org.member_added",
        {"org_slug": org.slug, "user_id": user.pk, "role": role},
    )

    return membership
```

**Critical note:** `fire_webhook_event()` manages `transaction.on_commit()` internally. Callers do NOT wrap calls in `on_commit` — confirmed by `utils.py` source and `connection.in_atomic_block` check on line 64.

### Pattern 2: Routing `InvitationService.accept()` through `add_member()`

**What:** Replace the inline `Membership.objects.create(...)` in `InvitationService.accept()` with a call to `MembershipService.add_member()`.

**Example:**

```python
# In InvitationService.accept() — replace existing Membership.objects.create call
with transaction.atomic():
    invitation.status = Invitation.Status.ACCEPTED
    invitation.save(update_fields=["status"])
    try:
        MembershipService.add_member(org=invitation.org, user=user, role=Membership.Role.MEMBER)
    except IntegrityError:
        raise ServiceError(
            code="ORG_006",
            message="You are already a member of this organization.",
            status_code=409,
        ) from None
```

**Note:** The `IntegrityError` catch around `Membership.objects.create` must be preserved — move it to wrap the `add_member()` call since `add_member()` calls `Membership.objects.create` internally.

### Pattern 3: Wiring `subscription.updated` in `billing/tasks.py`

**What:** Call `fire_webhook_event()` at the end of `_handle_subscription_updated()`, after the subscription DB update, firing for all orgs the subscribed user is a member of.

**Example:**

```python
# Source: CONTEXT.md decisions; append to _handle_subscription_updated() after subscription.save()
# B2B_START
_fire_subscription_updated_webhooks(customer.user, subscription)
# B2B_END
```

```python
def _fire_subscription_updated_webhooks(user, subscription) -> None:
    """Fire subscription.updated webhook for every org the user belongs to."""
    try:
        from apps.orgs.models import Membership
        from apps.webhooks.utils import fire_webhook_event

        orgs = [m.org for m in Membership.objects.filter(user=user).select_related("org")]
        payload = {
            "user_id": user.pk,
            "plan": subscription.plan_id or "",
            "status": subscription.status,
        }
        for org in orgs:
            fire_webhook_event(org, "subscription.updated", payload)
    except Exception:
        pass  # Never let webhook wiring crash Stripe event processing
```

**Critical:** Must be inside `B2B_START`/`B2B_END` markers. Must use lazy imports (same pattern as `_try_invalidate_org_member_caches()`). Must never raise — wrap in try/except so a webhook failure cannot crash Stripe event processing.

### Pattern 4: Invitation URL Fix

**What:** Single-line change in `InvitationService.invite()` line 217.

```python
# Before (line 217 in services.py):
"accept_url": f"https://app.example.com/accept-invite?token={invitation.token}",

# After:
"accept_url": f"{settings.FRONTEND_URL}/accept-invite?token={invitation.token}",
```

**Requires:** `from django.conf import settings` at the top of the import block (or lazy import inside the method — check if `settings` is already imported at module level). Current `services.py` imports only `from django.db import transaction` at module level; `settings` must be added.

### Anti-Patterns to Avoid

- **Wrapping `fire_webhook_event()` in `transaction.on_commit()`:** The function already handles `on_commit` internally (see `utils.py` lines 64-67). Double-wrapping causes the Celery task to be enqueued on commit of the outer `on_commit` callback — it will silently never fire.
- **Calling `fire_webhook_event()` outside try/except in `_handle_subscription_updated()`:** Any exception in webhook wiring would propagate out of the Stripe event handler and trigger Celery retry for the Stripe event — incorrect behavior.
- **Importing `fire_webhook_event` at module top-level in `billing/tasks.py`:** Creates circular import. Use lazy import inside the helper function body, same as the existing `_try_invalidate_org_member_caches()` pattern.
- **Forgetting `B2B_START`/`B2B_END` markers in billing/tasks.py:** Phase 31 scaffolder removes B2B code by stripping these marker blocks. Any billing webhook code not wrapped in markers will be left in non-B2B scaffolds.

---

## Don't Hand-Roll

| Problem                   | Don't Build                 | Use Instead                                                                      | Why                                                                               |
| ------------------------- | --------------------------- | -------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| Webhook delivery          | Custom HTTP dispatch        | `fire_webhook_event()`                                                           | Already implements HMAC signing, retry, circuit breaker, envelope versioning      |
| Transaction-safe dispatch | Manual `on_commit` wrapping | Call `fire_webhook_event()` directly                                             | It already checks `connection.in_atomic_block` and handles `on_commit` internally |
| First-org detection       | Complex user history query  | Simple `Membership.objects.filter(user=user).exclude(pk=membership.pk).exists()` | Straightforward count check                                                       |

---

## Common Pitfalls

### Pitfall 1: Missing `add_member()` — accepting invites no longer fires webhooks

**What goes wrong:** If `InvitationService.accept()` is not refactored to call `MembershipService.add_member()`, the webhook calls could be added to `accept()` directly — but then they are not centralized and future membership creation paths (e.g., direct admin action) would miss them.

**Why it happens:** `add_member()` doesn't exist yet; easy to just add `fire_webhook_event()` calls inline in `accept()`.

**How to avoid:** Create `add_member()` first, then route `accept()` through it.

**Warning signs:** Tests for webhook events added to `test_services.py` that call `InvitationService.accept()` but mock `fire_webhook_event` — these tests will catch the issue.

### Pitfall 2: `WEBHOOK_EVENTS` not defined in test settings

**What goes wrong:** Tests calling `fire_webhook_event()` will raise `ValueError("Unknown webhook event type: ...")` if `WEBHOOK_EVENTS` is not in the test settings.

**Why it happens:** Tests that don't use `override_settings(WEBHOOK_EVENTS=...)` rely on Django's default settings loading. The project's `base.py` defines `WEBHOOK_EVENTS` inside a `B2B_START` block, so it is always present.

**How to avoid:** Existing project settings include all three event types. Tests calling `fire_webhook_event()` can rely on default settings — no need for `override_settings`. Verify by checking `base.py` lines 671-684.

**Warning signs:** `ValueError: Unknown webhook event type` in test output.

### Pitfall 3: Circular import in `billing/tasks.py`

**What goes wrong:** Importing `fire_webhook_event` or `Membership` at module top-level in `billing/tasks.py` creates a circular import cycle: `billing.tasks` → `webhooks.utils` → (indirectly) → `orgs.models` → `billing.models` → `billing.tasks`.

**Why it happens:** Django resolves apps in order; circular cross-app imports at module level fail at startup.

**How to avoid:** Follow the established pattern in `_try_invalidate_org_member_caches()` — all cross-app imports inside the function body.

**Warning signs:** `ImportError` or `AppRegistryNotReady` at Django startup or test collection.

### Pitfall 4: `settings` not imported in `services.py` for the URL fix

**What goes wrong:** `NameError: name 'settings' is not defined` when `InvitationService.invite()` is called.

**Why it happens:** Current `apps/orgs/services.py` does not import `from django.conf import settings` at module level.

**How to avoid:** Add `from django.conf import settings` to the import block at the top of `services.py`.

**Warning signs:** `NameError` in any test that calls `InvitationService.invite()`.

### Pitfall 5: `first org` check must exclude the membership just created

**What goes wrong:** If `add_member()` checks `Membership.objects.filter(user=user).exists()` after creating the membership, it will always find at least one membership (the one just created) and never fire `user.created`.

**Why it happens:** Count happens after creation, so the new membership is already in the DB.

**How to avoid:** Use `.exclude(pk=membership.pk)` in the membership count query, or check before creating: `is_new = not Membership.objects.filter(user=user).exists()` before `Membership.objects.create(...)`.

---

## Code Examples

### Test pattern: mock `fire_webhook_event` at the caller level

```python
# Source: CONTEXT.md decisions + existing test_utils.py pattern
from unittest.mock import patch
import pytest

@pytest.mark.django_db
def test_add_member_fires_user_created_for_first_org(org, org_owner):
    """user.created fires when user joins their first org."""
    from django.contrib.auth import get_user_model
    User = get_user_model()

    new_user = User.objects.create_user(
        username="newuser", email="new@example.com", password="testpass"  # pragma: allowlist secret
    )

    with patch("apps.orgs.services.fire_webhook_event") as mock_fire:
        from apps.orgs.services import MembershipService
        MembershipService.add_member(org=org, user=new_user, role="member")

    calls = [call.args[1] for call in mock_fire.call_args_list]
    assert "user.created" in calls
    assert "org.member_added" in calls
```

### Test pattern: FRONTEND_URL regression test

```python
# Source: CONTEXT.md decisions + existing override_settings patterns in test suite
from unittest.mock import patch
import pytest
from django.test import override_settings

@pytest.mark.django_db
@override_settings(FRONTEND_URL="https://my-product.example.com")
def test_invite_accept_url_uses_frontend_url(org, org_owner, on_commit_immediately):
    """ORG-02 regression: invitation email accept_url uses settings.FRONTEND_URL."""
    from apps.orgs.services import InvitationService

    with patch("apps.notifications.utils.send_email") as mock_send:
        InvitationService.invite(org=org, invited_by=org_owner, email="guest@example.com")

    assert mock_send.called
    context = mock_send.call_args.kwargs["context"]
    assert context["accept_url"].startswith("https://my-product.example.com"), (
        f"accept_url should use FRONTEND_URL, got: {context['accept_url']}"
    )
```

### Existing `on_commit_immediately` fixture (no need to create)

```python
# Source: apps/api/conftest.py:143 — available to all tests
@pytest.fixture()
def on_commit_immediately(monkeypatch):
    """Patch transaction.on_commit to fire callbacks immediately."""
    # ... patches transaction.on_commit so send_email() fires synchronously
```

---

## State of the Art

| Old Approach                                                         | Current Approach                               | When Changed | Impact                                                                         |
| -------------------------------------------------------------------- | ---------------------------------------------- | ------------ | ------------------------------------------------------------------------------ |
| Inline `Membership.objects.create()` in `InvitationService.accept()` | Route through `MembershipService.add_member()` | Phase 32     | Centralizes webhook firing for all future membership creation paths            |
| No webhook callers                                                   | Three event call sites wired                   | Phase 32     | HOOK-01 fully satisfied — real deliveries can now be observed in delivery logs |
| Hardcoded `https://app.example.com` in invite email                  | `settings.FRONTEND_URL`                        | Phase 32     | ORG-02 fully satisfied — works in any environment                              |

---

## Open Questions

1. **`is_first_org` check: before or after `Membership.objects.create()`?**
   - What we know: If checked after creation, must use `.exclude(pk=membership.pk)` or it always returns True.
   - Recommendation: Check before creating (simpler, no exclude needed): `is_new_user = not Membership.objects.filter(user=user).exists()` then create membership, then fire events conditionally.

2. **Should `_handle_subscription_updated` fire webhooks before or after `_try_invalidate_org_member_caches`?**
   - What we know: Both are independent side effects; order doesn't affect correctness.
   - Recommendation: Fire webhooks after cache invalidation — consistent with "state is settled" before external notification.

---

## Validation Architecture

### Test Framework

| Property           | Value                                                                                           |
| ------------------ | ----------------------------------------------------------------------------------------------- |
| Framework          | pytest + pytest-django                                                                          |
| Config file        | `apps/api/pytest.ini` (or `pyproject.toml [tool.pytest.ini_options]`)                           |
| Quick run command  | `cd apps/api && python -m pytest tests/orgs/test_services.py tests/billing/test_tasks.py -x -q` |
| Full suite command | `cd apps/api && python -m pytest -x -q`                                                         |

### Phase Requirements → Test Map

| Req ID  | Behavior                                                  | Test Type | Automated Command                                                                                | File Exists? |
| ------- | --------------------------------------------------------- | --------- | ------------------------------------------------------------------------------------------------ | ------------ |
| HOOK-01 | `user.created` fires when first membership created        | unit      | `pytest tests/orgs/test_services.py::test_add_member_fires_user_created_for_first_org -x`        | Wave 0       |
| HOOK-01 | `org.member_added` fires on every membership creation     | unit      | `pytest tests/orgs/test_services.py::test_add_member_fires_org_member_added -x`                  | Wave 0       |
| HOOK-01 | `user.created` does NOT fire for subsequent orgs          | unit      | `pytest tests/orgs/test_services.py::test_add_member_no_user_created_for_second_org -x`          | Wave 0       |
| HOOK-01 | `subscription.updated` fires for each org user belongs to | unit      | `pytest tests/billing/test_tasks.py::test_subscription_updated_fires_webhook_for_member_orgs -x` | Wave 0       |
| ORG-02  | `accept_url` starts with `settings.FRONTEND_URL`          | unit      | `pytest tests/orgs/test_services.py::test_invite_accept_url_uses_frontend_url -x`                | Wave 0       |

### Sampling Rate

- **Per task commit:** `cd apps/api && python -m pytest tests/orgs/test_services.py tests/billing/test_tasks.py -x -q`
- **Per wave merge:** `cd apps/api && python -m pytest -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] New test cases in `tests/orgs/test_services.py` — covers HOOK-01 (add_member wiring) and ORG-02 (FRONTEND_URL regression)
- [ ] New test cases in `tests/billing/test_tasks.py` — covers HOOK-01 (subscription.updated wiring)

_(Existing test files exist; new test functions must be added within them. No new files needed.)_

---

## Sources

### Primary (HIGH confidence)

- `apps/api/apps/webhooks/utils.py` — `fire_webhook_event()` implementation; confirmed `transaction.on_commit()` is internal, callers do not wrap
- `apps/api/apps/orgs/services.py` — Current service implementations; confirmed `MembershipService.add_member()` does not exist; confirmed `settings` not imported; confirmed hardcoded URL at line 217
- `apps/api/apps/billing/tasks.py` — `_handle_subscription_updated()` at line 99; confirmed `B2B_START`/`B2B_END` marker pattern at line 156; confirmed lazy import pattern in `_try_invalidate_org_member_caches()`
- `apps/api/config/settings/base.py:312` — `FRONTEND_URL` defined
- `apps/api/config/settings/base.py:671-684` — `WEBHOOK_EVENTS` confirmed with all three event types and canonical payloads
- `apps/api/tests/webhooks/test_utils.py` — Confirmed `patch("apps.webhooks.tasks.deliver_webhook.delay")` test pattern and `transaction=True` requirement
- `apps/api/tests/orgs/test_services.py` — Existing InvitationService tests; target file for new regression test
- `apps/api/conftest.py:143` — `on_commit_immediately` fixture exists at root conftest

### Secondary (MEDIUM confidence)

- `.planning/STATE.md` Decisions log — `fire_webhook_event()` pattern confirmed from Phase 27 decisions
- `.planning/phases/32-webhook-wiring-invite-url/32-CONTEXT.md` — All implementation decisions locked

---

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — all libraries are existing project code, no new dependencies
- Architecture: HIGH — wiring points confirmed by direct code inspection; `add_member()` absence confirmed
- Pitfalls: HIGH — circular import and `on_commit` double-wrapping confirmed by reading actual implementation
- Test patterns: HIGH — existing test files inspected; `on_commit_immediately` fixture location confirmed

**Research date:** 2026-03-13
**Valid until:** Not time-sensitive — all findings are based on current codebase state, not external dependencies
