# Phase 04: web-application - Research

**Researched:** 2026-02-16
**Domain:** Next.js 15 web auth experience & dashboard shell
**Confidence:** MEDIUM

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions

- Root `/` renders the login form immediately with a small marketing blurb/hero; no separate marketing landing.
- Signup and password reset each live on their own dedicated routes (`/signup`, `/reset`) with full-page forms.
- Users must verify email before logging in; unverified accounts cannot enter the UI.
- After auth success we respect any `?next` param captured by middleware and default to `/dashboard`.
- Desktop layout uses a persistent left sidebar with logo and links to Dashboard, Profile, Settings (include an Activity/Log placeholder to show navigation depth) plus a top header.
- Header includes user avatar menu (profile/logout) and the dark-mode toggle; planner can surface toast/notifications there later.
- On mobile/tablet the sidebar collapses behind a hamburger-triggered sheet; header stays visible for toggle + avatar.
- Protected routes redirect unauthenticated visitors to `/login?next=...` immediately.
- While the session is being validated (SSR or client hydration) show a skeleton version of the destination page rather than a blank screen.
- If a session expires mid-flow, force redirect back to `/login` and show a flash/toast explaining the session ended.
- Default auth middleware + hooks should honor `redirect` query params so successful logins land on the originally requested page, falling back to `/dashboard`.
- Ship a comprehensive but minimal/unopinionated design system baseline (buttons, inputs, cards, tables, alerts, toggle, etc.) aligned with the shared UI primitives so downstream repos can reskin easily.
- Provide both light and dark modes with a reliable toggle but keep the palette neutral (grays + accent) so product teams can extend it.

### Claude's Discretion

- Exact marketing blurb copy, imagery, and layout around the login card.
- Visual style of skeleton/loading states and the animation when sidebars collapse.
- Microcopy on session-expired toast and inline error wording.

### Deferred Ideas (OUT OF SCOPE)

- None — discussion stayed within phase scope.
  </user_constraints>

## Summary

Next.js 15.1 App Router remains the foundation for this phase, but two breaking changes are critical for planners: the legacy `middleware.ts` contract has been renamed to `proxy.ts`, and the platform now expects route groups plus nested layouts to separate unauthenticated `(auth)` surfaces from the `(dashboard)` shell (Next.js docs v16.1.6: layouts/pages, route groups, proxy). Authentication must therefore be enforced before render inside `proxy.ts`, with redirects preserving `redirect` search params, while page components stay focused on rendering data coming from `@repo/business-logic`’s `AuthProvider` and TanStack Query bundle.

The design system brief requires shipping shadcn/ui-derived primitives (buttons, inputs, cards, tables, sheet, dropdown, toggle) layered with Tailwind CSS 4 utility tokens and a neutral palette. Compared to the current `@repo/ui` React Native primitives, web pages should live under `apps/web/src/components/ui/` so that shadcn code generation and class-variance-authority drive styling, while the `ThemeProvider` from `next-themes` adds synchronized light/dark modes (shadcn docs: Next install + dark mode). Skeletons for auth validation live in `loading.tsx` files and must mirror the dashboard shell structure to avoid layout shift (Next.js docs: loading UI). React Hook Form + Zod continue to power all forms through the shared `@repo/validation` package, meaning every screen shares consistent validation, error surfacing, and submission states.

**Primary recommendation:** Build the auth and dashboard route groups as server-first layouts protected by `proxy.ts`, hydrate them through the existing `AuthProvider` + TanStack Query bundle, and compose every UI surface from shadcn-generated primitives styled by Tailwind CSS 4 with `next-themes` managing dark mode.

## Standard Stack

### Core

| Library               | Version   | Purpose                                                                 | Why Standard                                                                                                                        |
| --------------------- | --------- | ----------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| next                  | 15.1.0    | App Router, nested layouts, proxy routing, streaming                    | Required by foundation stack; App Router features (route groups, proxy) unlock skeletons and SSR auth gates (Next.js docs v16.1.6). |
| react / react-dom     | 19.0.0    | React 19 concurrent features + Server Components                        | Matches Next 15 peer deps and enables Suspense-based skeletons plus async Server Components.                                        |
| tailwindcss           | 4.0.0     | Utility-first styling layer                                             | Already configured in repo; ties directly into shadcn tokens and makes neutral theming easy.                                        |
| shadcn/ui CLI         | latest    | Generates DOM-ready UI primitives under `apps/web/src/components/ui/`   | Official shadcn workflow for Next.js; ensures accessible buttons, cards, dialogs, tables (shadcn docs).                             |
| @tanstack/react-query | 5.90.21   | Declarative server-state caching and mutations                          | Bundled by `@repo/business-logic` to wrap openapi client, handles session-aware queries and skeleton hydration.                     |
| @repo/business-logic  | workspace | Ships `AuthProvider`, `useAuth`, token storage, and shared query client | Centralizes auth/session logic for both web and mobile (`packages/business-logic/src/auth-provider.tsx`, `hooks/use-auth.ts`).      |

### Supporting

| Library                                   | Version         | Purpose                                                  | When to Use                                                                                           |
| ----------------------------------------- | --------------- | -------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| react-hook-form                           | 7.71.1          | Lightweight form controller with RHF + React 19          | Every login/signup/reset form; use controllers when integrating shadcn inputs (React Hook Form docs). |
| @hookform/resolvers + zod                 | 3.10.0 / 3.23.8 | Schema validation + resolver powering `@repo/validation` | Use `zodResolver` with shared schemas for parity with backend and mobile (Zod docs).                  |
| next-themes                               | 0.3.x           | Theme context + class toggling for dark mode             | Wrap root layout + header toggle to satisfy light/dark requirement (shadcn dark mode doc).            |
| class-variance-authority + tailwind-merge | 0.7.x / 2.x     | Compose shadcn variant classes                           | Required when extending generated components (buttons, cards) with accent palette.                    |
| lucide-react                              | 0.370.x         | Icon set for sidebar nav + hero                          | Standard icon library in shadcn registry for avatar, hamburger, and navigation glyphs.                |
| sonner (toast)                            | 1.5.x           | Lightweight toast for session-expired flashes            | Use for session-ended notifications triggered by `useAuth` error events.                              |

### Alternatives Considered

| Instead of            | Could Use                          | Tradeoff                                                                                                   |
| --------------------- | ---------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `proxy.ts` guard      | Client-side `useEffect` auth check | Cannot stop SSR route access, ignores Next 15 rename, and breaks locked redirect behavior.                 |
| TanStack Query bundle | SWR or manual fetch + context      | Duplicates `@repo/business-logic` capabilities (token headers, invalidation) and would desync from mobile. |
| shadcn/ui             | Hand-written Tailwind components   | Slower to ship, harder to standardize variants and dark mode, and contradicts design system requirement.   |

**Installation:**

```bash
cd apps/web
pnpm dlx shadcn@latest init --force
pnpm add next-themes class-variance-authority tailwind-merge lucide-react sonner
pnpm add react-hook-form @hookform/resolvers zod
pnpm shadcn add button input card form table alert dropdown-menu sheet sidebar switch skeleton toast
```

## Architecture Patterns

### Recommended Project Structure

```
apps/web/src/
  app/
    proxy.ts                # Session-aware guard (Next 15 proxy)
    (auth)/
      layout.tsx            # Hero + login card shell
      login/page.tsx
      signup/page.tsx
      reset/page.tsx
      verify-email/page.tsx
      loading.tsx           # Skeleton mirroring auth card
    (dashboard)/
      layout.tsx            # Sidebar + header shell
      dashboard/page.tsx
      profile/page.tsx
      settings/page.tsx
      activity/page.tsx
      loading.tsx           # Skeleton for shell sections
    api/auth/[...path]/route.ts # Proxy to Django auth endpoints
  components/
    ui/                     # shadcn primitives
    auth/                   # Form + hero composites
    dashboard/              # Sidebar, header, widgets
  hooks/
    use-session-toast.ts    # Hooks around useAuth() status
  lib/
    auth/                   # SSR helpers, cookie parsing
    theme/                  # Theme constants + accent palette
```

### Pattern 1: Route-grouped layouts

**What:** Separate `(auth)` and `(dashboard)` route groups with dedicated layouts to share marketing hero vs. authenticated shell states (Next.js docs: layouts/pages + route groups).
**When to use:** Any page under `/`, `/login`, `/signup`, `/reset`, `/dashboard`, `/profile`, `/settings`, `/activity`.
**Example:**

```tsx
// Source: Next.js docs (v16.1.6) — route group layouts
export default function AuthLayout({ children }: LayoutProps<"/(auth)">) {
  return (
    <section className="grid min-h-screen lg:grid-cols-[minmax(320px,480px)_1fr]">
      <div className="flex flex-col justify-center bg-muted px-10 py-16">
        <MarketingHero />
      </div>
      <div className="flex items-center justify-center px-6 py-16">
        <AuthCard>{children}</AuthCard>
      </div>
    </section>
  );
}
```

### Pattern 2: Proxy-guarded session redirects

**What:** Use root-level `proxy.ts` to inspect cookies before routing, redirect unauthenticated traffic to `/login?redirect=...`, and short-circuit expired sessions (Next.js proxy docs v16.1.6).
**When to use:** Every navigation except static assets and public auth routes.
**Example:**

```ts
// Source: Next.js proxy docs (v16.1.6)
import { NextResponse, type NextRequest } from "next/server";
import { validateSession } from "@/lib/auth/server";

const PUBLIC_PATHS = ["/", "/login", "/signup", "/reset", "/verify-email"];

export async function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  if (PUBLIC_PATHS.some((path) => pathname.startsWith(path))) {
    return NextResponse.next();
  }

  const session = await validateSession(request.cookies);
  if (!session?.isAuthenticated) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("redirect", pathname + request.nextUrl.search);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|api/).*)"],
};
```

### Pattern 3: AuthProvider + skeleton handoff

**What:** Wrap the entire app with `AuthProvider` (from `packages/business-logic`) inside `AppProviders`, surface `useAuth()` inside route layouts to render skeleton shells while `isLoading` is true, and pair them with `loading.tsx` for navigation skeletons (Next.js loading docs + existing provider code).
**When to use:** Dashboard shell layout, header avatar menu, session-expired toast logic.
**Example:**

```tsx
// Source: packages/business-logic + Next.js loading docs
export default function DashboardLayout({ children }: LayoutProps<"/(dashboard)">) {
  const { isLoading, isAuthenticated } = useAuth();

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  if (!isAuthenticated) {
    redirect("/login");
  }

  return (
    <Shell>
      <Sidebar />
      <main>{children}</main>
    </Shell>
  );
}
```

### Anti-Patterns to Avoid

- **Client-only guard:** Waiting for `useEffect` to validate sessions causes unauthorized flashes and violates locked redirect behavior; enforce in `proxy.ts` instead.
- **Mixing RN and DOM primitives:** Reusing `@repo/ui` React Native components in web layouts blocks Tailwind styling and SSR; stick to shadcn DOM components inside `apps/web`.
- **Skeleton divergence:** Designing `loading.tsx` that looks different from the final layout causes layout jump and defeats “mirror layout” decision.

## Don't Hand-Roll

| Problem                  | Don't Build                      | Use Instead                                                    | Why                                                                                                                      |
| ------------------------ | -------------------------------- | -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| Session-aware API client | Custom fetch wrappers            | `@repo/api-client` + `AuthProvider` bundle                     | Already covers version headers, bearer/session tokens, and TanStack Query cache invalidation.                            |
| Form state + validation  | Manual `useState` + ad-hoc regex | React Hook Form + `@repo/validation` Zod schemas               | Matches backend validation, plugs into shadcn form components, and handles error summaries (React Hook Form + Zod docs). |
| Theme toggling           | CSS toggles + `localStorage`     | `next-themes` `ThemeProvider` with `suppressHydrationWarning`  | Handles SSR, respects OS preference, and is the workflow shadcn documents.                                               |
| UI primitives            | Plain `<div>` wrappers           | shadcn/ui CLI components (button, card, table, sidebar, sheet) | Provides accessible keyboard interactions and ready-made Tailwind variants.                                              |
| Toast notifications      | Custom portal                    | `sonner` (already used in shadcn blocks)                       | Works with React 19, SSR-safe, includes promise helpers for session-expired flows.                                       |

**Key insight:** Lean on the shared packages (`@repo/business-logic`, `@repo/api-client`, `@repo/validation`) and shadcn’s registry so that both web and mobile share validation/auth logic while the web app stays customizable through Tailwind tokens.

## Common Pitfalls

### Pitfall 1: Still using `middleware.ts`

**What goes wrong:** Next.js 15 renamed middleware to `proxy.ts`; keeping the old file prevents auth guards from running.
**Why it happens:** Many templates still reference middleware guides.
**How to avoid:** Rename to `proxy.ts`, export `proxy()` plus `config.matcher`, and keep matchers aligned with Next docs.
**Warning signs:** Requests hitting protected routes without cookies never redirect.

### Pitfall 2: Theme flicker during hydration

**What goes wrong:** Without `ThemeProvider` + `suppressHydrationWarning`, light/dark classes mismatch between SSR and client, causing flashes.
**Why it happens:** `next-themes` requires wrapping `<html>` and forwarding props (shadcn dark mode doc).
**How to avoid:** Wrap root layout with `ThemeProvider` (attribute="class", enableSystem) and add `suppressHydrationWarning` to `<html>`; store toggle state in header menu.
**Warning signs:** Lighthouse flags “background color was painted twice,” or the dark mode toggle resets on refresh.

### Pitfall 3: Skeleton doesn’t mirror final layout

**What goes wrong:** Loading states that differ from the dashboard layout cause major layout shift when `useAuth` resolves.
**Why it happens:** `loading.tsx` is treated as placeholder instead of structural skeleton (Next.js loading docs).
**How to avoid:** Build `DashboardSkeleton` using the same sidebar/header grid and placeholder cards; reuse components between `loading.tsx` and `DashboardLayout`.
**Warning signs:** CLS spikes, or QA notes “content jumps” while session validates.

### Pitfall 4: Forgetting CSRF/session headers on mutations

**What goes wrong:** Django rejects POSTs when `X-CSRFToken` or session headers are missing.
**Why it happens:** Manual fetch calls bypass `@repo/api-client` or `useAuth` helper that sets tokens (see `packages/business-logic/src/hooks/use-auth.ts`).
**How to avoid:** Use the provided mutations (`login`, `logout`, etc.) or call the API client so CSRF + cookie credentials are included.
**Warning signs:** 403 responses with `CSRF token missing` during form submissions.

## Code Examples

### Proxy guard enforcing redirects

```ts
// Based on Next.js proxy docs (v16.1.6)
export async function proxy(request: NextRequest) {
  const publicPath = PUBLIC_PATHS.some((path) => request.nextUrl.pathname.startsWith(path));
  if (publicPath) {
    return NextResponse.next();
  }

  const sessionCookie = request.cookies.get("sessionid")?.value;
  if (!sessionCookie) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("redirect", request.nextUrl.pathname + request.nextUrl.search);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}
```

### Dashboard loading skeleton mirroring layout

```tsx
// Based on Next.js loading docs (v16.1.6)
export default function Loading() {
  return (
    <div className="grid min-h-screen grid-cols-[280px_1fr]">
      <aside className="bg-muted px-6 py-8">
        <Skeleton className="h-10 w-32 mb-6" />
        <SkeletonList count={4} />
      </aside>
      <div className="p-8 space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
          <SkeletonCard count={6} />
        </div>
      </div>
    </div>
  );
}
```

### Login form using React Hook Form + Zod resolver

```tsx
// Based on React Hook Form + Zod docs
const form = useForm<LoginInput>({
  resolver: zodResolver(loginSchema),
  defaultValues: { email: "", password: "", remember: false },
});

const onSubmit = form.handleSubmit(async (values) => {
  await login.mutateAsync(values);
  router.push(nextRedirect ?? "/dashboard");
});

return (
  <Form {...form}>
    <form onSubmit={onSubmit} className="space-y-4">
      <FormField
        name="email"
        control={form.control}
        render={({ field }) => <Input label="Email" type="email" autoComplete="email" {...field} />}
      />
      <FormField
        name="password"
        control={form.control}
        render={({ field }) => (
          <Input label="Password" type="password" autoComplete="current-password" {...field} />
        )}
      />
      <Button loading={login.isPending} className="w-full" type="submit">
        Sign in
      </Button>
    </form>
  </Form>
);
```

## State of the Art

| Old Approach                             | Current Approach                                   | When Changed                                | Impact                                                                      |
| ---------------------------------------- | -------------------------------------------------- | ------------------------------------------- | --------------------------------------------------------------------------- |
| `middleware.ts` auth guard               | `proxy.ts` (renamed in Next 16)                    | Next.js 16.0 rename (doc v16.1.6)           | Must rename + update exports or auth checks never run.                      |
| Inline CSS or localStorage theme toggles | `next-themes` `ThemeProvider` with class attribute | Documented in shadcn dark-mode guide (2025) | Prevents hydration warnings and shares logic with mobile/reskin teams.      |
| Manual fetch + context for `/api/v1`     | `@repo/api-client` + TanStack Query bundle         | Added in shared packages (current repo)     | Centralizes headers, retries, and cache invalidation while matching mobile. |

**Deprecated/outdated:**

- middleware-based guards — replaced by proxy in Next 15+.
- React Native-based web primitives in `@repo/ui` for DOM layouts — they rely on react-native-web and fight Tailwind; use shadcn DOM components instead.

## Open Questions

1. **Branding assets for the auth hero**
   - What we know: Layout must show “small marketing blurb/hero.”
   - What's unclear: Whether imagery copy comes from config, CMS, or hardcoded placeholders.
   - Recommendation: Default to placeholder copy + neutral illustration component and expose props so downstream projects can inject real assets later.
2. **Activity/log placeholder depth**
   - What we know: Sidebar must show an Activity/Log stub.
   - What's unclear: Should the `/activity` page include sample table data or stay empty?
   - Recommendation: Plan for a skeleton table with mocked rows sourced from the shadcn data-table example while keeping data fetching abstracted.

## Sources

### Primary (HIGH confidence)

- Next.js Docs v16.1.6 — Layouts & Pages, Route Groups, Proxy, Data Fetching, Loading UI (`https://nextjs.org/docs/app/building-your-application/...`).
- `openspec/specs/foundation/auth.md` — Dual auth + CSRF requirements for all clients.
- `packages/business-logic/src/auth-provider.tsx`, `packages/business-logic/src/hooks/use-auth.ts` — Existing AuthProvider/query bundle implementation.
- shadcn/ui Docs — Next.js installation & dark mode workflow (`https://ui.shadcn.com/docs/installation/next`, `https://ui.shadcn.com/docs/dark-mode/next`).
- React Hook Form Docs — Get Started (`https://react-hook-form.com/get-started`).
- Zod Docs — Basic usage (`https://zod.dev/?id=basic-usage`).

### Secondary (MEDIUM confidence)

- Repository observations of current `apps/web/app/*` structure and `packages/ui` primitives (React Native-based) to highlight gaps to close during planning.

### Tertiary (LOW confidence)

- None; all statements reference official docs or current repo code.

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — matches package.json + official docs, limited ambiguity.
- Architecture: MEDIUM — route grouping and skeleton strategy inferred from specs + docs but final component boundaries still flexible.
- Pitfalls: MEDIUM — derived from Next 15 changes + repo gaps; needs validation during planning.

**Research date:** 2026-02-16
**Valid until:** 2026-03-18 (Next.js + shadcn release cadence ~monthly)
