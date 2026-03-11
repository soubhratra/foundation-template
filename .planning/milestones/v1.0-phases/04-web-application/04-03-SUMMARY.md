---
phase: 04-web-application
plan: 03
subsystem: ui
tags: [nextjs, auth, middleware, react-query]

# Dependency graph
requires:
  - phase: 04-01
    provides: Base URL helpers and shared request utilities for the web app
  - phase: 04-02
    provides: AuthProvider + React Query wiring that powers useAuth hooks
provides:
  - Session-aware proxy guard plus validateSession server helper
  - Skeleton loaders and wrappers for /(auth) and /(dashboard) route groups
  - Session toast + redirect plumbing when API tokens expire
affects: [web-login, dashboard, middleware]

# Tech tracking
tech-stack:
  added: ["@repo/api-client (declared in @repo/web)"]
  patterns:
    [
      "Next.js proxy guard with safe redirect builder",
      "Skeleton-first hydration via client wrappers",
      "Global session-expiry toast hook",
    ]

key-files:
  created:
    - apps/web/app/proxy.ts
    - apps/web/src/lib/auth/server.ts
    - apps/web/src/hooks/use-session-toast.ts
    - apps/web/src/components/skeletons/auth-skeleton.tsx
    - apps/web/src/components/skeletons/dashboard-skeleton.tsx
  modified:
    - apps/web/app/(auth)/layout.tsx
    - apps/web/app/(dashboard)/layout.tsx
    - apps/web/app/providers.tsx
    - apps/web/app/layout.tsx
    - pnpm-lock.yaml

key-decisions:
  - "Proxy guard enforces redirects centrally so layouts and pages stay session-agnostic."
  - "`sessionExpired=1` query flag plus shared hook drive toast messaging to avoid duplicating UI state."

patterns-established:
  - "Skeleton wrappers decide between fallback and layout children, removing flicker on protected routes."
  - "React Query 401/403 states funnel through one hook that clears storage, shows toast, and reroutes."

# Metrics
duration: 12 min
completed: 2026-02-16
---

# Phase 04 Plan 03: Session Redirect + Skeletons Summary

**Session-aware proxy, shared skeleton loaders, and global session-expiry toasts keep protected routes flicker-free and redirect on auth loss.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-02-16T12:37:34Z
- **Completed:** 2026-02-16T12:50:22Z
- **Tasks:** 3
- **Files modified:** 16

## Accomplishments

- Added `validateSession` helpers plus `app/proxy.ts` so hitting `/dashboard` without cookies returns an immediate `/login?redirect=...` 307 generated before layouts render.
- Delivered reusable auth and dashboard skeleton components, client wrappers, and `loading.tsx` files so both route groups render placeholders while the session state resolves.
- Introduced `useSessionToast` + AppProviders wiring to clear tokens, show a toast, and redirect with `sessionExpired=1` whenever React Query reports 401/403.
- Manual reasoning verified the proxy preserves query strings, wrappers gate layout hydration, and the toast hook only fires after a previously-authenticated session expires.

## Task Commits

1. **Task 1: Build server-side auth helpers and proxy guard** - `08f9437` (feat)
2. **Task 2: Add loading skeletons for /(auth) and /(dashboard)** - `e3c68ca` (feat)
3. **Task 3: Detect session expiry and show toast + redirect** - `13a774b` (feat)

**Plan metadata:** docs commit pending (`docs(04-03): complete plan`)

## Files Created/Modified

- `apps/web/app/proxy.ts` - Central proxy enforcing session redirects before route handlers run
- `apps/web/src/lib/auth/server.ts` - validateSession + buildRedirectUrl helpers for proxy
- `apps/web/app/(auth)/loading.tsx` and `apps/web/app/(dashboard)/loading.tsx` - Skeleton-based loaders mirroring final layouts
- `apps/web/src/components/skeletons/*` & shell clients - Shared skeletons and wrappers used by layouts
- `apps/web/src/hooks/use-session-toast.ts` & `app/providers.tsx` - Global toast + redirect plumbing on expired sessions

## Decisions Made

- Proxy guard performs all redirect logic centrally so future routes do not rely on ad-hoc `useEffect` checks.
- The `sessionExpired=1` search param doubles as the UX signal for login/signup while keeping redirect targets sanitized through shared helpers.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added @repo/api-client dependency to @repo/web**

- **Found during:** Task 1 (proxy + helpers)
- **Issue:** The web workspace was not declaring `@repo/api-client`, causing TypeScript resolution failures for the mandated helper usage.
- **Fix:** Declared the dependency in `apps/web/package.json` and re-synced `pnpm-lock.yaml` via `pnpm install` so the client code can import the SDK.
- **Files modified:** apps/web/package.json, pnpm-lock.yaml
- **Verification:** `pnpm --filter web type-check`
- **Committed in:** 08f9437

**Total deviations:** 1 auto-fixed (blocking). **Impact on plan:** Required to satisfy the plan's `@repo/api-client` contract; no scope creep beyond dependency declaration.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Protected dashboards now rely on proxy-enforced redirects and skeleton-first layouts, so upcoming dashboard feature work can assume safe hydration.
- Session-expiry toasts and redirect plumbing are centralized, enabling future auth flows (e.g., refresh or logout) to hook into the same UX affordances.

## Self-Check: PASSED
