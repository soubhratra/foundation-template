import os
from contextlib import suppress
from pathlib import Path

import environ  # type: ignore[import-untyped]
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent.parent
env = environ.Env()

with suppress(FileNotFoundError):
    environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY", default="django-insecure-change-me-in-production")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# --------------------------------------------------------------------------
# Observability: Structured Logging (structlog) — Phase 13
# --------------------------------------------------------------------------
import structlog as _structlog  # noqa: E402

_log_renderer = "plain_console" if DEBUG else "json_formatter"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json_formatter": {
            "()": _structlog.stdlib.ProcessorFormatter,
            "processor": _structlog.processors.JSONRenderer(),
            "foreign_pre_chain": [
                _structlog.contextvars.merge_contextvars,
                _structlog.processors.TimeStamper(fmt="iso"),
                _structlog.stdlib.add_logger_name,
                _structlog.stdlib.add_log_level,
                _structlog.stdlib.PositionalArgumentsFormatter(),
            ],
        },
        "plain_console": {
            "()": _structlog.stdlib.ProcessorFormatter,
            "processor": _structlog.dev.ConsoleRenderer(),
            "foreign_pre_chain": [
                _structlog.contextvars.merge_contextvars,
                _structlog.processors.TimeStamper(fmt="iso"),
                _structlog.stdlib.add_logger_name,
                _structlog.stdlib.add_log_level,
                _structlog.stdlib.PositionalArgumentsFormatter(),
            ],
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": _log_renderer,
        },
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "django_structlog": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
        "celery": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

# Enable django-structlog Celery signal handlers for task context propagation.
DJANGO_STRUCTLOG_CELERY_ENABLED = True

# OTel OTLP endpoint — set to http://jaeger:4317 in docker-compose.yml (Phase 13-03).
# Tracing is a no-op when empty — no overhead in CI, no failed connections when Jaeger is absent.
OTEL_EXPORTER_OTLP_ENDPOINT = env("OTEL_EXPORTER_OTLP_ENDPOINT", default="")

# ---------------------------------------------------------------------------
# OBSERVABILITY MODULE
# ---------------------------------------------------------------------------
POSTHOG_API_KEY: str = env("POSTHOG_API_KEY", default="")
POSTHOG_HOST: str = env("POSTHOG_HOST", default="https://eu.i.posthog.com")
OBSERVABILITY_ADAPTER: str = env(
    "OBSERVABILITY_ADAPTER",
    default="apps.core.observability.NoOpAdapter",
)
# ---------------------------------------------------------------------------
# END OBSERVABILITY MODULE
# ---------------------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "ninja_extra",
    "corsheaders",
    "django_celery_results",
    "django_structlog",
    "allauth",
    "allauth.account",
    "allauth.headless",
    "allauth.socialaccount",
    "apps.accounts",
    "apps.core",
    "apps.ai",
    "apps.billing",  # BILLING MODULE — remove this line to exclude billing
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "apps.core.middleware.RequestContextMiddleware",
    "apps.core.middleware.ObservabilityMiddleware",  # OBSERVABILITY MODULE
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

AUTH_USER_MODEL = "accounts.User"

SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default="postgres://foundation:foundation@localhost:5432/foundation",
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")

FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:3000")

# --------------------------------------------------------------------------
# Celery Configuration
# --------------------------------------------------------------------------
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = "django-db"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes

# --------------------------------------------------------------------------
# OpenAI Configuration
# --------------------------------------------------------------------------
OPENAI_API_KEY = env("OPENAI_API_KEY", default="")

CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=[
        "http://localhost:3000",
        "http://localhost:19006",
    ],
)
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    "accept",
    "authorization",
    "content-type",
    "origin",
    "x-csrftoken",
    "x-requested-with",
    "x-api-version",
]

CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=[
        "http://localhost:3000",
        "http://localhost:19006",
    ],
)
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

PASSWORD_RESET_TIMEOUT = 60 * 60 * 24

ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_LOGIN_METHODS = ["email"]
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_SIGNUP_FORM_CLASS = "apps.accounts.headless.HeadlessSignupForm"
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "name*"]
ACCOUNT_RATE_LIMITS = {
    "confirm_email": "1/m",
}

HEADLESS_ONLY = True
HEADLESS_FRONTEND_URLS = {
    "account_confirm_email": f"{FRONTEND_URL}/auth/verify-email/{{key}}",
    "account_reset_password_from_key": f"{FRONTEND_URL}/auth/reset-password/{{key}}",
}
HEADLESS_ADAPTER = "apps.accounts.headless.HeadlessAdapter"
HEADLESS_TOKEN_STRATEGY = "apps.accounts.headless.SessionAwareJWTTokenStrategy"
HEADLESS_JWT_ALGORITHM = "HS256"
HEADLESS_JWT_ACCESS_TOKEN_EXPIRES_IN = 900
HEADLESS_JWT_ROTATE_REFRESH_TOKEN = True
HEADLESS_JWT_STATEFUL_VALIDATION_ENABLED = True

# ---------------------------------------------------------------------------
# BILLING MODULE
# ---------------------------------------------------------------------------
STRIPE_SECRET_KEY: str = env("STRIPE_SECRET_KEY", default="")
STRIPE_PUBLISHABLE_KEY: str = env("STRIPE_PUBLISHABLE_KEY", default="")
STRIPE_WEBHOOK_SECRET: str = env("STRIPE_WEBHOOK_SECRET", default="")

BILLING_ADAPTER: str = "apps.billing.adapters.StripeAdapter"

BILLING_PLANS: dict = {
    "free": {
        "name": "Free",
        "stripe_price_id_monthly": "",
        "stripe_price_id_annual": "",
        "trial_days": 0,
        "features": ["Up to 3 projects", "Community support"],
    },
    "pro": {
        "name": "Pro",
        "stripe_price_id_monthly": env("STRIPE_PRICE_PRO_MONTHLY", default=""),
        "stripe_price_id_annual": env("STRIPE_PRICE_PRO_ANNUAL", default=""),
        "trial_days": 14,
        "features": ["Unlimited projects", "Priority support", "API access"],
    },
    "enterprise": {
        "name": "Enterprise",
        "stripe_price_id_monthly": env("STRIPE_PRICE_ENTERPRISE_MONTHLY", default=""),
        "stripe_price_id_annual": env("STRIPE_PRICE_ENTERPRISE_ANNUAL", default=""),
        "trial_days": 0,
        "features": ["Everything in Pro", "Dedicated support", "Custom contracts", "SLA"],
    },
}
# ---------------------------------------------------------------------------
# END BILLING MODULE
# ---------------------------------------------------------------------------

# --------------------------------------------------------------------------
# Environment Variable Validation
# --------------------------------------------------------------------------
# In production, certain env vars MUST be explicitly set (not using defaults).
# In development, defaults are used for zero-config startup.
#
# This validation runs at import time (Django startup) and produces clear
# error messages identifying exactly which env vars are missing.
# --------------------------------------------------------------------------
if os.environ.get("DJANGO_SETTINGS_MODULE", "").endswith("production") and not DEBUG:
    _required_in_production = {
        "SECRET_KEY": SECRET_KEY,
        "DATABASE_URL": None,
        "ALLOWED_HOSTS": ALLOWED_HOSTS,
    }

    _missing = []
    if SECRET_KEY == "django-insecure-change-me-in-production":
        _missing.append("SECRET_KEY (still using insecure default)")
    if ALLOWED_HOSTS == ["localhost", "127.0.0.1"]:
        _missing.append("ALLOWED_HOSTS (still using localhost defaults)")

    if _missing:
        import sys

        print(
            "\n" + "=" * 60 + "\n"
            "MISSING REQUIRED ENVIRONMENT VARIABLES\n"
            + "=" * 60
            + "\n"
            + "\n".join(f"  - {var}" for var in _missing)
            + "\n\n"
            "Set these in your .env file or environment.\n"
            "See apps/api/.env.example for reference.\n" + "=" * 60 + "\n",
            file=sys.stderr,
        )
        raise ImproperlyConfigured(f"Missing required environment variables: {', '.join(_missing)}")
