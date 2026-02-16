import type { ReactNode } from "react";
import { StyleSheet, View } from "react-native";

import {
  Controller,
  FormProvider,
  type Control,
  type ControllerRenderProps,
  type FieldPath,
  type FieldValues,
  type SubmitHandler,
  type UseFormReturn,
} from "react-hook-form";

import { Button, Input, type InputProps, Text, theme } from "@repo/ui";

import { AuthMessage, type AuthMessageProps } from "./auth-shell";

export type AuthFormStatus = AuthMessageProps;

interface AuthFormProps<TFieldValues extends FieldValues> {
  readonly form: UseFormReturn<TFieldValues>;
  readonly onSubmit: SubmitHandler<TFieldValues>;
  readonly submitLabel: string;
  readonly children: ReactNode;
  readonly status?: AuthFormStatus | null;
  readonly isSubmitting?: boolean;
  readonly footer?: ReactNode;
}

export function AuthForm<TFieldValues extends FieldValues>({
  form,
  onSubmit,
  submitLabel,
  children,
  status,
  isSubmitting,
  footer,
}: AuthFormProps<TFieldValues>) {
  return (
    <FormProvider {...form}>
      <View style={styles.container}>
        {status ? <AuthMessage {...status} /> : null}
        <View style={styles.fields}>{children}</View>
        <Button
          onPress={form.handleSubmit(onSubmit)}
          loading={Boolean(isSubmitting)}
          disabled={Boolean(isSubmitting)}
        >
          {isSubmitting ? "Working…" : submitLabel}
        </Button>
        {footer ? <View style={styles.footer}>{footer}</View> : null}
      </View>
    </FormProvider>
  );
}

type BaseInputProps = Omit<
  InputProps,
  | "value"
  | "onChangeText"
  | "onBlur"
  | "label"
  | "helperText"
  | "errorText"
  | "containerStyle"
>;

interface RenderProps<TFieldValues extends FieldValues, TName extends FieldPath<TFieldValues>> {
  readonly field: ControllerRenderProps<TFieldValues, TName>;
  readonly error?: string;
}

interface AuthFormFieldProps<TFieldValues extends FieldValues, TName extends FieldPath<TFieldValues>> {
  readonly control: Control<TFieldValues>;
  readonly name: TName;
  readonly label?: string;
  readonly helperText?: string;
  readonly inputProps?: BaseInputProps;
  readonly children?: (props: RenderProps<TFieldValues, TName>) => ReactNode;
}

export function AuthFormField<
  TFieldValues extends FieldValues,
  TName extends FieldPath<TFieldValues>,
>({ control, name, label, helperText, inputProps, children }: AuthFormFieldProps<TFieldValues, TName>) {
  return (
    <Controller
      control={control}
      name={name}
      render={({ field, fieldState }) => {
        if (children) {
          return <>{children({ field, error: fieldState.error?.message })}</>;
        }

        return (
          <Input
            label={label}
            helperText={helperText}
            errorText={fieldState.error?.message}
            value={(field.value as string) ?? ""}
            onBlur={field.onBlur}
            onChangeText={field.onChange}
            {...inputProps}
          />
        );
      }}
    />
  );
}

export interface AuthFormHintProps {
  readonly title?: string;
  readonly description: string;
}

export function AuthFormHint({ title, description }: AuthFormHintProps) {
  return (
    <View style={styles.hint}>
      {title ? (
        <Text variant="body" weight="bold">
          {title}
        </Text>
      ) : null}
      <Text variant="caption" style={styles.hintDescription}>
        {description}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: theme.spacing.lg,
  },
  fields: {
    gap: theme.spacing.md,
  },
  footer: {
    gap: theme.spacing.xs,
    alignItems: "center",
  },
  hint: {
    borderRadius: theme.radii.md,
    borderWidth: 1,
    borderStyle: "dashed",
    borderColor: theme.colors.border,
    padding: theme.spacing.md,
    gap: theme.spacing.xs,
  },
  hintDescription: {
    color: theme.colors.muted,
  },
});
