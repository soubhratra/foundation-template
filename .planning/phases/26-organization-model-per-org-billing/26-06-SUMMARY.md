---
phase: 26-organization-model-per-org-billing
plan: "06"
subsystem: billing-entitlements
tags:
  - entitlements
  - orgs
  - billing
  - cache
  - b2b
dependency_graph:
  requires:
    - 26-05 (org controllers and schemas)
    - apps.orgs.services (_resolve_org_plan_id)
    - apps.orgs.models (OrgCustomer, Membership)
    - apps.billing.entitlements (_flags_for_plan, _resolve_plan_id)
  provides:
    - has_org_feature() in apps.core.entitlements — callable from any Django app
    - _try_invalidate_org_member_caches() in apps.billing.tasks — org cache invalidation on webhook
  affects:
    - apps/api/apps/core/entitlements.py
    - apps/api/apps/billing/tasks.py
    - apps/api/tests/core/test_entitlements.py
    - apps/api/tests/billing/test_tasks.py
tech_stack:
  added: []
  patterns:
    - Lazy imports inside function bodies to avoid circular imports at Django startup
    - B2B_START/B2B_END markers around org-specific code blocks in billing/tasks.py
    - Separate org cache key (entitlements:org:{org.pk}:{user.pk}) from personal cache key
    - except ImportError: return True pattern for billing-absent environments
    - except Exception: pass pattern for silent OrgCustomer not-found handling
key_files:
  created: []
  modified:
    - apps/api/apps/core/entitlements.py
    - apps/api/apps/billing/tasks.py
    - apps/api/tests/core/test_entitlements.py
    - apps/api/tests/billing/test_tasks.py
decisions:
  - "26-06: OrgCustomer auto-created by post_save signal — test updates stripe_customer_id on existing record instead of creating a second one"
  - "26-06: Lazy imports (from apps.orgs.models import OrgCustomer) inside _try_invalidate_org_member_caches() body prevent circular imports"
  - "26-06: except Exception: pass in _try_invalidate_org_member_caches() covers both OrgCustomer.DoesNotExist and any future DB/cache errors without propagating"
metrics:
  duration_minutes: 7
  completed_date: "2026-03-12"
  tasks_completed: 2
  files_modified: 4
---

# Phase 26 Plan 06: Org Entitlements and Cache Invalidation Summary

**One-liner:** `has_org_feature()` with org-scoped cache + org member cache invalidation on subscription webhook, turning all 3 BILL-02 test stubs GREEN.

## What Was Built

### Task 1: has_org_feature() added to apps/core/entitlements.py

Added `has_org_feature(user, org, key)` after `has_feature()` using the exact pattern from RESEARCH.md Pattern 3.

Key behaviors:

- Checks `entitlements:org:{org.pk}:{user.pk}` cache key first
- When cache miss: calls `_resolve_org_plan_id(org)` to get org plan
- If org has active subscription (`plan_id` not None): uses org plan flags
- If no org subscription: falls back to personal plan via `_resolve_plan_id(user)`
- Cache TTL from `ENTITLEMENT_CACHE_TTL` setting (default 300s)
- Returns `True` when `ImportError` — no billing module installed

The cache key is separate from the personal key `entitlements:{user.pk}` so org and personal caches are invalidated independently.

### Task 2: \_try_invalidate_org_member_caches() added to apps/billing/tasks.py

Added `_try_invalidate_org_member_caches(stripe_customer_id)` before `_TIER1_HANDLERS`, wrapped in `B2B_START`/`B2B_END` markers.

Key behaviors:

- Lazy-imports `OrgCustomer` and `Membership` inside `try` block (avoids circular import)
- Looks up `OrgCustomer.objects.get(stripe_customer_id=stripe_customer_id)`
- Iterates all `Membership` rows for that org and deletes each `entitlements:org:{org.pk}:{user_id}` cache key
- `except Exception: pass` — silently returns when OrgCustomer not found (personal subscription event)

Added call to `_try_invalidate_org_member_caches(stripe_customer_id)` at the end of `_handle_subscription_updated()`, wrapped in `B2B_START`/`B2B_END` comments, after the personal cache invalidation line.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Test tried to create OrgCustomer directly but post_save signal auto-creates one**

- **Found during:** Task 2 test implementation
- **Issue:** `OrgCustomer.objects.create(org=org, stripe_customer_id=...)` raised `IntegrityError` because the `post_save` signal on `Organization` auto-calls `OrgCustomer.objects.get_or_create(org=instance)` — the OrgCustomer already existed
- **Fix:** Changed test to update the auto-created OrgCustomer: `org.billing_customer.stripe_customer_id = stripe_cid; org.billing_customer.save(...)`
- **Files modified:** `tests/billing/test_tasks.py`
- **Commit:** `1f7c704`

**2. [Rule 3 - Lint] Line length violations in test_entitlements.py**

- **Found during:** Task 1 pre-commit hook
- **Issue:** `patch(...)` calls with long string arguments exceeded ruff's 100-char limit
- **Fix:** ruff auto-reformatted the file (pre-commit hook `--fix` mode)
- **Files modified:** `tests/core/test_entitlements.py`, `apps/core/entitlements.py`
- **Commit:** `ffa601a`

## Test Results

| Test Suite                                 | Before                     | After      |
| ------------------------------------------ | -------------------------- | ---------- |
| tests/core/test_entitlements.py            | 2 passed, 2 FAILED (stubs) | 4 passed   |
| tests/billing/test_tasks.py                | 8 passed, 1 FAILED (stub)  | 9 passed   |
| tests/orgs/                                | 13 passed                  | 13 passed  |
| Full suite (excluding pre-existing errors) | 179 passed                 | 191 passed |

Pre-existing errors in `tests/billing/test_controllers.py` and `tests/billing/test_services.py` (12 total) are unaffected — confirmed by running them before and after the change.

## B2B Markers Placed

```
apps/api/apps/billing/tasks.py:
  Line 156: # B2B_START  (_try_invalidate_org_member_caches call site)
  Line 158: # B2B_END
  Line 237: # B2B_START  (_try_invalidate_org_member_caches function definition)
  Line 269: # B2B_END
```

## Key Files

- `/Users/soubhratra/workspace/foundation-template/apps/api/apps/core/entitlements.py` — `has_org_feature()` added
- `/Users/soubhratra/workspace/foundation-template/apps/api/apps/billing/tasks.py` — `_try_invalidate_org_member_caches()` added

## Commits

| Hash      | Description                                                               |
| --------- | ------------------------------------------------------------------------- |
| `ffa601a` | feat(26-06): add has_org_feature() to core/entitlements.py                |
| `1f7c704` | feat(26-06): add \_try_invalidate_org_member_caches() to billing/tasks.py |

## Self-Check: PASSED

- `apps/api/apps/core/entitlements.py` — exists and importable
- `apps/api/apps/billing/tasks.py` — exists, B2B markers confirmed
- `apps/api/tests/core/test_entitlements.py` — exists, 4 tests pass
- `apps/api/tests/billing/test_tasks.py` — exists, BILL-02 test passes
- Commit `ffa601a` — confirmed in git log
- Commit `1f7c704` — confirmed in git log
