# Mobile Frontend Specification (Expo)

> Applies to `apps/mobile/` in the monorepo.
> This document defines Expo Router patterns, monorepo configuration, and
> shared frontend conventions for React Native.

## Overview

The mobile app uses Expo (managed workflow) with Expo Router for navigation.
It shares types and schemas with the web app through `packages/` and
prioritizes native UX patterns while keeping business logic shared when feasible.

## Project Structure

Root path: `apps/mobile/`

```
apps/mobile/
  src/
    app/                     # Expo Router
      (auth)/                # Auth stack
      (tabs)/                # Tab navigation
      _layout.tsx            # Root layout
    components/              # Reusable UI components
    hooks/                   # React Query + local hooks
    lib/                     # API client, query keys, helpers
    assets/                  # Images, fonts, icons
```

## Expo Router Patterns

- Auth screens live in `apps/mobile/src/app/(auth)/` with a stack layout.
- Main app lives in `apps/mobile/src/app/(tabs)/` using tab navigation.
- Root layout in `apps/mobile/src/app/_layout.tsx` handles session gating.

## Monorepo Configuration

- Mobile app is a pnpm workspace under `apps/mobile/`.
- Shared types are imported from `@repo/shared-types`.
- Shared Zod schemas are imported from `packages/schemas/`.
- Shared UI primitives live in `packages/ui-primitives/` and are used
  only for basic atoms (Text, Button, Input, Layout). Keep platform
  navigation and complex UI native to mobile.

## Data and State

- Server state uses React Query (TanStack Query).
- Client-only state uses Zustand where necessary.
- API calls use generated types from `@repo/shared-types`.

## UX Criteria (Mobile)

- Navigation is mobile-native: tabs for primary sections, stacks for
  screen-to-screen flow, and modal presentation for short actions.
- Touch targets are at least 44x44 px and spacing favors thumb reach.
- Forms provide inline errors, disable submit during requests, and
  show clear success states.
- Loading states are visible at screen entry and on key actions
  (skeletons or spinners, no blank screens).
- Offline tolerance: show a friendly retry state when network calls fail.

## Constraints

1. Expo managed workflow only. No bare workflow.
2. Expo Router for navigation. No custom navigation stacks outside it.
3. File naming uses kebab-case (per `openspec/specs/foundation/conventions.md`).
4. Share primitives only; do not force web layouts onto mobile.
