# Phase 20: Social Auth - Research

**Researched:** 2026-03-12
**Domain:** OAuth2 social login — allauth 65.x headless, Google/GitHub web, Apple iOS native
**Confidence:** HIGH (allauth docs verified), MEDIUM (Apple native custom endpoint — non-standard pattern)

---

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions

- Credentials stored in environment variables, not the Django admin SocialApp model
- Providers are conditionally registered: a provider only activates when its credentials are present in the environment; its button does not appear on the frontend when credentials are absent
- Env var names: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, `APPLE_CLIENT_ID`, `APPLE_TEAM_ID`, `APPLE_KEY_ID`, `APPLE_PRIVATE_KEY`
- Apple private key stored inline as env var content (base64 or escaped newlines) — no file-on-disk required
- `SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT=True` for Google and GitHub
- Apple relay addresses (`@privaterelay.appleid.com`) excluded from auto-merge
- Apple Sign In: iOS mobile only — no web login page button, no Services ID required
- Apple requires a custom server-side token verification endpoint — Expo's `expo-apple-authentication` issues JWTs with `aud` = Bundle ID (not Services ID), which differs from allauth's standard social token flow expectation
- Apple: persist name from first login only; do not overwrite on return logins; no "complete profile" forced step
- Apple relay email accepted silently — no banner, no nudge
- Web login and signup pages: Google + GitHub buttons below the email/password form, separated by an "or" divider; buttons appear only when credentials are set
- Apple Sign In not shown on web
- Scaffolder: removes `allauth.socialaccount` and all provider apps from `INSTALLED_APPS` entirely, removes `SOCIALACCOUNT_PROVIDERS` settings block (sentinel: `# SOCIAL AUTH MODULE`), removes all six social credential env vars from `.env.example`, removes social buttons from web login/signup pages and Apple button from mobile auth screen
- Scaffolder removal is generation-time only (fresh project, no existing DB rows)

### Claude's Discretion

- Exact SOCIALACCOUNT_PROVIDERS settings structure (allauth 65.x format)
- How conditional provider registration is wired in settings (e.g., list comprehension vs explicit if-blocks)
- Whether the custom Apple endpoint lives in `apps/accounts/` or a new `apps/social/` app
- Exact `expo-apple-authentication` integration in React Native (credential request flow)
- Callback URL handling and Django URL routing for OAuth redirects

### Deferred Ideas (OUT OF SCOPE)

- Apple Sign In on web (requires separate Services ID + domain verification in Apple Developer Console)
- Google Sign In on mobile
- GitHub on mobile
- SSO/SAML for enterprise B2B
  </user_constraints>

---

<phase_requirements>

## Phase Requirements

| ID        | Description                                                                                   | Research Support                                                                                                                |
| --------- | --------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| SOCIAL-01 | User can sign up and log in via Google OAuth on the web app                                   | allauth Google provider APPS config; headless browser redirect flow; web button conditional on `GOOGLE_CLIENT_ID`               |
| SOCIAL-02 | User can sign up and log in via GitHub OAuth on the web app                                   | allauth GitHub provider APPS config; same redirect flow; web button conditional on `GITHUB_CLIENT_ID`                           |
| SOCIAL-03 | User can sign up and log in via Apple Sign In on the iOS mobile app                           | Custom Django endpoint verifying Expo Apple JWT (aud=bundle_id); `expo-apple-authentication`; mobile button always shown on iOS |
| SOCIAL-04 | Social login with matching email auto-connects accounts (Google/GitHub); Apple relay excluded | `SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT=True`; custom SocialAccountAdapter per-provider override                       |
| SOCIAL-05 | `create-foundation-app --without social-auth` removes all social auth configuration cleanly   | Sentinel comment pattern; `removeSocialAuthModule()` in remove.ts; CLI flag wiring in index.ts                                  |

</phase_requirements>

---

## Summary

This phase adds social login to the Foundation Template across three providers. Google and GitHub use the standard allauth headless OAuth2 browser redirect flow — the frontend sends the user to `POST /api/v1/auth/browser/v1/auth/provider/redirect` (allauth provides this URL automatically when `allauth.headless` is in `INSTALLED_APPS`), the OAuth dance happens server-side, and allauth calls `HEADLESS_FRONTEND_URLS["socialaccount_login_error"]` or redirects back to the SPA. Apple is structurally different: the Expo SDK issues an identity token whose `aud` claim equals the iOS Bundle ID, not a Services ID, so allauth's standard `/provider/token` endpoint cannot verify it. A custom Django endpoint (e.g., `POST /api/v1/auth/apple/`) performs the verification using PyJWT against Apple's JWKS.

Credential management follows the established template pattern: env vars in `.env.example`, read into `SOCIALACCOUNT_PROVIDERS` at settings import time, with conditional provider inclusion so no provider is registered unless credentials are present. The `--without social-auth` removal path follows the existing sentinel-comment pattern used by billing and email modules.

The most important non-obvious fact: **do not add `allauth.socialaccount` to `INSTALLED_APPS` conditionally** — it is already there (added in an earlier phase). The phase adds the _provider sub-apps_ (`allauth.socialaccount.providers.google`, etc.) conditionally, and the `SOCIALACCOUNT_PROVIDERS` settings block with sentinel comments for removal.

**Primary recommendation:** Use allauth 65.x APPS array in `SOCIALACCOUNT_PROVIDERS` (settings-based, no SocialApp DB records needed), wire providers conditionally via env var checks in settings, use PyJWT + Apple JWKS for custom Apple endpoint.

---

## Standard Stack

### Core

| Library                                | Version                                       | Purpose                                                                             | Why Standard                                                                            |
| -------------------------------------- | --------------------------------------------- | ----------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| django-allauth                         | >=65.14.3 (already installed)                 | OAuth provider handling, email auto-connect, headless endpoints                     | Already in template; provides `/provider/redirect` and `/provider/token` headless URLs  |
| allauth.socialaccount.providers.google | (bundled)                                     | Google OAuth2                                                                       | Official allauth bundled provider                                                       |
| allauth.socialaccount.providers.github | (bundled)                                     | GitHub OAuth2                                                                       | Official allauth bundled provider                                                       |
| allauth.socialaccount.providers.apple  | (bundled)                                     | Apple Sign In — used for settings-based config only (not the verification endpoint) | Official allauth bundled provider; provides Apple-specific JWT client secret generation |
| pyjwt[crypto]                          | >=2.11.0 (already installed as pyjwt>=2.11.0) | Verify Apple identity tokens against Apple JWKS                                     | Already in template; `cryptography>=46.0.5` also already installed                      |
| requests                               | >=2.32.5 (already installed)                  | Fetch Apple JWKS from `https://appleid.apple.com/auth/keys`                         | Already in template                                                                     |
| expo-apple-authentication              | Expo SDK 53 built-in                          | iOS native Apple Sign In credential request                                         | Expo managed workflow — requires iOS-only conditional rendering                         |

### Supporting

| Library                            | Version  | Purpose                                 | When to Use                                            |
| ---------------------------------- | -------- | --------------------------------------- | ------------------------------------------------------ |
| @repo/business-logic (use-auth.ts) | internal | Add social login mutation hooks for web | New `useSocialLogin` hook or extend existing `useAuth` |

### Alternatives Considered

| Instead of                   | Could Use                                     | Tradeoff                                                                                                    |
| ---------------------------- | --------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| Custom Apple JWT endpoint    | allauth's standard `/provider/token` endpoint | Allauth's endpoint expects `aud` = Services ID; Expo issues `aud` = Bundle ID. Custom endpoint is required. |
| Inline if-blocks in settings | Django app config / AppConfig.ready()         | If-blocks in settings are simpler and consistent with existing EMAIL_BACKEND pattern                        |

**No new package installations required.** All dependencies (allauth, pyjwt, cryptography, requests) are already in `apps/api/pyproject.toml`. On the mobile side, `expo-apple-authentication` is part of Expo SDK 53 managed workflow.

---

## Architecture Patterns

### Recommended Project Structure

```
apps/api/
├── config/settings/base.py          # SOCIALACCOUNT_PROVIDERS block (sentinel-fenced)
├── apps/accounts/
│   ├── social_adapter.py            # Custom SocialAccountAdapter (email-merge per-provider)
│   └── apple_auth.py                # AppleJWTVerifier + POST /api/v1/auth/apple/ endpoint
apps/web/app/(auth)/
│   ├── page.tsx                     # Login page — add SocialButtons below form
│   └── signup/page.tsx             # Signup page — add SocialButtons below form
apps/web/src/components/auth/
│   └── social-buttons.tsx           # Conditional Google + GitHub buttons
apps/mobile/app/(auth)/
│   └── sign-in.tsx                  # Add Apple Sign In button (iOS-only)
packages/create-foundation-app/src/
│   ├── prompts.ts                   # Add "social-auth" to feature list
│   ├── remove.ts                    # Add removeSocialAuthModule()
│   └── index.ts                     # Wire --without social-auth flag
apps/api/tests/
│   └── test_scaffolder_social_removal.py  # SOCIAL-05 integration test
packages/create-foundation-app/tests/
│   └── remove-social-auth.test.ts   # Unit tests for removeSocialAuthModule()
```

### Pattern 1: Settings-Based Conditional Provider Registration

**What:** Read env vars at import time; only add provider to `INSTALLED_APPS` extensions and `SOCIALACCOUNT_PROVIDERS` when credentials are present. Mirrors the `EMAIL_BACKEND` auto-switch pattern.

**When to use:** All three social providers follow this pattern.

**Example (inside base.py, sentinel-fenced):**

```python
# ---------------------------------------------------------------------------
# SOCIAL AUTH MODULE
# ---------------------------------------------------------------------------
GOOGLE_CLIENT_ID: str = env("GOOGLE_CLIENT_ID", default="")
GOOGLE_CLIENT_SECRET: str = env("GOOGLE_CLIENT_SECRET", default="")
GITHUB_CLIENT_ID: str = env("GITHUB_CLIENT_ID", default="")
GITHUB_CLIENT_SECRET: str = env("GITHUB_CLIENT_SECRET", default="")
APPLE_CLIENT_ID: str = env("APPLE_CLIENT_ID", default="")
APPLE_TEAM_ID: str = env("APPLE_TEAM_ID", default="")
APPLE_KEY_ID: str = env("APPLE_KEY_ID", default="")
_apple_private_key_b64: str = env("APPLE_PRIVATE_KEY", default="")
APPLE_PRIVATE_KEY: str = (
    base64.b64decode(_apple_private_key_b64).decode() if _apple_private_key_b64 else ""
)

# Extend INSTALLED_APPS conditionally
_social_providers: list[str] = []
if GOOGLE_CLIENT_ID:  # SOCIAL AUTH MODULE
    _social_providers.append("allauth.socialaccount.providers.google")
if GITHUB_CLIENT_ID:  # SOCIAL AUTH MODULE
    _social_providers.append("allauth.socialaccount.providers.github")
if APPLE_CLIENT_ID:  # SOCIAL AUTH MODULE
    _social_providers.append("allauth.socialaccount.providers.apple")
INSTALLED_APPS = INSTALLED_APPS + _social_providers

# SOCIALACCOUNT_PROVIDERS: only include provider blocks when credentials present
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True

SOCIALACCOUNT_PROVIDERS: dict = {}
if GOOGLE_CLIENT_ID:
    SOCIALACCOUNT_PROVIDERS["google"] = {
        "APPS": [{"client_id": GOOGLE_CLIENT_ID, "secret": GOOGLE_CLIENT_SECRET, "key": ""}],
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
        "EMAIL_AUTHENTICATION": True,
    }
if GITHUB_CLIENT_ID:
    SOCIALACCOUNT_PROVIDERS["github"] = {
        "APPS": [{"client_id": GITHUB_CLIENT_ID, "secret": GITHUB_CLIENT_SECRET, "key": ""}],
        "SCOPE": ["user:email"],
        "VERIFIED_EMAIL": True,
        "EMAIL_AUTHENTICATION": True,
    }
if APPLE_CLIENT_ID:
    SOCIALACCOUNT_PROVIDERS["apple"] = {
        "APPS": [{
            "client_id": APPLE_CLIENT_ID,
            "secret": APPLE_KEY_ID,
            "key": APPLE_TEAM_ID,
            "settings": {
                "certificate_key": APPLE_PRIVATE_KEY,
                "hidden": True,  # iOS native only; never show on web
            },
        }],
    }
# ---------------------------------------------------------------------------
# END SOCIAL AUTH MODULE
# ---------------------------------------------------------------------------
```

Source: [allauth provider_configuration docs](https://docs.allauth.org/en/dev/socialaccount/provider_configuration.html), [allauth configuration docs](https://docs.allauth.org/en/latest/socialaccount/configuration.html)

### Pattern 2: Custom SocialAccountAdapter for Per-Provider Email Merge Control

**What:** Subclass `allauth.socialaccount.adapter.DefaultSocialAccountAdapter` and override `is_auto_signup_allowed` or `pre_social_login` to skip auto-connect for Apple relay emails.

**When to use:** `SOCIAL-04` — auto-merge is enabled globally but must be suppressed for `@privaterelay.appleid.com` addresses.

**Example:**

```python
# apps/accounts/social_adapter.py
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

APPLE_RELAY_DOMAIN = "privaterelay.appleid.com"

class FoundationSocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_email_verified(self, request, email: str) -> bool:
        # Apple relay addresses: treat as verified but never auto-connect
        # to existing password accounts (relay doesn't confirm identity ownership)
        if email and email.endswith(f"@{APPLE_RELAY_DOMAIN}"):
            return False  # prevents SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT
        return super().is_email_verified(request, email)
```

Then set `SOCIALACCOUNT_ADAPTER = "apps.accounts.social_adapter.FoundationSocialAccountAdapter"` in `base.py`.

**Confidence:** MEDIUM — the exact adapter method to override for per-provider email merge suppression requires validation against allauth 65.x internals. The `pre_social_login` hook may be more appropriate. See Open Questions.

### Pattern 3: Custom Apple JWT Verification Endpoint

**What:** A Django Ninja Extra endpoint at `POST /api/v1/auth/apple/` that receives the Expo `identityToken` JWT, verifies it against Apple's JWKS, creates/links a user account, and returns the JWT access + refresh tokens (app client pattern).

**When to use:** SOCIAL-03 — the only path for iOS native Apple Sign In.

**Why custom:** Expo's `expo-apple-authentication` issues an `identityToken` where `aud` = iOS Bundle ID (e.g., `com.yourapp.app`). Allauth's standard `/provider/token` endpoint for Apple expects `aud` = a Services ID (web OAuth). These are different Apple application types. Passing an iOS identity token to allauth's standard endpoint will fail JWT verification.

**Apple JWKS Verification (PyJWT pattern):**

```python
# apps/accounts/apple_auth.py
import requests
import jwt  # pyjwt
from jwt.algorithms import RSAAlgorithm

APPLE_JWKS_URL = "https://appleid.apple.com/auth/keys"
APPLE_ISSUER = "https://appleid.apple.com"

def verify_apple_identity_token(identity_token: str, bundle_id: str) -> dict:
    """Verify an Apple identity token from expo-apple-authentication.

    Returns the decoded payload (sub, email, email_verified, is_private_email).
    Raises jwt.PyJWTError on invalid token.
    """
    # Fetch Apple's JWKS (cache in production with functools.lru_cache / django.core.cache)
    jwks = requests.get(APPLE_JWKS_URL, timeout=5).json()
    # Match key by kid in token header
    unverified_header = jwt.get_unverified_header(identity_token)
    public_key = None
    for key_data in jwks["keys"]:
        if key_data["kid"] == unverified_header["kid"]:
            public_key = RSAAlgorithm.from_jwk(key_data)
            break
    if public_key is None:
        raise ValueError("Apple public key not found for kid")
    payload = jwt.decode(
        identity_token,
        public_key,
        algorithms=["RS256"],
        audience=bundle_id,
        issuer=APPLE_ISSUER,
        leeway=60,  # 60-second leeway for clock skew
    )
    return payload
```

Source: [PyJWT docs](https://pyjwt.readthedocs.io/en/latest/), [Apple JWKS](https://appleid.apple.com/auth/keys)

### Pattern 4: Web Social Login Buttons (Conditional Rendering)

**What:** A `SocialButtons` component checks which providers are configured (via a `/api/v1/auth/browser/v1/config` response or env vars exposed via Next.js `NEXT_PUBLIC_*`) and renders buttons accordingly. Clicking a button POSTs to allauth's redirect endpoint.

**Allauth headless browser social login flow:**

1. Frontend: `POST /api/v1/auth/browser/v1/auth/provider/redirect` with body `{"provider": "google", "process": "login", "callback_url": "/auth/callback"}`
2. Allauth: responds with `{"data": {"location": "https://accounts.google.com/..."}}`
3. Frontend: navigates to the returned URL
4. OAuth completes: allauth handles callback at `/accounts/google/login/callback/` (auto-registered)
5. Allauth: redirects to `HEADLESS_FRONTEND_URLS["socialaccount_login_error"]` on failure, or to `callback_url` on success

**Confidence:** HIGH — confirmed from allauth issue tracker and community usage patterns. The `/_allauth/browser/v1/auth/provider/redirect` endpoint is documented in allauth headless.

**Implementation note:** The web app uses `NEXT_PUBLIC_GOOGLE_ENABLED` and `NEXT_PUBLIC_GITHUB_ENABLED` environment variables (set to `"true"` when the corresponding API credentials are configured) to conditionally render buttons. This avoids a round-trip to the API config endpoint on every page load.

### Pattern 5: Mobile Apple Sign In (Expo)

**What:** Use `expo-apple-authentication` (Expo SDK 53 built-in) to request credentials. The returned `identityToken` is sent to the custom `POST /api/v1/auth/apple/` endpoint.

**iOS-only rendering:**

```typescript
// apps/mobile/app/(auth)/sign-in.tsx
import * as AppleAuthentication from "expo-apple-authentication";
import { Platform } from "react-native";

// In component JSX:
{Platform.OS === "ios" && (
  <AppleAuthentication.AppleAuthenticationButton
    buttonType={AppleAuthentication.AppleAuthenticationButtonType.SIGN_IN}
    buttonStyle={AppleAuthentication.AppleAuthenticationButtonStyle.BLACK}
    cornerRadius={8}
    onPress={handleAppleSignIn}
  />
)}
```

**Credential request:**

```typescript
async function handleAppleSignIn() {
  const credential = await AppleAuthentication.signInAsync({
    requestedScopes: [
      AppleAuthentication.AppleAuthenticationScope.FULL_NAME,
      AppleAuthentication.AppleAuthenticationScope.EMAIL,
    ],
  });
  // credential.identityToken — JWT, aud = bundle_id
  // credential.fullName — only populated on FIRST login
  // credential.email — only populated on FIRST login
  // Send to custom backend endpoint
  await appleLogin.mutateAsync({
    identity_token: credential.identityToken,
    full_name: credential.fullName?.givenName ?? null,
  });
}
```

Source: [Expo AppleAuthentication docs](https://docs.expo.dev/versions/latest/sdk/apple-authentication/)

### Anti-Patterns to Avoid

- **Using SocialApp DB records:** The template pattern stores credentials in env vars, not the Django admin. Configuring via both settings AND admin creates a `MultipleObjectsReturned` error in allauth.
- **Adding `allauth.socialaccount` conditionally:** It is already in `INSTALLED_APPS`. Only the provider sub-apps go in the conditional list.
- **Passing Apple identity token to allauth's standard `/provider/token` endpoint:** Will fail — `aud` mismatch (Bundle ID vs Services ID).
- **Reading Apple private key from a file path at runtime:** Breaks in Docker and cloud deploys. Use the env var content (base64-decoded PEM string) directly.
- **Calling Apple JWKS on every request without caching:** Apple's JWKS changes rarely; fetch and cache with a TTL (e.g., Django cache with 1-hour timeout) to avoid latency and rate limits.
- **Using `access_type: "offline"` for Google:** Only needed if the backend needs to refresh Google tokens independently. For a headless SaaS login flow, `online` is sufficient and simpler.

---

## Don't Hand-Roll

| Problem                               | Don't Build          | Use Instead                                                | Why                                                                    |
| ------------------------------------- | -------------------- | ---------------------------------------------------------- | ---------------------------------------------------------------------- |
| OAuth2 redirect flow (Google, GitHub) | Custom OAuth2 client | allauth `provider/redirect` headless endpoint              | State parameter, CSRF, token exchange, error handling all handled      |
| SocialAccount ↔ User linking          | Custom connect logic | allauth `SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT`  | Handles edge cases: duplicate emails, multiple connected providers     |
| Apple client secret generation        | Custom JWT signer    | allauth's built-in Apple provider generates client secrets | Apple requires ES256 JWT as client secret; allauth does this correctly |
| Apple public key fetching/caching     | Custom key store     | PyJWT + `RSAAlgorithm.from_jwk()` + Django cache           | Handles key rotation (Apple rotates JWKS periodically)                 |

**Key insight:** The only custom code needed is the Apple identity token verification endpoint — everything else is configuration.

---

## Common Pitfalls

### Pitfall 1: Allauth Callback URL Not Registered in Google/GitHub Console

**What goes wrong:** OAuth redirect fails with `redirect_uri_mismatch` (Google) or `The redirect_uri MUST match the registered callback URL` (GitHub).
**Why it happens:** allauth registers callback URLs under `/accounts/<provider>/login/callback/` by default. In this template, the allauth URLs are mounted under `api/v1/auth/`, making the callback `http://localhost:8000/api/v1/auth/google/login/callback/`.
**How to avoid:** Set OAuth App callback URL to `{BACKEND_URL}/api/v1/auth/google/login/callback/` (not the frontend URL). Document this in the phase output and in `.env.example` comments.
**Warning signs:** 302 redirect to Google/GitHub OAuth page, then immediate redirect back with error query param.

### Pitfall 2: Apple Private Key Newlines Corrupted in Env Var

**What goes wrong:** `jwt.exceptions.DecodeError: Not enough segments` or `Could not deserialize key data` when generating Apple client secrets.
**Why it happens:** PEM keys have newlines; many deployment platforms strip or escape newlines in env vars.
**How to avoid:** Base64-encode the `.p8` file content: `APPLE_PRIVATE_KEY=$(cat AuthKey_XXX.p8 | base64)`. Decode in settings: `base64.b64decode(env_value).decode()`. Document the encoding requirement in `.env.example` comments.
**Warning signs:** Apple client secret generation failing at startup or on first Apple Sign In attempt.

### Pitfall 3: SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT Applies to All Providers

**What goes wrong:** Apple relay addresses get auto-connected to an existing account, silently linking an unverified relay email to a real account.
**Why it happens:** `SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT=True` is a global setting; allauth does not have built-in per-provider overrides.
**How to avoid:** Custom `SocialAccountAdapter` that suppresses auto-connect for `@privaterelay.appleid.com` emails (see Pattern 2 above). Verify exact adapter hook in allauth 65.x internals before implementing.
**Warning signs:** Users with relay emails unexpectedly linked to existing accounts.

### Pitfall 4: allauth.socialaccount Already in INSTALLED_APPS

**What goes wrong:** If the plan adds `allauth.socialaccount` to `INSTALLED_APPS` again, Django raises `ImproperlyConfigured: Application labels aren't unique`.
**Why it happens:** `allauth.socialaccount` was added in an earlier phase — it is already present (line 112 of `base.py`).
**How to avoid:** Only add the provider sub-apps (`allauth.socialaccount.providers.google` etc.) conditionally. Never add `allauth.socialaccount` again.
**Warning signs:** Django startup error about duplicate app labels.

### Pitfall 5: Apple Only Returns User Name on First Login

**What goes wrong:** Return logins have `fullName = null` and `email = null` in the Expo credential response. If the endpoint attempts to overwrite the stored profile name with null, the user loses their name.
**Why it happens:** This is intentional Apple behavior — name and email are only transmitted once.
**How to avoid:** Backend endpoint: only update `user.full_name` if the provided value is non-empty (`if full_name: user.full_name = full_name`). Return logins carry only `identityToken` and `user.sub` — look up user by `SocialAccount.uid`.
**Warning signs:** Users losing their display name after signing out and back in on iOS.

### Pitfall 6: Scaffolder Leaves Dead `allauth.socialaccount` Migrations

**What goes wrong:** `manage.py check` passes but `migrate` tries to create social account tables even after `--without social-auth` removal.
**Why it happens:** `allauth.socialaccount` itself stays in `INSTALLED_APPS` (it was there before social auth was a feature), only the provider sub-apps are removed by the scaffolder.
**How to avoid:** The `removeSocialAuthModule()` function must remove `"allauth.socialaccount"` itself from `INSTALLED_APPS` (not just the provider apps), since this module was added as part of Phase 20's `SOCIAL AUTH MODULE` sentinel block.
**Warning signs:** `migrate` creates `socialaccount_*` tables in projects that opted out of social auth.

---

## Code Examples

### Base.py SOCIAL AUTH MODULE sentinel block (complete)

```python
# ---------------------------------------------------------------------------
# SOCIAL AUTH MODULE
# ---------------------------------------------------------------------------
import base64 as _base64  # noqa: E402

GOOGLE_CLIENT_ID: str = env("GOOGLE_CLIENT_ID", default="")
GOOGLE_CLIENT_SECRET: str = env("GOOGLE_CLIENT_SECRET", default="")
GITHUB_CLIENT_ID: str = env("GITHUB_CLIENT_ID", default="")
GITHUB_CLIENT_SECRET: str = env("GITHUB_CLIENT_SECRET", default="")
APPLE_CLIENT_ID: str = env("APPLE_CLIENT_ID", default="")
APPLE_TEAM_ID: str = env("APPLE_TEAM_ID", default="")
APPLE_KEY_ID: str = env("APPLE_KEY_ID", default="")
_apple_pk_b64: str = env("APPLE_PRIVATE_KEY", default="")
APPLE_PRIVATE_KEY: str = _base64.b64decode(_apple_pk_b64).decode() if _apple_pk_b64 else ""

_social_installed: list[str] = []  # SOCIAL AUTH MODULE
if GOOGLE_CLIENT_ID:  # SOCIAL AUTH MODULE
    _social_installed.append("allauth.socialaccount.providers.google")
if GITHUB_CLIENT_ID:  # SOCIAL AUTH MODULE
    _social_installed.append("allauth.socialaccount.providers.github")
if APPLE_CLIENT_ID:  # SOCIAL AUTH MODULE
    _social_installed.append("allauth.socialaccount.providers.apple")
INSTALLED_APPS = INSTALLED_APPS + _social_installed  # SOCIAL AUTH MODULE

SOCIALACCOUNT_ADAPTER = "apps.accounts.social_adapter.FoundationSocialAccountAdapter"  # SOCIAL AUTH MODULE
SOCIALACCOUNT_AUTO_SIGNUP = True  # SOCIAL AUTH MODULE
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True  # SOCIAL AUTH MODULE
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True  # SOCIAL AUTH MODULE

SOCIALACCOUNT_PROVIDERS: dict = {}  # SOCIAL AUTH MODULE
if GOOGLE_CLIENT_ID:  # SOCIAL AUTH MODULE
    SOCIALACCOUNT_PROVIDERS["google"] = {
        "APPS": [{"client_id": GOOGLE_CLIENT_ID, "secret": GOOGLE_CLIENT_SECRET, "key": ""}],
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
        "EMAIL_AUTHENTICATION": True,
    }
if GITHUB_CLIENT_ID:  # SOCIAL AUTH MODULE
    SOCIALACCOUNT_PROVIDERS["github"] = {
        "APPS": [{"client_id": GITHUB_CLIENT_ID, "secret": GITHUB_CLIENT_SECRET, "key": ""}],
        "SCOPE": ["user:email"],
        "VERIFIED_EMAIL": True,
        "EMAIL_AUTHENTICATION": True,
    }
if APPLE_CLIENT_ID:  # SOCIAL AUTH MODULE
    SOCIALACCOUNT_PROVIDERS["apple"] = {
        "APPS": [{
            "client_id": APPLE_CLIENT_ID,
            "secret": APPLE_KEY_ID,
            "key": APPLE_TEAM_ID,
            "settings": {"certificate_key": APPLE_PRIVATE_KEY, "hidden": True},
        }],
    }
# ---------------------------------------------------------------------------
# END SOCIAL AUTH MODULE
# ---------------------------------------------------------------------------
```

**Note on sentinel strategy:** The `# SOCIAL AUTH MODULE` inline comments on each line inside the block allow `removeSocialAuthModule()` to use a single regex to remove the whole `# -----------` fenced block AND individually tagged `INSTALLED_APPS` extension lines. This is consistent with how `removeEmailModule()` works.

### Scaffolder removeSocialAuthModule() (TypeScript skeleton)

```typescript
// packages/create-foundation-app/src/remove.ts
export async function removeSocialAuthModule(outputDir: string): Promise<void> {
  // 1. Remove allauth.socialaccount from INSTALLED_APPS in base.py
  // 2. Remove SOCIAL AUTH MODULE fenced block from base.py
  // 3. Remove SOCIALACCOUNT_ADAPTER, SOCIALACCOUNT_PROVIDERS, and related lines
  // 4. Remove all six social env vars from apps/api/.env.example
  // 5. Remove social buttons from apps/web/app/(auth)/page.tsx and signup/page.tsx
  // 6. Remove Apple Sign In button from apps/mobile/app/(auth)/sign-in.tsx
}
```

The removal function uses the same regex patterns as `removeEmailModule()`:

- Fenced block removal: `/\n# -{10,}\n# SOCIAL AUTH MODULE\n# -{10,}[\s\S]*?# -{10,}\n# END SOCIAL AUTH MODULE\n# -{10,}/`
- Line removal: match lines with `# SOCIAL AUTH MODULE` inline comment

### allauth headless browser OAuth redirect (frontend fetch call)

```typescript
// POST to initiate Google OAuth redirect
const response = await fetch("/api/v1/auth/browser/v1/auth/provider/redirect", {
  method: "POST",
  headers: { "Content-Type": "application/json", "X-CSRFToken": getCsrfToken() },
  credentials: "include",
  body: JSON.stringify({
    provider: "google", // or "github"
    process: "login",
    callback_url: "/auth/callback", // frontend URL that allauth redirects back to
  }),
});
const data = await response.json();
window.location.href = data.data.location; // navigate to Google OAuth consent screen
```

Source: allauth headless community patterns (allauth issue tracker, codeberg.org)

---

## State of the Art

| Old Approach                                                     | Current Approach                                                                   | When Changed             | Impact                                                             |
| ---------------------------------------------------------------- | ---------------------------------------------------------------------------------- | ------------------------ | ------------------------------------------------------------------ |
| SocialApp DB records for credentials                             | `SOCIALACCOUNT_PROVIDERS` APPS array in settings                                   | allauth 50+              | No Django admin setup step required; credentials fully in env vars |
| `allauth.socialaccount.providers.google.urls` manual URL include | Auto-discovered via `allauth.headless.urls`                                        | allauth 64+ headless     | No manual URL entries in `urls.py` for OAuth callbacks             |
| Separate allauth 64 / allauth 65 config format                   | allauth 65.x: `HEADLESS_ONLY`, `HEADLESS_FRONTEND_URLS`, `HEADLESS_TOKEN_STRATEGY` | allauth 65.0 (Sept 2024) | Template already on 65.x; no migration needed                      |

**Deprecated/outdated:**

- `SOCIALACCOUNT_PROVIDERS["google"]["APP"]` (singular): The old singular `APP` dict is deprecated in favor of `APPS` list. Use `APPS` array.
- Storing credentials via Django admin `SocialApp` model: Replaced by settings-based `APPS` array for template use.

---

## Open Questions

1. **Exact allauth 65.x adapter method for suppressing Apple relay auto-connect**
   - What we know: `SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT=True` is global; `DefaultSocialAccountAdapter` has `pre_social_login(request, sociallogin)` and `is_auto_signup_allowed(request, sociallogin)` hooks
   - What's unclear: Which hook to override to suppress auto-connect specifically for relay emails; whether checking `sociallogin.account.provider == "apple"` is sufficient or if checking the email domain is more reliable
   - Recommendation: At plan time, read `allauth/socialaccount/adapter.py` source (in the installed package) to identify the correct hook. The `pre_social_login` method can call `sociallogin.email_addresses` to inspect addresses. If no clean hook exists, set `SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT=False` globally and implement connect logic in the Apple custom endpoint manually.

2. **allauth headless `socialaccount_login_error` frontend URL**
   - What we know: `HEADLESS_FRONTEND_URLS` requires a `"socialaccount_login_error"` entry for failed OAuth flows
   - What's unclear: Whether a generic `/auth/error?provider=google&error=...` or provider-specific route is the right pattern for this template
   - Recommendation: Add `"socialaccount_login_error": f"{FRONTEND_URL}/auth/error"` to `HEADLESS_FRONTEND_URLS` in base.py as part of this phase.

3. **HEADLESS_FRONTEND_URLS for successful social login callback**
   - What we know: The `callback_url` parameter in the redirect POST controls where the user lands after OAuth success; allauth redirects to that URL
   - What's unclear: Whether allauth requires this to match a trusted origin or just blindly redirects
   - Recommendation: CSRF state parameter already handles this; plan to add `HEADLESS_FRONTEND_URLS["account_login"]` as a fallback, and document the frontend callback handler.

---

## Validation Architecture

### Test Framework

| Property           | Value                                                                                                          |
| ------------------ | -------------------------------------------------------------------------------------------------------------- |
| Framework          | pytest 8.x + pytest-django                                                                                     |
| Config file        | `apps/api/pytest.ini` or `pyproject.toml [tool.pytest.ini_options]`                                            |
| Quick run command  | `cd apps/api && python -m pytest tests/test_auth_integration.py tests/test_scaffolder_social_removal.py -x -q` |
| Full suite command | `cd apps/api && python -m pytest -x -q`                                                                        |
| TS unit tests      | `cd packages/create-foundation-app && pnpm test -- remove-social-auth`                                         |

### Phase Requirements → Test Map

| Req ID    | Behavior                                                                          | Test Type            | Automated Command                                                             | File Exists? |
| --------- | --------------------------------------------------------------------------------- | -------------------- | ----------------------------------------------------------------------------- | ------------ |
| SOCIAL-01 | Google OAuth: settings block active when `GOOGLE_CLIENT_ID` set                   | unit                 | `pytest tests/test_social_settings.py::test_google_provider_registered -x`    | Wave 0       |
| SOCIAL-01 | Google button present in web login page HTML                                      | manual/visual        | n/a                                                                           | n/a          |
| SOCIAL-02 | GitHub OAuth: settings block active when `GITHUB_CLIENT_ID` set                   | unit                 | `pytest tests/test_social_settings.py::test_github_provider_registered -x`    | Wave 0       |
| SOCIAL-03 | Apple JWT verification accepts valid token, rejects expired/bad-aud               | unit                 | `pytest tests/test_apple_auth.py::test_verify_identity_token -x`              | Wave 0       |
| SOCIAL-03 | Apple name stored on first login, not overwritten on return                       | unit                 | `pytest tests/test_apple_auth.py::test_name_persisted_first_login -x`         | Wave 0       |
| SOCIAL-04 | SocialAccountAdapter suppresses auto-connect for relay email                      | unit                 | `pytest tests/test_social_adapter.py::test_relay_email_not_auto_connected -x` | Wave 0       |
| SOCIAL-05 | `removeSocialAuthModule()` removes INSTALLED_APPS entry, settings block, env vars | unit (TS)            | `pnpm test -- remove-social-auth`                                             | Wave 0       |
| SOCIAL-05 | CLI integration: `manage.py check` passes after removal                           | integration (Python) | `pytest tests/test_scaffolder_social_removal.py -x`                           | Wave 0       |

### Sampling Rate

- **Per task commit:** `cd apps/api && python -m pytest tests/test_social_settings.py tests/test_apple_auth.py tests/test_social_adapter.py -x -q`
- **Per wave merge:** `cd apps/api && python -m pytest -x -q && cd ../../packages/create-foundation-app && pnpm test`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `apps/api/tests/test_social_settings.py` — covers SOCIAL-01, SOCIAL-02 (conditional provider registration)
- [ ] `apps/api/tests/test_apple_auth.py` — covers SOCIAL-03 (JWT verification + name persistence)
- [ ] `apps/api/tests/test_social_adapter.py` — covers SOCIAL-04 (relay email exclusion)
- [ ] `apps/api/tests/test_scaffolder_social_removal.py` — covers SOCIAL-05 (integration: manage.py check post-removal)
- [ ] `packages/create-foundation-app/tests/remove-social-auth.test.ts` — covers SOCIAL-05 (unit: regex removal correctness)

---

## Sources

### Primary (HIGH confidence)

- [allauth provider_configuration docs](https://docs.allauth.org/en/dev/socialaccount/provider_configuration.html) — APPS array format, settings-based credentials
- [allauth socialaccount configuration docs](https://docs.allauth.org/en/latest/socialaccount/configuration.html) — `SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT`, `SOCIALACCOUNT_EMAIL_AUTHENTICATION`
- [allauth Google provider docs](https://docs.allauth.org/en/latest/socialaccount/providers/google.html) — SCOPE, AUTH_PARAMS, OAUTH_PKCE_ENABLED
- [allauth GitHub provider docs](https://docs.allauth.org/en/latest/socialaccount/providers/github.html) — SCOPE, VERIFIED_EMAIL
- [allauth Apple provider docs](https://docs.allauth.org/en/latest/socialaccount/providers/apple.html) — APPS array with certificate_key, hidden flag, iOS vs web client_id distinction
- [PyJWT docs](https://pyjwt.readthedocs.io/en/latest/) — RSAAlgorithm.from_jwk, decode with audience/issuer
- [Expo AppleAuthentication docs](https://docs.expo.dev/versions/latest/sdk/apple-authentication/) — identityToken field, fullName population on first login only

### Secondary (MEDIUM confidence)

- allauth headless issue tracker (codeberg.org) — confirmed `/_allauth/browser/v1/auth/provider/redirect` endpoint URL pattern; `_allauth/app/v1/auth/provider/token` for native apps
- Apple JWKS endpoint `https://appleid.apple.com/auth/keys` — public keys for identity token verification
- [Expo expo/issues#16162](https://github.com/expo/expo/issues/16162) — confirmed `aud` = Bundle ID in Expo managed workflow identity token; explains why standard allauth endpoint cannot be used

### Tertiary (LOW confidence)

- Per-provider adapter hook identification — identified `pre_social_login` as candidate; needs validation against allauth 65.x source at plan time

---

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — all libraries verified against official docs; no new installs needed
- Architecture: HIGH for Google/GitHub (allauth standard); MEDIUM for Apple (custom endpoint pattern confirmed necessary, exact implementation needs verification)
- Pitfalls: HIGH — confirmed from allauth docs, community issues, and existing codebase patterns
- Scaffolder removal: HIGH — pattern directly mirrors Phase 19 email removal implementation

**Research date:** 2026-03-12
**Valid until:** 2026-04-12 (stable — allauth 65.x; Apple JWKS endpoint stable)
