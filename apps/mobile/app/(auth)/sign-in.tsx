import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Pressable,
  StyleSheet,
  Switch,
  View,
} from "react-native";

import { useLocalSearchParams, useRouter } from "expo-router";
import { useForm } from "react-hook-form";

import { useAuth } from "@repo/business-logic";
import {
  AuthFooter,
  AuthForm,
  AuthFormField,
  type AuthFormStatus,
} from "@/components/auth";
import { Input, Text, theme } from "@repo/ui";
import {
  createZodFormOptions,
  loginSchema,
  type LoginInput,
} from "@repo/validation";

export default function SignInScreen() {
  const [status, setStatus] = useState<AuthFormStatus | null>(null);
  const router = useRouter();
  const params = useLocalSearchParams();
  const prefilledEmail = useMemo(() => resolveEmailParam(params.email), [params.email]);
  const form = useForm<LoginInput>(
    createZodFormOptions(loginSchema, {
      defaultValues: {
        email: prefilledEmail ?? "",
        password: "",
        remember: false,
      },
    }),
  );
  const { loginWithJwt } = useAuth();

  useEffect(() => {
    if (prefilledEmail && form.getValues("email") !== prefilledEmail) {
      form.setValue("email", prefilledEmail);
    }
  }, [prefilledEmail, form]);

  const handleSubmit = useCallback(
    async (values: LoginInput) => {
      setStatus(null);
      try {
        await loginWithJwt.mutateAsync(values);
        setStatus({
          variant: "success",
          title: "Signed in",
          description: "Redirecting you to your workspace…",
        });
        router.replace("/(tabs)/home");
      } catch (error) {
        const message = error instanceof Error ? error.message : "Unable to sign in right now.";
        setStatus({
          variant: "error",
          title: "Unable to sign in",
          description: message,
        });
      }
    },
    [loginWithJwt, router],
  );

  return (
    <AuthForm
      form={form}
      submitLabel="Access workspace"
      isSubmitting={loginWithJwt.isPending}
      onSubmit={handleSubmit}
      status={status}
      footer={
        <AuthFooter
          links={[
            {
              prefix: "New here?",
              label: "Create an account",
              href: "/(auth)/sign-up",
            },
            {
              prefix: "Need help?",
              label: "Reset password",
              href: "/(auth)/reset-password",
            },
          ]}
        />
      }
    >
      <AuthFormField
        control={form.control}
        name="email"
        label="Email"
        inputProps={{
          keyboardType: "email-address",
          autoCapitalize: "none",
          autoComplete: "email",
          textContentType: "emailAddress",
          placeholder: "ada@lovelace.dev",
        }}
      />
      <AuthFormField control={form.control} name="password">
        {({ field, error }) => (
          <View style={styles.passwordField}>
            <View style={styles.passwordHeader}>
              <Text variant="subtle" weight="medium">
                Password
              </Text>
              <Text
                variant="caption"
                weight="bold"
                style={styles.passwordHint}
                onPress={() => router.replace("/(auth)/reset-password")}
              >
                Forgot?
              </Text>
            </View>
            <Input
              value={field.value}
              onBlur={field.onBlur}
              onChangeText={field.onChange}
              placeholder="••••••••"
              secureTextEntry
              autoCapitalize="none"
              autoComplete="password"
              textContentType="password"
              errorText={error}
            />
          </View>
        )}
      </AuthFormField>
      <AuthFormField control={form.control} name="remember">
        {({ field }) => (
          <Pressable
            onPress={() => field.onChange(!field.value)}
            style={styles.toggleRow}
            accessibilityRole="button"
            accessibilityLabel="Stay signed in"
          >
            <View style={styles.toggleCopy}>
              <Text variant="subtle" weight="bold">
                Stay signed in
              </Text>
              <Text variant="caption" style={styles.toggleDescription}>
                Store your JWT tokens securely on this device.
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

function resolveEmailParam(value?: string | string[]): string | undefined {
  if (Array.isArray(value)) {
    return value[0];
  }
  return typeof value === "string" && value.trim().length > 0 ? value.trim() : undefined;
}

const styles = StyleSheet.create({
  passwordField: {
    gap: theme.spacing.xs,
  },
  passwordHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  passwordHint: {
    color: theme.colors.primary,
  },
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
});
