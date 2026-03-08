---
phase: 11-api-endpoints-billing-frontend
plan: "04"
subsystem: billing-ui
tags: [billing, next.js, server-components, shadcn, stripe]
dependency_graph:
  requires: [11-03]
  provides: [billing-page-ui, past-due-banner, billing-return-page]
  affects: [apps/web/app/(dashboard)]
tech_stack:
  added: []
  patterns:
    - Async Next.js layout with try/catch billing status check
    - Config-driven UI via billing.config.ts with no React Context
    - Server actions passed as props from server component to client component
    - Sheet modals (side="bottom") for proration preview and cancel confirmation
    - baseUrl-relative import for billing.config.ts (not @/ alias since config is at web root)
key_files:
  created:
    - apps/web/src/components/dashboard/past-due-banner.tsx
    - apps/web/app/(dashboard)/billing/page.tsx
    - apps/web/app/(dashboard)/billing/billing-client.tsx
    - apps/web/app/(dashboard)/billing/return/page.tsx
  modified:
    - apps/web/app/(dashboard)/layout.tsx
decisions:
  - "billing.config imported as 'billing.config' (baseUrl-relative) not '@/billing.config' since tsconfig @/* maps to ./src/* only and billing.config.ts lives at web root"
  - "PastDueBanner is self-contained client component importing createPortalSessionAction directly — no prop drilling from server layout"
  - "BillingPage passes server actions as props to BillingClient (stable reference, TypeScript-safe pattern for server→client action delegation)"
  - "deriveSubscriptionState() maps cancel_at_period_end=true to 'cancel_at_period_end' state before checking status — ensures reactivate button shows correctly"
metrics:
  duration_seconds: 151
  completed_date: "2026-03-08"
  tasks_completed: 2
  files_changed: 5
---

# Phase 11 Plan 04: Billing UI — Dashboard Banner, Billing Page, Return Page Summary

Complete billing frontend: async layout past-due banner + full /billing page (plan cards, invoice table, Sheet modals) + /billing/return success page, all config-driven from billing.config.ts.

## What Was Built

### Task 1: Dashboard Layout + PastDueBanner (commits: 0f6df6c)

- `apps/web/app/(dashboard)/layout.tsx` converted from sync to `async function` with billing status fetch wrapped in try/catch
- `apps/web/src/components/dashboard/past-due-banner.tsx` created as self-contained "use client" component that imports `createPortalSessionAction` directly — no prop drilling needed from server layout
- Banner renders above `<main>` when `status === "past_due"`, hidden otherwise
- Billing failures never block layout render (silent catch)

### Task 2: Billing Page + Client Component + Return Page (commits: 5a7bab2)

- `apps/web/app/(dashboard)/billing/page.tsx`: async server component fetching subscription + invoices in parallel via `Promise.all` with individual `.catch()` fallbacks
- `apps/web/app/(dashboard)/billing/billing-client.tsx`: full interactive client component with:
  - **Plan overview section**: current plan name, status badge, cancel_at_period_end badge, renewal date, action buttons (cancel/reactivate/portal)
  - **Plan selection section**: 2-col grid of plan cards with features list, badges, and Upgrade/Select buttons triggering proration preview
  - **Payment history section**: Table with Date, Amount, Status, Download link columns; empty state from config
  - **Proration Sheet**: slides up from bottom with proration breakdown before confirming plan change
  - **Cancel Sheet**: confirmation modal with period-end date copy and destructive confirm button
- `apps/web/app/(dashboard)/billing/return/page.tsx`: post-checkout success page that reads `?session_id`, auto-redirects to /billing after 3 seconds

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed billing.config import path**

- **Found during:** Task 1 (TypeScript compilation)
- **Issue:** `@/billing.config` resolved to `src/billing.config` but file lives at web root. Import produced TS2307 module-not-found error.
- **Fix:** Changed import to `billing.config` (baseUrl-relative, no `@/` prefix) which resolves correctly since `tsconfig.json` has `baseUrl: "."` at the web app root.
- **Files modified:** `past-due-banner.tsx`, `billing-client.tsx`
- **Commit:** 0f6df6c (included in task commit)

## Self-Check: PASSED

All 5 files verified present. Both commits (0f6df6c, 5a7bab2) verified in git log.
