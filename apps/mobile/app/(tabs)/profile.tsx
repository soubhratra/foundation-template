import { StyleSheet, View } from "react-native";

import { Link, router } from "expo-router";

import { Button, Card, Text } from "@repo/ui";

export default function ProfileScreen() {
  return (
    <View style={styles.container}>
      <Card style={styles.card}>
        <Text variant="title" weight="bold">
          Profile
        </Text>
        <Text variant="subtle">User preferences and account settings render here later.</Text>
        <Button onPress={() => router.replace("/(auth)/sign-in")} accessibilityLabel="Simulate logout">
          Sign out placeholder
        </Button>
        <Link href="/(tabs)/settings" asChild>
          <Text variant="caption" style={styles.link}>
            Manage workspace settings
          </Text>
        </Link>
      </Card>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 24,
    gap: 16,
  },
  card: {
    gap: 16,
  },
  link: {
    textAlign: "center",
  },
});
