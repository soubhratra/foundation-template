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
