import { type ReactNode } from "react";
import { StyleSheet, View } from "react-native";

import { Card, Text, theme } from "@repo/ui";

import { ToggleRow } from "./switch-toggle";

export interface PreferenceToggle {
  key: string;
  label: string;
  description?: string;
}

export interface PreferencesCardProps {
  /** Card title */
  title: string;
  /** Description text */
  description?: string;
  /** List of toggles to display */
  toggles: PreferenceToggle[];
  /** Current values keyed by toggle key */
  values: Record<string, boolean>;
  /** Callback when a toggle value changes */
  onToggleChange: (key: string, value: boolean) => void;
  /** Whether the toggles are disabled */
  disabled?: boolean;
  /** Optional footer content */
  footer?: ReactNode;
}

/**
 * Card component for displaying and managing toggle preferences.
 * Pairs with usePreferences hook for persistence.
 */
export function PreferencesCard({
  title,
  description,
  toggles,
  values,
  onToggleChange,
  disabled,
  footer,
}: PreferencesCardProps) {
  return (
    <Card style={styles.card}>
      <Text variant="title" weight="bold">
        {title}
      </Text>

      {description && (
        <Text variant="subtle" style={styles.description}>
          {description}
        </Text>
      )}

      <View style={styles.togglesContainer}>
        {toggles.map((toggle) => (
          <ToggleRow
            key={toggle.key}
            toggle={toggle}
            value={values[toggle.key] ?? false}
            onValueChange={onToggleChange}
            disabled={disabled}
          />
        ))}
      </View>

      {footer}
    </Card>
  );
}

/**
 * Standard notification preference toggles based on notificationPrefsSchema.
 * TODO: When backend implements /api/v1ferences endpoint,
 * these should sync/users/pre with the server instead of persisting locally only.
 */
export const NOTIFICATION_PREFERENCE_TOGGLES: PreferenceToggle[] = [
  {
    key: "productEmails",
    label: "Product Emails",
    description: "Receive updates about new features and improvements",
  },
  {
    key: "securityAlerts",
    label: "Security Alerts",
    description: "Get notified about account security events",
  },
  {
    key: "marketingEmails",
    label: "Marketing",
    description: "Receive promotional content and offers",
  },
  {
    key: "smsAlerts",
    label: "SMS Alerts",
    description: "Get important notifications via text message",
  },
];

const styles = StyleSheet.create({
  card: {
    gap: theme.spacing.md,
  },
  description: {
    marginTop: -theme.spacing.xs,
  },
  togglesContainer: {
    marginTop: theme.spacing.sm,
  },
});
