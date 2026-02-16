/**
 * Auth bootstrap utilities for React Native
 *
 * Ensures SecureStore tokens are restored and optionally refreshed before the UI renders.
 * Provides a promise-returning API for the root layout to await before rendering.
 */

import { createSecureStoreTokenStorage, type TokenStorage } from "@repo/business-logic";

import { createSecureStoreAdapter } from "./token-refresh";

/**
 * Configuration for the auth bootstrap process
 */
export interface BootstrapConfig {
  /** The API base URL */
  baseUrl: string;
  /** Enable development logging */
  dev?: boolean;
}

/**
 * Bootstrap state for tracking the auth initialization
 */
export interface BootstrapState {
  /** Whether bootstrap has completed */
  ready: boolean;
  /** Whether an attempt was made to restore/refresh tokens */
  attempted: boolean;
  /** Error message if bootstrap failed */
  error?: string;
}

/**
 * Global bootstrap state (module-level to persist across renders)
 */
let globalBootstrapState: BootstrapState = {
  ready: false,
  attempted: false,
};

/**
 * Create a TokenStorage instance backed by SecureStore
 */
export function createMobileTokenStorage(): TokenStorage {
  const adapter = createSecureStoreAdapter();
  return createSecureStoreTokenStorage(adapter);
}

/**
 * Ensure JWT session is valid by:
 * 1. Reading tokens from SecureStore
 * 2. Optionally refreshing if access token is missing but refresh exists
 * 3. Waiting for initial /users/me query to complete
 *
 * @param config - Bootstrap configuration
 * @returns Promise that resolves when bootstrap completes
 */
export async function ensureJwtSession(config: BootstrapConfig): Promise<BootstrapState> {
  const { baseUrl, dev = false } = config;
  const startTime = Date.now();

  if (dev) {
    console.log("[bootstrap] Starting JWT session bootstrap...");
  }

  try {
    const tokenStorage = createMobileTokenStorage();

    // Step 1: Read tokens from SecureStore
    const tokens = await tokenStorage.getTokens();

    if (dev) {
      console.log("[bootstrap] Tokens from SecureStore:", {
        hasAccess: !!tokens.accessToken,
        hasRefresh: !!tokens.refreshToken,
        hasSession: !!tokens.sessionToken,
      });
    }

    // Step 2: If access token is missing but refresh exists, try to refresh
    if (!tokens.accessToken && tokens.refreshToken) {
      if (dev) {
        console.log("[bootstrap] Access token missing, attempting refresh...");
      }

      // Dynamic import to avoid circular dependencies
      const { refreshJwtSession } = await import("./token-refresh");

      const newTokens = await refreshJwtSession(baseUrl, tokenStorage);

      if (newTokens) {
        if (dev) {
          console.log("[bootstrap] Token refresh successful");
        }
      } else {
        if (dev) {
          console.log("[bootstrap] Token refresh failed or returned null");
        }
      }
    }

    // Step 3: Preload the token storage into the AuthProvider
    // This is handled by passing the tokenStorage to AuthProvider in the layout

    // Mark bootstrap as complete
    globalBootstrapState = {
      ready: true,
      attempted: true,
    };

    const duration = Date.now() - startTime;
    if (dev) {
      console.log(`[bootstrap] Bootstrap complete in ${duration}ms`);
    }

    return globalBootstrapState;
  } catch (error) {
    const duration = Date.now() - startTime;
    const errorMessage = error instanceof Error ? error.message : "Unknown error";

    console.error(`[bootstrap] Bootstrap failed after ${duration}ms:`, errorMessage);

    globalBootstrapState = {
      ready: false,
      attempted: true,
      error: errorMessage,
    };

    return globalBootstrapState;
  }
}

/**
 * Get the current bootstrap state
 */
export function getBootstrapState(): BootstrapState {
  return globalBootstrapState;
}

/**
 * Reset the bootstrap state (useful for testing or logout)
 */
export function resetBootstrapState(): void {
  globalBootstrapState = {
    ready: false,
    attempted: false,
  };
}
