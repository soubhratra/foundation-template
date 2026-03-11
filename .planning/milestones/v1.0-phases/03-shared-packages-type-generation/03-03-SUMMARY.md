---
phase: 03-shared-packages-type-generation
plan: 03
subsystem: packages
tags: [zod, react-hook-form, tsup, validation]
requires:
  - phase: 02-api-core-auth-backend
    provides: Auth constraints + Allauth field expectations for auth/profile flows
provides:
  - Shared auth/profile Zod schemas exported from @repo/validation
  - React Hook Form helper that wraps zodResolver with typed defaults
affects:
  - 04-web-application
  - 05-mobile-application
tech-stack:
  added:
    - tsup
  patterns:
    - Shared Zod schemas live in @repo/validation for both clients
    - createZodFormOptions centralizes React Hook Form configuration
key-files:
  created:
    - packages/validation/src/forms.ts
    - packages/validation/tsup.config.ts
  modified:
    - packages/validation/package.json
    - packages/validation/src/auth.ts
    - packages/validation/src/profile.ts
    - packages/validation/src/index.ts
    - packages/validation/tsconfig.json
key-decisions:
  - "Deferred pnpm-lock.yaml updates to avoid clobbering staged work from other phase 03 plans"
patterns-established:
  - "Validation schemas stay in a single package with inferred TS types"
  - "React Hook Form + zodResolver wiring uses a helper to keep flows in sync"
duration: 7 min
completed: 2026-02-16
---

# Phase 03 Plan 03: Shared Validation Package Summary

**Shared Zod auth/profile schemas packaged with a reusable React Hook Form resolver helper**

## Performance

- **Duration:** 7 min
- **Started:** 2026-02-16T03:44:01Z
- **Completed:** 2026-02-16T03:51:27Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- Scaffolded `@repo/validation` with login/signup/password/profile Zod schemas plus inferred types for downstream imports.
- Added `createZodFormOptions` + `buildFormDefaults` helpers that wrap `zodResolver` so React Hook Form wiring matches on web and mobile.
- Wired a `tsup` build so the package emits CJS/ESM bundles and `.d.ts` files ready for workspace consumers.

## Task Commits

Each task was committed atomically:

1. **Task 1: Bootstrap @repo/validation schemas** - `e825039` (feat)
2. **Task 2: Add React Hook Form helpers + build pipeline** - `5dc3e38` (feat)

Plan metadata commit will follow after documentation/state updates.

## Files Created/Modified

- `packages/validation/package.json` - defines workspace metadata, scripts, and peer dependency surface for the validation package.
- `packages/validation/tsconfig.json` - points to shared TS config so the package can type-check/build consistently.
- `packages/validation/src/auth.ts` - hosts Zod schemas + inferred types for login, signup, password reset/change flows.
- `packages/validation/src/profile.ts` - models profile + notification preference schemas with defaults.
- `packages/validation/src/index.ts` - re-exports schemas and helpers for package consumers.
- `packages/validation/src/forms.ts` - new helper module for `createZodFormOptions`, `buildFormDefaults`, and field error mapping.
- `packages/validation/tsup.config.ts` - build config emitting ESM/CJS bundles and declarations for the package entry points.

## Decisions Made

- Locked validation logic into `@repo/validation` and exposed helper exports instead of duplicating schema + form wiring in each app.
- Deferred `pnpm-lock.yaml` changes to respect the larger staged changeset for `packages/ui`; a future global install will regenerate the lock once those files are ready to land.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Left pnpm-lock.yaml untouched to avoid overwriting staged work**

- **Found during:** Task 1 (Bootstrap package)
- **Issue:** The lockfile already contained staged edits for other packages. Updating it would have pulled their work into this commit.
- **Fix:** Installed dependencies locally for verification but restored the original lockfile so existing staged work stays intact. Documented the follow-up need for a coordinated lock update.
- **Files modified:** pnpm-lock.yaml (restored to original state)
- **Verification:** `pnpm --filter @repo/validation type-check` & `pnpm --filter @repo/validation build`
- **Committed in:** Not applicable (lockfile intentionally left unchanged)

**Total deviations:** 1 auto-fixed (blocking lockfile coordination)
**Impact on plan:** No scope creep; code changes still match planned deliverables.

## Issues Encountered

- Initial `tsup` declaration build complained about an unconstrained `createFieldErrorMap` reducer type; tightening the guard resolved the DTS build so `pnpm --filter @repo/validation build` now passes.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Web and mobile clients can now import identical auth, password, and profile validation schemas plus a shared React Hook Form helper from `@repo/validation`.
- Ready for Phase 03 Plan 04 (UI primitives) to consume these schemas while routing form submissions through the shared helper.

---

_Phase: 03-shared-packages-type-generation_
_Completed: 2026-02-16_

## Self-Check: PASSED
