"use client";

import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";

const REDIRECT_PARAM = "redirect";
const REDIRECT_COOKIE = "redirect";
const DEFAULT_REDIRECT = "/dashboard";
const SAFE_REDIRECT_PATTERN = /^\/[A-Za-z0-9._~!$&'()*+,;=:@/%?#-]*$/;

interface RedirectCandidate {
  readonly value: string;
  readonly source: "query" | "cookie";
}

export interface RedirectTargetResult {
  readonly target: string;
  readonly hasRedirect: boolean;
}

export function useRedirectTarget(fallback: string = DEFAULT_REDIRECT): RedirectTargetResult {
  const searchParams = useSearchParams();
  const redirectParam = searchParams?.get(REDIRECT_PARAM);

  const candidate = useMemo(() => {
    const fromQuery = sanitizeRedirect(redirectParam);
    if (fromQuery) {
      return { value: fromQuery, source: "query" } satisfies RedirectCandidate;
    }
    const fromCookie = sanitizeRedirect(readRedirectCookie());
    if (fromCookie) {
      return { value: fromCookie, source: "cookie" } satisfies RedirectCandidate;
    }
    return null;
  }, [redirectParam]);

  const [persisted, setPersisted] = useState<string | null>(null);

  useEffect(() => {
    if (candidate?.value && !persisted) {
      setPersisted(candidate.value);
    }
    if (candidate?.source === "cookie") {
      clearRedirectCookie();
    }
  }, [candidate, persisted]);

  const value = persisted ?? candidate?.value ?? null;

  return {
    target: value ?? fallback,
    hasRedirect: Boolean(value),
  };
}

function sanitizeRedirect(value: string | null | undefined): string | null {
  if (!value) {
    return null;
  }
  if (!value.startsWith("/") || value.startsWith("//")) {
    return null;
  }
  if (value.includes("://")) {
    return null;
  }
  return SAFE_REDIRECT_PATTERN.test(value) ? value : null;
}

function readRedirectCookie(): string | null {
  if (typeof document === "undefined") {
    return null;
  }
  const cookies = document.cookie?.split(";") ?? [];
  const match = cookies
    .map((cookie) => cookie.trim())
    .find((cookie) => cookie.startsWith(`${REDIRECT_COOKIE}=`));
  if (!match) {
    return null;
  }
  const [, rawValue] = match.split("=");
  try {
    return decodeURIComponent(rawValue ?? "");
  } catch {
    return rawValue ?? null;
  }
}

function clearRedirectCookie(): void {
  if (typeof document === "undefined") {
    return;
  }
  document.cookie = `${REDIRECT_COOKIE}=; Max-Age=0; path=/`;
}
