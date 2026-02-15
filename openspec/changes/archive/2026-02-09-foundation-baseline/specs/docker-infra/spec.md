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
The Docker infrastructure SHALL provide Redis 7 (alpine variant) for Celery task queue brokering and optional caching. Redis MUST include a health check and be accessible to host applications.

#### Scenario: Celery Worker Connection
- **WHEN** a Celery worker starts on the host with `REDIS_URL=redis://localhost:6379/0`
- **THEN** the worker connects to the Redis container
- **AND** tasks enqueued by Django are picked up by the worker
- **AND** task results are stored back in Redis

#### Scenario: Redis Health Check
- **WHEN** the Redis container is starting
- **THEN** the health check runs `redis-cli ping` every 5 seconds
- **AND** the container reports healthy once PONG is received
- **AND** dependent services can wait for healthy status

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
