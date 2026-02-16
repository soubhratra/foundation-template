import { StyleSheet, View } from "react-native";

import { Link, router } from "expo-router";

import { Button, Card, Text } from "@repo/ui";

export default function SignUpScreen() {
  const handleContinue = () => {
    router.replace("/(tabs)/home");
  };

  return (
    <Card style={styles.card}>
      <View style={styles.header}>
        <Text variant="title" weight="bold">
          Create account
        </Text>
        <Text variant="subtle">Placeholder copy keeps navigation testable today.</Text>
      </View>
      <Button onPress={handleContinue} accessibilityLabel="Complete placeholder sign up">
        Finish setup
      </Button>
      <Link href="/(auth)/sign-in" asChild>
        <Text variant="label" style={styles.link}>
          Already a member? Sign in
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
