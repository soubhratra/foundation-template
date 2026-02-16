import type { BottomTabNavigationOptions } from "@react-navigation/bottom-tabs";
import type { LucideIcon } from "lucide-react-native";
import { StyleSheet, View } from "react-native";

import { Text } from "@repo/ui";

export interface TabBarConfig {
  readonly title: string;
  readonly icon: LucideIcon;
  readonly testID: string;
}

export function createTabOptions(config: TabBarConfig): BottomTabNavigationOptions {
  const IconComponent = config.icon;
  return {
    title: config.title,
    tabBarButtonTestID: config.testID,
    tabBarAccessibilityLabel: config.title,
    tabBarIcon: ({ color, focused, size }) => (
      <View style={styles.iconWrapper} testID={`${config.testID}-icon`}>
        <IconComponent color={color} size={size} strokeWidth={focused ? 2.5 : 2} />
        <Text variant="caption" style={[styles.label, focused && styles.labelFocused]}>
          {config.title}
        </Text>
      </View>
    ),
  } satisfies BottomTabNavigationOptions;
}

const styles = StyleSheet.create({
  iconWrapper: {
    alignItems: "center",
    gap: 4,
  },
  label: {
    fontSize: 11,
    color: "#94a3b8",
  },
  labelFocused: {
    color: "#0f172a",
    fontWeight: "600",
  },
});
