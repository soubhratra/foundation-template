import { type ReactNode } from "react";
import { StyleSheet, View, ViewStyle } from "react-native";

import { Button, Card, Text, theme, type ButtonProps } from "@repo/ui";

export interface ProfileCardProps {
  /** Card title */
  title: string;
  /** Optional description text */
  description?: string;
  /** Optional description slot for more complex content */
  descriptionSlot?: ReactNode;
  /** Action button configuration */
  action?: {
    label: string;
    onPress: ButtonProps["onPress"];
    variant?: ButtonProps["variant"];
    disabled?: boolean;
    loading?: boolean;
  };
  /** Additional card styling */
  style?: ViewStyle;
  /** Card content */
  children?: ReactNode;
}

/**
 * Shared profile card component that wraps @repo/ui primitives
 * with consistent padding and optional description slot.
 */
export function ProfileCard({
  title,
  description,
  descriptionSlot,
  action,
  style,
  children,
}: ProfileCardProps) {
  return (
    <Card style={[styles.card, style]}>
      <Text variant="title" weight="bold">
        {title}
      </Text>

      {description && (
        <Text variant="subtle" style={styles.description}>
          {description}
        </Text>
      )}

      {descriptionSlot}

      {children}

      {action && (
        <Button
          onPress={action.onPress}
          variant={action.variant ?? "solid"}
          disabled={action.disabled}
          loading={action.loading}
        >
          {action.label}
        </Button>
      )}
    </Card>
  );
}

export interface ProfileCardSectionProps {
  title: string;
  children: ReactNode;
  style?: ViewStyle;
}

/**
 * Section within a profile card for grouping related content.
 */
export function ProfileCardSection({ title, children, style }: ProfileCardSectionProps) {
  return (
    <View style={[styles.section, style]}>
      <Text variant="subtle" weight="medium" style={styles.sectionTitle}>
        {title}
      </Text>
      {children}
    </View>
  );
}

export interface ProfileCardRowProps {
  label: string;
  value?: string;
  children?: ReactNode;
  style?: ViewStyle;
}

/**
 * Row within a profile card section for label/value pairs.
 */
export function ProfileCardRow({ label, value, children, style }: ProfileCardRowProps) {
  return (
    <View style={[styles.row, style]}>
      <Text variant="caption" style={styles.rowLabel}>
        {label}
      </Text>
      {value ? (
        <Text variant="body" style={styles.rowValue}>
          {value}
        </Text>
      ) : (
        children
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    gap: theme.spacing.md,
  },
  description: {
    marginTop: -theme.spacing.xs,
  },
  section: {
    gap: theme.spacing.sm,
  },
  sectionTitle: {
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: theme.spacing.sm,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: theme.colors.border,
  },
  rowLabel: {
    flex: 1,
  },
  rowValue: {
    flex: 2,
    textAlign: "right",
  },
});
