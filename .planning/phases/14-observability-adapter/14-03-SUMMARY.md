---
phase: 14-observability-adapter
plan: "03"
subsystem: ui
tags:
  [posthog, analytics, session-replay, next-js, expo, react-native, page-tracking, screen-tracking]

# Dependency graph
requires:
  - phase: 14-observability-adapter
    provides: ObservabilityAdapter ABC and PostHogAdapter Django backend — frontend counterpart to this plan

provides:
  - PostHog provider integration in Next.js web app with automatic $pageview tracking
  - PostHog provider integration in Expo mobile app with automatic $screen tracking
  - Session replay with maskAllInputs: true privacy default in web
  - Both frontends work with no PostHog key set — SDK silences itself via opt_out_capturing()

affects:
  [any phase adding new web pages or mobile screens, phase adding feature flags UI, UX phases]

# Tech tracking
tech-stack:
  added:
    - posthog-js ^1.360.1 (web analytics + session replay)
    - posthog-react-native ^4.37.2 (mobile analytics)
    - expo-file-system ~18.0.12
    - expo-application ~6.0.2
    - expo-device ~7.0.3
    - expo-localization ~16.0.1
  patterns:
    - posthog.init() at module level with typeof window guard — prevents SSR double-init
    - PostHogPageView inner component using useRef dedup — prevents double-firing on React StrictMode re-renders
    - PostHogScreenTracker using useSegments with prevSegmentsRef dedup — same dedup pattern for mobile
    - autocapture={{ captureScreens: false }} on Expo — mandatory to avoid Expo Router/useNavigationState crash
    - loaded callback with opt_out_capturing() when no key — build-safe no-op without PostHog credentials

key-files:
  created: []
  modified:
    - apps/web/app/providers.tsx
    - apps/web/.env.example
    - apps/mobile/app/_layout.tsx
    - apps/mobile/.env.example
    - apps/mobile/app.json

key-decisions:
  - "PostHogProvider as outermost wrapper in both apps — ensures PostHogPageView/PostHogScreenTracker can use usePostHog() hook inside the provider tree"
  - "capture_pageview: false in posthog.init() + manual PostHogPageView — Next.js App Router requires manual tracking; autocapture misses client-side navigations"
  - "autocapture={{ captureScreens: false }} in Expo — Expo Router is incompatible with PostHog's useNavigationState-based screen autocapture (crashes on launch)"
  - "loaded callback opts out when no NEXT_PUBLIC_POSTHOG_KEY — no-op in CI and dev without credentials, avoids console errors"
  - "useRef dedup in both trackers — prevents duplicate events from StrictMode double-renders and Suspense re-mounts"
  - "eu.i.posthog.com ingestion host default (not eu.posthog.com) — eu.posthog.com is the app UI URL, not the ingestion endpoint"

patterns-established:
  - "PostHog init pattern: module-level with window guard, no-key opt_out_capturing in loaded callback"
  - "Page/screen tracking dedup: useRef with prevValue comparison before firing capture/screen"

requirements-completed: [OBS-03]

# Metrics
duration: 3min
completed: 2026-03-11
---

# Phase 14 Plan 03: PostHog Frontend Providers Summary

**PostHog providers added to Next.js web and Expo mobile apps — automatic $pageview and $screen tracking with session replay, no per-page instrumentation required**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-11T19:11:27Z
- **Completed:** 2026-03-11T19:11:57Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Next.js web app: posthog.init() with SSR guard + PostHogPageView tracking all client-side navigations via usePathname + PostHogProvider wrapping AppProviders
- Expo mobile app: PostHogScreenTracker using useSegments for all screen changes + PostHogProvider as outermost wrapper with autocapture.captureScreens=false
- Both apps gracefully degrade to no-op when no PostHog API key is set — zero console errors in CI/dev

## Task Commits

Each task was committed atomically:

1. **Task 1: Add PostHog to Next.js web app** - `dc69d98` (feat)
2. **Task 2: Add PostHog to Expo mobile app** - `dc0b1ac` (feat)

**Plan metadata:** _(see final commit below)_

## Files Created/Modified

- `apps/web/app/providers.tsx` - Added posthog.init(), PostHogPageView component, PostHogProvider outermost wrapper
- `apps/web/.env.example` - Added NEXT_PUBLIC_POSTHOG_KEY and NEXT_PUBLIC_POSTHOG_HOST
- `apps/mobile/app/_layout.tsx` - Added PostHogScreenTracker, PostHogProvider outermost wrapper
- `apps/mobile/.env.example` - Added EXPO_PUBLIC_POSTHOG_KEY
- `apps/mobile/app.json` - Added expo-localization plugin (added by npx expo install)

## Decisions Made

- PostHogProvider is outermost in both apps so inner tracker components can call usePostHog() — if wrapped inside AuthProvider the hook would be unavailable
- capture_pageview: false is mandatory in Next.js App Router — the SDK's built-in page tracking doesn't fire on client-side navigation between routes
- autocapture={{ captureScreens: false }} is a hard requirement for Expo Router — PostHog's default screen tracking calls useNavigationState which conflicts with Expo Router's navigation model and crashes the app on launch
- eu.i.posthog.com (not eu.posthog.com) — the eu.posthog.com URL is the PostHog app dashboard; eu.i.posthog.com is the ingestion API endpoint

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

Pre-existing TypeScript errors in both apps (`AuthProvider` missing required props from a type definition mismatch, `SecureStoreAdapter` export missing from `@repo/business-logic`) were confirmed pre-existing via `git stash` verification. These errors exist on both apps' baselines before any changes in this plan — out of scope per deviation rules scope boundary. No new TypeScript errors introduced.

## User Setup Required

To enable PostHog analytics:

1. Get a PostHog project API key from [PostHog](https://eu.posthog.com)
2. For web: add `NEXT_PUBLIC_POSTHOG_KEY=phc_...` to `apps/web/.env.local`
3. For mobile: add `EXPO_PUBLIC_POSTHOG_KEY=phc_...` to `apps/mobile/.env`
4. Verify: navigate pages (web) or screens (mobile) → check PostHog Live Events within 30s

Leave variables empty (or omit) to disable PostHog entirely — no errors, no data sent.

## Next Phase Readiness

- OBS-03 frontend half complete — PostHog providers installed and auto-tracking on both frontends
- PostHog backend (Django) should already be wired via 14-01/14-02 ObservabilityAdapter plans
- No blockers for subsequent phases

## Self-Check: PASSED

- apps/web/app/providers.tsx: FOUND
- apps/mobile/app/\_layout.tsx: FOUND
- apps/web/.env.example: FOUND
- apps/mobile/.env.example: FOUND
- 14-03-SUMMARY.md: FOUND
- Commit dc69d98: FOUND
- Commit dc0b1ac: FOUND

---

_Phase: 14-observability-adapter_
_Completed: 2026-03-11_
