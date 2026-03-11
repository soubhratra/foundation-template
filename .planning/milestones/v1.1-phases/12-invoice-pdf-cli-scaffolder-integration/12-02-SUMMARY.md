---
phase: 12-invoice-pdf-cli-scaffolder-integration
plan: "02"
subsystem: cli-scaffolder
tags: [cli, scaffolder, billing, stripe, vitest, tdd]
dependency_graph:
  requires: []
  provides:
    - removeBillingModule() function in packages/create-foundation-app/src/remove.ts
    - billing option in CLI feature selection prompt
    - --without billing / --without-billing CLI flag
  affects:
    - packages/create-foundation-app/src/remove.ts
    - packages/create-foundation-app/src/prompts.ts
    - packages/create-foundation-app/src/index.ts
    - packages/create-foundation-app/tests/remove-billing.test.ts
tech_stack:
  added:
    - vitest ^2.0.0 (devDependency in create-foundation-app)
  patterns:
    - TDD Wave 0 (RED tests before implementation)
    - ENOENT-tolerant directory/file deletion via fs-extra remove()
    - Dash-delimited regex for multi-line Python comment block removal
key_files:
  created:
    - packages/create-foundation-app/tests/remove-billing.test.ts
    - packages/create-foundation-app/vitest.config.ts
  modified:
    - packages/create-foundation-app/src/remove.ts
    - packages/create-foundation-app/src/prompts.ts
    - packages/create-foundation-app/src/index.ts
    - packages/create-foundation-app/package.json
    - package.json (root — pnpm override version fix)
    - packages/business-logic/package.json (devtools version fix)
    - apps/web/package.json (devtools version fix)
decisions:
  - BILLING MODULE block regex uses dash-delimited comment markers (10+ dashes) not line-count heuristics, making it robust against block content changes
  - pyproject.toml removal is ENOENT-tolerant — tests run on a tmpdir without pyproject.toml, so graceful skip is the correct behavior
  - --without billing flag filters out billing post-prompt (not pre-prompt) — this preserves the rawFeatures prompt result but overrides billing selection, clean separation of concerns
  - withoutBillingFlag detection supports both --without billing (space-separated) and --without-billing (hyphenated) to match any future CLI convention
metrics:
  duration_seconds: 246
  completed_date: "2026-03-10"
  tasks_completed: 3
  files_modified: 7
---

# Phase 12 Plan 02: CLI Scaffolder Billing Removal Summary

One-liner: Vitest TDD suite + `removeBillingModule()` that surgically strips all billing artifacts (Django app, settings block, URL routes, frontend pages, config file) from scaffolded projects, wired into `create-foundation-app` prompt and `--without billing` flag.

## Tasks Completed

| Task | Name                                                   | Commit  | Files                                                        |
| ---- | ------------------------------------------------------ | ------- | ------------------------------------------------------------ |
| 0    | Create remove-billing.test.ts with failing tests (RED) | b0f6c7c | tests/remove-billing.test.ts, vitest.config.ts, package.json |
| 1    | Add removeBillingModule() to remove.ts (GREEN)         | de3dc58 | src/remove.ts                                                |
| 2    | Wire billing into prompts.ts and index.ts              | a70a936 | src/prompts.ts, src/index.ts                                 |

## What Was Built

### removeBillingModule(outputDir: string): Promise<void>

Exported from `packages/create-foundation-app/src/remove.ts`. Steps performed:

1. Delete `apps/api/apps/billing/` directory (ENOENT tolerant)
2. Remove `"apps.billing"` INSTALLED_APPS line from `base.py`
3. Remove `# BILLING MODULE ... # END BILLING MODULE` settings block from `base.py` (dash-delimited regex)
4. Remove `BILLING_ADAPTER` line from `development.py` only (other settings preserved)
5. Remove `# BILLING_START ... # BILLING_END` URL block from `urls.py`
6. Remove `from apps.billing import webhooks as billing_views` import from `urls.py`
7. Delete `apps/web/app/(dashboard)/billing/` directory (ENOENT tolerant)
8. Delete `apps/web/billing.config.ts` (ENOENT tolerant)
9. Remove `stripe` and `weasyprint` deps from `pyproject.toml` (ENOENT tolerant)

### Prompt + CLI Flag Integration

- `SelectedFeatures` type now includes `"billing"` as a valid value
- `promptFeatures()` shows billing option checked by default (`initialValues` includes `"billing"`)
- `index.ts` parses `--without billing` (space-separated) or `--without-billing` (hyphenated)
- When flag is set: billing is filtered from rawFeatures after prompt (no re-prompt)
- Feature removal block calls `removeBillingModule()` when billing not in selected features

### Test Coverage

7 behavioral tests in `tests/remove-billing.test.ts`, all GREEN:

- Removes `apps/api/apps/billing/` directory
- Removes `apps.billing` from INSTALLED_APPS in base.py
- Removes BILLING MODULE settings block from base.py
- Removes BILLING_ADAPTER line from development.py (other lines preserved)
- Removes BILLING_START/BILLING_END block and billing import from urls.py
- Removes `apps/web/app/(dashboard)/billing/` directory
- Removes `apps/web/billing.config.ts`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed workspace install failure due to deleted npm package version**

- **Found during:** Task 0 (vitest installation step)
- **Issue:** `@tanstack/react-query-devtools@5.90.21` was pinned in the pnpm workspace override at root `package.json`, and in `packages/business-logic/package.json` and `apps/web/package.json`. This version was no longer available on npm (`5.91.3` is the latest), causing all pnpm install commands to fail workspace-wide.
- **Fix:** Updated the pnpm override in `package.json` from `5.90.21` to `5.91.3`, updated `^5.90.21` to `^5.91.3` in `packages/business-logic/package.json` and `apps/web/package.json`.
- **Files modified:** `package.json`, `packages/business-logic/package.json`, `apps/web/package.json`, `pnpm-lock.yaml`
- **Commit:** b0f6c7c

## Self-Check: PASSED

- FOUND: packages/create-foundation-app/tests/remove-billing.test.ts
- FOUND: packages/create-foundation-app/src/remove.ts (with removeBillingModule export)
- FOUND: packages/create-foundation-app/src/prompts.ts (with billing in SelectedFeatures)
- FOUND: packages/create-foundation-app/src/index.ts (with removeBillingModule wired in)
- FOUND commit b0f6c7c: test(12-02): add failing tests for removeBillingModule (RED state)
- FOUND commit de3dc58: feat(12-02): implement removeBillingModule() in remove.ts
- FOUND commit a70a936: feat(12-02): wire billing into prompts.ts and index.ts
