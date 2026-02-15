# Expo Mobile App Specification

> Baseline specification for the Foundation Template.
> This document is the source of truth. All implementations must conform to these specs.

## Overview

The Expo mobile application lives at `apps/mobile/` in the Turborepo monorepo. It uses the Expo managed workflow (no native code ejection), Expo Router for file-based navigation, JWT token auth stored in `expo-secure-store`, and consumes shared packages (`@repo/api-client`, `@repo/validation`, `@repo/ui`, `@repo/business-logic`) from the monorepo. The mobile app communicates directly with the Django API (no BFF proxy).

---

## Specifications

### 1. Expo Router Directory Structure

```
apps/mobile/
  app/
    (auth)/
      login.tsx               # Login screen
      signup.tsx              # Signup screen
      _layout.tsx             # Stack navigator for auth flow
    (tabs)/
      index.tsx               # Home tab (maps to dashboard)
      settings.tsx            # Settings tab
      profile.tsx             # Profile tab
      _layout.tsx             # Tab navigator layout
    _layout.tsx               # Root layout: auth state, providers, font loading
    +not-found.tsx            # 404 fallback screen
  components/                 # Mobile-specific components
    auth/
      login-form.tsx
      signup-form.tsx
    navigation/
      tab-bar.tsx
      tab-bar-icon.tsx
    shared/
      screen-header.tsx
      loading-screen.tsx
  lib/
    auth.ts                   # Auth utilities (token storage, refresh)
    api.ts                    # Mobile API client configuration
    storage.ts                # Secure storage wrapper
  app.json                    # Expo static config
  app.config.ts               # Expo dynamic config (env vars)
  metro.config.js             # Metro bundler monorepo config
  tsconfig.json
  package.json
```

### 2. Navigation Patterns

#### Root Layout (`app/_layout.tsx`)

The root layout is the app entry point. It handles:

- Font loading with `expo-font` and `useFonts`
- Splash screen control (`expo-splash-screen`)
- Auth state initialization (check for stored JWT)
- Conditional routing: redirect to `(auth)` or `(tabs)` based on auth state
- React Query provider

```tsx
// app/_layout.tsx
import { useEffect, useState } from "react";
import { Slot, useRouter, useSegments } from "expo-router";
import * as SplashScreen from "expo-splash-screen";
import { useFonts, Inter_400Regular, Inter_600SemiBold } from "@expo-google-fonts/inter";
import { QueryProvider } from "@/components/providers/query-provider";
import { AuthProvider, useAuth } from "@repo/business-logic";
import { getStoredToken } from "@/lib/auth";

SplashScreen.preventAutoHideAsync();

function AuthGate({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const segments = useSegments();
  const router = useRouter();

  useEffect(() => {
    if (isLoading) return;

    const inAuthGroup = segments[0] === "(auth)";

    if (!isAuthenticated && !inAuthGroup) {
      router.replace("/(auth)/login");
    } else if (isAuthenticated && inAuthGroup) {
      router.replace("/(tabs)");
    }
  }, [isAuthenticated, isLoading, segments]);

  return <>{children}</>;
}

export default function RootLayout() {
  const [fontsLoaded] = useFonts({ Inter_400Regular, Inter_600SemiBold });

  useEffect(() => {
    if (fontsLoaded) SplashScreen.hideAsync();
  }, [fontsLoaded]);

  if (!fontsLoaded) return null;

  return (
    <QueryProvider>
      <AuthProvider tokenProvider={getStoredToken}>
        <AuthGate>
          <Slot />
        </AuthGate>
      </AuthProvider>
    </QueryProvider>
  );
}
```

#### Auth Stack (`app/(auth)/_layout.tsx`)

Auth screens use a stack navigator with no visible header. Users navigate forward through login/signup and are redirected to tabs on success.

```tsx
// app/(auth)/_layout.tsx
import { Stack } from "expo-router";

export default function AuthLayout() {
  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="login" />
      <Stack.Screen name="signup" />
    </Stack>
  );
}
```

#### Tab Navigator (`app/(tabs)/_layout.tsx`)

Authenticated users see a bottom tab bar with Home, Settings, and Profile tabs.

```tsx
// app/(tabs)/_layout.tsx
import { Tabs } from "expo-router";
import { Home, Settings, User } from "lucide-react-native";

export default function TabLayout() {
  return (
    <Tabs screenOptions={{ tabBarActiveTintColor: "#0066FF" }}>
      <Tabs.Screen
        name="index"
        options={{
          title: "Home",
          tabBarIcon: ({ color, size }) => <Home color={color} size={size} />,
        }}
      />
      <Tabs.Screen
        name="settings"
        options={{
          title: "Settings",
          tabBarIcon: ({ color, size }) => <Settings color={color} size={size} />,
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: "Profile",
          tabBarIcon: ({ color, size }) => <User color={color} size={size} />,
        }}
      />
    </Tabs>
  );
}
```

#### Navigation Summary

| Navigator | Type | Screens | Auth Requirement |
|-----------|------|---------|------------------|
| Root `_layout.tsx` | Slot (conditional) | Routes to `(auth)` or `(tabs)` | Checks auth state |
| `(auth)/_layout.tsx` | Stack | `login`, `signup` | Unauthenticated only |
| `(tabs)/_layout.tsx` | Tabs | `index` (Home), `settings`, `profile` | Authenticated only |

#### Deep Linking Configuration

Deep links are configured in `app.json` under `expo.scheme` and via Expo Router's file-based routing.

| URL Pattern | Screen | Use Case |
|-------------|--------|----------|
| `myapp://login` | `(auth)/login` | Push notification: session expired |
| `myapp://signup` | `(auth)/signup` | Marketing link |
| `myapp://settings` | `(tabs)/settings` | App settings shortcut |
| `myapp://profile` | `(tabs)/profile` | Profile deep link |

```json
{
  "expo": {
    "scheme": "myapp"
  }
}
```

### 3. Auth Implementation

#### Token Storage

Tokens are stored securely using `expo-secure-store`, which uses Keychain (iOS) and Keystore (Android).

```ts
// lib/storage.ts
import * as SecureStore from "expo-secure-store";

const ACCESS_TOKEN_KEY = "auth_access_token";
const REFRESH_TOKEN_KEY = "auth_refresh_token";

export async function storeTokens(accessToken: string, refreshToken: string): Promise<void> {
  await SecureStore.setItemAsync(ACCESS_TOKEN_KEY, accessToken);
  await SecureStore.setItemAsync(REFRESH_TOKEN_KEY, refreshToken);
}

export async function getAccessToken(): Promise<string | null> {
  return SecureStore.getItemAsync(ACCESS_TOKEN_KEY);
}

export async function getRefreshToken(): Promise<string | null> {
  return SecureStore.getItemAsync(REFRESH_TOKEN_KEY);
}

export async function clearTokens(): Promise<void> {
  await SecureStore.deleteItemAsync(ACCESS_TOKEN_KEY);
  await SecureStore.deleteItemAsync(REFRESH_TOKEN_KEY);
}
```

#### Auth State Provider

The auth state is managed by the shared `useAuth` hook from `@repo/business-logic`, initialized with a `MobileAuthProvider` that reads from secure storage.

| State | Behavior |
|-------|----------|
| `isLoading: true` | App is checking secure store for existing tokens; splash screen remains visible |
| `isAuthenticated: false` | No valid token found; user routed to `(auth)/login` |
| `isAuthenticated: true` | Valid token found; user routed to `(tabs)` |

#### Token Refresh Interceptor

The API client includes a request interceptor that handles transparent token refresh.

```ts
// lib/api.ts
import createClient from "openapi-fetch";
import type { paths } from "@repo/api-client";
import { getAccessToken, getRefreshToken, storeTokens, clearTokens } from "./storage";

const API_URL = process.env.EXPO_PUBLIC_API_URL || "http://localhost:8000";

let isRefreshing = false;
let refreshPromise: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = await getRefreshToken();
  if (!refreshToken) return null;

  const response = await fetch(`${API_URL}/api/v1/auth/token/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh: refreshToken }),
  });

  if (!response.ok) {
    await clearTokens();
    return null;
  }

  const data = await response.json();
  await storeTokens(data.access, data.refresh || refreshToken);
  return data.access;
}

export function createMobileApiClient() {
  const client = createClient<paths>({ baseUrl: API_URL });

  // Add auth header to every request
  client.use({
    async onRequest({ request }) {
      const token = await getAccessToken();
      if (token) {
        request.headers.set("Authorization", `Bearer ${token}`);
      }
      return request;
    },
    async onResponse({ response, request }) {
      if (response.status === 401) {
        // Prevent concurrent refresh attempts
        if (!isRefreshing) {
          isRefreshing = true;
          refreshPromise = refreshAccessToken();
        }

        const newToken = await refreshPromise;
        isRefreshing = false;
        refreshPromise = null;

        if (newToken) {
          // Retry original request with new token
          request.headers.set("Authorization", `Bearer ${newToken}`);
          return fetch(request);
        }
        // If refresh failed, token cleared -- auth state will redirect to login
      }
      return response;
    },
  });

  return client;
}
```

### 4. Metro Bundler Configuration

Metro must be configured explicitly for monorepo package resolution with pnpm.

```js
// metro.config.js
const { getDefaultConfig } = require("expo/metro-config");
const path = require("path");

const projectRoot = __dirname;
const monorepoRoot = path.resolve(projectRoot, "../..");

const config = getDefaultConfig(projectRoot);

// Watch all files in the monorepo for hot reload
config.watchFolders = [monorepoRoot];

// Resolve packages from both local and root node_modules
config.resolver.nodeModulesPaths = [
  path.resolve(projectRoot, "node_modules"),
  path.resolve(monorepoRoot, "node_modules"),
];

// Prevent duplicate React instances from symlinked packages
config.resolver.disableHierarchicalLookup = true;

module.exports = config;
```

| Configuration | Purpose |
|---------------|---------|
| `watchFolders: [monorepoRoot]` | Enables hot reload when shared package files change |
| `nodeModulesPaths` (two entries) | Resolves packages from local `node_modules` first, then monorepo root (pnpm hoisted) |
| `disableHierarchicalLookup` | Prevents Metro from finding duplicate React/React Native copies in symlinked packages |

#### Platform Extension Resolution

Metro and webpack both resolve platform-specific file extensions automatically:

| Extension | Resolved By | Platform |
|-----------|-------------|----------|
| `.native.tsx` | Metro | iOS and Android |
| `.ios.tsx` | Metro | iOS only |
| `.android.tsx` | Metro | Android only |
| `.web.tsx` | Webpack (Next.js) | Web only |
| `.tsx` | Both | Fallback (all platforms) |

Shared packages use `.native.tsx` and `.web.tsx` splits when a component has platform-specific implementations.

### 5. Shared Package Consumption

| Package | Usage in Mobile | Import Example |
|---------|----------------|----------------|
| `@repo/api-client` | Typed API calls via `openapi-fetch` | `import type { paths } from "@repo/api-client"` |
| `@repo/validation` | Form validation with Zod schemas | `import { loginSchema } from "@repo/validation"` |
| `@repo/ui` | Cross-platform UI primitives | `import { Button, Text, Card } from "@repo/ui"` |
| `@repo/business-logic` | Auth hooks, user hooks, utilities | `import { useAuth, useUser } from "@repo/business-logic"` |

All shared packages must:
- Have `"main": "src/index.ts"` in their `package.json` (source entry for Metro)
- Not import from `expo-*` packages (mobile-only)
- Not import navigation libraries
- Not use web-only APIs (`window`, `document`, `localStorage`)

### 6. App Configuration

#### app.json (static config)

```json
{
  "expo": {
    "name": "Foundation App",
    "slug": "foundation-app",
    "version": "1.0.0",
    "scheme": "myapp",
    "orientation": "portrait",
    "icon": "./assets/icon.png",
    "splash": {
      "image": "./assets/splash.png",
      "resizeMode": "contain",
      "backgroundColor": "#ffffff"
    },
    "assetBundlePatterns": ["**/*"],
    "ios": {
      "supportsTablet": true,
      "bundleIdentifier": "com.foundation.app"
    },
    "android": {
      "adaptiveIcon": {
        "foregroundImage": "./assets/adaptive-icon.png",
        "backgroundColor": "#ffffff"
      },
      "package": "com.foundation.app"
    },
    "plugins": [
      "expo-router",
      "expo-secure-store"
    ]
  }
}
```

#### app.config.ts (dynamic config with env vars)

```ts
// app.config.ts
import { ExpoConfig, ConfigContext } from "expo/config";

export default ({ config }: ConfigContext): ExpoConfig => ({
  ...config,
  name: "Foundation App",
  slug: "foundation-app",
  extra: {
    apiUrl: process.env.EXPO_PUBLIC_API_URL || "http://localhost:8000",
  },
});
```

### 7. GIVEN/WHEN/THEN Scenarios

#### Scenario: App Launch -- Check Stored Token

```
GIVEN the user has previously logged in
  AND a valid JWT access token is stored in expo-secure-store
WHEN the app launches
THEN the root _layout.tsx initializes the AuthProvider
  AND the AuthProvider reads the token from secure storage
  AND isAuthenticated becomes true
  AND the AuthGate redirects to /(tabs)
  AND the splash screen hides after fonts load
```

```
GIVEN the user has never logged in (first launch)
  AND no token exists in expo-secure-store
WHEN the app launches
THEN the root _layout.tsx initializes the AuthProvider
  AND the AuthProvider finds no token
  AND isAuthenticated becomes false
  AND the AuthGate redirects to /(auth)/login
  AND the splash screen hides after fonts load
```

#### Scenario: Login Flow -- Store JWT, Navigate to Tabs

```
GIVEN the user is on the login screen
  AND the user enters valid email and password
WHEN the user taps "Log In"
THEN the login form validates input against the Zod schema from @repo/validation
  AND a POST request is sent to /api/v1/auth/login on Django
  AND Django validates credentials and returns { access, refresh } tokens
  AND the tokens are stored in expo-secure-store via storeTokens()
  AND the AuthProvider's isAuthenticated state updates to true
  AND the AuthGate detects the state change and navigates to /(tabs)
```

```
GIVEN the user is on the login screen
  AND the user enters an incorrect password
WHEN the user taps "Log In"
THEN the POST to /api/v1/auth/login returns 401
  AND an error message "Invalid credentials" is displayed on the login screen
  AND no tokens are stored
  AND the user remains on the login screen
```

#### Scenario: Token Expiry -- Refresh or Redirect to Login

```
GIVEN the user is authenticated with a valid refresh token
  AND the access token has expired
WHEN the user makes an API request that returns 401
THEN the API client interceptor detects the 401
  AND it sends the refresh token to /api/v1/auth/token/refresh
  AND Django returns a new access token
  AND the new token is stored in expo-secure-store
  AND the original request is retried with the new access token
  AND the user sees no interruption
```

```
GIVEN the user is authenticated
  AND both the access token and refresh token have expired
WHEN the user makes an API request that returns 401
THEN the API client interceptor attempts token refresh
  AND the refresh endpoint returns 401 (refresh token invalid)
  AND both tokens are cleared from expo-secure-store
  AND the AuthProvider's isAuthenticated state updates to false
  AND the AuthGate redirects the user to /(auth)/login
```

#### Scenario: Shared Component Rendering

```
GIVEN a shared Button component exists in @repo/ui
  AND it is implemented using React Native core Pressable and Text
WHEN the Expo app imports and renders <Button label="Submit" />
THEN Metro resolves the .native.tsx variant (if it exists) or the default .tsx
  AND the component renders as a native Pressable with Text
  AND the same component (resolved as .web.tsx or default) renders in Next.js via react-native-web
```

---

## Constraints

- **Expo managed workflow only.** No ejection. No bare workflow. No custom native modules (use Expo SDK or `expo-dev-client` if native modules are needed).
- **No session cookies for auth.** Mobile uses JWT tokens stored in `expo-secure-store`. Session cookies are for the web app only.
- **No `AsyncStorage` for sensitive data.** Use `expo-secure-store` for tokens. `AsyncStorage` is for non-sensitive preferences only.
- **No navigation code in shared packages.** Navigation is mobile-specific (Expo Router) and must stay in `apps/mobile/`.
- **No `expo-*` imports in shared packages.** Shared packages use only `react-native` core APIs. Any `expo-*` dependency makes the package mobile-only.
- **No web-only APIs in shared code.** No `window`, `document`, `localStorage` in `@repo/ui`, `@repo/validation`, or `@repo/business-logic`.
- **EXPO_PUBLIC_ prefix for env vars.** Only variables prefixed with `EXPO_PUBLIC_` are available in the Expo runtime bundle.
- **Metro config must be explicit.** Do not rely on Metro's default resolution for monorepo packages. Always configure `watchFolders`, `nodeModulesPaths`, and `disableHierarchicalLookup`.

---

## References

- `.planning/research/STACK.md` -- Expo SDK, React Native version compatibility, @tanstack/react-query, Zod
- `.planning/research/ARCHITECTURE.md` -- Expo Router structure, Metro config pattern, auth flow (JWT for mobile), monorepo layout
- `.planning/research/PITFALLS.md` -- Expo Metro bundler misconfiguration (Pitfall 6), RNW overreach (Pitfall 3), auth dual strategy (Pitfall 2)
- `.planning/PROJECT.md` -- Core requirements (managed workflow, auth, shared packages)
