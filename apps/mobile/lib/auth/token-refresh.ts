/**
 * Token refresh utilities for React Native
 *
 * Handles JWT refresh against the backend API, persisting results to SecureStore.
 * Resilient to 401 errors by clearing tokens so login can resume cleanly.
 */

import * as SecureStore from "expo-secure-store";

import type { TokenStorage } from "@repo/business-logic";

const API_BASE_PATH = "/api/v1";

/**
 * Create a SecureStore-backed token storage adapter for the business-logic package
 */
export function createSecureStoreAdapter() {
  return {
    getItemAsync: SecureStore.getItemAsync,
    setItemAsync: SecureStore.setItemAsync,
    deleteItemAsync: SecureStore.deleteItemAsync,
  };
}

/**
 * Refresh JWT tokens by calling the refresh endpoint
 *
 * @param baseUrl - The API base URL
 * @param tokenStorage - TokenStorage instance for persisting tokens
 * @returns The new tokens if successful, or throws an error
 */
export async function refreshJwtSession(
  baseUrl: string,
  tokenStorage: TokenStorage,
): Promise<{ accessToken: string; refreshToken: string } | null> {
  const tokens = await tokenStorage.getTokens();
  const refreshToken = tokens.refreshToken;

  if (!refreshToken) {
    // No refresh token available, can't refresh
    return null;
  }

  const url = `${baseUrl.replace(/\/$/, "")}${API_BASE_PATH}/auth/jwt/refresh/`;

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ refresh: refreshToken }),
    });

    if (response.status === 401) {
      // Refresh token expired or invalid - clear tokens so login can resume
      await tokenStorage.clearTokens();
      return null;
    }

    if (!response.ok) {
      const errorText = await response.text();
      console.error("[token-refresh] Refresh failed:", response.status, errorText);
      return null;
    }

    const data = await response.json();

    // Extract tokens from response
    const accessToken = data.access ?? data.access_token;
    const newRefreshToken = data.refresh ?? data.refresh_token ?? refreshToken;

    if (!accessToken) {
      console.error("[token-refresh] No access token in refresh response");
      return null;
    }

    // Persist the new tokens
    await tokenStorage.setTokens({
      accessToken,
      refreshToken: newRefreshToken,
    });

    return { accessToken, refreshToken: newRefreshToken };
  } catch (error) {
    // Network error or other issues
    console.error("[token-refresh] Refresh error:", error);
    return null;
  }
}
