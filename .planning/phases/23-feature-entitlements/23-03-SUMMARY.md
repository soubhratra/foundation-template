---
phase: 23-feature-entitlements
plan: "03"
subsystem: billing/entitlements
tags: [entitlements, billing, cache, webhook, stripe, tdd]
dependency_graph:
  requires: [23-02]
  provides: [cache-invalidation-on-subscription-updated, plan-id-webhook-resolution]
  affects: [apps/api/apps/billing/tasks.py, apps/api/tests/billing/test_entitlements.py]
tech_stack:
  added: []
  patterns:
    - Unconditional cache invalidation after webhook handler (outside try/except)
    - Stripe items.data[0].price.id traversal (not top-level price field)
    - Lazy import of PlanProviderMapping inside conditional branch (avoids circular)
key_files:
  created: []
  modified:
    - apps/api/apps/billing/tasks.py
    - apps/api/tests/billing/test_entitlements.py
decisions:
  - "cache.delete() is unconditional — fires even when price_id is empty or PlanProviderMapping.DoesNotExist; covers unmapped plan downgrades"
  - "_extract_price_id_from_event() returns empty string on empty items.data — guards against Stripe subscriptions with no line items"
  - "PlanProviderMapping.objects.get uses is_active=True filter — inactive mappings do not update plan_id"
  - "subscription.save(update_fields=['plan_id', 'updated_at']) on plan_id write — avoids overwriting concurrent field updates"
metrics:
  duration_minutes: 4
  completed_date: "2026-03-12"
  tasks_completed: 1
  files_changed: 2
---

# Phase 23 Plan 03: Cache Invalidation on Subscription Updated Summary

**One-liner:** Unconditional entitlement cache invalidation on customer.subscription.updated webhook with price-to-plan resolution via PlanProviderMapping.

## What Was Built

Completed the entitlement system by extending `_handle_subscription_updated` in `apps/billing/tasks.py`:

1. **`_extract_price_id_from_event` helper** — Extracts `items.data[0].price.id` from the Stripe webhook payload. Returns empty string when `items.data` is empty (guards against Stripe subscriptions with no line items).

2. **Plan ID resolution** — After the existing `subscription.save()`, looks up `PlanProviderMapping` by `price_id + provider='stripe' + is_active=True`. On match, writes `plan_id` to the subscription and saves with `update_fields`. On `DoesNotExist`, logs a WARNING and continues.

3. **Unconditional cache invalidation** — `cache.delete(f"entitlements:{customer.user.pk}")` fires after the `if price_id:` block regardless of whether plan resolution succeeded. This ensures stale entitlement results never survive a plan upgrade or downgrade, even when `PlanProviderMapping` has no entry for the incoming price.

4. **`TestCacheInvalidation` real test** — Replaced the stub with a real test: seeds the cache with `{"api_access": True}`, fires `_handle_subscription_updated` with a minimal `items.data=[]` payload, asserts `cache.get()` returns `None` afterward.

## Test Results

| Test Class             | Tests | Result |
| ---------------------- | ----- | ------ |
| TestHasFeature         | 5     | PASS   |
| TestCaching            | 1     | PASS   |
| TestCacheInvalidation  | 1     | PASS   |
| TestBillingOffFallback | 2     | PASS   |

**Total: 9 passed. Phase 23 complete.**

## TDD Commits

| Phase | Commit  | Description                                       |
| ----- | ------- | ------------------------------------------------- |
| RED   | f9a6745 | Replace TestCacheInvalidation stub with real test |
| GREEN | 7dd9372 | Implement plan_id write + cache.delete in tasks   |

## Deviations from Plan

None - plan executed exactly as written.

## Self-Check: PASSED

- FOUND: apps/api/apps/billing/tasks.py (modified — contains `cache.delete`)
- FOUND: apps/api/tests/billing/test_entitlements.py (modified — real test replacing stub)
- Commits: f9a6745 (RED), 7dd9372 (GREEN)
- All 9 entitlement tests pass
- Full suite: 175 passed, 1 skipped, 12 pre-existing errors (unrelated to this plan)
