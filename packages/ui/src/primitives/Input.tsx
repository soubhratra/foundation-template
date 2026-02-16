import { forwardRef, useState } from "react";
import {
  StyleProp,
  StyleSheet,
  TextInput,
  TextInputProps,
  TextStyle,
  View,
  ViewStyle,
} from "react-native";

import { Text } from "./Text";
import { theme } from "../theme";

export interface InputProps extends Omit<TextInputProps, "style"> {
  label?: string;
  helperText?: string;
  errorText?: string;
  containerStyle?: StyleProp<ViewStyle>;
  inputStyle?: StyleProp<TextStyle>;
  labelStyle?: StyleProp<TextStyle>;
  helperTextStyle?: StyleProp<TextStyle>;
  errorTextStyle?: StyleProp<TextStyle>;
}

export const Input = forwardRef<TextInput, InputProps>(function Input(
  {
    label,
    helperText,
    errorText,
    containerStyle,
    inputStyle,
    labelStyle,
    helperTextStyle,
    errorTextStyle,
    onFocus,
    onBlur,
    multiline,
    ...rest
  },
  ref,
) {
  const [focused, setFocused] = useState(false);

  const handleFocus: NonNullable<TextInputProps["onFocus"]> = (event) => {
    setFocused(true);
    onFocus?.(event);
  };

  const handleBlur: NonNullable<TextInputProps["onBlur"]> = (event) => {
    setFocused(false);
    onBlur?.(event);
  };

  const borderColor = errorText
    ? theme.colors.danger
    : focused
      ? theme.colors.focus
      : theme.colors.border;

  return (
    <View style={StyleSheet.flatten([styles.wrapper, containerStyle])}>
      {label ? (
        <Text variant="subtle" style={StyleSheet.flatten([styles.label, labelStyle])}>
          {label}
        </Text>
      ) : null}
      <View
        style={StyleSheet.flatten([
          styles.inputContainer,
          { borderColor, minHeight: multiline ? theme.input.height * 1.5 : theme.input.height },
          focused && styles.focusRing,
        ])}
      >
        <TextInput
          ref={ref}
          style={StyleSheet.flatten([styles.input, inputStyle])}
          placeholderTextColor={theme.colors.textMuted}
          onFocus={handleFocus}
          onBlur={handleBlur}
          multiline={multiline}
          {...rest}
        />
      </View>
      {errorText ? (
        <Text
          variant="caption"
          style={StyleSheet.flatten([styles.errorText, errorTextStyle])}
        >
          {errorText}
        </Text>
      ) : helperText ? (
        <Text
          variant="caption"
          style={StyleSheet.flatten([styles.helperText, helperTextStyle])}
        >
          {helperText}
        </Text>
      ) : null}
    </View>
  );
});

const styles = StyleSheet.create({
  wrapper: {
    width: "100%",
  },
  label: {
    color: theme.colors.text,
    marginBottom: theme.spacing.xs,
  },
  inputContainer: {
    borderWidth: 1,
    borderRadius: theme.radii.md,
    backgroundColor: theme.colors.surface,
    paddingHorizontal: theme.spacing.md,
    justifyContent: "center",
  },
  focusRing: {
    shadowColor: theme.colors.focus,
    shadowOpacity: 0.45,
    shadowOffset: { width: 0, height: 0 },
    shadowRadius: 6,
    elevation: 2,
  },
  input: {
    color: theme.colors.text,
    fontSize: theme.typography.bodySize,
    paddingVertical: theme.spacing.xs,
  },
  helperText: {
    color: theme.colors.muted,
    marginTop: theme.spacing.xs,
  },
  errorText: {
    color: theme.colors.danger,
    marginTop: theme.spacing.xs,
  },
});
