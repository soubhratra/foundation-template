---
phase: 21-gdpr-baseline
plan: "01"
subsystem: accounts/tests
tags: [gdpr, tdd, red-state, deletion, export]
dependency_graph:
  requires: []
  provides:
    - apps/api/tests/accounts/__init__.py
    - apps/api/tests/accounts/test_deletion.py
    - apps/api/tests/accounts/test_export.py
  affects:
    - Plan 21-02 (must implement AccountController and delete_user_account to turn these GREEN)
tech_stack:
  added: []
  patterns:
    - Per-test import gate (try/except ImportError + pytest.fail) prevents collection ERRORs for unimplemented modules
    - get_or_create in billing fixture — billing signal auto-creates Customer on user save, so direct create() causes IntegrityError
key_files:
  created:
    - apps/api/tests/accounts/__init__.py
    - apps/api/tests/accounts/test_deletion.py
    - apps/api/tests/accounts/test_export.py
  modified: []
decisions:
  - billing signal auto-creates Customer on user save — fixture must use get_or_create then update stripe_customer_id field
  - Import gate pattern (pytest.fail inside try/except ImportError) chosen over pytest.importorskip to give developer-friendly error messages
metrics:
  duration_seconds: 285
  completed_date: "2026-03-12"
  tasks_completed: 2
  files_created: 3
  files_modified: 0
---

# Phase 21 Plan 01: GDPR Baseline RED Test Stubs Summary

**One-liner:** TDD RED test stubs for GDPR-01 account deletion cascade and GDPR-02 JSON data export, establishing contracts for Plan 02 implementation.

## What Was Built

Created the `tests/accounts/` test package with 13 failing tests that define the exact API contracts for the GDPR deletion and data export features. All tests fail with clear `Failed:` messages (not collection ERRORs) until Plan 02 implements `AccountController` and `delete_user_account`.

### Test Files

**`tests/accounts/test_deletion.py`** — 6 tests covering GDPR-01:

- `TestDeleteAccountEndpoint.test_delete_account_returns_202` — correct password → 202 + `{"message": "Account deletion initiated."}`
- `TestDeleteAccountEndpoint.test_delete_wrong_password_returns_400` — wrong password → 400
- `TestDeleteAccountEndpoint.test_delete_unauthenticated_returns_401` — no auth → 401
- `TestDeletionTaskCascade.test_deletion_task_cascade` — verifies cascade order: `cancel_subscription` → `delete_customer` → `delete_person` → `user.delete()`
- `TestDeletionTaskCascade.test_deletion_task_idempotent` — non-existent user PK → `None` without raising
- `TestDeletionTaskCascade.test_deletion_task_continues_on_stripe_failure` — `cancel_subscription` raises → task still calls `user.delete()`

**`tests/accounts/test_export.py`** — 7 tests covering GDPR-02:

- `test_export_returns_200` — authenticated GET → 200
- `test_export_schema` — top-level keys: `profile`, `social_accounts`, `billing`, `exported_at`
- `test_export_profile_fields` — profile has: `email`, `first_name`, `last_name`, `date_joined`, `last_login`
- `test_export_download_header` — `Content-Disposition: attachment; filename=my-data.json`
- `test_export_billing_no_customer` — no Customer row → `subscription_status=None`, `plan_id=None`, `payments=[]`
- `test_export_unauthenticated_returns_401` — no auth → 401
- `test_export_excludes_stripe_ids` — `cus_` and `sub_` must not appear in JSON response

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed IntegrityError in export_user_with_billing fixture**

- **Found during:** Task 2 verification — `test_export_excludes_stripe_ids` raised `ERROR` (not `FAILED`)
- **Issue:** Billing app has a `post_save` signal that auto-creates a `Customer` row when a user is saved. The original fixture called `Customer.objects.create(...)` after the signal had already created one, causing `IntegrityError: duplicate key value violates unique constraint billing_customer_user_id_key`
- **Fix:** Changed fixture to `Customer.objects.get_or_create(user=export_user)` then `customer.save(update_fields=["stripe_customer_id"])` — updates the auto-created row instead of creating a duplicate
- **Files modified:** `apps/api/tests/accounts/test_export.py`
- **Commit:** fa33b68

**2. [Rule 3 - Linting] Fixed ruff E501 line-too-long in both test files**

- **Found during:** Pre-commit hook on both task commits
- **Fix:** Shortened docstrings on 4 test methods to stay within 100-char limit
- **Files modified:** `apps/api/tests/accounts/test_deletion.py`, `apps/api/tests/accounts/test_export.py`

## Decisions Made

- **Import gate pattern** (`try/except ImportError` + `pytest.fail()`) chosen over `pytest.importorskip` because it gives actionable error messages pointing to the exact file and class the implementer needs to create. `importorskip` silently skips tests, which would hide missing implementations.
- **Billing signal awareness:** `export_user_with_billing` fixture must use `get_or_create` — the billing signal auto-creates a `Customer` on user save, so any attempt to `create()` a second one fails. This pattern should be documented for all future billing-related test fixtures.

## Self-Check

**Files exist:**

- `apps/api/tests/accounts/__init__.py` — FOUND
- `apps/api/tests/accounts/test_deletion.py` — FOUND (6 tests)
- `apps/api/tests/accounts/test_export.py` — FOUND (7 tests)

**Commits exist:**

- `5139f98` — GDPR-01 deletion stubs
- `fa33b68` — GDPR-02 export stubs

**RED state confirmed:** `pytest tests/accounts/ -q` → 13 failed, 0 errors, 0 passed

## Self-Check: PASSED
