# Django API Backend

## ADDED Requirements

### Requirement: Django Ninja Extra REST API Framework
The backend SHALL use Django Ninja Extra for all REST API endpoints with class-based controllers, automatic OpenAPI 3.1 schema generation, and Pydantic schema validation. The framework MUST be configured with auto-discovery of controllers from installed Django apps.

#### Scenario: Controller Auto-Discovery
- **WHEN** a Django app defines an `@api_controller` decorated class in its controllers.py
- **THEN** `api.auto_discover_controllers()` in config/urls.py registers all controller routes
- **AND** the controller's endpoints are accessible under `/api/v1/<prefix>`
- **AND** the endpoints appear in the auto-generated OpenAPI schema

#### Scenario: Pydantic Input Validation
- **WHEN** a POST request is sent to a controller endpoint with a Pydantic schema as the payload parameter
- **THEN** Django Ninja Extra validates the request body against the schema
- **AND** validation failures return 422 with field-level error details
- **AND** valid payloads are passed to the controller as Pydantic model instances

### Requirement: Layered Architecture Pattern
Each Django app MUST follow a three-layer architecture: Controllers (HTTP boundary), Services (business logic), and ORM (data access). Controllers MUST NOT contain business logic or direct ORM queries.

#### Scenario: Controller Delegates to Service
- **WHEN** a controller method receives a validated request
- **THEN** it calls a service method with typed parameters (user, data, IDs)
- **AND** the service executes business logic and ORM queries
- **AND** the controller returns the service result wrapped in the response schema

#### Scenario: Service Layer Testability
- **WHEN** a service class method is unit tested
- **THEN** it can be tested without HTTP context or request objects
- **AND** it receives typed inputs and returns Django model instances or dicts
- **AND** ORM queries use Django's test database

### Requirement: Split Settings Configuration
The Django project MUST use split settings (base.py, development.py, production.py) under config/settings/. The active settings module MUST be selected via the DJANGO_SETTINGS_MODULE environment variable.

#### Scenario: Development Settings Override
- **WHEN** DJANGO_SETTINGS_MODULE is set to `config.settings.development`
- **THEN** base.py settings are loaded first
- **AND** development.py overrides (DEBUG=True, console email backend, CORS_ALLOW_ALL_ORIGINS=True) are applied
- **AND** the Django server runs in debug mode with relaxed CORS

#### Scenario: Production Settings Security
- **WHEN** DJANGO_SETTINGS_MODULE is set to `config.settings.production`
- **THEN** DEBUG is False
- **AND** SECURE_SSL_REDIRECT, SECURE_HSTS_SECONDS, and CSRF_COOKIE_SECURE are enabled
- **AND** CORS_ALLOWED_ORIGINS is read from environment variables (explicit whitelist)
- **AND** email backend uses SMTP configuration

### Requirement: Custom User Model with Email Authentication
The backend MUST define a custom User model inheriting from AbstractUser before the first migration. The model MUST use email as USERNAME_FIELD, removing the username field entirely.

#### Scenario: Custom User Model Creation
- **WHEN** `python manage.py migrate` is run for the first time
- **THEN** the accounts.User model is created in migration 0001_initial
- **AND** AUTH_USER_MODEL setting points to "accounts.User"
- **AND** all Django auth machinery uses the custom model

#### Scenario: Email-Based Authentication
- **WHEN** a user signs up or logs in
- **THEN** the email field is used as the unique identifier
- **AND** the username field does not exist in the database schema
- **AND** User.USERNAME_FIELD returns "email"

### Requirement: Health Check Endpoint
The API MUST expose a public health check endpoint at `/api/v1/health` that verifies database connectivity. The endpoint SHALL NOT require authentication and MUST return service status information.

#### Scenario: Healthy Database Connection
- **WHEN** a GET request is sent to `/api/v1/health`
- **THEN** the endpoint executes `SELECT 1` against the database
- **AND** returns 200 with `{"status": "healthy", "database": "connected"}`

#### Scenario: Database Connection Failure
- **WHEN** a GET request is sent to `/api/v1/health` while the database is unreachable
- **THEN** the endpoint catches the connection exception
- **AND** returns 200 with `{"status": "degraded", "database": "disconnected"}`
- **AND** does not raise a 500 error

### Requirement: uv Package Manager
The Django project MUST use uv as the package manager for Python dependencies. All dependencies MUST be declared in pyproject.toml with locked versions in uv.lock.

#### Scenario: Dependency Installation
- **WHEN** a developer runs `uv sync` in apps/api/
- **THEN** uv reads pyproject.toml and uv.lock
- **AND** installs all dependencies into a virtual environment
- **AND** the installation completes 10-100x faster than pip

#### Scenario: Lockfile Consistency
- **WHEN** uv.lock is committed to version control
- **THEN** all developers and CI pipelines install identical dependency versions
- **AND** `uv sync --frozen` fails if pyproject.toml changes without regenerating uv.lock
- **AND** dependency drift is prevented

### Requirement: Django Admin Interface
The API MUST enable Django Admin at `/admin/` with registration for core models (User, etc.). Admin access MUST require superuser status.

#### Scenario: Superuser Admin Access
- **WHEN** a superuser navigates to `/admin/` and logs in
- **THEN** the Django Admin dashboard displays
- **AND** registered models (User, etc.) are accessible for CRUD operations
- **AND** the admin uses the custom User model with email authentication

#### Scenario: Non-Superuser Access Denied
- **WHEN** a regular user attempts to access `/admin/`
- **THEN** they are redirected to the login page
- **AND** after login, they receive a permission denied error
- **AND** only is_staff=True users can access the admin
