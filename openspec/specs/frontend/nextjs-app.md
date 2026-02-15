# Next.js 15 App Router Specification

> Baseline specification for the Foundation Template.
> This document is the source of truth. All implementations must conform to these specs.

## Overview

The Next.js 15 web application lives at `apps/web/` in the Turborepo monorepo. It uses the App Router (not Pages Router), Server Components by default, Shadcn/ui for the design system, Tailwind CSS for styling, and consumes shared packages (`@repo/api-client`, `@repo/validation`, `@repo/ui`, `@repo/business-logic`) from the monorepo. Authentication uses session cookies proxied through Next.js API rewrites to Django, so the browser never talks directly to Django for auth.

---

## Specifications

### 1. App Router Directory Structure

```
apps/web/
  app/
    (auth)/
      login/
        page.tsx
      signup/
        page.tsx
      reset-password/
        page.tsx
      verify-email/
        page.tsx
      layout.tsx              # Auth layout: centered card, unauthenticated only
    (dashboard)/
      dashboard/
        page.tsx              # Main dashboard view
      settings/
        page.tsx              # Account settings
      profile/
        page.tsx              # User profile
      layout.tsx              # Dashboard layout: sidebar + header, authenticated only
    api/
      auth/
        [...path]/
          route.ts            # Proxy to Django Allauth headless endpoints
      webhooks/
        stripe/
          route.ts            # Stripe webhook receiver (if billing added)
    layout.tsx                # Root layout: providers, fonts, theme
    page.tsx                  # Landing / marketing page (public)
    not-found.tsx             # Custom 404
    error.tsx                 # Global error boundary
    loading.tsx               # Global loading state
  components/                 # Web-specific components (page-level)
    auth/
      login-form.tsx
      signup-form.tsx
      reset-password-form.tsx
    dashboard/
      sidebar.tsx
      header.tsx
      dashboard-shell.tsx
    shared/
      theme-toggle.tsx
      user-avatar.tsx
  lib/
    api.ts                    # Server-side API client (cookie-forwarding)
    auth.ts                   # Auth utility functions
    utils.ts                  # Web-specific helpers
  middleware.ts               # Auth guards, session validation, redirects
  next.config.ts
  tailwind.config.ts
  tsconfig.json
  package.json
```

### 2. Route Groups

Route groups use parenthesized directories to organize routes without affecting the URL path.

| Route Group | URL Prefix | Purpose | Auth Requirement |
|-------------|-----------|---------|------------------|
| `(auth)/` | `/login`, `/signup`, `/reset-password`, `/verify-email` | Authentication pages | Unauthenticated only (redirect to `/dashboard` if logged in) |
| `(dashboard)/` | `/dashboard`, `/settings`, `/profile` | Authenticated application shell | Authenticated only (redirect to `/login` if logged out) |
| `api/` | `/api/auth/*`, `/api/webhooks/*` | API routes (BFF proxy, webhooks) | Varies per route |

### 3. Layout System

#### Root Layout (`app/layout.tsx`)

The root layout wraps every page. It provides:

- `<html>` and `<body>` tags with `suppressHydrationWarning` for dark mode
- Font loading (Inter via `next/font/google`)
- `ThemeProvider` from `next-themes` for dark/light mode
- `QueryClientProvider` from `@tanstack/react-query` for client-side data fetching
- Global metadata (`title`, `description`, `viewport`)

```tsx
// app/layout.tsx
import { Inter } from "next/font/google";
import { ThemeProvider } from "@/components/providers/theme-provider";
import { QueryProvider } from "@/components/providers/query-provider";
import "@/app/globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata = {
  title: "Foundation App",
  description: "Built with Foundation Template",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
          <QueryProvider>
            {children}
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
```

#### Auth Layout (`app/(auth)/layout.tsx`)

- Renders a vertically and horizontally centered card
- No sidebar, no header -- minimal chrome
- Accessible only to unauthenticated users (middleware enforces redirect)

```tsx
// app/(auth)/layout.tsx
export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="w-full max-w-md p-6">
        {children}
      </div>
    </div>
  );
}
```

#### Dashboard Layout (`app/(dashboard)/layout.tsx`)

- Sidebar navigation (collapsible on mobile)
- Top header with user avatar, theme toggle, logout
- Accessible only to authenticated users (middleware enforces redirect)
- Fetches current user data in the layout (Server Component), passes to children via context or props

```tsx
// app/(dashboard)/layout.tsx
import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/auth";
import { Sidebar } from "@/components/dashboard/sidebar";
import { Header } from "@/components/dashboard/header";

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const user = await getCurrentUser();
  if (!user) redirect("/login");

  return (
    <div className="flex h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col">
        <Header user={user} />
        <main className="flex-1 overflow-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
```

### 4. Middleware

The middleware at `apps/web/middleware.ts` handles:

| Concern | Logic |
|---------|-------|
| Auth guard for dashboard routes | Check session cookie; redirect to `/login` if absent or invalid |
| Auth guard for auth routes | Check session cookie; redirect to `/dashboard` if present and valid |
| Session validation | Optionally validate session against Django on each request (configurable) |
| Public routes passthrough | `/`, `/api/webhooks/*`, static assets -- no auth check |

```ts
// middleware.ts
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const AUTH_ROUTES = ["/login", "/signup", "/reset-password", "/verify-email"];
const DASHBOARD_ROUTES = ["/dashboard", "/settings", "/profile"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const sessionCookie = request.cookies.get("sessionid");
  const isAuthenticated = !!sessionCookie;

  // Redirect authenticated users away from auth pages
  if (AUTH_ROUTES.some((route) => pathname.startsWith(route)) && isAuthenticated) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  // Redirect unauthenticated users away from dashboard
  if (DASHBOARD_ROUTES.some((route) => pathname.startsWith(route)) && !isAuthenticated) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|api/webhooks).*)"],
};
```

### 5. Component Organization

| Location | Scope | Examples |
|----------|-------|---------|
| `app/components/` | Web-specific, page-level components | `login-form.tsx`, `sidebar.tsx`, `dashboard-shell.tsx` |
| Shadcn/ui (`components/ui/`) | Design system primitives (generated via `npx shadcn-ui@latest add`) | `button.tsx`, `card.tsx`, `input.tsx`, `dialog.tsx` |
| `@repo/ui` | Cross-platform primitives shared with Expo | `Button`, `Text`, `Input`, `Card` (React Native Web) |
| `@repo/business-logic` | Shared hooks and utilities | `useAuth`, `useUser`, `formatDate` |

Shadcn/ui components are the primary design system for web. The shared `@repo/ui` package provides cross-platform primitives that may be used inside Shadcn/ui compositions or standalone.

### 6. Data Fetching Patterns

#### Server Components (default)

Server Components fetch data directly from Django (server-to-server, no CORS). They use the `@repo/api-client` with cookie forwarding.

```tsx
// app/(dashboard)/dashboard/page.tsx
import { createServerApiClient } from "@/lib/api";

export default async function DashboardPage() {
  const api = await createServerApiClient();
  const { data, error } = await api.GET("/api/v1/users/me");

  if (error) return <div>Error loading dashboard</div>;

  return (
    <div>
      <h1>Welcome, {data.first_name}</h1>
      {/* Dashboard content */}
    </div>
  );
}
```

```ts
// lib/api.ts
import createClient from "openapi-fetch";
import { cookies } from "next/headers";
import type { paths } from "@repo/api-client";

export async function createServerApiClient() {
  const cookieStore = await cookies();
  return createClient<paths>({
    baseUrl: process.env.DJANGO_API_URL,
    headers: {
      cookie: cookieStore.toString(),
    },
  });
}
```

#### Client Components (interactive)

Client Components use `@tanstack/react-query` for data fetching, caching, and mutations. They consume hooks from `@repo/business-logic`.

```tsx
"use client";

import { useUser } from "@repo/business-logic";

export function ProfileForm() {
  const { data: user, isLoading } = useUser();

  if (isLoading) return <Skeleton />;

  return <form>{/* form fields using user data */}</form>;
}
```

#### Pattern Summary

| Context | Method | Auth | Cache |
|---------|--------|------|-------|
| Server Component | `openapi-fetch` via `createServerApiClient()` | Cookie forwarding | Next.js fetch cache |
| Client Component | `@tanstack/react-query` hooks from `@repo/business-logic` | Browser cookies (same-origin via proxy) | React Query cache |
| Server Action / API Route | Direct `fetch` to Django internal URL | Cookie forwarding or service token | No client cache |

### 7. API Routes (BFF Proxy)

Next.js API routes proxy auth requests to Django to keep cookies same-origin.

```ts
// app/api/auth/[...path]/route.ts
import { NextRequest, NextResponse } from "next/server";

const DJANGO_API_URL = process.env.DJANGO_API_URL!;

async function proxyToDjango(request: NextRequest, path: string[]) {
  const apiPath = path.join("/");
  const url = `${DJANGO_API_URL}/api/v1/auth/${apiPath}`;

  const response = await fetch(url, {
    method: request.method,
    headers: {
      "Content-Type": "application/json",
      cookie: request.headers.get("cookie") || "",
    },
    body: request.method !== "GET" ? await request.text() : undefined,
  });

  const data = await response.json();
  const nextResponse = NextResponse.json(data, { status: response.status });

  // Forward Set-Cookie headers from Django
  const setCookie = response.headers.getSetCookie();
  for (const cookie of setCookie) {
    nextResponse.headers.append("Set-Cookie", cookie);
  }

  return nextResponse;
}

export async function GET(req: NextRequest, { params }: { params: { path: string[] } }) {
  return proxyToDjango(req, params.path);
}

export async function POST(req: NextRequest, { params }: { params: { path: string[] } }) {
  return proxyToDjango(req, params.path);
}
```

### 8. next.config.ts

```ts
// next.config.ts
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Transpile React Native Web and monorepo packages
  transpilePackages: [
    "react-native",
    "react-native-web",
    "@repo/ui",
    "@repo/business-logic",
    "@repo/api-client",
    "@repo/validation",
  ],

  // Alias react-native to react-native-web
  webpack: (config) => {
    config.resolve.alias = {
      ...(config.resolve.alias || {}),
      "react-native$": "react-native-web",
    };
    return config;
  },

  // Proxy API requests to Django (same-origin for cookies)
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.DJANGO_API_URL || "http://localhost:8000"}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
```

### 9. Dark Mode Implementation

Dark mode uses `next-themes` integrated with Tailwind CSS.

| Aspect | Implementation |
|--------|---------------|
| Default | System preference (`prefers-color-scheme`) |
| Toggle | `ThemeToggle` component using `useTheme()` from `next-themes` |
| Persistence | `localStorage` via `next-themes` |
| CSS | Tailwind `dark:` variant classes (e.g., `bg-background dark:bg-background`) |
| Shadcn/ui | CSS custom properties in `globals.css` for light/dark themes |
| Flash prevention | `suppressHydrationWarning` on `<html>`, `next-themes` injects script before paint |

```tsx
// components/shared/theme-toggle.tsx
"use client";

import { useTheme } from "next-themes";
import { Button } from "@/components/ui/button";
import { Moon, Sun } from "lucide-react";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
    >
      <Sun className="h-5 w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
      <Moon className="absolute h-5 w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
    </Button>
  );
}
```

### 10. Tailwind CSS + Shadcn/ui Configuration

- Tailwind config extends Shadcn/ui's default theme with CSS custom properties
- Content paths include `app/**`, `components/**`, and `@repo/ui` source
- The `cn()` utility (from `clsx` + `tailwind-merge`) is used for conditional class composition
- Shadcn/ui components are installed into `components/ui/` via CLI and are fully editable

### 11. GIVEN/WHEN/THEN Scenarios

#### Scenario: Page Load as Authenticated User

```
GIVEN a user has a valid session cookie ("sessionid")
  AND the user navigates to /dashboard
WHEN the middleware processes the request
THEN the request passes through without redirect
  AND the DashboardLayout Server Component fetches the user from Django
  AND the dashboard page renders with the user's data
```

#### Scenario: Page Load as Unauthenticated User

```
GIVEN a user has no session cookie
  AND the user navigates to /dashboard
WHEN the middleware processes the request
THEN the middleware redirects to /login (302)
  AND the AuthLayout renders a centered login card
```

```
GIVEN a user has a valid session cookie
  AND the user navigates to /login
WHEN the middleware processes the request
THEN the middleware redirects to /dashboard (302)
  AND the user never sees the login page
```

#### Scenario: Form Submission with Validation

```
GIVEN a user is on the /signup page
  AND the signup form uses a Zod schema from @repo/validation
WHEN the user submits the form with an invalid email
THEN the Zod schema validates client-side
  AND an inline error message appears below the email field
  AND no network request is made to Django
```

```
GIVEN a user is on the /signup page
  AND the signup form passes client-side Zod validation
WHEN the user submits the form
THEN a POST request is sent to /api/auth/signup (proxied to Django)
  AND on success: the session cookie is set, user is redirected to /dashboard
  AND on failure: the server error message is displayed in the form
```

#### Scenario: Server Component Data Fetch

```
GIVEN a Server Component in the dashboard layout needs user data
WHEN the component renders on the server
THEN it calls createServerApiClient() which forwards the session cookie
  AND the Django API validates the session and returns user data
  AND the component renders HTML with the user data (no client-side fetch)
```

```
GIVEN the Django API returns a 401 for an expired session
WHEN the Server Component receives the error
THEN the component calls redirect("/login") from next/navigation
  AND the user is redirected to the login page
```

#### Scenario: Dark Mode Toggle

```
GIVEN the user's system preference is "light"
  AND no theme preference is stored in localStorage
WHEN the page loads
THEN the light theme is applied (no dark: classes active)
  AND the ThemeToggle shows a sun icon
```

```
GIVEN the user clicks the ThemeToggle
WHEN the theme switches from "light" to "dark"
THEN the "dark" class is added to the <html> element
  AND Tailwind dark: variant classes activate
  AND the preference is persisted to localStorage
  AND subsequent page loads use the stored preference
```

---

## Constraints

- **No Pages Router.** App Router only. No `pages/` directory.
- **No direct Django calls from the browser.** All API traffic goes through Next.js rewrites or API routes to maintain same-origin cookies.
- **No business logic in API routes.** API routes proxy to Django or handle webhooks. No database queries, no auth logic, no data transformations beyond header manipulation.
- **Server Components by default.** Only add `"use client"` when the component needs interactivity (event handlers, hooks, browser APIs).
- **No `axios`.** Use `openapi-fetch` (wraps native `fetch`) via `@repo/api-client`.
- **No manual API types.** All API types are generated from the Django OpenAPI spec via `openapi-typescript`.
- **Shadcn/ui is the web design system.** Do not introduce Material UI, Chakra, or other component libraries.
- **Shared `@repo/ui` components are supplementary**, not replacements for Shadcn/ui on web.

---

## References

- `.planning/research/STACK.md` -- Supporting stack decisions (openapi-typescript, openapi-fetch, Shadcn/ui, Tailwind, react-query)
- `.planning/research/ARCHITECTURE.md` -- App Router structure, BFF proxy pattern, auth flow, monorepo layout
- `.planning/research/PITFALLS.md` -- Auth misconfiguration (Pitfall 2), RNW component overreach (Pitfall 3), Docker hot reload (Pitfall 7)
- `.planning/PROJECT.md` -- Core requirements, constraints, scope
