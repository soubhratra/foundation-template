import type { ComponentProps, ReactNode } from "react";
import {
  ActivityIndicator,
  Pressable,
  PressableProps,
  StyleProp,
  StyleSheet,
  TextStyle,
  View,
  ViewStyle,
} from "react-native";

import { Text } from "./Text";
import { theme } from "../theme";

type ButtonVariant = "solid" | "outline" | "ghost";
type ButtonSize = "sm" | "md" | "lg";

type NativeChild = ComponentProps<typeof View>["children"];

export interface ButtonProps
  extends Omit<PressableProps, "style" | "children"> {
  children: NativeChild;
  loading?: boolean;
  variant?: ButtonVariant;
  size?: ButtonSize;
  leftIcon?: NativeChild;
  rightIcon?: NativeChild;
  contentStyle?: StyleProp<ViewStyle>;
  textStyle?: StyleProp<TextStyle>;
}

const sizeStyles: Record<ButtonSize, ViewStyle & { textSize: number }> = {
  sm: {
    paddingVertical: theme.spacing.xs,
    paddingHorizontal: theme.spacing.md,
    borderRadius: theme.radii.sm,
    minHeight: 40,
    textSize: 14,
  },
  md: {
    paddingVertical: theme.spacing.sm,
    paddingHorizontal: theme.spacing.lg,
    borderRadius: theme.radii.md,
    minHeight: 48,
    textSize: 16,
  },
  lg: {
    paddingVertical: theme.spacing.md,
    paddingHorizontal: theme.spacing.xl,
    borderRadius: theme.radii.lg,
    minHeight: 56,
    textSize: 18,
  },
};

const variantStyles: Record<ButtonVariant, ViewStyle> = {
  solid: {
    backgroundColor: theme.colors.primary,
    borderColor: theme.colors.primary,
    borderWidth: 1,
  },
  outline: {
    backgroundColor: "transparent",
    borderColor: theme.colors.border,
    borderWidth: 1,
  },
  ghost: {
    backgroundColor: "transparent",
    borderWidth: 0,
  },
};

const variantTextColors: Record<ButtonVariant, string> = {
  solid: theme.colors.primaryForeground,
  outline: theme.colors.text,
  ghost: theme.colors.text,
};

export function Button({
  children,
  loading = false,
  disabled,
  size = "md",
  variant = "solid",
  leftIcon,
  rightIcon,
  contentStyle,
  textStyle,
  ...rest
}: ButtonProps) {
  const baseDisabled = disabled ?? loading;

  return (
    <Pressable
      accessibilityRole="button"
      disabled={baseDisabled}
      style={({ pressed }) => [
        styles.container,
        sizeStyles[size],
        variantStyles[variant],
        pressed && !baseDisabled && styles.pressed,
        baseDisabled && styles.disabled,
        contentStyle,
      ]}
      {...rest}
    >
      {({ pressed }) => (
        <View style={styles.content}>
          {leftIcon ? <View style={styles.iconLeft}>{leftIcon}</View> : null}
          {loading ? (
            <ActivityIndicator
              color={variantTextColors[variant]}
              size="small"
              style={styles.loader}
            />
          ) : (
            <Text
              variant="body"
              weight="medium"
              style={StyleSheet.flatten([
                styles.label,
                { color: variantTextColors[variant], fontSize: sizeStyles[size].textSize },
                pressed && variant !== "solid" && styles.ghostPressedText,
                textStyle,
              ])}
            >
              {children}
            </Text>
          )}
          {rightIcon ? <View style={styles.iconRight}>{rightIcon}</View> : null}
        </View>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    borderRadius: theme.radii.md,
  },
  content: {
    flexDirection: "row",
    alignItems: "center",
  },
  label: {
    textAlign: "center",
    marginHorizontal: theme.spacing.xs,
  },
  pressed: {
    opacity: 0.9,
  },
  ghostPressedText: {
    color: theme.colors.primary,
  },
  disabled: {
    opacity: 0.5,
  },
  loader: {
    marginHorizontal: theme.spacing.xs,
  },
  iconLeft: {
    marginRight: theme.spacing.xs,
  },
  iconRight: {
    marginLeft: theme.spacing.xs,
  },
});
