---
phase: 24-social-auth-oauth-callback-pages
plan: "02"
subsystem: auth
tags: [oauth, allauth, next-js, react, error-handling, tdd, vitest]

# Dependency graph
requires:
  - phase: 24-social-auth-oauth-callback-pages-plan-01
    provides: "(auth)/callback page for successful OAuth redirects"
provides:
  - OAuth error display page at /auth/error mapping allauth error codes to human-readable messages
  - Back-to-sign-in link for error recovery
  - Unit tests covering SOCIAL-02 error page rendering (5 tests)
affects: [social-auth, allauth-integration, auth-ux]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Error code lookup table pattern: Record<string, string> with fallback to 'unknown' key"
    - "Vitest alias layering: specific @/app/* alias before generic @/* alias for Next.js app dir resolution"

key-files:
  created:
    - apps/web/app/(auth)/error/page.tsx
    - apps/web/src/__tests__/app/(auth)/error.test.tsx
  modified:
    - apps/web/vitest.config.ts

key-decisions:
  - "Vitest alias updated to map @/app/* -> ./app/* before @/* -> ./src/* — Next.js app/ dir is outside src/, so tests importing @/app/... require a specific alias prefix match"
  - "ERROR_MESSAGES Record<string, string> with fallback via ?? operator — simpler than switch/case, easy to extend with new allauth error codes"
  - "Raw error code shown in <code> element for debugging — helps triage provider-specific failures in production"

patterns-established:
  - "TDD RED-GREEN for auth pages: write failing test importing non-existent component first, then implement"
  - "AuthCard + AuthLinks composition: eyebrow/title/description + footer with back-link is the standard auth error page pattern"

requirements-completed: [SOCIAL-02]

# Metrics
duration: 4min
completed: 2026-03-12
---

# Phase 24 Plan 02: OAuth Error Page Summary

**Client-side OAuth error page at /auth/error mapping all six allauth error codes to human-readable messages with TDD test coverage**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-03-12T23:28:12Z
- **Completed:** 2026-03-12T23:32:00Z
- **Tasks:** 2 (TDD RED + GREEN)
- **Files modified:** 3

## Accomplishments

- OAuth error page renders allauth error codes (cancelled, unknown, denied, reauthentication_required, signup_closed, permission_denied) as user-friendly messages
- Falls back to "unknown" message for any unrecognised error code
- Back-to-sign-in link (href="/") in footer for error recovery
- Five unit tests all passing (SOCIAL-02 covered)
- vitest.config.ts alias fix enables importing Next.js app-directory components from tests

## Task Commits

Each task was committed atomically:

1. **Task 1: Write failing tests for OAuth error page (RED)** - `1043dc8` (test)
2. **Task 2: Implement OAuth error page and turn tests GREEN** - `113ea90` (feat)

**Plan metadata:** _(pending docs commit)_

_Note: TDD tasks committed as separate RED and GREEN commits_

## Files Created/Modified

- `apps/web/app/(auth)/error/page.tsx` — "use client" OAuth error display page, reads `?error=` param, maps to human-readable string, renders AuthCard with back-to-sign-in footer
- `apps/web/src/__tests__/app/(auth)/error.test.tsx` — 5 unit tests covering cancelled/unknown/denied messages, back-to-sign-in link, and unknown fallback
- `apps/web/vitest.config.ts` — Added `@/app/*` → `./app/*` alias before `@/*` → `./src/*` to support importing Next.js app-directory files in tests

## Decisions Made

- **Vitest alias layering (Rule 3 auto-fix):** `@` maps to `./src` in tsconfig, but the error page lives at `./app/`. Added a more-specific `@/app/*` alias in vitest.config.ts that takes precedence over the general `@` alias. This is the minimal fix — no test import changes needed.
- **Record lookup over switch/case:** `ERROR_MESSAGES[code] ?? ERROR_MESSAGES.unknown` is the idiomatic TypeScript pattern. Easier to extend when allauth adds error codes.
- **Raw error code displayed:** `<code>{errorCode}</code>` in component body helps diagnose provider-specific failures without needing server logs.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Updated vitest.config.ts alias to resolve @/app/\* imports**

- **Found during:** Task 2 (implement OAuth error page)
- **Issue:** vitest `@` alias maps to `./src`, but the component lives in `./app/` (Next.js app directory outside src/). Test import `@/app/(auth)/error/page` failed to resolve.
- **Fix:** Added `{ find: /^@\/app(.*)/, replacement: path.resolve(__dirname, './app') + '$1' }` as the first alias entry, before the general `@` → `./src` alias.
- **Files modified:** `apps/web/vitest.config.ts`
- **Verification:** `pnpm --filter @repo/web test -- error` passes all 5 tests; `pnpm --filter @repo/web test` passes all 13 tests
- **Committed in:** `113ea90` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (blocking)
**Impact on plan:** Auto-fix necessary for test resolution. No scope creep — the component location (./app/) is correct for Next.js; the vitest config was the only thing that needed updating.

## Issues Encountered

None — implementation matched plan exactly once the alias was fixed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- SOCIAL-01 (callback page) and SOCIAL-02 (error page) both complete
- All allauth OAuth redirect URLs now have matching frontend pages
- Phase 24 plan complete — social auth OAuth callback pages are production-ready

---

_Phase: 24-social-auth-oauth-callback-pages_
_Completed: 2026-03-12_
