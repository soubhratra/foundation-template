---
phase: 21-gdpr-baseline
plan: "04"
subsystem: web-frontend
tags: [gdpr, account-deletion, settings, dialog, server-action]
dependency_graph:
  requires:
    - 21-02 # DELETE /api/v1/account/ endpoint
    - 21-03 # Dialog component dependency noted in plan
  provides:
    - DangerZone UI component in /settings page
    - deleteAccountAction server action
  affects:
    - apps/web/app/(dashboard)/settings/settings-client.tsx
    - apps/web/app/(dashboard)/settings/page.tsx
tech_stack:
  added:
    - shadcn Dialog component (apps/web/src/components/ui/dialog.tsx)
  patterns:
    - Server action with cookie forwarding + X-CSRFToken for authenticated DELETE request
    - React Hook Form + Zod in dialog modal with inline server error display
    - Post-deletion session clear via useAuth().logout.mutate() + router.push("/")
key_files:
  created:
    - apps/web/src/components/ui/dialog.tsx
    - apps/web/src/actions/account-actions.ts
  modified:
    - apps/web/app/(dashboard)/settings/settings-client.tsx
    - apps/web/app/(dashboard)/settings/page.tsx
decisions:
  - deleteAccountAction uses direct fetch (not createApiClient) — DELETE /api/v1/account/ is not in the generated OpenAPI client; raw fetch with cookie forwarding matches the createUpstreamFetcher pattern from lib/api/server.ts
  - Session clear uses logout.mutate() from useAuth() — this calls DELETE /api/v1/auth/browser/v1/auth/session and clears storage tokens; same path as the header dropdown Sign Out button
  - DangerZone is a sub-component inside settings-client.tsx (not a separate file) — keeps the settings module self-contained; can be extracted later if it grows
metrics:
  duration_minutes: 4
  completed_date: "2026-03-12"
  tasks_completed: 2
  files_changed: 4
---

# Phase 21 Plan 04: Danger Zone — Account Deletion UI Summary

**One-liner:** Delete Account button in /settings opens a Dialog modal with password confirm, calls DELETE /api/v1/account/, and terminates the session on 202.

## What Was Built

The final frontend touchpoint for GDPR Article 17 (right to erasure). Users visiting `/settings` now see a **Danger Zone** section at the bottom of the page with a red "Delete Account" button.

Clicking the button opens a shadcn Dialog modal containing:

- A password confirmation field (React Hook Form + Zod)
- A destructive "Delete my account" submit button with loading state
- An outline Cancel button that resets the form and closes the modal

On submission:

- Calls `deleteAccountAction(password)` server action
- If 202: invokes `logout.mutate()` (which terminates the Django session and clears client tokens), then `router.push("/")`
- If 400: displays "Incorrect password." inline below the password field; modal stays open
- On any other error: displays "Something went wrong. Please try again."

## Commits

| Task | Description                                                           | Commit  |
| ---- | --------------------------------------------------------------------- | ------- |
| 1    | Install Dialog component and create deleteAccountAction server action | 502ef93 |
| 2    | Add DangerZone section and DeleteAccountModal to /settings            | 0f54dd5 |

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED

- `apps/web/src/components/ui/dialog.tsx` — EXISTS
- `apps/web/src/actions/account-actions.ts` — EXISTS
- `apps/web/app/(dashboard)/settings/settings-client.tsx` — MODIFIED (DangerZone added)
- `apps/web/app/(dashboard)/settings/page.tsx` — MODIFIED (deleteAccountAction prop passed)
- Commit 502ef93 — EXISTS
- Commit 0f54dd5 — EXISTS
- `pnpm build` — PASSES (no TypeScript errors)
