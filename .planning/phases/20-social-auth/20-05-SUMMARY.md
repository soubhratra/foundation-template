---
phase: 20-social-auth
plan: "05"
subsystem: mobile-auth
tags: [expo, apple-sign-in, ios, react-native, jwt, social-auth]

# Dependency graph
requires:
  - phase: 20-03
    provides: POST /api/v1/auth/apple/ endpoint returning {access, refresh} JWT tokens
provides:
  - apps/mobile/app/(auth)/sign-in.tsx with iOS-only Apple Sign In button
affects: []

# Tech tracking
tech-stack:
  added:
    - expo-apple-authentication@~7.1.3 (Expo SDK 52 compatible)
  patterns:
    - "Apple Sign In mobile flow: expo-apple-authentication.signInAsync() -> POST /api/v1/auth/apple/ -> tokenStorage.setTokens({accessToken, refreshToken}) -> queryClient.invalidateQueries(USER_QUERY_KEY)"
    - "iOS-only Apple button: Platform.OS === 'ios' guard in footer slot of AuthForm — renders only on iOS, never on Android or web"
    - "Silent ERR_CANCELED: catch block checks error.message.includes('ERR_CANCELED') and returns without setStatus — Apple sheet dismissal is not an error"
    - "Token storage via useAuthContext(): tokenStorage.setTokens() with {accessToken, refreshToken} field names (not {access, refresh} — plan interface was incorrect)"

key-files:
  created: []
  modified:
    - apps/mobile/app/(auth)/sign-in.tsx
    - apps/mobile/package.json
    - packages/business-logic/src/hooks/use-auth.ts
    - pnpm-lock.yaml

key-decisions:
  - "Use useAuthContext() not useAuth() for token storage — useAuth() does not expose setTokens; tokenStorage is on the auth context; property names are accessToken/refreshToken not access/refresh"
  - "Rebuild @repo/business-logic after const-reassignment fix — dist/index.d.ts was missing from gitignore causing all AuthContextValue/TokenStorage types to resolve as never"
  - "expo-apple-authentication added explicitly to package.json — not auto-included in Expo 52 managed workflow; must be installed separately"

# Metrics
duration: 6min
completed: 2026-03-12
---

# Phase 20 Plan 05: Apple Sign In Mobile Screen Summary

**iOS-only Apple Sign In button in mobile sign-in screen using expo-apple-authentication, sending identityToken to the custom backend endpoint, with silent cancel handling and JWT token storage**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-12T12:17:41Z
- **Completed:** 2026-03-12T12:23:00Z
- **Tasks:** 1
- **Files modified:** 4

## Accomplishments

- `apps/mobile/app/(auth)/sign-in.tsx` updated with iOS-only Apple Sign In button in the footer slot of `AuthForm`
- `handleAppleSignIn` callback: requests `FULL_NAME` + `EMAIL` scopes, POSTs `identity_token` + `full_name` to `/api/v1/auth/apple/`, stores `accessToken`/`refreshToken` via `tokenStorage.setTokens()`, invalidates `USER_QUERY_KEY`, navigates to `/(tabs)/home`
- `Platform.OS === "ios"` guard — button never renders on Android
- `SOCIAL AUTH MODULE` sentinel comment present for scaffolder detection
- `ERR_CANCELED` error silently ignored (user dismissed Apple sheet)
- `expo-apple-authentication@~7.1.3` added to mobile dependencies
- Pre-existing `const` reassignment bug in `use-auth.ts` auto-fixed to allow `@repo/business-logic` to build

## Task Commits

1. **Task 1: Apple Sign In button** - `c7cd4af` (feat)

## Files Created/Modified

- `apps/mobile/app/(auth)/sign-in.tsx` — Modified: Apple Sign In integration (iOS-only button, handleAppleSignIn, styles, imports)
- `apps/mobile/package.json` — Modified: added `expo-apple-authentication@~7.1.3`
- `packages/business-logic/src/hooks/use-auth.ts` — Modified: auto-fixed const-reassignment bug in `request()` function
- `pnpm-lock.yaml` — Modified: updated with new dependency

## Decisions Made

- **Token storage via `useAuthContext()`**: The plan's interface reference said `const { setTokens } = useAuth()`, but `useAuth()` does not expose `setTokens`. The correct approach is `useAuthContext()` which exposes `tokenStorage: TokenStorage`. Token fields are `accessToken`/`refreshToken` (not `access`/`refresh`)
- **`@repo/business-logic` rebuild**: The `dist/index.d.ts` was missing (package was built but types weren't generated due to the const bug). After fixing the bug, rebuilding the package fixed all `never`-typed `tokenStorage` and `queryClient` issues in sign-in.tsx

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] expo-apple-authentication not installed**

- **Found during:** Task 1 (TypeScript check)
- **Issue:** `Cannot find module 'expo-apple-authentication'` — the package was not in `apps/mobile/package.json`. The plan stated "Expo SDK 53 built-in — no install required" but the installed version is Expo 52, and even in Expo 53 the package must be explicitly listed
- **Fix:** `npx expo install expo-apple-authentication` (uses expo's version resolver for correct compatibility) → added `expo-apple-authentication@~7.1.3`
- **Files modified:** `apps/mobile/package.json`, `pnpm-lock.yaml`
- **Committed in:** c7cd4af

**2. [Rule 1 - Bug] `const` reassignment in `use-auth.ts` request() function**

- **Found during:** Task 1 (attempting to rebuild @repo/business-logic to fix never types)
- **Issue:** `headers` destructured as `const` from `init` then reassigned on line 192 — esbuild and tsc both rejected this
- **Fix:** Changed `const { headers, ...rest } = init` to `const { headers: initHeaders, ...rest } = init; let headers = initHeaders`, created `merged` from `initHeaders` and reassigned `headers = merged`
- **Files modified:** `packages/business-logic/src/hooks/use-auth.ts`
- **Committed in:** c7cd4af

**3. [Rule 1 - Bug] `theme.colors.mutedForeground` does not exist**

- **Found during:** Task 1 (TypeScript check)
- **Issue:** Plan specified `color: theme.colors.mutedForeground` but the theme type only has `textMuted` (not `mutedForeground`)
- **Fix:** Changed to `theme.colors.textMuted`
- **Files modified:** `apps/mobile/app/(auth)/sign-in.tsx`
- **Committed in:** c7cd4af

**4. [Rule 2 - Missing Functionality] Use `useAuthContext()` instead of `useAuth().setTokens`**

- **Found during:** Task 1 (reviewing actual API)
- **Issue:** Plan's interface reference said `const { setTokens } = useAuth()`, but `UseAuthResult` has no `setTokens` property; correct API is `useAuthContext().tokenStorage.setTokens({ accessToken, refreshToken })`
- **Fix:** Added `useAuthContext` and `USER_QUERY_KEY` imports; used `tokenStorage.setTokens()` + `queryClient.invalidateQueries()` for correct token storage and auth state invalidation
- **Files modified:** `apps/mobile/app/(auth)/sign-in.tsx`
- **Committed in:** c7cd4af

---

**Total deviations:** 4 auto-fixed (3x Rule 1 Bug, 1x Rule 3 Blocking)
**Impact on plan:** All deviations required for correct implementation. No scope creep.

## Deferred Items

- Pre-existing: `apps/mobile/app/_layout.tsx` TypeScript error — `enableDevtools` prop passed to `AuthProvider` but not in `AuthProviderProps`. Was masked before because `@repo/business-logic/dist/index.d.ts` was missing. Documented in `deferred-items.md`.

## Next Phase Readiness

- Plan 20-05 (SOCIAL-03 mobile) complete
- Phase 20 SOCIAL-01, SOCIAL-02, SOCIAL-03 all satisfied
- Remaining: Plan 20-06 if any (check ROADMAP)

## Self-Check: PASSED

- apps/mobile/app/(auth)/sign-in.tsx: FOUND
- apps/mobile/package.json (expo-apple-authentication): FOUND
- packages/business-logic/src/hooks/use-auth.ts (const fix): FOUND
- Commit c7cd4af: FOUND

---

_Phase: 20-social-auth_
_Completed: 2026-03-12_
