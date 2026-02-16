import { NextResponse, type NextRequest } from "next/server";

import { buildRedirectUrl, validateSession } from "@/lib/auth/server";

const LOGIN_PATH = "/login";
const SESSION_EXPIRED_PARAM = "sessionExpired";
const PUBLIC_ROUTES = new Set(["/", "/login", "/signup", "/reset", "/verify-email"]);
const PUBLIC_PREFIXES = ["/_next", "/api", "/static", "/public", "/favicon", "/fonts"];
const ASSET_EXTENSIONS = /\.(?:css|js|json|ico|png|jpg|jpeg|svg|gif|webp|txt|xml|map)$/i;

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon\\.ico|manifest\\.webmanifest).*)"],
};

export default async function proxy(request: NextRequest) {
  if (shouldBypass(request)) {
    return NextResponse.next();
  }

  const session = await validateSession(request);
  if (session.isAuthenticated) {
    return NextResponse.next();
  }

  const redirectUrl = buildRedirectUrl(request, LOGIN_PATH);
  if (session.hasSessionCookie) {
    redirectUrl.searchParams.set(SESSION_EXPIRED_PARAM, "1");
  }

  return NextResponse.redirect(redirectUrl);
}

function shouldBypass(request: NextRequest): boolean {
  const { pathname } = request.nextUrl;

  if (request.method === "OPTIONS") {
    return true;
  }

  if (PUBLIC_ROUTES.has(pathname)) {
    return true;
  }

  for (const prefix of PUBLIC_PREFIXES) {
    if (pathname === prefix || pathname.startsWith(`${prefix}/`)) {
      return true;
    }
  }

  if (ASSET_EXTENSIONS.test(pathname)) {
    return true;
  }

  return false;
}
