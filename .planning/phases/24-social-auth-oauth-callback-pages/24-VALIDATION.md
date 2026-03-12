---
phase: 24
slug: social-auth-oauth-callback-pages
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-12
---

# Phase 24 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property               | Value                                   |
| ---------------------- | --------------------------------------- |
| **Framework**          | Vitest 4.x + React Testing Library 16.x |
| **Config file**        | `apps/web/vitest.config.ts`             |
| **Quick run command**  | `pnpm --filter @repo/web test`          |
| **Full suite command** | `pnpm --filter @repo/web test`          |
| **Estimated runtime**  | ~15 seconds                             |

---

## Sampling Rate

- **After every task commit:** Run `pnpm --filter @repo/web test`
- **After every plan wave:** Run `pnpm --filter @repo/web test`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID  | Plan | Wave | Requirement | Test Type | Automated Command                          | File Exists | Status     |
| -------- | ---- | ---- | ----------- | --------- | ------------------------------------------ | ----------- | ---------- |
| 24-01-01 | 01   | 0    | SOCIAL-01   | unit      | `pnpm --filter @repo/web test -- callback` | ❌ W0       | ⬜ pending |
| 24-01-02 | 01   | 1    | SOCIAL-01   | unit      | `pnpm --filter @repo/web test -- callback` | ❌ W0       | ⬜ pending |
| 24-02-01 | 02   | 0    | SOCIAL-02   | unit      | `pnpm --filter @repo/web test -- error`    | ❌ W0       | ⬜ pending |
| 24-02-02 | 02   | 2    | SOCIAL-02   | unit      | `pnpm --filter @repo/web test -- error`    | ❌ W0       | ⬜ pending |

_Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky_

---

## Wave 0 Requirements

- [ ] `apps/web/src/__tests__/app/(auth)/callback.test.tsx` — stubs for SOCIAL-01 (callback page behavior: loading state, refetch call, redirect to dashboard, redirect to error)
- [ ] `apps/web/src/__tests__/app/(auth)/error.test.tsx` — stubs for SOCIAL-02 (error page: human-readable messages for all error codes, back-to-sign-in link)

_Existing Vitest + RTL + setup.ts infrastructure is sufficient — only test files are missing._

---

## Manual-Only Verifications

| Behavior                                                              | Requirement | Why Manual                                                   | Test Instructions                                                                                                                                             |
| --------------------------------------------------------------------- | ----------- | ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Google OAuth end-to-end: user signs in via Google, lands on dashboard | SOCIAL-01   | Requires live OAuth provider credentials and browser session | 1. Start dev server. 2. Click "Continue with Google". 3. Complete Google sign-in. 4. Verify redirect to `/dashboard` with no 404.                             |
| GitHub OAuth end-to-end: user signs in via GitHub, lands on dashboard | SOCIAL-02   | Requires live OAuth provider credentials and browser session | 1. Start dev server. 2. Click "Continue with GitHub". 3. Complete GitHub sign-in. 4. Verify redirect to `/dashboard` with no 404.                             |
| OAuth cancel recovery: user cancels OAuth, sees error page            | SOCIAL-02   | Requires browser interaction with OAuth consent screen       | 1. Start OAuth flow. 2. Cancel on provider consent screen. 3. Verify redirect to `/auth/error` with human-readable message and back-to-sign-in link — no 404. |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
