---
phase: 20-social-auth
plan: "04"
subsystem: auth
tags: [social-auth, oauth, google, github, nextjs, shadcn, allauth]

# Dependency graph
requires:
  - phase: 20-02
    provides: Django allauth social account providers configured (Google, GitHub, Apple)
provides:
  - SocialButtons React component with conditional Google + GitHub buttons
  - Login page wired with SocialButtons below email/password form
  - Signup page wired with SocialButtons below signup form
  - Social auth credential env vars documented in apps/api/.env.example
  - Next.js public env var flags documented in apps/web/.env.example
affects:
  - 20-05
  - future scaffolder tasks (SOCIAL AUTH MODULE sentinel comments)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Conditional rendering via NEXT_PUBLIC env vars evaluated at module scope
    - allauth headless browser OAuth redirect via POST to /api/v1/auth/browser/v1/auth/provider/redirect
    - CSRF token read from csrftoken cookie (consistent with use-auth.ts pattern)
    - SOCIAL AUTH MODULE sentinel comments for scaffolder removal detection

key-files:
  created:
    - apps/web/src/components/auth/social-buttons.tsx
  modified:
    - apps/web/app/(auth)/page.tsx
    - apps/web/app/(auth)/signup/page.tsx
    - apps/api/.env.example
    - apps/web/.env.example

key-decisions:
  - "NEXT_PUBLIC env var flags (NEXT_PUBLIC_GOOGLE_ENABLED, NEXT_PUBLIC_GITHUB_ENABLED) gate button rendering — evaluated at module scope so tree-shaking works correctly"
  - "SocialButtons renders null (not empty fragment) when no providers enabled — no orphan divider rendered"
  - "Apple Sign In intentionally absent from web UI — iOS-only per SOCIAL-03 design; Apple vars are in .env.example for backend only"
  - "SOCIAL AUTH MODULE sentinel comment on first line of social-buttons.tsx enables scaffolder removeModule() regex detection"

patterns-established:
  - "Provider redirect pattern: POST to allauth headless endpoint, read data.location, redirect window"
  - "CSRF in social buttons: inline cookie parse (same pattern as use-auth.ts)"

requirements-completed: [SOCIAL-01, SOCIAL-02]

# Metrics
duration: 3min
completed: 2026-03-12
---

# Phase 20 Plan 04: Social Auth Web UI Summary

**Conditional Google + GitHub social login buttons wired into web login and signup pages via allauth headless OAuth redirect, with .env.example documentation for all six social credential vars.**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-12T12:17:36Z
- **Completed:** 2026-03-12T12:20:34Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Created `SocialButtons` component that conditionally renders Google and GitHub buttons based on `NEXT_PUBLIC_*` env flags, rendering null when neither is enabled
- Wired `SocialButtons` into both the login page (`apps/web/app/(auth)/page.tsx`) and signup page (`apps/web/app/(auth)/signup/page.tsx`) below the respective forms
- Documented all six social credential vars (Google, GitHub, Apple) in `apps/api/.env.example` with setup console URLs and comments
- Added `NEXT_PUBLIC_GOOGLE_ENABLED` and `NEXT_PUBLIC_GITHUB_ENABLED` to `apps/web/.env.example`

## Task Commits

1. **Task 1: SocialButtons component** - `03ac278` (feat)
2. **Task 2: Wire into pages + .env.example** - `623b328` (feat)

## Files Created/Modified

- `apps/web/src/components/auth/social-buttons.tsx` - New component: conditional Google + GitHub buttons, allauth provider redirect, CSRF, sonner error toast
- `apps/web/app/(auth)/page.tsx` - Added SocialButtons import and render below login form
- `apps/web/app/(auth)/signup/page.tsx` - Added SocialButtons import and render below signup form
- `apps/api/.env.example` - Added Social Auth section with Google, GitHub, Apple credential vars + NEXT_PUBLIC flag comments
- `apps/web/.env.example` - Added NEXT_PUBLIC_GOOGLE_ENABLED and NEXT_PUBLIC_GITHUB_ENABLED placeholder vars

## Decisions Made

- `NEXT_PUBLIC_GOOGLE_ENABLED` / `NEXT_PUBLIC_GITHUB_ENABLED` evaluated at module scope (not inside render) so Next.js static analysis can tree-shake unused code
- `SocialButtons` returns `null` (not empty JSX) when neither provider is enabled — prevents an orphan "Or continue with" divider from appearing
- Apple Sign In button intentionally absent from web pages — iOS-only by design (SOCIAL-03 routes through a native token endpoint, not browser OAuth)
- `SOCIAL AUTH MODULE` sentinel comment on line 1 of `social-buttons.tsx` follows existing module sentinel pattern (`BILLING MODULE`, `EMAIL MODULE`) for scaffolder `removeModule()` regex detection

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Pre-existing TypeScript build error in `apps/web/app/(auth)/page.tsx` line 52 (`login.mutateAsync` type mismatch) unrelated to this plan's changes. Verified pre-existing by stashing changes and re-running tsc. Not in scope to fix.

## User Setup Required

To enable social login buttons in the web app:

1. Configure OAuth credentials in apps/api/.env (see `apps/api/.env.example` Social Auth section)
2. Set `NEXT_PUBLIC_GOOGLE_ENABLED=true` and/or `NEXT_PUBLIC_GITHUB_ENABLED=true` in `apps/web/.env.local`

## Next Phase Readiness

- Social buttons component ready for 20-05 (OAuth callback handler)
- All social credential env vars documented and ready for developer setup
- No blockers

---

_Phase: 20-social-auth_
_Completed: 2026-03-12_
