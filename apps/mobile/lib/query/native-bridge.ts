/**
 * TanStack Query native bridge for React Native
 *
 * Wires TanStack Query's focus and online managers to React Native's
 * AppState and NetInfo APIs, ensuring queries refetch when the app
 * regains focus or network connectivity.
 *
 * @see https://tanstack.com/query/latest/docs/framework/react/guides/advanced-swr#focus-and-revalidate
 */

import { AppState, type AppStateStatus, Platform } from "react-native";
import NetInfo, { type NetInfoState } from "@react-native-community/netinfo";

import { focusManager, onlineManager } from "@tanstack/react-query";

/**
 * Configuration for the native query bridge
 */
export interface NativeQueryBridgeConfig {
  /** Enable debug logging */
  debug?: boolean;
}

/**
 * Result of registering the native query bridge
 */
export interface NativeQueryBridge {
  /** Call to unregister the bridge and clean up listeners */
  unregister: () => void;
}

/**
 * Register native bridges for TanStack Query
 *
 * This function sets up:
 * - focusManager: Refetches queries when app gains focus
 * - onlineManager: Refetches queries when network becomes available
 *
 * @param config - Optional configuration
 * @returns NativeQueryBridge with unregister function
 */
export function registerNativeQueryBridge(config?: NativeQueryBridgeConfig): NativeQueryBridge {
  const { debug = false } = config ?? {};

  // Skip on web where these managers are handled natively
  if (Platform.OS === "web") {
    if (debug) {
      console.log("[native-bridge] Skipping - web platform");
    }
    return { unregister: () => {} };
  }

  // Set up focus manager based on AppState
  function handleAppStateChange(state: AppStateStatus) {
    if (debug) {
      console.log("[native-bridge] AppState changed:", state);
    }

    // Focus when app comes to foreground
    if (state === "active") {
      focusManager.setFocused(true);
    } else if (state === "background") {
      focusManager.setFocused(false);
    }
  }

  // Set up online manager based on NetInfo
  onlineManager.setEventListener((setOnline) => {
    return NetInfo.addEventListener((state: NetInfoState) => {
      if (debug) {
        console.log("[native-bridge] NetInfo changed:", state.isConnected);
      }
      setOnline(!!state.isConnected);
    });
  });

  // Set initial focus state based on current AppState
  const currentState = AppState.currentState;
  focusManager.setFocused(currentState === "active");

  // Register AppState listener
  const appStateSubscription = AppState.addEventListener("change", handleAppStateChange);

  // Get initial network state
  NetInfo.fetch()
    .then((state) => {
      onlineManager.setOnline(!!state.isConnected);
    })
    .catch((error) => {
      console.error("[native-bridge] Failed to fetch initial NetInfo:", error);
    });

  if (debug) {
    console.log("[native-bridge] Registered for platform:", Platform.OS);
  }

  // Return cleanup function
  return {
    unregister() {
      if (debug) {
        console.log("[native-bridge] Unregistering...");
      }

      // Clean up AppState listener
      const subscription = appStateSubscription;
      if (subscription?.remove) {
        subscription.remove();
      }

      // Reset focus state
      focusManager.setFocused(true);

      // Reset online state
      onlineManager.setOnline(true);

      if (debug) {
        console.log("[native-bridge] Unregistered");
      }
    },
  };
}
