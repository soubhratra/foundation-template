# Phase 23: Feature Entitlements - Research

**Researched:** 2026-03-12
**Domain:** Django cache-aside pattern, billing plan resolution, ImportError-based optional module fallback
**Confidence:** HIGH

## Summary

Phase 23 is a self-contained utility layer that adds `has_feature(user, key) -> bool` to the codebase. All architectural decisions are locked in CONTEXT.md — the design is fully determined. Research confirms that every dependency required is already installed and working: `django_redis` is configured on the `default` cache backend, `PlanProviderMapping` has the `plan_id` field needed for resolution, and the project-wide `conftest.py` already overrides `CACHES` to `LocMemCache` so caching works in tests without Redis.

The three new files needed are small and focused: `apps/billing/entitlements.py` (the real implementation behind the billing guard), `apps/core/entitlements.py` (the stable public API with the ImportError fallback), and a Django migration adding `plan_id` to `Subscription`. The webhook invalidation is a targeted two-line addition to the existing `_handle_subscription_updated` function in `apps/billing/tasks.py`.

The biggest implementation risk is the Stripe webhook payload shape: `customer.subscription.updated` sends `items.data[0].price.id` as the price ID, not a top-level field. The plan resolution code must traverse that path to call `PlanProviderMapping.objects.get(price_id=..., provider="stripe")`. The current `_handle_subscription_updated` only reads top-level fields; this traversal is new.

**Primary recommendation:** Implement in two tasks — Task 1: model migration + `BILLING_PLANS` update + both entitlement files + unit tests. Task 2: webhook handler update (plan_id write + cache invalidation) + integration tests.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions

- `BILLING_PLANS` gets a `feature_flags` dict per plan alongside the existing `features` display list
- `has_feature()` reads `feature_flags`, never `features`
- Missing key in `feature_flags` returns `False` (deny by default)
- No startup validation of key consistency
- User with no Subscription → treated as free plan (check `free.feature_flags`)
- Unknown/unmapped `plan_id` → fall back to free plan + log WARNING
- Real implementation in `apps/billing/entitlements.py` as `_has_feature()`
- Public API in `apps/core/entitlements.py` as `has_feature()` with ImportError fallback returning `True`
- Public import path: `from apps.core.entitlements import has_feature` — one stable import
- No logging in the billing-off fallback path
- Cache key: `entitlements:{user.pk}` → full feature flags dict
- Cache-aside pattern: populated on first call, not eagerly
- TTL: 300 seconds (5 minutes)
- Cache backend: `default`
- Invalidation via `cache.delete(f"entitlements:{user.pk}")` in `_handle_subscription_updated` in `apps/billing/tasks.py`
- Add `plan_id` CharField (nullable, max_length=50) to `Subscription` model
- `plan_id` is set at webhook time in `_handle_subscription_updated`
- `has_feature()` reads `user.billing_customer.subscription.plan_id` — one query at call time

### Claude's Discretion

- Exact migration number for adding `plan_id` (follows existing chain: 0003 is last, so 0004)
- Whether `_has_feature()` takes an optional `plan_override` param for test convenience
- Exact logging format for the unknown-plan warning

### Deferred Ideas (OUT OF SCOPE)

- Per-user feature flag overrides
- Feature flag UI / admin dashboard
- Integration with LaunchDarkly, Unleash, etc.
- `@require_feature("key")` decorator variant
- Invalidation on `customer.subscription.deleted`
  </user_constraints>

<phase_requirements>

## Phase Requirements

| ID     | Description                                                                                                                     | Research Support                                                                                                                                                                            |
| ------ | ------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ENT-01 | `has_feature(user, "feature_key")` returns True/False based on the user's active billing plan and `BILLING_PLANS` settings dict | `BILLING_PLANS` dict confirmed in `config/settings/base.py` at line 488; `Subscription` model confirmed in `apps/billing/models.py`; cache-aside pattern documented below                   |
| ENT-02 | Entitlement results are cached in Redis and invalidated automatically when a billing plan-change webhook is processed           | `django_redis` confirmed as `default` backend; `_handle_subscription_updated` confirmed in `apps/billing/tasks.py`; `LocMemCache` override in conftest confirmed (tests work without Redis) |
| ENT-03 | When `--without billing`, `has_feature()` returns `True` for all keys (no billing = no gating)                                  | `try/except ImportError` pattern confirmed from `apps/core/` precedent; `apps/core/` is always present in both billing and no-billing projects                                              |

</phase_requirements>

## Standard Stack

### Core

| Library                           | Version     | Purpose                     | Why Standard                                                              |
| --------------------------------- | ----------- | --------------------------- | ------------------------------------------------------------------------- |
| `django.core.cache` (built-in)    | Django 5.2  | Cache read/write/delete     | Already used project-wide; `django_redis` backend configured on `default` |
| `django.conf.settings` (built-in) | Django 5.2  | Read `BILLING_PLANS` dict   | Standard Django settings access                                           |
| `logging` (stdlib)                | Python 3.12 | WARNING for unknown plan_id | Matches structlog-aware logging already in project                        |

### No New Dependencies

All required libraries are already installed. This phase adds no new packages to `pyproject.toml` or `uv.lock`.

**Installation:**

```bash
# No new packages — all dependencies already present
```

## Architecture Patterns

### File Layout

```
apps/
├── billing/
│   ├── entitlements.py       # NEW — _has_feature() implementation (billing-guarded)
│   ├── models.py             # MODIFY — add plan_id CharField to Subscription
│   ├── migrations/
│   │   └── 0004_subscription_plan_id.py  # NEW — nullable plan_id field
│   └── tasks.py              # MODIFY — add plan_id write + cache.delete() to _handle_subscription_updated
└── core/
    └── entitlements.py       # NEW — public has_feature() with ImportError fallback
config/
└── settings/
    └── base.py               # MODIFY — add feature_flags dict to each BILLING_PLANS entry
tests/
├── billing/
│   └── test_entitlements.py  # NEW — tests for _has_feature() and cache behavior
└── core/
    └── test_entitlements.py  # NEW — tests for public has_feature() including billing-off path
```

### Pattern 1: Cache-Aside (Lazy Population)

**What:** On first `has_feature()` call for a user, read from DB, write to cache, return value. On subsequent calls within TTL, read from cache without DB hit.

**When to use:** Any hot-path read that is stable between subscription changes.

**Example:**

```python
# apps/billing/entitlements.py
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

ENTITLEMENT_CACHE_TTL = 300  # 5 minutes


def _has_feature(user, key: str, plan_override: str | None = None) -> bool:
    """Check if user's billing plan includes the named feature flag.

    plan_override is for test convenience only — skips DB lookup.
    """
    if plan_override is not None:
        flags = _flags_for_plan(plan_override)
        return flags.get(key, False)

    cache_key = f"entitlements:{user.pk}"
    cached = cache.get(cache_key)

    if cached is None:
        plan_id = _resolve_plan_id(user)
        cached = _flags_for_plan(plan_id)
        cache.set(cache_key, cached, timeout=ENTITLEMENT_CACHE_TTL)

    return cached.get(key, False)


def _resolve_plan_id(user) -> str:
    """Return the internal plan_id for user, defaulting to 'free'."""
    try:
        plan_id = user.billing_customer.subscription.plan_id
    except Exception:
        return "free"

    if not plan_id:
        return "free"

    billing_plans = settings.BILLING_PLANS
    if plan_id not in billing_plans:
        logger.warning(
            "entitlements: unknown plan_id=%r for user=%s — falling back to free",
            plan_id,
            user.pk,
        )
        return "free"

    return plan_id


def _flags_for_plan(plan_id: str) -> dict:
    """Return the feature_flags dict for the given plan_id, or empty dict."""
    billing_plans = settings.BILLING_PLANS
    plan = billing_plans.get(plan_id, billing_plans.get("free", {}))
    return plan.get("feature_flags", {})
```

### Pattern 2: ImportError Fallback (Billing-Off Mode)

**What:** `apps/core/entitlements.py` always exists. It attempts to import `_has_feature` from `apps.billing.entitlements`. If billing is not installed (`ImportError`), it returns `True` for every call.

**When to use:** Any optional module that must present a no-op interface when absent. Matches the same philosophy as `require_active_subscription` but inverted (True instead of raising).

**Example:**

```python
# apps/core/entitlements.py
def has_feature(user, key: str) -> bool:
    """Return True if user's plan includes the named feature flag.

    When billing module is not installed (--without billing), returns True
    for every key — no features are gated when there is no billing system.
    """
    try:
        from apps.billing.entitlements import _has_feature
        return _has_feature(user, key)
    except ImportError:
        return True
```

### Pattern 3: Webhook Cache Invalidation (Targeted Delete)

**What:** On `customer.subscription.updated`, after writing `plan_id` to the Subscription record, immediately delete the user's entitlement cache entry.

**Where:** Added to the end of `_handle_subscription_updated` in `apps/billing/tasks.py`.

**Example:**

```python
# Addition to _handle_subscription_updated in apps/billing/tasks.py
from django.core.cache import cache

# ... existing subscription.save() call ...

# Write plan_id resolved from webhook items data
price_id = _extract_price_id_from_event(event_data)
if price_id:
    from apps.billing.models import PlanProviderMapping
    try:
        mapping = PlanProviderMapping.objects.get(
            price_id=price_id, provider="stripe", is_active=True
        )
        subscription.plan_id = mapping.plan_id
        subscription.save(update_fields=["plan_id", "updated_at"])
    except PlanProviderMapping.DoesNotExist:
        logger.warning(
            "customer.subscription.updated: no PlanProviderMapping for price_id=%s",
            price_id,
        )

# Invalidate entitlement cache regardless of plan resolution outcome
cache.delete(f"entitlements:{customer.user.pk}")
```

### Anti-Patterns to Avoid

- **Resolving plan via `PlanProviderMapping` at call time:** `has_feature()` must NOT query `PlanProviderMapping` — that table is only consulted at webhook time to write `plan_id` to `Subscription`. The call-time path reads `subscription.plan_id` directly.
- **Raising exceptions from `has_feature()`:** It must always return `bool`. Any lookup failure (no customer, no subscription, unknown plan) must degrade gracefully to `False` (or `True` in the billing-off case). Never raise.
- **Storing individual flags as separate cache keys:** The design stores one dict per user (`entitlements:{user.pk}`) to allow a single `cache.delete()` call to invalidate all flags on plan change.
- **Caching at the plan level instead of user level:** User-level caching is required because future phases may add per-user overrides. Plan-level caching would make that harder and doesn't reduce DB queries for the common case.

## Don't Hand-Roll

| Problem                               | Don't Build                  | Use Instead                                            | Why                                                                                     |
| ------------------------------------- | ---------------------------- | ------------------------------------------------------ | --------------------------------------------------------------------------------------- |
| Cache TTL management                  | Custom expiry logic          | `cache.set(..., timeout=300)`                          | Django cache handles expiry atomically                                                  |
| Idempotent cache invalidation         | Check-then-delete            | `cache.delete()` (unconditional)                       | `delete()` is a no-op on a cache miss; checking first adds a round-trip for no benefit  |
| Price-to-plan resolution at call time | DB lookup in `has_feature()` | Read `subscription.plan_id` written by webhook handler | Webhook already resolved the mapping; doing it again on every feature check is wasteful |

## Common Pitfalls

### Pitfall 1: Stripe Webhook Payload Shape for Price ID

**What goes wrong:** `customer.subscription.updated` does not have a top-level `price_id` field. Developers expect `event_data.get("price_id")` but get `None`.

**Why it happens:** Stripe wraps subscription items in `items.data[0].price.id`. The top-level event data for subscription events contains `status`, `cancel_at_period_end`, `current_period_start`, `current_period_end`, and `customer` — not price information.

**How to avoid:** Extract price ID via: `event_data.get("items", {}).get("data", [{}])[0].get("price", {}).get("id", "")`. Guard against empty `items.data` list.

**Warning signs:** `plan_id` column on `Subscription` stays `None` for all users after upgrade/downgrade webhook fires.

### Pitfall 2: N+1 Query in `_resolve_plan_id`

**What goes wrong:** `user.billing_customer.subscription.plan_id` traverses two FK relationships. If called in a loop (e.g., in a list endpoint), each call issues two extra queries.

**Why it happens:** Django ORM does not pre-fetch related objects unless `select_related` is used.

**How to avoid:** This is an accepted single-call utility. For bulk contexts, callers must `select_related("billing_customer__subscription")` before calling `has_feature()`. The N+1 guard in `conftest.py` will catch accidental bulk usage in tests.

**Warning signs:** `nplusone.core.exceptions.NPlusOneError` in tests that call `has_feature()` in a loop.

### Pitfall 3: Cache Not Invalidated When `PlanProviderMapping` Is Missing

**What goes wrong:** If the Stripe webhook fires for a plan with no `PlanProviderMapping` entry, the code logs a warning and skips the `plan_id` write — but must still call `cache.delete()`. If invalidation is placed only in the success branch, a downgrade to an unmapped plan leaves the old entitlement cache intact for 5 minutes.

**How to avoid:** Place `cache.delete(f"entitlements:{customer.user.pk}")` unconditionally after the plan resolution block, not inside the `try` branch.

**Warning signs:** After a plan downgrade to an unmapped plan, `has_feature()` still returns `True` for restricted features within the TTL window.

### Pitfall 4: `has_feature()` Called Before `billing_customer` Is Set

**What goes wrong:** Newly created users (via signup) may not yet have a `Customer` record created by the billing signal. Calling `has_feature()` immediately after creation raises `RelatedObjectDoesNotExist`.

**Why it happens:** Django signals are synchronous but the `Customer` creation signal (`post_save` on User) runs after the save. In tests, signal is active — but if billing is removed, no signal fires.

**How to avoid:** The `except Exception: return "free"` guard in `_resolve_plan_id` already covers this. Confirm the `except` block is broad enough to catch `RelatedObjectDoesNotExist` (it is — that is a subclass of `Exception`).

### Pitfall 5: Tests Break When LocMemCache Is Used Instead of Redis

**What goes wrong:** Tests run with `LocMemCache` (set by `test_isolation_settings` in `conftest.py`). If `_has_feature()` code imports `django_redis` directly instead of using `from django.core.cache import cache`, it will bypass the `LocMemCache` override.

**How to avoid:** Always use `from django.core.cache import cache` — never `from django_redis.cache import RedisCache`. The test override in `conftest.py` targets the Django cache framework, not the backend directly.

## Code Examples

### BILLING_PLANS Settings Extension

```python
# config/settings/base.py — add feature_flags to each plan entry
BILLING_PLANS: dict = {
    "free": {
        "name": "Free",
        "stripe_price_id_monthly": "",
        "stripe_price_id_annual": "",
        "trial_days": 0,
        "features": ["Up to 3 projects", "Community support"],
        "feature_flags": {
            "api_access": False,
            "advanced_analytics": False,
            "white_label": False,
        },
    },
    "pro": {
        "name": "Pro",
        "stripe_price_id_monthly": env("STRIPE_PRICE_PRO_MONTHLY", default=""),
        "stripe_price_id_annual": env("STRIPE_PRICE_PRO_ANNUAL", default=""),
        "trial_days": 14,
        "features": ["Unlimited projects", "Priority support", "API access"],
        "feature_flags": {
            "api_access": True,
            "advanced_analytics": True,
            "white_label": False,
        },
    },
    "enterprise": {
        "name": "Enterprise",
        "stripe_price_id_monthly": env("STRIPE_PRICE_ENTERPRISE_MONTHLY", default=""),
        "stripe_price_id_annual": env("STRIPE_PRICE_ENTERPRISE_ANNUAL", default=""),
        "trial_days": 0,
        "features": ["Everything in Pro", "Dedicated support", "Custom contracts", "SLA"],
        "feature_flags": {
            "api_access": True,
            "advanced_analytics": True,
            "white_label": True,
        },
    },
}
```

### Django Migration for plan_id Field

```python
# apps/billing/migrations/0004_subscription_plan_id.py
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ("billing", "0003_fix_stub_pro_monthly_price_id"),
    ]
    operations = [
        migrations.AddField(
            model_name="subscription",
            name="plan_id",
            field=models.CharField(max_length=50, null=True, blank=True),
        ),
    ]
```

### Extracting Price ID from Stripe Subscription Updated Payload

```python
# Helper used inside _handle_subscription_updated
def _extract_price_id_from_event(event_data: dict) -> str:
    """Extract the active price ID from a subscription.updated event payload."""
    items = event_data.get("items", {})
    data_list = items.get("data", [])
    if not data_list:
        return ""
    return data_list[0].get("price", {}).get("id", "")
```

### Consumer Example (ENT-01 usage pattern)

```python
# Anywhere in the application: views, services, tasks
from apps.core.entitlements import has_feature

def export_advanced_report(request):
    if not has_feature(request.user, "advanced_analytics"):
        raise PermissionDenied("Advanced analytics not available on your plan.")
    ...
```

## State of the Art

| Old Approach               | Current Approach                        | When Changed          | Impact                                                              |
| -------------------------- | --------------------------------------- | --------------------- | ------------------------------------------------------------------- |
| Per-request DB plan lookup | Cache-aside with 5-min TTL              | Phase 23 (this phase) | Eliminates repeated DB queries on gated endpoints                   |
| No plan_id on Subscription | `plan_id` CharField set at webhook time | Phase 23 (this phase) | Decouples entitlement reads from `PlanProviderMapping` at call time |

## Open Questions

1. **Stripe items.data shape for multi-item subscriptions**
   - What we know: Standard Stripe subscriptions have one item in `items.data`. `data[0].price.id` is the price being billed.
   - What's unclear: If a subscription has multiple items (usage-based metered billing), `data[0]` may not be the right item.
   - Recommendation: Use `data[0]` for now — this template has single-plan subscriptions. Add a comment noting the multi-item limitation.

2. **plan_id field on `Subscription` for existing subscriptions**
   - What we know: After migration, all existing `Subscription` rows will have `plan_id=None`.
   - What's unclear: Whether to backfill via a data migration or wait for the next webhook.
   - Recommendation: No backfill — the `_resolve_plan_id` fallback-to-free logic handles `None` plan_id correctly. A WARNING is logged. For a template, this is acceptable; product teams can backfill if needed.

## Validation Architecture

### Test Framework

| Property           | Value                                                                                                   |
| ------------------ | ------------------------------------------------------------------------------------------------------- |
| Framework          | pytest + pytest-django                                                                                  |
| Config file        | `apps/api/pyproject.toml` (`[tool.pytest.ini_options]`)                                                 |
| Quick run command  | `cd apps/api && python -m pytest tests/billing/test_entitlements.py tests/core/test_entitlements.py -x` |
| Full suite command | `cd apps/api && python -m pytest`                                                                       |

### Phase Requirements → Test Map

| Req ID | Behavior                                                                 | Test Type   | Automated Command                                                                                                     | File Exists? |
| ------ | ------------------------------------------------------------------------ | ----------- | --------------------------------------------------------------------------------------------------------------------- | ------------ |
| ENT-01 | `has_feature(user, key)` returns True for plan with flag=True            | unit        | `pytest tests/billing/test_entitlements.py::TestHasFeature::test_returns_true_for_enabled_flag -x`                    | Wave 0       |
| ENT-01 | `has_feature(user, key)` returns False for plan with flag=False          | unit        | `pytest tests/billing/test_entitlements.py::TestHasFeature::test_returns_false_for_disabled_flag -x`                  | Wave 0       |
| ENT-01 | `has_feature(user, key)` returns False for missing key (deny by default) | unit        | `pytest tests/billing/test_entitlements.py::TestHasFeature::test_missing_key_returns_false -x`                        | Wave 0       |
| ENT-01 | User with no Subscription treated as free plan                           | unit        | `pytest tests/billing/test_entitlements.py::TestHasFeature::test_no_subscription_uses_free_plan -x`                   | Wave 0       |
| ENT-01 | Unknown plan_id falls back to free + logs WARNING                        | unit        | `pytest tests/billing/test_entitlements.py::TestHasFeature::test_unknown_plan_id_falls_back_to_free -x`               | Wave 0       |
| ENT-02 | Second call within TTL reads from cache (no DB query)                    | unit        | `pytest tests/billing/test_entitlements.py::TestCaching::test_second_call_uses_cache -x`                              | Wave 0       |
| ENT-02 | Cache invalidated on subscription.updated webhook                        | integration | `pytest tests/billing/test_entitlements.py::TestCacheInvalidation::test_cache_invalidated_on_subscription_updated -x` | Wave 0       |
| ENT-03 | `has_feature()` returns True when billing not installed                  | unit        | `pytest tests/core/test_entitlements.py::TestBillingOffFallback::test_returns_true_when_billing_absent -x`            | Wave 0       |
| ENT-03 | No ImportError when billing absent                                       | unit        | `pytest tests/core/test_entitlements.py::TestBillingOffFallback::test_no_import_error -x`                             | Wave 0       |

### Sampling Rate

- **Per task commit:** `cd apps/api && python -m pytest tests/billing/test_entitlements.py tests/core/test_entitlements.py -x`
- **Per wave merge:** `cd apps/api && python -m pytest`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/billing/test_entitlements.py` — covers ENT-01, ENT-02
- [ ] `tests/core/test_entitlements.py` — covers ENT-03

_(Existing `tests/billing/conftest.py` and global `tests/conftest.py` already provide `user`, `customer`, `subscription` fixtures and `LocMemCache` override — no new conftest needed)_

## Sources

### Primary (HIGH confidence)

- Direct code inspection — `apps/api/apps/billing/models.py` — confirmed `Subscription` fields, `PlanProviderMapping.plan_id` field name
- Direct code inspection — `apps/api/apps/billing/tasks.py` — confirmed `_handle_subscription_updated` signature and structure
- Direct code inspection — `apps/api/config/settings/base.py:488` — confirmed `BILLING_PLANS` structure with `features` list
- Direct code inspection — `apps/api/tests/conftest.py:70-73` — confirmed `LocMemCache` override in `test_isolation_settings`
- Direct code inspection — `apps/api/apps/billing/migrations/` — confirmed last migration is `0003`, next is `0004`
- Direct code inspection — `apps/api/apps/billing/decorators.py` — confirmed `require_active_subscription` pattern for reference
- Direct code inspection — `apps/api/apps/accounts/permissions.py` — confirmed `RequireRole` pattern (plain-function alternative chosen for `has_feature`)

### Secondary (MEDIUM confidence)

- Stripe documentation pattern (training knowledge): `customer.subscription.updated` payload shape — `items.data[0].price.id` is the price ID. Flagged in Open Questions for verification at implementation time.

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — all dependencies confirmed present via direct file inspection
- Architecture: HIGH — design is fully locked in CONTEXT.md; code patterns confirmed from existing codebase
- Pitfalls: HIGH (Pitfalls 1, 2, 3, 4, 5) — derived from direct code reading of existing patterns; Stripe payload shape is MEDIUM (training knowledge)
- Test map: HIGH — test infrastructure confirmed via direct inspection of `conftest.py` and pytest config

**Research date:** 2026-03-12
**Valid until:** 2026-04-12 (stable Django/cache APIs — low churn)
