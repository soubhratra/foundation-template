## Implementation Decisions

### Why `entitlements:{user.pk}` as the cache key (not user email or username)

`user.pk` (integer primary key) is immutable, compact, and collision-free. Email addresses can change; usernames can change; PKs do not. The cache key format `entitlements:{user.pk}` (e.g., `entitlements:42`) is easy to reason about and invalidate.

### Why 300-second TTL (not longer, not shorter)

300s (5 minutes) balances freshness with performance. A user who upgrades their plan sees the change reflected within 5 minutes at worst — acceptable for the template's use case. The webhook-triggered invalidation (`cache.delete(f"entitlements:{user.pk}")`) ensures plan changes propagate immediately in the common case (Stripe webhook received → cache cleared → next request reads fresh data).

**Trade-off:** A longer TTL (e.g., 1 hour) would reduce Redis load but increase the window of stale entitlements when webhook delivery is delayed. 300s was chosen as a conservative default that products can override.

### Why unconditional cache invalidation (even when plan resolution fails)

`_handle_subscription_updated` deletes the entitlement cache key regardless of whether the incoming webhook's price ID matched a `PlanProviderMapping` entry. This is intentional: an unrecognised price ID means the plan state is uncertain, and serving stale cached entitlements during uncertainty is worse than forcing a fresh (but potentially "free" plan) lookup.

**Implementation detail:** The `cache.delete()` call is placed after the `plan_id` write attempt, outside any conditional branch, so it runs even when `items.data` is empty or `plan_id` resolution logs a WARNING.

### Why billing-absent fallback returns `True` (not `False`)

When the billing module is not installed (e.g., a product scaffolded with `--without billing`), `has_feature()` cannot know which features are gated because the `BILLING_PLANS` configuration does not exist. Returning `False` by default would silently gate all features in billing-absent environments — breaking the product unexpectedly. Returning `True` (allow-all) is the safe default: the product works fully until billing is integrated.

**Alternative rejected:** Raising `ImproperlyConfigured` when billing is absent — this would break non-billing products at import time, which violates the modular scaffold design.

### Why `_resolve_plan_id()` returns `"free"` for missing subscriptions

The `"free"` plan is the conservative baseline — it has all feature flags set to `False`. A user with no billing relationship should have the same access as a new free plan user, not a paid user. Falling through to `"free"` ensures that unsubscribed, lapsed, or error-state users are not accidentally granted premium access.

### Why `has_feature()` never raises

Entitlement checks are called in hot paths (API endpoint permission checks, UI conditional rendering). An exception from `has_feature()` would surface as a 500 error on every guarded endpoint. The function catches all exceptions internally and falls back to `"free"` plan flags, logging a WARNING so the error is observable without being disruptive.
