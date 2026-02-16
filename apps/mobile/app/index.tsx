import { StyleSheet, View, ScrollView } from "react-native";

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

export default function HomeScreen() {
  const { loginWithJwt } = useAuth();

  const {
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginInput>({
    resolver: zodResolver(loginSchema),
    defaultValues,
  });

  const onSubmit = handleSubmit(async (values) => {
    await loginWithJwt.mutateAsync(values);
  });

  return (
    <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
      <Card style={styles.card}>
        <View style={styles.header}>
          <Text variant="title" weight="bold">
            Sign in on mobile
          </Text>
          <Text variant="subtle">Tokens are stored securely with expo-secure-store.</Text>
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
          {loginWithJwt.error ? (
            <Text variant="caption" style={styles.error}>
              {loginWithJwt.error.message}
            </Text>
          ) : null}
          {loginWithJwt.isSuccess ? (
            <Text variant="subtle" style={styles.success}>
              Signed in successfully. Tokens persisted to secure storage.
            </Text>
          ) : null}
          <Button onPress={onSubmit} loading={loginWithJwt.isPending} disabled={loginWithJwt.isPending}>
            Continue
          </Button>
        </View>
      </Card>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  scroll: {
    flexGrow: 1,
    padding: 24,
    justifyContent: "center",
  },
  card: {
    width: "100%",
    gap: 24,
  },
  header: {
    gap: 8,
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
