# Phase 20: Social Auth - Context

**Gathered:** 2026-03-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Add social login to the template: Google + GitHub OAuth on the web app, Apple Sign In on iOS mobile only. Includes email-collision account auto-merge (Google/GitHub only), and a `--without social-auth` scaffolder flag that removes all social auth infrastructure cleanly.

Creating new auth providers beyond these three, adding social auth to web for Apple, or adding Google/GitHub to mobile are out of scope for this phase.

</domain>

<decisions>
## Implementation Decisions

### Credential management

- Credentials stored in environment variables, not the Django admin SocialApp model
- Pattern consistent with RESEND_API_KEY and STRIPE_SECRET_KEY: fill `.env.example`, nothing else required
- Providers are conditionally registered: a provider only activates when its credentials are present in the environment. If credentials are absent, its button does not appear on the frontend. Zero-config default — social login simply isn't available until credentials are added.
- Env var names (matches provider console terminology):
  - Google: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
  - GitHub: `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`
  - Apple: `APPLE_CLIENT_ID`, `APPLE_TEAM_ID`, `APPLE_KEY_ID`, `APPLE_PRIVATE_KEY`
- Apple private key (`.p8` file) stored inline as env var content (base64 or escaped newlines) — no file-on-disk required; works in Docker containers, CI, and cloud deploys

### Email auto-merge

- `SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT=True` for Google and GitHub — signing in with a social provider whose email matches an existing password account silently connects them (already decided)
- Apple relay addresses (`@privaterelay.appleid.com`) are explicitly excluded from auto-merge — they don't reliably map to a real email address (already decided)

### Apple Sign In — platform and flow

- iOS mobile only. Apple Sign In button does NOT appear on the web login page (no Apple Services ID + domain verification required; avoids separate web Apple app config)
- Requires a custom server-side token verification endpoint — Expo's `expo-apple-authentication` issues JWTs with `aud` = Bundle ID (not Services ID), which differs from allauth's standard social token flow expectation; a dedicated endpoint performs native JWT verification
- Apple only returns the user's name on the first sign-in; subsequent logins carry no name. Behavior: persist the name from the first login to the user profile; on return logins do not overwrite; if name is blank (relay user or returning user), profile name stays empty until user fills it in — no forced "complete profile" step
- Relay email UX: accept `@privaterelay.appleid.com` silently — no banner, no nudge to add a real email. It's a valid Apple-forwarded address. User can update their profile email later.

### Web UI

- Web login and signup pages: Google + GitHub buttons below the email/password form, separated by an "or" divider
- Buttons appear only when the respective provider's credentials are set in the environment (conditional rendering mirrors backend conditional registration)
- Apple Sign In not shown on web

### Scaffolder removal (`--without social-auth`)

- Removes `allauth.socialaccount` and all provider apps (`allauth.socialaccount.providers.google` etc.) from `INSTALLED_APPS` entirely — no residual DB tables or migrations
- Removes `SOCIALACCOUNT_PROVIDERS` settings block from `base.py` (using sentinel comment pattern: `# SOCIAL AUTH MODULE`)
- Removes all six social credential env vars from `.env.example`
- Removes Google/GitHub social buttons from web login/signup pages
- Removes Apple Sign In button from the mobile auth screen
- Assumes generation-time only (fresh project, no existing DB rows) — no squash migration needed, consistent with `--without billing` behavior

### Claude's Discretion

- Exact SOCIALACCOUNT_PROVIDERS settings structure (allauth 65.x format)
- How conditional provider registration is wired in settings (e.g., list comprehension vs explicit if-blocks)
- Whether the custom Apple endpoint lives in `apps/accounts/` or a new `apps/social/` app
- Exact `expo-apple-authentication` integration in React Native (credential request flow)
- Callback URL handling and Django URL routing for OAuth redirects

</decisions>

<code_context>

## Existing Code Insights

### Reusable Assets

- `allauth.socialaccount` already in `INSTALLED_APPS` — no install step needed
- `apps/web/app/(auth)/page.tsx`: existing login page using `AuthCard` + `AuthForm` + `AuthLinks` components — social buttons slot below the existing form
- `apps/mobile/app/(auth)/`: existing auth route group in Expo Router — Apple Sign In button added here
- `packages/create-foundation-app/src/remove.ts`: established sentinel-comment removal pattern (`# BILLING MODULE`, `# EMAIL MODULE`) — `# SOCIAL AUTH MODULE` follows same convention
- `packages/create-foundation-app/src/prompts.ts`: feature list with `initialValues` array — add `"social-auth"` entry following `"email"` entry pattern

### Established Patterns

- Env-var-conditional activation: `EMAIL_BACKEND` auto-switches on `RESEND_API_KEY`; same pattern for `GOOGLE_CLIENT_ID` / `GITHUB_CLIENT_ID` / `APPLE_CLIENT_ID` gating provider registration
- Sentinel comment removal: `# BILLING MODULE — remove this line to exclude billing`, `# EMAIL MODULE — remove this line to exclude email` — social auth uses same pattern
- Scaffolder `--without` flag: billing and email both use `withoutBillingFlag` / `withoutEmailFlag` variable in `index.ts` parsed from argv — add `withoutSocialAuthFlag`

### Integration Points

- `INSTALLED_APPS` in `config/settings/base.py`: add social providers conditionally
- `SOCIALACCOUNT_PROVIDERS` settings block in `base.py`: new block (with sentinel comments for removal)
- `apps/api/config/urls.py`: allauth headless URLs already registered; social provider URLs added via allauth's autodiscovery — no manual URL addition required
- `packages/create-foundation-app/src/prompts.ts`: add `social-auth` to feature list
- `packages/create-foundation-app/src/remove.ts`: add `removeSocialAuthModule()` function

</code_context>

<specifics>
## Specific Ideas

- Apple private key pattern: `APPLE_PRIVATE_KEY=$(cat AuthKey_XXX.p8 | base64)` — document this in `.env.example` comment so developers know the format
- The "conditional provider" pattern means a developer can add social login to their project simply by adding the relevant env vars — no code changes required after scaffolding

</specifics>

<deferred>
## Deferred Ideas

- Apple Sign In on web (requires separate Services ID + domain verification in Apple Developer Console) — SOCIAL-F01 territory
- Google Sign In on mobile — SOCIAL-F01, requires dev build + separate Android/iOS credential setup; explicitly deferred per requirements
- GitHub on mobile — not in scope for this template phase
- SSO/SAML for enterprise B2B — SOCIAL-F02, OpenSpec guide only

</deferred>

---

_Phase: 20-social-auth_
_Context gathered: 2026-03-12_
