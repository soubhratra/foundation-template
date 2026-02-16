import { useMemo } from "react";

import { Stack } from "expo-router";
import * as SecureStore from "expo-secure-store";

import { AuthProvider, createSecureStoreTokenStorage, type SecureStoreAdapter } from "@repo/business-logic";

import { env } from "@/lib/env";

const API_BASE_PATH = "/api/v1";

const secureStoreAdapter: SecureStoreAdapter = {
  getItemAsync: SecureStore.getItemAsync,
  setItemAsync: SecureStore.setItemAsync,
  deleteItemAsync: SecureStore.deleteItemAsync,
};

function buildApiBaseUrl(value: string): string {
  return `${value.replace(/\/$/, "")}${API_BASE_PATH}`;
}

export default function RootLayout() {
  const tokenStorage = useMemo(() => createSecureStoreTokenStorage(secureStoreAdapter), []);

  return (
    <AuthProvider
      baseUrl={buildApiBaseUrl(env.EXPO_PUBLIC_API_URL)}
      tokenStorage={tokenStorage}
      enableDevtools={false}
    >
      <Stack />
    </AuthProvider>
  );
}
