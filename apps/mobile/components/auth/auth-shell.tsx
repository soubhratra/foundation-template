import type { ReactNode } from "react";
import { SafeAreaView, ScrollView, StyleSheet, View } from "react-native";

import { StatusBar } from "expo-status-bar";

import { Card, Text, theme } from "@repo/ui";

export type AuthMessageVariant = "success" | "error";

export interface AuthMessageProps {
  readonly variant: AuthMessageVariant;
  readonly title?: string;
  readonly description?: string;
}

export interface AuthShellProps {
  readonly eyebrow?: string;
  readonly title: string;
  readonly description?: string;
  readonly children: ReactNode;
  readonly footer?: ReactNode;
}

export function AuthShell({ eyebrow, title, description, footer, children }: AuthShellProps) {
  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar style="dark" />
      <ScrollView
        keyboardShouldPersistTaps="handled"
        contentContainerStyle={styles.scrollContent}
      >
        <View style={styles.header}>
          {eyebrow ? (
            <Text variant="caption" weight="medium" style={styles.eyebrow}>
              {eyebrow}
            </Text>
          ) : null}
          <Text variant="title" weight="bold">
            {title}
          </Text>
          {description ? (
            <Text variant="subtle" style={styles.description}>
              {description}
            </Text>
          ) : null}
        </View>
        <Card style={styles.card}>{children}</Card>
        {footer ? <View style={styles.footer}>{footer}</View> : null}
      </ScrollView>
    </SafeAreaView>
  );
}

export function AuthMessage({ variant, title, description }: AuthMessageProps) {
  if (!title && !description) {
    return null;
  }

  const isSuccess = variant === "success";
  const containerStyle = isSuccess ? styles.successBanner : styles.errorBanner;
  const badgeStyle = isSuccess ? styles.successBadge : styles.errorBadge;
  const badgeLabel = isSuccess ? "Success" : "Heads up";

  return (
    <View style={[styles.banner, containerStyle]}>
      <View style={[styles.badge, badgeStyle]}>
        <Text variant="caption" weight="bold" style={styles.badgeText}>
          {badgeLabel}
        </Text>
      </View>
      <View style={styles.bannerContent}>
        {title ? (
          <Text variant="body" weight="bold" style={styles.bannerTitle}>
            {title}
          </Text>
        ) : null}
        {description ? (
          <Text variant="caption" style={styles.bannerDescription}>
            {description}
          </Text>
        ) : null}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  scrollContent: {
    flexGrow: 1,
    padding: theme.spacing.xl,
    gap: theme.spacing.lg,
  },
  header: {
    gap: theme.spacing.xs,
  },
  eyebrow: {
    textTransform: "uppercase",
    letterSpacing: 1.2,
    color: theme.colors.muted,
  },
  description: {
    color: theme.colors.muted,
  },
  card: {
    padding: theme.spacing.xl,
    gap: theme.spacing.md,
  },
  footer: {
    gap: theme.spacing.sm,
  },
  banner: {
    borderRadius: theme.radii.md,
    padding: theme.spacing.md,
    gap: theme.spacing.sm,
    borderWidth: 1,
    borderColor: theme.colors.border,
  },
  bannerContent: {
    gap: theme.spacing.xs,
  },
  bannerTitle: {
    color: theme.colors.text,
  },
  bannerDescription: {
    color: theme.colors.muted,
  },
  successBanner: {
    backgroundColor: "rgba(34,197,94,0.12)",
    borderColor: "rgba(34,197,94,0.4)",
  },
  errorBanner: {
    backgroundColor: "rgba(239,68,68,0.12)",
    borderColor: "rgba(239,68,68,0.4)",
  },
  badge: {
    alignSelf: "flex-start",
    paddingHorizontal: theme.spacing.sm,
    paddingVertical: theme.spacing.xs / 1.5,
    borderRadius: theme.radii.pill,
  },
  successBadge: {
    backgroundColor: "rgba(34,197,94,0.16)",
  },
  errorBadge: {
    backgroundColor: "rgba(239,68,68,0.16)",
  },
  badgeText: {
    color: theme.colors.text,
  },
});
