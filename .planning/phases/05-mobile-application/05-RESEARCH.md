# Phase 05: Mobile Application - Research

**Researched:** 2026-02-16
**Domain:** Expo Router mobile app with shared auth stack
**Confidence:** MEDIUM

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
No CONTEXT.md exists for this phase; default foundation mandates (Expo Router, shared packages, dual auth) remain binding per `openspec/specs/frontend/mobile.md` and `openspec/specs/foundation/auth.md`.

### Claude's Discretion
Not specified.

### Deferred Ideas (OUT OF SCOPE)
Not specified.
</user_constraints>

## Summary

Phase 05 must deliver a production-ready Expo Router app where sign-up/login, auth-gated tab navigation, and profile updates reuse the shared packages shipped in Phase 3 (API client, validation, UI, business-logic) while satisfying MOB-01..MOB-08 and AUTH-07 (`.planning/REQUIREMENTS.md`). The current scaffold already wires `AuthProvider` to Expo Secure Store tokens in `app/_layout.tsx`, so the plan should expand that pattern into full auth flows, tab layouts, and profile forms instead of rebuilding anything ad-hoc (`apps/mobile/app/_layout.tsx`, `packages/business-logic/src/utils/storage.ts`).

Expo Router’s protected route APIs and splash-screen control let us gate `(auth)` vs `(tabs)` stacks without duplicating navigation logic, and the official guide even shows the exact `SecureStore` persistence pattern we need (`docs.expo.dev/router/advanced/authentication/`). Combined with TanStack Query’s React Native focus/online managers, we can keep shared query cache coherent with Expo Router screens to satisfy the “shared API client + JWT persistence” success criteria (`tanstack.com/query/latest/docs/framework/react/react-native?plain=1`).

Form UX should match web by using `@repo/validation` schemas + React Hook Form controllers and `@repo/ui` primitives, while `lucide-react-native` covers tab icons mandated by the Expo spec (`openspec/specs/expo-app/spec.md`). Keep Metro configured to watch workspace packages to avoid duplicate React copies (`apps/mobile/metro.config.js`).

**Primary recommendation:** Wrap the entire app in the shared `AuthProvider` seeded with `createSecureStoreTokenStorage`, gate navigation with Expo Router’s `Stack.Protected`, and wire TanStack Query’s `focusManager`/`onlineManager` to React Native AppState + NetInfo so JWT state, tabs, and profile data stay synchronized across restarts/offline sessions.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `expo` | `~52.0.0` | Managed runtime + OTA updates | Matches repo scaffold and Expo SDK mandates for React 18.3 (`apps/mobile/package.json`). |
| `expo-router` | `~4.0.0` | File-based navigation, `Stack.Protected`, deep linking | Required by mobile spec for auth/tab routing; official guide provides SecureStore-aware auth gating (`openspec/specs/frontend/mobile.md`, `docs.expo.dev/router/advanced/authentication/`). |
| `react-native` | `~0.76.0` | Platform runtime for iOS/Android | Matches Expo SDK 52 requirement and existing workspace deps (`apps/mobile/package.json`). |
| `@tanstack/react-query` | `^5.90.21` | Shared API cache + hooks via `@repo/api-client` | Already bundled in `@repo/business-logic`; React Native-specific focus/online APIs documented by TanStack (`packages/business-logic/package.json`, `tanstack.com/query/latest/docs/framework/react/react-native?plain=1`). |
| `react-hook-form` | `^7.71.1` | Form state + validation bridge to Zod schemas | Required to consume `@repo/validation` schemas; RN Controller example is officially supported (`apps/mobile/package.json`, `react-hook-form.com/get-started#ReactNative`). |
| `@repo/business-logic` | `workspace:*` | Auth context, API client bundle, SecureStore adapters | Provides `AuthProvider`, `useAuth`, `createSecureStoreTokenStorage` so mobile/web share auth semantics (`packages/business-logic/src`). |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `expo-secure-store` | `~13.0.0` | Encrypt + persist JWT/refresh tokens per AUTH-07 | Required for login, refresh, and auto sign-in flows (`apps/mobile/package.json`, `docs.expo.dev/versions/latest/sdk/securestore/`). |
| `react-native-safe-area-context` / `react-native-screens` | `4.12.0` / `~4.4.0` | Native navigation primitives used by Expo Router | Keep installed so tabs + stacks respect notches and performance budgets (`apps/mobile/package.json`). |
| `@hookform/resolvers` | `^3.10.0` | Bridge React Hook Form to Zod schemas | All auth/profile forms should use `zodResolver(loginSchema|signupSchema|updateProfileSchema)` to mirror backend validation (`apps/mobile/package.json`, `packages/validation/src`). |
| `lucide-react-native` | `^0.564.0` (aligns with web’s `lucide-react`) | Tab icons per Expo spec | Add to mobile workspace so tab layout matches brand guidelines (`openspec/specs/expo-app/spec.md`, `apps/web/package.json`). |
| Expo core libs (`expo-linking`, `expo-constants`, `expo-status-bar`) | `~7.0.0`, `~17.0.0`, `~2.0.0` | Deep linking, env config, status bar styling | Already in `package.json`; configure linking for `foundation://` scheme per spec (`apps/mobile/package.json`, `openspec/specs/expo-app/spec.md`). |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Expo Router auth gating | Manual React Navigation stacks with guards | Violates stack decision + duplicates logic; Expo Router `Stack.Protected` already gives redirect semantics tied to auth state (`docs.expo.dev/router/advanced/authentication/`). |
| SecureStore token storage | AsyncStorage or in-memory stores | AsyncStorage is unencrypted and can’t satisfy AUTH-07 persistence requirements; memory store breaks restart persistence (`docs.expo.dev/versions/latest/sdk/securestore/`). |
| React Hook Form | Formik or uncontrolled inputs | Would require bespoke schema adapters; React Hook Form already integrates with Zod + RN controllers and matches web forms (`react-hook-form.com/get-started#ReactNative`). |

**Installation:**
```bash
# Ensure required icon + hook deps exist in the mobile workspace
pnpm --filter @repo/mobile add lucide-react-native

# (Re)sync native modules via Expo after modifying deps
npx expo install expo-router expo-secure-store @hookform/resolvers react-hook-form @tanstack/react-query
```

## Architecture Patterns

### Recommended Project Structure
```
apps/mobile/
  app/
    (auth)/            # Login + signup stack
    (tabs)/            # Home, Settings, Profile tabs
    _layout.tsx        # Root layout: providers + auth gate
    +not-found.tsx
  components/          # Auth forms, tab bar, shared headers
  lib/                 # api.ts, storage adapters, env helpers
  metro.config.js      # Monorepo resolver
  package.json
```
*Source: `openspec/specs/frontend/mobile.md`, `openspec/specs/expo-app/spec.md`*

### Pattern 1: Root Auth Gate with Shared AuthProvider
**What:** Wrap `<Slot />` in `AuthProvider` seeded with `createSecureStoreTokenStorage` and guard `(auth)` vs `(tabs)` groups using Expo Router protected routes or segment-aware redirects.
**When to use:** Always—this is how we keep JWT tokens in sync across app restarts and honor AUTH-07.
**Example:**
```tsx
import { Stack } from "expo-router";
import { SessionProvider, useSession } from "../ctx";

function RootNavigator() {
  const { session } = useSession();
  return (
    <Stack>
      <Stack.Protected guard={!!session}>
        <Stack.Screen name="(app)" />
      </Stack.Protected>
      <Stack.Protected guard={!session}>
        <Stack.Screen name="(auth)" />
      </Stack.Protected>
    </Stack>
  );
}
```
*Source: `docs.expo.dev/router/advanced/authentication/`, `apps/mobile/app/_layout.tsx`*

### Pattern 2: JWT Persistence + Refresh via SecureStore Adapter
**What:** Use `createSecureStoreTokenStorage` (from `@repo/business-logic`) so `useAuth` reads/writes tokens with OS-level encryption, and add an API middleware that refreshes tokens (`/api/v1/auth/token/refresh`) on 401 before retrying.
**When to use:** Login/signup mutations, background token refresh, logout flows, and profile update flows that need current user context.
**Supporting details:** SecureStore’s API exposes `setItemAsync`/`getItemAsync` and warns about payload sizes + iOS uninstall persistence, so code must handle `null` tokens gracefully (`docs.expo.dev/versions/latest/sdk/securestore/`, `packages/business-logic/src/utils/storage.ts`).

### Pattern 3: React Query Provider with AppState/NetInfo Bridges
**What:** Provide a singleton `QueryClient` via `AuthProvider` and wire TanStack’s `focusManager` + `onlineManager` to `AppState` + NetInfo so Expo screens refetch when the app regains focus or connectivity.
**When to use:** Any screen that should mirror backend state (Home dashboard, Profile, Settings) and needs offline awareness.
**Example:**
```ts
import NetInfo from "@react-native-community/netinfo";
import { onlineManager, focusManager } from "@tanstack/react-query";
import { AppState, Platform } from "react-native";

onlineManager.setEventListener((setOnline) =>
  NetInfo.addEventListener((state) => setOnline(!!state.isConnected))
);

function onAppStateChange(status: AppStateStatus) {
  if (Platform.OS !== "web") {
    focusManager.setFocused(status === "active");
  }
}
AppState.addEventListener("change", onAppStateChange);
```
*Source: `tanstack.com/query/latest/docs/framework/react/react-native?plain=1`*

### Anti-Patterns to Avoid
- **Bypassing `AuthProvider`:** Creating ad-hoc fetch wrappers or storing tokens in component state will desync with shared packages and break refresh logic (`packages/business-logic/src/auth-provider.tsx`).
- **Using AsyncStorage for JWTs:** Violates AUTH-07 and leaves tokens unencrypted; SecureStore is required (`docs.expo.dev/versions/latest/sdk/securestore/`).
- **Multiple QueryClients:** Spinning up a new `QueryClient` per screen defeats cache sharing and wastes refresh attempts—stick to the provider returned by `buildApiQueryClient`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Auth state + token storage | Custom context or AsyncStorage hooks | `AuthProvider` + `createSecureStoreTokenStorage` from `@repo/business-logic` | Already enforces shared API client, refresh hooks, and SecureStore adapter. |
| API networking + retries | Manual `fetch` wrappers per screen | `@repo/api-client`’s OpenAPI + TanStack integration | Ensures typed endpoints and consistent headers (`packages/api-client/src`). |
| Form validation | Local regex or inline checks | `@repo/validation` + `react-hook-form` | Keeps web/mobile forms identical and aligned with backend Zod schemas (`packages/validation/src`). |
| UI primitives | Recreating buttons/inputs/text | `@repo/ui` | Provides design-approved RN components shared with web (`packages/ui/src`). |

**Key insight:** Every requirement (auth forms, tabs, profile) already has shared building blocks—reuse them to keep parity with the Next.js app and avoid divergent logic.

## Common Pitfalls

### Pitfall 1: Splash Screen Dismissed Before Tokens Load
**What goes wrong:** App briefly shows the wrong stack because `SplashScreen.hideAsync` fires before SecureStore reads complete.
**Why it happens:** Async token checks race against navigation; Expo Router renders `(tabs)` before auth state resolves.
**How to avoid:** Call `SplashScreen.preventAutoHideAsync()` early and only hide after fonts + token state resolve (`docs.expo.dev/router/advanced/authentication/`, `apps/mobile/app/_layout.tsx`).
**Warning signs:** Flicker between login and tabs on cold start.

### Pitfall 2: SecureStore Payload/Backup Limits
**What goes wrong:** Large payloads or Android auto-backup cause SecureStore failures, leading to silent logouts.
**Why it happens:** SecureStore rejects oversized strings and Android backups can’t decrypt entries after reinstall.
**How to avoid:** Store only JWT/access/refresh tokens (no user profile data) and, if custom backup rules exist, exclude SecureStore keys per Expo docs (`docs.expo.dev/versions/latest/sdk/securestore/`).
**Warning signs:** `SecureStore` promises reject on some devices; users stay logged out after reinstall.

### Pitfall 3: Duplicate React Instances from Metro
**What goes wrong:** Redbox errors complaining about multiple React copies when importing workspace packages.
**Why it happens:** Metro resolver isn’t pointed at root `node_modules` with `disableHierarchicalLookup`.
**How to avoid:** Keep `apps/mobile/metro.config.js` updated with shared package paths and `disableHierarchicalLookup = true` whenever adding packages (`apps/mobile/metro.config.js`).
**Warning signs:** RN complains about Hooks being called from two React versions.

### Pitfall 4: Queries Not Refetching After Regaining Focus
**What goes wrong:** Tabs show stale data when the app resumes.
**Why it happens:** TanStack Query defaults assume web `window` events, so React Native never calls focus/online listeners.
**How to avoid:** Register `AppState` and NetInfo listeners via `focusManager.setFocused` and `onlineManager.setEventListener` (`tanstack.com/query/latest/docs/framework/react/react-native?plain=1`).
**Warning signs:** Pull-to-refresh works but automatic refresh never fires after backgrounding the app.

## Code Examples

### Expo Router Protected Tabs
```tsx
import { Stack } from "expo-router";
import { useSession } from "../ctx";

function RootNavigator() {
  const { session } = useSession();
  return (
    <Stack>
      <Stack.Protected guard={!!session}>
        <Stack.Screen name="(app)" />
      </Stack.Protected>
      <Stack.Protected guard={!session}>
        <Stack.Screen name="sign-in" />
      </Stack.Protected>
    </Stack>
  );
}
```
*Source: `docs.expo.dev/router/advanced/authentication/`*

### React Query Online/Focus Management in RN
```ts
import NetInfo from "@react-native-community/netinfo";
import { onlineManager, focusManager } from "@tanstack/react-query";
import { AppState, Platform } from "react-native";

onlineManager.setEventListener((setOnline) =>
  NetInfo.addEventListener((state) => setOnline(!!state.isConnected))
);

AppState.addEventListener("change", (status) => {
  if (Platform.OS !== "web") {
    focusManager.setFocused(status === "active");
  }
});
```
*Source: `tanstack.com/query/latest/docs/framework/react/react-native?plain=1`*

### React Hook Form Controller with RN Inputs
```tsx
import { Controller, useForm } from "react-hook-form";
import { TextInput } from "react-native";

const { control, handleSubmit, formState: { errors } } = useForm({
  defaultValues: { firstName: "" },
});

<Controller
  control={control}
  rules={{ required: true }}
  render={({ field: { onChange, onBlur, value } }) => (
    <TextInput
      placeholder="First name"
      onBlur={onBlur}
      onChangeText={onChange}
      value={value}
    />
  )}
  name="firstName"
/>
```
*Source: `react-hook-form.com/get-started#ReactNative`*

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual auth guarding per screen with `useEffect` redirects | Expo Router `Stack.Protected` + shared session context | Expo Router auth guide (2025-10-25) | Single source of truth for auth routing, no duplicated checks. |
| AsyncStorage/plaintext JWT storage | `expo-secure-store` with SecureStoreAdapter | SecureStore SDK 54 docs (2025) | Encrypted tokens + persistence across restarts to meet AUTH-07. |
| Web-centric React Query focus handling | AppState/NetInfo-driven `focusManager` + `onlineManager` | TanStack Query v5 RN docs (2025) | Reliable refetching when app resumes or regains connectivity. |

**Deprecated/outdated:** AsyncStorage JWT storage, manual navigation guards, and per-screen fetch logic are all superseded by SecureStore adapters, Expo Router protected layouts, and the shared API client.

## Open Questions

1. **Token refresh endpoint contract**
   - What we know: `openspec/specs/expo-app/spec.md` requires POST `/api/v1/auth/token/refresh`, but `@repo/api-client` currently lacks a refresh helper.
   - What's unclear: Does the Django API expose this endpoint already, and what response schema should the client expect (`access`, `refresh`, expiry)?
   - Recommendation: Confirm endpoint availability + schema during planning; if missing, coordinate with Phase 2 owners or add a client-side wrapper in `lib/api.ts` following the spec’s example.

2. **Profile update hook sharing**
   - What we know: Mobile must edit profile/account settings (MOB-08) and web already exposes `updateProfileAction`, but `@repo/business-logic` lacks a reusable `updateProfile` mutation.
   - What's unclear: Should we extend `@repo/business-logic` with profile mutations or call the API directly from mobile components?
   - Recommendation: Prefer adding a shared hook/mutation so mobile + web stay aligned; verify API path (`/api/v1/users/me`) and add it to the package before implementation.

## Sources

### Primary (HIGH confidence)
- `openspec/specs/frontend/mobile.md` — Required structure, shared package usage
- `openspec/specs/expo-app/spec.md` — Tabs, SecureStore keys, Metro config, token refresh requirements
- `openspec/specs/foundation/auth.md` — Dual auth strategy + JWT persistence (AUTH-07)
- `.planning/REQUIREMENTS.md` — MOB-01..MOB-08 and AUTH-07 scope
- `apps/mobile/package.json` — Current dependency versions
- `apps/mobile/app/_layout.tsx` — Existing AuthProvider + SecureStore usage
- `apps/mobile/metro.config.js` — Monorepo resolver pattern
- `packages/business-logic/src/auth-provider.tsx` & `utils/storage.ts` — Shared auth context + SecureStore adapter
- `packages/validation/src/auth.ts` & `profile.ts` — Zod schemas for auth/profile forms
- `packages/ui/src` — RN-first UI primitives

### Secondary (MEDIUM confidence)
- `docs.expo.dev/router/advanced/authentication/` (2025-10-25) — Auth gating with SecureStore example
- `docs.expo.dev/router/advanced/tabs/` (2025-10-31) — Tab layout + options
- `docs.expo.dev/versions/latest/sdk/securestore/` — SecureStore persistence rules
- `tanstack.com/query/latest/docs/framework/react/react-native?plain=1` — RN focus/online management
- `react-hook-form.com/get-started#ReactNative` — RN Controller usage

### Tertiary (LOW confidence)
- None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — Source of truth is repo `package.json` + official docs.
- Architecture: MEDIUM — Based on specs + current scaffold, but refresh hook details need confirmation.
- Pitfalls: MEDIUM — Derived from official docs + past Expo experience; needs validation during planning.

**Research date:** 2026-02-16
**Valid until:** 2026-03-18 (Expo/TanStack releases move fast; revisit after 30 days or SDK upgrade).
