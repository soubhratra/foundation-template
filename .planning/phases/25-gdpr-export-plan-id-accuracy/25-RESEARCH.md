# Phase 25: GDPR Export plan_id Accuracy - Research

**Researched:** 2026-03-12
**Domain:** Django ORM — AccountExportService patch + pytest-django
**Confidence:** HIGH

---

<phase_requirements>

## Phase Requirements

| ID      | Description                                                                              | Research Support                                                                                                             |
| ------- | ---------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| GDPR-02 | Authenticated user can export all personal data as JSON via `GET /api/v1/account/export` | Fix to `AccountExportService.export()` closes INT-03 gap: reads `sub.plan_id` from ORM instead of returning hardcoded `None` |

</phase_requirements>

---

## Summary

Phase 25 is a single-file surgical fix. The `AccountExportService.export()` method in
`apps/api/apps/accounts/services.py` already accesses the `Subscription` record (`sub =
customer.subscription`) but then returns `plan_id = None` with a comment explaining that
`plan_id` was not stored on the model. Phase 23 added `Subscription.plan_id` via migration
`0004_subscription_plan_id.py`. The fix is therefore a one-line change: replace the
`plan_id = None` assignment with `plan_id = sub.plan_id`.

The existing test file (`tests/accounts/test_export.py`) already asserts that
`billing.plan_id` is `None` for a user without a Customer row — this test is a no-regression
guard that will continue to pass. A new test must cover the positive case: a user whose
`Subscription` row has a non-null `plan_id` should receive that value in the export response.

No new dependencies, no schema changes, no migration required. The change is entirely in
`apps/accounts/services.py` and `tests/accounts/test_export.py`.

**Primary recommendation:** Replace `plan_id = None` in the `try` block inside
`AccountExportService.export()` with `plan_id = sub.plan_id`. Add one pytest case that
creates a `Subscription` with `plan_id="pro"` and asserts the export returns `"plan_id": "pro"`.

---

## Standard Stack

### Core

| Library                | Version | Purpose                                                     | Why Standard                                   |
| ---------------------- | ------- | ----------------------------------------------------------- | ---------------------------------------------- |
| Django ORM             | 5.1+    | Reads `Subscription.plan_id`                                | Project-wide ORM; field already migrated       |
| pytest-django          | 4.9+    | Test DB access via `@pytest.mark.django_db` or `db` fixture | Established project test stack                 |
| ninja_extra TestClient | 0.21+   | Authenticated endpoint testing                              | Required by `tests/accounts/conftest.py` patch |

### No New Libraries

This phase requires zero new dependencies. All needed pieces already exist in the codebase.

---

## Architecture Patterns

### Relevant Code Paths

```
apps/api/
├── apps/accounts/services.py          # AccountExportService.export() — ONE LINE CHANGE
├── apps/billing/models.py             # Subscription.plan_id (CharField, null=True, blank=True)
└── tests/accounts/
    ├── conftest.py                    # Session-scoped patch: ninja TestClient → ninja_extra
    └── test_export.py                 # Existing tests + NEW plan_id round-trip test
```

### The Broken Code (exact lines 239–243 in services.py)

```python
try:
    sub = customer.subscription
    subscription_status = sub.status
    # plan_id is not stored on Subscription directly — no Stripe IDs in export
    plan_id = None          # <-- THIS IS WRONG since Phase 23 added the field
except Exception:
    subscription_status = None
    plan_id = None
```

### The Fix

```python
try:
    sub = customer.subscription
    subscription_status = sub.status
    plan_id = sub.plan_id   # reads from Subscription.plan_id (added in Phase 23 migration 0004)
except Exception:
    subscription_status = None
    plan_id = None
```

### New Test Pattern

Follow the existing fixture pattern in `tests/accounts/test_export.py`. The
`export_user_with_billing` fixture already sets `stripe_customer_id` on `Customer`.
The new test extends that pattern to also create a `Subscription` row:

```python
@pytest.fixture
def export_user_with_plan(db, export_user):
    """User with a Customer + Subscription with an explicit plan_id."""
    from apps.billing.models import Customer, Subscription, SubscriptionStatus

    customer, _ = Customer.objects.get_or_create(user=export_user)
    Subscription.objects.update_or_create(
        customer=customer,
        defaults={
            "plan_id": "pro",
            "status": SubscriptionStatus.ACTIVE,
        },
    )
    return export_user


def test_export_billing_plan_id_round_trip(self, db, export_user_with_plan) -> None:
    """billing.plan_id matches the value stored on Subscription.plan_id."""
    from apps.accounts.controllers import AccountController
    from ninja.testing import TestClient

    client = TestClient(AccountController)
    client.force_login(export_user_with_plan)
    response = client.get("/export")

    billing = response.json().get("billing", {})
    assert billing.get("plan_id") == "pro", (
        f"Expected billing.plan_id='pro', got {billing.get('plan_id')!r}. "
        "AccountExportService.export() must read sub.plan_id from the ORM."
    )
```

### Anti-Patterns to Avoid

- **Do not expose `stripe_subscription_id` or `stripe_customer_id`** — `test_export_excludes_stripe_ids` guards this; fix must not break it.
- **Do not add a new `except` branch** — the outer `except Exception` already handles missing subscriptions; keep the fallback `plan_id = None` there.
- **Do not use `select_related`** — the subscription is accessed via `customer.subscription` which is a reverse OneToOne; `customer.subscription` issues one additional query, which is acceptable for a GDPR export (low frequency). Adding `select_related` on the customer query is valid but not required.

---

## Don't Hand-Roll

| Problem        | Don't Build                                    | Use Instead                     | Why                                                                                              |
| -------------- | ---------------------------------------------- | ------------------------------- | ------------------------------------------------------------------------------------------------ |
| plan_id lookup | Custom resolver querying `PlanProviderMapping` | `sub.plan_id` direct field read | `plan_id` is already stored on `Subscription` since Phase 23 migration; no mapping lookup needed |

---

## Common Pitfalls

### Pitfall 1: Subscription does not always exist

**What goes wrong:** `customer.subscription` raises `Subscription.DoesNotExist` (RelatedObjectDoesNotExist) when no subscription row exists.
**Why it happens:** OneToOne reverse access raises on missing related object.
**How to avoid:** The existing `except Exception` block already catches this and returns `plan_id = None`. Keep it — the fix only changes the assignment inside the `try` block.
**Warning signs:** Test `test_export_billing_no_customer` would fail if the fallback is broken.

### Pitfall 2: plan_id is None for subscriptions created before Phase 23

**What goes wrong:** For `Subscription` rows created before the `0004` migration was applied, `plan_id` will be `None` (field default is `null=True`).
**Why it happens:** Migration added the field with `null=True, blank=True` — existing rows default to NULL.
**How to avoid:** This is correct expected behaviour. Returning `None` when the field is `None` is not a bug — only returning `None` when the field has a real value is the bug.
**Warning signs:** No warning needed — this is a no-regression case.

### Pitfall 3: Conftest scope — ninja TestClient patch

**What goes wrong:** Tests fail with `AttributeError: 'TestClient' object has no attribute 'force_login'` if conftest is not loaded.
**Why it happens:** The session-scoped fixture in `tests/accounts/conftest.py` patches `ninja.testing.TestClient` and injects `force_login()`. Without it, the test pattern used throughout the suite fails.
**How to avoid:** The new test goes in `tests/accounts/test_export.py` — same directory as the conftest. No action needed; it applies automatically.

---

## Code Examples

### Full context of change site (services.py lines ~236–265)

Current (broken):

```python
# Source: apps/api/apps/accounts/services.py lines 239-243
try:
    sub = customer.subscription
    subscription_status = sub.status
    # plan_id is not stored on Subscription directly — no Stripe IDs in export
    plan_id = None
except Exception:
    subscription_status = None
    plan_id = None
```

Fixed:

```python
try:
    sub = customer.subscription
    subscription_status = sub.status
    plan_id = sub.plan_id  # Subscription.plan_id added in Phase 23 (migration 0004)
except Exception:
    subscription_status = None
    plan_id = None
```

### Subscription model field (billing/models.py line 49)

```python
# Source: apps/api/apps/billing/models.py
plan_id = models.CharField(max_length=50, null=True, blank=True)
```

---

## State of the Art

| Old Approach                                                                | Current Approach                                      | When Changed            | Impact                                  |
| --------------------------------------------------------------------------- | ----------------------------------------------------- | ----------------------- | --------------------------------------- |
| `plan_id = None` hardcoded (Phase 21 comment: "not stored on Subscription") | `plan_id = sub.plan_id` (field exists since Phase 23) | Phase 23 migration 0004 | Export now reflects actual billing plan |

**The original comment** in services.py — `"plan_id is not stored on Subscription directly"` — was accurate when Phase 21 was written. Phase 23 added the field. The comment and the `None` assignment both need to be removed/replaced.

---

## Validation Architecture

### Test Framework

| Property           | Value                                                              |
| ------------------ | ------------------------------------------------------------------ |
| Framework          | pytest 8.0+ with pytest-django 4.9+                                |
| Config file        | `apps/api/pyproject.toml` (`[tool.pytest.ini_options]`)            |
| Quick run command  | `cd apps/api && python -m pytest tests/accounts/test_export.py -x` |
| Full suite command | `cd apps/api && python -m pytest tests/accounts/ -x`               |

### Phase Requirements → Test Map

| Req ID  | Behavior                                                                      | Test Type | Automated Command                                                  | File Exists?                                        |
| ------- | ----------------------------------------------------------------------------- | --------- | ------------------------------------------------------------------ | --------------------------------------------------- |
| GDPR-02 | `GET /api/v1/account/export` returns actual `plan_id` for subscribed user     | unit (DB) | `cd apps/api && python -m pytest tests/accounts/test_export.py -x` | ✅ (existing) + ❌ new round-trip test (Wave 0 gap) |
| GDPR-02 | Export returns `plan_id: null` for users without subscription (no regression) | unit (DB) | same command                                                       | ✅ `test_export_billing_no_customer`                |

### Sampling Rate

- **Per task commit:** `cd apps/api && python -m pytest tests/accounts/test_export.py -x`
- **Per wave merge:** `cd apps/api && python -m pytest tests/accounts/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/accounts/test_export.py::TestExportEndpoint::test_export_billing_plan_id_round_trip` — covers GDPR-02 positive plan_id case; file exists but method does not yet exist

---

## Open Questions

None. The scope is fully defined by the code inspection. The `Subscription.plan_id` field exists, is nullable, is already on the `customer.subscription` object that the service accesses. The only work is removing the hardcoded `None` and writing the positive-case test.

---

## Sources

### Primary (HIGH confidence)

- Direct code read: `apps/api/apps/accounts/services.py` — confirmed `plan_id = None` hardcoded in `AccountExportService.export()`
- Direct code read: `apps/api/apps/billing/models.py` — confirmed `Subscription.plan_id = CharField(max_length=50, null=True, blank=True)`
- Direct code read: `apps/api/apps/billing/migrations/0004_subscription_plan_id.py` — confirmed migration exists and applied field
- Direct code read: `tests/accounts/test_export.py` — confirmed existing tests, their fixture patterns, and what is missing
- Direct code read: `tests/accounts/conftest.py` — confirmed TestClient patch, `force_login` injection, fixture scope

### Secondary (MEDIUM confidence)

- `.planning/STATE.md` decision log entry: `[Phase 21-gdpr-baseline]: GDPR export plan_id is None — Subscription model stores stripe_subscription_id not internal plan_id; exposing Stripe ID would violate no-Stripe-IDs requirement` — confirms why `None` was written at the time and validates that the fix (using the non-Stripe `plan_id` field) is safe.

---

## Metadata

**Confidence breakdown:**

- What to change: HIGH — exact lines identified, no ambiguity
- How to test: HIGH — existing test pattern is clear, new fixture follows established pattern
- Regression risk: HIGH confidence LOW risk — existing `test_export_excludes_stripe_ids` guards the no-Stripe-ID invariant; `test_export_billing_no_customer` guards null fallback

**Research date:** 2026-03-12
**Valid until:** Stable — no external dependencies, no third-party API surface
