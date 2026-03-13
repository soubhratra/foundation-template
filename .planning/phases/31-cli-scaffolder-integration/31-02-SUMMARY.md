---
phase: 31-cli-scaffolder-integration
plan: 02
subsystem: infra
tags: [cli, scaffolder, typescript, b2b, create-foundation-app]

# Dependency graph
requires:
  - phase: 31-01
    provides: RED pytest tests for B2B scaffold (test_scaffold_without_b2b, test_scaffold_with_b2b)
provides:
  - stripMarkerBlocks(content, markerName) generic utility in transform.ts
  - removeB2BModule(outputDir) in remove.ts — deletes B2B dirs, patches pyproject.toml, strips markers
  - --with b2b / --with-b2b CLI flag in create-foundation-app
  - B2B multiselect option in interactive prompts (unchecked by default)
  - Balanced B2B_START/B2B_END markers in base.py (8 each)
  - All 6 scaffolder tests GREEN (2 new B2B + 4 existing)
affects: [future-scaffolder-changes, new-product-scaffolding]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Dynamic import of globby inside async function body (avoid top-level ESM circular dep issues)
    - ENOENT-tolerant directory deletion pattern (try/catch code !== ENOENT)
    - Generic marker-fenced block stripper using non-greedy regex with 3+ blank line collapse

key-files:
  created: []
  modified:
    - apps/api/config/settings/base.py
    - packages/create-foundation-app/src/transform.ts
    - packages/create-foundation-app/src/remove.ts
    - packages/create-foundation-app/src/prompts.ts
    - packages/create-foundation-app/src/index.ts

key-decisions:
  - "B2B is opt-in via --with b2b flag (not opt-out); default scaffold excludes B2B"
  - "django-unfold NOT removed by removeB2BModule — admin theme is unconditional, not B2B-only"
  - "B2B multiselect option unchecked by default — must not appear in initialValues array"
  - "Dynamic import of globby inside removeB2BModule function body avoids ESM module resolution issues"
  - "stripMarkerBlocks collapses 3+ consecutive blank lines to 2 after stripping — prevents cosmetic whitespace gaps"

patterns-established:
  - "Marker-fenced block pattern: # FEATURE_START / # FEATURE_END for opt-in feature isolation in Python files"
  - "--with flag pattern mirrors --without flag pattern: parse argv, check index+1 or includes(--with-x)"

requirements-completed: [SCAFF-01]

# Metrics
duration: 2min
completed: 2026-03-13
---

# Phase 31 Plan 02: CLI Scaffolder B2B Integration Summary

**Full B2B scaffolder integration: --with b2b flag, removeB2BModule(), stripMarkerBlocks(), and all 6 scaffolder tests GREEN**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-13T19:38:24Z
- **Completed:** 2026-03-13T19:40:51Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Fixed unmatched `# B2B_END` marker in `base.py` (counts now 8/8 balanced)
- Added `stripMarkerBlocks(content, markerName)` generic utility to `transform.ts` — non-greedy regex strips marker-fenced blocks from Python files
- Added `removeB2BModule(outputDir)` to `remove.ts` — deletes orgs/api_keys/webhooks/audit dirs, removes django-pghistory and django-hijack from pyproject.toml, strips all B2B marker blocks from remaining .py files
- Wired `--with b2b` / `--with-b2b` CLI flag in `index.ts`; added B2B multiselect option (unchecked by default) in `prompts.ts`
- CLI builds without TypeScript errors; `test_scaffold_without_b2b` and `test_scaffold_with_b2b` both PASS; all 4 pre-existing scaffolder tests unaffected

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix unmatched B2B marker in base.py + add stripMarkerBlocks() to transform.ts + add removeB2BModule() to remove.ts** - `300363c` (fix)
2. **Task 2: Wire --with b2b flag in prompts.ts + index.ts, build CLI, run tests GREEN** - `725e2ac` (feat)

**Plan metadata:** (docs commit — see below)

## Files Created/Modified

- `apps/api/config/settings/base.py` — Inserted missing `# B2B_END` after API_KEY_SCOPES block
- `packages/create-foundation-app/src/transform.ts` — Added `stripMarkerBlocks(content, markerName)` export
- `packages/create-foundation-app/src/remove.ts` — Added `removeB2BModule(outputDir)` export, imported `stripMarkerBlocks`
- `packages/create-foundation-app/src/prompts.ts` — Added `"b2b"` to `SelectedFeatures` type, added B2B multiselect option (unchecked by default)
- `packages/create-foundation-app/src/index.ts` — Imported `removeB2BModule`, added `--with b2b` flag parsing, updated features array construction, added B2B removal guard in Step 4

## Decisions Made

- B2B is opt-in (not opt-out): the `--with b2b` pattern is opposite to the existing `--without billing` pattern, because B2B is enterprise-only and should not be in every generated project by default.
- `django-unfold` is NOT removed by `removeB2BModule` — it is an unconditional dependency (admin theme for all projects), not B2B-specific.
- `stripMarkerBlocks` uses a dynamic import of `globby` inside `removeB2BModule` body to match the existing ESM import pattern used elsewhere in remove.ts.
- B2B multiselect option intentionally absent from `initialValues` — must remain unchecked by default.

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Phase 31 (cli-scaffolder-integration) complete: B2B scaffolder integration fully implemented and tested
- All 6 scaffolder tests GREEN (billing, email, observability, social-auth, and 2 new B2B tests)
- The `--with b2b` flag is the sole mechanism for including B2B code in scaffolded projects; default scaffold is B2B-free

---

_Phase: 31-cli-scaffolder-integration_
_Completed: 2026-03-13_

## Self-Check: PASSED

- transform.ts: FOUND — exports `stripMarkerBlocks`
- remove.ts: FOUND — exports `removeB2BModule`
- prompts.ts: FOUND — contains `"b2b"` in type and options
- index.ts: FOUND — wired with flag parsing and removal guard
- 31-02-SUMMARY.md: FOUND
- Commit 300363c: FOUND (Task 1)
- Commit 725e2ac: FOUND (Task 2)
