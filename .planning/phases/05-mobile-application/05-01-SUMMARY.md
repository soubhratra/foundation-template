---
phase: 05-mobile-application
plan: 01
subsystem: mobile
tags: [expo-router, react-native, navigation, auth]

# Dependency graph
requires:
  - phase: 04-web-application
    provides: Shared auth flows + @repo packages baseline
provides:
  - Guarded Expo Router root layout with SplashScreen-aware AuthGate
  - Authenticated tab navigator skeleton with lucide icons and Detox IDs
  - Shared auth route group shell and placeholder screens for forms
affects: [05-mobile-application-plan-02, detox-tests]

# Tech tracking
tech-stack:
  added: [lucide-react-native, react-native-svg]
  patterns:
    - SplashScreen + useSegments AuthGate that hides UI until tokens resolve
    - Central tab-bar helper to stamp lucide icons and consistent testIDs

key-files:
  created:
    - apps/mobile/app/(tabs)/_layout.tsx
    - apps/mobile/app/(tabs)/home.tsx
    - apps/mobile/app/(tabs)/activity.tsx
    - apps/mobile/app/(tabs)/profile.tsx
    - apps/mobile/app/(tabs)/settings.tsx
    - apps/mobile/components/navigation/tab-bar.tsx
  modified:
    - apps/mobile/app/_layout.tsx
    - apps/mobile/app/index.tsx
    - apps/mobile/app/(auth)/_layout.tsx
    - apps/mobile/app/(auth)/sign-in.tsx
    - apps/mobile/app/(auth)/sign-up.tsx
    - apps/mobile/metro.config.js
    - apps/mobile/package.json
    - pnpm-lock.yaml

key-decisions:
  - Added Metro alias for @repo/api-client so Expo bundler can resolve shared hooks during smoke tests.
  - Redirected the root index route to /(auth)/sign-in to keep deep links inside the guarded stack consistent.
  - Standardized lucide-react-native icons + helper-generated tab testIDs for Detox.

patterns-established:
  - "AuthGate orchestrates SplashScreen + useSegments redirects so tabs/auth never flicker during token restore"
  - "createTabOptions helper wraps lucide icons, labels, and Detox testIDs for every tab"

# Metrics
duration: 12 min
completed: 2026-02-16
---

# Phase 05 Plan 01: Mobile Navigation Skeleton Summary

**Expo Router root now gates auth vs tab stacks with a lucide-powered navigation shell and SplashScreen-safe auth guard.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-02-16T16:26:02Z
- **Completed:** 2026-02-16T16:38:11Z
- **Tasks:** 3
- **Files modified:** 14

## Accomplishments
- Root layout now uses an AuthGate that blocks rendering until SecureStore tokens load, hides SplashScreen properly, and flips Stack.Protected segments via `useSegments` redirects.
- `(auth)` route group gained a shared SafeArea shell plus placeholder sign-in/up screens with `Link` + `router.replace` wiring for upcoming forms.
- Added lucide-based tab navigator, shared tab bar helper, Detox testIDs, and placeholder Home/Activity/Profile/Settings screens so future plans can focus on data instead of plumbing.

## Task Commits

Each task was committed atomically:

1. **Task 1: Guard root layout with Stack.Protected + SplashScreen** - `dc152f2` (feat)
2. **Task 2: Scaffold (auth) route group shell** - `2628181` (feat)
3. **Task 3: Build tab navigator with lucide icons + placeholder screens** - `de6dcbf` (feat)

Plan metadata commit pending.

## Files Created/Modified
- `apps/mobile/app/_layout.tsx` - AuthGate + SplashScreen logic, Stack.Protected guards, and router redirects
- `apps/mobile/app/(auth)/*` - SafeArea auth shell plus placeholder sign-in/sign-up screens with navigation stubs
- `apps/mobile/app/(tabs)/*` - Tabs layout and four placeholder destination screens wired to lucide icons
- `apps/mobile/components/navigation/tab-bar.tsx` - Helper for lucide icons, labels, and Detox testIDs
- `apps/mobile/metro.config.js` - Added @repo/api-client alias/watch folder for Expo bundler
- `apps/mobile/package.json`, `pnpm-lock.yaml` - Added lucide-react-native + react-native-svg dependencies

## Decisions Made
- Added Metro alias for @repo/api-client so Expo bundler can resolve shared hooks during smoke tests.
- Redirected the root index route to /(auth)/sign-in to keep deep links inside the guarded stack consistent.
- Standardized lucide-react-native icons + helper-generated tab testIDs for Detox.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Expo bundler could not resolve @repo/api-client**
- **Found during:** Task 3 (tab navigator smoke test)
- **Issue:** `expo start --offline` failed because Metro could not resolve `@repo/api-client` referenced by `@repo/business-logic`.
- **Fix:** Added the package to `sharedPackages`/`extraNodeModules` in `metro.config.js` so Metro points at the workspace source.
- **Files modified:** apps/mobile/metro.config.js
- **Verification:** Reran `pnpm --filter @repo/mobile exec expo start --offline` successfully.
- **Committed in:** `de6dcbf`

**Total deviations:** 1 auto-fixed (blocking). **Impact:** Fix was required for Expo smoke test and keeps Metro aligned with workspace packages.

## Issues Encountered
- Expo Router’s `--web` static render path still throws “Objects are not valid as a React child” when using the custom `Stack.Protected` wrapper. Native (`expo start --offline`) bundling succeeds, so the plan target is unblocked, but web parity will need a follow-up once a supported guard abstraction ships.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Auth/tabs skeleton is in place with lucide icons, Detox IDs, and placeholder flows, so Plan 05-02 can focus on real sign-in/up form logic without reworking navigation.

## Self-Check: PASSED
