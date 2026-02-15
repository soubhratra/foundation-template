# Web Frontend Specification (Next.js)

> Applies to `apps/web/` in the monorepo.
> This document defines web-only patterns for Next.js App Router, Shadcn/ui usage,
> and shared frontend conventions. It complements `openspec/specs/foundation/conventions.md`.

## Overview

The web app uses Next.js 15+ App Router with server components by default,
Tailwind CSS 4, and Shadcn/ui for all UI primitives. The app is structured
to support fast iteration, consistent UI, and a clear separation between
server data fetching and client interactivity.

## Project Structure

Root path: `apps/web/`

```
apps/web/
  src/
    app/                     # Next.js App Router
      (auth)/                # Unauthenticated route group
      (dashboard)/           # Authenticated route group
      api/                   # BFF/proxy routes
      layout.tsx             # Root layout (providers, fonts)
      page.tsx               # Landing or app entry
    components/              # Shared UI components (Shadcn + app-specific)
    hooks/                   # Client hooks (React Query, Zustand)
    lib/                     # Utilities, API client, query keys
    styles/                  # Tailwind base and global styles
```

## App Router Patterns

### Server Components by Default
- Pages and layouts in `apps/web/src/app/` are server components unless
  they need client state or effects.
- Add "use client" only when necessary (forms, local state, browser APIs).
- Keep data fetching in server components when possible.

### Route Groups
- Auth routes live under `apps/web/src/app/(auth)/`.
- Authenticated app routes live under `apps/web/src/app/(dashboard)/`.
- Use route group layouts for shared UI shells (auth card, dashboard layout).

### BFF Proxy Routes
- API proxy routes live in `apps/web/src/app/api/`.
- Use `apps/web/src/app/api/auth/[...path]/route.ts` to forward
  auth-related requests to the Django API.

## Shadcn/ui Conventions

- Shadcn/ui is the only web UI primitive library.
- Generated Shadcn components live in `apps/web/src/components/ui/`.
- App-level components compose Shadcn primitives in `apps/web/src/components/`.
- Use Tailwind CSS 4 utilities for layout and spacing; avoid custom CSS
  unless a global style is required.
- Forms use React Hook Form + Zod with Shadcn form patterns.

## Data and State

- Server state uses React Query (TanStack Query).
- Client-only state uses Zustand in `apps/web/src/hooks/` or `apps/web/src/lib/`.
- Type-safe API calls use generated types from `@repo/shared-types`.

## Monorepo Integration

- Shared Zod schemas live in `packages/schemas/` and are imported into
  `apps/web/src/` for client-side validation.
- Shared UI primitives for cross-platform usage live in `packages/ui-primitives/`.
- Do not add `apps/api/` as a pnpm workspace dependency.

## UX Criteria (Web)

- Clear auth entry: login and signup are first-class pages with a simple,
  scannable layout in `apps/web/src/app/(auth)/`.
- Consistent page structure: every page defines a title, primary action,
  and a predictable content layout.
- Form feedback: inline validation errors for fields, non-field errors in a
  toast/alert, and loading states on submit.
- Empty states: every list and dashboard view includes a helpful empty state
  with a single next-step action.
- Accessibility baseline: focus states visible, label-to-input associations,
  and keyboard navigability for forms and dialogs.

## Constraints

1. App Router only. No Pages Router usage.
2. Shadcn/ui for all web primitives. Do not install other UI libraries.
3. Server components by default; client components only when required.
4. File naming uses kebab-case (per `openspec/specs/foundation/conventions.md`).
