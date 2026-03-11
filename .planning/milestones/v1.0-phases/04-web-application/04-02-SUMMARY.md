---
phase: 04-web-application
plan: 02
subsystem: ui
tags: [nextjs, auth, react-hook-form]

# Dependency graph
requires:
  - phase: 04-web-application-04-01
    provides: shadcn layouts + marketing hero shell for auth pages
provides:
  - Shared AuthCard/AuthForm toolkit plus sanitized redirect helper
  - Login, signup, reset, and verify-email routes backed by headless auth endpoints
affects: [web-auth, onboarding, route-guards]

# Tech tracking
tech-stack:
  added: []
  patterns: [auth-form toolkit, csrf-aware request helper, redirect-target hook]

key-files:
  created:
    - apps/web/src/components/auth/auth-card.tsx
    - apps/web/src/components/auth/auth-form.tsx
    - apps/web/src/components/auth/auth-links.tsx
    - apps/web/src/hooks/use-redirect-target.ts
    - apps/web/src/lib/request.ts
    - apps/web/app/(auth)/signup/page.tsx
    - apps/web/app/(auth)/reset/page.tsx
    - apps/web/app/(auth)/verify-email/page.tsx
  modified:
    - apps/web/app/(auth)/layout.tsx
    - apps/web/app/(auth)/page.tsx
    - packages/validation/src/auth.ts

key-decisions:
  - "Centralized a CSRF-aware `postJson` helper so every auth mutation consistently hits Django headless endpoints."
  - "Extended @repo/validation with `emailVerificationSchema` to keep verify-email flows aligned with shared form schemas."

patterns-established:
  - "AuthCard/AuthForm pair standardizes RHF + shadcn wiring, inline alerts, and footer links across auth surfaces."
  - "`useRedirectTarget` hook sanitizes query/cookie redirect hints before navigating after login."

# Metrics
duration: 9min
completed: 2026-02-16
---

# Phase 04 Plan 02: Auth Flows Summary

**Reusable auth form toolkit powering login, signup, reset, and verify-email flows with redirect + CSRF safety**

## Performance

- **Duration:** 9 min
- **Started:** 2026-02-16T12:25:52Z
- **Completed:** 2026-02-16T12:34:30Z
- **Tasks:** 3
- **Files modified:** 12

## Accomplishments

- Created AuthCard/AuthForm/AuthLinks components plus `useRedirectTarget` so every auth screen shares consistent RHF, shadcn, and redirect handling.
- Rebuilt the login route to honor sanitized redirect parameters, surface verification hints when accounts are unconfirmed, and disable inputs while mutations run.
- Implemented signup, reset, and verify-email pages that post to the Django headless endpoints via the CSRF-aware helper and shared validation schemas.

## Task Commits

Each task was committed atomically:

1. **Task 1: Create shared auth form components and helpers** - `f08ef97` (feat)
2. **Task 2: Implement login page with redirect-aware session login** - `80650ff` (feat)
3. **Task 3: Build signup, reset, and verify-email pages** - `1a4c4a6` (feat)

**Plan metadata:** _(included in final docs commit)_

## Files Created/Modified

- `apps/web/src/components/auth/auth-card.tsx` - Card wrapper with reusable auth headings and footers.
- `apps/web/src/components/auth/auth-form.tsx` - RHF-aware form shell that renders inline alerts and disabled states.
- `apps/web/src/hooks/use-redirect-target.ts` - Hook that resolves redirect hints from query/cookies and sanitizes them.
- `apps/web/src/lib/request.ts` - CSRF-aware fetch helper for Django headless endpoints.
- `apps/web/app/(auth)/page.tsx` - Redirect-aware login form with verification hints and shared components.
- `apps/web/app/(auth)/signup/page.tsx` - Signup form posting to `/api/v1/auth/account/` with marketing opt-in support.
- `apps/web/app/(auth)/reset/page.tsx` - Password reset request UI calling the Allauth endpoint.
- `apps/web/app/(auth)/verify-email/page.tsx` - Key entry page that confirms email and links back to login.
- `packages/validation/src/auth.ts` - Added `emailVerificationSchema` so verify-email uses shared validation.

## Decisions Made

- Introduced a dedicated `postJson` helper to guarantee CSRF tokens and credentialed fetch requests for all auth mutations, avoiding duplicated header logic in each page.
- Added `emailVerificationSchema` / `EmailVerificationInput` to @repo/validation so every auth route (including verify-email) relies on the shared schema package instead of ad-hoc validators.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Auth flows now hit live endpoints with consistent UX, so Phase 04-03 can focus on proxy guards, skeleton handoffs, and session-expired toasts using the same toolkit without reworking forms.

## Self-Check: PASSED

- Verified key files exist on disk.
- Confirmed task commits `f08ef97`, `80650ff`, and `1a4c4a6` are present in git history.
