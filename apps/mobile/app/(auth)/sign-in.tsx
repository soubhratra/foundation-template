import { StyleSheet, View } from "react-native";

import { Link, router } from "expo-router";

import { Button, Card, Text } from "@repo/ui";

export default function SignInScreen() {
  const handleContinue = () => {
    router.replace("/(tabs)/home");
  };

  return (
    <Card style={styles.card}>
      <View style={styles.header}>
        <Text variant="title" weight="bold">
          Sign in
        </Text>
        <Text variant="subtle">Forms arrive in 05-02 — auth wiring comes first.</Text>
      </View>
      <Button onPress={handleContinue} accessibilityLabel="Continue to tabs">
        Continue
      </Button>
      <Link href="/(auth)/sign-up" asChild>
        <Text variant="caption" style={styles.link}>
          Need an account? Create one instead
        </Text>
      </Link>
    </Card>
  );
}

const styles = StyleSheet.create({
  card: {
    gap: 16,
  },
  header: {
    gap: 4,
  },
  link: {
    textAlign: "center",
  },
});
