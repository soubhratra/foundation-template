---
phase: 20-social-auth
verified: 2026-03-12T08:35:00Z
status: passed
score: 5/5 must-haves verified
re_verification: false
---

# Phase 20: Social Auth Verification Report

**Phase Goal:** Users can sign up and log in via Google, GitHub, or Apple without creating a password, and existing password-account users are auto-merged on email match
**Verified:** 2026-03-12T08:35:00Z
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| #   | Truth                                                                                            | Status   | Evidence                                                                                                                                                                                                                                                                                        |
| --- | ------------------------------------------------------------------------------------------------ | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Django conditionally registers Google/GitHub/Apple providers when credentials are present in env | VERIFIED | `_configure_social_providers()` pure function in `base.py` SOCIAL AUTH MODULE block; `if google_id and google_secret:` guards; 10 tests GREEN in `test_social_settings.py`                                                                                                                      |
| 2   | Apple relay emails cannot trigger auto-connect to existing password accounts                     | VERIFIED | `FoundationSocialAccountAdapter.can_authenticate_by_email()` returns `False` for `@privaterelay.appleid.com`; 4 tests GREEN in `test_social_adapter.py`                                                                                                                                         |
| 3   | iOS users can sign in with Apple via the mobile app                                              | VERIFIED | `verify_apple_identity_token()` + `handle_apple_login()` in `apple_auth.py`; `POST /api/v1/auth/apple/` via `AppleSignInController` in `controllers.py` (auto-discovered); `Platform.OS === "ios"` guard + `AppleAuthentication` button in `sign-in.tsx`; 5 tests GREEN in `test_apple_auth.py` |
| 4   | Web users see conditional Google + GitHub sign-in buttons on login and signup pages              | VERIFIED | `SocialButtons` component renders based on `NEXT_PUBLIC_GOOGLE_ENABLED` / `NEXT_PUBLIC_GITHUB_ENABLED`; imported and rendered in both `(auth)/page.tsx` and `(auth)/signup/page.tsx`; calls `POST /api/v1/auth/browser/v1/auth/provider/redirect` with CSRF token                               |
| 5   | `create-foundation-app --without social-auth` cleanly removes all social auth infrastructure     | VERIFIED | `removeSocialAuthModule()` exported from `remove.ts`; `--without social-auth` flag wired in `index.ts`; `social-auth` in `SelectedFeatures` type and `promptFeatures()` with default-on; 11 TypeScript unit tests GREEN + Python integration test GREEN                                         |

**Score:** 5/5 truths verified

---

## Required Artifacts

### Plan 01 — Test Stubs

| Artifact                                                          | Expected                            | Status   | Details                              |
| ----------------------------------------------------------------- | ----------------------------------- | -------- | ------------------------------------ |
| `apps/api/tests/test_social_settings.py`                          | RED tests for SOCIAL-01 + SOCIAL-02 | VERIFIED | 10 tests; GREEN after implementation |
| `apps/api/tests/test_apple_auth.py`                               | RED tests for SOCIAL-03             | VERIFIED | 5 tests; GREEN after implementation  |
| `apps/api/tests/test_social_adapter.py`                           | RED tests for SOCIAL-04             | VERIFIED | 4 tests; GREEN after implementation  |
| `apps/api/tests/test_scaffolder_social_removal.py`                | Integration test for SOCIAL-05      | VERIFIED | GREEN                                |
| `packages/create-foundation-app/tests/remove-social-auth.test.ts` | Unit tests for SOCIAL-05            | VERIFIED | 11 tests; all GREEN                  |

### Plan 02 — Settings + Adapter

| Artifact                                   | Expected                                                                | Status   | Details                                                                                                                                                                                                |
| ------------------------------------------ | ----------------------------------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `apps/api/config/settings/base.py`         | SOCIAL AUTH MODULE sentinel block with `_configure_social_providers()`  | VERIFIED | Block present at line ~380; `_configure_social_providers` function substantive (40+ lines); `SOCIALACCOUNT_ADAPTER` points to custom adapter; `SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True` |
| `apps/api/apps/accounts/social_adapter.py` | `FoundationSocialAccountAdapter` overriding `can_authenticate_by_email` | VERIFIED | Class present; blocks `@privaterelay.appleid.com`; delegates others via `bool(super()...)`                                                                                                             |

### Plan 03 — Apple JWT Endpoint

| Artifact                                | Expected                                                              | Status   | Details                                                                                                                        |
| --------------------------------------- | --------------------------------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `apps/api/apps/accounts/apple_auth.py`  | `verify_apple_identity_token()` + JWKS cache + `handle_apple_login()` | VERIFIED | All three functions present; JWKS cache with 1-hour TTL; key-rotation retry on `InvalidSignatureError`; name persistence logic |
| `apps/api/apps/accounts/controllers.py` | `AppleSignInController` with `POST /auth/apple/`                      | VERIFIED | Controller present; wired through `api.auto_discover_controllers()` in `urls.py`; `apps.accounts` in `INSTALLED_APPS`          |

### Plan 04 — Web UI

| Artifact                                          | Expected                            | Status   | Details                                                                                                                   |
| ------------------------------------------------- | ----------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------- |
| `apps/web/src/components/auth/social-buttons.tsx` | Conditional Google + GitHub buttons | VERIFIED | `handleProviderRedirect()` calls `POST /api/v1/auth/browser/v1/auth/provider/redirect`; CSRF cookie read; no Apple button |
| `apps/web/app/(auth)/page.tsx`                    | Contains `SocialButtons`            | VERIFIED | Import at line 11; render at line 145                                                                                     |
| `apps/web/app/(auth)/signup/page.tsx`             | Contains `SocialButtons`            | VERIFIED | Import at line 10; render at line 179                                                                                     |
| `apps/api/.env.example`                           | Social auth credential env vars     | VERIFIED | `GOOGLE_CLIENT_ID`, `GITHUB_CLIENT_ID`, `APPLE_CLIENT_ID` all present with setup comments                                 |

### Plan 05 — Mobile Apple Sign In

| Artifact                             | Expected                      | Status   | Details                                                                                                                                                                                                           |
| ------------------------------------ | ----------------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `apps/mobile/app/(auth)/sign-in.tsx` | iOS-only Apple Sign In button | VERIFIED | `Platform.OS === "ios"` guard at line 117; `AppleAuthentication.AppleAuthenticationButton` present; `SOCIAL AUTH MODULE` sentinel comment present; POSTs to `/api/v1/auth/apple/`; silent `ERR_CANCELED` handling |

### Plan 06 — CLI Scaffolder

| Artifact                                        | Expected                                                       | Status   | Details                                                                                                                                                                                                  |
| ----------------------------------------------- | -------------------------------------------------------------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `packages/create-foundation-app/src/remove.ts`  | `removeSocialAuthModule()`                                     | VERIFIED | Exported at line 656; 145 lines; covers base.py fenced block + sentinel lines + unconditional `allauth.socialaccount` removal + `.env.example` + `social-buttons.tsx` delete + web pages + mobile screen |
| `packages/create-foundation-app/src/prompts.ts` | `"social-auth"` in `SelectedFeatures` + `promptFeatures()`     | VERIFIED | Union type at line 8; multiselect option at line 85; in `initialValues` at line 98 (default-on)                                                                                                          |
| `packages/create-foundation-app/src/index.ts`   | `--without social-auth` flag + `removeSocialAuthModule()` call | VERIFIED | Flag parsed at lines 56–58; filter at line 78; removal call at lines 139–141                                                                                                                             |

---

## Key Link Verification

| From                 | To                                               | Via                                                                                     | Status   | Details                                                                    |
| -------------------- | ------------------------------------------------ | --------------------------------------------------------------------------------------- | -------- | -------------------------------------------------------------------------- |
| `base.py`            | `social_adapter.py`                              | `SOCIALACCOUNT_ADAPTER = "apps.accounts.social_adapter.FoundationSocialAccountAdapter"` | VERIFIED | Setting present at line 467                                                |
| `social_adapter.py`  | `DefaultSocialAccountAdapter`                    | `class FoundationSocialAccountAdapter(DefaultSocialAccountAdapter)`                     | VERIFIED | Inherits and overrides `can_authenticate_by_email`                         |
| `controllers.py`     | `apple_auth.py`                                  | `from .apple_auth import handle_apple_login, verify_apple_identity_token`               | VERIFIED | Import inside endpoint handler at line 73                                  |
| `urls.py`            | `controllers.py`                                 | `api.auto_discover_controllers()`                                                       | VERIFIED | Auto-discover at line 165; `apps.accounts` in `INSTALLED_APPS` at line 113 |
| `(auth)/page.tsx`    | `social-buttons.tsx`                             | `import { SocialButtons } from "@/components/auth/social-buttons"`                      | VERIFIED | Import at line 11; render at line 145                                      |
| `social-buttons.tsx` | `/api/v1/auth/browser/v1/auth/provider/redirect` | `fetch POST with X-CSRFToken`                                                           | VERIFIED | `handleProviderRedirect()` at line 10; fetch call at line 17               |
| `sign-in.tsx`        | `POST /api/v1/auth/apple/`                       | `fetch()` in `handleAppleSignIn`                                                        | VERIFIED | Fetch at line 70 with `EXPO_PUBLIC_API_URL`                                |
| `index.ts`           | `remove.ts`                                      | `import { removeSocialAuthModule } from './remove.js'`                                  | VERIFIED | Import at line 21; call at lines 139–141                                   |
| `remove.ts`          | `base.py` (allauth.socialaccount)                | unconditional regex + sentinel block regex                                              | VERIFIED | Two-pass removal; 11 unit tests GREEN                                      |

---

## Requirements Coverage

| Requirement | Source Plans        | Description                                                                             | Status    | Evidence                                                                                                                                                                         |
| ----------- | ------------------- | --------------------------------------------------------------------------------------- | --------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| SOCIAL-01   | 20-01, 20-02, 20-04 | User can sign up/log in via Google OAuth on the web app                                 | SATISFIED | `_configure_social_providers` registers Google when `GOOGLE_CLIENT_ID` + `GOOGLE_CLIENT_SECRET` set; `SocialButtons` renders Google button; allauth headless redirect flow wired |
| SOCIAL-02   | 20-01, 20-02, 20-04 | User can sign up/log in via GitHub OAuth on the web app                                 | SATISFIED | Same pattern as SOCIAL-01 but for GitHub; both covered by same `SocialButtons` component                                                                                         |
| SOCIAL-03   | 20-01, 20-03, 20-05 | User can sign up/log in via Apple Sign In on iOS mobile app                             | SATISFIED | `verify_apple_identity_token()` + `handle_apple_login()` in `apple_auth.py`; `POST /api/v1/auth/apple/` endpoint live; iOS-only button in `sign-in.tsx`                          |
| SOCIAL-04   | 20-01, 20-02        | Social login auto-connects to existing password account; Apple relay addresses excluded | SATISFIED | `SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True` globally; `FoundationSocialAccountAdapter` blocks `@privaterelay.appleid.com` specifically                              |
| SOCIAL-05   | 20-01, 20-06        | `create-foundation-app --without social-auth` removes all social auth cleanly           | SATISFIED | `removeSocialAuthModule()` exported; `--without social-auth` flag wired; 11 + 1 tests GREEN                                                                                      |

No orphaned requirements — all 5 IDs appeared in plan frontmatter and were accounted for.

---

## Anti-Patterns Found

| File                                              | Line | Pattern       | Severity | Impact                                                                           |
| ------------------------------------------------- | ---- | ------------- | -------- | -------------------------------------------------------------------------------- |
| `apps/web/src/components/auth/social-buttons.tsx` | 94   | `return null` | Info     | Intentional conditional: renders null when no providers are enabled. Not a stub. |

No blocker or warning anti-patterns found.

---

## Human Verification Required

### 1. Google OAuth End-to-End Flow

**Test:** With a real Google OAuth app configured, click "Continue with Google" on the web login page.
**Expected:** Browser redirects to Google consent screen, user grants access, returns to app and is logged in.
**Why human:** Requires live Google OAuth credentials and a running backend. Cannot simulate allauth's server-side token exchange in static analysis.

### 2. GitHub OAuth End-to-End Flow

**Test:** With a real GitHub OAuth app configured, click "Continue with GitHub" on the web login page.
**Expected:** Redirects to GitHub, grants access, returns logged in.
**Why human:** Same reason as Google — live OAuth exchange required.

### 3. Apple Sign In on Physical iOS Device

**Test:** On a real iOS device (or simulator with Apple ID signed in), tap "Sign in with Apple" on the mobile sign-in screen.
**Expected:** Apple authentication sheet appears requesting FULL_NAME + EMAIL permissions; granting returns an identityToken that is sent to the backend; user is logged in and navigated to the dashboard.
**Why human:** `expo-apple-authentication` requires a real Expo build with valid iOS provisioning profile and App Store capabilities. Cannot run in TypeScript type-check only.

### 4. Email Auto-Merge (Existing Password Account + Google/GitHub Login)

**Test:** Create a user account with email/password for `test@example.com`. Then log in via Google OAuth with the same email `test@example.com`.
**Expected:** Allauth auto-connects the social account to the existing user. The user is logged in without creating a duplicate account.
**Why human:** Requires live OAuth credentials + a running database to verify `SocialAccount` is linked to the pre-existing `User` row.

### 5. Apple Relay Email Non-Merge

**Test:** Create a user with email/password. Attempt Apple Sign In using `@privaterelay.appleid.com` relay email on same app account.
**Expected:** A new user is created (relay email is not auto-connected to existing account).
**Why human:** Requires Apple Sign In on a real device with an Apple ID that issues a relay address.

---

## Test Results Summary

| Test Suite                                                        | Count  | Result                 |
| ----------------------------------------------------------------- | ------ | ---------------------- |
| `apps/api/tests/test_social_settings.py`                          | 10     | 10 passed              |
| `apps/api/tests/test_apple_auth.py`                               | 5      | 5 passed               |
| `apps/api/tests/test_social_adapter.py`                           | 4      | 4 passed               |
| `apps/api/tests/test_scaffolder_social_removal.py`                | 1      | 1 passed (integration) |
| `packages/create-foundation-app/tests/remove-social-auth.test.ts` | 11     | 11 passed              |
| **Total**                                                         | **31** | **31 passed**          |

Django `manage.py check` — 3 warnings (pre-existing allauth deprecation warnings for `ACCOUNT_EMAIL_REQUIRED` / `ACCOUNT_USERNAME_REQUIRED`). Zero errors. Not introduced by Phase 20.

---

## Gaps Summary

No gaps. All 5 requirements satisfied. All 31 automated tests pass GREEN. All key links verified in the actual codebase (not just claimed in SUMMARY.md). The only items requiring human verification are those that inherently need live OAuth credentials and a real iOS device — these cannot be resolved by code changes.

---

_Verified: 2026-03-12T08:35:00Z_
_Verifier: Claude (gsd-verifier)_
