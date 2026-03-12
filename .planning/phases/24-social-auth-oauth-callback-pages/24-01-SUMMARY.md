---
phase: 24-social-auth-oauth-callback-pages
plan: 01
subsystem: auth
tags: [oauth, next-js, react, social-auth, vitest, react-testing-library]

# Dependency graph
requires:
  - phase: 20-social-auth
    provides: useAuth hook with refetch, SocialButtons with callback_url='/auth/callback'
provides:
  - OAuth callback page at /auth/callback that completes the Google/GitHub OAuth web flow
  - Unit tests (4) covering loading state, refetch call, dashboard redirect, error redirect
affects:
  - 24-02 (error page that /auth/error?error=unknown redirects to)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - OAuth callback pattern: useEffect fires refetch() on mount, redirects based on result.data presence
    - router.replace (not push) on callback pages to prevent back-navigation into loading state

key-files:
  created:
    - apps/web/app/(auth)/callback/page.tsx
    - apps/web/src/__tests__/app/(auth)/callback.test.tsx
  modified: []

key-decisions:
  - "callback page evaluates result.data from refetch() Promise (not reactive hook state) to avoid initial-render false-negative"
  - "router.replace used instead of router.push — prevents user back-navigating into the loading page after OAuth completion"
  - "No AuthCard wrapper — callback page is loading-only, not an interactive auth form"
  - "Test import path is ../../../../app/(auth)/callback/page (4 levels up) — app/ sits at apps/web root, not under src/"

patterns-established:
  - "OAuth callback pattern: client component + useEffect + refetch().then(redirect) — avoids stale reactive state"

requirements-completed:
  - SOCIAL-01

# Metrics
duration: 4min
completed: 2026-03-12
---

# Phase 24 Plan 01: OAuth Callback Page Summary

**Missing `/auth/callback` page added as client component: calls `useAuth().refetch()` on mount, redirects to `/dashboard` on success or `/auth/error?error=unknown` on no session**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-12T23:27:50Z
- **Completed:** 2026-03-12T23:31:00Z
- **Tasks:** 2 (TDD: RED + GREEN)
- **Files modified:** 2

## Accomplishments

- Created `apps/web/app/(auth)/callback/page.tsx` — fixes the 404 that broke all Google/GitHub OAuth flows
- Four unit tests covering: loading state, refetch call, dashboard redirect, error redirect
- Full web test suite passes (13 tests across 4 test files)

## Task Commits

Each task was committed atomically:

1. **Task 1: Failing tests for OAuth callback page (RED)** - `1043dc8` (test) — committed alongside pre-staged error.test.tsx
2. **Task 2: Implement OAuth callback page (GREEN)** - `1c1f604` (feat)

_Note: TDD tasks — RED commit before GREEN. Path auto-fix applied inline during GREEN task._

## Files Created/Modified

- `apps/web/app/(auth)/callback/page.tsx` - Client component handling OAuth post-redirect session resolution
- `apps/web/src/__tests__/app/(auth)/callback.test.tsx` - 4 unit tests covering all SOCIAL-01 callback behaviors

## Decisions Made

- Used `result.data` from the refetch Promise rather than reactive `isAuthenticated` state — avoids false-negative on initial render before hydration
- `router.replace` ensures the loading page is not added to browser history (user pressing back goes to OAuth provider, not callback loop)
- No `AuthCard` wrapper — callback is a transient loading state, not an interactive form page

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected import path in test file**

- **Found during:** Task 2 (GREEN — running tests after creating page)
- **Issue:** Plan specified `../../../app/(auth)/callback/page` but `app/` is at `apps/web/app/`, not under `apps/web/src/`. Test file at `src/__tests__/app/(auth)/` needs 4 levels up, not 3.
- **Fix:** Changed import to `../../../../app/(auth)/callback/page`
- **Files modified:** `apps/web/src/__tests__/app/(auth)/callback.test.tsx`
- **Verification:** All 4 tests pass after fix
- **Committed in:** `1c1f604` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - import path bug)
**Impact on plan:** Necessary fix for tests to resolve the component. No scope creep.

## Issues Encountered

- Pre-existing `error.test.tsx` was staged alongside `callback.test.tsx` in the RED commit — both files landed in `1043dc8`. The error test belonged to plan 24-02 and was already written. This did not affect callback test correctness.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `/auth/callback` page is live and handles all Google/GitHub OAuth redirects correctly
- Prerequisite for plan 24-02: `/auth/error` page (handles `/auth/error?error=unknown` redirect target)
- No blockers for 24-02

## Self-Check: PASSED

All files and commits verified:

- `apps/web/app/(auth)/callback/page.tsx` — FOUND
- `apps/web/src/__tests__/app/(auth)/callback.test.tsx` — FOUND
- `24-01-SUMMARY.md` — FOUND
- Commit `1043dc8` (test) — FOUND
- Commit `1c1f604` (feat) — FOUND

---

_Phase: 24-social-auth-oauth-callback-pages_
_Completed: 2026-03-12_
