---
phase: 21-gdpr-baseline
plan: "03"
subsystem: ui
tags: [posthog, analytics, gdpr, cookie-consent, localStorage, next.js, shadcn]

requires:
  - phase: 21-01
    provides: GDPR infrastructure contracts and research establishing localStorage key 'analytics_consent'

provides:
  - CookieConsentBanner client component with consent-gated posthog.init()
  - providers.tsx refactored to remove unconditional PostHog initialisation
  - Root layout wired to render CookieConsentBanner as fixed bottom overlay

affects: [22-billing-portal, 23-entitlements, any phase adding analytics or user tracking]

tech-stack:
  added: []
  patterns:
    - "Consent-gated analytics: posthog.init() called only after user grants consent via localStorage key"
    - "Hydration-safe boolean gate: useState(false) + useEffect reads localStorage to avoid SSR mismatch"
    - "Double-init guard: useRef<boolean> initialized=false, checked before calling posthog.init()"

key-files:
  created:
    - apps/web/src/components/cookie-consent-banner.tsx
  modified:
    - apps/web/app/providers.tsx
    - apps/web/app/layout.tsx

key-decisions:
  - "posthog.init() moved entirely out of providers.tsx into CookieConsentBanner — PostHogProvider wrapper stays (enables usePostHog() hooks) but init is consent-gated"
  - "Banner uses fixed bottom bar layout (not modal) — plan spec locked this; clicking outside does not count as consent"
  - "localStorage key 'analytics_consent' with values 'granted'|'denied'|absent — established in CONTEXT.md; banner re-show suppressed when key is present"

patterns-established:
  - "Cookie consent pattern: useState(false) initial state prevents hydration error; useEffect on mount reads localStorage and branches on granted/denied/absent"
  - "PostHog init guard: useRef<boolean> initialized=false prevents double-init on re-render or StrictMode double-invocation"

requirements-completed: [GDPR-03]

duration: 3min
completed: 2026-03-12
---

# Phase 21 Plan 03: GDPR Cookie Consent Banner Summary

**Consent-gated PostHog analytics via fixed bottom banner: posthog.init() removed from providers.tsx and moved behind localStorage analytics_consent gate in CookieConsentBanner component**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-12T20:02:58Z
- **Completed:** 2026-03-12T20:06:00Z
- **Tasks:** 2
- **Files modified:** 3 (+ 1 pre-existing bug fix)

## Accomplishments

- Created `CookieConsentBanner` client component: shows fixed bottom bar for first-time visitors, calls `posthog.init()` on Accept, calls `posthog.opt_out_capturing()` on Decline, stores choice in `localStorage`
- Removed unconditional `posthog.init()` block from `providers.tsx` (was firing on every page load before any user consent — ePrivacy Directive violation)
- Wired `CookieConsentBanner` into root `layout.tsx` as last child inside `ThemeProvider`

## Task Commits

Each task was committed atomically:

1. **Task 1: Create CookieConsentBanner and refactor providers.tsx** - `5f061ee` (feat)
2. **Task 2: Wire CookieConsentBanner into root layout** - `e217e6e` (feat)

## Files Created/Modified

- `apps/web/src/components/cookie-consent-banner.tsx` - New client component: consent-gated posthog.init(), fixed bottom bar UI with Accept/Decline buttons
- `apps/web/app/providers.tsx` - Removed unconditional `if (typeof window !== "undefined") { posthog.init(...) }` block; PostHogProvider wrapper preserved
- `apps/web/app/layout.tsx` - Added CookieConsentBanner import and render

## Decisions Made

- PostHog init config values (api_host, capture_pageview, session_recording) carried verbatim from the removed providers.tsx block into the banner's `initPostHogOnce()` helper
- `initPostHogOnce` is a module-scope function taking the ref as parameter — avoids useCallback dependency array complexity while maintaining the double-init guard

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed pre-existing TypeScript error in billing-client.tsx**

- **Found during:** Task 1 build verification
- **Issue:** `match[1]` typed as `string | undefined` but function return type was `string` — TypeScript strict mode error blocking build
- **Fix:** Changed `return match ? match[1] : ""` to `return match ? (match[1] ?? "") : ""`
- **Files modified:** `apps/web/app/(dashboard)/billing/billing-client.tsx`
- **Verification:** `pnpm turbo build --filter=@repo/web` passed after fix
- **Committed in:** `5f061ee` (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Pre-existing error blocked build verification; fix was minimal and necessary. No scope creep.

## Issues Encountered

- `pnpm build` inside `apps/web/` directly fails with `Module not found: @repo/business-logic` — must run `pnpm turbo build --filter=@repo/web` from repo root so Turborepo builds the dependency first. Plan's verify command uses the direct path; adjusted to turbo invocation.

## User Setup Required

None - no external service configuration required. Banner appears automatically for first-time visitors; posthog.init() requires `NEXT_PUBLIC_POSTHOG_KEY` to be set in `.env.local` for analytics to actually send data.

## Next Phase Readiness

- GDPR-03 cookie consent complete. Plan 04 (delete account modal / Dialog component) can proceed independently.
- PostHog is now fully consent-gated — no analytics fire before user acceptance.

---

_Phase: 21-gdpr-baseline_
_Completed: 2026-03-12_
