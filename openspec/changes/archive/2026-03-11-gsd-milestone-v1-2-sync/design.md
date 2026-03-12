## Context

This is a milestone sync, not a new feature build. Milestone v1.2 (Phases 13–18) has already been implemented, verified, and committed. All 17 requirements are satisfied. This change captures the architectural decisions made during implementation so future products scaffolded from this template inherit consistent, documented patterns.

The design document records decisions that are already in the codebase — it explains the "why" for reviewers of the specs and for future contributors who encounter these patterns.

## Goals / Non-Goals

**Goals:**

- Document key architectural decisions made during v1.2 so they are preserved in specs and not lost in git history
- Explain the rationale behind non-obvious choices (adapter pattern, middleware ordering, Redis DB split, plain Django views for health probes, no native nplusone pytest plugin)
- Identify trade-offs accepted during implementation so future milestones can revisit them with context

**Non-Goals:**

- Implementing anything new — all code is already shipped
- Rehashing obvious decisions (e.g., "we use structlog because we chose structlog")
- Specifying line-by-line implementation details — that lives in the code and phase SUMMARY files

## Decisions

### 1. ObservabilityAdapter ABC mirrors PaymentAdapter — swappable via one Django setting

**Decision:** `ObservabilityAdapter` is a Django ABC with `PostHogAdapter` as the default, loaded via `get_observability_adapter()` factory using a `OBSERVABILITY_ADAPTER` dotted-path setting. `NoOpAdapter` is the default in `base.py`; `PostHogAdapter` is activated by setting `POSTHOG_API_KEY`.

**Rationale:** PostHog was chosen over Sentry as the default because a single PostHog SDK covers errors + analytics + feature flags + session replay. Locking in Sentry would require a second dependency for analytics. The adapter pattern keeps it swappable without changing application code — `SentryAdapter` is documented as a one-setting swap. This mirrors the `PaymentAdapter` pattern from v1.1, establishing a template-wide convention for optional integrations.

**Alternatives considered:**

- Sentry as default: Rejected — PostHog covers more surface area with one SDK; Sentry available as `SentryAdapter`
- Direct PostHog calls (no adapter): Rejected — couples application code to PostHog; `--without observability` removal would require touching every call site

---

### 2. Health probes as plain Django views, not Ninja Extra controllers

**Decision:** `/api/health/live|ready|startup` are implemented as plain `django.http.JsonResponse` view functions mounted before the Ninja app at `path("api/health/", ...)`.

**Rationale:** Health probes must work even if the Ninja app fails to initialize (misconfigured router, import error in a controller). Plain Django views bypass Ninja entirely and are available as soon as Django's URL resolver is functional. Probes are mounted before `api/v1/` in `urls.py` to prevent URL shadowing.

**Alternatives considered:**

- Ninja Extra controller for health probes: Rejected — circular dependency risk; probes should be independent of API layer health
- Third-party health check library (django-health-check): Rejected — adds a dependency for three simple functions; implementation is 119 lines of transparent, testable code

---

### 3. Redis uses separate DB indices for broker, cache, and sessions

**Decision:** Redis DB 0 = Celery broker (`REDIS_URL`), DB 1 = Django cache (`CACHE_REDIS_URL`), DB 2 = Django sessions (`SESSION_REDIS_URL`). All three env vars are injected into Docker Compose service environment blocks.

**Rationale:** Sharing a single Redis DB across all three uses creates operational risk: a `FLUSHDB` for cache debugging also clears task queues and session data. Separate DB indices provide logical isolation at zero infrastructure cost (same Redis instance). The env var split allows each concern to be pointed at a different Redis instance in production without code changes.

**Trade-off accepted:** Three env vars instead of one. Mitigated by documenting all three in `.env.example` with clear comments.

---

### 4. RequestContextMiddleware + ObservabilityMiddleware ordering

**Decision:** MIDDLEWARE order (relevant section): `RequestContextMiddleware` → `ObservabilityMiddleware` → `AuthRateLimitMiddleware`. CSPMiddleware sits at position 1 (immediately after SecurityMiddleware).

**Rationale:** `RequestContextMiddleware` must run first to bind `request_id`, `user_id`, `method`, `path` to structlog context — these fields must be available when `ObservabilityMiddleware.process_exception` captures an exception. `CSPMiddleware` at position 1 ensures every response gets security headers regardless of what other middleware does. `AuthRateLimitMiddleware` runs last in the chain so it sees authenticated request state.

**Known gap:** `status_code` and `duration_ms` are absent from structlog context on unhandled 500 paths — exception propagation bypasses the response-binding step in `RequestContextMiddleware.__call__`. A future improvement would add `process_exception` to `RequestContextMiddleware` to bind `status_code=500` and approximate `duration_ms`.

---

### 5. nplusone: no native pytest plugin in v1.0.0 — custom conftest implementation

**Decision:** `nplusone>=1.0` has no `nplusone.ext.pytest` plugin. A custom `_LazyLoadProfiler` context manager and `allow_lazy_load` decorator were implemented directly in `conftest.py`. A synthetic `nplusone.ext.pytest` module is registered in `sys.modules` for import compatibility with any code that references it.

**Rationale:** The plan referenced `nplusone.ext.pytest.allow_lazy_load` which does not exist. Rather than pin an older nplusone version with a plugin, the equivalent behavior was reimplemented using nplusone's internal `LazyListener` blinker signal. The functional contract (raise immediately on N+1, suppress with `@allow_lazy_load` decorator per-test) is fully preserved.

**Trade-off accepted:** Custom conftest code that future maintainers must understand. Mitigated by in-code comments and the 18-02-SUMMARY.md decision log.

---

### 6. OTel zero-overhead no-op when OTEL_EXPORTER_OTLP_ENDPOINT is unset

**Decision:** `configure_otel()` returns immediately if `OTEL_EXPORTER_OTLP_ENDPOINT` is not set. `OTLPSpanExporter` is imported lazily (inside the function body) so the ~100ms import overhead is only paid when tracing is active.

**Rationale:** CI and local dev without Jaeger should incur zero overhead from OTel. Making tracing opt-in via an env var means developers can run locally without Jaeger and without any OTel errors or latency. Jaeger is available in Docker Compose for those who need it.

---

### 7. schemathesis uses CLI tool, not pytest plugin; runs against live Django dev server

**Decision:** The CI `schemathesis` job runs `schemathesis run http://127.0.0.1:8000/api/openapi.json --checks all` against a live `manage.py runserver` instance, not the `@schema.parametrize()` pytest plugin.

**Rationale:** The pytest plugin requires `@schema.parametrize()` decorators on test functions — this couples the test suite to schemathesis and makes it harder to exclude specific paths. The CLI approach treats the running server as a black box, fuzzes the OpenAPI spec directly, and is simpler to configure. `--hypothesis-max-examples 30` keeps CI cost bounded; `--exclude-path` flags remove auth/webhook/health paths that schemathesis cannot exercise without credentials or valid signatures.

**Known gap:** The schemathesis CI job has no Redis service, so cache/session middleware degrades silently during fuzzing. Tracked as tech debt — fix is adding a `redis` service to the `schemathesis` job's `services:` block.

---

### 8. commitlint hook uses `commit-msg` stage, requires explicit pre-commit install step

**Decision:** `conventional-pre-commit` runs at `stages: [commit-msg]` in `.pre-commit-config.yaml`. Activation requires `pre-commit install --hook-type commit-msg` in addition to the default `pre-commit install`.

**Rationale:** Commit message hooks run at a different git lifecycle stage than pre-commit hooks. The two-step install is a pre-commit limitation, not a design choice. The config file documents this with a comment, but `DEV_SETUP.md` should explicitly include the `--hook-type commit-msg` step to ensure developers activate it.

## Risks / Trade-offs

- **Redis env var gap in Docker Compose (BREAK-2, now fixed):** CACHE_REDIS_URL and SESSION_REDIS_URL were missing from service environment blocks at initial verification. Fixed in quick task 1 (commit d7f5918). Future env var additions to settings must be mirrored in Compose files.

- **Stale test URL after endpoint refactor (BREAK-1, now fixed):** test_middleware.py used `/api/v1/health` which was removed by Phase 15. Fixed in quick task 1 (commit 5f9c12c). Pattern to avoid: tests that hit endpoint URLs are fragile across phases that refactor routing.

- **schemathesis Redis service gap (BREAK-3, deferred):** schemathesis CI job lacks a Redis service. Cache/session middleware fails silently. Low severity because auth paths are excluded and `RATELIMIT_FAIL_OPEN=True`, but should be fixed before v1.3 ships.

- **Mobile PostHog host hardcoded:** `apps/mobile/app/_layout.tsx` hardcodes `eu.i.posthog.com`. US-region PostHog projects cannot redirect without a code change. Fix: read `EXPO_PUBLIC_POSTHOG_HOST` env var with eu.i.posthog.com as default.

- **Nyquist validation incomplete:** All 6 v1.2 phase VALIDATION.md files have `nyquist_compliant: false`. Phases 15 and 18 are missing VALIDATION.md entirely. This is documentation debt, not a functional gap — all phases passed VERIFICATION.

## Open Questions

- Should the schemathesis Redis service gap be fixed as a quick task before v1.3 planning, or deferred to v1.3?
- Should `DEV_SETUP.md` include `pre-commit install --hook-type commit-msg` as an explicit step, or should a `Makefile` target handle both `pre-commit install` invocations at once?
- Should the mobile PostHog host be made configurable via `EXPO_PUBLIC_POSTHOG_HOST` env var in this sync, or deferred to v1.3 cleanup?
