---
phase: 20-social-auth
plan: "06"
subsystem: infra
tags: [typescript, cli, scaffolder, social-auth, allauth, create-foundation-app]

# Dependency graph
requires:
  - phase: 20-04
    provides: social auth web UI (SocialButtons component, web login/signup pages)
  - phase: 20-05
    provides: Apple Sign In mobile screen (AppleAuthentication import + button block)
  - phase: 20-01
    provides: remove-social-auth test suite (11 TypeScript unit tests, Python integration test)
provides:
  - removeSocialAuthModule() exported from packages/create-foundation-app/src/remove.ts
  - --without social-auth CLI flag wired in index.ts
  - "social-auth" in SelectedFeatures type and promptFeatures() multiselect
affects: [create-foundation-app, scaffolder, social-auth, new-project-creation]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Two-pass env removal: fenced SOCIAL AUTH MODULE block first, then per-var fallback regex"
    - "Comment-inclusive env removal: tertiary regex removes all lines mentioning the var name (not just assignment lines)"
    - "Optional module removal pattern: sentinel-comment fenced block in config files + force-delete of isolated component files"

key-files:
  created: []
  modified:
    - packages/create-foundation-app/src/remove.ts
    - packages/create-foundation-app/src/prompts.ts
    - packages/create-foundation-app/src/index.ts

key-decisions:
  - "Env removal uses three passes: (1) fenced SOCIAL AUTH MODULE section block, (2) # Social Auth comment lines, (3) per-var regex matching all lines containing the var name — covers both fixture format (simple KEY= lines) and real .env.example format (includes # APPLE_CLIENT_ID = description comments)"
  - "SocialButtons JSX removal regex changed from ^\\s*<SocialButtons\\s*\\/> to ^[^\\n]*<SocialButtons[^>]*\\/>[^\\n]* to also remove lines like 'return <SocialButtons />;' where JSX appears inline"

patterns-established:
  - "Env removal for real template files must handle comment-form references (# VAR = description) not only assignment lines (VAR=)"

requirements-completed: [SOCIAL-05]

# Metrics
duration: 8min
completed: 2026-03-12
---

# Phase 20 Plan 06: Social Auth CLI Scaffolder Summary

**removeSocialAuthModule() implemented in create-foundation-app CLI — 11 unit tests + integration test GREEN, --without social-auth flag wired, social-auth added to promptFeatures() with default-on selection**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-12T12:22:00Z
- **Completed:** 2026-03-12T12:30:35Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Implemented `removeSocialAuthModule()` in `remove.ts` — cleans base.py (SOCIAL AUTH MODULE fenced block + sentinel lines + unconditional allauth.socialaccount removal), deletes social-buttons.tsx, strips social credential env vars from .env.example, removes SocialButtons from web login/signup pages, removes Apple Sign In import/element from mobile sign-in screen
- Wired `--without social-auth` / `--without-social-auth` CLI flag in `index.ts` with proper feature filter and removal call
- Added `"social-auth"` to `SelectedFeatures` union type and `promptFeatures()` multiselect (selected by default) in `prompts.ts`
- All 11 TypeScript unit tests GREEN; Python integration test `test_scaffolder_social_removal.py` GREEN; full phase suite (19 tests) GREEN

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement removeSocialAuthModule() GREEN** - `4f6b94d` (feat)
2. **Task 2: Wire --without social-auth flag in prompts.ts and index.ts** - `f8bd1ac` (feat)

## Files Created/Modified

- `packages/create-foundation-app/src/remove.ts` - Added `removeSocialAuthModule()` function (145 lines)
- `packages/create-foundation-app/src/prompts.ts` - Extended `SelectedFeatures` type, added social-auth option with default-on
- `packages/create-foundation-app/src/index.ts` - Added `withoutSocialAuthFlag` parsing, feature filter, `removeSocialAuthModule()` call

## Decisions Made

- Env removal uses three-pass strategy: fenced block regex first, then comment-line regex, then per-var regex covering all line forms — required because the real `.env.example` has `# APPLE_CLIENT_ID = iOS App Bundle ID` comment lines alongside `APPLE_CLIENT_ID=` assignment lines
- SocialButtons JSX removal uses broad pattern `^[^\n]*<SocialButtons[^>]*\/>[^\n]*` rather than leading-whitespace-only pattern, to catch `return <SocialButtons />;` inline patterns

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed env removal regex to also remove comment-form references**

- **Found during:** Task 2 (integration test execution)
- **Issue:** The per-var regex `^APPLE_CLIENT_ID=.*$` only matched assignment lines. The real `.env.example` has `# APPLE_CLIENT_ID = iOS App Bundle ID (e.g., com.yourapp.app)` as a documentation comment, which survived removal and caused the integration test assertion `"APPLE_CLIENT_ID" not in env_content` to fail.
- **Fix:** Added tertiary pass using `^[^\n]*${varName}[^\n]*\n?` pattern that removes all lines containing the var name (assignments and comment references). Added primary fenced-block regex for the real .env.example section structure.
- **Files modified:** `packages/create-foundation-app/src/remove.ts`
- **Verification:** Integration test `test_scaffolder_social_removal.py` passes GREEN; unit tests still 11/11 GREEN
- **Committed in:** `f8bd1ac` (Task 2 commit)

**2. [Rule 1 - Bug] Fixed SocialButtons JSX removal regex to match inline return statements**

- **Found during:** Task 1 (unit test execution)
- **Issue:** Regex `^\s*<SocialButtons\s*\/>\s*\n?` only matched lines where `<SocialButtons />` was the entire line content. The fixture had `  return <SocialButtons />;` where the JSX is embedded in a return statement — the leading `return` caused the match to fail.
- **Fix:** Changed to `^[^\n]*<SocialButtons[^>]*\/>[^\n]*\n?` to match any line containing a self-closing SocialButtons element.
- **Files modified:** `packages/create-foundation-app/src/remove.ts`
- **Verification:** All 11 unit tests pass GREEN after fix
- **Committed in:** `f8bd1ac` (Task 2 commit — fix applied before Task 1 commit was finalized for Task 2 changes)

---

**Total deviations:** 2 auto-fixed (both Rule 1 - Bug)
**Impact on plan:** Both fixes necessary for correctness — the plan's implementation sketch assumed simpler fixture patterns than the real template files contain. No scope creep.

## Issues Encountered

None beyond the two auto-fixed bugs above.

## Next Phase Readiness

- Phase 20 (Social Auth) is now complete — all 6 plans executed, SOCIAL-01 through SOCIAL-05 satisfied
- Full phase test suite GREEN: 19 tests across test_social_settings.py, test_apple_auth.py, test_social_adapter.py, test_scaffolder_social_removal.py
- CLI scaffolder can now produce clean projects without social auth infrastructure via `--without social-auth`

---

_Phase: 20-social-auth_
_Completed: 2026-03-12_
