# Deferred Items — Phase 18

## Pre-Existing Issues (Out of Scope)

### 1. C901 complexity violation in test_scaffolder_observability_removal.py

**File:** `apps/api/tests/test_scaffolder_observability_removal.py:38`
**Issue:** `test_remove_observability_cleans_all_touch_points` has McCabe complexity 15 (exceeds max 10)
**Introduced in:** Phase 14 (commit b056a06)
**Discovered during:** Plan 18-02 Task 2 — running `uv run ruff check . --select C90`

The function is a large integration test that tests many touch points in one test method.
This is a pre-existing issue not caused by 18-02 changes.

**Recommended fix:** Refactor into smaller focused test methods, or use `# noqa: C901` with documented justification.
