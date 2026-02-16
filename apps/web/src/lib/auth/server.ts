import type { NextRequest } from "next/server";

import { ApiError, createApiClient, type paths } from "@repo/api-client";

import { env } from "@/config/env";

import { buildApiBaseUrl } from "../../../app/base-url";

const SESSION_COOKIE_NAME = "sessionid";
const REDIRECT_PARAM = "redirect";
const SAFE_REDIRECT_PATTERN = /^\/[A-Za-z0-9._~!$&'()*+,;=:@/%?#-]*$/;

type CurrentUser = paths["/api/v1/users/me"]["get"]["responses"][200]["content"]["application/json"];

export interface SessionValidationResult {
  readonly isAuthenticated: boolean;
  readonly hasSessionCookie: boolean;
  readonly status?: number;
  readonly user?: CurrentUser;
}

const API_BASE_URL = buildApiBaseUrl(env.NEXT_PUBLIC_API_URL);

export async function validateSession(request: NextRequest): Promise<SessionValidationResult> {
  const sessionCookie = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  if (!sessionCookie) {
    return {
      isAuthenticated: false,
      hasSessionCookie: false,
    } satisfies SessionValidationResult;
  }

  const client = createApiClient({
    baseUrl: API_BASE_URL,
    defaultHeaders: {
      cookie: `${SESSION_COOKIE_NAME}=${encodeURIComponent(sessionCookie)}`,
    },
  });

  try {
    const result = await client.GET("/api/v1/users/me");

    if (result.data) {
      return {
        isAuthenticated: true,
        hasSessionCookie: true,
        user: result.data,
        status: result.response?.status,
      } satisfies SessionValidationResult;
    }

    return {
      isAuthenticated: false,
      hasSessionCookie: true,
      status: result.response?.status,
    } satisfies SessionValidationResult;
  } catch (error) {
    const status = error instanceof ApiError ? error.status : undefined;
    return {
      isAuthenticated: false,
      hasSessionCookie: true,
      status,
    } satisfies SessionValidationResult;
  }
}

export function buildRedirectUrl(request: NextRequest, targetPath: string): URL {
  const redirectTarget = buildRedirectTarget(request);
  const redirectUrl = new URL(targetPath, request.nextUrl.origin);
  if (redirectTarget) {
    redirectUrl.searchParams.set(REDIRECT_PARAM, redirectTarget);
  }
  return redirectUrl;
}

function buildRedirectTarget(request: NextRequest): string | null {
  const pathname = request.nextUrl.pathname;
  const search = request.nextUrl.search;
  const combined = `${pathname}${search}`;
  return isSafeRedirect(combined) ? combined : null;
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
