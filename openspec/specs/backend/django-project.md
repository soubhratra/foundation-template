# Django Project Structure and Configuration

> Baseline specification for the Foundation Template.
> This document is the source of truth. All implementations must conform to these specs.

## Overview

The Django backend lives at `apps/api/` within the Turborepo monorepo. It uses Django Ninja Extra as the API framework, Django Allauth for authentication, and follows a layered architecture with split settings, a custom user model, and app-level separation of concerns. The project is configured for both local development (via Docker Compose + `runserver`) and production deployment (via Gunicorn).

## Specifications

### 1. Project Layout

The Django project uses a `config/` directory for project-level configuration (settings, URLs, WSGI/ASGI) and an `apps/` directory for Django applications. This separates project wiring from business logic.

```
apps/api/
  manage.py
  pyproject.toml                # Python dependencies managed by uv
  uv.lock                      # Lockfile for reproducible installs
  Dockerfile                   # Multi-stage: dev + prod targets
  config/
    __init__.py
    settings/
      __init__.py               # Imports based on DJANGO_SETTINGS_MODULE
      base.py                   # Shared settings (all environments)
      development.py            # Local dev overrides (DEBUG=True, console email)
      production.py             # Production overrides (DEBUG=False, SMTP email)
    urls.py                     # Root URL configuration
    wsgi.py                     # WSGI entry point (Gunicorn)
    asgi.py                     # ASGI entry point (future use)
    celery.py                   # Celery application instance
  apps/
    __init__.py
    accounts/                   # Custom user model, auth endpoints
      __init__.py
      models.py
      schemas.py                # Pydantic Input/Output schemas
      controllers.py            # Django Ninja Extra controllers
      services.py               # Business logic layer
      admin.py
      apps.py
      migrations/
      tests/
        __init__.py
        test_models.py
        test_services.py
        test_controllers.py
    core/                       # Shared utilities, base models, health check
      __init__.py
      models.py                 # Abstract base models (TimeStampedModel)
      schemas.py                # Shared error/pagination schemas
      controllers.py            # Health check controller
      services.py
      exceptions.py             # Custom exception classes
      middleware.py
      apps.py
      tests/
    ai/                         # LangGraph module (removable)
      __init__.py
      models.py                 # Embedding models with VectorField
      schemas.py
      controllers.py
      services.py
      graphs/                   # LangGraph graph definitions
      tasks.py                  # Celery tasks (embedding generation)
      apps.py
      migrations/
      tests/
  tests/                        # Project-level integration tests
    conftest.py
```

### 2. Settings Configuration

#### 2.1 Base Settings (`config/settings/base.py`)

The base settings file contains all configuration shared across environments. Environment-specific values are loaded from environment variables via `django-environ`.

```python
import environ
from pathlib import Path

env = environ.Env()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Read .env file if it exists (not required in Docker where env vars are injected)
environ.Env.read_env(BASE_DIR / ".env", overrides=False)

SECRET_KEY = env("SECRET_KEY")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    # Third-party
    "ninja_extra",
    "allauth",
    "allauth.account",
    "allauth.headless",
    "allauth.socialaccount",        # Required even without social providers
    "corsheaders",
    # Local apps
    "apps.accounts",
    "apps.core",
    "apps.ai",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# Database — psycopg3 via DATABASE_URL
DATABASES = {
    "default": env.db("DATABASE_URL"),
}
DATABASES["default"]["ENGINE"] = "django.db.backends.postgresql"

# Custom user model — MUST be set before first migration
AUTH_USER_MODEL = "accounts.User"

# Django Allauth configuration
SITE_ID = 1
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
HEADLESS_ONLY = True

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

# CORS — django-cors-headers
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[
    "http://localhost:3000",
])
CORS_ALLOW_CREDENTIALS = True

# CSRF trusted origins
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[
    "http://localhost:3000",
])

# Static files — whitenoise
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Celery
CELERY_BROKER_URL = env("REDIS_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env("REDIS_URL", default="redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
```

#### 2.2 Development Settings (`config/settings/development.py`)

```python
from .base import *  # noqa: F401, F403

DEBUG = True

# Console email backend — prints emails to terminal
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Relaxed CORS for local development
CORS_ALLOW_ALL_ORIGINS = True

# Django Debug Toolbar (optional, install separately)
# INSTALLED_APPS += ["debug_toolbar"]
# MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
# INTERNAL_IPS = ["127.0.0.1"]
```

#### 2.3 Production Settings (`config/settings/production.py`)

```python
from .base import *  # noqa: F401, F403

DEBUG = False

# SMTP email backend
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@example.com")

# Security settings
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# CORS must be explicit in production
CORS_ALLOW_ALL_ORIGINS = False
```

#### 2.4 Settings Selection

The active settings module is selected via the `DJANGO_SETTINGS_MODULE` environment variable:

| Environment | Value |
|-------------|-------|
| Local development | `config.settings.development` |
| Production | `config.settings.production` |
| Testing (pytest) | `config.settings.development` (overridden in `conftest.py` if needed) |

### 3. Django App Structure

Each app within `apps/` follows a consistent layered pattern:

| File | Responsibility |
|------|---------------|
| `models.py` | Django ORM models. Database schema definition. |
| `schemas.py` | Pydantic Input/Output schemas for Django Ninja Extra. Request validation and response serialization. |
| `controllers.py` | Django Ninja Extra controllers. HTTP endpoint definitions. Thin layer: validates input, checks permissions, delegates to services. |
| `services.py` | Business logic. Pure Python classes. No HTTP concerns. Testable independently. |
| `admin.py` | Django admin registration. |
| `apps.py` | Django app configuration (`AppConfig`). |
| `tests/` | Test directory with files per layer (`test_models.py`, `test_services.py`, `test_controllers.py`). |

### 4. Custom User Model (`apps/accounts/models.py`)

The custom user model uses email as the primary identifier (no username field). It MUST be created before the first migration.

```python
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.email
```

### 5. URL Configuration (`config/urls.py`)

```python
from django.contrib import admin
from django.urls import path
from ninja_extra import NinjaExtraAPI

api = NinjaExtraAPI(
    title="Foundation API",
    version="1.0.0",
    description="Foundation Template API",
)

# Auto-discover controllers from installed apps
api.auto_discover_controllers()

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
]
```

The `NinjaExtraAPI` instance at `/api/` serves as the single API entry point. It auto-discovers all `@api_controller` decorated classes from installed apps. The OpenAPI schema is available at `/api/openapi.json` by default.

### 6. WSGI and ASGI Configuration

**`config/wsgi.py`:**
```python
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")
application = get_wsgi_application()
```

**`config/asgi.py`:**
```python
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")
application = get_asgi_application()
```

### 7. Celery Configuration (`config/celery.py`)

```python
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("foundation")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
```

The Celery app is loaded in `config/__init__.py`:

```python
from .celery import app as celery_app

__all__ = ["celery_app"]
```

### 8. Management Commands

#### `export_openapi_schema`

A custom management command exports the OpenAPI JSON spec for consumption by the TypeScript type generation pipeline.

```python
# apps/core/management/commands/export_openapi_schema.py
import json
from django.core.management.base import BaseCommand
from config.urls import api


class Command(BaseCommand):
    help = "Export the OpenAPI schema to stdout as JSON"

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            type=str,
            help="Output file path (default: stdout)",
        )

    def handle(self, *args, **options):
        schema = api.get_openapi_schema()
        output = json.dumps(schema, indent=2)

        if options["output"]:
            with open(options["output"], "w") as f:
                f.write(output)
            self.stdout.write(f"Schema written to {options['output']}")
        else:
            self.stdout.write(output)
```

### 9. Base Abstract Models (`apps/core/models.py`)

```python
import uuid
from django.db import models


class TimeStampedModel(models.Model):
    """Abstract base model with created/updated timestamps."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDModel(TimeStampedModel):
    """Abstract base model with UUID primary key and timestamps."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True
```

### 10. Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | Yes | None | Django secret key. Must be unique per project. |
| `DJANGO_SETTINGS_MODULE` | Yes | None | Settings module path. |
| `DATABASE_URL` | Yes | None | PostgreSQL connection string. Format: `postgres://user:pass@host:port/db` |
| `ALLOWED_HOSTS` | No | `localhost,127.0.0.1` | Comma-separated list of allowed hosts. |
| `CORS_ALLOWED_ORIGINS` | No | `http://localhost:3000` | Comma-separated list of CORS origins. |
| `CSRF_TRUSTED_ORIGINS` | No | `http://localhost:3000` | Comma-separated list of CSRF trusted origins. |
| `REDIS_URL` | No | `redis://localhost:6379/0` | Redis connection string for Celery broker. |
| `DEBUG` | No | `False` | Debug mode. Controlled by settings module, not env var. |
| `EMAIL_HOST` | Prod only | None | SMTP server host. |
| `EMAIL_PORT` | Prod only | `587` | SMTP server port. |
| `EMAIL_HOST_USER` | Prod only | None | SMTP username. |
| `EMAIL_HOST_PASSWORD` | Prod only | None | SMTP password. |

### 11. Docker Configuration

The Dockerfile uses multi-stage builds with `dev` and `prod` targets:

```dockerfile
FROM python:3.12-slim AS base
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen
COPY . .

FROM base AS dev
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

FROM base AS prod
RUN python manage.py collectstatic --noinput
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
```

### 12. Testing Configuration (`conftest.py`)

```python
import pytest

@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass
```

**`pyproject.toml` pytest section:**
```toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings.development"
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "--tb=short -q"
```

## Scenarios

### GIVEN a fresh clone of the template repository
### WHEN `uv sync` is run in `apps/api/`
### THEN all Python dependencies install successfully from the lockfile

---

### GIVEN the Docker Compose services are running (db healthy)
### WHEN `python manage.py migrate` is run
### THEN all migrations apply without error, including the custom User model migration as `0001`

---

### GIVEN `DJANGO_SETTINGS_MODULE=config.settings.development`
### WHEN the Django dev server starts
### THEN `DEBUG` is `True`, email backend is console, and CORS allows all origins

---

### GIVEN `DJANGO_SETTINGS_MODULE=config.settings.production`
### WHEN the Django application starts via Gunicorn
### THEN `DEBUG` is `False`, CORS is restricted to explicit origins, SSL redirect is enabled, and email uses SMTP

---

### GIVEN the API server is running
### WHEN a GET request is made to `/api/openapi.json`
### THEN a valid OpenAPI 3.x schema is returned containing all registered controllers

---

### GIVEN the custom user model is configured
### WHEN `AUTH_USER_MODEL` is inspected
### THEN it points to `accounts.User` which uses email as `USERNAME_FIELD` with no username field

---

### GIVEN a developer runs `python manage.py export_openapi_schema --output openapi.json`
### WHEN the command completes
### THEN the file `openapi.json` contains the full API schema matching the runtime `/api/openapi.json` output

## Constraints

- The custom user model (`accounts.User`) MUST be created before the first `migrate` command. Changing `AUTH_USER_MODEL` after initial migration requires database recreation.
- `DJANGO_SETTINGS_MODULE` MUST be set in every environment. There is no fallback "default" settings module.
- `SECRET_KEY` MUST be unique per project instance. The template ships with a placeholder that the CLI scaffolder replaces.
- `psycopg` (psycopg3) is the required PostgreSQL adapter. Do NOT use `psycopg2` or `psycopg2-binary`.
- The `config/` directory contains ONLY project-level wiring. No business logic, no models, no schemas.
- Each app in `apps/` MUST have its own `tests/` directory. No top-level `tests/` as the sole test location.
- WhiteNoise handles static files in all environments. Do NOT configure Nginx or S3 for static files in the base template.
- `django-environ` is the sole mechanism for reading environment variables. Do NOT use `os.environ` directly or `python-dotenv`.

## References

- `.planning/research/STACK.md` -- Supporting stack decisions (psycopg3, django-environ, whitenoise, ruff, uv)
- `.planning/research/ARCHITECTURE.md` -- Monorepo structure, layered app pattern, settings split rationale
- `.planning/research/PITFALLS.md` -- Pitfall #4 (monolithic settings), Pitfall #2 (auth misconfiguration), custom user model warning
- `.planning/PROJECT.md` -- Core requirements, constraints, out-of-scope items
