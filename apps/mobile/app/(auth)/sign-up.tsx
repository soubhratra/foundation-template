import { useState } from "react";
import { Pressable, StyleSheet, Switch, View } from "react-native";

import { useRouter } from "expo-router";
import { useForm } from "react-hook-form";

import {
  AuthFooter,
  AuthForm,
  AuthFormField,
  type AuthFormStatus,
} from "@/components/auth";
import { Button, Text, theme } from "@repo/ui";
import {
  createZodFormOptions,
  signupSchema,
  type SignupInput,
} from "@repo/validation";

import { useCreateAccountMutation } from "@/lib/api/auth";

const defaultValues: SignupInput = {
  name: "",
  email: "",
  password: "",
  confirmPassword: "",
  marketingOptIn: true,
};

export default function SignUpScreen() {
  const router = useRouter();
  const [status, setStatus] = useState<AuthFormStatus | null>(null);
  const [lastEmail, setLastEmail] = useState<string | null>(null);
  const form = useForm<SignupInput>(createZodFormOptions(signupSchema, { defaultValues }));
  const createAccount = useCreateAccountMutation();

  const handleSubmit = async (values: SignupInput) => {
    setStatus(null);
    try {
      await createAccount.mutateAsync(values);
      form.reset({ ...defaultValues, email: values.email });
      setLastEmail(values.email);
      setStatus({
        variant: "success",
        title: "Verify your email",
        description: "Check your inbox for a verification link to finish onboarding.",
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unable to create your account.";
      setStatus({
        variant: "error",
        title: "Signup failed",
        description: message,
      });
    }
  };

  const footer = (
    <View style={styles.formFooter}>
      {status?.variant === "success" ? (
        <Button
          variant="outline"
          size="sm"
          onPress={() =>
            router.replace({
              pathname: "/(auth)/sign-in",
              params: lastEmail ? { email: lastEmail } : undefined,
            })
          }
        >
          Return to sign in
        </Button>
      ) : null}
      <AuthFooter
        links={[
          { prefix: "Already a member?", label: "Sign in", href: "/(auth)/sign-in" },
          { prefix: "Need help?", label: "Reset password", href: "/(auth)/reset-password" },
        ]}
      />
    </View>
  );

  return (
    <AuthForm
      form={form}
      submitLabel="Create account"
      isSubmitting={createAccount.isPending}
      onSubmit={handleSubmit}
      status={status}
      footer={footer}
    >
      <AuthFormField
        control={form.control}
        name="name"
        label="Full name"
        inputProps={{ placeholder: "Ada Lovelace" }}
      />
      <AuthFormField
        control={form.control}
        name="email"
        label="Email"
        inputProps={{
          keyboardType: "email-address",
          autoCapitalize: "none",
          autoComplete: "email",
          textContentType: "emailAddress",
          placeholder: "founder@workspace.dev",
        }}
      />
      <AuthFormField
        control={form.control}
        name="password"
        label="Password"
        inputProps={{
          secureTextEntry: true,
          autoCapitalize: "none",
          autoComplete: "new-password",
          textContentType: "newPassword",
          placeholder: "••••••••",
        }}
      />
      <AuthFormField
        control={form.control}
        name="confirmPassword"
        label="Confirm password"
        inputProps={{
          secureTextEntry: true,
          autoCapitalize: "none",
          autoComplete: "new-password",
          textContentType: "newPassword",
          placeholder: "••••••••",
        }}
      />
      <AuthFormField control={form.control} name="marketingOptIn">
        {({ field }) => (
          <Pressable
            onPress={() => field.onChange(!field.value)}
            style={styles.toggleRow}
            accessibilityRole="button"
            accessibilityLabel="Toggle product updates"
          >
            <View style={styles.toggleCopy}>
              <Text variant="subtle" weight="bold">
                Product updates
              </Text>
              <Text variant="caption" style={styles.toggleDescription}>
                Receive onboarding tips and release highlights occasionally.
              </Text>
            </View>
            <Switch
              value={Boolean(field.value)}
              onValueChange={field.onChange}
              trackColor={{ true: theme.colors.primary, false: theme.colors.border }}
            />
          </Pressable>
        )}
      </AuthFormField>
    </AuthForm>
  );
}

const styles = StyleSheet.create({
  toggleRow: {
    borderRadius: theme.radii.md,
    borderWidth: 1,
    borderColor: theme.colors.border,
    padding: theme.spacing.md,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    gap: theme.spacing.md,
  },
  toggleCopy: {
    flex: 1,
    gap: theme.spacing.xs,
  },
  toggleDescription: {
    color: theme.colors.muted,
  },
  formFooter: {
    width: "100%",
    gap: theme.spacing.sm,
  },
});
