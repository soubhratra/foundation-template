---
phase: 23
slug: feature-entitlements
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-12
audited: 2026-03-12
---

# Phase 23 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property               | Value                                                                                                   |
| ---------------------- | ------------------------------------------------------------------------------------------------------- |
| **Framework**          | pytest + pytest-django                                                                                  |
| **Config file**        | `apps/api/pyproject.toml` (`[tool.pytest.ini_options]`)                                                 |
| **Quick run command**  | `cd apps/api && python -m pytest tests/billing/test_entitlements.py tests/core/test_entitlements.py -x` |
| **Full suite command** | `cd apps/api && python -m pytest`                                                                       |
| **Estimated runtime**  | ~15 seconds (quick), ~60 seconds (full)                                                                 |

---

## Sampling Rate

- **After every task commit:** Run `cd apps/api && python -m pytest tests/billing/test_entitlements.py tests/core/test_entitlements.py -x`
- **After every plan wave:** Run `cd apps/api && python -m pytest`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID  | Plan | Wave | Requirement            | Test Type        | Automated Command                                                                                       | File Exists | Status   |
| -------- | ---- | ---- | ---------------------- | ---------------- | ------------------------------------------------------------------------------------------------------- | ----------- | -------- |
| 23-01-01 | 01   | 0    | ENT-01, ENT-02, ENT-03 | unit/integration | `cd apps/api && python -m pytest tests/billing/test_entitlements.py tests/core/test_entitlements.py -x` | ✅          | ✅ green |
| 23-02-01 | 02   | 1    | ENT-01                 | unit             | `cd apps/api && python -m pytest tests/billing/test_entitlements.py::TestHasFeature -x`                 | ✅          | ✅ green |
| 23-02-02 | 02   | 1    | ENT-01                 | unit             | `cd apps/api && python -m pytest tests/billing/test_entitlements.py::TestCaching -x`                    | ✅          | ✅ green |
| 23-03-01 | 03   | 1    | ENT-02                 | integration      | `cd apps/api && python -m pytest tests/billing/test_entitlements.py::TestCacheInvalidation -x`          | ✅          | ✅ green |
| 23-03-02 | 03   | 1    | ENT-03                 | unit             | `cd apps/api && python -m pytest tests/core/test_entitlements.py -x`                                    | ✅          | ✅ green |

_Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky_

---

## Wave 0 Requirements

- [x] `tests/billing/test_entitlements.py` — ENT-01/ENT-02 (7 tests: TestHasFeature×5, TestCaching×1, TestCacheInvalidation×1)
- [x] `tests/core/test_entitlements.py` — ENT-03 (2 tests: TestBillingOffFallback×2)

_Existing `tests/billing/conftest.py` and global `tests/conftest.py` already provide `user`, `customer`, `subscription` fixtures and `LocMemCache` override — no new conftest needed._

### Test stubs to create in Wave 0

**`tests/billing/test_entitlements.py`:**

- `TestHasFeature::test_returns_true_for_enabled_flag`
- `TestHasFeature::test_returns_false_for_disabled_flag`
- `TestHasFeature::test_missing_key_returns_false`
- `TestHasFeature::test_no_subscription_uses_free_plan`
- `TestHasFeature::test_unknown_plan_id_falls_back_to_free`
- `TestCaching::test_second_call_uses_cache`
- `TestCacheInvalidation::test_cache_invalidated_on_subscription_updated`

**`tests/core/test_entitlements.py`:**

- `TestBillingOffFallback::test_returns_true_when_billing_absent`
- `TestBillingOffFallback::test_no_import_error`

---

## Manual-Only Verifications

_All phase behaviors have automated verification._

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 15s (actual: 8.39s for 9 tests)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** ✅ 2026-03-12 — 9/9 tests passing, no manual-only

---

## Validation Audit 2026-03-12

| Metric        | Count |
| ------------- | ----- |
| Gaps found    | 0     |
| Resolved      | 0     |
| Escalated     | 0     |
| Tests run     | 9     |
| Tests passing | 9     |
