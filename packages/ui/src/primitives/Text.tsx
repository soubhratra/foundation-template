import { forwardRef } from "react";
import {
  Text as RNText,
  TextProps as RNTextProps,
  StyleSheet,
  StyleProp,
  TextStyle,
} from "react-native";

import { theme } from "../theme";

type TextVariant = "title" | "body" | "subtle" | "caption";

export interface TextProps extends RNTextProps {
  variant?: TextVariant;
  weight?: "regular" | "medium" | "bold";
  style?: StyleProp<TextStyle>;
}

const variantStyles: Record<TextVariant, TextStyle> = {
  title: {
    fontSize: theme.typography.titleSize,
    color: theme.colors.text,
  },
  body: {
    fontSize: theme.typography.bodySize,
    color: theme.colors.text,
  },
  subtle: {
    fontSize: theme.typography.subtleSize,
    color: theme.colors.textMuted,
  },
  caption: {
    fontSize: theme.typography.captionSize,
    color: theme.colors.textMuted,
    letterSpacing: theme.typography.letterSpacing,
  },
};

const weightMap: Record<NonNullable<TextProps["weight"]>, TextStyle> = {
  regular: {
    fontFamily: theme.typography.fontFamily,
    fontWeight: "400",
  },
  medium: {
    fontFamily: theme.typography.fontFamily,
    fontWeight: "500",
  },
  bold: {
    fontFamily: theme.typography.fontFamily,
    fontWeight: "600",
  },
};

export const Text = forwardRef<RNText, TextProps>(function Text(
  { variant = "body", weight = "regular", style, ...rest },
  ref,
) {
  return (
    <RNText
      ref={ref}
      style={StyleSheet.flatten([
        variantStyles[variant],
        weightMap[weight],
        style,
      ])}
      {...rest}
    />
  );
});
