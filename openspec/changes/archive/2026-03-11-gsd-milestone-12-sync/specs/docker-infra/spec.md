## MODIFIED Requirements

### Requirement: Redis for Celery and Caching

The Docker infrastructure SHALL provide Redis 7 (alpine variant) with three logically separated databases: DB 0 for Celery broker/results, DB 1 for Django cache, and DB 2 for Django sessions. All service environment blocks MUST inject both `CACHE_REDIS_URL` and `SESSION_REDIS_URL` alongside `REDIS_URL`.

#### Scenario: Redis DB separation enforced by URL convention

- **WHEN** Docker Compose is started
- **THEN** every service that uses Redis MUST receive three distinct env vars:
  - `REDIS_URL=redis://redis:6379/0` (Celery broker and results)
  - `CACHE_REDIS_URL=redis://redis:6379/1` (Django cache)
  - `SESSION_REDIS_URL=redis://redis:6379/2` (Django sessions)
- **AND** these env vars MUST be injected into the `api`, `celery-worker`, and `celery-beat` service environments

#### Scenario: Redis Health Check

- **WHEN** the Redis container is starting
- **THEN** the health check MUST run `redis-cli ping` every 5 seconds
- **AND** the container MUST report healthy once PONG is received
- **AND** dependent services MUST wait for the healthy status before starting

## ADDED Requirements

### Requirement: Jaeger All-In-One for Local Trace Inspection

The Docker infrastructure SHALL provide a Jaeger all-in-one service for collecting and visualizing OpenTelemetry traces in local development.

#### Scenario: Jaeger service defined in Docker Compose

- **WHEN** Docker Compose is started
- **THEN** a `jaeger` service using `jaegertracing/all-in-one:latest` MUST be present
- **AND** port `4317` MUST be exposed for OTLP gRPC ingestion by instrumented services
- **AND** port `16686` MUST be exposed for the Jaeger web UI accessible at `http://localhost:16686`

#### Scenario: Django traces visible in Jaeger UI

- **WHEN** the Django API handles an HTTP request with OTel tracing enabled
- **THEN** the trace MUST appear in the Jaeger UI at `http://localhost:16686` within seconds
- **AND** the service name MUST match `OTEL_SERVICE_NAME` configured in the API service environment
- **AND** individual database query spans MUST be visible as children of the request span

#### Scenario: Jaeger excluded from production Compose

- **WHEN** `docker-compose.prod.yml` is used
- **THEN** the `jaeger` service MUST NOT be present
- **AND** production OTel traces MUST be directed to an external OTLP endpoint via `OTEL_EXPORTER_OTLP_ENDPOINT`

### Requirement: Celery Beat and Flower in Docker Compose

The Docker infrastructure SHALL define `celery-beat` and `flower` services in `docker-compose.yml`, with Flower excluded from `docker-compose.prod.yml`.

#### Scenario: celery-beat service always starts in development

- **WHEN** Docker Compose is started from the repository root
- **THEN** the `celery-beat` service MUST start without requiring profile flags
- **AND** it MUST depend on `db` and `redis` reaching healthy status before starting

#### Scenario: flower service starts in development at port 5555

- **WHEN** Docker Compose is started in development
- **THEN** the `flower` service MUST start and bind to port `5555`
- **AND** `http://localhost:5555` MUST serve the Flower task monitoring dashboard
- **AND** Flower MUST connect to the Redis instance using `REDIS_URL`
