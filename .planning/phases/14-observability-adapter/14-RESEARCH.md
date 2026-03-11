# Phase 14: ObservabilityAdapter - Research

**Researched:** 2026-03-11
**Domain:** PostHog Python SDK, posthog-js, posthog-react-native, Django middleware, Celery signals, create-foundation-app CLI
**Confidence:** HIGH (all decisions pre-locked in CONTEXT.md; verification confirms APIs are compatible)

---

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions

**Adapter ABC interface**

- Minimal interface: `capture_exception(exc, context)` and `capture_event(event, properties)` only
- Session replay and page views are auto-wired via providers — not manual adapter calls
- Three concrete classes: `PostHogAdapter` (default), `NoOpAdapter` (test/absent key fallback), `SentryAdapter` (stub only, documented swap)
- All live in `apps/core/observability.py`

**Django exception auto-capture**

- Custom Django middleware in `apps/core/middleware.py` (alongside existing `RequestContextMiddleware` from Phase 13)
- Middleware uses `process_exception()` hook: catches any unhandled exception, calls `get_observability_adapter().capture_exception()`, re-raises so Django's normal 500 flow continues
- Sits after `SessionMiddleware` (so `request.user` is available for context)
- Auto-identifies user: middleware reads `request.user.pk` and includes it as context in `capture_exception` — no explicit `identify()` call needed in views

**Celery exception auto-capture**

- Connect to Celery's `task_failure` signal in `CoreConfig.ready()` — same pattern as Phase 13's `task_prerun`/`task_postrun` for structlog
- Signal handler calls `get_observability_adapter().capture_exception(exc, context)` with `task_name` and `task_args` as context
- No custom Task base class — auto-capture guarantee is unconditional

**No-key / NoOp behavior**

- `OBSERVABILITY_ADAPTER = env('OBSERVABILITY_ADAPTER', default='apps.core.observability.NoOpAdapter')` in `base.py`
- `POSTHOG_API_KEY = env('POSTHOG_API_KEY', default='')` in `base.py`
- When `POSTHOG_API_KEY` is absent, default setting resolves to `NoOpAdapter` — all calls silently no-op, zero overhead
- `PostHogAdapter.__init__` reads `settings.POSTHOG_API_KEY` on instantiation and initializes `posthog.Client` — explicit opt-in by setting both env vars

**Settings location**

- All observability settings in `base.py` (not a separate file)
- `OBSERVABILITY_ADAPTER` defaults to `NoOpAdapter` path so CI and local dev without PostHog credentials work out of the box
- `.env.example` includes `POSTHOG_API_KEY=` (empty, with comment) so developers know to fill it in

**Django adapter resolution**

- `get_observability_adapter()` in `apps/core/observability.py` — same `import_string(settings.OBSERVABILITY_ADAPTER)` pattern as `get_adapter()` in billing

**Next.js PostHog setup**

- `PostHogProvider` from `posthog-js/react` added to `AppProviders` in `apps/web/app/providers.tsx`
- Handles page view tracking automatically via `usePathname` hook — no per-page instrumentation needed
- Env vars: `NEXT_PUBLIC_POSTHOG_KEY` + `NEXT_PUBLIC_POSTHOG_HOST` (defaults to `https://eu.posthog.com`)
- Session replay enabled by default: `session_recording: { maskAllInputs: true }` (inputs masked for privacy)
- No cookie consent gate — opt-out pattern; product-specific consent logic is per-project responsibility

**Expo mobile PostHog setup**

- `PostHogProvider` from `posthog-react-native` wraps the root navigator in `apps/mobile/app/_layout.tsx`
- Screen tracking is automatic via `useNavigationContainerRef` — no per-screen instrumentation
- Env var: `EXPO_PUBLIC_POSTHOG_KEY`

**SentryAdapter scope**

- Stub class only: `SentryAdapter` in `apps/core/observability.py` with `raise NotImplementedError` on all methods
- Block comment above the class: migration guide explaining which `sentry-sdk` calls map to each abstract method
- README section: "Swapping to Sentry" — covers Python SDK, Next.js (`@sentry/nextjs`), Expo (`@sentry/react-native`)
- No Sentry SDK installed in template — stub demonstrates the swap pattern without adding a dependency

**`--without observability` CLI removal (6 touch points)**

1. Delete `apps/api/apps/core/observability.py`
2. Remove `ObservabilityMiddleware` from `MIDDLEWARE` in `base.py`
3. Remove `OBSERVABILITY_ADAPTER` + `POSTHOG_API_KEY` from `base.py` settings
4. Remove `posthog` from `apps/api/pyproject.toml` (observability dependency group)
5. Remove `PostHogProvider` from `apps/web/app/providers.tsx` + remove `NEXT_PUBLIC_POSTHOG_*` from env examples
6. Remove `PostHogProvider` from `apps/mobile/app/_layout.tsx` + remove `EXPO_PUBLIC_POSTHOG_KEY` from mobile env example

- Implement as `removeObservability()` in `packages/create-foundation-app/src/remove.ts`
- Add `observability` to `SelectedFeatures` type in `prompts.ts` and wire into `promptFeatures()` multi-select

### Claude's Discretion

- Exact `PostHogAdapter.capture_exception()` context shape (which fields from `request`/`exc` to serialize)
- Whether to batch-configure PostHog via `django-posthog` or raw `posthog` Python SDK (raw SDK preferred — no extra dependency)
- `NoOpAdapter` method signatures (can be simple `pass` or return minimal dicts)
- PostHog host default (`eu.posthog.com` vs `us.posthog.com` vs `app.posthog.com`) — env var covers it
- Exact `task_failure` signal handler wiring location (inline in `CoreConfig.ready()` or imported from `observability.py`)

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>

## Phase Requirements

| ID     | Description                                                                                                                                                                                                                                                                  | Research Support                                                                                                                                                                                                                     |
| ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| OBS-03 | Developer can capture exceptions + product analytics + session replay via `ObservabilityAdapter` ABC with `PostHogAdapter` as default — covers Django + Celery + Next.js + Expo — `--without observability` removes it cleanly; `SentryAdapter` available as documented swap | PostHog Python SDK v7 `posthog.Posthog` client; posthog-js `PostHogProvider`; posthog-react-native `PostHogProvider`; existing billing adapter pattern is the structural model; `removeBillingModule()` is the removal pattern model |

</phase_requirements>

---

## Summary

Phase 14 wires exception tracking, product analytics, and session replay across four layers (Django, Celery, Next.js, Expo) behind a minimal `ObservabilityAdapter` ABC with two lines of interface: `capture_exception` and `capture_event`. The architecture is a direct port of the billing adapter pattern already in production in this codebase — `PaymentAdapter` → `ObservabilityAdapter`, `get_adapter()` → `get_observability_adapter()`, `StubAdapter` → `NoOpAdapter`.

The PostHog Python SDK (v7, current as of 2026-03) uses `posthog.Posthog(api_key, host=host)` for client instantiation and `client.capture_exception(exc, distinct_id, properties=...)` for manual exception capture. Django middleware `process_exception()` is the correct hook for unconditional auto-capture — it fires on any unhandled exception before Django's 500 handling, and the middleware must re-raise to leave Django's debug/logging flow intact. Celery's `task_failure` signal is the correct unconditional capture point for worker exceptions.

The frontend setup is straightforward: Next.js uses `PostHogProvider` from `posthog-js/react` inside the existing `AppProviders` client component, with a `PostHogPageView` inner component that uses `usePathname` to fire `$pageview` events on navigation. The React Native side uses `PostHogProvider` from `posthog-react-native` wrapping the root `Stack` in `_layout.tsx` — **with `autocapture.captureScreens` disabled** because Expo Router's architecture is incompatible with the `useNavigationState` hook that PostHog's autocapture relies on (known upstream issue, closed as "not planned"). Screen tracking defaults to page view events fired manually or via a `useEffect` hook watching the Expo Router pathname, which is documented in the CONTEXT.md as "automatic via `useNavigationContainerRef`" — the research clarifies the Expo Router limitation and the correct workaround.

**Primary recommendation:** Use raw `posthog` Python SDK (no `django-posthog` wrapper) initialized as a `posthog.Posthog` client instance stored on the adapter — same pattern as `StripeClient` in `StripeAdapter`. Use `posthog-react-native` with `autocapture={true}` but `autocapture={{ captureScreens: false }}` to avoid the Expo Router navigation state error; fire screen events via `useSegments` or `usePathname` from `expo-router` in a `useEffect`.

---

## Standard Stack

### Core

| Library                | Version                         | Purpose                                           | Why Standard                                                                                     |
| ---------------------- | ------------------------------- | ------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| `posthog` (Python)     | 7.9.8 (current)                 | Django + Celery exception capture, event tracking | PostHog's official Python SDK; raw client preferred over `django-posthog` wrapper (no extra dep) |
| `posthog-js`           | latest (via `posthog-js/react`) | Next.js analytics, session replay, page views     | Already the canonical PostHog JS SDK with React bindings included                                |
| `posthog-react-native` | 4.37.1 (current)                | Expo mobile analytics, autocapture                | Official PostHog RN SDK; managed Expo install via `npx expo install`                             |

### Supporting (for Expo install)

| Library             | Version        | Purpose                         | When to Use                                 |
| ------------------- | -------------- | ------------------------------- | ------------------------------------------- |
| `expo-file-system`  | SDK-compatible | PostHog RN storage backend      | Required peer dep for Expo managed workflow |
| `expo-application`  | SDK-compatible | Device/app metadata for PostHog | Required peer dep for Expo managed workflow |
| `expo-device`       | SDK-compatible | Device type detection           | Required peer dep for Expo managed workflow |
| `expo-localization` | SDK-compatible | Locale metadata                 | Required peer dep for Expo managed workflow |

### Alternatives Considered

| Instead of                                 | Could Use                          | Tradeoff                                                                                                                                           |
| ------------------------------------------ | ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| Raw `posthog` Python SDK                   | `django-posthog` wrapper           | Wrapper adds no capability and creates an extra dependency; raw SDK is simpler and follows billing adapter pattern                                 |
| `posthog-react-native` autocapture screens | Manual `useEffect` screen tracking | Autocapture's screen tracking doesn't work with Expo Router (useNavigationState error); manual `useEffect` with `useSegments` is the reliable path |

### Installation

```bash
# Python (add to pyproject.toml observability dependency group)
uv add posthog  # or: pip install posthog

# Next.js (posthog-js already available if not installed)
pnpm add posthog-js --filter @repo/web

# Expo mobile
npx expo install posthog-react-native expo-file-system expo-application expo-device expo-localization
```

---

## Architecture Patterns

### Recommended File Layout

```
apps/api/apps/core/
├── observability.py      # ObservabilityAdapter ABC + PostHogAdapter + NoOpAdapter + SentryAdapter stub
├── middleware.py         # ObservabilityMiddleware appended below RequestContextMiddleware
└── apps.py               # CoreConfig.ready() — add task_failure signal here

apps/api/config/settings/
└── base.py               # POSTHOG_API_KEY, POSTHOG_HOST, OBSERVABILITY_ADAPTER settings

apps/web/app/
└── providers.tsx         # PostHogProvider wraps AppProviders tree; PostHogPageView inside

apps/mobile/app/
└── _layout.tsx           # PostHogProvider wraps Stack navigator

packages/create-foundation-app/src/
├── remove.ts             # Add removeObservability() function
├── prompts.ts            # Add "observability" to SelectedFeatures + promptFeatures()
└── index.ts              # Call removeObservability() when not selected
```

### Pattern 1: ObservabilityAdapter ABC (mirrors PaymentAdapter)

**What:** Abstract base class with two abstract methods. All concrete adapters subclass it.
**When to use:** Every exception capture and event call in the codebase.

```python
# Source: modeled after apps/api/apps/billing/adapters.py
import abc
from typing import Any

class ObservabilityAdapter(abc.ABC):
    @abc.abstractmethod
    def capture_exception(self, exc: BaseException, context: dict[str, Any]) -> None:
        """Capture an unhandled exception with optional context."""

    @abc.abstractmethod
    def capture_event(self, event: str, properties: dict[str, Any]) -> None:
        """Capture a named product analytics event."""
```

### Pattern 2: PostHogAdapter (raw posthog.Posthog client)

**What:** Concrete adapter that initializes `posthog.Posthog` client from settings on instantiation.
**When to use:** When `POSTHOG_API_KEY` is set and `OBSERVABILITY_ADAPTER` points to this class.

```python
# Source: PostHog Python SDK docs — posthog.Posthog(api_key, host=host)
from django.conf import settings
from posthog import Posthog

class PostHogAdapter(ObservabilityAdapter):
    def __init__(self) -> None:
        self._client = Posthog(
            api_key=settings.POSTHOG_API_KEY,
            host=settings.POSTHOG_HOST,
        )

    def capture_exception(self, exc: BaseException, context: dict[str, Any]) -> None:
        distinct_id = context.get("user_id", "anonymous")
        self._client.capture_exception(exc, distinct_id, properties=context)

    def capture_event(self, event: str, properties: dict[str, Any]) -> None:
        distinct_id = properties.pop("distinct_id", "anonymous")
        self._client.capture(distinct_id, event, properties)
```

**Claude's discretion for context shape** — recommended fields for `capture_exception` context:

- `user_id` (str | None): `request.user.pk` if authenticated, else `"anonymous"`
- `path` (str): `request.path`
- `method` (str): `request.method`
- `exc_type` (str): `type(exc).__name__`

For Celery context:

- `task_name` (str): from signal kwargs `sender.__name__`
- `task_id` (str): from signal kwargs `task_id`
- `user_id`: `"celery"` (no user context in background tasks)

### Pattern 3: NoOpAdapter (silence without overhead)

**What:** No-op implementation — all methods are `pass`. Selected by default via settings.
**When to use:** Automatically when `POSTHOG_API_KEY` is absent (dev, CI, test).

```python
class NoOpAdapter(ObservabilityAdapter):
    def capture_exception(self, exc: BaseException, context: dict[str, Any]) -> None:
        pass

    def capture_event(self, event: str, properties: dict[str, Any]) -> None:
        pass
```

### Pattern 4: get_observability_adapter() (mirrors get_adapter() in billing)

**What:** Factory function resolving adapter via `import_string(settings.OBSERVABILITY_ADAPTER)`.
**When to use:** Called by middleware and signal handlers.

```python
# Source: modeled after apps/api/apps/billing/utils.py
from django.conf import settings
from django.utils.module_loading import import_string

def get_observability_adapter() -> ObservabilityAdapter:
    adapter_class = import_string(settings.OBSERVABILITY_ADAPTER)
    return adapter_class()
```

**Note:** A new adapter instance is created per call. This is fine for NoOpAdapter and safe for PostHogAdapter because `posthog.Posthog` is a lightweight client. If instantiation cost matters, cache the instance at module level or use a Django app-level singleton — but this is Claude's discretion.

### Pattern 5: ObservabilityMiddleware (process_exception hook)

**What:** Django middleware class appended to `apps/core/middleware.py` alongside `RequestContextMiddleware`.
**When to use:** Inserted into `MIDDLEWARE` after `RequestContextMiddleware` in `base.py`.

```python
# Source: Django middleware docs — process_exception() hook
class ObservabilityMiddleware:
    def __init__(self, get_response) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        return self.get_response(request)

    def process_exception(self, request: HttpRequest, exception: Exception) -> None:
        context = {
            "user_id": str(request.user.pk) if hasattr(request, "user") and request.user.is_authenticated else "anonymous",
            "path": request.path,
            "method": request.method,
            "exc_type": type(exception).__name__,
        }
        get_observability_adapter().capture_exception(exception, context)
        # Return None — Django continues its normal 500 flow (DEBUG pages, logging, etc.)
```

**Critical:** `process_exception` must return `None` (not re-raise). When `process_exception` returns `None`, Django continues its normal exception processing chain — the exception propagates, gets logged, and the 500 response is generated normally. Returning a response object from `process_exception` would suppress the exception.

### Pattern 6: Celery task_failure signal

**What:** Signal handler connected in `CoreConfig.ready()` that fires on any Celery task exception.
**When to use:** Wired once at app startup.

```python
# Source: modeled after Phase 13 signal wiring in CoreConfig.ready()
# Celery signal: task_failure(sender, task_id, exception, args, kwargs, traceback, einfo)
from celery.signals import task_failure

@task_failure.connect(weak=False)
def handle_task_failure(sender, task_id, exception, args, kwargs, traceback, einfo, **extra):
    from apps.core.observability import get_observability_adapter
    context = {
        "task_name": sender.__name__ if hasattr(sender, "__name__") else str(sender),
        "task_id": task_id,
        "task_args": str(args),
        "user_id": "celery",
    }
    get_observability_adapter().capture_exception(exception, context)
```

**`weak=False`** is required here (same as Phase 13's `worker_process_init` signal) to prevent the handler from being garbage collected.

### Pattern 7: Next.js PostHogProvider in providers.tsx

**What:** PostHogProvider wrapping the `AppProviders` tree, with inner `PostHogPageView` component.
**When to use:** Client-side only (`"use client"` already present on providers.tsx).

```typescript
// Source: PostHog Next.js docs — PostHogProvider + usePathname pattern
"use client";
import posthog from "posthog-js";
import { PostHogProvider, usePostHog } from "posthog-js/react";
import { useEffect, useRef } from "react";
import { usePathname } from "next/navigation";

// Initialize outside component to avoid re-init on re-render
if (typeof window !== "undefined") {
  posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
    api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST ?? "https://eu.i.posthog.com",
    capture_pageview: false, // Manual via PostHogPageView
    capture_pageleave: true,
    session_recording: {
      maskAllInputs: true, // Privacy-safe default
    },
  });
}

function PostHogPageView() {
  const pathname = usePathname();
  const posthog = usePostHog();
  const prevPathnameRef = useRef<string | null>(null);

  useEffect(() => {
    if (pathname && prevPathnameRef.current !== pathname) {
      prevPathnameRef.current = pathname;
      posthog.capture("$pageview", { $current_url: window.location.href });
    }
  }, [pathname, posthog]);

  return null;
}

// Inside AppProviders JSX:
// <PostHogProvider client={posthog}>
//   <PostHogPageView />
//   {children}
// </PostHogProvider>
```

### Pattern 8: Expo PostHogProvider in \_layout.tsx

**What:** PostHogProvider wrapping root `Stack` navigator. Screen tracking via `useSegments` workaround.
**When to use:** Root layout only.

```typescript
// Source: PostHog React Native docs — PostHogProvider with Expo install
// CRITICAL: Do NOT set autocapture.captureScreens = true with Expo Router
// (causes useNavigationState error — upstream issue, closed as "not planned")
import { PostHogProvider } from "posthog-react-native";

// Inside RootLayout:
// <PostHogProvider
//   apiKey={env.EXPO_PUBLIC_POSTHOG_KEY}
//   options={{ host: "https://eu.i.posthog.com" }}
//   autocapture={{ captureScreens: false }}  // Expo Router compat
// >
//   ...existing providers and Stack...
// </PostHogProvider>
```

**Screen tracking for Expo Router** — use `useSegments` from `expo-router` to manually fire `$screen` events:

```typescript
// Inside a hook or component inside PostHogProvider:
import { useSegments } from "expo-router";
import { usePostHog } from "posthog-react-native";
import { useEffect, useRef } from "react";

function PostHogScreenTracker() {
  const segments = useSegments();
  const posthog = usePostHog();
  const prevSegmentsRef = useRef<string | null>(null);
  const screenName = segments.join("/") || "(index)";

  useEffect(() => {
    if (prevSegmentsRef.current !== screenName) {
      prevSegmentsRef.current = screenName;
      posthog.screen(screenName);
    }
  }, [screenName, posthog]);

  return null;
}
```

### Pattern 9: removeObservability() in remove.ts

**What:** Six-step removal function following `removeBillingModule()` shape exactly.
**When to use:** When `--without observability` flag is passed to create-foundation-app.

Steps mirror the 6 touch points in CONTEXT.md:

1. Delete `apps/api/apps/core/observability.py`
2. Regex-remove `ObservabilityMiddleware` line from `MIDDLEWARE` in `base.py`
3. Regex-remove `OBSERVABILITY_ADAPTER` and `POSTHOG_API_KEY` + `POSTHOG_HOST` lines from `base.py` (use comment-delimited block: `# OBSERVABILITY MODULE` / `# END OBSERVABILITY MODULE`)
4. Regex-remove `posthog` dep line from the observability dep group in `pyproject.toml`
5. Regex-remove PostHog import + `PostHogProvider` wrapper + `PostHogPageView` from `providers.tsx`; regex-remove `NEXT_PUBLIC_POSTHOG_*` lines from `apps/web/.env.example`
6. Regex-remove PostHog import + `PostHogProvider` wrapper from `_layout.tsx`; regex-remove `EXPO_PUBLIC_POSTHOG_KEY` from `apps/mobile/.env.example`

### Anti-Patterns to Avoid

- **`process_exception` re-raising:** Don't call `raise` inside `process_exception`. Return `None` and Django handles the exception naturally. Re-raising causes duplicate exception processing.
- **Global `posthog.api_key = ...` initialization:** Don't set the module-level singleton like the Django docs show. Use `posthog.Posthog(api_key=...)` to get an instance — same pattern as StripeAdapter uses `stripe_sdk.StripeClient(api_key=...)`. Global mutation is not thread-safe.
- **`autocapture.captureScreens: true` with Expo Router:** This triggers `useNavigationState` error. Always set `captureScreens: false` and use `useSegments` hook instead.
- **Instantiating PostHogAdapter in tests:** PostHogAdapter requires `settings.POSTHOG_API_KEY`. Tests use `NoOpAdapter` via the default setting — never override to PostHogAdapter in tests.
- **Deleting `observability.py` only:** The `--without observability` flow must also remove the `task_failure` signal registration from `CoreConfig.ready()` and the middleware entry from `MIDDLEWARE`. Missing either leaves broken imports.

---

## Don't Hand-Roll

| Problem                        | Don't Build                            | Use Instead                                                     | Why                                                                                                               |
| ------------------------------ | -------------------------------------- | --------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| Session replay masking         | Custom DOM scrubbing                   | `session_recording: { maskAllInputs: true }` in posthog-js init | PostHog handles input masking, network request filtering, and replay compression                                  |
| Celery task exception tracking | Custom task base class with try/except | `task_failure` signal                                           | Signal fires unconditionally on ALL tasks regardless of task base class; custom base class only covers subclasses |
| Adapter resolution boilerplate | Custom `getattr` or importlib          | `import_string(settings.OBSERVABILITY_ADAPTER)`                 | Already proven in billing; handles dotted path resolution, import errors, class vs instance                       |
| Page view deduplication        | Counter or Set                         | `useRef` to track previous pathname                             | PostHog's `capture_pageview: false` + `useEffect` on pathname change is idiomatic; framework handles dedup        |

---

## Common Pitfalls

### Pitfall 1: `process_exception` return value confusion

**What goes wrong:** Middleware returns `None` (correct) but developer assumes exceptions are suppressed. Or middleware returns a `Response` object to "handle" the error — which silently swallows exceptions from PostHog's perspective (no re-raise, no Django 500 handler).
**Why it happens:** Django middleware `process_exception` docs say returning a response suppresses exception propagation.
**How to avoid:** Always return `None` explicitly (or `return` with no value). Add a docstring: "Returns None to continue Django's normal 500 flow."
**Warning signs:** 500 errors not appearing in Django logs or debug pages.

### Pitfall 2: `task_failure` signal fired in the wrong process

**What goes wrong:** Signal connected in `CoreConfig.ready()` at import time, but Celery worker processes fork after `ready()` — the signal handler exists in the parent process but may not survive the fork boundary.
**Why it happens:** Celery uses prefork pool; signals registered before fork are inherited but async-safe setup requires `worker_process_init`.
**How to avoid:** `weak=False` on signal connection prevents GC. For Phase 13 reference: `worker_process_init` is used for OTel because `BatchSpanProcessor` uses threads. `task_failure` signal doesn't use threads — connecting in `CoreConfig.ready()` is correct for this case.
**Warning signs:** Celery task exceptions captured in development (single worker) but not in production (prefork pool).

### Pitfall 3: `PostHogProvider` wrapping order in providers.tsx

**What goes wrong:** `PostHogProvider` wraps the outermost tree but `PostHogPageView` is outside `PostHogProvider` — `usePostHog()` returns null.
**Why it happens:** Provider-Consumer pattern requires PostHogPageView to be a _descendant_ of PostHogProvider.
**How to avoid:** `PostHogPageView` must be inside `<PostHogProvider>...</PostHogProvider>`.
**Warning signs:** `usePostHog()` returns undefined in `PostHogPageView`.

### Pitfall 4: Expo Router screen tracking with autocapture

**What goes wrong:** `autocapture={true}` (or `autocapture={{ captureScreens: true }}`) causes: `Error: Couldn't get the navigation state. Is your component inside a navigator?`
**Why it happens:** PostHog RN's screen autocapture uses `useNavigationState` which requires a parent `NavigationContainer`. Expo Router _is_ the NavigationContainer and doesn't expose it to children.
**How to avoid:** Set `autocapture={{ captureScreens: false }}` and implement `PostHogScreenTracker` component using `useSegments` from `expo-router`.
**Warning signs:** App crashes on launch when PostHogProvider wraps the navigator.

### Pitfall 5: `pyproject.toml` observability dep group not in production install

**What goes wrong:** `posthog` lives in an optional dep group `[observability]` and isn't installed in the production Docker build.
**Why it happens:** Same mistake as billing's `[billing]` group — optional groups require explicit `--extra observability` flag.
**How to avoid:** `posthog` should be in the main `[project.dependencies]` list (not a separate group), exactly like structlog and opentelemetry packages. It's a runtime dependency, not optional at the package manager level — the NoOpAdapter handles the "off" case at runtime via settings, not at install time.
**Warning signs:** `ImportError: No module named 'posthog'` in production.

### Pitfall 6: PostHog `posthog-js` `api_host` URL format

**What goes wrong:** Using `https://app.posthog.com` as host — this is the UI URL, not the ingestion endpoint.
**Why it happens:** Confusion between the PostHog app URL and the ingestion API URL.
**How to avoid:** Use `https://us.i.posthog.com` (US) or `https://eu.i.posthog.com` (EU). The CONTEXT.md default is `https://eu.posthog.com` — verify against PostHog's current docs; the correct ingestion host for EU cloud is `https://eu.i.posthog.com`.
**Warning signs:** Events not appearing in PostHog dashboard; CORS errors in browser console.

---

## Code Examples

Verified patterns from existing codebase + PostHog SDK docs:

### Existing billing utils.py (model for get_observability_adapter)

```python
# Source: apps/api/apps/billing/utils.py (existing)
from django.conf import settings
from django.utils.module_loading import import_string
from apps.billing.adapters import PaymentAdapter

def get_adapter() -> PaymentAdapter:
    adapter_class = import_string(settings.BILLING_ADAPTER)
    return adapter_class()
```

### removeBillingModule pattern (model for removeObservability)

```typescript
// Source: packages/create-foundation-app/src/remove.ts (existing)
// Pattern: readFile → regex replace → writeFile for each touch point
// Marker comments in source files enable reliable removal:
//   # BILLING MODULE / # END BILLING MODULE in base.py
//   # BILLING_START / # BILLING_END in urls.py
// Use same pattern: # OBSERVABILITY MODULE / # END OBSERVABILITY MODULE in base.py
```

### PostHog Python SDK v7 client instantiation

```python
# Source: PostHog Python SDK docs (posthog v7.9.8)
from posthog import Posthog

client = Posthog(
    api_key="phc_...",
    host="https://eu.i.posthog.com",
    # enable_exception_autocapture=True,  # NOT needed — we use middleware
)
client.capture_exception(exc, distinct_id="user-123", properties={"path": "/api/..."})
```

### Celery task_failure signal (model: Phase 13 structlog signal)

```python
# Source: Phase 13 CoreConfig.ready() pattern (existing)
# task_failure kwargs: sender, task_id, exception, args, kwargs, traceback, einfo
from celery.signals import task_failure

@task_failure.connect(weak=False)
def handle_task_failure(sender, task_id, exception, args, **extra):
    ...
```

### SelectedFeatures type extension (prompts.ts)

```typescript
// Source: packages/create-foundation-app/src/prompts.ts (existing)
// Current: Array<"web" | "mobile" | "landing" | "ai" | "billing">
// Add:     | "observability"
export type SelectedFeatures = Array<
  "web" | "mobile" | "landing" | "ai" | "billing" | "observability"
>;
```

---

## State of the Art

| Old Approach                                                 | Current Approach                                                 | When Changed                          | Impact                                                                           |
| ------------------------------------------------------------ | ---------------------------------------------------------------- | ------------------------------------- | -------------------------------------------------------------------------------- |
| `posthog.api_key = "..."` global assignment                  | `posthog.Posthog(api_key=..., host=...)` instance                | v3+ SDK                               | Thread-safe; multiple clients possible; matches billing adapter pattern          |
| `exception_autocapture_integrations = [Integrations.Django]` | General-purpose context middleware or manual `capture_exception` | v6+ SDK                               | Simpler; no integration list needed; our custom middleware is the right approach |
| PostHog RN `autocapture.captureScreens: true`                | Manual `useSegments` + `posthog.screen()`                        | Ongoing (Expo Router incompatibility) | Screen tracking still works; just not automatic                                  |

**Deprecated/outdated:**

- `django-posthog` wrapper package: No longer needed; raw `posthog` SDK has all Django integration points. Not in PyPI with active maintenance.
- `posthog-react-native` from separate `posthog-js-lite` repo: That repo is now archived; `posthog-react-native` is maintained as part of `posthog-js` monorepo.

---

## Open Questions

1. **PostHog EU ingestion host URL**
   - What we know: CONTEXT.md specifies `https://eu.posthog.com` as default host; npm search results mention `https://eu.i.posthog.com`
   - What's unclear: Whether `https://eu.posthog.com` redirects to `https://eu.i.posthog.com` or returns CORS errors
   - Recommendation: Use `https://eu.i.posthog.com` for posthog-js and posthog-react-native (confirmed ingestion endpoint from multiple sources); `https://eu.posthog.com` for Python SDK host (works for server-side). Either value is set by `POSTHOG_HOST` / `NEXT_PUBLIC_POSTHOG_HOST` env var so the default doesn't need to be perfect.

2. **PostHogAdapter instantiation cost (per-call vs singleton)**
   - What we know: `get_observability_adapter()` creates a new instance per call (same as `get_adapter()` in billing); `posthog.Posthog.__init__` initializes a queue and background consumer thread
   - What's unclear: Whether creating a new `Posthog` instance per request/signal is safe or causes thread leaks
   - Recommendation: Cache the adapter instance at module level using a `_adapter_instance: ObservabilityAdapter | None = None` module-level variable with lazy init, or create a singleton via Django's app config. This is Claude's discretion — start with per-call (billing pattern) and optimize if needed.

3. **`task_failure` signal and Celery prefork pool**
   - What we know: Phase 13 used `worker_process_init` for OTel because of thread-based `BatchSpanProcessor`; `task_failure` signal connected in `CoreConfig.ready()` should work in prefork workers
   - What's unclear: Whether posthog.Posthog's background consumer thread survives the prefork boundary
   - Recommendation: Connect `task_failure` signal in `CoreConfig.ready()` (as specified in CONTEXT.md). If PostHog client is instantiated in `PostHogAdapter.__init__` and called from within the signal handler, the client is created fresh per call — no pre-fork thread issue.

---

## Validation Architecture

### Test Framework

| Property           | Value                                                   |
| ------------------ | ------------------------------------------------------- |
| Framework          | pytest 8.x + pytest-django                              |
| Config file        | `apps/api/pyproject.toml` — `[tool.pytest.ini_options]` |
| Quick run command  | `cd apps/api && python -m pytest tests/core/ -x -q`     |
| Full suite command | `cd apps/api && python -m pytest tests/ -x -q`          |

### Phase Requirements → Test Map

| Req ID | Behavior                                                                       | Test Type   | Automated Command                                                                    | File Exists? |
| ------ | ------------------------------------------------------------------------------ | ----------- | ------------------------------------------------------------------------------------ | ------------ |
| OBS-03 | `NoOpAdapter.capture_exception` and `capture_event` are silent no-ops          | unit        | `pytest tests/core/test_observability.py::test_noop_adapter -x`                      | ❌ Wave 0    |
| OBS-03 | `PostHogAdapter` calls `client.capture_exception` with correct context         | unit (mock) | `pytest tests/core/test_observability.py::test_posthog_adapter_capture_exception -x` | ❌ Wave 0    |
| OBS-03 | `get_observability_adapter()` returns `NoOpAdapter` when default settings used | unit        | `pytest tests/core/test_observability.py::test_get_adapter_default -x`               | ❌ Wave 0    |
| OBS-03 | `ObservabilityMiddleware.process_exception` calls adapter and returns None     | unit        | `pytest tests/core/test_observability.py::test_middleware_process_exception -x`      | ❌ Wave 0    |
| OBS-03 | `ObservabilityMiddleware` includes `user_id` from `request.user` in context    | unit        | `pytest tests/core/test_observability.py::test_middleware_user_context -x`           | ❌ Wave 0    |
| OBS-03 | `task_failure` signal fires adapter on Celery task exception                   | unit        | `pytest tests/core/test_observability.py::test_celery_signal_handler -x`             | ❌ Wave 0    |
| OBS-03 | `--without observability` removes PostHog imports; `manage.py check` passes    | integration | `pytest tests/test_scaffolder_observability_removal.py -x`                           | ❌ Wave 0    |

### Sampling Rate

- **Per task commit:** `cd apps/api && python -m pytest tests/core/test_observability.py -x -q`
- **Per wave merge:** `cd apps/api && python -m pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `apps/api/tests/core/test_observability.py` — covers OBS-03 adapter unit tests, middleware tests, signal handler tests
- [ ] `apps/api/tests/test_scaffolder_observability_removal.py` — covers CLI removal integration test (modeled on `test_scaffolder_billing_removal.py`)

_(conftest.py and pytest infrastructure already exist — no Wave 0 framework gaps)_

---

## Sources

### Primary (HIGH confidence)

- PostHog Python SDK GitHub (master README) — version 7.3.1+ confirmed, Python 3.12 supported
- Existing `apps/api/apps/billing/adapters.py` — PaymentAdapter pattern (exact structural model)
- Existing `apps/api/apps/billing/utils.py` — `get_adapter()` pattern (exact model)
- Existing `apps/api/apps/core/middleware.py` — `RequestContextMiddleware` sibling pattern
- Existing `apps/api/apps/core/apps.py` — `CoreConfig.ready()` signal wiring pattern
- Existing `apps/api/apps/core/tracing.py` — no-op-when-absent pattern
- Existing `packages/create-foundation-app/src/remove.ts` — `removeBillingModule()` exact model
- Existing `packages/create-foundation-app/src/prompts.ts` — `SelectedFeatures` type

### Secondary (MEDIUM confidence)

- WebSearch: posthog Python SDK v7.9.8 current version (PyPI, 2026)
- WebSearch: posthog-react-native v4.37.1 current version (npm, March 2026)
- WebSearch: PostHog Django docs — `posthog.api_key` global init pattern (official docs)
- WebSearch: PostHog Python docs — `capture_exception(exc, distinct_id, properties=...)` signature
- WebSearch: PostHog RN docs — `npx expo install posthog-react-native expo-file-system expo-application expo-device expo-localization`
- WebSearch: PostHog Next.js docs — `capture_pageview: false` + `usePathname` page view pattern
- GitHub PostHog/posthog-js issues/2740 — Expo Router `useNavigationState` incompatibility confirmed, closed "not planned"

### Tertiary (LOW confidence)

- PostHog ingestion host URL: `eu.i.posthog.com` vs `eu.posthog.com` — could not confirm canonical URL from docs (PostHog website serves CSS only to fetch tool). Treat as LOW until implementation verifies.

---

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — existing billing pattern is identical; PostHog SDK version confirmed via WebSearch
- Architecture: HIGH — all patterns are either direct ports of existing billing adapter code or confirmed via official docs
- Pitfalls: MEDIUM/HIGH — `process_exception` behavior is documented Django behavior (HIGH); Expo Router autocapture incompatibility confirmed via GitHub issue (HIGH); host URL format is LOW confidence
- Expo screen tracking workaround: MEDIUM — `useSegments` pattern is reasonable but not confirmed against PostHog's own examples

**Research date:** 2026-03-11
**Valid until:** 2026-04-11 (PostHog SDK APIs are relatively stable; Expo Router compatibility issue is ongoing upstream)
