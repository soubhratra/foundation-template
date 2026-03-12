import { useCallback, useEffect, useMemo, useState } from "react";
import { Platform, Pressable, StyleSheet, Switch, View } from "react-native";

import * as AppleAuthentication from "expo-apple-authentication";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useForm } from "react-hook-form";

import { useAuth, useAuthContext, USER_QUERY_KEY } from "@repo/business-logic";
import { AuthFooter, AuthForm, AuthFormField, type AuthFormStatus } from "@/components/auth";
import { Input, Text, theme } from "@repo/ui";
import { createZodFormOptions, loginSchema, type LoginInput } from "@repo/validation";

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
  const { tokenStorage, queryClient } = useAuthContext();

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

  const handleAppleSignIn = useCallback(async () => {
    try {
      const credential = await AppleAuthentication.signInAsync({
        requestedScopes: [
          AppleAuthentication.AppleAuthenticationScope.FULL_NAME,
          AppleAuthentication.AppleAuthenticationScope.EMAIL,
        ],
      });

      if (!credential.identityToken) return;

      const response = await fetch(`${process.env.EXPO_PUBLIC_API_URL}/api/v1/auth/apple/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          identity_token: credential.identityToken,
          full_name: credential.fullName?.givenName ?? null,
        }),
      });

      if (response.ok) {
        const tokens = (await response.json()) as { access: string; refresh: string };
        await tokenStorage.setTokens({
          accessToken: tokens.access,
          refreshToken: tokens.refresh,
        });
        await queryClient.invalidateQueries({ queryKey: USER_QUERY_KEY });
        router.replace("/(tabs)/home");
      } else {
        setStatus({
          variant: "error",
          title: "Apple Sign In failed",
          description: "Please try again.",
        });
      }
    } catch (error: unknown) {
      // ERR_CANCELED: user dismissed the Apple sheet — silent dismiss
      if (error instanceof Error && error.message.includes("ERR_CANCELED")) {
        return;
      }
      setStatus({
        variant: "error",
        title: "Apple Sign In failed",
        description: "Please try again.",
      });
    }
  }, [router, tokenStorage, queryClient]);

  return (
    <AuthForm
      form={form}
      submitLabel="Access workspace"
      isSubmitting={loginWithJwt.isPending}
      onSubmit={handleSubmit}
      status={status}
      footer={
        <>
          {/* SOCIAL AUTH MODULE */}
          {Platform.OS === "ios" && (
            <View style={styles.socialContainer}>
              <View style={styles.divider}>
                <View style={styles.dividerLine} />
                <Text style={styles.dividerText}>or</Text>
                <View style={styles.dividerLine} />
              </View>
              <AppleAuthentication.AppleAuthenticationButton
                buttonType={AppleAuthentication.AppleAuthenticationButtonType.SIGN_IN}
                buttonStyle={AppleAuthentication.AppleAuthenticationButtonStyle.BLACK}
                cornerRadius={8}
                style={styles.appleButton}
                onPress={handleAppleSignIn}
              />
            </View>
          )}
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
        </>
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
  socialContainer: {
    marginTop: 16,
  },
  appleButton: {
    width: "100%",
    height: 44,
  },
  divider: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 12,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: theme.colors.border,
  },
  dividerText: {
    marginHorizontal: 8,
    fontSize: 12,
    color: theme.colors.textMuted,
  },
});
