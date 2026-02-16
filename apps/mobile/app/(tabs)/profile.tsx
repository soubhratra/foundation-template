"use client";

import { useState, useCallback } from "react";
import { StyleSheet, View, ScrollView } from "react-native";

import { Link, router } from "expo-router";

import { Button, Text } from "@repo/ui";

import { useUser } from "@repo/business-logic";
import { ProfileCard, ProfileCardSection, ProfileCardRow } from "@/components/profile/profile-card";
import { ProfileForm } from "@/components/profile/profile-form";
import { useUpdateProfileMutation } from "@/lib/api/profile";
import type { UpdateProfileInput } from "@repo/validation";

/**
 * Profile screen that displays and edits the authenticated user's profile.
 * Consumes useUser() for current data and uses ProfileForm for updates.
 */
export default function ProfileScreen() {
  const { user, refresh: refreshUser } = useUser();
  const [successMessage, setSuccessMessage] = useState<string | undefined>();

  const updateProfileMutation = useUpdateProfileMutation({
    onSuccess: () => {
      setSuccessMessage("Profile updated successfully!");
      // Clear success message after 3 seconds
      setTimeout(() => setSuccessMessage(undefined), 3000);
    },
  });

  const handleSubmit = useCallback(
    async (data: UpdateProfileInput) => {
      setSuccessMessage(undefined);
      await updateProfileMutation.mutateAsync(data);
    },
    [updateProfileMutation],
  );

  const handleRefresh = useCallback(async () => {
    await refreshUser();
    setSuccessMessage(undefined);
  }, [refreshUser]);

  const handleResetPassword = useCallback(() => {
    router.push("/(auth)/reset-password");
  }, []);

  // No user data - show loading or error
  if (!user) {
    return (
      <View style={styles.container}>
        <View style={styles.errorContainer}>
          <Text variant="body">Loading profile...</Text>
        </View>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Profile Summary Card */}
      <ProfileCard
        title="Profile"
        description="Your account information"
        style={styles.card}
      >
        <ProfileCardSection title="Account">
          <ProfileCardRow label="Email" value={user.email} />

          <ProfileCardRow label="Full Name" value={user.full_name ?? "Not set"} />
        </ProfileCardSection>

        <View style={styles.actionsRow}>
          <Button
            onPress={handleRefresh}
            variant="outline"
            size="sm"
            disabled={updateProfileMutation.isPending}
          >
            Refresh
          </Button>

          <Link href="/(tabs)/settings" asChild>
            <Button variant="ghost" size="sm">
              Settings
            </Button>
          </Link>
        </View>
      </ProfileCard>

      {/* Edit Profile Form */}
      <ProfileCard
        title="Edit Profile"
        description="Update your personal information"
        style={styles.card}
      >
        <ProfileForm
          defaultValues={{
            fullName: user.full_name ?? "",
            timezone: "UTC",
          }}
          onSubmit={handleSubmit}
          isSubmitting={updateProfileMutation.isPending}
          errorMessage={updateProfileMutation.error?.message}
          successMessage={successMessage}
        />
      </ProfileCard>

      {/* Security Actions */}
      <ProfileCard
        title="Security"
        description="Manage your account security"
        style={styles.card}
      >
        <Button onPress={handleResetPassword} variant="outline">
          Reset Password
        </Button>
      </ProfileCard>
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
  card: {
    backgroundColor: "#ffffff",
  },
  loadingContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  errorContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 24,
  },
  actionsRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    gap: 12,
    marginTop: 8,
  },
});
