## ADDED Requirements

### Requirement: Liveness Probe Endpoint

The backend SHALL expose a `/api/health/live` HTTP endpoint that returns 200 when the Django process is running, without checking downstream dependencies.

#### Scenario: Liveness probe returns 200

- **WHEN** a GET request is made to `/api/health/live`
- **THEN** the response MUST be HTTP 200 with JSON body `{"status": "ok"}`
- **AND** no database, Redis, or Celery checks MUST be performed
- **AND** the endpoint MUST respond within 100ms under normal conditions

#### Scenario: Liveness probe accessible without authentication

- **WHEN** an unauthenticated request is made to `/api/health/live`
- **THEN** the response MUST be HTTP 200 (no auth required)
- **AND** the endpoint MUST NOT set session cookies or CSRF tokens

### Requirement: Readiness Probe Endpoint

The backend SHALL expose a `/api/health/ready` HTTP endpoint that returns 200 only when all critical dependencies (database and Redis) are accessible.

#### Scenario: Readiness probe succeeds when all dependencies healthy

- **WHEN** a GET request is made to `/api/health/ready` and database and Redis are reachable
- **THEN** the response MUST be HTTP 200 with JSON body `{"status": "ok", "checks": {"db": "ok", "redis": "ok"}}`

#### Scenario: Readiness probe fails when database is unreachable

- **WHEN** a GET request is made to `/api/health/ready` and the database cannot be reached
- **THEN** the response MUST be HTTP 503
- **AND** the JSON body MUST include `{"status": "error", "checks": {"db": "error", "redis": "ok"}}` (or the specific failing dependency)

#### Scenario: Readiness probe fails when Redis is unreachable

- **WHEN** a GET request is made to `/api/health/ready` and Redis cannot be reached
- **THEN** the response MUST be HTTP 503
- **AND** the JSON body MUST include `{"status": "error", "checks": {"db": "ok", "redis": "error"}}`

#### Scenario: Readiness probe accessible without authentication

- **WHEN** an unauthenticated request is made to `/api/health/ready`
- **THEN** authentication MUST NOT be required
- **AND** the endpoint MUST NOT be rate-limited

### Requirement: Startup Probe Endpoint

The backend SHALL expose a `/api/health/startup` HTTP endpoint that returns 200 only when the application has completed startup, including verifying no pending database migrations exist.

#### Scenario: Startup probe succeeds when no pending migrations

- **WHEN** a GET request is made to `/api/health/startup` and all migrations have been applied
- **THEN** the response MUST be HTTP 200 with JSON body `{"status": "ok", "checks": {"db": "ok", "migrations": "ok"}}`

#### Scenario: Startup probe fails when pending migrations exist

- **WHEN** a GET request is made to `/api/health/startup` and unapplied migrations are detected
- **THEN** the response MUST be HTTP 503
- **AND** the JSON body MUST include `{"status": "error", "checks": {"migrations": "pending"}}`
- **AND** the deployment orchestrator MUST hold traffic until this probe returns 200

#### Scenario: Health endpoints use plain Django views

- **WHEN** the health endpoints are implemented
- **THEN** they MUST be implemented as plain Django views in `apps/core/health.py`, NOT as Django Ninja endpoints
- **AND** the views MUST be registered in `config/urls.py` under the `/api/health/` prefix
- **AND** the views MUST be exempt from Django's CSRF middleware
