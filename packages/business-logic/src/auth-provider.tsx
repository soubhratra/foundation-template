"use client";

import { createContext, type ReactNode, useContext, useMemo } from "react";
import { QueryClientProvider } from "@tanstack/react-query";

import type { ApiQueryClientBundle, BuildApiQueryClientOptions } from "@repo/api-client";
import { buildApiQueryClient } from "@repo/api-client";

import { createMemoryTokenStorage, type TokenStorage } from "./utils/storage";

function resolveDefaultBaseUrl(): string {
  const fallback =
    process.env.NEXT_PUBLIC_API_URL ??
    process.env.EXPO_PUBLIC_API_URL ??
    process.env.API_URL ??
    "http://localhost:8000";
  return sanitizeBaseUrl(fallback);
}

function sanitizeBaseUrl(url?: string): string {
  if (!url) {
    return resolveDefaultBaseUrl();
  }
  return url.endsWith("/") ? url.slice(0, -1) : url;
}

export interface AuthContextValue extends ApiQueryClientBundle {
  readonly baseUrl: string;
  readonly tokenStorage: TokenStorage;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuthContext(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuthContext must be used within an AuthProvider");
  }
  return context;
}

export interface AuthProviderProps extends BuildApiQueryClientOptions {
  readonly children: ReactNode;
  readonly tokenStorage?: TokenStorage;
}

export function AuthProvider({
  children,
  tokenStorage,
  queryClient,
  queryClientOptions,
  baseUrl: providedBaseUrl,
  defaultHeaders,
  fetch: customFetch,
  getAccessToken,
  getSessionToken,
  version,
}: AuthProviderProps) {
  const baseUrl = sanitizeBaseUrl(providedBaseUrl);

  const storage = useMemo(() => tokenStorage ?? createMemoryTokenStorage(), [tokenStorage]);

  const bundle = useMemo<ApiQueryClientBundle>(() => {
    return buildApiQueryClient({
      baseUrl,
      defaultHeaders,
      fetch: customFetch,
      getAccessToken,
      getSessionToken,
      version,
      queryClient,
      queryClientOptions,
    });
  }, [
    baseUrl,
    customFetch,
    defaultHeaders,
    getAccessToken,
    getSessionToken,
    queryClient,
    queryClientOptions,
    version,
  ]);

  const contextValue = useMemo<AuthContextValue>(() => {
    return {
      ...bundle,
      baseUrl,
      tokenStorage: storage,
    };
  }, [baseUrl, bundle, storage]);

  return (
    <AuthContext.Provider value={contextValue}>
      <QueryClientProvider client={bundle.queryClient}>{children}</QueryClientProvider>
    </AuthContext.Provider>
  );
}
