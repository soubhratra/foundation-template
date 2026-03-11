---
phase: 03-shared-packages-type-generation
plan: 05
subsystem: shared-packages
tags: [react-query, openapi, storage, tsup]

# Dependency graph
requires:
  - phase: 03-02
    provides: "@repo/api-client + validation exports"
  - phase: 03-04
    provides: "UI primitives consumed by future auth surfaces"
provides:
  - Shared AuthProvider + hooks package powering web and mobile
  - Token storage adapters for browser/local + Expo SecureStore
  - tsup build outputs (ESM/CJS/d.ts) wired into workspace tooling
affects: [apps/web, apps/mobile]

# Tech tracking
tech-stack:
  added: ["@tanstack/react-query-devtools"]
  patterns:
    - React Query context provider exporting cross-platform auth state

key-files:
  created:
    - packages/business-logic/src/auth-provider.tsx
    - packages/business-logic/src/hooks/use-auth.ts
    - packages/business-logic/src/utils/storage.ts
  modified:
    - packages/business-logic/tsconfig.json
    - pnpm-lock.yaml

key-decisions:
  - "Bound Allauth auth endpoints via fetch until OpenAPI spec exposes them to openapi-react-query"

patterns-established:
  - "TokenStorage interface with platform-specific adapters (memory, web, SecureStore)"
  - "Devtools-aware QueryClient provider usable in both Next.js and Expo"

# Metrics
duration: 1h 2m
completed: 2026-02-16
---

# Phase 03 Plan 05: Shared business-logic hooks Summary

**AuthProvider, token persistence helpers, and React Query hooks unify login/logout flows for both clients.**

## Performance

- **Duration:** 1h 2m
- **Started:** 2026-02-16T04:12:50Z
- **Completed:** 2026-02-16T05:15:25Z
- **Tasks:** 3
- **Files modified:** 10

## Accomplishments

- Added the `@repo/business-logic` workspace with an AuthProvider that wraps `buildApiQueryClient`, lazy React Query Devtools, and shared context exports.
- Delivered typed `useAuth`/`useUser` hooks plus TokenStorage adapters (memory, browser, SecureStore) so apps can persist session + JWT tokens per platform.
- Configured tsup/tsconfig/package exports so the package emits ESM, CJS, and d.ts bundles and can be resolved via `@repo/business-logic`.
- Validated the new workspace by rebuilding it and re-running `pnpm --filter web|mobile type-check` and lint commands to ensure no regressions downstream.

## Task Commits

Each task was committed atomically:

1. **Task 1: Create @repo/business-logic with auth hooks** - `4f88b20` (feat)
2. **Task 2: Implement storage helpers + hook exports** - `be9ab10` (feat)
3. **Task 3: Configure tsup build + package exports** - `7ccff5f` (chore)

**Plan metadata:** _Pending - recorded after SUMMARY + STATE updates_

## Files Created/Modified

- `packages/business-logic/package.json` - Declares workspace metadata, scripts, deps, and exports map.
- `packages/business-logic/src/auth-provider.tsx` - Provides QueryClient context, lazy devtools, and token-aware API bundle.
- `packages/business-logic/src/hooks/use-auth.ts` - Implements shared `useAuth` login/logout hooks with optional per-call storage overrides.
- `packages/business-logic/src/hooks/use-user.ts` - Lightweight hook that derives auth state from the QueryClient cache.
- `packages/business-logic/src/utils/storage.ts` - Defines the TokenStorage interface plus memory/web/SecureStore adapters.
- `packages/business-logic/tsconfig.json` - Points `baseUrl` to `src` and maps `@repo/business-logic` for downstream TypeScript resolution.
- `packages/business-logic/tsup.config.ts` - Builds ESM/CJS/d.ts bundles with the proper externals.
- `pnpm-lock.yaml` - Captures workspace dependency graph updates for the new package.

## Decisions Made

- Used direct `fetch` bindings for Allauth session/JWT endpoints because the OpenAPI snapshot currently omits those routes; we can switch back to openapi-react-query mutations once the spec includes them.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added manual auth endpoint bindings while spec is incomplete**

- **Found during:** Task 1 (Create package)
- **Issue:** Allauth login/logout endpoints are absent from the generated OpenAPI schema, so openapi-react-query mutations cannot be typed for those routes.
- **Fix:** Issued typed `fetch` helpers inside `useAuth` and routed responses through the new TokenStorage abstraction so we can persist session/JWT values until the spec is updated.
- **Files modified:** packages/business-logic/src/hooks/use-auth.ts, packages/business-logic/src/utils/storage.ts
- **Verification:** `pnpm --filter @repo/business-logic build`
- **Committed in:** 4f88b20

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Ensured login/logout flows function despite missing OpenAPI definitions; scope remains aligned with plan deliverables.

## Issues Encountered

- ESLint emitted existing `MODULE_TYPELESS_PACKAGE_JSON` warnings for apps/web and apps/mobile during lint runs; no changes were required for this plan.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Shared auth hooks now exist, so upcoming plans can wrap layouts in `AuthProvider` and wire login/logout screens without duplicating logic.
- Pending follow-up: regenerate the OpenAPI schema with Allauth endpoints so we can convert the manual fetch mutations into openapi-react-query calls.

---

_Phase: 03-shared-packages-type-generation_
_Completed: 2026-02-16_

## Self-Check: PASSED
