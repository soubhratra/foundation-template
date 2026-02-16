/**
 * AuthGate component - SplashScreen-aware authentication gate
 *
 * Blocks rendering until bootstrap completes and tokens are restored.
 * Shows branded loading view while waiting, then renders children.
 */

import { useEffect, useState } from "react";
import { ActivityIndicator, StyleSheet, View } from "react-native";

import { SplashScreen, useRouter, useSegments } from "expo-router";

import { useAuth } from "@repo/business-logic";
import { Text } from "@repo/ui";

import { ensureJwtSession, getBootstrapState } from "@/lib/auth/bootstrap";
import { env } from "@/lib/env";

interface AuthGateProps {
  /** Child components to render after authentication is confirmed */
  children: React.ReactNode;
}

/**
 * AuthGate - Blocks rendering until bootstrap completes
 *
 * 1. Calls ensureJwtSession to restore/refresh tokens from SecureStore
 * 2. Waits for useAuth() to settle (initial /users/me query complete)
 * 3. Then handles navigation based on auth state
 */
export function AuthGate({ children }: AuthGateProps) {
  const { isAuthenticated, isLoading, refetch } = useAuth();
  const router = useRouter();
  const segments = useSegments();

  const [bootstrapError, setBootstrapError] = useState<string | undefined>();
  const [isInitializing, setIsInitializing] = useState(true);

  // Bootstrap on mount
  useEffect(() => {
    let mounted = true;

    async function bootstrap() {
      try {
        const state = getBootstrapState();

        // If already bootstrapped, skip
        if (state.ready && state.attempted) {
          setIsInitializing(false);
          return;
        }

        // Build API base URL
        const apiBase = env.EXPO_PUBLIC_API_URL;

        // Run bootstrap
        const result = await ensureJwtSession({
          baseUrl: apiBase,
          dev: __DEV__,
        });

        if (!mounted) return;

        setBootstrapError(result.error);

        // After bootstrap, trigger initial user fetch if we have tokens
        if (result.ready) {
          try {
            await refetch();
          } catch {
            // Ignore refetch errors - auth state will handle unauthenticated
          }
        }
      } catch (error) {
        if (!mounted) return;
        const errorMessage = error instanceof Error ? error.message : "Bootstrap failed";
        setBootstrapError(errorMessage);
        console.error("[AuthGate] Bootstrap error:", errorMessage);
      } finally {
        if (mounted) {
          setIsInitializing(false);
        }
      }
    }

    bootstrap();

    return () => {
      mounted = false;
    };
  }, [refetch]);

  // Hide splash screen when bootstrap + auth settle
  useEffect(() => {
    if (!isInitializing && !isLoading) {
      SplashScreen.hideAsync().catch(() => undefined);
    }
  }, [isInitializing, isLoading]);

  // Handle navigation based on auth state
  useEffect(() => {
    if (isInitializing || isLoading) {
      return;
    }

    const inAuthGroup = segments[0] === "(auth)";

    if (isAuthenticated && inAuthGroup) {
      router.replace("/(tabs)/home");
    } else if (!isAuthenticated && !inAuthGroup) {
      // If bootstrap failed or tokens were cleared, go to sign in
      router.replace("/(auth)/sign-in");
    }
  }, [isAuthenticated, isLoading, isInitializing, router, segments]);

  // Show loading while bootstrapping
  if (isInitializing || isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#6366f1" />
        <Text variant="subtle" weight="medium">
          Loading your session...
        </Text>
        {bootstrapError && (
          <Text variant="caption" style={{ color: "#ef4444" }}>
            {bootstrapError}
          </Text>
        )}
      </View>
    );
  }

  // Error state - allow navigation to handle
  if (bootstrapError && !isAuthenticated) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#6366f1" />
        <Text variant="subtle" weight="medium">
          Session expired. Please sign in again.
        </Text>
      </View>
    );
  }

  return <>{children}</>;
}

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    gap: 12,
    padding: 24,
    backgroundColor: "#ffffff",
  },
});
