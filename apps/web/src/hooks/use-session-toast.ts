"use client";

import { useEffect, useMemo, useRef } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { ApiError } from "@repo/api-client";
import { useAuth, useAuthContext } from "@repo/business-logic";

import { toast } from "@/components/ui/sonner";

const SESSION_EXPIRED_PARAM = "sessionExpired";
const REDIRECT_PARAM = "redirect";
const DEFAULT_REDIRECT_PATH = "/dashboard";
const SAFE_REDIRECT_PATTERN = /^\/[A-Za-z0-9._~!$&'()*+,;=:@/%?#-]*$/;

interface UseSessionToastOptions {
  readonly redirectBase?: string;
}

export function useSessionToast(options?: UseSessionToastOptions): void {
  const { redirectBase = "/login" } = options ?? {};
  const { tokenStorage } = useAuthContext();
  const { isAuthenticated, isError, isLoading, error } = useAuth();

  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const hadAuthenticatedRef = useRef(false);
  const redirectingRef = useRef(false);
  const seenParamSignatureRef = useRef<string | null>(null);

  useEffect(() => {
    if (isAuthenticated) {
      hadAuthenticatedRef.current = true;
      redirectingRef.current = false;
    }
  }, [isAuthenticated]);

  const searchSignature = useMemo(() => {
    if (!searchParams) {
      return pathname ?? "/";
    }
    const query = searchParams.toString();
    return query ? `${pathname ?? "/"}?${query}` : pathname ?? "/";
  }, [pathname, searchParams]);

  useEffect(() => {
    if (!searchParams) {
      seenParamSignatureRef.current = null;
      return;
    }

    const hasSessionFlag = searchParams.get(SESSION_EXPIRED_PARAM) === "1";
    if (!hasSessionFlag) {
      seenParamSignatureRef.current = null;
      return;
    }

    if (seenParamSignatureRef.current === searchSignature) {
      return;
    }

    seenParamSignatureRef.current = searchSignature;
    toast.warning("Your session ended. Please sign in again.");
  }, [searchParams, searchSignature]);

  useEffect(() => {
    if (!isError || isLoading || redirectingRef.current) {
      return;
    }
    if (!hadAuthenticatedRef.current) {
      return;
    }
    if (!isSessionExpiredError(error)) {
      return;
    }

    redirectingRef.current = true;
    void tokenStorage.clearTokens();

    const redirectTarget = buildRedirectTarget(pathname, searchParams);
    const nextHref = buildLoginHref(redirectBase, redirectTarget);

    toast.error("Your session expired. Redirecting to the login page…");
    router.replace(nextHref);
  }, [error, isError, isLoading, pathname, redirectBase, router, searchParams, tokenStorage]);
}

function isSessionExpiredError(error: unknown): error is ApiError {
  if (!(error instanceof ApiError)) {
    return false;
  }
  return error.status === 401 || error.status === 403;
}

function buildRedirectTarget(pathname: string | null, searchParams: URLSearchParams | null): string {
  const safePath = sanitizePathname(pathname) ?? DEFAULT_REDIRECT_PATH;
  const search = searchParams?.toString();
  if (!search) {
    return safePath;
  }
  const candidate = `${safePath}?${search}`;
  return isSafeRedirect(candidate) ? candidate : safePath;
}

function buildLoginHref(basePath: string, redirectTarget: string): string {
  const params = new URLSearchParams();
  params.set(SESSION_EXPIRED_PARAM, "1");
  if (redirectTarget) {
    params.set(REDIRECT_PARAM, redirectTarget);
  }
  const query = params.toString();
  return query ? `${basePath}?${query}` : basePath;
}

function sanitizePathname(pathname: string | null): string | null {
  if (!pathname) {
    return null;
  }
  const normalized = pathname.startsWith("/") ? pathname : `/${pathname}`;
  return isSafeRedirect(normalized) ? normalized : null;
}

function isSafeRedirect(value: string): boolean {
  if (!value.startsWith("/") || value.startsWith("//")) {
    return false;
  }
  if (value.includes("://")) {
    return false;
  }
  return SAFE_REDIRECT_PATTERN.test(value);
}
