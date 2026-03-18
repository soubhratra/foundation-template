# Feature Entitlements

> Defines the plan-based feature gating system: `has_feature(user, key)` checks a user's subscription plan against a `BILLING_PLANS` feature-flags dict, with cache-aside caching and billing-absent fallback.

## Overview

Feature entitlements bridge the billing system and application code. The single public API is `has_feature(user, key)` — a boolean function that never raises, defaults to deny (free plan) when billing is present, and defaults to allow-all when the billing module is absent (safe for non-billing scaffolds).

The check is cached per-user with a 300-second TTL (Django's cache framework) and invalidated immediately on `customer.subscription.updated` webhooks. This means plan changes propagate within 5 minutes in the worst case (delayed webhook) and immediately in the common case (webhook received → cache cleared).

See also: `openspec/specs/organization-model/spec.md` for `has_org_feature()`, the org-context variant.

## Requirements

### Requirement: has_feature() Public API with Deny-by-Default

The system SHALL expose `has_feature(user, key)` as the single public entitlement check that returns a boolean and never raises.

#### Scenario: User with active pro plan has api_access

- **WHEN** a user's subscription has `plan_id = "pro"`
- **AND** the `BILLING_PLANS["pro"]["feature_flags"]["api_access"]` is `True`
- **THEN** `has_feature(user, "api_access")` SHALL return `True`

#### Scenario: User with free plan does not have api_access

- **WHEN** a user's subscription has `plan_id = "free"`
- **AND** the `BILLING_PLANS["free"]["feature_flags"]["api_access"]` is `False`
- **THEN** `has_feature(user, "api_access")` SHALL return `False`

#### Scenario: Unknown plan ID falls back to free plan flags

- **WHEN** `Subscription.plan_id` contains a value not in `BILLING_PLANS`
- **THEN** `_flags_for_plan()` SHALL fall back to the `"free"` plan feature flags
- **AND** a `WARNING` log SHALL be emitted

#### Scenario: Missing subscription chain resolves to free plan

- **WHEN** a user has no `billing_customer`, no `subscription`, or a null `plan_id`
- **THEN** `_resolve_plan_id()` SHALL return `"free"`
- **AND** `has_feature()` SHALL return the free plan's value for the feature key

### Requirement: Subscription.plan_id Field

The `Subscription` model SHALL have a nullable `plan_id` field that stores the internal plan identifier.

#### Scenario: plan_id is set on subscription update webhook

- **WHEN** a `customer.subscription.updated` Stripe webhook is received
- **THEN** `_handle_subscription_updated` SHALL extract `items.data[0].price.id`
- **AND** look up `PlanProviderMapping` by `price_id + provider='stripe' + is_active=True`
- **AND** on match, write `plan_id` to `Subscription` using `update_fields=['plan_id', 'updated_at']`

#### Scenario: plan_id is not set when price has no mapping

- **WHEN** the incoming price ID has no active `PlanProviderMapping` entry
- **THEN** a WARNING SHALL be logged
- **AND** `plan_id` SHALL remain unchanged

### Requirement: Cache-Aside with 300s TTL

Entitlement lookups SHALL be cached per-user with a 300-second TTL to avoid repeated database and settings lookups.

#### Scenario: Second call within TTL returns cached result

- **WHEN** `has_feature(user, key)` is called twice within 300 seconds
- **THEN** the second call SHALL return the cached value without hitting the database

#### Scenario: Cache uses per-user key

- **WHEN** the cache is populated
- **THEN** the cache key SHALL be `f"entitlements:{user.pk}"`

### Requirement: Cache Invalidation on Subscription Change

The entitlement cache SHALL be invalidated unconditionally when a subscription is updated via webhook.

#### Scenario: Cache cleared after customer.subscription.updated

- **WHEN** `_handle_subscription_updated` processes a webhook event
- **THEN** `cache.delete(f"entitlements:{customer.user.pk}")` SHALL be called
- **AND** this SHALL happen regardless of whether plan resolution succeeded
- **AND** this SHALL happen even when `items.data` is empty

### Requirement: BILLING_PLANS Feature Flags Structure

Each entry in `BILLING_PLANS` in `config/settings/base.py` SHALL include a `feature_flags` dict alongside the existing `features` list.

#### Scenario: Feature flags are defined per plan

- **WHEN** `BILLING_PLANS` is configured
- **THEN** each plan entry SHALL have a `feature_flags` dict with consistent keys across all plans
- **AND** the `free` plan SHALL have all feature flags set to `False`
- **AND** the `enterprise` plan SHALL have all feature flags set to `True`

### Requirement: Billing-Absent Fallback Returns True

When the billing module is not installed (e.g., in a scaffolded product without billing), `has_feature()` SHALL default to allowing all features.

#### Scenario: has_feature returns True when billing module is absent

- **WHEN** `apps.billing.entitlements` cannot be imported
- **THEN** `has_feature(user, key)` SHALL return `True`
- **AND** no exception SHALL be raised

### Requirement: Frontend useEntitlement Hook (Product Pattern)

Products scaffolded from this template SHOULD implement a `useEntitlement(feature)` hook for conditional rendering based on plan entitlements. This hook is not shipped in the template itself — it is a prescribed pattern for product teams to implement, calling `GET /api/v1/account/` (which includes plan entitlement data) or a dedicated entitlement endpoint.

#### Scenario: Component conditionally renders based on entitlement

- **WHEN** `useEntitlement("api_access")` is called in a React component
- **THEN** it SHALL return `true` if the current user's plan includes `api_access`
- **AND** return `false` otherwise
- **AND** components SHALL use this to gate feature-specific UI elements

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
