"use client";

import { useCallback } from "react";
import { useMutation, type UseMutationResult, type UseQueryResult } from "@tanstack/react-query";

import type { paths } from "@repo/api-client/gen/v1";
import type { LoginInput } from "@repo/validation";

import { useAuthContext } from "../auth-provider";
import type { TokenStorage } from "../utils/storage";

export const USER_QUERY_PATH = "/api/v1/users/me" as const;
export const USER_QUERY_KEY = ["get", USER_QUERY_PATH] as const;

// Allauth headless endpoints — browser client (session cookie) and app client (JWT)
const SESSION_LOGIN_PATH = "/api/v1/auth/browser/v1/auth/login" as const;
const JWT_LOGIN_PATH = "/api/v1/auth/app/v1/auth/login" as const;
const LOGOUT_PATH = "/api/v1/auth/browser/v1/auth/session" as const;
// Config endpoint: GET triggers get_token() on Django, which sets the csrftoken cookie
const BROWSER_CONFIG_PATH = "/api/v1/auth/browser/v1/config" as const;

type CurrentUser =
  paths[typeof USER_QUERY_PATH]["get"]["responses"][200]["content"]["application/json"];

export interface SessionLoginResponse {
  readonly user?: CurrentUser;
  readonly session_token?: string | null;
  readonly session?: {
    readonly key?: string | null;
  } | null;
}

export interface JwtLoginResponse {
  readonly access_token?: string | null;
  readonly refresh_token?: string | null;
  readonly token_type?: string | null;
  readonly expires_in?: number | null;
}

export type SessionLoginVariables = LoginInput & {
  readonly tokenStorage?: TokenStorage;
};

export type JwtLoginVariables = LoginInput & {
  readonly tokenStorage?: TokenStorage;
};

interface ErrorEnvelope {
  readonly error?: { readonly message?: string };
  readonly detail?: string;
  // django-allauth headless error format
  readonly errors?: ReadonlyArray<{ readonly message?: string; readonly code?: string }>;
}

type UserQueryResult = UseQueryResult<CurrentUser | undefined, never>;

export interface UseAuthOptions {
  readonly tokenStorage?: TokenStorage;
}

interface MutationHooks {
  readonly login: UseMutationResult<SessionLoginResponse, Error, SessionLoginVariables>;
  readonly loginWithJwt: UseMutationResult<JwtLoginResponse, Error, JwtLoginVariables>;
  readonly logout: UseMutationResult<void, Error, void>;
}

export interface UseAuthResult extends MutationHooks {
  readonly user: CurrentUser | undefined;
  readonly isAuthenticated: boolean;
  readonly isLoading: UserQueryResult["isLoading"];
  readonly isError: UserQueryResult["isError"];
  readonly error: UserQueryResult["error"];
  readonly refetch: UserQueryResult["refetch"];
}

export function useAuth(options?: UseAuthOptions): UseAuthResult {
  const context = useAuthContext();
  const storage = options?.tokenStorage ?? context.tokenStorage;

  const userQuery = context.api.useQuery("get", USER_QUERY_PATH);

  const invalidateUser = useCallback(() => {
    return context.queryClient.invalidateQueries({ queryKey: USER_QUERY_KEY });
  }, [context.queryClient]);

  const login = useMutation<SessionLoginResponse, Error, SessionLoginVariables>({
    mutationFn: async ({ tokenStorage: overrideStorage, ...credentials }) => {
      const adapter = overrideStorage ?? storage;
      // Prime the CSRF cookie if not yet present (first visit before any GET request)
      if (!getCsrfToken()) {
        await fetch(buildUrl(context.baseUrl, BROWSER_CONFIG_PATH), { credentials: "include" });
      }
      const result = await requestJson<SessionLoginResponse>(context.baseUrl, SESSION_LOGIN_PATH, {
        method: "POST",
        body: JSON.stringify(credentials),
        credentials: "include",
      });
      if (result?.session_token !== undefined) {
        await adapter.setTokens({ sessionToken: result.session_token ?? null });
      }
      return result;
    },
    onSuccess: () => invalidateUser(),
  });

  const loginWithJwt = useMutation<JwtLoginResponse, Error, JwtLoginVariables>({
    mutationFn: async ({ tokenStorage: overrideStorage, ...credentials }) => {
      const adapter = overrideStorage ?? storage;
      const result = await requestJson<JwtLoginResponse>(context.baseUrl, JWT_LOGIN_PATH, {
        method: "POST",
        body: JSON.stringify(credentials),
      });
      await adapter.setTokens({
        accessToken: result?.access_token ?? null,
        refreshToken: result?.refresh_token ?? null,
      });
      return result;
    },
    onSuccess: () => invalidateUser(),
  });

  const logout = useMutation<void, Error, void>({
    mutationFn: async () => {
      await request(context.baseUrl, LOGOUT_PATH, {
        method: "DELETE",
        credentials: "include",
      });
      await storage.clearTokens();
    },
    onSettled: () => invalidateUser(),
  });

  return {
    user: userQuery.data,
    isAuthenticated: Boolean(userQuery.data?.id),
    isLoading: userQuery.isLoading,
    isError: userQuery.isError,
    error: userQuery.error,
    refetch: userQuery.refetch,
    login,
    loginWithJwt,
    logout,
  };
}

async function requestJson<T>(baseUrl: string, path: string, init: RequestInit): Promise<T> {
  const mergedHeaders: Record<string, string> = { "Content-Type": "application/json" };
  const incoming = init.headers;
  if (incoming instanceof Headers) {
    incoming.forEach((value, key) => {
      mergedHeaders[key] = value;
    });
  } else if (Array.isArray(incoming)) {
    for (const [key, value] of incoming) {
      mergedHeaders[key] = value;
    }
  } else if (incoming) {
    Object.assign(mergedHeaders, incoming as Record<string, string>);
  }

  const response = await request(baseUrl, path, {
    ...init,
    headers: mergedHeaders,
  });
  if (response.status === 204) {
    return {} as T;
  }
  const text = await response.text();
  if (!text) {
    return {} as T;
  }
  return JSON.parse(text) as T;
}

function getCsrfToken(): string | undefined {
  if (typeof document === "undefined") return undefined;
  const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]*)/);
  return match ? decodeURIComponent(match[1]!) : undefined;
}

async function request(baseUrl: string, path: string, init: RequestInit): Promise<Response> {
  const url = buildUrl(baseUrl, path);
  const method = (init.method ?? "GET").toUpperCase();
  const isMutating = !["GET", "HEAD", "OPTIONS", "TRACE"].includes(method);

  const { headers, ...rest } = init;
  if (isMutating) {
    const csrf = getCsrfToken();
    if (csrf) {
      const merged = new Headers(headers);
      merged.set("X-CSRFToken", csrf);
      headers = merged;
    }
  }

  const response = await fetch(url, {
    credentials: "include",
    ...rest,
    headers,
  });
  if (!response.ok) {
    throw new Error(await formatError(response));
  }
  return response;
}

async function formatError(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as ErrorEnvelope;
    return (
      payload.error?.message ??
      payload.errors?.[0]?.message ??
      payload.detail ??
      response.statusText
    );
  } catch {
    return response.statusText || `Request failed with status ${response.status}`;
  }
}

function buildUrl(baseUrl: string, path: string): string {
  if (!path.startsWith("/")) {
    return `${baseUrl}/${path}`;
  }
  return `${baseUrl}${path}`;
}
