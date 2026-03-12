# Deferred Items — Phase 20 Social Auth

## Pre-existing TypeScript Errors (Out of Scope)

These errors existed before plan 20-05 execution and are unrelated to social auth changes.

### 1. apps/mobile/app/\_layout.tsx — enableDevtools prop mismatch

**Error:** `Property 'enableDevtools' does not exist on type 'IntrinsicAttributes & AuthProviderProps'`

**Context:** `_layout.tsx` passes `enableDevtools={false}` to `AuthProvider`, but `AuthProviderProps` does not include that prop. This was masked before because `@repo/business-logic/dist/index.d.ts` was missing (package was never built), causing tsc to fall back to `any` types.

**Discovered:** During plan 20-05 execution (after rebuilding `@repo/business-logic`)

**Fix required:** Either add `enableDevtools` prop to `AuthProviderProps` in `packages/business-logic/src/auth-provider.tsx`, or remove the prop from `_layout.tsx`.
