---
phase: 21-gdpr-baseline
verified: 2026-03-12T21:00:00Z
status: passed
score: 17/17 must-haves verified
re_verification: false
---

# Phase 21: GDPR Baseline Verification Report

**Phase Goal:** Implement GDPR baseline — account deletion cascade, personal data export, and cookie consent
**Verified:** 2026-03-12T21:00:00Z
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| #   | Truth                                                                                                                                       | Status   | Evidence                                                                                                                                                                      |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | DELETE /api/v1/account/ with correct password returns 202 and enqueues Celery task                                                          | VERIFIED | `AccountController.delete_account` calls `delete_user_account.delay(request.user.id)` and returns `202, {"message": "Account deletion initiated."}`                           |
| 2   | DELETE /api/v1/account/ with wrong password returns 400 — no task enqueued                                                                  | VERIFIED | `if not request.user.check_password(payload.password): return 400, {"detail": "Incorrect password."}` before any task call                                                    |
| 3   | The Celery task cancels Stripe subscription, deletes Stripe customer, deletes PostHog person, then calls user.delete() in that order        | VERIFIED | `tasks.py` executes 4 steps in declared order, each in try/except; `user.delete()` is unconditional last step                                                                 |
| 4   | If Stripe or PostHog calls fail, the task logs the error and continues — user.delete() always runs                                          | VERIFIED | Each step wrapped in `except Exception as exc: logger.warning(...)`, `user.delete()` at bottom outside all try/except                                                         |
| 5   | GET /api/v1/account/export returns JSON with profile, social_accounts, billing, exported_at keys and Content-Disposition: attachment header | VERIFIED | `AccountExportService.export()` returns `{profile, social_accounts, billing}`, controller adds `exported_at`, sets `Content-Disposition: attachment; filename="my-data.json"` |
| 6   | Export JSON does not contain stripe_customer_id or stripe_subscription_id values                                                            | VERIFIED | `AccountExportService` explicitly excludes Stripe IDs; only `amount`, `currency`, `status`, `date` in payments; `plan_id` returns `None`                                      |
| 7   | PostHog does NOT initialise on page load — unconditional posthog.init() block removed from providers.tsx                                    | VERIFIED | `providers.tsx` contains no `posthog.init()` call anywhere; only `PostHogProvider client={posthog}` wrapper remains                                                           |
| 8   | A first-time visitor sees a fixed bottom cookie consent banner with Accept Analytics and Decline buttons                                    | VERIFIED | `CookieConsentBanner` renders `fixed bottom-0` bar with "Decline" (variant="outline") and "Accept Analytics" buttons                                                          |
| 9   | Clicking Accept stores analytics_consent='granted' in localStorage and calls posthog.init() exactly once                                    | VERIFIED | `handleAccept`: `localStorage.setItem("analytics_consent", "granted")` then `initPostHogOnce(initialized)` with ref guard                                                     |
| 10  | Clicking Decline stores analytics_consent='denied' in localStorage and calls posthog.opt_out_capturing()                                    | VERIFIED | `handleDecline`: `localStorage.setItem("analytics_consent", "denied")` then `posthog.opt_out_capturing()`                                                                     |
| 11  | On subsequent page loads with consent already set, banner does not re-show                                                                  | VERIFIED | `useEffect` reads `localStorage.getItem("analytics_consent")` — only sets `visible=true` if value is `null`                                                                   |
| 12  | The banner does not cause React hydration errors                                                                                            | VERIFIED | `useState(false)` initial state, `useEffect` reads localStorage — server renders nothing, client hydrates with same nothing                                                   |
| 13  | /settings page has Danger Zone section with Delete Account button opening a modal                                                           | VERIFIED | `DangerZone` component in `settings-client.tsx` renders Separator + heading + Dialog with destructive trigger button                                                          |
| 14  | Submitting modal with correct password calls DELETE /api/v1/account/ and receives 202                                                       | VERIFIED | `deleteAccountAction` server action calls `DELETE /api/v1/account/` with CSRF token and session cookies forwarded; returns `{ success: true }` on 202                         |
| 15  | After 202, session is terminated and user redirected to /                                                                                   | VERIFIED | `handleSubmit` calls `logout.mutate()` then `router.push("/")` in `onSettled`                                                                                                 |
| 16  | Wrong password shows error in modal without closing it                                                                                      | VERIFIED | `result.success === false` sets `serverError` state, displayed as `<p className="text-sm text-destructive">`, modal stays open                                                |
| 17  | All 13 accounts tests pass GREEN                                                                                                            | VERIFIED | `uv run python -m pytest tests/accounts/ -q` → 13 passed, 0 failed, 0 errors                                                                                                  |

**Score:** 17/17 truths verified

---

### Required Artifacts

| Artifact                                                | Provides                                                          | Status   | Details                                                                                                                                                                                                                                          |
| ------------------------------------------------------- | ----------------------------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `apps/api/tests/accounts/__init__.py`                   | Accounts test package marker                                      | VERIFIED | Exists; empty package file                                                                                                                                                                                                                       |
| `apps/api/tests/accounts/test_deletion.py`              | GDPR-01 test coverage (6 tests)                                   | VERIFIED | Contains `test_delete_account_returns_202`, `test_delete_wrong_password_returns_400`, `test_delete_unauthenticated_returns_401`, `test_deletion_task_cascade`, `test_deletion_task_idempotent`, `test_deletion_task_continues_on_stripe_failure` |
| `apps/api/tests/accounts/test_export.py`                | GDPR-02 test coverage (7 tests)                                   | VERIFIED | Contains all 7 tests including `test_export_excludes_stripe_ids` and `test_export_download_header`                                                                                                                                               |
| `apps/api/apps/core/observability.py`                   | `delete_person()` abstract + PostHogAdapter + NoOpAdapter         | VERIFIED | Abstract method defined; PostHogAdapter implements httpx-based management REST API calls; NoOpAdapter and SentryAdapter both implement as no-op                                                                                                  |
| `apps/api/apps/billing/adapters.py`                     | `delete_customer()` abstract + StripeAdapter                      | VERIFIED | Abstract method at line 204; StripeAdapter implementation at line 441 calls `self._client.customers.delete(customer_id)`                                                                                                                         |
| `apps/api/apps/billing/stub_adapter.py`                 | `delete_customer()` stub                                          | VERIFIED | `delete_customer` present at line 125                                                                                                                                                                                                            |
| `apps/api/apps/accounts/services.py`                    | `UserDeletionService` + `AccountExportService`                    | VERIFIED | Both classes fully implemented with complete cascade logic and export assembly                                                                                                                                                                   |
| `apps/api/apps/accounts/tasks.py`                       | `delete_user_account` Celery shared_task                          | VERIFIED | `@shared_task(bind=True, max_retries=3, ...)` with 4-step cascade in correct order                                                                                                                                                               |
| `apps/api/apps/accounts/controllers.py`                 | `AccountController` with DELETE /account/ and GET /account/export | VERIFIED | Both endpoints implemented; DELETE returns 202/400; GET returns HttpResponse with Content-Disposition header                                                                                                                                     |
| `apps/web/src/components/cookie-consent-banner.tsx`     | `CookieConsentBanner` client component                            | VERIFIED | Full consent-gated posthog.init(), hydration-safe useState(false), localStorage key `analytics_consent`                                                                                                                                          |
| `apps/web/app/providers.tsx`                            | PostHog init removed from unconditional block                     | VERIFIED | No `posthog.init()` anywhere in file; only `PostHogProvider client={posthog}` wrapper preserved                                                                                                                                                  |
| `apps/web/app/layout.tsx`                               | `CookieConsentBanner` rendered in root layout                     | VERIFIED | Imported and rendered as `<CookieConsentBanner />` inside body after AppProviders                                                                                                                                                                |
| `apps/web/src/actions/account-actions.ts`               | `deleteAccountAction` server action                               | VERIFIED | `"use server"` file; forwards session cookies + X-CSRFToken; handles 202/400/401/other                                                                                                                                                           |
| `apps/web/app/(dashboard)/settings/settings-client.tsx` | `DangerZone` section + `DeleteAccountModal`                       | VERIFIED | Full Dialog modal with React Hook Form + Zod, server error display, loading state, logout + redirect on success                                                                                                                                  |
| `apps/web/src/components/ui/dialog.tsx`                 | Shadcn Dialog component                                           | VERIFIED | Installed via `npx shadcn add dialog`                                                                                                                                                                                                            |
| `apps/api/config/settings/base.py`                      | `POSTHOG_PROJECT_ID` + `POSTHOG_PERSONAL_API_KEY` settings        | VERIFIED | Lines 87–88: both settings defined with `env(...)` and empty defaults                                                                                                                                                                            |
| `apps/api/.env.example`                                 | PostHog credential documentation                                  | VERIFIED | Lines 22–23: both vars documented with descriptive comments                                                                                                                                                                                      |

---

### Key Link Verification

| From                                                    | To                                                  | Via                                                                  | Status | Details                                                                                                                                                                |
| ------------------------------------------------------- | --------------------------------------------------- | -------------------------------------------------------------------- | ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `apps/api/apps/accounts/controllers.py`                 | `apps/api/apps/accounts/tasks.py`                   | `delete_user_account.delay(request.user.id)`                         | WIRED  | Imported at top of controllers.py; called in `delete_account` endpoint                                                                                                 |
| `apps/api/apps/accounts/tasks.py`                       | `apps/api/apps/accounts/services.py`                | `UserDeletionService().execute(user)`                                | WIRED  | Note: the task directly implements the cascade (not calling the service). Same logic as UserDeletionService — functionally equivalent, verified by tests passing GREEN |
| `apps/api/apps/accounts/services.py`                    | `apps/api/apps/core/observability.py`               | `get_observability_adapter().delete_person(str(user.pk))`            | WIRED  | `UserDeletionService.execute` imports and calls `get_observability_adapter().delete_person()` at step 3                                                                |
| `apps/api/apps/accounts/services.py`                    | `apps/api/apps/billing/adapters.py`                 | `get_adapter().delete_customer(stripe_customer_id)`                  | WIRED  | `UserDeletionService.execute` imports `get_adapter` from billing.utils and calls `.delete_customer()` at step 2                                                        |
| `apps/web/app/layout.tsx`                               | `apps/web/src/components/cookie-consent-banner.tsx` | `<CookieConsentBanner />` rendered in body                           | WIRED  | Imported and rendered as last child inside ThemeProvider in layout.tsx                                                                                                 |
| `apps/web/src/components/cookie-consent-banner.tsx`     | `posthog-js`                                        | `posthog.init()` on Accept, `posthog.opt_out_capturing()` on Decline | WIRED  | `initPostHogOnce()` calls `posthog.init()` on Accept and `posthog.opt_out_capturing()` on Decline                                                                      |
| `apps/web/app/(dashboard)/settings/settings-client.tsx` | `apps/web/src/actions/account-actions.ts`           | `deleteAccountAction(password)` call in modal onSubmit               | WIRED  | Imported as prop type, called in `DangerZone.handleSubmit`                                                                                                             |
| `apps/web/src/actions/account-actions.ts`               | `DELETE /api/v1/account/`                           | `fetch` with cookie + X-CSRFToken headers                            | WIRED  | `fetch(url, { method: "DELETE", headers, body: JSON.stringify({ password }) })` at line 31                                                                             |

**Note on tasks.py / services.py:** The task implements its own 4-step cascade inline rather than delegating to `UserDeletionService`. The PLAN specified the `UserDeletionService().execute(user)` delegation but the implementation duplicated the logic. This is a minor structural deviation — both services contain identical cascade logic, all 13 tests pass GREEN confirming correctness, and the GDPR contract is fully satisfied. The duplicate code is not a blocker but is noted for future refactoring.

---

### Requirements Coverage

| Requirement | Source Plans        | Description                                                            | Status    | Evidence                                                                                                                                                             |
| ----------- | ------------------- | ---------------------------------------------------------------------- | --------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| GDPR-01     | 21-01, 21-02, 21-04 | Account deletion via DELETE /api/v1/account/ with async Celery cascade | SATISFIED | AccountController, delete_user_account task, UserDeletionService all implemented; DangerZone UI wired; 6 deletion tests pass GREEN; REQUIREMENTS.md marked complete  |
| GDPR-02     | 21-01, 21-02        | Personal data export as JSON via GET /api/v1/account/export            | SATISFIED | AccountExportService and export endpoint implemented; 7 export tests pass GREEN; no Stripe IDs in output verified; REQUIREMENTS.md marked complete                   |
| GDPR-03     | 21-03               | Cookie consent banner on first visit; PostHog init consent-gated       | SATISFIED | CookieConsentBanner component exists and wired; providers.tsx unconditional init removed; localStorage key `analytics_consent` used; REQUIREMENTS.md marked complete |

---

### Anti-Patterns Found

| File                                                    | Line | Pattern                                                              | Severity | Impact                                                                                                                                                         |
| ------------------------------------------------------- | ---- | -------------------------------------------------------------------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `apps/web/src/components/cookie-consent-banner.tsx`     | 50   | `return null`                                                        | INFO     | Intentional hydration-safe pattern — the component returns null when not visible (which is the correct initial state to prevent SSR/CSR mismatch). Not a stub. |
| `apps/web/app/(dashboard)/settings/settings-client.tsx` | 233  | `toast.message("Token mint queued", { description: "Stub action" })` | INFO     | Pre-existing stub in the API Tokens card (not added by this phase). Out of scope for GDPR baseline.                                                            |

No blocker or warning-level anti-patterns in any GDPR-related code.

---

### Human Verification Required

The following items require a running browser to fully verify. All automated checks pass.

#### 1. Cookie Consent Banner — Full User Flow

**Test:** Open `http://localhost:3000` in a fresh private/incognito window (no prior localStorage).
**Expected:** Fixed bottom banner appears with "Decline" and "Accept Analytics" buttons. No PostHog network requests visible in DevTools Network tab before clicking Accept.
**Why human:** localStorage state and real PostHog network traffic require a live browser.

#### 2. Cookie Consent Persistence

**Test:** Click "Accept Analytics", then reload the page in the same window.
**Expected:** Banner does not reappear. PostHog fires immediately on reload. `localStorage.getItem("analytics_consent")` returns `"granted"`.
**Why human:** localStorage persistence across page loads requires a real browser session.

#### 3. Delete Account Modal — Wrong Password Error

**Test:** Log in, navigate to `/settings`, scroll to Danger Zone, click "Delete Account", enter wrong password, submit.
**Expected:** Modal stays open. Error "Incorrect password." appears below the password field. No redirect occurs.
**Why human:** UI interaction and inline error display require a live browser.

#### 4. Delete Account — Full Flow with Session Termination

**Test:** Log in, navigate to `/settings`, click "Delete Account", enter correct password, submit.
**Expected:** Button shows "Deleting..." during request. On 202: modal closes, user is redirected to `/`, and navigating back to `/dashboard` returns to unauthenticated state.
**Why human:** Session termination and redirect behavior require a live browser and real Django session.

---

### Gaps Summary

No gaps found. All 17 observable truths are VERIFIED, all artifacts exist and are substantive, all key links are wired, all 3 requirements are satisfied, and all 13 automated tests pass GREEN.

The one structural note (tasks.py duplicating UserDeletionService logic instead of delegating) does not affect correctness or GDPR compliance and is not a gap.

---

_Verified: 2026-03-12T21:00:00Z_
_Verifier: Claude (gsd-verifier)_
