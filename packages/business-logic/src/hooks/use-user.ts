"use client";

import { useMemo, useSyncExternalStore } from "react";

import type { paths } from "@repo/api-client/gen/v1";

import { useAuthContext } from "../auth-provider";
import { USER_QUERY_KEY, USER_QUERY_PATH } from "./use-auth";

type CurrentUser = paths[typeof USER_QUERY_PATH]["get"]["responses"][200]["content"]["application/json"];

export interface UseUserResult {
  readonly user: CurrentUser | undefined;
  readonly isAuthenticated: boolean;
  readonly hasProfile: boolean;
  readonly refresh: () => Promise<void>;
}

export function useUser(): UseUserResult {
  const { queryClient } = useAuthContext();

  const subscribe = useMemo(() => {
    return (onStoreChange: () => void) => {
      const unsubscribe = queryClient.getQueryCache().subscribe(onStoreChange);
      return () => unsubscribe();
    };
  }, [queryClient]);

  const snapshot = useMemo(() => {
    return () => queryClient.getQueryData<CurrentUser>(USER_QUERY_KEY);
  }, [queryClient]);

  const user = useSyncExternalStore(subscribe, snapshot, snapshot);

  const refresh = useMemo(() => {
    return () => queryClient.invalidateQueries({ queryKey: USER_QUERY_KEY }).then(() => undefined);
  }, [queryClient]);

  return useMemo(() => {
    return {
      user,
      isAuthenticated: Boolean(user?.id),
      hasProfile: Boolean(user?.full_name ?? user?.email),
      refresh,
    };
  }, [refresh, user]);
}
