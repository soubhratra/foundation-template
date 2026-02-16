"use client";

import { useForm, Controller, type SubmitHandler } from "react-hook-form";
import { StyleSheet, View } from "react-native";
import { zodResolver } from "@hookform/resolvers/zod";

import { Button, Input, Text } from "@repo/ui";
import {
  updateProfileSchema,
  type UpdateProfileInput,
} from "@repo/validation";

export interface ProfileFormProps {
  /** Default values for the form */
  defaultValues?: Partial<UpdateProfileInput>;
  /** Submit handler called with validated form data */
  onSubmit: (data: UpdateProfileInput) => Promise<void>;
  /** Whether the form is currently submitting */
  isSubmitting?: boolean;
  /** External error message to display */
  errorMessage?: string;
  /** Success message to display */
  successMessage?: string;
}

/**
 * Profile form component using updateProfileSchema.
 * Exposes props for default values, submit handler, and mutation state
 * so the profile screen simply plugs in API logic.
 */
export function ProfileForm({
  defaultValues,
  onSubmit,
  isSubmitting = false,
  errorMessage,
  successMessage,
}: ProfileFormProps) {
  const {
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<UpdateProfileInput>({
    resolver: zodResolver(updateProfileSchema),
    defaultValues: {
      fullName: defaultValues?.fullName ?? "",
      timezone: defaultValues?.timezone ?? "UTC",
    },
  });

  const handleFormSubmit: SubmitHandler<UpdateProfileInput> = async (data) => {
    await onSubmit(data);
  };

  return (
    <View style={styles.container}>
      {/* Full Name Field */}
      <Controller
        name="fullName"
        control={control}
        render={({ field: { onChange, onBlur, value, ref } }) => (
          <Input
            ref={ref}
            label="Full Name"
            value={value}
            onChangeText={onChange}
            onBlur={onBlur}
            errorText={errors.fullName?.message}
            placeholder="Enter your full name"
            autoCapitalize="words"
            autoComplete="name"
            textContentType="name"
          />
        )}
      />

      {/* Timezone Field */}
      <Controller
        name="timezone"
        control={control}
        render={({ field: { onChange, onBlur, value, ref } }) => (
          <Input
            ref={ref}
            label="Timezone"
            value={value}
            onChangeText={onChange}
            onBlur={onBlur}
            errorText={errors.timezone?.message}
            placeholder="e.g., America/New_York"
            autoCapitalize="none"
            autoCorrect={false}
            helperText="Enter a valid IANA timezone (e.g., UTC, America/Los_Angeles)"
          />
        )}
      />

      {/* Error Message */}
      {errorMessage && (
        <View style={styles.messageContainer}>
          <Text variant="caption" style={styles.errorText}>
            {errorMessage}
          </Text>
        </View>
      )}

      {/* Success Message */}
      {successMessage && (
        <View style={styles.messageContainer}>
          <Text variant="caption" style={styles.successText}>
            {successMessage}
          </Text>
        </View>
      )}

      {/* Submit Button */}
      <Button
        onPress={handleSubmit(handleFormSubmit)}
        loading={isSubmitting}
        disabled={isSubmitting}
      >
        {isSubmitting ? "Saving..." : "Save Changes"}
      </Button>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: 16,
  },
  messageContainer: {
    marginTop: -8,
  },
  errorText: {
    color: "#dc2626",
  },
  successText: {
    color: "#16a34a",
  },
});
