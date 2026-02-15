# Authentication Specification

> Baseline specification for the Foundation Template.
> This document is the source of truth. All implementations must conform to these specs.

## Overview

The Foundation Template implements a dual authentication strategy: session cookies for web (Next.js) and JWT tokens for mobile (Expo). Django Allauth in headless mode provides the backend for both flows. This dual strategy is the single most complex integration in the template. It must be implemented correctly in Phase 2 -- auth touches every API endpoint, every frontend page, and every mobile screen.

## Specifications

### Dual Auth Strategy

| Platform | Auth Mechanism | Token Storage | Transport | CSRF |
|----------|---------------|---------------|-----------|------|
| Next.js (browser) | Session cookies | httpOnly cookie (managed by Django) | Cookie header (automatic) | CSRF token required for mutations |
| Next.js (SSR) | Forwarded cookies | Server-side from incoming request | Cookie header (manual forwarding) | Not applicable (server-to-server) |
| Expo (mobile) | JWT access + refresh tokens | expo-secure-store (Keychain/Keystore) | Authorization: Bearer header | Not applicable (no cookies) |

**Why dual strategy:**
- Web: httpOnly cookies are more secure than storing JWTs in browser storage. Django Allauth naturally provides session-based auth. Next.js middleware can read session cookies for server-side auth checks.
- Mobile: Mobile apps cannot use cookies effectively. JWT access + refresh token pair stored in device secure storage. The API client handles transparent token refresh.

### Django Allauth Headless Mode Configuration

```python
# config/settings/base.py
INSTALLED_APPS = [
    # ...
    "allauth",
    "allauth.account",
    "allauth.headless",
    # ...
]

MIDDLEWARE = [
    # ...
    "allauth.account.middleware.AccountMiddleware",
    # ...
]

# Allauth configuration
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True

# Headless mode
HEADLESS_ONLY = True  # Disable Django's HTML auth views
HEADLESS_FRONTEND_URLS = {
    "account_confirm_email": "{FRONTEND_URL}/auth/verify-email/{key}",
    "account_reset_password_from_key": "{FRONTEND_URL}/auth/reset-password/{key}",
}

# Session settings (for web auth)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = True  # Set to False only in development
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14  # 14 days

# CSRF settings
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=["http://localhost:3000"])
CSRF_COOKIE_HTTPONLY = False  # Frontend needs to read CSRF token
CSRF_COOKIE_SAMESITE = "Lax"
```

### Signup Flow

#### Web Signup

**GIVEN** a user navigates to /auth/signup on the Next.js web app
**WHEN** they submit the signup form with email, password, first_name, last_name
**THEN** the Next.js client sends POST to Django `/api/v1/auth/signup`
**AND** Django Allauth creates the user account
**AND** Django sends a verification email with a confirmation link
**AND** the API returns 200 with user data and a session cookie
**AND** the user is redirected to a "check your email" page

**GIVEN** the user clicks the verification link in the email
**WHEN** the link opens `{FRONTEND_URL}/auth/verify-email/{key}`
**THEN** the Next.js page sends POST to Django `/api/v1/auth/verify-email` with the key
**AND** Django Allauth marks the email as verified
**AND** the user is redirected to the dashboard

```typescript
// apps/web/app/(auth)/signup/page.tsx
"use client";
import { apiClient } from "@repo/api-client";
import { signupSchema } from "@repo/schemas";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

export default function SignupPage() {
  const form = useForm({
    resolver: zodResolver(signupSchema),
  });

  async function onSubmit(data) {
    const { error } = await apiClient.POST("/auth/signup", {
      body: data,
    });
    if (error) {
      // Display error to user
    } else {
      // Redirect to email verification page
    }
  }
}
```

#### Mobile Signup

**GIVEN** a user opens the signup screen in the Expo mobile app
**WHEN** they submit the signup form with email, password, first_name, last_name
**THEN** the Expo client sends POST to Django `/api/v1/auth/signup`
**AND** Django Allauth creates the user account and issues JWT tokens
**AND** the API returns 200 with user data, access token, and refresh token
**AND** the Expo app stores tokens in expo-secure-store
**AND** the user is navigated to a "check your email" screen

```typescript
// apps/mobile/lib/auth.ts
import * as SecureStore from "expo-secure-store";

const TOKEN_KEY = "auth_access_token";
const REFRESH_KEY = "auth_refresh_token";

export async function storeTokens(access: string, refresh: string) {
  await SecureStore.setItemAsync(TOKEN_KEY, access);
  await SecureStore.setItemAsync(REFRESH_KEY, refresh);
}

export async function getAccessToken(): Promise<string | null> {
  return SecureStore.getItemAsync(TOKEN_KEY);
}

export async function clearTokens() {
  await SecureStore.deleteItemAsync(TOKEN_KEY);
  await SecureStore.deleteItemAsync(REFRESH_KEY);
}
```

### Login Flow

#### Web Login

**GIVEN** a user navigates to /auth/login on the Next.js web app
**WHEN** they submit the login form with email and password
**THEN** the client sends POST to Django `/api/v1/auth/login`
**AND** Django Allauth validates credentials
**AND** Django creates a session and sets an httpOnly session cookie in the response
**AND** the user is redirected to the dashboard

**GIVEN** a user has a valid session cookie
**WHEN** they navigate to any authenticated page
**THEN** Next.js middleware reads the session cookie from the request
**AND** validates the session (via a lightweight check or proxy to Django)
**AND** allows the request to proceed
**AND** the cookie is automatically sent on all subsequent API requests

**GIVEN** a user has an expired or invalid session cookie
**WHEN** they navigate to any authenticated page
**THEN** Next.js middleware detects the invalid session
**AND** redirects the user to /auth/login
**AND** preserves the original URL as a `redirect` query parameter

#### Mobile Login

**GIVEN** a user opens the login screen in the Expo mobile app
**WHEN** they submit the login form with email and password
**THEN** the client sends POST to Django `/api/v1/auth/login`
**AND** Django Allauth validates credentials and issues JWT tokens
**AND** the API returns access token (short-lived) and refresh token (long-lived)
**AND** the Expo app stores both tokens in expo-secure-store
**AND** the user is navigated to the main tab navigator

**GIVEN** a user has a valid access token stored in expo-secure-store
**WHEN** they make any authenticated API request
**THEN** the API client reads the token from secure store
**AND** adds `Authorization: Bearer {access_token}` header
**AND** the request is authenticated by Django

### Logout Flow

**GIVEN** a user clicks "Log out" on the web app
**WHEN** the client sends POST to Django `/api/v1/auth/logout`
**THEN** Django invalidates the server-side session
**AND** the session cookie is cleared from the response
**AND** the user is redirected to the login page

**GIVEN** a user taps "Log out" on the mobile app
**WHEN** the client sends POST to Django `/api/v1/auth/logout`
**THEN** Django invalidates the token (if using token blacklisting)
**AND** the Expo app clears tokens from expo-secure-store
**AND** the user is navigated to the login screen

### Password Reset Flow

**GIVEN** a user clicks "Forgot password?" on the login page (web or mobile)
**WHEN** they submit their email address
**THEN** the client sends POST to Django `/api/v1/auth/password/reset`
**AND** Django Allauth sends a password reset email with a link
**AND** the link points to `{FRONTEND_URL}/auth/reset-password/{key}`
**AND** the user sees a "check your email" message

**GIVEN** the user clicks the reset link in the email
**WHEN** the link opens the reset password page with the key
**THEN** the page displays a new password form
**AND** on submit, sends POST to Django `/api/v1/auth/password/reset/confirm` with the key and new password
**AND** Django Allauth validates the key and updates the password
**AND** the user is redirected to the login page

### Email Verification Flow

**GIVEN** a user signs up with an unverified email
**WHEN** they attempt to access authenticated endpoints
**THEN** the API returns 403 with code `email_not_verified` (if ACCOUNT_EMAIL_VERIFICATION = "mandatory")
**AND** the frontend displays a message to check their email

**GIVEN** a user requests a new verification email
**WHEN** the client sends POST to Django `/api/v1/auth/email/verify/resend`
**THEN** Django Allauth sends a new verification email
**AND** the user sees a confirmation message

### Token Refresh Flow (Mobile Only)

**GIVEN** the Expo app makes an API request with an expired access token
**WHEN** the API returns 401 Unauthorized
**THEN** the API client interceptor catches the 401
**AND** sends POST to Django `/api/v1/auth/token/refresh` with the refresh token
**AND** Django returns a new access token (and optionally a new refresh token)
**AND** the Expo app stores the new tokens in expo-secure-store
**AND** the original request is retried with the new access token
**AND** the retry is transparent to the calling code

**GIVEN** the refresh token is also expired or invalid
**WHEN** the refresh request returns 401
**THEN** the API client clears all tokens from expo-secure-store
**AND** navigates the user to the login screen
**AND** the original request fails with an auth error

```typescript
// packages/api-client/src/interceptors.ts
export function createAuthInterceptor(
  getToken: () => Promise<string | null>,
  refreshToken: () => Promise<string | null>,
  onAuthFailure: () => void,
) {
  return async (request: Request) => {
    const token = await getToken();
    if (token) {
      request.headers.set("Authorization", `Bearer ${token}`);
    }
    return request;
  };
}
```

### Next.js Middleware Auth Guards

```typescript
// apps/web/middleware.ts
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PUBLIC_PATHS = [
  "/",
  "/auth/login",
  "/auth/signup",
  "/auth/forgot-password",
  "/auth/reset-password",
  "/auth/verify-email",
];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Allow public paths
  if (PUBLIC_PATHS.some((path) => pathname.startsWith(path))) {
    return NextResponse.next();
  }

  // Check for session cookie
  const sessionCookie = request.cookies.get("sessionid");

  if (!sessionCookie) {
    const loginUrl = new URL("/auth/login", request.url);
    loginUrl.searchParams.set("redirect", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    // Match all paths except static files and API routes
    "/((?!_next/static|_next/image|favicon.ico|api/).*)",
  ],
};
```

### Expo Secure Store Token Management

```typescript
// apps/mobile/lib/auth-provider.tsx
import * as SecureStore from "expo-secure-store";
import { createContext, useContext, useEffect, useState } from "react";
import { router } from "expo-router";

type AuthState = {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: User | null;
};

const AuthContext = createContext<AuthState>(/* ... */);

export function AuthProvider({ children }) {
  const [state, setState] = useState<AuthState>({
    isAuthenticated: false,
    isLoading: true,
    user: null,
  });

  useEffect(() => {
    // Check for stored tokens on app launch
    checkAuthState();
  }, []);

  async function checkAuthState() {
    const token = await SecureStore.getItemAsync("auth_access_token");
    if (token) {
      // Validate token by fetching current user
      try {
        const user = await fetchCurrentUser(token);
        setState({ isAuthenticated: true, isLoading: false, user });
      } catch {
        // Token invalid, clear and redirect to login
        await clearTokens();
        setState({ isAuthenticated: false, isLoading: false, user: null });
      }
    } else {
      setState({ isAuthenticated: false, isLoading: false, user: null });
    }
  }

  // ... login, logout, refresh methods
}
```

### CSRF Handling Strategy

| Scenario | CSRF Required | Approach |
|----------|--------------|----------|
| Web GET requests | No | Cookies sent automatically |
| Web POST/PATCH/DELETE | Yes | Read CSRF token from cookie, send in X-CSRFToken header |
| Mobile requests | No | JWT auth, no cookies, CSRF not applicable |
| Next.js SSR (server-to-server) | No | No cookies in server context, uses forwarded auth |

```typescript
// Web: CSRF token handling in API client
function getCsrfToken(): string | null {
  if (typeof document === "undefined") return null;
  const cookie = document.cookie
    .split("; ")
    .find((row) => row.startsWith("csrftoken="));
  return cookie ? cookie.split("=")[1] : null;
}

// Add CSRF token to mutation requests
const webApiClient = createClient<paths>({
  baseUrl: "/api/v1",
  headers: {
    "X-CSRFToken": getCsrfToken() ?? "",
  },
});
```

**GIVEN** a web client sends a POST request to the Django API
**WHEN** CSRF protection is enabled (default for session auth)
**THEN** the client reads the CSRF token from the `csrftoken` cookie
**AND** includes it in the `X-CSRFToken` request header
**AND** Django validates the token
**AND** the request proceeds if valid

**GIVEN** a mobile client sends a POST request to the Django API
**WHEN** the client uses JWT Bearer token auth
**THEN** CSRF validation is not applied (JWT auth is exempt from CSRF)
**AND** the request proceeds if the JWT is valid

### Auth API Endpoints

| Method | Path | Purpose | Auth Required |
|--------|------|---------|--------------|
| POST | `/api/v1/auth/signup` | Create new account | No |
| POST | `/api/v1/auth/login` | Authenticate user | No |
| POST | `/api/v1/auth/logout` | End session / invalidate token | Yes |
| POST | `/api/v1/auth/password/reset` | Request password reset email | No |
| POST | `/api/v1/auth/password/reset/confirm` | Set new password with reset key | No |
| POST | `/api/v1/auth/password/change` | Change password (authenticated) | Yes |
| POST | `/api/v1/auth/email/verify` | Verify email with key | No |
| POST | `/api/v1/auth/email/verify/resend` | Resend verification email | Yes |
| POST | `/api/v1/auth/token/refresh` | Refresh JWT access token (mobile) | No (refresh token required) |
| GET | `/api/v1/users/me` | Get current authenticated user | Yes |

### Development vs Production Auth Settings

| Setting | Development | Production |
|---------|------------|------------|
| SESSION_COOKIE_SECURE | False | True |
| CSRF_COOKIE_SECURE | False | True |
| SESSION_COOKIE_DOMAIN | Not set (localhost) | .example.com |
| CORS_ALLOWED_ORIGINS | ["http://localhost:3000"] | Env var list |
| CSRF_TRUSTED_ORIGINS | ["http://localhost:3000"] | Env var list |
| EMAIL_BACKEND | django.core.mail.backends.console.EmailBackend | Production email (SES, Resend) |
| ACCOUNT_EMAIL_VERIFICATION | "optional" (for dev convenience) | "mandatory" |

## Constraints

1. **Never disable CSRF.** No `@csrf_exempt` decorators, no `CSRF_EXEMPT` settings. Use proper CSRF token forwarding or JWT auth (which is inherently CSRF-safe).
2. **Never store tokens in AsyncStorage.** Mobile tokens must use expo-secure-store (Keychain on iOS, Keystore on Android). AsyncStorage is not encrypted.
3. **Never store JWTs in browser localStorage/sessionStorage.** Web auth uses httpOnly session cookies only.
4. **Session and JWT auth must coexist.** The Django API must accept both session cookies (web) and Bearer tokens (mobile) on the same endpoints.
5. **HEADLESS_ONLY must be True.** Django Allauth's HTML views are disabled. All auth is API-driven.
6. **Email verification is mandatory in production.** Users with unverified emails cannot access authenticated endpoints.
7. **SameSite=None must never be used in production.** Development uses Lax; production uses Lax. None exposes the app to CSRF.
8. **Refresh token rotation is recommended.** Each refresh request should return a new refresh token and invalidate the old one.

## References

- `.planning/research/ARCHITECTURE.md` -- Authentication flow diagrams, dual auth strategy rationale
- `.planning/research/PITFALLS.md` -- Pitfall #2: Django Allauth cross-platform auth misconfiguration
- `.planning/research/STACK.md` -- Django Allauth configuration, CORS setup
