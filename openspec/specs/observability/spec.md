## Requirements

### Requirement: Structured JSON Logging with structlog

The backend SHALL use structlog for all application logging, producing JSON-formatted log lines with auto-injected request context in production.

#### Scenario: structlog configured for production

- **WHEN** Django runs in production mode
- **THEN** all log output MUST be structured JSON
- **AND** each log line MUST include `timestamp`, `level`, `logger`, and `message` fields
- **AND** `request_id`, `user_id`, and `method`/`path` MUST be automatically injected for request-scoped logs

#### Scenario: structlog configured for development

- **WHEN** Django runs in development mode
- **THEN** log output SHOULD use the ConsoleRenderer for human-readable output
- **AND** all structlog context fields MUST still be populated

#### Scenario: Request context injected via middleware

- **WHEN** a request enters the Django middleware stack
- **THEN** `RequestContextMiddleware` in `apps/core/middleware.py` MUST bind a `request_id` (UUID), `method`, and `path` to the structlog context
- **AND** the context MUST be cleared at the end of each request
- **AND** all log calls made within the request lifecycle MUST include these fields automatically

### Requirement: OpenTelemetry Distributed Tracing

The backend SHALL instrument Django, Celery, and PostgreSQL with OpenTelemetry, exporting traces to a configured OTLP endpoint (default: Jaeger in development).

#### Scenario: OTel SDK initialized at app startup

- **WHEN** the Django application starts (`apps/core/apps.py` `ready()`)
- **THEN** `apps/core/tracing.py` MUST configure `OTLPSpanExporter` pointed at `OTEL_EXPORTER_OTLP_ENDPOINT`
- **AND** `DjangoInstrumentor`, `PsycopgInstrumentor`, and `CeleryInstrumentor` MUST be applied
- **AND** the service name MUST be read from `OTEL_SERVICE_NAME` env var

#### Scenario: HTTP request traced end-to-end

- **WHEN** an HTTP request is handled by Django
- **THEN** the OTel Django instrumentor MUST create a span for the request lifecycle
- **AND** the span MUST include `http.method`, `http.url`, `http.status_code` attributes
- **AND** the trace context MUST propagate to downstream Celery tasks via task headers

#### Scenario: Database queries traced

- **WHEN** Django ORM executes a SQL query during a traced request
- **THEN** the Psycopg instrumentor MUST create a child span for the query
- **AND** the span MUST include `db.system`, `db.statement` (sanitized — no bind values), and `db.operation` attributes

#### Scenario: Tracing disabled when endpoint not configured

- **WHEN** `OTEL_EXPORTER_OTLP_ENDPOINT` is not set
- **THEN** tracing MUST be a no-op (NullSpanExporter or SDK not initialized)
- **AND** the application MUST start and function normally without any tracing overhead

### Requirement: ObservabilityAdapter ABC for Product Analytics and Exception Tracking

The system SHALL define an `ObservabilityAdapter` abstract base class in `apps/core/observability.py` with a `PostHogAdapter` default implementation covering exception capture, task failure tracking, and frontend event collection.

#### Scenario: ObservabilityAdapter interface enforced

- **WHEN** a developer implements a custom adapter
- **THEN** they MUST subclass `ObservabilityAdapter`
- **AND** MUST implement `capture_exception(exc, context)`, `capture_event(name, properties)`, and `identify_user(user_id, properties)` methods
- **AND** failure to implement any method MUST raise `NotImplementedError`

#### Scenario: PostHogAdapter captures Django exceptions

- **WHEN** an unhandled exception propagates through `apps/core/middleware.py`
- **THEN** `PostHogAdapter.capture_exception()` MUST be called with the exception and request context
- **AND** the event MUST be sent to PostHog as `"$exception"` with `distinct_id` set to user ID or anonymous ID
- **AND** if `POSTHOG_API_KEY` is not set, the call MUST be a no-op

#### Scenario: PostHogAdapter captures Celery task failures

- **WHEN** a Celery task raises an unhandled exception after all retries
- **THEN** the Celery task failure signal MUST call `PostHogAdapter.capture_exception()`
- **AND** the event MUST include `task_name`, `task_id`, and `args` in properties

#### Scenario: Next.js page views tracked

- **WHEN** a user navigates to a new page in the Next.js app
- **THEN** the `PostHogProvider` in `app/providers.tsx` MUST call `posthog.capture("$pageview")` with the current URL
- **AND** the PostHog distinct ID MUST be the authenticated user ID when available, otherwise the anonymous ID
- **AND** tracking MUST NOT fire if `NEXT_PUBLIC_POSTHOG_KEY` is not set

#### Scenario: Expo screen views tracked

- **WHEN** a user navigates to a new screen in the Expo app
- **THEN** the root Expo Router layout MUST call `posthog.screen(routeName)` on route focus events
- **AND** tracking MUST NOT fire if `EXPO_PUBLIC_POSTHOG_KEY` is not set

### Requirement: Observability Opt-Out via CLI Scaffolder Flag

The CLI scaffolder SHALL support a `--without observability` flag that removes all observability infrastructure from scaffolded projects.

#### Scenario: Project scaffolded without observability

- **WHEN** the CLI scaffolder is run with `--without observability`
- **THEN** `apps/core/logging.py`, `apps/core/tracing.py`, and `apps/core/observability.py` MUST NOT be generated
- **AND** `INSTALLED_APPS` MUST NOT include any OTel or PostHog configuration
- **AND** `settings/base.py` MUST NOT include `STRUCTLOG_*` or `OTEL_*` settings
- **AND** `PostHogProvider` MUST NOT be added to `app/providers.tsx`

#### Scenario: Observability packages excluded from pyproject.toml

- **WHEN** a project is scaffolded with `--without observability`
- **THEN** `structlog`, `opentelemetry-sdk`, `opentelemetry-instrumentation-*`, and `posthog` MUST be absent from `pyproject.toml`
- **AND** `pnpm` workspace packages MUST NOT install `posthog-js`
