---
phase: 03-shared-packages-type-generation
plan: 03-02
subsystem: shared-packages
tags: [openapi-fetch, openapi-react-query, react-query, tsup]

# Dependency graph
requires:
  - phase: 03-01
    provides: OpenAPI schema artifacts consumed by the client generator
provides:
  - Shared `@repo/api-client` workspace package exporting the typed fetch factory and React Query wrapper
  - Build tooling that emits dual ESM/CJS bundles plus `.d.ts` output for the client
affects: [apps/web, apps/mobile, packages/business-logic]

# Tech tracking
tech-stack:
  added: [openapi-fetch, openapi-react-query, @tanstack/react-query, tsup]
  patterns: ["Env-aware API factories sourced from shared OpenAPI types", "Tsup-based dual bundle builds for workspace libraries"]

key-files:
  created:
    - packages/api-client/package.json
    - packages/api-client/src/create-client.ts
    - packages/api-client/src/errors.ts
    - packages/api-client/src/index.ts
    - packages/api-client/src/react-query.ts
    - packages/api-client/tsconfig.json
    - packages/api-client/eslint.config.js
    - packages/api-client/tsup.config.ts
  modified:
    - pnpm-lock.yaml

key-decisions:
  - "Export `./gen/v1` directly from the tracked OpenAPI snapshot so consumers always import the committed artifact without requiring extra copy steps"

patterns-established:
  - "OpenAPI React Query bundle: build TanStack Query clients straight from `openapi-fetch` and expose them as shared hooks"
  - "Normalized API error surface that always throws `{ code, message, details }` via `ApiError`"

# Metrics
duration: 7 min
completed: 2026-02-16
---

# Phase 03 Plan 02: Shared API Client Summary

**Env-aware @repo/api-client package with typed openapi-fetch factory, React Query bindings, and tsup dual-bundle build**

## Performance

- **Duration:** 7 min
- **Started:** 2026-02-16T04:02:22Z
- **Completed:** 2026-02-16T04:09:58Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments

- Created the `@repo/api-client` workspace package with scripts, peer deps, lint/type-check commands, and env-driven configuration defaults
- Implemented `createApiClient`, React Query helpers, and shared error normalization powered by the generated OpenAPI `paths`
- Added a tsup configuration that emits CJS/ESM bundles plus declarations so Turbo build/type-check pipelines pick up the client

## Task Commits

Each task was committed atomically:

1. **Task 1: Scaffold typed API + React Query clients** - `c3ca75e` (feat)
2. **Task 2: Configure tsup build + scripts** - `f0d6281` (chore)

**Plan metadata:** docs(03-02): record plan execution

## Files Created/Modified

- `packages/api-client/package.json` - Defines workspace package metadata, exports, scripts, and dependencies
- `packages/api-client/src/create-client.ts` - Env-aware `openapi-fetch` factory with token injection middleware
- `packages/api-client/src/react-query.ts` - Helper to build TanStack Query clients + QueryClient bundle
- `packages/api-client/src/errors.ts` - Shared `ApiError` surface and helpers to unwrap results
- `packages/api-client/src/index.ts` - Public entrypoint that re-exports factories, errors, and types
- `packages/api-client/tsconfig.json` - Library compiler config targeting ES2022 + DOM types
- `packages/api-client/eslint.config.js` - Hooks package linting into the shared flat config
- `packages/api-client/tsup.config.ts` - Dual ESM/CJS build with declarations for Turbo compatibility
- `pnpm-lock.yaml` - Captures dependency graph updates for new package dependencies

## Decisions Made

- Expose `@repo/api-client/gen/v1` from the committed `src/gen` artifact so consumers always read the exact OpenAPI snapshot without extra build steps or runtime copies

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Both Next.js and Expo apps can now drop in the shared client instead of touching `openapi-fetch` directly.
- Ready for follow-up plans to build higher-level business hooks (`packages/business-logic`) on top of this client.

---

_Phase: 03-shared-packages-type-generation_
_Completed: 2026-02-16_

## Self-Check: PASSED
