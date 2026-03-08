---
phase: 11-api-endpoints-billing-frontend
plan: "03"
subsystem: frontend-data-layer
tags: [billing, server-actions, next-js, typescript, sidebar]
dependency_graph:
  requires: []
  provides:
    - billing.config.ts (BillingConfig type system and default config)
    - ServerApi.getBillingStatus / getBillingSubscription / listBillingInvoices / previewBillingProration
    - billing-actions.ts (5 server actions for billing mutations)
    - sidebar Billing nav item
  affects:
    - apps/web/src/lib/api/server.ts
    - apps/web/src/actions/billing-actions.ts
    - apps/web/src/components/dashboard/sidebar.tsx
tech_stack:
  added: []
  patterns:
    - AnyApiClient cast pattern for ungenerated API paths (temporary, replaced post type-gen)
    - upstreamFetch for billing read methods in getServerApi()
    - ActionResponse<TField> reuse from profile-actions.ts
    - revalidatePath('/billing') after all mutating server actions
key_files:
  created:
    - apps/web/billing.config.ts
    - apps/web/src/actions/billing-actions.ts
  modified:
    - apps/web/src/lib/api/server.ts
    - apps/web/src/components/dashboard/sidebar.tsx
decisions:
  - Use AnyApiClient (any-typed) cast for POST mutation paths in billing-actions.ts until turbo run generate:types regenerates @repo/api-client; annotated with TODO comments
  - upstreamFetch for read methods (getBillingStatus etc.) — consistent with requestPasswordChange pattern in same file
  - billing.config.ts placed at apps/web root (same level as package.json) for clean import path billing.config
  - Sidebar Billing item placed after Activity (index 4), matching nav order from CONTEXT.md: Dashboard -> Profile -> Activity -> Settings -> Billing
metrics:
  duration_seconds: 154
  completed_date: "2026-03-08"
  tasks_completed: 2
  files_created: 2
  files_modified: 2
---

# Phase 11 Plan 03: Frontend Data Layer Summary

**One-liner:** Config-driven billing data layer — BillingConfig type system, 4 server-side read methods on getServerApi(), and 5 server actions for billing mutations, with Billing sidebar nav item.

## What Was Built

Plan 03 establishes the complete frontend data contract that Plan 04 (billing page UI) will consume. This plan runs in Wave 1 and is independent of Plans 01/02 (Django backend).

### billing.config.ts

Single developer-facing customization surface for the billing module. Exports:

- `BillingPlanDisplay` — plan card data (id, name, features, optional badge)
- `SubscriptionState` — union of 6 states mapping 1:1 to Django SubscriptionStatus enum
- `BillingActionType` — 5 action button types
- `BillingSection` — section config with id, visibility toggle, and heading
- `BillingConfig` — root type composing sections, plans, actions map, and copy strings
- `billingConfig` const — default config with 3 plans (free/pro/enterprise), 6 state-to-action mappings, 9 copy strings

### server.ts extensions

Added 5 exported interfaces to server.ts (temporary, replaced after `turbo run generate:types`):
`BillingStatusOut`, `SubscriptionDetailOut`, `InvoiceOut`, `InvoiceListOut`, `ProrationPreviewOut`

Extended `ServerApi` interface with 4 read methods:

- `getBillingStatus()` — lightweight status for dashboard layout banner; returns null on error (never blocks layout)
- `getBillingSubscription()` — full subscription detail for /billing page
- `listBillingInvoices(limit?)` — invoice list, default limit=10
- `previewBillingProration(planId, billingPeriod)` — proration preview amounts

All implemented via `upstreamFetch` (cookie-forwarding fetcher already in closure) with typed JSON casts.

### billing-actions.ts

5 server actions:

- `changePlanAction(planId, billingPeriod)` — POST change, revalidatePath('/billing')
- `cancelSubscriptionAction()` — POST cancel, revalidatePath('/billing')
- `reactivateSubscriptionAction()` — POST reactivate, revalidatePath('/billing')
- `createPortalSessionAction()` — POST portal-session, returns portal_url for client redirect
- `previewProrationAction(planId, billingPeriod)` — preview only, NO revalidatePath (read-only)

All follow ActionResponse<TField> envelope from profile-actions.ts. Mutation paths use `AnyApiClient` cast with TODO comment for post-type-gen replacement.

### sidebar.tsx

Added `CreditCard` to lucide-react import. Appended Billing nav item to `dashboardNavItems` after Activity (per CONTEXT.md nav order).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] as never cast rejected by TypeScript for POST body**

- **Found during:** Task 2 TypeScript verification
- **Issue:** Plan spec showed `as any` cast via `client.POST("path" as any, {...})` but the typed ApiClient still rejected the body argument shape when the path was cast as never
- **Fix:** Created `AnyApiClient` type alias (`type AnyApiClient = any`) and assigned `const client: AnyApiClient = api.client` before POST calls. This preserves the intent (bypass ungenerated types) while satisfying TypeScript without propagating `any` into the function signatures
- **Files modified:** apps/web/src/actions/billing-actions.ts
- **Commit:** 4b520af

None of the other deviations affected plan scope or architecture.

## Self-Check: PASSED

Files verified:

- FOUND: apps/web/billing.config.ts
- FOUND: apps/web/src/actions/billing-actions.ts
- FOUND: apps/web/src/lib/api/server.ts (modified)
- FOUND: apps/web/src/components/dashboard/sidebar.tsx (modified)

Commits verified:

- FOUND: b25ed75 (Task 1 — billing.config.ts)
- FOUND: 4b520af (Task 2 — server.ts + billing-actions.ts + sidebar.tsx)

TypeScript: 0 errors (`npx tsc --noEmit` clean)
