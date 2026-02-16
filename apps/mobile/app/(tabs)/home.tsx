import { StyleSheet, View } from "react-native";

import { Link } from "expo-router";

import { Button, Card, Text } from "@repo/ui";

export default function HomeScreen() {
  return (
    <View style={styles.container}>
      <Card style={styles.card}>
        <Text variant="title" weight="bold">
          Home overview
        </Text>
        <Text variant="subtle">
          Placeholder charts and feed cards will live here once data hooks land.
        </Text>
        <Button onPress={() => console.warn("Refreshing placeholder dashboard")}>Refresh data</Button>
        <Link href="/(tabs)/profile" asChild>
          <Text variant="caption" style={styles.link}>
            Jump to profile
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
