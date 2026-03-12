---
phase: 14-observability-adapter
plan: "04"
subsystem: create-foundation-app CLI scaffolder
tags: [cli, scaffolder, observability, posthog, remove]
dependency_graph:
  requires: []
  provides:
    - removeObservability() exported from packages/create-foundation-app/src/remove.ts
    - "observability" in SelectedFeatures type
    - promptFeatures() shows observability as selectable option
    - index.ts calls removeObservability() when observability not selected
  affects:
    - packages/create-foundation-app/src/remove.ts
    - packages/create-foundation-app/src/prompts.ts
    - packages/create-foundation-app/src/index.ts
tech_stack:
  added: []
  patterns:
    - String-based indexOf/slice for multi-line JSX tag removal (avoids catastrophic regex backtracking)
    - Same readFile/regex/writeFile pattern as removeBillingModule() for other touch points
key_files:
  created: []
  modified:
    - packages/create-foundation-app/src/remove.ts
    - packages/create-foundation-app/src/prompts.ts
    - packages/create-foundation-app/src/index.ts
decisions:
  - "String-based indexOf/slice used for multi-line PostHogProvider JSX tag removal — regex with /m flag + repeated group caused catastrophic backtracking on 2.5KB file; string approach is O(n) and deterministic"
metrics:
  duration_minutes: 11
  completed_date: "2026-03-11"
  tasks_completed: 2
  files_modified: 3
requirements:
  - OBS-03
---

# Phase 14 Plan 04: CLI Scaffolder Observability Removal Summary

**One-liner:** `--without observability` CLI flag that strips all 7 PostHog touch points (Django, Next.js, Expo) cleanly via removeObservability() in the create-foundation-app scaffolder.

## Tasks Completed

| Task | Name                                                        | Commit  | Files                                        |
| ---- | ----------------------------------------------------------- | ------- | -------------------------------------------- |
| 1    | Implement removeObservability() in remove.ts                | 942709e | packages/create-foundation-app/src/remove.ts |
| 2    | Wire SelectedFeatures, promptFeatures, index.ts; test GREEN | 068e808 | prompts.ts, index.ts, remove.ts (bug fix)    |

## What Was Built

### removeObservability() — 7 touch points

The function handles all observability artifacts across the full monorepo:

1. **Delete** `apps/api/apps/core/observability.py`
2. **base.py** — remove `ObservabilityMiddleware` line from MIDDLEWARE list
3. **base.py** — remove `OBSERVABILITY MODULE` dash-comment settings block
4. **apps.py** — remove `task_failure` signal handler (prevents ImportError after observability.py is deleted)
5. **pyproject.toml** — remove `posthog>=x.y.z` dependency line
6. **providers.tsx** — remove PostHog imports, `posthog.init` block, `PostHogPageView` component, and `<PostHogProvider>` wrapper; strip web `.env.example` PostHog vars
7. **\_layout.tsx** — remove `posthog-react-native` import, `PostHogScreenTracker` component, and `<PostHogProvider>` wrapper; strip mobile `.env.example` PostHog var

All file-not-found cases use ENOENT guards and `logger.warning` so the function is idempotent.

### CLI wiring

- `SelectedFeatures` type: added `| "observability"` union member
- `promptFeatures()`: added `{ value: "observability", label: "Observability (PostHog analytics + error tracking)" }` option with `"observability"` in `initialValues`
- `index.ts`: added `--without observability` / `--without-observability` flag parsing; added `removeObservability(config.outputDir)` call after billing removal block

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Catastrophic regex backtracking on multi-line JSX tag removal**

- **Found during:** Task 2 verification (test_scaffolder_observability_removal.py timing out at 60s)
- **Issue:** Regex `/^\s*<PostHogProvider\n(?:\s+[^\n]*\n)*\s*>\n/m` with multiline flag caused the Node.js process to hang indefinitely (CPU-bound) on the 2.5KB `_layout.tsx` file. The `m` flag causes the engine to attempt matching at every line start; combined with the repeated group `(?:\s+[^\n]*\n)*` and trailing `\s*>`, it triggers O(2^n) backtracking when the pattern doesn't match cleanly.
- **Fix:** Replaced with deterministic string operations: `indexOf("    <PostHogProvider")` to find start, `indexOf("\n    >", tagStart)` to find the closing `>` line, then `slice()` to excise the range. O(n) and not subject to regex catastrophic backtracking.
- **Files modified:** `packages/create-foundation-app/src/remove.ts`
- **Commit:** 068e808

## Verification

- `pnpm build` in `packages/create-foundation-app`: TypeScript compiles without errors
- `test_scaffolder_observability_removal.py`: PASSED (0.23s)
- `removeObservability` exported from `dist/remove.js`: confirmed
- `SelectedFeatures` includes `"observability"` in `dist/prompts.js`: confirmed
- `removeObservability` called in `dist/index.js`: confirmed

## Self-Check

- [x] packages/create-foundation-app/src/remove.ts — modified with removeObservability()
- [x] packages/create-foundation-app/src/prompts.ts — modified with observability type + option
- [x] packages/create-foundation-app/src/index.ts — modified with import + wiring
- [x] Commit 942709e exists
- [x] Commit 068e808 exists
- [x] Integration test passes: test_scaffolder_observability_removal.py PASSED
