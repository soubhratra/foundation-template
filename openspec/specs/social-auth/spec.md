# Social Authentication

> Provider-specific OAuth flows: Google and GitHub OAuth for web via Django Allauth, Apple Sign In for iOS via Expo, email-collision auto-merge, and the unified `/auth/callback` page. Base infrastructure (allauth.socialaccount, FoundationSocialAccountAdapter) is in `openspec/specs/auth/spec.md`.

## Overview

Social auth in the template uses Django Allauth's social account system with three providers: Google and GitHub for web (standard OAuth redirect flow) and Apple for iOS (identity token verification via Apple's JWKS endpoint).

Key design decisions:

- **Single `/auth/callback` route** for all web OAuth providers — both redirect to the same page, which calls `useAuth().refetch()` and redirects to the dashboard. `router.replace` prevents back-navigation into the loading state.
- **Apple needs a dedicated endpoint** (`POST /api/v1/auth/apple/`) because `expo-apple-authentication` returns a token where `aud` is the iOS Bundle ID, which differs from the web OAuth client ID that allauth's standard headless endpoint expects.
- **Auto-merge is provider-selective**: Google and GitHub auto-connect on email match (both providers verify email ownership). Apple relay addresses (`privaterelay.appleid.com`) are excluded from auto-connect to prevent impersonation across Apple IDs.
- **`_configure_social_providers()` is a pure function** to make it unit-testable without Django settings side effects.

For scaffolder opt-out, see `--without social-auth` in `openspec/specs/cli-scaffolder/spec.md`.

## Requirements

### Requirement: Google and GitHub OAuth for Web via Django Allauth

The system SHALL support Google OAuth and GitHub OAuth login for the web application using `django-allauth` social account providers.

#### Scenario: Google OAuth login succeeds

- **WHEN** a user completes the Google OAuth flow
- **THEN** a `SocialAccount` record SHALL be created or updated for the user
- **AND** an existing account with the same email SHALL be merged (see auto-merge requirement)
- **AND** the user SHALL be signed in with a valid session cookie

#### Scenario: GitHub OAuth login succeeds

- **WHEN** a user completes the GitHub OAuth flow
- **THEN** a `SocialAccount` record SHALL be created or updated for the user
- **AND** the same auto-merge and session behavior applies as Google

#### Scenario: Provider registration requires both client_id and secret

- **WHEN** `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are both set
- **THEN** Google SHALL be registered as an active provider
- **WHEN** either value is absent or empty
- **THEN** Google SHALL NOT be registered (no partial registration)
- **AND** the same rule applies to GitHub (`GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET`)

### Requirement: Apple Sign In for iOS via Expo

The iOS mobile app SHALL support Apple Sign In using `expo-apple-authentication` and verify the Apple identity token server-side.

#### Scenario: Apple Sign In completes on iOS

- **WHEN** a user authenticates with Apple on an iOS device
- **THEN** the app SHALL receive an `identityToken` (RS256 JWT signed by Apple)
- **AND** the token SHALL be verified against Apple's public JWKS endpoint
- **AND** on success, a session SHALL be created via the same allauth social account flow

#### Scenario: Apple private key is accepted in both base64 and PEM format

- **WHEN** `APPLE_PRIVATE_KEY` contains a base64-encoded value
- **THEN** it SHALL be decoded before use
- **WHEN** `APPLE_PRIVATE_KEY` is a raw PEM string (e.g., in tests)
- **THEN** it SHALL be used as-is with graceful fallback

### Requirement: Email-Collision Account Auto-Merge

The system SHALL automatically merge a new social login with an existing account that has the same verified email address.

#### Scenario: Existing account found by email during social login

- **WHEN** a user attempts social login with an email that matches an existing verified account
- **THEN** the social account SHALL be connected to the existing user record
- **AND** no duplicate user SHALL be created
- **AND** the setting `SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True` SHALL be enabled

#### Scenario: Email verification required for auto-merge

- **WHEN** the existing account's email is NOT verified
- **THEN** the auto-merge SHALL NOT occur
- **AND** a new account SHALL be created instead

### Requirement: OAuth Callback Page in Next.js

The web application SHALL provide a single unified OAuth callback page at `/auth/callback` that handles the allauth session handoff after any OAuth provider redirects back.

#### Scenario: Callback page completes OAuth flow on redirect

- **WHEN** Google or GitHub redirects the user to `/auth/callback`
- **THEN** the page SHALL call `useAuth().refetch()` on mount to verify the session allauth created server-side
- **AND** on success (session present) SHALL redirect the user to `/dashboard` using `router.replace`
- **AND** on failure SHALL redirect to `/auth/error?error=unknown`

#### Scenario: router.replace prevents back-navigation into loading state

- **WHEN** the callback redirect completes
- **THEN** `router.replace` SHALL be used (not `router.push`) so the user cannot navigate back to the loading page

#### Scenario: SocialButtons passes the unified callback URL

- **WHEN** `SocialButtons` initiates an OAuth flow
- **THEN** it SHALL pass `callback_url='/auth/callback'` for all providers (Google and GitHub share the same callback route)

### Requirement: Social Auth Settings via \_configure_social_providers()

Social provider registration SHALL be handled by a pure function `_configure_social_providers(env_dict)` that accepts an environment dictionary and returns a settings dict with `extra_installed_apps`, `providers`, and `auto_connect`.

#### Scenario: Pure function is importable and testable

- **WHEN** `_configure_social_providers` is imported from `config.settings.base`
- **THEN** it SHALL be callable with a plain dict without triggering Django settings reload
- **AND** its output SHALL be deterministic given the same input

### Requirement: CLI Scaffolder Opt-Out via --without social-auth

The `create-foundation-app` CLI SHALL support removing the social auth module.

#### Scenario: removeSocialAuthModule() strips all social auth artifacts

- **WHEN** `--without social-auth` is selected during scaffolding
- **THEN** `removeSocialAuthModule(outputDir)` SHALL:
  - Remove the `# SOCIAL AUTH MODULE` / `# END SOCIAL AUTH MODULE` fenced block from settings
  - Delete `apps/api/apps/accounts/social_adapter.py`
  - Remove `SocialButtons` component from login/signup pages
  - Remove `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, `APPLE_*` vars from `.env.example`

#### Scenario: Social auth is selected by default in interactive prompt

- **WHEN** the user runs the CLI without flags
- **THEN** "Social Auth" SHALL appear as a pre-selected option in the features multi-select prompt

## Implementation Decisions

### Why a dedicated Apple JWT verification endpoint (not allauth's standard headless endpoint)

Expo's `expo-apple-authentication` returns an identity token where `aud` (audience) is the iOS Bundle ID (e.g., `com.example.app`). Allauth's standard headless social login endpoint expects `aud` to match the web OAuth client ID. These are different values, so a dedicated server-side endpoint `POST /api/v1/auth/apple/` is required to verify the token independently.

**What the endpoint does:** Fetches Apple's public JWKS, verifies the RS256 JWT signature and `aud`/`iss` claims, then creates or retrieves the allauth `SocialAccount` and issues a session.

**Alternative rejected:** Using `ExpoGoAdapter` or a custom allauth social provider — this pushes JWKS logic into the allauth provider lifecycle which is harder to test and would require forking allauth internals.

### Why per-provider auto-merge settings (Google/GitHub enabled, Apple disabled)

`SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True` for Google and GitHub: both providers verify email ownership before releasing it in the token, so merging on email match is safe.

Apple is excluded from auto-connect for relay addresses. When a user hides their email via "Sign in with Apple", Apple issues an ephemeral relay address (e.g., `abc123@privaterelay.appleid.com`). Auto-connecting a relay address to an existing real-email account would allow impersonation if two people happen to share the same underlying Apple ID relay.

**Implementation:** `SocialAccountAdapter.pre_social_login()` inspects the provider and email domain. Real Apple emails auto-connect; relay addresses do not.

### Why `APPLE_PRIVATE_KEY` accepts both base64 and raw PEM

Environment variables in Docker/Railway/Heroku deployments frequently have issues with literal newlines in multi-line PEM keys. Base64 encoding sidesteps this. The code checks for base64 encoding at runtime (tries `base64.b64decode`, falls back to raw PEM) so developers can use either format without configuration changes.

### Why a single `/auth/callback` route for both Google and GitHub

Maintaining separate `/auth/callback/google` and `/auth/callback/github` pages adds no value — both do the same thing (call `useAuth().refetch()`, then redirect). A single route reduces the surface area and means `SocialButtons` passes the same `callback_url` for all providers. `router.replace` (not `router.push`) is used so the callback page is not reachable via browser back-navigation.

### Why `_configure_social_providers()` is a pure function

Pure function (accepts an env dict, returns settings) makes the social provider registration logic unit-testable without triggering Django settings imports. Tests can call it with arbitrary dicts without mocking `os.environ` or touching `settings`.
