"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import * as SecureStore from "expo-secure-store";

import {
  notificationPrefsSchema,
  type NotificationPrefsInput,
} from "@repo/validation";

/**
 * Storage key for preferences in SecureStore.
 */
const PREFERENCES_STORAGE_KEY = "user_preferences";

/**
 * Default preferences based on notificationPrefsSchema.
 */
const DEFAULT_PREFERENCES: NotificationPrefsInput = {
  productEmails: true,
  securityAlerts: true,
  marketingEmails: false,
  smsAlerts: false,
};

export interface UsePreferencesResult {
  /** Current preference values */
  preferences: NotificationPrefsInput;
  /** Whether preferences are still loading */
  isLoading: boolean;
  /** Update a single preference */
  setPreference: <K extends keyof NotificationPrefsInput>(
    key: K,
    value: NotificationPrefsInput[K],
  ) => Promise<void>;
  /** Update multiple preferences at once */
  setPreferences: (prefs: Partial<NotificationPrefsInput>) => Promise<void>;
  /** Reset to default preferences */
  resetToDefaults: () => Promise<void>;
}

interface PreferencesContextValue {
  preferences: NotificationPrefsInput;
  isLoading: boolean;
  setPreference: UsePreferencesResult["setPreference"];
  setPreferences: UsePreferencesResult["setPreferences"];
  resetToDefaults: UsePreferencesResult["resetToDefaults"];
}

const PreferencesContext = createContext<PreferencesContextValue | null>(null);

interface PreferencesProviderProps {
  children: React.ReactNode;
}

/**
 * Provider component for preferences state.
 * Should be placed near the AuthProvider in the app hierarchy.
 */
export function PreferencesProvider({ children }: PreferencesProviderProps) {
  const [preferences, setPreferencesState] = useState<NotificationPrefsInput>(
    DEFAULT_PREFERENCES,
  );
  const [isLoading, setIsLoading] = useState(true);

  // Load preferences from SecureStore on mount
  useEffect(() => {
    const loadPreferences = async () => {
      try {
        const stored = await SecureStore.getItemAsync(PREFERENCES_STORAGE_KEY);
        if (stored) {
          const parsed = JSON.parse(stored);
          const validated = notificationPrefsSchema.parse(parsed);
          setPreferencesState(validated);
        }
      } catch (error) {
        console.warn("[preferences] Failed to load preferences:", error);
        // Use defaults if parsing fails
      } finally {
        setIsLoading(false);
      }
    };

    loadPreferences();
  }, []);

  const savePreferences = useCallback(async (prefs: NotificationPrefsInput) => {
    try {
      await SecureStore.setItemAsync(
        PREFERENCES_STORAGE_KEY,
        JSON.stringify(prefs),
      );
    } catch (error) {
      console.warn("[preferences] Failed to save preferences:", error);
      throw error;
    }
  }, []);

  const setPreference = useCallback(
    async <K extends keyof NotificationPrefsInput>(
      key: K,
      value: NotificationPrefsInput[K],
    ) => {
      const newPrefs = { ...preferences, [key]: value };
      setPreferencesState(newPrefs);
      await savePreferences(newPrefs);
    },
    [preferences, savePreferences],
  );

  const setPreferencesFn = useCallback(
    async (prefs: Partial<NotificationPrefsInput>) => {
      const newPrefs = { ...preferences, ...prefs };
      setPreferencesState(newPrefs);
      await savePreferences(newPrefs);
    },
    [preferences, savePreferences],
  );

  const resetToDefaults = useCallback(async () => {
    setPreferencesState(DEFAULT_PREFERENCES);
    await savePreferences(DEFAULT_PREFERENCES);
  }, [savePreferences]);

  return (
    <PreferencesContext.Provider
      value={{
        preferences,
        isLoading,
        setPreference,
        setPreferences: setPreferencesFn,
        resetToDefaults,
      }}
    >
      {children}
    </PreferencesContext.Provider>
  );
}

/**
 * Hook for accessing and managing user preferences.
 * Backed by SecureStore for persistent storage.
 *
 * TODO: When backend implements /api/v1/users/preferences endpoint,
 * sync local preferences with server on load and save.
 */
export function usePreferences(): UsePreferencesResult {
  const context = useContext(PreferencesContext);
  if (!context) {
    // Return default values if used outside provider (fallback)
    return {
      preferences: DEFAULT_PREFERENCES,
      isLoading: false,
      setPreference: async () => {
        console.warn("[preferences] usePreferences called outside PreferencesProvider");
      },
      setPreferences: async () => {
        console.warn("[preferences] usePreferences called outside PreferencesProvider");
      },
      resetToDefaults: async () => {
        console.warn("[preferences] usePreferences called outside PreferencesProvider");
      },
    };
  }
  return context;
}

/**
 * Helper to get a preference value.
 * Useful for reading a single preference without full hook.
 */
export function usePreference<K extends keyof NotificationPrefsInput>(
  key: K,
): NotificationPrefsInput[K] {
  const { preferences } = usePreferences();
  return preferences[key];
}
