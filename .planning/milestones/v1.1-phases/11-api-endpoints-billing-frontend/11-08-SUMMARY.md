---
phase: 11-api-endpoints-billing-frontend
plan: "08"
subsystem: billing-tests
tags: [billing, tests, conftest, test-fixtures, gap-closure]
dependency_graph:
  requires:
    - apps/api/apps/billing/migrations/0002_plan_provider_mapping_stub_seed.py
  provides:
    - Aligned test fixtures matching migration 0002 seeded values
  affects:
    - apps/api/tests/billing/test_services.py
tech_stack:
  added: []
  patterns:
    - "Test fixtures use get_or_create defaults that match migration-seeded values"
key_files:
  modified:
    - apps/api/tests/billing/conftest.py
    - apps/api/tests/billing/test_services.py
decisions:
  - "Migration 0002 seeded values are the canonical source of truth for price_ids in tests"
  - "conftest fixtures must align defaults with migration data to avoid silent no-op get_or_create"
metrics:
  duration_seconds: 109
  completed_date: "2026-03-08"
  tasks_completed: 2
  files_modified: 2
requirements:
  - BILL-03
---

# Phase 11 Plan 08: Fix Service Test Price ID Mismatch Summary

Aligned billing test fixtures and assertions with the stub adapter price_id naming convention seeded by migration 0002, turning 3 previously failing RED tests GREEN without any production code changes.

## What Was Built

Fixed a naming mismatch between migration 0002 (which seeded `price_stub_pro_monthly`) and test infrastructure (which expected `price_pro_monthly`). The fix covered two files:

1. **conftest.py** — Updated `plan_mapping` and `subscription` fixture `get_or_create` defaults from `"price_pro_monthly"` to `"price_stub_pro_monthly"` so fixtures return values matching the migration-seeded DB row.

2. **test_services.py** — Updated 3 assertions (`price_id` and `new_price_id`) from `"price_pro_monthly"` to `"price_stub_pro_monthly"` to match what the StubAdapter echoes back after resolving the price from PlanProviderMapping.

## Root Cause

Migration 0002 seeds `price_id="price_stub_pro_monthly"` for the pro/stub/monthly PlanProviderMapping row. The conftest `plan_mapping` fixture used `get_or_create` with `defaults={"price_id": "price_pro_monthly"}`. Since the migration row already exists when tests run against the test DB, `get_or_create` returns the existing migration row — with its `"price_stub_pro_monthly"` value — so the fixture defaults are never applied. Three test assertions that expected `"price_pro_monthly"` then failed.

## Tasks Completed

| Task | Description                                                 | Commit  | Files            |
| ---- | ----------------------------------------------------------- | ------- | ---------------- |
| 1    | Align conftest fixtures with migration 0002 price_id values | c0d6112 | conftest.py      |
| 2    | Update test assertions to match stub price_id               | 27cf708 | test_services.py |

## Verification Results

- `grep -c "price_pro_monthly" apps/api/tests/billing/conftest.py` → 0 (no remaining old strings)
- `grep -c "price_pro_monthly" apps/api/tests/billing/test_services.py` → 0 (no remaining old strings)
- `uv run pytest tests/billing/test_services.py -q` → **10 passed, 0 failures**
- `uv run pytest tests/billing/ -q` → **63 passed, 1 skipped, 0 failures** (no regressions)

## Decisions Made

- Migration 0002 seeded values are the canonical source of truth for price_id values in tests. Test fixtures must align with these values, not define independent strings.
- `get_or_create` defaults are silently ignored when the row already exists; fixtures that rely on defaults for assertion correctness must match the data the migration seeded.

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED

- FOUND: apps/api/tests/billing/conftest.py
- FOUND: apps/api/tests/billing/test_services.py
- FOUND: .planning/phases/11-api-endpoints-billing-frontend/11-08-SUMMARY.md
- FOUND: commit c0d6112 (fix conftest defaults)
- FOUND: commit 27cf708 (fix test assertions)
