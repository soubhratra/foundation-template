# Docker Infrastructure

## ADDED Requirements

### Requirement: Hybrid Development Model

The default development environment SHALL run infrastructure services (Postgres, Redis) in Docker containers while applications (Django, Next.js, Expo) run on the host. This MUST be the documented and recommended development workflow.

#### Scenario: Infrastructure-Only Docker Compose

- **WHEN** a developer runs `docker compose up` from the repository root
- **THEN** only Postgres 16 with PGVector and Redis 7 containers start
- **AND** services expose ports to the host (5432, 6379)
- **AND** applications on the host connect via localhost

#### Scenario: Host-Based Application Development

- **WHEN** applications run on the host with infrastructure in Docker
- **THEN** file watching and hot reload work natively without Docker volume latency
- **AND** IDE autocomplete resolves node_modules and Python packages instantly
- **AND** Expo dev server can connect to physical devices via USB/network

### Requirement: PostgreSQL with PGVector Extension

The Docker infrastructure SHALL provide PostgreSQL 16+ with the PGVector extension pre-installed using the `pgvector/pgvector:pg16` image. The database MUST be configured with persistent volume mounts and health checks.

#### Scenario: PGVector Extension Availability

- **WHEN** Django runs the initial migration to enable PGVector (`CREATE EXTENSION IF NOT EXISTS vector`)
- **THEN** the extension is available in the database
- **AND** VectorField columns can be created
- **AND** HNSW indexes can be built with vector_cosine_ops operator class

#### Scenario: Database Persistence Across Restarts

- **WHEN** `docker compose down` is run without the `-v` flag
- **THEN** the postgres_data volume persists
- **AND** `docker compose up` restores the database with all data intact
- **AND** migrations do not need to be re-run

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

### Requirement: Service Health Checks

All infrastructure services in Docker Compose MUST define health checks that validate service readiness. Health checks MUST use appropriate intervals (5s) and retries (5) for local development.

#### Scenario: Postgres Health Check

- **WHEN** the Postgres container is starting
- **THEN** the health check runs `pg_isready -U foundation` every 5 seconds
- **AND** the container reports healthy after 5 successful checks
- **AND** Django can safely run migrations once the container is healthy

#### Scenario: Startup Order with Health Checks

- **WHEN** a full-stack docker-compose.full.yml is used (future extension)
- **THEN** services can use `depends_on` with `condition: service_healthy`
- **AND** dependent services wait for infrastructure health before starting

### Requirement: Environment Variable Configuration

Each service MUST have a committed `.env.example` file documenting all required environment variables. The actual `.env` files MUST be gitignored and created by developers from the examples.

#### Scenario: First-Time Setup from Example

- **WHEN** a new developer clones the repository
- **THEN** they copy `.env.example` to `.env` in the repository root
- **AND** copy `apps/api/.env.example` to `apps/api/.env`
- **AND** copy `apps/web/.env.example` to `apps/web/.env.local`
- **AND** all services start successfully with default example values

#### Scenario: Docker Compose Environment Injection

- **WHEN** docker-compose.yml references `${POSTGRES_PASSWORD}` from the environment
- **THEN** Docker Compose reads the value from the root `.env` file
- **AND** the value is passed to the Postgres container's environment
- **AND** secrets never appear in committed files

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

#### Scenario: Flower excluded from production Compose

- **WHEN** `docker-compose.prod.yml` is used
- **THEN** the `flower` service MUST NOT be present
- **AND** no Flower packages or ports MUST be exposed in production

### Requirement: Volume Mount Strategy

Infrastructure services MUST use named volumes for persistent data (postgres_data, redis_data) rather than bind mounts. Application services in full Docker mode (optional) MUST use bind mounts for live code updates.

#### Scenario: Named Volume for Database Persistence

- **WHEN** the Postgres service defines `volumes: [postgres_data:/var/lib/postgresql/data]`
- **THEN** Docker creates a named volume managed by Docker Desktop
- **AND** data persists across container recreations
- **AND** `docker volume ls` shows the volume
- **AND** `docker volume rm <volume>` can reset the database

#### Scenario: Bind Mount for Development Code

- **WHEN** docker-compose.full.yml adds Django with `volumes: [./apps/api:/app]`
- **THEN** code changes on the host are immediately visible in the container
- **AND** Django's auto-reloader detects changes and restarts the server
- **AND** no manual container restart is required
