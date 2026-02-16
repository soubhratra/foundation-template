---
phase: 03-shared-packages-type-generation
plan: 06
subsystem: shared-packages
tags: [nextjs, expo, react-query, react-hook-form, shared-ui]

# Dependency graph
requires:
  - phase: 03-05
    provides: "@repo/business-logic AuthProvider and auth hooks"
provides:
  - Web + mobile bundlers transpile/watch shared packages without Metro/Next errors
  - Root layouts wrap children with AuthProvider using env-configured /api/v1 URLs
  - Starter login screens exercise @repo/ui, @repo/validation, and @repo/business-logic together
affects: [phase-04-web-application, phase-05-mobile-application]

# Tech tracking
tech-stack:
  added: [@hookform/resolvers, react-hook-form, @tanstack/react-query-devtools, expo-secure-store]
  patterns: ["AppProviders client wrapper keeps Next.js layout server-rendered", "Expo layout owns secure-store-backed token storage"]

key-files:
  created: [apps/web/app/providers.tsx]
  modified:
    - apps/web/package.json
    - apps/mobile/package.json
    - apps/web/next.config.ts
    - apps/mobile/metro.config.js
    - apps/web/app/layout.tsx
    - apps/mobile/app/_layout.tsx
    - apps/web/app/env.ts
    - apps/mobile/lib/env.ts
    - apps/web/app/page.tsx
    - apps/mobile/app/index.tsx
    - pnpm-lock.yaml

key-decisions:
  - "Use a dedicated client Providers component so the Next.js root layout stays server-rendered while configuring AuthProvider."
  - "Disable React Query Devtools on Expo until a native target exists to avoid bundling DOM-only tooling."

patterns-established:
  - "AuthProvider wrappers always receive env-derived /api/v1 URLs plus platform-specific token storage (localStorage vs expo-secure-store)."
  - "React Hook Form + Controller + @repo/ui primitives form the cross-platform pattern for future auth screens."

# Metrics
duration: 3h 50m
completed: 2026-02-16
---

# Phase 03 Plan 06: Shared package consumption Summary

**Web and Expo entrypoints now import @repo/ui, @repo/validation, and @repo/business-logic via AuthProvider-backed login flows hitting the Django /api/v1 stack.**

## Performance

- **Duration:** 3h 50m
- **Started:** 2026-02-16T07:18:06Z
- **Completed:** 2026-02-16T11:09:05Z
- **Tasks:** 3
- **Files modified:** 11

## Accomplishments

- Added shared package + form dependencies plus Next/Metro resolver rules so both bundlers pick up @repo/ui and @repo/business-logic without manual linking.
- Wrapped the Next.js body subtree and Expo Router root with AuthProvider instances that derive /api/v1 base URLs from validated env modules and store tokens appropriately (localStorage vs expo-secure-store).
- Replaced placeholder landing pages with react-hook-form login flows that use @repo/ui primitives, @repo/validation loginSchema, and useAuth mutations (session login on web, JWT login on mobile) while surfacing mutation state to the UI.

## Task Commits

Each task was committed atomically:

1. **Task 1: Update bundlers and dependencies to consume shared packages** - `9f58f49` (feat)
2. **Task 2: Wrap root layouts with AuthProvider** - `ae41579` (feat)
3. **Task 3: Build shared login screens using common packages** - `3c74971` (feat)

**Plan metadata:** _pending_ (docs commit after STATE update)

## Files Created/Modified

- `apps/web/app/providers.tsx` - Client-side provider that instantiates AuthProvider with localStorage-backed tokens for the web layout.
- `apps/mobile/app/_layout.tsx` - Expo Router root now wraps `<Stack />` in AuthProvider with expo-secure-store token storage and env-based API base URL.
- `apps/web/app/page.tsx`, `apps/mobile/app/index.tsx` - Shared login forms built with @repo/ui components, @repo/validation schemas, and useAuth mutations.
- `apps/web/package.json`, `apps/mobile/package.json`, `pnpm-lock.yaml` - Added @repo shared packages, react-query peers, react-hook-form tooling, and expo-secure-store.
- `apps/web/next.config.ts`, `apps/mobile/metro.config.js` - Documented transpile, alias, watch, and resolver settings so both bundlers rebuild when shared packages change.

## Decisions Made

- Use a thin `AppProviders` client wrapper to keep the Next.js layout server-rendered while configuring AuthProvider and token storage.
- Disable React Query Devtools on Expo (while still depending on the package) until a native renderer exists, preventing DOM-only tooling from executing on-device.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Web and Expo shells now consume all shared packages, so Phase 04/05 feature plans can build real auth flows on top of working providers and form scaffolding.
- React Query lint/type-check commands succeeded (`pnpm --filter web|mobile type-check` and `pnpm --filter web|mobile lint`), confirming the shared wiring is stable.

## Self-Check: PENDING
