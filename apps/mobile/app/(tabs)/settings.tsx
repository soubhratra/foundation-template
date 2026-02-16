import { StyleSheet, View } from "react-native";

import { Button, Card, Text } from "@repo/ui";

export default function SettingsScreen() {
  return (
    <View style={styles.container}>
      <Card style={styles.card}>
        <Text variant="title" weight="bold">
          Settings
        </Text>
        <Text variant="subtle">Wire account toggles + feature flags here next.</Text>
        <Button onPress={() => console.warn("Saved placeholder preferences")}>Save changes</Button>
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
    gap: 12,
  },
});
