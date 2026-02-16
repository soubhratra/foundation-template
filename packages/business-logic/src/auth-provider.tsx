"use client";

import {
  ComponentType,
  createContext,
  type ReactNode,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { QueryClientProvider } from "@tanstack/react-query";

import type {
  ApiQueryClientBundle,
  BuildApiQueryClientOptions,
} from "@repo/api-client";
import { buildApiQueryClient } from "@repo/api-client";

import { createMemoryTokenStorage, type TokenStorage } from "./utils/storage";

type DevtoolsComponent = ComponentType<{ initialIsOpen?: boolean }>;

let resolvedDevtools: DevtoolsComponent | null | undefined;
let devtoolsPromise: Promise<DevtoolsComponent | null> | null = null;

async function loadDevtools(): Promise<DevtoolsComponent | null> {
  if (typeof window === "undefined") {
    return null;
  }

  if (typeof resolvedDevtools !== "undefined") {
    return resolvedDevtools;
  }

  if (!devtoolsPromise) {
    devtoolsPromise = import("@tanstack/react-query-devtools")
      .then((module) => module.ReactQueryDevtools as DevtoolsComponent)
      .catch(() => null);
  }

  const component = await devtoolsPromise;
  resolvedDevtools = component;
  devtoolsPromise = null;
  return component ?? null;
}

interface ReactQueryDevtoolsPortalProps {
  readonly initialIsOpen?: boolean;
}

function ReactQueryDevtoolsPortal({ initialIsOpen }: ReactQueryDevtoolsPortalProps) {
  const [Devtools, setDevtools] = useState<DevtoolsComponent | null>(
    typeof resolvedDevtools === "undefined" ? null : resolvedDevtools,
  );

  useEffect(() => {
    let mounted = true;
    loadDevtools()
      .then((component) => {
        if (mounted) {
          setDevtools(component);
        }
      })
      .catch(() => {
        if (mounted) {
          setDevtools(null);
        }
      });
    return () => {
      mounted = false;
    };
  }, []);

  if (!Devtools) {
    return null;
  }

  return <Devtools initialIsOpen={initialIsOpen} />;
}

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
  readonly enableDevtools?: boolean;
  readonly devtoolsInitialIsOpen?: boolean;
}

const DEFAULT_DEVTOOLS = process.env.NODE_ENV !== "production";

export function AuthProvider({
  children,
  tokenStorage,
  enableDevtools = DEFAULT_DEVTOOLS,
  devtoolsInitialIsOpen,
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

  const storage = useMemo(
    () => tokenStorage ?? createMemoryTokenStorage(),
    [tokenStorage],
  );

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

  const shouldRenderDevtools = enableDevtools && typeof window !== "undefined";

  return (
    <AuthContext.Provider value={contextValue}>
      <QueryClientProvider client={bundle.queryClient}>
        {children}
        {shouldRenderDevtools ? (
          <ReactQueryDevtoolsPortal initialIsOpen={devtoolsInitialIsOpen} />
        ) : null}
      </QueryClientProvider>
    </AuthContext.Provider>
  );
}
