import { type ReactNode, useEffect, useMemo, useRef } from "react";

import { SplashScreen, Stack as ExpoStack, useSegments } from "expo-router";
import * as SecureStore from "expo-secure-store";

import { PostHogProvider, usePostHog } from "posthog-react-native";

import {
  AuthProvider,
  createSecureStoreTokenStorage,
  type SecureStoreAdapter,
} from "@repo/business-logic";

import { env } from "@/lib/env";

import { AuthGate } from "@/components/navigation/auth-gate";
import { registerNativeQueryBridge } from "@/lib/query/native-bridge";
import { PreferencesProvider } from "@/lib/preferences/store";

const API_BASE_PATH = "/api/v1";

const secureStoreAdapter: SecureStoreAdapter = {
  getItemAsync: SecureStore.getItemAsync,
  setItemAsync: SecureStore.setItemAsync,
  deleteItemAsync: SecureStore.deleteItemAsync,
};

function buildApiBaseUrl(value: string): string {
  return `${value.replace(/\/$/, "")}${API_BASE_PATH}`;
}

void SplashScreen.preventAutoHideAsync();

type ProtectedScreenProps = {
  readonly guard: boolean;
  readonly children: ReactNode;
};

type StackComponent = typeof ExpoStack & {
  Protected: (props: ProtectedScreenProps) => ReactNode;
};

const Stack = ExpoStack as StackComponent;

Stack.Protected = function ProtectedRoute({ guard, children }: ProtectedScreenProps) {
  if (!guard) {
    return null;
  }
  return <>{children}</>;
};

function PostHogScreenTracker() {
  const segments = useSegments();
  const posthog = usePostHog();
  const prevSegmentsRef = useRef<string | null>(null);
  const screenName = segments.join("/") || "(index)";

  useEffect(() => {
    if (prevSegmentsRef.current !== screenName) {
      prevSegmentsRef.current = screenName;
      posthog.screen(screenName);
    }
  }, [screenName, posthog]);

  return null;
}

export default function RootLayout() {
  const tokenStorage = useMemo(() => createSecureStoreTokenStorage(secureStoreAdapter), []);

  // Register TanStack Query native bridge on mount
  useEffect(() => {
    const bridge = registerNativeQueryBridge({ debug: __DEV__ });
    return () => bridge.unregister();
  }, []);

  return (
    <PostHogProvider
      apiKey={process.env.EXPO_PUBLIC_POSTHOG_KEY ?? ""}
      options={{ host: process.env.EXPO_PUBLIC_POSTHOG_HOST ?? "https://eu.i.posthog.com" }}
      autocapture={{ captureScreens: false }}
    >
      <PostHogScreenTracker />
      <AuthProvider
        baseUrl={buildApiBaseUrl(env.EXPO_PUBLIC_API_URL)}
        tokenStorage={tokenStorage}
        enableDevtools={false}
      >
        <PreferencesProvider>
          <AuthGate>
            <Stack screenOptions={{ headerShown: false }}>
              <Stack.Protected guard={true}>
                <Stack.Screen name="(tabs)" />
              </Stack.Protected>
              <Stack.Protected guard={true}>
                <Stack.Screen name="(auth)" />
              </Stack.Protected>
            </Stack>
          </AuthGate>
        </PreferencesProvider>
      </AuthProvider>
    </PostHogProvider>
  );
}
