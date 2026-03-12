---
phase: 19-transactional-email
plan: "04"
subsystem: scaffolder-cli
tags: [scaffolder, email, typescript, tdd, remove-module]
dependency_graph:
  requires: [19-02, 19-03]
  provides: [EMAIL-05, removeEmailModule-export, email-feature-in-prompts]
  affects: [packages/create-foundation-app]
tech_stack:
  added: []
  patterns: [tdd-red-green, sentinel-comment-regex-removal, enoent-guard]
key_files:
  created:
    - packages/create-foundation-app/tests/remove-email.test.ts
  modified:
    - packages/create-foundation-app/src/remove.ts
    - packages/create-foundation-app/src/prompts.ts
    - packages/create-foundation-app/src/index.ts
decisions:
  - removeEmailModule() mirrors removeBillingModule() pattern exactly — same ENOENT guard, same dash-fenced block regex, same sentinel comment approach
  - TDD executed strictly: RED commit (35f430b) before GREEN commit (6ae7c46) — 7 unit tests written first
  - EMAIL MODULE block uses same dash-comment fencing as BILLING MODULE — consistent scaffolder removal pattern across all optional modules
metrics:
  duration_seconds: 246
  completed_date: "2026-03-11"
  tasks_completed: 2
  files_changed: 4
---

# Phase 19 Plan 04: Scaffolder Email Removal Summary

**One-liner:** CLI scaffolder support for `--without email` — `removeEmailModule()` strips anymail, notifications app, and EMAIL MODULE settings block using sentinel-comment regex pattern.

## Tasks Completed

| Task      | Name                                       | Commit  | Files                        |
| --------- | ------------------------------------------ | ------- | ---------------------------- |
| 1 (RED)   | Failing test for removeEmailModule()       | 35f430b | tests/remove-email.test.ts   |
| 1 (GREEN) | Implement removeEmailModule() in remove.ts | 6ae7c46 | src/remove.ts                |
| 2         | Wire email into prompts.ts and index.ts    | c049a03 | src/prompts.ts, src/index.ts |

## What Was Built

`removeEmailModule(outputDir)` in `packages/create-foundation-app/src/remove.ts`:

1. Deletes `apps/api/apps/notifications/` directory (ENOENT guard — silent skip if absent)
2. Strips `"anymail"` line from INSTALLED_APPS using `# EMAIL MODULE` sentinel comment regex
3. Strips `"apps.notifications"` line from INSTALLED_APPS using `# EMAIL MODULE` sentinel comment regex
4. Removes the entire `# EMAIL MODULE` / `# END EMAIL MODULE` dash-fenced settings block from `base.py` (removes `RESEND_API_KEY`, `EMAIL_BACKEND`, `ANYMAIL`, `DEFAULT_FROM_EMAIL` settings)
5. Removes `RESEND_API_KEY` and `DEFAULT_FROM_EMAIL` lines from `apps/api/.env.example` (ENOENT guard — silent skip if absent)

`packages/create-foundation-app/src/prompts.ts`:

- `SelectedFeatures` type union extended with `"email"`
- `promptFeatures()` multi-select includes "Transactional Email" option with hint
- `"email"` added to `initialValues` (selected by default)

`packages/create-foundation-app/src/index.ts`:

- `removeEmailModule` imported from `./remove.js`
- `if (!config.features.includes("email")) { await removeEmailModule(config.outputDir); }` added after observability block

## Verification

Full phase test suite: 9 tests GREEN across EMAIL-01 through EMAIL-05

```
tests/notifications/ tests/test_scaffolder_email_removal.py
9 passed, 1 warning in 2.79s
```

Django system check: passes (3 pre-existing allauth deprecation warnings, no errors — out of scope).

## Deviations from Plan

None — plan executed exactly as written. TDD cycle followed strictly (RED → commit → GREEN → commit).

## Self-Check: PASSED

- packages/create-foundation-app/tests/remove-email.test.ts: FOUND
- packages/create-foundation-app/src/remove.ts: FOUND (contains removeEmailModule export)
- packages/create-foundation-app/src/prompts.ts: FOUND (contains "email" in SelectedFeatures)
- packages/create-foundation-app/src/index.ts: FOUND (contains removeEmailModule import and call)
- Commit 35f430b: FOUND (test RED)
- Commit 6ae7c46: FOUND (implementation GREEN)
- Commit c049a03: FOUND (wiring)
