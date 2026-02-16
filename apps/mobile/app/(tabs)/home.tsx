"use client";

import { useCallback } from "react";
import { StyleSheet, View, ScrollView } from "react-native";

import { Link } from "expo-router";

import { Button, Card, Text } from "@repo/ui";

import { useUser } from "@repo/business-logic";

/**
 * Home screen that displays personalized greeting and quick links.
 * Consumes useUser() to demonstrate authenticated session works
 * beyond just auth flows - proving SecureStore-backed sessions work.
 */
export default function HomeScreen() {
  const { user, isAuthenticated, refresh } = useUser();

  const handleRefresh = useCallback(async () => {
    await refresh();
  }, [refresh]);

  // Get the user's first name for personalization
  const firstName = user?.full_name?.split(" ")[0] ?? user?.email?.split("@")[0] ?? "User";

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Welcome Card */}
      <Card style={styles.welcomeCard}>
        <Text variant="title" weight="bold">
          Welcome{isAuthenticated ? `, ${firstName}` : ""}!
        </Text>
        <Text variant="subtle" style={styles.welcomeText}>
          {isAuthenticated
            ? "Your session is active and SecureStore is working."
            : "Sign in to access your account."}
        </Text>

        {isAuthenticated && (
          <View style={styles.userInfo}>
            <Text variant="caption">Signed in as:</Text>
            <Text variant="body" weight="medium">
              {user?.email}
            </Text>
          </View>
        )}
      </Card>

      {/* Quick Actions */}
      {isAuthenticated ? (
        <>
          <Text variant="title" weight="bold" style={styles.sectionTitle}>
            Quick Actions
          </Text>

          <View style={styles.actionsGrid}>
            <Link href="/(tabs)/profile" asChild>
              <Card style={styles.actionCard}>
                <Text variant="body" weight="medium">
                  Edit Profile
                </Text>
                <Text variant="caption">
                  Update your name and preferences
                </Text>
              </Card>
            </Link>

            <Link href="/(tabs)/settings" asChild>
              <Card style={styles.actionCard}>
                <Text variant="body" weight="medium">
                  Settings
                </Text>
                <Text variant="caption">
                  Manage notifications and security
                </Text>
              </Card>
            </Link>
          </View>
        </>
      ) : (
        <Card style={styles.signInCard}>
          <Text variant="body">
            Sign in to access your profile and customize your experience.
          </Text>
          <Link href="/(auth)/sign-in" asChild>
            <Button>Sign In</Button>
          </Link>
        </Card>
      )}

      {/* Session Info */}
      <Card style={styles.sessionCard}>
        <Text variant="title" weight="bold">
          Session Status
        </Text>
        <View style={styles.statusRow}>
          <Text variant="body">Authenticated:</Text>
          <Text variant="body" weight="medium" style={styles.statusValue}>
            {isAuthenticated ? "Yes" : "No"}
          </Text>
        </View>
        <Button
          onPress={handleRefresh}
          variant="outline"
          size="sm"
        >
          Refresh Session
        </Button>
      </Card>
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
    gap: 16,
  },
  welcomeCard: {
    gap: 8,
  },
  welcomeText: {
    marginTop: 4,
  },
  userInfo: {
    marginTop: 8,
    paddingTop: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: "#e5e7eb",
    gap: 4,
  },
  sectionTitle: {
    marginLeft: 4,
    marginTop: 8,
  },
  actionsGrid: {
    gap: 12,
  },
  actionCard: {
    gap: 4,
  },
  signInCard: {
    gap: 16,
  },
  sessionCard: {
    gap: 12,
  },
  statusRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  statusValue: {
    color: "#16a34a",
  },
});
