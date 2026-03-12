---
phase: 23-feature-entitlements
plan: "02"
subsystem: billing/entitlements
tags: [entitlements, billing, cache, feature-flags, tdd]
dependency_graph:
  requires: [23-01]
  provides: [has_feature-public-api, billing-entitlements-module, subscription-plan-id-field]
  affects: [apps/api/apps/billing, apps/api/apps/core, apps/api/config/settings]
tech_stack:
  added: []
  patterns:
    - Cache-aside with LocMemCache in tests, Redis in production (django.core.cache.cache)
    - ImportError-fallback pattern for optional billing module
    - Deny-by-default feature flag resolution
key_files:
  created:
    - apps/api/apps/billing/entitlements.py
    - apps/api/apps/billing/migrations/0004_subscription_plan_id.py
    - apps/api/apps/core/entitlements.py
  modified:
    - apps/api/apps/billing/models.py
    - apps/api/config/settings/base.py
    - apps/api/tests/billing/test_entitlements.py
    - apps/api/tests/core/test_entitlements.py
decisions:
  - "Cache key is entitlements:{user.pk} with 300s TTL — per-user granularity allows targeted invalidation in Plan 03"
  - "plan_override param on _has_feature() for test convenience only — avoids needing full DB fixtures for flag-value tests"
  - "_flags_for_plan falls back to BILLING_PLANS.free dict when plan_id not found — secondary safety net after _resolve_plan_id"
  - "Import of _has_feature inside has_feature() function body — catches ImportError per-call, not at module load time"
metrics:
  duration_minutes: 3
  completed_date: "2026-03-12"
  tasks_completed: 2
  files_changed: 7
---

# Phase 23 Plan 02: Core Entitlement System Summary

**One-liner:** Cache-aside has_feature() backed by BILLING_PLANS feature_flags dict with deny-by-default and billing-absent fallback.

## What Was Built

Implemented the complete entitlement system that turns ENT-01 and ENT-03 test stubs GREEN:

1. **Subscription.plan_id field** — Nullable CharField(50) added to the Subscription model via migration 0004. This links the subscription record to internal plan identifiers like "free", "pro", "enterprise".

2. **BILLING_PLANS feature_flags** — Added a `feature_flags` dict alongside the existing `features` list in each plan entry in `config/settings/base.py`. Free plan: all False. Pro plan: api_access + advanced_analytics True, white_label False. Enterprise: all True.

3. **apps/billing/entitlements.py** — Private module with three functions:
   - `_has_feature(user, key, plan_override=None)` — Cache-aside lookup with 300s TTL. Returns bool, never raises.
   - `_resolve_plan_id(user)` — Walks user.billing_customer.subscription.plan_id with broad except → free. Logs WARNING for unknown plan IDs.
   - `_flags_for_plan(plan_id)` — Returns the feature_flags dict for a plan; falls back to free plan if plan_id missing.

4. **apps/core/entitlements.py** — Public API with `has_feature(user, key)`. Imports \_has_feature inside the function body so ImportError is caught per-call, returning True when billing is absent.

## Test Results

| Test Class             | Tests | Result                |
| ---------------------- | ----- | --------------------- |
| TestHasFeature         | 5     | PASS                  |
| TestCaching            | 1     | PASS                  |
| TestBillingOffFallback | 2     | PASS                  |
| TestCacheInvalidation  | 1     | FAIL (stub — Plan 03) |

**Total: 8 passed, 1 expected-failing stub.**

## Deviations from Plan

None - plan executed exactly as written.

## Self-Check: PASSED

- FOUND: apps/api/apps/billing/entitlements.py
- FOUND: apps/api/apps/billing/migrations/0004_subscription_plan_id.py
- FOUND: apps/api/apps/core/entitlements.py
- Commits: 01f0147 (RED billing tests), 7b8184b (GREEN billing impl), 42bfd3a (RED core tests), a837602 (GREEN core impl)
