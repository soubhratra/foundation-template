---
phase: 27-outbound-webhooks
plan: "01"
subsystem: webhooks
tags: [tdd, red-phase, webhooks, celery, hmac]
dependency_graph:
  requires: [26-orgs]
  provides: [red-test-contract-for-27-02, red-test-contract-for-27-03, red-test-contract-for-27-04]
  affects: []
tech_stack:
  added: []
  patterns: [module-level-import-red, pytest-fail-red-stubs]
key_files:
  created:
    - apps/api/tests/webhooks/__init__.py
    - apps/api/tests/webhooks/conftest.py
    - apps/api/tests/webhooks/test_models.py
    - apps/api/tests/webhooks/test_utils.py
    - apps/api/tests/webhooks/test_tasks.py
    - apps/api/tests/webhooks/test_controllers.py
    - apps/api/tests/webhooks/test_checks.py
  modified: []
decisions:
  - "Module-level import in __init__.py (not conftest.py) causes ImportError at collection time — ensures all 7 test files fail RED before any implementation exists"
  - "test_models.py uses real assertions (not pytest.fail) because the fixture itself raises ImportError at collection — behaviour is equivalent RED"
  - "conftest.py uses lazy imports (inside fixture bodies) for WebhookEndpoint and WebhookDelivery to prevent double-import errors while keeping __init__.py as the authoritative RED trigger"
metrics:
  duration_min: 2
  completed_date: "2026-03-13"
  tasks_completed: 1
  files_created: 7
  files_modified: 0
---

# Phase 27 Plan 01: RED Test Stubs — Outbound Webhooks Summary

**One-liner:** 7 failing test files establishing the complete HOOK-01..04 test contract; suite fails at collection with `ModuleNotFoundError: No module named 'apps.webhooks'`.

## What Was Built

All RED test stubs for Phase 27 (Outbound Webhooks). The test suite fails immediately at collection time because `apps.webhooks` does not yet exist — this is the intended state.

### Files Created

| File                                 | Purpose                                                                   |
| ------------------------------------ | ------------------------------------------------------------------------- |
| `tests/webhooks/__init__.py`         | Module-level import → immediate `ImportError` at collection (RED trigger) |
| `tests/webhooks/conftest.py`         | Fixtures: `org_owner`, `org`, `org_admin`, `endpoint`, `delivery`         |
| `tests/webhooks/test_models.py`      | Field defaults, cascade delete, 10KB truncation — HOOK-01                 |
| `tests/webhooks/test_utils.py`       | `fire_webhook_event()` validation and dispatch — HOOK-01                  |
| `tests/webhooks/test_tasks.py`       | `deliver_webhook` retry/HMAC/circuit-breaker — HOOK-01, HOOK-04           |
| `tests/webhooks/test_controllers.py` | 14 HTTP endpoint stubs — HOOK-01, HOOK-02, HOOK-03, HOOK-04               |
| `tests/webhooks/test_checks.py`      | `WEBHOOK_EVENTS` system check — HOOK-01                                   |

### Test Coverage by Requirement

| Requirement                               | Stubs Defined                                |
| ----------------------------------------- | -------------------------------------------- |
| HOOK-01 (registration + HMAC + 7 retries) | 14 stubs across models, utils, tasks, checks |
| HOOK-02 (paginated delivery history)      | 2 stubs in controllers                       |
| HOOK-03 (manual retry)                    | 2 stubs in controllers                       |
| HOOK-04 (circuit breaker + email)         | 4 stubs across tasks and controllers         |

## Verification

```
cd apps/api && .venv/bin/pytest tests/webhooks/ -x -q
```

Output:

```
ImportError while loading conftest '.../tests/webhooks/conftest.py'.
tests/webhooks/__init__.py:3: in <module>
    from apps.webhooks.models import (  # noqa: F401
E   ModuleNotFoundError: No module named 'apps.webhooks'
```

RED state confirmed — zero passing tests, clean collection failure.

## Commits

| Hash    | Message                                               |
| ------- | ----------------------------------------------------- |
| 7512803 | test(27-01): add RED test stubs for outbound webhooks |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Linting] Ruff reformatted multi-line imports and removed unused import**

- **Found during:** Pre-commit hook on first commit attempt
- **Issue:** `from apps.webhooks.models import WebhookDelivery, WebhookDeliveryAttempt, WebhookEndpoint` was written on one line; ruff expanded to multi-line format. `WebhookDeliveryAttempt` unused import in `test_models.py` was also flagged and the unused alias removed by ruff.
- **Fix:** Re-staged ruff-modified files and committed successfully on second attempt
- **Files modified:** `__init__.py`, `test_models.py`, `test_controllers.py`
- **Commit:** 7512803

## Self-Check: PASSED

All 7 files confirmed present. Commit `7512803` confirmed in git log. RED state confirmed via test run.
