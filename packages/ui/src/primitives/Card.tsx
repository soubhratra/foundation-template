import { forwardRef } from "react";
import {
  StyleProp,
  StyleSheet,
  View,
  ViewProps,
  ViewStyle,
} from "react-native";

import { theme } from "../theme";

export interface CardProps extends ViewProps {
  padding?: "sm" | "md" | "lg";
  style?: StyleProp<ViewStyle>;
}

export const Card = forwardRef<View, CardProps>(function Card(
  { children, padding = "md", style, ...rest },
  ref,
) {
  return (
    <View
      ref={ref}
      style={StyleSheet.flatten([
        styles.container,
        paddingStyles[padding],
        style,
      ])}
      {...rest}
    >
      {children}
    </View>
  );
});

const paddingStyles: Record<NonNullable<CardProps["padding"]>, ViewStyle> = {
  sm: { padding: theme.spacing.sm },
  md: { padding: theme.spacing.md },
  lg: { padding: theme.spacing.lg },
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radii.lg,
    borderWidth: 1,
    borderColor: theme.colors.border,
    shadowColor: "#000000",
    shadowOpacity: 0.15,
    shadowOffset: { width: 0, height: 8 },
    shadowRadius: 16,
    elevation: 4,
  },
});
