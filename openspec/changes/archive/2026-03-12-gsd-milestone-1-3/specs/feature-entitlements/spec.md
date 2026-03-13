## ADDED Requirements

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
