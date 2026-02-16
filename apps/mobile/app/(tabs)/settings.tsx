"use client";

import { useCallback } from "react";
import { StyleSheet, View, ScrollView, Alert } from "react-native";

import { router } from "expo-router";

import { Button, Text } from "@repo/ui";

import { useAuth } from "@repo/business-logic";
import { PreferencesCard, NOTIFICATION_PREFERENCE_TOGGLES } from "@/components/profile/preferences-card";
import { usePreferences } from "@/lib/preferences/store";

/**
 * Settings screen for managing notification preferences and account actions.
 * Uses usePreferences for toggle state and useAuth for logout.
 */
export default function SettingsScreen() {
  const { preferences, setPreference, isLoading: prefsLoading } = usePreferences();
  const auth = useAuth();

  const handleToggleChange = useCallback(
    async (key: string, value: boolean) => {
      await setPreference(key as keyof typeof preferences, value);
    },
    [setPreference],
  );

  const handleLogout = useCallback(async () => {
    Alert.alert(
      "Sign Out",
      "Are you sure you want to sign out?",
      [
        {
          text: "Cancel",
          style: "cancel",
        },
        {
          text: "Sign Out",
          style: "destructive",
          onPress: async () => {
            try {
              await auth.logout.mutateAsync();
              router.replace("/(auth)/sign-in");
            } catch (error) {
              Alert.alert(
                "Error",
                error instanceof Error ? error.message : "Failed to sign out",
              );
            }
          },
        },
      ],
    );
  }, [auth]);

  const handleResetPassword = useCallback(() => {
    router.push("/(auth)/reset-password");
  }, []);

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Notification Preferences */}
      <PreferencesCard
        title="Notifications"
        description="Choose how you want to be contacted"
        toggles={NOTIFICATION_PREFERENCE_TOGGLES}
        values={preferences}
        onToggleChange={handleToggleChange}
        disabled={prefsLoading}
      />

      {/* Security Section */}
      <View style={styles.section}>
        <Text variant="title" weight="bold" style={styles.sectionTitle}>
          Security
        </Text>

        <View style={styles.card}>
          <Button
            onPress={handleResetPassword}
            variant="outline"
            disabled={auth.logout.isPending}
          >
            Reset Password
          </Button>

          <Button
            onPress={handleLogout}
            variant="ghost"
            disabled={auth.logout.isPending}
            loading={auth.logout.isPending}
          >
            Sign Out
          </Button>
        </View>
      </View>

      {/* App Info */}
      <View style={styles.section}>
        <Text variant="title" weight="bold" style={styles.sectionTitle}>
          About
        </Text>

        <View style={styles.card}>
          <Text variant="caption" style={styles.versionText}>
            Foundation Template v0.1.0
          </Text>
          <Text variant="caption" style={styles.versionText}>
            Built with Expo + Django
          </Text>
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#f9fafb",
  },
  content: {
    padding: 16,
    gap: 24,
  },
  section: {
    gap: 12,
  },
  sectionTitle: {
    marginLeft: 4,
  },
  card: {
    backgroundColor: "#ffffff",
    borderRadius: 12,
    padding: 16,
    gap: 12,
  },
  versionText: {
    textAlign: "center",
    color: "#9ca3af",
  },
});
