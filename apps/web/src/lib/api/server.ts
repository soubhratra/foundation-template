import { cache } from "react";

import { cookies } from "next/headers";

import type { components } from "@repo/api-client/gen/v1";
import { ApiError, createApiClient, type ApiClient, type paths } from "@repo/api-client";
import type { PasswordChangeInput } from "@repo/validation";

import { buildApiBaseUrl } from "../../../app/base-url";
import { env } from "@/config/env";

const API_BASE_URL = buildApiBaseUrl(env.NEXT_PUBLIC_API_URL);
const API_ORIGIN = env.NEXT_PUBLIC_API_URL.replace(/\/$/, "");
const PASSWORD_CHANGE_PATH = "/api/v1/auth/password/change/";
const CSRF_COOKIE_NAME = "csrftoken";

export type CurrentUser = paths["/api/v1/users/me"]["get"]["responses"][200]["content"]["application/json"];
export type UpdateCurrentUserInput = components["schemas"]["UserUpdateIn"];

export interface ServerApi {
  readonly client: ApiClient;
  readonly getCurrentUser: () => Promise<CurrentUser | undefined>;
  readonly updateCurrentUser: (input: UpdateCurrentUserInput) => Promise<CurrentUser | undefined>;
  readonly requestPasswordChange: (input: PasswordChangeInput) => Promise<void>;
}

const fetchCurrentUser = cache(async (cookieHeader: string | null, csrfToken: string | null) => {
  const client = createClient(cookieHeader, csrfToken);
  const result = await client.GET("/api/v1/users/me");
  return result.data ?? undefined;
});

type CookieStore = Awaited<ReturnType<typeof cookies>>;

export async function getServerApi(): Promise<ServerApi> {
  const store = await cookies();
  const cookieHeader = serializeCookies(store);
  const csrfToken = store.get(CSRF_COOKIE_NAME)?.value ?? null;
  const client = createClient(cookieHeader, csrfToken);
  const upstreamFetch = createUpstreamFetcher(cookieHeader, csrfToken);

  return {
    client,
    getCurrentUser: () => fetchCurrentUser(cookieHeader, csrfToken),
    updateCurrentUser: async (input) => {
      const result = await client.PATCH("/api/v1/users/me", { body: input });
      return result.data ?? undefined;
    },
    requestPasswordChange: async (input) => {
      await upstreamFetch(PASSWORD_CHANGE_PATH, {
        method: "POST",
        body: JSON.stringify({
          old_password: input.currentPassword,
          new_password1: input.newPassword,
          new_password2: input.confirmPassword,
        }),
        headers: {
          "Content-Type": "application/json",
        },
      });
    },
  } satisfies ServerApi;
}

function createClient(cookieHeader: string | null, csrfToken: string | null): ApiClient {
  return createApiClient({
    baseUrl: API_BASE_URL,
    defaultHeaders: buildDefaultHeaders(cookieHeader, csrfToken),
  });
}

function serializeCookies(store: CookieStore): string | null {
  const serialized = store
    .getAll()
    .map((cookie) => `${cookie.name}=${encodeURIComponent(cookie.value)}`)
    .join("; ");
  return serialized.length > 0 ? serialized : null;
}

function buildDefaultHeaders(cookieHeader: string | null, csrfToken: string | null): HeadersInit | undefined {
  const headers: Record<string, string> = {};
  if (cookieHeader) {
    headers.cookie = cookieHeader;
  }
  if (csrfToken) {
    headers["X-CSRFToken"] = csrfToken;
  }
  return Object.keys(headers).length > 0 ? headers : undefined;
}

function createUpstreamFetcher(cookieHeader: string | null, csrfToken: string | null) {
  return async (path: string, init: RequestInit = {}) => {
    const url = buildAbsoluteUrl(path);
    const headers = new Headers(init.headers ?? undefined);
    if (cookieHeader) {
      headers.set("cookie", cookieHeader);
    }
    if (csrfToken) {
      headers.set("X-CSRFToken", csrfToken);
    }
    const response = await fetch(url, {
      ...init,
      headers,
      cache: "no-store",
    });
    if (!response.ok) {
      throw await buildApiError(response);
    }
    return response;
  };
}

function buildAbsoluteUrl(path: string): string {
  if (/^https?:\/\//i.test(path)) {
    return path;
  }
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${API_ORIGIN}${normalizedPath}`;
}

async function buildApiError(response: Response): Promise<ApiError> {
  let message = response.statusText || "Request failed";
  try {
    const payload = (await response.clone().json()) as { error?: { message?: string } };
    message = payload.error?.message ?? message;
  } catch {
    try {
      const text = await response.clone().text();
      message = text || message;
    } catch {
      // Ignore parsing failures.
    }
  }

  return new ApiError({
    code: "api_request_failed",
    message,
    status: response.status,
  });
}
