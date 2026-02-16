---
phase: 04-web-application
plan: 05
subsystem: ui
tags: [nextjs, server-actions, api-client]
requires:
  - phase: 04-04
    provides: "Dashboard shell + profile/settings UI awaiting live data"
provides:
  - Server-side api helper that forwards session + CSRF cookies to Django
  - Dashboard/profile/settings pages reading real data via server components
  - Server actions for profile updates, notification prefs, and password changes
affects: [04-web-application, 05-mobile-auth]
tech-stack:
  added: []
  patterns:
    - "Server actions invoked from client islands after server components fetch data"
    - "Notification preferences persisted in cookies until dedicated API endpoints exist"
key-files:
  created:
    - apps/web/src/lib/api/server.ts
    - apps/web/src/actions/profile-actions.ts
    - apps/web/app/(dashboard)/profile/profile-client.tsx
    - apps/web/app/(dashboard)/settings/settings-client.tsx
  modified:
    - apps/web/app/(dashboard)/dashboard/page.tsx
    - apps/web/app/(dashboard)/profile/page.tsx
    - apps/web/app/(dashboard)/settings/page.tsx
    - apps/web/src/components/dashboard/account-form.tsx
key-decisions:
  - "Persist notification and alert preferences in signed cookies because the backend has not published preference endpoints yet."
  - "Use shared server actions for Django Allauth password changes to avoid duplicating request logic in client components."
patterns-established:
  - "Server components call getServerApi() for cookie-aware data fetching before rendering client widgets."
  - "Client-side React Hook Form components return ActionFormResult objects so server-action errors map cleanly to inputs."
duration: 13 min
completed: 2026-02-16
---

# Phase 04 Plan 05: Server Actions Dashboard Wiring

**Server-side api helper plus dashboard/profile/settings server actions now read and update real Django data**

## Performance

- **Duration:** 13 min
- **Started:** 2026-02-16T13:06:26Z
- **Completed:** 2026-02-16T13:19:35Z
- **Tasks:** 3
- **Files modified:** 10

## Accomplishments
- Added `getServerApi()` so server components forward session + CSRF cookies to the Django API without duplicating fetch logic.
- Refreshed `/dashboard` to stream actual `/api/v1/users/me` + health data, with graceful fallback alerts when the API is unreachable.
- Rebuilt `/profile` and `/settings` as server components backed by server actions for profile edits, notification toggles, and password changes.

## Task Commits

Each task was committed atomically:

1. **Task 1: Create server-side api-client utilities** - `9267fb6` (feat)
2. **Task 2: Fetch real data for dashboard + activity pages** - `6a0e8ff` (feat)
3. **Task 3: Wire profile + settings forms to server actions** - `37df591` (feat)

**Plan metadata:** _pending_ (docs commit after summary/state updates)

## Files Created/Modified
- `apps/web/src/lib/api/server.ts` - Server-side helper returning cookie-aware api client + typed helpers.
- `apps/web/app/(dashboard)/dashboard/page.tsx` - Async server component pulling current user + health data with fallback alerts.
- `apps/web/src/actions/profile-actions.ts` - Server actions for profile updates, notification prefs, and password changes.
- `apps/web/app/(dashboard)/profile/*` - Server wrapper + client component that invoke server actions and refresh AuthProvider cache.
- `apps/web/app/(dashboard)/settings/*` - Server/client pair wiring password + notification forms to server actions.
- `apps/web/src/components/dashboard/account-form.tsx` - Supports ActionFormResult responses to map server errors onto RHF inputs.

## Decisions Made
- Persist notification and alert preferences in cookies because Django has not shipped preference endpoints yet; keeps UI state consistent across reloads without blocking on backend work.
- Reuse Django Allauth password-change endpoint via server action to avoid duplicating CSRF handling in client components.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Cookie-based notification persistence**
- **Found during:** Task 3 (Wire profile + settings forms)
- **Issue:** The plan expected notification forms to PATCH dedicated API endpoints, but the backend only exposes `/api/v1/users/me` + Allauth routes, leaving preferences with no persistence path.
- **Fix:** Stored channel/alert preferences in signed cookies via server actions so toggles survive reloads until backend endpoints exist.
- **Files modified:** apps/web/src/actions/profile-actions.ts, apps/web/app/(dashboard)/profile/profile-client.tsx, apps/web/app/(dashboard)/settings/settings-client.tsx
- **Verification:** Preferences remain selected after refreshing `/profile` and `/settings`.
- **Committed in:** 37df591

**Total deviations:** 1 auto-fixed (1 missing critical). **Impact on plan:** Ensures UX continuity without blocking on new API work.

## Issues Encountered
- Backend lacks preference endpoints, so cookies were used as an interim persistence layer while still centralizing the logic in server actions.

## Manual Smoke Test
1. Run `pnpm --filter web dev` from the repo root.
2. Visit `http://localhost:3000/profile` while authenticated.
3. Update the display name, submit the form, and confirm the new name appears immediately and after refreshing the page.
4. Toggle notification switches, click “Save prefs,” refresh, and verify the toggles retain their saved state.
5. Visit `http://localhost:3000/settings`, change the password fields (use placeholder values), submit, and confirm the success toast plus form reset.

## Next Phase Readiness
- Web dashboard/profile/settings now fetch real data and leverage server actions, so upcoming web plans can focus on additional widgets rather than plumbing.
- Mobile/Auth phases can mirror the new api helper + server action patterns when they need authenticated server calls.

## Self-Check: PASSED
