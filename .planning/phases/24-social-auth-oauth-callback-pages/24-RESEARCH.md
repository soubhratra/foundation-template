# Phase 24: Social Auth OAuth Callback Pages - Research

**Researched:** 2026-03-12
**Domain:** Next.js App Router page creation, django-allauth headless social auth redirect flow
**Confidence:** HIGH

---

<phase_requirements>

## Phase Requirements

| ID        | Description                                                 | Research Support                                                                                                                                       |
| --------- | ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| SOCIAL-01 | User can sign up and log in via Google OAuth on the web app | The callback page at `/auth/callback` completes the web OAuth flow; session is already set by allauth's Django-side callback before the redirect fires |
| SOCIAL-02 | User can sign up and log in via GitHub OAuth on the web app | Same callback page handles GitHub; allauth uses identical redirect path for all OAuth2 providers                                                       |

</phase_requirements>

---

## Summary

Phase 20 built the full social auth backend and the "initiate OAuth" frontend (the Google/GitHub buttons on the login page). The OAuth redirect request hardcodes `callback_url: "/auth/callback"` in `social-buttons.tsx`. allauth uses this value as `next_url` in the OAuth state machine: after Django's internal `/accounts/google/login/callback/` endpoint finishes the token exchange and creates/logs-in the user, it issues an HTTP redirect to that `next_url`. For error cases, allauth redirects to the `HEADLESS_FRONTEND_URLS["socialaccount_login_error"]` URL — which is already configured as `{FRONTEND_URL}/auth/error`.

Both `/auth/callback` and `/auth/error` currently return HTTP 404 because those page files do not exist. This phase creates exactly two files:

- `apps/web/app/(auth)/callback/page.tsx` — reads allauth session, calls `useAuth().refetch()`, redirects to dashboard
- `apps/web/app/(auth)/error/page.tsx` — reads `?error=` query param, displays human-readable message, links back to `/`

**Primary recommendation:** Two small client components, one per page. No new dependencies, no new API calls, no backend changes. The session cookie is already set by the time the browser hits `/auth/callback` — the page only needs to trigger a React Query refetch, then navigate to `/dashboard`.

---

## Standard Stack

### Core

| Library                               | Version          | Purpose                                                              | Why Standard                             |
| ------------------------------------- | ---------------- | -------------------------------------------------------------------- | ---------------------------------------- |
| Next.js App Router                    | 15.1.x           | File-based routing; `app/(auth)/callback/page.tsx` creates the route | Project standard, already used           |
| `useAuth` from `@repo/business-logic` | workspace        | `refetch()` re-fetches `/api/v1/users/me` to confirm session is live | Established auth hook, exposes `refetch` |
| `useRouter` (next/navigation)         | Next.js built-in | `router.replace("/dashboard")` after successful refetch              | Used in existing auth pages              |
| `useSearchParams` (next/navigation)   | Next.js built-in | Read `?error=` and `?error_process=` on the error page               | Used in `verify-email/page.tsx`          |
| `AuthCard` from `@/components/auth`   | local            | Error page UI shell matching existing auth page style                | All auth pages use this component        |
| `AuthLinks` from `@/components/auth`  | local            | "Back to sign-in" link in error page footer                          | Used in all existing auth pages          |

### Supporting

| Library                                 | Version | Purpose                                               | When to Use                    |
| --------------------------------------- | ------- | ----------------------------------------------------- | ------------------------------ |
| Sonner toast (`@/components/ui/sonner`) | 1.5.x   | Optional: show success toast on callback page         | Existing pattern in login page |
| Lucide icons                            | 0.564.x | Optional spinner / loading indicator on callback page | Already in project             |

### Alternatives Considered

| Instead of                        | Could Use                          | Tradeoff                                                                                                                                                                                                                                          |
| --------------------------------- | ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `useAuth().refetch()`             | Direct `fetch("/api/v1/users/me")` | `refetch()` updates the React Query cache so all downstream consumers see auth state immediately; raw fetch does not                                                                                                                              |
| `router.replace`                  | `router.push`                      | `replace` avoids adding `/auth/callback` to browser history (user cannot back-navigate into the callback page)                                                                                                                                    |
| Client component with `useEffect` | Server component with redirect     | Server component cannot read Django's session cookie in this flow; allauth sets `sessionid` via `Set-Cookie` on the final redirect response, which the browser handles after the redirect — the Next.js server component would not see it in time |

**Installation:** No new packages required.

---

## Architecture Patterns

### Recommended Project Structure

```
apps/web/app/(auth)/
├── page.tsx              # Login (existing)
├── signup/page.tsx       # Signup (existing)
├── reset/page.tsx        # Password reset (existing)
├── verify-email/page.tsx # Email verification (existing)
├── callback/
│   └── page.tsx          # NEW: OAuth callback handler
└── error/
    └── page.tsx          # NEW: OAuth error display
```

Both new pages sit inside `(auth)/` so they inherit `(auth)/layout.tsx` — the same `AuthShellClient` wrapper and split-panel layout used by all auth pages. No new layout file needed.

### Pattern 1: OAuth Callback Page (client component with `useEffect`)

**What:** Mount → trigger `refetch()` → on success navigate to dashboard; on failure navigate to `/auth/error`
**When to use:** When the auth session is established server-side before the browser loads the page

```typescript
// Source: verified against useAuth() hook interface in packages/business-logic/src/hooks/use-auth.ts
"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@repo/business-logic";

export default function OAuthCallbackPage() {
  const router = useRouter();
  const { refetch, isAuthenticated } = useAuth();

  useEffect(() => {
    void refetch().then((result) => {
      if (result.data?.id) {
        router.replace("/dashboard");
      } else {
        router.replace("/auth/error?error=unknown");
      }
    });
  }, [refetch, router]);

  // Show a loading/processing state while refetch resolves
  return (
    <div className="flex flex-col items-center gap-4 py-16 text-center">
      {/* Loading indicator */}
    </div>
  );
}
```

### Pattern 2: OAuth Error Page (client component reading search params)

**What:** Read `?error=` query param, map to human-readable message, display with link back to login
**When to use:** When allauth redirects to `socialaccount_login_error` URL

allauth appends these params on error redirects (verified in `allauth/headless/socialaccount/internal.py`):

- `?error=unknown` — catch-all for unexpected failures
- `?error=cancelled` — user cancelled the OAuth consent screen
- `?error=denied` — provider denied access
- `?error=reauthentication_required` — session requires re-auth
- `?error=signup_closed` — registration is disabled
- `?error=permission_denied` — general permission error
- `?error_process=login` — the process that failed (always `login` in our case)

```typescript
// Source: verified in allauth/socialaccount/providers/base/constants.py + headless/socialaccount/internal.py
"use client";

import { useSearchParams } from "next/navigation";
import { AuthCard, AuthLinks } from "@/components/auth";

const ERROR_MESSAGES: Record<string, string> = {
  unknown:     "An unexpected error occurred. Please try again.",
  cancelled:   "You cancelled the sign-in. Try again when ready.",
  denied:      "Access was denied by the provider. Please try again.",
  reauthentication_required: "Re-authentication required. Please sign in again.",
  signup_closed: "Account registration is currently closed.",
  permission_denied: "You do not have permission to sign in.",
};

export default function OAuthErrorPage() {
  const searchParams = useSearchParams();
  const errorCode = searchParams?.get("error") ?? "unknown";
  const message = ERROR_MESSAGES[errorCode] ?? ERROR_MESSAGES.unknown;

  return (
    <AuthCard
      eyebrow="Authentication error"
      title="Sign-in failed"
      description={message}
      footer={
        <AuthLinks items={[{ prefix: "Ready to try again?", label: "Back to sign-in", href: "/" }]} />
      }
    >
      {/* No form — display-only */}
      <p className="text-sm text-muted-foreground text-center">
        Error code: <code className="font-mono">{errorCode}</code>
      </p>
    </AuthCard>
  );
}
```

### Anti-Patterns to Avoid

- **Using a server component for the callback page:** allauth sets `sessionid` via `Set-Cookie` on the final OAuth redirect. The Next.js server component render happens before the browser fully resolves cookies from that redirect. A client component using `useEffect` fires after hydration, when cookies are committed.
- **Calling `router.push("/dashboard")` instead of `router.replace`:** Leaves `/auth/callback` in browser history; user can inadvertently navigate back to the loading page.
- **Displaying raw error codes to users:** Map `?error=` values to human-readable strings (see error map above). The raw code should be shown only as supplementary detail.
- **Not wrapping `useSearchParams` in `Suspense`:** Next.js 15 requires `useSearchParams()` on client components to be wrapped in `<Suspense>` boundaries, or the page will throw during static generation. Since `(auth)/layout.tsx` already exports `dynamic = "force-dynamic"`, static generation is disabled and this is not a blocking issue — but be aware of the constraint.

---

## Don't Hand-Roll

| Problem                         | Don't Build                        | Use Instead                                                          | Why                                                                                                 |
| ------------------------------- | ---------------------------------- | -------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| Session state check after OAuth | Custom fetch to `/api/v1/users/me` | `useAuth().refetch()`                                                | Updates React Query cache atomically; all subscribers see new auth state simultaneously             |
| Error message mapping           | Switch/case statement              | `Record<string, string>` lookup table                                | Error codes from allauth are a fixed set (verified); simple map is sufficient and testable          |
| Loading spinner                 | Custom SVG animation               | Existing `AuthSkeleton` or Lucide `Loader2` icon with `animate-spin` | Already in project, consistent with design system                                                   |
| Auth UI shell                   | Custom card/layout                 | `AuthCard` + `(auth)/layout.tsx`                                     | Error page sits inside `(auth)` route group; inherits the existing split-panel layout automatically |

---

## Common Pitfalls

### Pitfall 1: Callback Page Returns 404 in Production

**What goes wrong:** The file `apps/web/app/(auth)/callback/page.tsx` doesn't exist → Next.js returns 404 when allauth redirects to `/auth/callback`.
**Why it happens:** Phase 20 wired the `callback_url` in `social-buttons.tsx` but deferred page creation.
**How to avoid:** This is the primary deliverable of Phase 24 — create the file.
**Warning signs:** Google/GitHub OAuth flow completes on the provider side but user lands on a 404 page.

### Pitfall 2: Error Page Returns 404

**What goes wrong:** `HEADLESS_FRONTEND_URLS["socialaccount_login_error"]` in `base.py` points to `{FRONTEND_URL}/auth/error` but the file doesn't exist.
**Why it happens:** The Django setting was added in Phase 20 without the corresponding Next.js page.
**How to avoid:** Create `apps/web/app/(auth)/error/page.tsx`.
**Warning signs:** Any OAuth error (user cancels, provider rejects) → 404.

### Pitfall 3: `refetch()` Resolves Before Session Cookie Is Committed

**What goes wrong:** `refetch()` fires too early and returns unauthenticated — user gets redirected to error page even though the OAuth succeeded.
**Why it happens:** Race condition between cookie commitment and React hydration.
**How to avoid:** In practice this is not an issue: `useEffect` runs after hydration, and the browser commits `Set-Cookie` headers from the redirect chain before rendering starts. The `sessionid` cookie is available when the Next.js page mounts.
**Warning signs:** Intermittent failures where the callback page redirects to `/auth/error?error=unknown` even after successful Google/GitHub login.

### Pitfall 4: Infinite Redirect Loop on Callback Page

**What goes wrong:** The callback page always redirects to `/auth/error` because the `refetch()` check is wrong (e.g., checking `isAuthenticated` state from the initial render instead of the `refetch()` result).
**Why it happens:** `isAuthenticated` from `useAuth()` may be `false` on initial mount (query not yet resolved). The check must use the `data` from the `refetch()` promise return value, not the ambient `isAuthenticated` boolean.
**How to avoid:** Use `refetch().then((result) => { if (result.data?.id) ... })` — evaluate `result.data` from the promise, not the hook's reactive state.

### Pitfall 5: `useSearchParams()` Without Suspense Boundary Warning

**What goes wrong:** Next.js warns or throws because `useSearchParams()` is used outside a `<Suspense>` boundary during static generation.
**Why it happens:** Next.js App Router requires Suspense when using `useSearchParams` in statically rendered pages.
**How to avoid:** `(auth)/layout.tsx` already exports `dynamic = "force-dynamic"`, which disables static generation for all pages in the route group. No additional Suspense wrapper is needed, but test with `next build` to confirm no static optimization warnings.

---

## Code Examples

### How allauth Determines the Callback URL

```python
# Source: allauth/headless/socialaccount/views.py (verified in installed venv)
# RedirectToProviderView.post() — called when social-buttons.tsx POSTs:
#   { provider: "google", process: "login", callback_url: "/auth/callback" }

def post(self, request, *args, **kwargs):
    form = RedirectToProviderForm(request.POST)
    ...
    provider = form.cleaned_data["provider"]
    next_url = form.cleaned_data["callback_url"]   # <-- "/auth/callback"
    process = form.cleaned_data["process"]
    return provider.redirect(request, process, next_url=next_url, headless=True)
```

After Django's internal OAuth2 callback finalizes (token exchange, user creation/login), allauth redirects to `next_url` (success) or `HEADLESS_FRONTEND_URLS["socialaccount_login_error"]` (error).

### How allauth Appends Error Params

```python
# Source: allauth/headless/socialaccount/internal.py (verified in installed venv)
# complete_login() — success path redirects to sociallogin.state["next"] ("/auth/callback")
# error path:
next_url = httpkit.add_query_params(
    next_url,                               # "/auth/callback" for errors that happen after
                                            # the state is known; error URL for pre-state errors
    {"error": error, "error_process": sociallogin.state["process"]},
)
# For pre-state errors (e.g., user denies before state is established):
next_url = httpkit.get_frontend_url(request, "socialaccount_login_error") or "/"
next_url = httpkit.add_query_params(next_url, params)
# Resulting URL: /auth/error?error=denied&error_process=login
```

### Existing `refetch` Usage Pattern

```typescript
// Source: packages/business-logic/src/hooks/use-auth.ts (line 138)
// UseAuthResult exposes:
readonly refetch: UserQueryResult["refetch"];
// refetch() returns Promise<QueryObserverResult<CurrentUser | undefined, never>>
// result.data is CurrentUser | undefined
// CurrentUser has { id: string; email: string; ... }
```

### `social-buttons.tsx` Callback URL (existing, for reference)

```typescript
// Source: apps/web/src/components/auth/social-buttons.tsx (line 17-22)
// The callback_url sent to allauth — must match the page we create
body: JSON.stringify({
  provider,
  process: "login",
  callback_url: "/auth/callback",  // <- creates the page at this path
}),
```

---

## State of the Art

| Old Approach                                    | Current Approach                               | When Changed             | Impact                                                                      |
| ----------------------------------------------- | ---------------------------------------------- | ------------------------ | --------------------------------------------------------------------------- |
| allauth traditional redirect (Django templates) | allauth headless mode (`HEADLESS_ONLY = True`) | Phase 02 (project setup) | Django redirects to a frontend URL; frontend page must finalize the session |
| Callback page missing (gap from Phase 20)       | Phase 24 creates the missing pages             | This phase               | Closes INT-01 + INT-02; unblocks E2E OAuth testing                          |

**Deprecated/outdated:**

- None relevant to this phase. The pattern is stable.

---

## Open Questions

1. **Does allauth redirect to `/auth/callback` (no error params) on success, or does it redirect to the error URL?**
   - What we know: `complete_login()` in `allauth/headless/socialaccount/internal.py` redirects to `sociallogin.state["next"]` (which is `/auth/callback`) on the happy path. Error case redirects to `socialaccount_login_error` URL (`/auth/error`).
   - What's unclear: Whether any intermediate OAuth stages (e.g., email verification required before login completes) could redirect to `/auth/callback` with a pending state instead of a completed session. In that case, `refetch()` would return unauthenticated.
   - Recommendation: On the callback page, if `refetch()` returns no user, redirect to `/auth/error?error=unknown` rather than hanging. This handles the edge case gracefully.

2. **Should the callback page show a spinner or render blank while `refetch()` resolves?**
   - What we know: `refetch()` is a network call (GET `/api/v1/users/me`) and may take 100–500ms.
   - What's unclear: User preference for visual feedback.
   - Recommendation: Show a simple centered "Completing sign-in..." text with a `Loader2` spinner. Avoid using `AuthCard` (which implies user action is needed) — a minimal loading state matches the `billing/return/page.tsx` pattern.

---

## Validation Architecture

### Test Framework

| Property           | Value                                   |
| ------------------ | --------------------------------------- |
| Framework          | Vitest 4.x + React Testing Library 16.x |
| Config file        | `apps/web/vitest.config.ts`             |
| Quick run command  | `pnpm --filter @repo/web test`          |
| Full suite command | `pnpm --filter @repo/web test`          |

### Phase Requirements → Test Map

| Req ID    | Behavior                                                              | Test Type | Automated Command                          | File Exists? |
| --------- | --------------------------------------------------------------------- | --------- | ------------------------------------------ | ------------ |
| SOCIAL-01 | Callback page renders loading state on mount                          | unit      | `pnpm --filter @repo/web test -- callback` | ❌ Wave 0    |
| SOCIAL-01 | Callback page calls `refetch()` in useEffect                          | unit      | `pnpm --filter @repo/web test -- callback` | ❌ Wave 0    |
| SOCIAL-01 | Callback page redirects to `/dashboard` when refetch returns user     | unit      | `pnpm --filter @repo/web test -- callback` | ❌ Wave 0    |
| SOCIAL-01 | Callback page redirects to `/auth/error` when refetch returns no user | unit      | `pnpm --filter @repo/web test -- callback` | ❌ Wave 0    |
| SOCIAL-02 | Error page renders human-readable message for `?error=cancelled`      | unit      | `pnpm --filter @repo/web test -- error`    | ❌ Wave 0    |
| SOCIAL-02 | Error page renders human-readable message for `?error=unknown`        | unit      | `pnpm --filter @repo/web test -- error`    | ❌ Wave 0    |
| SOCIAL-02 | Error page renders link back to sign-in page                          | unit      | `pnpm --filter @repo/web test -- error`    | ❌ Wave 0    |

### Sampling Rate

- **Per task commit:** `pnpm --filter @repo/web test`
- **Per wave merge:** `pnpm --filter @repo/web test`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `apps/web/src/__tests__/app/(auth)/callback.test.tsx` — covers SOCIAL-01 callback page behavior
- [ ] `apps/web/src/__tests__/app/(auth)/error.test.tsx` — covers SOCIAL-02 error page rendering

_(Existing test infrastructure — Vitest + RTL + setup.ts — covers all phase requirements; only test files are missing)_

---

## Sources

### Primary (HIGH confidence)

- Installed allauth venv (`/apps/api/.venv/lib/python3.12/site-packages/allauth/`) — direct source inspection of:
  - `headless/socialaccount/internal.py` — redirect flow and error URL construction
  - `headless/socialaccount/views.py` — `RedirectToProviderView`, `callback_url` handling
  - `socialaccount/providers/base/constants.py` — `AuthError` values
- `apps/api/config/settings/base.py` — `HEADLESS_FRONTEND_URLS` configuration confirming `/auth/error` target
- `apps/web/src/components/auth/social-buttons.tsx` — `callback_url: "/auth/callback"` hardcoded in POST body
- `packages/business-logic/src/hooks/use-auth.ts` — `refetch` on `UseAuthResult` interface
- `apps/web/app/(auth)/layout.tsx` — `dynamic = "force-dynamic"` already set; `AuthShellClient` used by all child pages
- `apps/web/app/(dashboard)/billing/return/page.tsx` — closest existing pattern: client page using `useEffect` + `router.replace`

### Secondary (MEDIUM confidence)

- Phase 20 VERIFICATION.md — confirms social auth backend and web buttons are complete; callback/error pages explicitly not created
- `.planning/ROADMAP.md` — 2-plan structure (24-01: callback page, 24-02: error page) already defined by product owner

### Tertiary (LOW confidence)

- None. All claims verified against local codebase or installed allauth source.

---

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — all libraries already in project, no new dependencies
- Architecture: HIGH — allauth redirect flow verified against installed source; callback URL verified against existing `social-buttons.tsx`
- Pitfalls: HIGH — race condition analysis based on direct code inspection; error codes verified against allauth constants

**Research date:** 2026-03-12
**Valid until:** 2026-06-12 (allauth headless API is stable; Next.js App Router conventions are stable)
