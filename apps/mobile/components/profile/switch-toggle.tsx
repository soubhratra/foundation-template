import {
  Switch,
  SwitchProps as RNSwitchProps,
  StyleSheet,
  View,
} from "react-native";

import { Text, theme } from "@repo/ui";

export interface SwitchToggleProps extends Omit<RNSwitchProps, "onValueChange"> {
  /** Label displayed next to the switch */
  label: string;
  /** Optional description text */
  description?: string;
  /** Callback when value changes */
  onValueChange?: (value: boolean) => void;
}

/**
 * Toggle switch component with label and optional description.
 */
export function SwitchToggle({
  label,
  description,
  value,
  onValueChange,
  disabled,
  ...rest
}: SwitchToggleProps) {
  return (
    <View style={styles.container}>
      <View style={styles.labelContainer}>
        <Text variant="body" disabled={disabled}>
          {label}
        </Text>
        {description && (
          <Text variant="caption" style={styles.description}>
            {description}
          </Text>
        )}
      </View>
      <Switch
        value={value}
        onValueChange={onValueChange}
        disabled={disabled}
        trackColor={{ false: theme.colors.muted, true: theme.colors.primary }}
        thumbColor={theme.colors.surface}
        ios_backgroundColor={theme.colors.muted}
        {...rest}
      />
    </View>
  );
}

export interface ToggleRowProps {
  /** The toggle configuration */
  toggle: {
    key: string;
    label: string;
    description?: string;
  };
  /** Current value */
  value: boolean;
  /** Callback when value changes */
  onValueChange: (key: string, value: boolean) => void;
  /** Whether the toggle is disabled */
  disabled?: boolean;
}

/**
 * Single toggle row for use in a preferences list.
 */
export function ToggleRow({ toggle, value, onValueChange, disabled }: ToggleRowProps) {
  return (
    <View style={styles.row}>
      <SwitchToggle
        label={toggle.label}
        description={toggle.description}
        value={value}
        onValueChange={(newValue) => onValueChange(toggle.key, newValue)}
        disabled={disabled}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: theme.spacing.sm,
  },
  labelContainer: {
    flex: 1,
    marginRight: theme.spacing.md,
  },
  description: {
    marginTop: 2,
    opacity: 0.7,
  },
  row: {
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: theme.colors.border,
  },
});
