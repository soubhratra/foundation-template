import { Tabs } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { ActivitySquare, Home, Settings2, UserRound } from "lucide-react-native";

import { createTabOptions } from "@/components/navigation/tab-bar";

export default function TabsLayout() {
  const insets = useSafeAreaInsets();
  const bottomInset = Math.max(insets.bottom, 12);

  return (
    <Tabs
      initialRouteName="home"
      screenOptions={{
        headerShown: false,
        tabBarShowLabel: false,
        tabBarActiveTintColor: "#0f172a",
        tabBarInactiveTintColor: "#94a3b8",
        tabBarStyle: {
          backgroundColor: "#ffffff",
          borderTopColor: "rgba(15, 23, 42, 0.08)",
          borderTopWidth: 1,
          paddingTop: 12,
          paddingBottom: bottomInset,
          height: 64 + bottomInset,
        },
        sceneStyle: {
          backgroundColor: "#f8fafc",
        },
      }}
    >
      <Tabs.Screen
        name="home"
        options={createTabOptions({ title: "Home", icon: Home, testID: "tab-home" })}
      />
      <Tabs.Screen
        name="activity"
        options={createTabOptions({ title: "Activity", icon: ActivitySquare, testID: "tab-activity" })}
      />
      <Tabs.Screen
        name="profile"
        options={createTabOptions({ title: "Profile", icon: UserRound, testID: "tab-profile" })}
      />
      <Tabs.Screen
        name="settings"
        options={createTabOptions({ title: "Settings", icon: Settings2, testID: "tab-settings" })}
      />
    </Tabs>
  );
}
