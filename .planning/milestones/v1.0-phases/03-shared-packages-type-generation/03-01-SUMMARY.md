---
phase: 03-shared-packages-type-generation
plan: 01
subsystem: packages
tags: [openapi, turbo, typescript]
requires:
  - phase: 02-api-core-auth-backend
    provides: export_openapi_schema management command
provides:
  - deterministic OpenAPI + TypeScript generation pipeline
  - pnpm/turbo entrypoints for regenerating shared API clients
affects: [04-web-auth-flows, 05-mobile-auth]
tech-stack:
  added: []
  patterns: [deterministic-schema-regeneration]
key-files:
  created: []
  modified:
    - package.json
    - apps/api/package.json
    - scripts/generate-api-types.mjs
    - turbo.json
    - packages/api-client/openapi.json
    - packages/api-client/src/gen/v1.d.ts
    - pnpm-lock.yaml
key-decisions:
  - "Run turbo generate:api-types only in @repo/api so CI stays focused on backend schema changes"
patterns-established:
  - "Always regenerate shared API types through pnpm generate:types before committing controller changes"
duration: 15 min
completed: 2026-02-16
---

# Phase 03 Plan 01: Shared API Type Generation Summary

**End-to-end OpenAPI export now runs via pnpm generate:types and writes tracked artifacts for downstream packages.**

## Performance

- **Duration:** 15 min
- **Started:** 2026-02-16T03:43:55Z
- **Completed:** 2026-02-16T03:59:08Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- Regenerated the committed OpenAPI snapshot and TypeScript declarations so downstream clients reflect the current Django schema.
- Wired pnpm scripts and a turbo pipeline so `pnpm generate:types` re-runs the exporter with a single command.
- Documented the workflow inside the generator script to reinforce the expectation that schema-affecting changes trigger the pipeline.

## Task Commits

Each task was committed atomically:

1. **Task 1: Script deterministic OpenAPI export + type generation** - `5ac717c` (feat)
2. **Task 2: Expose pnpm/turbo entrypoints for the pipeline** - `48ff07f` (feat)

**Plan metadata:** (pending) (docs: complete plan)

## Files Created/Modified

- `package.json` / `apps/api/package.json` - Added pnpm/turbo scripts that drive the generator from both the repo root and the backend workspace.
- `scripts/generate-api-types.mjs` - Documented when to run the script while keeping the normalized export flow intact.
- `turbo.json` - Described the file inputs/outputs for the generate:api-types task so caching and CI comparisons are accurate.
- `packages/api-client/openapi.json` / `packages/api-client/src/gen/v1.d.ts` - Updated committed artifacts to match the freshly exported schema.
- `pnpm-lock.yaml` - Captured dependency metadata for `openapi-typescript` so the CLI resolves without a global install.

## Decisions Made

- Filtered the turbo task to `@repo/api` so CI only executes the exporter where the Django source files live, avoiding unnecessary runs in unrelated packages.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Turbo filtering against the root package failed because the workspace exposes only scoped packages. Switching the filter to `@repo/api` keeps the command scoped to the backend while satisfying the plan requirement.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Shared API typings now regenerate deterministically, unblocking later frontend and mobile phases that depend on accurate client contracts.

## Self-Check: PASSED
