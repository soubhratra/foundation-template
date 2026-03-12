# Phase 13: Structured Logging + Distributed Tracing - Context

**Gathered:** 2026-03-11
**Status:** Ready for planning

<domain>
## Phase Boundary

Wire structured JSON logging via `structlog` with auto-injected request context on every Django request, and OpenTelemetry auto-instrumentation across Django + Celery + PostgreSQL with OTLP export to Jaeger running in Docker Compose. No user-facing UI. Backend infrastructure only.

Requirements: OBS-01, OBS-02.

</domain>

<decisions>
## Implementation Decisions

### Log format (dev vs prod)

- Development (`DEBUG=True`): structlog `ConsoleRenderer` — colorized, human-readable key=value output
- Production (`DEBUG=False`): structlog `JSONRenderer` — valid JSON per line
- Switch is automatic via `DEBUG` setting — no extra env var needed

### Log routing (unified pipeline)

- ALL log output routed through structlog — Django internals (`django.request`, `django.security`, etc.) + app code + Celery
- Configure Django's `LOGGING` dict to use structlog's stdlib handler so nothing bypasses the pipeline
- Celery: `task_prerun` / `task_postrun` signals bind `task_id` and `task_name` into structlog context automatically

### Log/trace correlation

- A custom structlog processor reads the active OpenTelemetry context and injects `trace_id` + `span_id` into every log event when a trace is active
- Format: 32-char hex string matching OTel/Jaeger convention (paste directly into Jaeger search)
- When no trace is active (e.g., management commands, tests), `trace_id` / `span_id` fields are omitted — not null
- Processor lives in `apps/core/logging.py` as a standalone, importable, testable function

### Request context injection

- New Django middleware in `apps/core/middleware.py` (file does not exist yet — must be created)
- Injected fields per request: `request_id` (UUID4), `user_id` (auth user PK or `"anonymous"`), `method`, `path`, `status_code`, `duration_ms`
- No raw client IP — avoids GDPR friction; per-project opt-in if needed
- `X-Request-ID` echoed as a response header so API clients can include it in bug reports
- `request_id` is always generated fresh by middleware (not from incoming headers)

### Trace context propagation to Celery

- OTel's Celery auto-instrumentation propagates parent trace context via task headers
- A Celery task dispatched from a traced Django view continues the same trace
- Task logs include the same `trace_id` as the originating Django request — full end-to-end trace per OBS-02

### Jaeger in Docker Compose

- Image: `jaegertracing/all-in-one` — single container, zero configuration
- Ports: `4317` (OTLP gRPC ingest), `16686` (Jaeger UI)
- Added to default `docker-compose.yml` — always starts with `docker compose up`, no extra flags
- Service name: `jaeger` (used in Docker Compose networking)

### OTel endpoint configuration

- Endpoint via `OTEL_EXPORTER_OTLP_ENDPOINT` env var (follows OTel SDK convention)
- Docker Compose sets `OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317` for the API service
- Tracing is a **no-op when the env var is not set** — no overhead in CI, no failed connections when Jaeger isn't running
- When env var is present, Django startup calls `configure_otel()` (helper in `apps/core/tracing.py` or similar)

### Claude's Discretion

- Exact structlog processors chain ordering (e.g., add_log_level, TimeStamper, StackInfoRenderer, format_exc_info, OtelProcessor, renderer)
- OTel service name value (can default to `DJANGO_SETTINGS_MODULE` or a `OTEL_SERVICE_NAME` env var)
- Whether to auto-instrument `psycopg2` vs `psycopg3` (depends on what's installed — detect at runtime)
- Django LOGGING dict structure details (root logger level, loggers to suppress like `django.server` in tests)
- pytest fixture to disable structlog output noise during test runs

</decisions>

<code_context>

## Existing Code Insights

### Reusable Assets

- `apps/core/`: Core Django app — good home for new `middleware.py` and `logging.py` files; currently has `controllers.py`, `exceptions.py`, `schemas.py`, `models.py`
- `apps/api/config/celery.py`: Celery app instance — OTel Celery instrumentation patches this app on startup

### Established Patterns

- Settings split: `base.py` / `development.py` / `production.py` — new logging config goes in `base.py`, with format switch based on `DEBUG`
- Middleware stack in `base.py` `MIDDLEWARE` list — new request context middleware slots in after `SessionMiddleware` (needs authenticated user to be available via `request.user`)
- `env()` pattern via `django-environ` — `OTEL_EXPORTER_OTLP_ENDPOINT` follows same `env("...", default="")` pattern
- Celery result backend is `django-db` — no change needed; OTel instruments the broker transport layer

### Integration Points

- `MIDDLEWARE` list in `base.py`: insert `apps.core.middleware.RequestContextMiddleware` after `allauth.account.middleware.AccountMiddleware` (so `request.user` is populated)
- `config/celery.py`: call `configure_otel()` after `app = Celery(...)` when `OTEL_EXPORTER_OTLP_ENDPOINT` is set
- `docker-compose.yml`: add `jaeger` service and `OTEL_EXPORTER_OTLP_ENDPOINT` env var to the `api` service

</code_context>

<specifics>
## Specific Ideas

- Inject `trace_id` as hex string so it pastes directly into Jaeger's search box without transformation
- `X-Request-ID` response header enables API clients to self-report `request_id` in bug reports — makes support easier for every scaffolded product
- More context is better for security/traceability, but no raw IP to avoid GDPR complexity out of the box

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

_Phase: 13-structured-logging-distributed-tracing_
_Context gathered: 2026-03-11_
