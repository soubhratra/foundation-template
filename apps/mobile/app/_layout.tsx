import { type ReactNode, useEffect, useMemo } from "react";
import { ActivityIndicator, StyleSheet, View } from "react-native";

import { Redirect, SplashScreen, Stack as ExpoStack } from "expo-router";
import * as SecureStore from "expo-secure-store";

import {
  AuthProvider,
  createSecureStoreTokenStorage,
  type SecureStoreAdapter,
  useAuth,
} from "@repo/business-logic";
import { Text } from "@repo/ui";

import { env } from "@/lib/env";

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
  readonly redirect: string;
  readonly children: ReactNode;
};

type StackComponent = typeof ExpoStack & {
  Protected: (props: ProtectedScreenProps) => ReactNode;
};

const Stack = ExpoStack as StackComponent;

Stack.Protected = function ProtectedRoute({ guard, redirect, children }: ProtectedScreenProps) {
  if (!guard) {
    return <Redirect href={redirect} />;
  }
  return <>{children}</>;
};

export default function RootLayout() {
  const tokenStorage = useMemo(() => createSecureStoreTokenStorage(secureStoreAdapter), []);

  return (
    <AuthProvider
      baseUrl={buildApiBaseUrl(env.EXPO_PUBLIC_API_URL)}
      tokenStorage={tokenStorage}
      enableDevtools={false}
    >
      <AuthGate />
    </AuthProvider>
  );
}

function AuthGate() {
  const { isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading) {
      SplashScreen.hideAsync().catch(() => undefined);
    }
  }, [isLoading]);

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" />
        <Text variant="subtle" weight="medium">
          Checking your session...
        </Text>
      </View>
    );
  }

  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Protected guard={isAuthenticated} redirect="/(auth)/sign-in">
        <Stack.Screen name="(tabs)" />
      </Stack.Protected>
      <Stack.Protected guard={!isAuthenticated} redirect="/(tabs)/home">
        <Stack.Screen name="(auth)" />
      </Stack.Protected>
    </Stack>
  );
}

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    gap: 12,
    padding: 24,
  },
});
