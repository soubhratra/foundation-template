# Phase 23: Feature Entitlements - Context

**Gathered:** 2026-03-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Add a `has_feature(user, key)` utility that returns `True`/`False` based on the user's active billing plan and `BILLING_PLANS` settings dict, with Redis-cached results and immediate invalidation on plan-change webhooks. When billing is not installed, `has_feature()` returns `True` for all keys.

No feature flag UI, no per-user flag overrides, no feature flagging service (LaunchDarkly etc.) — those are future phases.

</domain>

<decisions>
## Implementation Decisions

### Feature key schema

- `BILLING_PLANS` is extended with a `feature_flags` dict per plan alongside the existing `features` display list:
  ```python
  "pro": {
      "features": ["Unlimited projects", "API access"],  # display only — unchanged
      "feature_flags": {
          "api_access": True,
          "advanced_analytics": True,
          "white_label": False,
      },
  }
  ```
- `has_feature()` reads `feature_flags`, never `features`
- Missing key in `feature_flags` → returns `False` (deny by default — new features restricted until explicitly granted per plan)
- No startup validation — trust the developer to keep keys consistent across plans

### No-subscription fallback

- User with no `Subscription` record → treated as **free plan** (check `free.feature_flags`)
- Unknown or unmapped `plan_id` on a Subscription → fall back to free plan + log a WARNING so developers notice the gap

### Code placement and billing-off fallback

- Real implementation lives in `apps/billing/entitlements.py` (`_has_feature()`)
- Public API lives in `apps/core/entitlements.py` (`has_feature()`), which always exists:
  ```python
  def has_feature(user, key: str) -> bool:
      try:
          from apps.billing.entitlements import _has_feature
          return _has_feature(user, key)
      except ImportError:
          return True  # billing not installed — all features accessible
  ```
- Public import path: `from apps.core.entitlements import has_feature` — one stable import regardless of billing presence
- No logging in the fallback path — returning `True` is correct behavior, not an error condition

### Cache design

- Cache key: `entitlements:{user.pk}` → full feature flags dict `{"api_access": True, ...}`
- One Redis entry per user, populated on first `has_feature()` call (cache-aside pattern)
- TTL: **300 seconds (5 minutes)**
- Cache backend: `default` (not `sessions`)
- Invalidation: `cache.delete(f"entitlements:{user.pk}")` triggered in `_handle_subscription_updated` inside `apps/billing/tasks.py` — immediate, fires on every `customer.subscription.updated` webhook

### Plan resolution path

- Add `plan_id` CharField (nullable, max_length=50) to the `Subscription` model — stores the internal plan key (e.g., `"pro"`)
- `plan_id` is set at webhook time inside `_handle_subscription_updated` in `tasks.py`: resolve `price_id → plan_id` via `PlanProviderMapping` and write it to the Subscription record alongside status/period updates
- `has_feature()` reads `user.billing_customer.subscription.plan_id` — one query, no join through PlanProviderMapping at call time

### Claude's Discretion

- Exact migration number for adding `plan_id` to Subscription (follows existing migration chain)
- Whether `_has_feature()` in billing takes an optional `plan_override` param for test convenience
- Exact logging format for the unknown-plan warning

</decisions>

<specifics>
## Specific Ideas

- The `try/except ImportError` pattern in `apps/core/entitlements.py` is the same philosophy as `require_active_subscription` — raise at the boundary, let the global handler format it — but applied to feature gating rather than subscription gating
- Phase 22 RBAC uses `RequireRole` as a Ninja Extra permission class; `has_feature()` is a plain utility function (not a decorator, not a permission class) — call it from wherever you need it: views, services, serializers, Celery tasks

</specifics>

<code_context>

## Existing Code Insights

### Reusable Assets

- `apps/billing/decorators.py` (`require_active_subscription`): Reference for PermissionDenied + `permission_denied_handler` error pattern — `has_feature()` is a simpler cousin (returns bool, doesn't raise)
- `apps/billing/tasks.py` (`_handle_subscription_updated`): Already updates Subscription status and period dates on webhook — add `plan_id` write and `cache.delete(f"entitlements:{user.pk}")` here
- `apps/billing/models.py` (`Subscription`): Add `plan_id` nullable CharField — migration needed
- `apps/billing/models.py` (`PlanProviderMapping`): Used at webhook time to resolve `price_id → plan_id`; not needed at `has_feature()` call time
- `apps/core/` — always present in both billing and no-billing projects; home for the public `has_feature()` stub

### Established Patterns

- `django_redis` cache already configured (`default` backend at `CACHE_REDIS_URL`) — use `from django.core.cache import cache` directly
- `BILLING_PLANS` dict in `config/settings/base.py` — adding `feature_flags` key per plan extends the existing structure without breaking anything
- Webhook handlers are private functions (`_handle_*`) called by the `process_stripe_event` Celery task — follow the same pattern for plan_id update logic
- Tests override CACHES to `LocMemCache` via `conftest test_isolation_settings` — `has_feature()` caching will work in tests without Redis

### Integration Points

- `apps/billing/models.py`: Add `plan_id` field to `Subscription`, create migration
- `apps/billing/tasks.py` (`_handle_subscription_updated`): Write `plan_id` + call `cache.delete()`
- `apps/billing/entitlements.py` (new file): `_has_feature()` implementation
- `apps/core/entitlements.py` (new file): Public `has_feature()` with ImportError fallback
- `config/settings/base.py` (`BILLING_PLANS`): Add `feature_flags` dict to each plan entry

</code_context>

<deferred>
## Deferred Ideas

- Per-user feature flag overrides (e.g., manually grant a feature to a specific user) — future phase
- Feature flag UI / admin dashboard — future admin phase
- Integration with a dedicated feature flagging service (LaunchDarkly, Unleash, etc.) — future phase
- `@require_feature("key")` decorator variant — convenience wrapper, easy to add after has_feature() exists
- Invalidation on `customer.subscription.deleted` — not decided today; 5-minute TTL covers the gap

</deferred>

---

_Phase: 23-feature-entitlements_
_Context gathered: 2026-03-12_
