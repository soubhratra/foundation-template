---
phase: 05-mobile-application
plan: 02
subsystem: mobile
tags: [expo, auth, react-hook-form]

# Dependency graph
requires:
  - phase: 05-01
    provides: Auth/tab navigator scaffolding
provides:
  - Shared Expo auth shell + form/footer primitives
  - JWT sign-in, signup, and password reset screens hitting Django
affects: [apps/mobile, packages/business-logic]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - AuthShell/AuthFooter standardize Expo auth layouts and nav links
    - Mobile auth forms use shared validation schemas + RHF controllers

key-files:
  created:
    - apps/mobile/app/(auth)/reset-password.tsx
    - apps/mobile/lib/api/auth.ts
  modified:
    - apps/mobile/components/auth/auth-shell.tsx
    - apps/mobile/components/auth/auth-form.tsx
    - apps/mobile/components/auth/auth-footer.tsx
    - apps/mobile/app/(auth)/_layout.tsx
    - apps/mobile/app/(auth)/sign-in.tsx
    - apps/mobile/app/(auth)/sign-up.tsx

key-decisions:
  - "Called Allauth account/reset endpoints through the existing business-logic client while OpenAPI lacks those paths."

patterns-established:
  - "AuthFooter anchors all auth screens with declarative expo-router links."
  - "Status banners flow through AuthMessage so success/error copy stays consistent."

# Metrics
duration: 8 min
completed: 2026-02-16
---

# Phase 05 Plan 02: Mobile Auth Screens Summary

**Mobile auth shell plus sign-in/signup/reset screens now reuse shared validation, @repo/business-logic, and Expo Router navigation.**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-16T21:20:32Z
- **Completed:** 2026-02-16T21:28:46Z
- **Tasks:** 3
- **Files modified:** 9

## Accomplishments
- Built AuthShell, AuthForm, and AuthFooter primitives and updated the auth layout so every screen inherits the same SafeArea, typography, and status banners.
- Replaced the placeholder sign-in view with a validated form that calls `useAuth().loginWithJwt`, supports remember toggles, and reuses shared footers (lint + type-check both run).
- Added API mutation helpers plus fully wired signup and password-reset screens that surface success/error states and route back to sign-in.

## Task Commits

Each task was committed atomically:

1. **Task 1: Build shared auth shell + form primitives** - `4b9e603` (feat)
2. **Task 2: Implement sign-in screen with shared validation + useAuth** - `d631a72` (feat)
3. **Task 3: Implement signup + reset flows hitting Django endpoints** - `6b482ea` (feat)

## Files Created/Modified
- `apps/mobile/components/auth/auth-shell.tsx` - SafeArea auth wrapper with reusable success/error banners.
- `apps/mobile/components/auth/auth-form.tsx` - React Hook Form + @repo/ui bridge with field helper, status messaging, and footer slot.
- `apps/mobile/components/auth/auth-footer.tsx` / `index.ts` - Declarative expo-router link list shared by auth screens.
- `apps/mobile/app/(auth)/_layout.tsx` - Layout now composes AuthShell so child screens stay minimal.
- `apps/mobile/app/(auth)/sign-in.tsx` - Production login form calling `useAuth().loginWithJwt` and honoring email prefill params.
- `apps/mobile/app/(auth)/sign-up.tsx` - Signup form with marketing toggle, success CTA, and navigation links.
- `apps/mobile/app/(auth)/reset-password.tsx` - Password reset form with optional redirect hint and success messaging.
- `apps/mobile/lib/api/auth.ts` - Mutation helpers that proxy Allauth account/reset calls through the business-logic client.

## Decisions Made
- Reused the business-logic client's fetch pipeline (cast to a generic client) for account/reset endpoints until the OpenAPI generator includes those paths; this keeps auth headers/versioning consistent.
- Surfaced footer CTAs (AuthFooter + optional outline button) through AuthForm's footer slot so new auth screens inherit navigation affordances automatically.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] OpenAPI schema lacks Allauth account/reset paths**
- **Found during:** Task 3 (signup + reset flows)
- **Issue:** The generated `@repo/api-client` `paths` interface only exposes `/users/me` and health endpoints, so TypeScript rejected POSTs to `/api/v1/auth/account/` and `/api/v1/auth/password/reset/`.
- **Fix:** Routed those requests through the existing `AuthProvider` client cast to a generic interface, typed payloads/responses with the shared Zod schemas, and kept centralized error normalization.
- **Verification:** `pnpm --filter @repo/mobile type-check` + `pnpm --filter @repo/mobile lint`
- **Committed in:** 6b482ea

**Total deviations:** 1 auto-fixed (blocking)
**Impact on plan:** Allowed auth forms to ship while retaining strongly-typed inputs; no scope creep beyond typed helper shim.

## Issues Encountered
- None – linting and type-checking both succeeded, and a dedicated mobile test script does not exist yet, so verification relied on lint/type passes per plan guidance.

## User Setup Required
None - no external configuration needed.

## Next Phase Readiness
- Expo auth stack now mirrors the web experience and calls the real Django endpoints, so Phase 05-03 can focus on SecureStore token management without re-doing UI work.

## Self-Check: PASSED
