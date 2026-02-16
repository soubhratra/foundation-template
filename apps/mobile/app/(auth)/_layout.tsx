import { Slot } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { SafeAreaView, ScrollView, StyleSheet, View } from "react-native";

import { Text } from "@repo/ui";

export default function AuthLayout() {
  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar style="dark" />
      <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
        <View style={styles.header}>
          <Text variant="caption" weight="medium">
            Secure access
          </Text>
          <Text variant="title" weight="bold">
            Welcome to Foundation Mobile
          </Text>
          <Text variant="subtle">Authenticate to continue into the workspace.</Text>
        </View>
        <View style={styles.content}>
          <Slot />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: "#f4f4f5",
  },
  scroll: {
    flexGrow: 1,
    padding: 24,
    gap: 24,
  },
  header: {
    gap: 6,
  },
  content: {
    flex: 1,
    gap: 16,
  },
});
