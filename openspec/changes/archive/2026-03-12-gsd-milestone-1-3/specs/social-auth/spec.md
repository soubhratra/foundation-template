## ADDED Requirements

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
