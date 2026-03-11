# Phase 14: ObservabilityAdapter - Context

**Gathered:** 2026-03-11
**Status:** Ready for planning

<domain>
## Phase Boundary

Wire error tracking + product analytics + session replay via an `ObservabilityAdapter` ABC modeled after `PaymentAdapter`. `PostHogAdapter` is the default. `NoOpAdapter` is auto-selected when `POSTHOG_API_KEY` is absent. `--without observability` strips all PostHog imports cleanly across Django, Next.js, and Expo, with `manage.py check` passing clean.

Requirements: OBS-03.

</domain>

<decisions>
## Implementation Decisions

### Adapter ABC interface

- Minimal interface: `capture_exception(exc, context)` and `capture_event(event, properties)` only
- Session replay and page views are auto-wired via providers — not manual adapter calls
- Three concrete classes: `PostHogAdapter` (default), `NoOpAdapter` (test/absent key fallback), `SentryAdapter` (stub only, documented swap)
- All live in `apps/core/observability.py`

### Django exception auto-capture

- Custom Django middleware in `apps/core/middleware.py` (alongside existing `RequestContextMiddleware` from Phase 13)
- Middleware uses `process_exception()` hook: catches any unhandled exception, calls `get_observability_adapter().capture_exception()`, re-raises so Django's normal 500 flow continues
- Sits after `SessionMiddleware` (so `request.user` is available for context)
- Auto-identifies user: middleware reads `request.user.pk` and includes it as context in `capture_exception` — no explicit `identify()` call needed in views

### Celery exception auto-capture

- Connect to Celery's `task_failure` signal in `CoreConfig.ready()` — same pattern as Phase 13's `task_prerun`/`task_postrun` for structlog
- Signal handler calls `get_observability_adapter().capture_exception(exc, context)` with `task_name` and `task_args` as context
- No custom Task base class — auto-capture guarantee is unconditional

### No-key / NoOp behavior

- `OBSERVABILITY_ADAPTER = env('OBSERVABILITY_ADAPTER', default='apps.core.observability.NoOpAdapter')` in `base.py`
- `POSTHOG_API_KEY = env('POSTHOG_API_KEY', default='')` in `base.py`
- When `POSTHOG_API_KEY` is absent, default setting resolves to `NoOpAdapter` — all calls silently no-op, zero overhead
- `PostHogAdapter.__init__` reads `settings.POSTHOG_API_KEY` on instantiation and initializes `posthog.Client` — explicit opt-in by setting both env vars

### Settings location

- All observability settings in `base.py` (not a separate file)
- `OBSERVABILITY_ADAPTER` defaults to `NoOpAdapter` path so CI and local dev without PostHog credentials work out of the box
- `.env.example` includes `POSTHOG_API_KEY=` (empty, with comment) so developers know to fill it in

### Django adapter resolution

- `get_observability_adapter()` in `apps/core/observability.py` — same `import_string(settings.OBSERVABILITY_ADAPTER)` pattern as `get_adapter()` in billing

### Next.js PostHog setup

- `PostHogProvider` from `posthog-js/react` added to `AppProviders` in `apps/web/app/providers.tsx`
- Handles page view tracking automatically via `usePathname` hook — no per-page instrumentation needed
- Env vars: `NEXT_PUBLIC_POSTHOG_KEY` + `NEXT_PUBLIC_POSTHOG_HOST` (defaults to `https://eu.posthog.com`)
- Session replay enabled by default: `session_recording: { maskAllInputs: true }` (inputs masked for privacy)
- No cookie consent gate — opt-out pattern; product-specific consent logic is per-project responsibility

### Expo mobile PostHog setup

- `PostHogProvider` from `posthog-react-native` wraps the root navigator in `apps/mobile/app/_layout.tsx`
- Screen tracking is automatic via `useNavigationContainerRef` — no per-screen instrumentation
- Env var: `EXPO_PUBLIC_POSTHOG_KEY`

### SentryAdapter scope

- Stub class only: `SentryAdapter` in `apps/core/observability.py` with `raise NotImplementedError` on all methods
- Block comment above the class: migration guide explaining which `sentry-sdk` calls map to each abstract method
- README section: "Swapping to Sentry" — covers Python SDK (`sentry_sdk.init()`), Next.js (`@sentry/nextjs`), Expo (`@sentry/react-native`)
- No Sentry SDK installed in template — stub demonstrates the swap pattern without adding a dependency

### `--without observability` CLI removal (6 touch points)

1. Delete `apps/api/apps/core/observability.py`
2. Remove `ObservabilityMiddleware` from `MIDDLEWARE` in `base.py`
3. Remove `OBSERVABILITY_ADAPTER` + `POSTHOG_API_KEY` from `base.py` settings
4. Remove `posthog` from `apps/api/requirements.txt`
5. Remove `PostHogProvider` from `apps/web/app/providers.tsx` + remove `NEXT_PUBLIC_POSTHOG_*` from `.env.example` and `apps/web/.env.example`
6. Remove `PostHogProvider` from `apps/mobile/app/_layout.tsx` + remove `EXPO_PUBLIC_POSTHOG_KEY` from `apps/mobile/.env.example`

- Implement as `removeObservability()` in `packages/create-foundation-app/src/remove.ts` — same function shape as `removeBilling()`
- Add `observability` to `SelectedFeatures` type in `prompts.ts` and wire into `promptFeatures()` multi-select

### Claude's Discretion

- Exact `PostHogAdapter.capture_exception()` context shape (which fields from `request`/`exc` to serialize)
- Whether to batch-configure PostHog via `django-posthog` or raw `posthog` Python SDK (raw SDK preferred — no extra dependency)
- `NoOpAdapter` method signatures (can be simple `pass` or return minimal dicts)
- PostHog host default (`eu.posthog.com` vs `us.posthog.com` vs `app.posthog.com`) — env var covers it
- Exact `task_failure` signal handler wiring location (inline in `CoreConfig.ready()` or imported from `observability.py`)

</decisions>

<code_context>

## Existing Code Insights

### Reusable Assets

- `apps/api/apps/billing/adapters.py`: `PaymentAdapter` ABC — exact structural model for `ObservabilityAdapter`. Same `abc.ABC` + `@abc.abstractmethod` pattern.
- `apps/api/apps/billing/utils.py`: `get_adapter()` via `import_string(settings.BILLING_ADAPTER)` — copy this pattern for `get_observability_adapter()`
- `apps/api/apps/billing/stub_adapter.py`: StubAdapter pattern — model for `NoOpAdapter`
- `apps/api/apps/core/middleware.py`: Existing `RequestContextMiddleware` (Phase 13) — `ObservabilityMiddleware` is a sibling in the same file or a separate class below it
- `apps/api/apps/core/tracing.py`: `configure_otel()` no-op-when-absent pattern — exact same philosophy for `PostHogAdapter` (no-op when key absent)
- `apps/web/app/providers.tsx`: `AppProviders` client component — `PostHogProvider` wraps the tree here
- `apps/mobile/app/_layout.tsx`: Root layout navigator — `PostHogProvider` wraps the navigator here
- `packages/create-foundation-app/src/remove.ts`: `removeBilling()` function — structural model for `removeObservability()`
- `packages/create-foundation-app/src/prompts.ts`: `SelectedFeatures` type + `promptFeatures()` — add `"observability"` option

### Established Patterns

- Settings split `base.py`/`development.py`/`production.py` — new observability settings go in `base.py`
- `env()` via `django-environ` — `POSTHOG_API_KEY` and `OBSERVABILITY_ADAPTER` follow same `env("...", default="...")` pattern
- `CoreConfig.ready()` for signal registration — `task_failure` signal connects here (same as Phase 13's structlog signals)
- Adapter resolution pattern: `import_string(settings.X_ADAPTER)` — already proven with billing

### Integration Points

- `MIDDLEWARE` list in `base.py`: insert `ObservabilityMiddleware` after existing `RequestContextMiddleware` (Phase 13)
- `CoreConfig.ready()` in `apps/core/apps.py`: connect `task_failure` signal (alongside Phase 13's task signals)
- `apps/web/app/providers.tsx`: wrap children with `PostHogProvider` inside `AppProviders`
- `apps/mobile/app/_layout.tsx`: wrap navigator with `PostHogProvider`
- `packages/create-foundation-app/src/remove.ts`: add `removeObservability()` function
- `packages/create-foundation-app/src/prompts.ts`: add `"observability"` to `SelectedFeatures` and `promptFeatures()`
- `packages/create-foundation-app/src/index.ts`: call `removeObservability()` when observability not selected

</code_context>

<specifics>
## Specific Ideas

- `NoOpAdapter` auto-selected via default settings value — no conditional logic needed in `get_observability_adapter()`, just `import_string(settings.OBSERVABILITY_ADAPTER)()`
- Middleware re-raises after `capture_exception` so Django's normal 500 flow (DEBUG error pages, logging) continues unchanged
- `maskAllInputs: true` on session recording — privacy-safe default that doesn't require per-project config
- SentryAdapter stub + comment block is the "documented swap" — the code tells you exactly what to implement without installing a dependency

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

_Phase: 14-observability-adapter_
_Context gathered: 2026-03-11_
