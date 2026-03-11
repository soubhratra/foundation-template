---
phase: 03-shared-packages-type-generation
plan: 04
subsystem: shared-packages
tags: [react-native-web, tsup, expo]
requires:
  - phase: 03-03
    provides: "validation helpers that rely on shared TS configs"
provides:
  - "@repo/ui package exporting RN primitives usable by Next.js + Expo"
  - "Bundler wiring so both apps transpile/react-native-web alias the package"
affects: [phase-04-web-application, phase-05-mobile-application]
tech-stack:
  added: [tsup]
  patterns:
    - "React Native primitives live in a workspace package and ship dual-format bundles"
    - "Next.js + Metro alias react-native to react-native-web for shared components"
key-files:
  created:
    - packages/ui/src/primitives/Button.tsx
    - packages/ui/src/primitives/Input.tsx
  modified:
    - apps/web/next.config.ts
    - apps/mobile/metro.config.js
key-decisions:
  - "Use React 19 type definitions across Expo to eliminate ReactNode mismatches"
patterns-established:
  - "Theme-driven RN primitives with consistent StyleProp overrides"
  - "tsup pipelines emitting ESM, CJS, and .d.ts outputs for shared packages"
duration: 14 min
completed: 2026-02-16
---

# Phase 03 Plan 04: Shared UI Primitives Summary

**React Native Web primitives now live in @repo/ui with Web + Expo bundlers configured to transpile and alias them consistently.**

## Performance

- **Duration:** 14 min
- **Started:** 2026-02-16T03:44:02Z
- **Completed:** 2026-02-16T03:58:19Z
- **Tasks:** 2
- **Files modified:** 13

## Accomplishments

- Created the `@repo/ui` workspace with themed `Button`, `Text`, `Input`, and `Card` primitives that wrap React Native components so both apps share identical markup.
- Added a reusable theme token file plus index exports so downstream callers have a single import surface.
- Configured `tsup` to emit clean CJS/ESM bundles with declarations while treating React/React Native dependencies as externals.
- Wired Next.js and Expo Metro to transpile `@repo/ui`, alias `react-native` ➜ `react-native-web`, and watch the workspace packages folder so imports resolve in both dev servers.
- Verified the package builds and both apps pass `tsc --noEmit`, ensuring the shared primitives do not introduce type regressions.

## Task Commits

1. **Task 1: Build @repo/ui primitives** - `0f61b0a` (feat)
2. **Task 2: Configure tsup build + exports for @repo/ui** - `83e33da` (chore)

## Files Created/Modified

- `packages/ui/src/primitives/Button.tsx` - Pressable-based button with size/variant + loading support.
- `packages/ui/src/primitives/Input.tsx` - Shared TextInput with label, helper/error text, and focus ring state.
- `packages/ui/src/theme.ts` - Color, spacing, and typography tokens consumed by each primitive.
- `packages/ui/package.json` / `packages/ui/tsup.config.ts` - Scripts, dual-format exports, and tsup build configuration.
- `apps/web/next.config.ts` - Added `@repo/ui` to `transpilePackages` and aliased `react-native` to `react-native-web` with web-specific extensions.
- `apps/mobile/metro.config.js` - Watched workspace packages, mapped `@repo/ui`, and disabled hierarchical lookup to keep Metro aware of shared code.
- `apps/mobile/tsconfig.json` & `apps/mobile/package.json` - Scoped type roots and aligned `@types/react` so Expo type-checking uses the same ReactNode definition as the rest of the monorepo.

## Decisions Made

- Aligned Expo's `@types/react` dependency with React 19 definitions (and constrained `typeRoots`) to avoid JSX runtime mismatches when consuming RN components from `@repo/ui`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Expo type-check failed with mismatched ReactNode definition**

- **Found during:** Task 2 (bundler wiring)
- **Issue:** `pnpm --filter @repo/mobile type-check` could not render `<Stack />` because React 19 types (from the repo root) conflicted with Expo's local React 18 types, resulting in a `bigint` assignment error.
- **Fix:** Scoped mobile `typeRoots` and bumped `@types/react` to `^19.0.0` so Metro + Expo share the same ReactNode definition as the rest of the monorepo.
- **Files modified:** apps/mobile/package.json, apps/mobile/tsconfig.json
- **Verification:** `pnpm --filter @repo/mobile type-check`
- **Committed in:** 83e33da

**Total deviations:** 1 auto-fixed (bug). **Impact:** Required to unblock Expo type-checking so shared primitives compile everywhere.

## Issues Encountered

- Expo type-check initially failed because the project mixed React 18 and 19 type packages; resolved by aligning `@types/react` across the workspace (see deviation).

## User Setup Required

None - no third-party services or secrets were added.

## Next Phase Readiness

- `@repo/ui` now exports stable primitives and both bundlers know how to load them, so Phase 03 Plan 05 and upcoming Phase 04 web work can immediately consume the shared package.

## Self-Check

- `packages/ui/src/primitives/Button.tsx` - FOUND
- `apps/web/next.config.ts` - FOUND
- Commits `0f61b0a`, `83e33da` - FOUND in git log

**Self-Check: PASSED**
