---
phase: 04-web-application
plan: 01
subsystem: ui
tags: [nextjs, shadcn, tailwindcss, theming]

# Dependency graph
requires:
  - phase: 03-shared-packages-type-generation
    provides: shared validation schemas + client hooks
provides:
  - shadcn/ui component registry with DOM-first primitives
  - Theme provider + toaster wiring for the web app
  - Route-grouped /(auth) and /(dashboard) layouts ready for downstream pages
affects: [web-app, auth, dashboard]

# Tech tracking
tech-stack:
  added: [shadcn/ui, next-themes, sonner, tailwindcss@3]
  patterns: [route groups, theme-aware layouts, shadcn registry]

key-files:
  created:
    - apps/web/app/(auth)/layout.tsx
    - apps/web/app/(dashboard)/layout.tsx
    - apps/web/app/base-url.ts
  modified:
    - apps/web/app/globals.css
    - apps/web/package.json
    - apps/web/next.config.ts

key-decisions:
  - "Downgraded to Tailwind CSS 3.4 due to Next.js 15/PostCSS incompatibility with the Tailwind 4 preview."
  - "Exported buildApiBaseUrl from app/base-url.ts so layouts and future pages can share the helper."

patterns-established:
  - "Route-grouped App Router layouts: /(auth) for marketing hero shells and /(dashboard) for sidebar shells."
  - "Theme-aware DOM primitives via shadcn/ui with next-themes + sonner provider wiring."

# Metrics
duration: 23 min
completed: 2026-02-16
---

# Phase 04 Plan 01: Web Shell Summary

**Shadcn-powered auth and dashboard shells with next-themes + toast wiring**

## Performance

- **Duration:** 23 min
- **Started:** 2026-02-16T12:00:31Z
- **Completed:** 2026-02-16T12:23:55Z
- **Tasks:** 3
- **Files modified:** 37

## Accomplishments
- Installed shadcn CLI tooling, next-themes, and supporting deps while wiring a shared `src` alias + cn helper.
- Generated the base shadcn primitives plus theme provider, marketing hero, and dashboard sidebar placeholders for downstream pages.
- Split the App Router into /(auth) and /(dashboard) route groups with hero-backed auth shell, sidebar dashboard shell, and centralized base URL builder.

## Task Commits

Each task was committed atomically:

1. **Task 1: Install shadcn + theming dependencies and configure Tailwind** - `5ce3f4d` (feat)
2. **Task 2: Generate base shadcn UI primitives + theme provider** - `bc4dbd1` (feat)
3. **Task 3: Split App Router into /(auth) and /(dashboard) layouts with providers** - `d1f3c7c` (feat)

## Files Created/Modified
- `apps/web/app/(auth)/layout.tsx` - Marketing hero auth shell with card slot.
- `apps/web/app/(auth)/page.tsx` - DOM-based login form using shadcn Form components.
- `apps/web/app/(dashboard)/layout.tsx` - Sidebar/header dashboard shell wired to ThemeToggle + SidebarProvider.
- `apps/web/app/(dashboard)/dashboard/page.tsx` - Placeholder dashboard content cards and telemetry skeleton.
- `apps/web/app/base-url.ts` - Shared helper exporting the API base URL builder.
- `apps/web/app/layout.tsx` - ThemeProvider + Toaster wrapping AppProviders with hydration-safe `<html>`.
- `apps/web/src/components/**` - shadcn UI primitives, theme provider, marketing hero, dashboard sidebar, and toast helpers.
- `apps/web/package.json` / `pnpm-lock.yaml` - Added shadcn deps, next-themes, sonner, and Tailwind toolchain updates.
- `apps/web/postcss.config.js` / `apps/web/app/globals.css` - Tailwind setup, CSS variables, and base styles.

## Decisions Made
- Tailwind CSS was downgraded to the stable 3.4 toolchain because Next.js 15's built-in PostCSS loader currently rejects the Tailwind 4 preview plugin even when using `@tailwindcss/postcss`. Keeping v3 ensures the web build and lint commands pass consistently.
- The API base URL helper now lives in `app/base-url.ts` so future route groups can import it without duplicating logic.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Downgraded to Tailwind CSS 3 for build stability**
- **Found during:** Task 3 (layout split)
- **Issue:** Next.js 15's PostCSS loader crashed with the Tailwind 4 preview even when using the recommended `@tailwindcss/postcss` plugin, preventing `pnpm --filter web build` from succeeding.
- **Fix:** Reverted to the stable Tailwind 3.4 toolchain, restored classic `@tailwind base/components/utilities` directives, and reintroduced autoprefixer-based PostCSS config so builds and lint/type-check steps pass.
- **Files modified:** apps/web/package.json, apps/web/postcss.config.js, apps/web/app/globals.css, pnpm-lock.yaml
- **Verification:** `pnpm --filter web lint`, `pnpm --filter web type-check`, and `pnpm --filter web build` all succeed.

---

**Total deviations:** 1 auto-fixed (blocking)
**Impact on plan:** Required using the stable Tailwind toolchain to unblock the mandated verification commands; all UI deliverables still match the plan's intent.

## Issues Encountered
- Tailwind CSS 4 preview is incompatible with Next.js 15's PostCSS integration today, causing builds to fail until the project reverted to Tailwind 3.4.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Web shell now exposes theme-aware providers, shadcn primitives, and dedicated /(auth) + /(dashboard) layouts so follow-up plans can focus on auth flows, data wiring, and dashboard content without revisiting structure.

---
*Phase: 04-web-application*
*Completed: 2026-02-16*
