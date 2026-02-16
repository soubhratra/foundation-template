import { QueryClient, type DefaultOptions } from "@tanstack/react-query";
import createQueryClient, { type OpenapiQueryClient } from "openapi-react-query";

import type { paths } from "./gen/v1";
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
    retry: 1,
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

export function buildApiQueryClient(options: BuildApiQueryClientOptions = {}): ApiQueryClientBundle {
  const queryClient =
    options.queryClient ??
    new QueryClient({
      defaultOptions: mergeDefaultOptions(options.queryClientOptions),
    });

  const client = createApiClient(options);
  const api = createQueryClient<paths>(client);

  return { api, client, queryClient };
}
