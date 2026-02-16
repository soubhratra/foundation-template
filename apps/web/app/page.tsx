"use client";

import { StyleSheet, View } from "react-native";

import { zodResolver } from "@hookform/resolvers/zod";
import { Controller, useForm } from "react-hook-form";

import { Button, Card, Input, Text } from "@repo/ui";
import { loginSchema, type LoginInput } from "@repo/validation";
import { useAuth } from "@repo/business-logic";

const defaultValues: LoginInput = {
  email: "",
  password: "",
  remember: false,
};

export default function Home() {
  const { login } = useAuth();

  const {
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginInput>({
    resolver: zodResolver(loginSchema),
    defaultValues,
  });

  const onSubmit = handleSubmit(async (values) => {
    await login.mutateAsync(values);
  });

  return (
    <View style={styles.screen}>
      <Card style={styles.card}>
        <View style={styles.header}>
          <Text variant="title" weight="bold">
            Welcome back
          </Text>
          <Text variant="subtle" style={styles.subtitle}>
            Use your template credentials to sign in.
          </Text>
        </View>
        <View style={styles.form}>
          <Controller
            name="email"
            control={control}
            render={({ field }) => (
              <Input
                ref={field.ref}
                label="Email"
                keyboardType="email-address"
                autoCapitalize="none"
                autoComplete="email"
                value={field.value ?? ""}
                onChangeText={field.onChange}
                onBlur={field.onBlur}
                errorText={errors.email?.message}
              />
            )}
          />
          <Controller
            name="password"
            control={control}
            render={({ field }) => (
              <Input
                ref={field.ref}
                label="Password"
                secureTextEntry
                autoCapitalize="none"
                autoComplete="password"
                value={field.value ?? ""}
                onChangeText={field.onChange}
                onBlur={field.onBlur}
                errorText={errors.password?.message}
              />
            )}
          />
          {login.error ? (
            <Text variant="caption" style={styles.error}>
              {login.error.message}
            </Text>
          ) : null}
          {login.isSuccess ? (
            <Text variant="subtle" style={styles.success}>
              Login successful! Fetching user profile…
            </Text>
          ) : null}
          <Button onPress={onSubmit} loading={login.isPending} disabled={login.isPending}>
            Sign in
          </Button>
        </View>
      </Card>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    width: "100%",
    minHeight: "100%",
    alignItems: "center",
    justifyContent: "center",
    padding: 32,
    backgroundColor: "#f5f5f5",
  },
  card: {
    width: "100%",
    maxWidth: 420,
    gap: 24,
  },
  header: {
    gap: 8,
  },
  subtitle: {
    textAlign: "left",
  },
  form: {
    gap: 16,
  },
  error: {
    color: "#dc2626",
  },
  success: {
    color: "#16a34a",
  },
});
