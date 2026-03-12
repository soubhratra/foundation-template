## Why

Milestone v1.2 (Observability & DevEx Hardening, Phases 13–18) shipped 17 requirements across structured logging, distributed tracing, exception/analytics tracking, health probes, Redis-backed security, and dev-time quality gates. These decisions need to be captured in specs so every product scaffolded from this template inherits them without additional configuration.

## What Changes

- Introduce `observability` capability: structlog JSON logging with auto-injected request context; OpenTelemetry distributed tracing across Django + Celery + PostgreSQL with Jaeger; `ObservabilityAdapter` ABC with `PostHogAdapter` default covering Django exceptions, Celery task failures, Next.js page views, and Expo screen events; `--without observability` CLI scaffolder flag
- Introduce `health-probes` capability: plain Django views at `/api/health/live`, `/api/health/ready`, `/api/health/startup` checking DB, Redis, Celery, and pending migrations
- Extend `security`: Redis-backed auth endpoint rate limiting via `django-ratelimit`; security headers via `django-csp`, HSTS, `X-Frame-Options`, `Referrer-Policy` in Django + matching `headers()` in Next.js; Redis as default cache and session backend via `django-redis`
- Extend `devex-ci`: `detect-secrets` and `bandit` in pre-commit + CI; `nplusone` autouse pytest fixture for N+1 detection; `schemathesis` as a fourth parallel CI job for API contract fuzzing; `commitlint` commit-msg hook enforcing Conventional Commits; ruff McCabe complexity gate (`max-complexity = 10`)
- Extend `background-tasks`: dedicated `celery-beat` Docker Compose service with `django-celery-beat` DatabaseScheduler; Flower monitoring in dev Compose (not prod); example periodic task scaffold with retry + exponential backoff
- Extend `docker-infra`: Jaeger service for local OTel trace inspection; `CACHE_REDIS_URL` (DB 1) and `SESSION_REDIS_URL` (DB 2) as separate Redis databases injected into all service environments; `celery-worker` always running (not profile-gated)

## Capabilities

### New Capabilities

- `observability`: Structured logging (structlog), distributed tracing (OpenTelemetry + Jaeger), and `ObservabilityAdapter` ABC with `PostHogAdapter` default — covers Django request logs, OTel traces across Django/Celery/PostgreSQL, exception capture, product analytics, and session replay across Django, Celery, Next.js, and Expo; removable via `--without observability`
- `health-probes`: Three plain Django HTTP health endpoints (`/api/health/live`, `/api/health/ready`, `/api/health/startup`) for deployment orchestration and readiness checks

### Modified Capabilities

- `security`: Adding rate limiting (auth endpoints, Redis-backed, configurable per-endpoint), HTTP security headers (CSP with per-request nonces, HSTS in production only, X-Frame-Options, Referrer-Policy), and Redis as the default cache + session backend (replacing LocMemCache)
- `devex-ci`: Adding secret scanning (`detect-secrets` + `.secrets.baseline`), Python SAST (`bandit` at HIGH severity), N+1 detection (`nplusone` autouse fixture), API contract fuzzing (`schemathesis` CI job), conventional commit enforcement (`commitlint` commit-msg hook), and cyclomatic complexity gate (ruff C90, max=10)
- `background-tasks`: Adding dedicated `celery-beat` service with `django-celery-beat` DatabaseScheduler (replacing in-process Beat), Flower dev monitoring at port 5555, and example periodic task scaffold demonstrating retry + backoff patterns
- `docker-infra`: Adding Jaeger all-in-one service (ports 4317 OTLP gRPC + 16686 UI), `CACHE_REDIS_URL: redis://redis:6379/1` and `SESSION_REDIS_URL: redis://redis:6379/2` in all service environment blocks, `celery-worker` as always-on service (not profile-gated in v1.2 template)

## Impact

- `apps/api/`: new `apps/core/logging.py`, `apps/core/tracing.py`, `apps/core/observability.py`, `apps/core/health.py`, `apps/core/ratelimit.py`; extended `apps/core/middleware.py`, `apps/core/apps.py`; updated `config/settings/base.py`, `config/settings/development.py`, `config/settings/production.py`, `config/urls.py`, `config/celery.py`; new test files in `tests/core/`
- `apps/web/`: extended `app/providers.tsx` (PostHog page view tracking); extended `next.config.ts` (security headers)
- `apps/mobile/`: extended `app/_layout.tsx` (PostHog screen tracking)
- `packages/create-foundation-app/`: new `removeObservability()` in `src/remove.ts`; updated `src/prompts.ts` and `src/index.ts` for `--without observability` flag
- `docker-compose.yml`, `docker-compose.prod.yml`: Jaeger service, Redis DB split, celery-beat, Flower (dev only)
- `.pre-commit-config.yaml`: detect-secrets, bandit, commitlint (commit-msg stage)
- `.github/workflows/ci.yml`: bandit + pip-audit + pnpm audit steps; schemathesis fourth parallel job
- `apps/api/pyproject.toml`: structlog, opentelemetry-\*, posthog, django-ratelimit, django-csp, django-redis, django-celery-beat, flower, bandit, pip-audit, django-debug-toolbar, nplusone, schemathesis
