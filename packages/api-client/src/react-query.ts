import { QueryClient, type DefaultOptions } from "@tanstack/react-query";
import createQueryClient, { type OpenapiQueryClient } from "openapi-react-query";

import type { paths } from "./gen/v1";
import { ApiError } from "./errors";
import { createApiClient, type ApiClient, type CreateApiClientOptions } from "./create-client";

export interface BuildApiQueryClientOptions extends CreateApiClientOptions {
  /** Provide a pre-configured QueryClient instance. */
  queryClient?: QueryClient;
  /** Override TanStack Query defaults. */
  queryClientOptions?: DefaultOptions;
}

export interface ApiQueryClientBundle {
  /** Low-level openapi-fetch client for manual calls. */
  client: ApiClient;
  /** openapi-react-query helpers (useQuery, useMutation, etc.). */
  api: OpenapiQueryClient<paths>;
  /** QueryClient controlling cache + retries. */
  queryClient: QueryClient;
}

const DEFAULT_QUERY_OPTIONS: DefaultOptions = {
  queries: {
    retry: (failureCount, error) => {
      // Never retry auth errors — they won't succeed and cause a blank-page loop
      // on unauthenticated pages (401 keeps the query in pending/loading state).
      if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
        return false;
      }
      return failureCount < 1;
    },
    // Don't refetch when a new observer subscribes to an errored query.
    // Without this, every component that calls useAuth() on an unauthed page
    // triggers a new 401 fetch cycle, producing an infinite-loop in the console.
    retryOnMount: false,
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  },
  mutations: {
    retry: 0,
  },
};

function mergeDefaultOptions(overrides?: DefaultOptions): DefaultOptions {
  if (!overrides) {
    return DEFAULT_QUERY_OPTIONS;
  }

  return {
    queries: {
      ...DEFAULT_QUERY_OPTIONS.queries,
      ...overrides.queries,
    },
    mutations: {
      ...DEFAULT_QUERY_OPTIONS.mutations,
      ...overrides.mutations,
    },
  } satisfies DefaultOptions;
}

export function buildApiQueryClient(
  options: BuildApiQueryClientOptions = {},
): ApiQueryClientBundle {
  const queryClient =
    options.queryClient ??
    new QueryClient({
      defaultOptions: mergeDefaultOptions(options.queryClientOptions),
    });

  const client = createApiClient(options);
  const api = createQueryClient<paths>(client);

  return { api, client, queryClient };
}
