import { StyleSheet, View } from "react-native";

import { Button, Card, Text } from "@repo/ui";

export default function ActivityScreen() {
  return (
    <View style={styles.container}>
      <Card style={styles.card}>
        <Text variant="title" weight="bold">
          Activity feed
        </Text>
        <Text variant="subtle">Events, alerts, and audit history render here soon.</Text>
        <Button onPress={() => console.warn("Acknowledged placeholder notification")}>Dismiss latest</Button>
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
