import type { Client, ClientOptions, Middleware } from "openapi-fetch";
import createClient from "openapi-fetch";

import type { paths } from "./gen/v1";
import { normalizeFetchError } from "./errors";

type MaybePromise<T> = T | Promise<T>;

export type TokenProvider = () => MaybePromise<string | undefined | null>;
export type HeadersFactory = () => MaybePromise<HeadersInit | undefined>;

export interface CreateApiClientOptions {
  /** Override API base URL (defaults to env + localhost fallback). */
  baseUrl?: string;
  /** API version header value (defaults to v1 or env-provided). */
  version?: string;
  /** Async accessor that resolves to a bearer token. */
  getAccessToken?: TokenProvider;
  /** Async accessor that resolves to a backend session token/header value. */
  getSessionToken?: TokenProvider;
  /** Additional headers that should be included with every request. */
  defaultHeaders?: HeadersInit | HeadersFactory;
  /** Custom fetch implementation (SSR, testing, polyfills). */
  fetch?: ClientOptions["fetch"];
}

/**
 * Default API host that prioritizes NEXT_PUBLIC_API_URL/EXPO_PUBLIC_API_URL
 * (web + Expo) and falls back to API_URL for Node/RN before localhost.
 */
const DEFAULT_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  process.env.EXPO_PUBLIC_API_URL ??
  process.env.API_URL ??
  "http://localhost:8000";

const DEFAULT_VERSION =
  process.env.NEXT_PUBLIC_API_VERSION ??
  process.env.EXPO_PUBLIC_API_VERSION ??
  process.env.API_VERSION ??
  "v1";

function sanitizeBaseUrl(url: string): string {
  return url.endsWith("/") ? url.slice(0, -1) : url;
}

async function resolveHeaders(input?: HeadersInit | HeadersFactory): Promise<Headers> {
  if (!input) {
    return new Headers();
  }

  const raw = typeof input === "function" ? await input() : input;
  return new Headers(raw);
}

async function resolveBearerToken(provider?: TokenProvider): Promise<string | undefined> {
  if (!provider) {
    return undefined;
  }

  const token = await provider();
  if (!token) {
    return undefined;
  }

  return token.startsWith("Bearer ") ? token : `Bearer ${token}`;
}

async function resolveSessionToken(provider?: TokenProvider): Promise<string | undefined> {
  if (!provider) {
    return undefined;
  }

  const token = await provider();
  return token ?? undefined;
}

function createAuthMiddleware(options: CreateApiClientOptions, version: string): Middleware {
  return {
    onRequest: async ({ request }) => {
      const headers = new Headers(request.headers);

      headers.set("X-API-Version", version);

      const defaults = await resolveHeaders(options.defaultHeaders);
      defaults.forEach((value, key) => {
        headers.set(key, value);
      });

      const bearer = await resolveBearerToken(options.getAccessToken);
      if (bearer) {
        headers.set("Authorization", bearer);
      }

      const sessionToken = await resolveSessionToken(options.getSessionToken);
      if (sessionToken) {
        headers.set("X-Session-Token", sessionToken);
      }

      // Always include credentials so session cookies are sent for web (browser)
      // auth. For JWT and server-side usage this is a no-op.
      return new Request(request, { headers, credentials: "include" });
    },
    onResponse: async ({ response }) => {
      if (!response.ok) {
        let body: Record<string, unknown> = {};
        try {
          body = (await response.clone().json()) as Record<string, unknown>;
        } catch {
          // ignore parse errors — body may be empty or non-JSON
        }
        throw normalizeFetchError({ ...body, status: response.status });
      }
      return response;
    },
    onError: ({ error }) => {
      throw normalizeFetchError(error);
    },
  } satisfies Middleware;
}

export type ApiClient = Client<paths>;

export function createApiClient(options: CreateApiClientOptions = {}): ApiClient {
  const baseUrl = sanitizeBaseUrl(options.baseUrl ?? DEFAULT_BASE_URL);
  const version = options.version ?? DEFAULT_VERSION;

  const client = createClient<paths>({
    baseUrl,
    fetch: options.fetch,
  });

  client.use(createAuthMiddleware(options, version));

  return client;
}
