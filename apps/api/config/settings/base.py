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
POSTHOG_PROJECT_ID: str = env("POSTHOG_PROJECT_ID", default="")
POSTHOG_PERSONAL_API_KEY: str = env("POSTHOG_PERSONAL_API_KEY", default="")
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
    "csp",
    "django_celery_results",
    "django_celery_beat",
    "django_structlog",
    "allauth",
    "allauth.account",
    "allauth.headless",
    "allauth.socialaccount",
    "apps.accounts",
    "apps.core",
    "apps.ai",
    "apps.billing",  # BILLING MODULE — remove this line to exclude billing
    # B2B_START
    "apps.orgs",  # B2B MODULE — remove this line to exclude B2B
    "apps.webhooks",  # B2B MODULE — outbound webhooks
    # B2B_END
    "anymail",  # EMAIL MODULE — remove this line to exclude email
    "apps.notifications",  # EMAIL MODULE — remove this line to exclude email
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "csp.middleware.CSPMiddleware",  # SECURITY HEADERS — nonce generated per-request
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "apps.core.middleware.RequestContextMiddleware",
    "apps.core.middleware.ObservabilityMiddleware",  # OBSERVABILITY MODULE
    "apps.core.middleware.AuthRateLimitMiddleware",  # RATE LIMITING MODULE
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
CACHE_REDIS_URL = env("CACHE_REDIS_URL", default="redis://localhost:6379/1")
SESSION_REDIS_URL = env("SESSION_REDIS_URL", default="redis://localhost:6379/2")

# --- CACHE + SESSION BACKEND ---
# django-redis: replaces LocMemCache in all non-test environments.
# DB 0: Celery (CELERY_BROKER_URL)
# DB 1: Django cache (CACHE_REDIS_URL)
# DB 2: Django sessions (SESSION_REDIS_URL)
# Tests override CACHES to LocMemCache via conftest test_isolation_settings fixture.
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": CACHE_REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
        },
    },
    "sessions": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": SESSION_REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
        },
    },
}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "sessions"

# --- RATE LIMITING ---
# django-ratelimit: IP-based rate limiting on auth endpoints.
# Auth endpoints are allauth headless views — rate limiting is applied via
# AuthRateLimitMiddleware (path-prefix scoped) rather than @ratelimit decorator
# (allauth views are not owned code; decorator cannot be applied directly).
# RATELIMIT_FAIL_OPEN: pass through if Redis unreachable — auth availability > enforcement.
# RATELIMIT_ENABLE: set to False in tests via conftest autouse fixture (not in development.py).
RATELIMIT_AUTH_LOGIN: str = "5/m"
RATELIMIT_ENABLE: bool = True
RATELIMIT_FAIL_OPEN: bool = True
RATELIMIT_USE_CACHE: str = "default"
RATELIMIT_VIEW: str = "apps.core.ratelimit.ratelimited_error"

# --- SECURITY HEADERS ---
# django-csp 4.0 uses CONTENT_SECURITY_POLICY dict (NOT old CSP_* flat settings).
# Old API (CSP_DEFAULT_SRC etc.) is silently ignored in 4.0 — do not mix APIs.
#
# NONCE sentinel: django-csp replaces "NONCE" with 'nonce-{unique_value}' per request.
# request.csp_nonce is available in templates for inline scripts that must be whitelisted.
#
# Third-party sources:
#   PostHog: eu.i.posthog.com and us.i.posthog.com (EU/US data regions)
#   Stripe:  js.stripe.com (SDK), hooks.stripe.com (webhook ping JS)
#
# upgrade-insecure-requests omitted — HSTS in production.py handles upgrade-to-HTTPS.
# Adding it here would break local HTTP development.
CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        "default-src": ["'self'"],
        "script-src": ["'self'", "NONCE", "https://js.stripe.com"],
        "script-src-elem": ["'self'", "NONCE", "https://js.stripe.com"],
        "style-src": ["'self'", "NONCE"],
        "img-src": ["'self'", "data:", "blob:"],
        "font-src": ["'self'"],
        "connect-src": [
            "'self'",
            "https://eu.i.posthog.com",
            "https://us.i.posthog.com",
            "https://hooks.stripe.com",
        ],
        "frame-src": ["https://js.stripe.com"],
        "object-src": ["'none'"],
        "base-uri": ["'self'"],
        "form-action": ["'self'"],
        "frame-ancestors": ["'none'"],
    },
}

# X-Frame-Options: Django's XFrameOptionsMiddleware reads X_FRAME_OPTIONS.
# "DENY" is the Django default but we set it explicitly for auditability.
X_FRAME_OPTIONS = "DENY"

# Referrer-Policy: Django SecurityMiddleware reads SECURE_REFERRER_POLICY.
# "strict-origin-when-cross-origin" sends full URL on same-origin, origin only cross-origin.
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:3000")

# --------------------------------------------------------------------------
# Celery Configuration
# --------------------------------------------------------------------------
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = "django-db"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes

# --------------------------------------------------------------------------
# Celery Beat Schedule — Phase 15
# --------------------------------------------------------------------------
# DatabaseScheduler reads schedule from DB (django_celery_beat tables).
# Add tasks here for initial seeding; operators can edit via admin or API.
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

from celery.schedules import crontab  # noqa: E402, F401

CELERY_BEAT_SCHEDULE = {
    "example-periodic-task": {
        "task": "apps.core.tasks.example_periodic_task",
        "schedule": 60.0,  # every 60 seconds — change to crontab() for cron expressions
        "options": {"expires": 30},  # drop if no worker picks it up in 30s
    },
    # B2B_START
    "webhook-delivery-cleanup": {
        "task": "apps.webhooks.tasks.webhook_delivery_cleanup",
        "schedule": crontab(hour=2, minute=0),  # Daily at 2am
    },
    # B2B_END
}

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
    "socialaccount_login_error": f"{FRONTEND_URL}/auth/error",
}
HEADLESS_ADAPTER = "apps.accounts.headless.HeadlessAdapter"
HEADLESS_TOKEN_STRATEGY = "apps.accounts.headless.SessionAwareJWTTokenStrategy"
HEADLESS_JWT_ALGORITHM = "HS256"
HEADLESS_JWT_ACCESS_TOKEN_EXPIRES_IN = 900
HEADLESS_JWT_ROTATE_REFRESH_TOKEN = True
HEADLESS_JWT_STATEFUL_VALIDATION_ENABLED = True

# ---------------------------------------------------------------------------
# SOCIAL AUTH MODULE — remove this block to exclude social auth
# ---------------------------------------------------------------------------
import base64 as _base64  # noqa: E402  # SOCIAL AUTH MODULE


def _configure_social_providers(env_dict: dict) -> dict:  # SOCIAL AUTH MODULE
    """# SOCIAL AUTH MODULE
    Pure function: maps an env dict to social auth configuration.  # SOCIAL AUTH MODULE
    Called once at module load time. Also importable by tests for direct  # SOCIAL AUTH MODULE
    unit verification of conditional provider registration logic.  # SOCIAL AUTH MODULE
    Returns a dict with keys: extra_installed_apps, providers, auto_connect.  # SOCIAL AUTH MODULE
    """  # SOCIAL AUTH MODULE
    google_id = env_dict.get("GOOGLE_CLIENT_ID", "")  # SOCIAL AUTH MODULE
    google_secret = env_dict.get("GOOGLE_CLIENT_SECRET", "")  # SOCIAL AUTH MODULE
    github_id = env_dict.get("GITHUB_CLIENT_ID", "")  # SOCIAL AUTH MODULE
    github_secret = env_dict.get("GITHUB_CLIENT_SECRET", "")  # SOCIAL AUTH MODULE
    apple_id = env_dict.get("APPLE_CLIENT_ID", "")  # SOCIAL AUTH MODULE
    apple_team = env_dict.get("APPLE_TEAM_ID", "")  # SOCIAL AUTH MODULE
    apple_key_id = env_dict.get("APPLE_KEY_ID", "")  # SOCIAL AUTH MODULE
    apple_pk_b64 = env_dict.get("APPLE_PRIVATE_KEY", "")  # SOCIAL AUTH MODULE
    try:  # SOCIAL AUTH MODULE
        apple_pk = (
            _base64.b64decode(apple_pk_b64).decode() if apple_pk_b64 else ""
        )  # SOCIAL AUTH MODULE
    except Exception:  # SOCIAL AUTH MODULE
        apple_pk = (
            apple_pk_b64  # SOCIAL AUTH MODULE — fallback: use raw value (e.g. plain PEM in tests)
        )

    extra_installed_apps: list[str] = []  # SOCIAL AUTH MODULE
    providers: dict = {}  # SOCIAL AUTH MODULE

    if google_id and google_secret:  # SOCIAL AUTH MODULE
        extra_installed_apps.append("allauth.socialaccount.providers.google")  # SOCIAL AUTH MODULE
        providers["google"] = {  # SOCIAL AUTH MODULE
            "APPS": [{"client_id": google_id, "secret": google_secret, "key": ""}],
            "SCOPE": ["profile", "email"],
            "AUTH_PARAMS": {"access_type": "online"},
            "EMAIL_AUTHENTICATION": True,
        }  # SOCIAL AUTH MODULE
    if github_id and github_secret:  # SOCIAL AUTH MODULE
        extra_installed_apps.append("allauth.socialaccount.providers.github")  # SOCIAL AUTH MODULE
        providers["github"] = {  # SOCIAL AUTH MODULE
            "APPS": [{"client_id": github_id, "secret": github_secret, "key": ""}],
            "SCOPE": ["user:email"],
            "VERIFIED_EMAIL": True,
            "EMAIL_AUTHENTICATION": True,
        }  # SOCIAL AUTH MODULE
    if apple_id:  # SOCIAL AUTH MODULE
        extra_installed_apps.append("allauth.socialaccount.providers.apple")  # SOCIAL AUTH MODULE
        providers["apple"] = {  # SOCIAL AUTH MODULE
            "APPS": [
                {
                    "client_id": apple_id,
                    "secret": apple_key_id,
                    "key": apple_team,
                    "settings": {"certificate_key": apple_pk, "hidden": True},
                }
            ],
        }  # SOCIAL AUTH MODULE

    return {  # SOCIAL AUTH MODULE
        "extra_installed_apps": extra_installed_apps,  # SOCIAL AUTH MODULE
        "providers": providers,  # SOCIAL AUTH MODULE
        "auto_connect": True,  # SOCIAL AUTH MODULE
    }  # SOCIAL AUTH MODULE


_GOOGLE_CLIENT_ID: str = env("GOOGLE_CLIENT_ID", default="")  # SOCIAL AUTH MODULE
_GITHUB_CLIENT_ID: str = env("GITHUB_CLIENT_ID", default="")  # SOCIAL AUTH MODULE
_APPLE_CLIENT_ID: str = env("APPLE_CLIENT_ID", default="")  # SOCIAL AUTH MODULE

_social_cfg = _configure_social_providers(
    {  # SOCIAL AUTH MODULE
        "GOOGLE_CLIENT_ID": _GOOGLE_CLIENT_ID,  # SOCIAL AUTH MODULE
        "GOOGLE_CLIENT_SECRET": env("GOOGLE_CLIENT_SECRET", default=""),  # SOCIAL AUTH MODULE
        "GITHUB_CLIENT_ID": _GITHUB_CLIENT_ID,  # SOCIAL AUTH MODULE
        "GITHUB_CLIENT_SECRET": env("GITHUB_CLIENT_SECRET", default=""),  # SOCIAL AUTH MODULE
        "APPLE_CLIENT_ID": _APPLE_CLIENT_ID,  # SOCIAL AUTH MODULE
        "APPLE_TEAM_ID": env("APPLE_TEAM_ID", default=""),  # SOCIAL AUTH MODULE
        "APPLE_KEY_ID": env("APPLE_KEY_ID", default=""),  # SOCIAL AUTH MODULE
        "APPLE_PRIVATE_KEY": env("APPLE_PRIVATE_KEY", default=""),  # SOCIAL AUTH MODULE
    }
)  # SOCIAL AUTH MODULE

INSTALLED_APPS = INSTALLED_APPS + _social_cfg["extra_installed_apps"]  # SOCIAL AUTH MODULE
SOCIALACCOUNT_PROVIDERS: dict = _social_cfg["providers"]  # SOCIAL AUTH MODULE
SOCIALACCOUNT_ADAPTER = (
    "apps.accounts.social_adapter.FoundationSocialAccountAdapter"  # SOCIAL AUTH MODULE
)
SOCIALACCOUNT_AUTO_SIGNUP = True  # SOCIAL AUTH MODULE
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True  # SOCIAL AUTH MODULE
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True  # SOCIAL AUTH MODULE
# ---------------------------------------------------------------------------
# END SOCIAL AUTH MODULE
# ---------------------------------------------------------------------------

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
        "feature_flags": {
            "api_access": False,
            "advanced_analytics": False,
            "white_label": False,
        },
    },
    "pro": {
        "name": "Pro",
        "stripe_price_id_monthly": env("STRIPE_PRICE_PRO_MONTHLY", default=""),
        "stripe_price_id_annual": env("STRIPE_PRICE_PRO_ANNUAL", default=""),
        "trial_days": 14,
        "features": ["Unlimited projects", "Priority support", "API access"],
        "feature_flags": {
            "api_access": True,
            "advanced_analytics": True,
            "white_label": False,
        },
    },
    "enterprise": {
        "name": "Enterprise",
        "stripe_price_id_monthly": env("STRIPE_PRICE_ENTERPRISE_MONTHLY", default=""),
        "stripe_price_id_annual": env("STRIPE_PRICE_ENTERPRISE_ANNUAL", default=""),
        "trial_days": 0,
        "features": ["Everything in Pro", "Dedicated support", "Custom contracts", "SLA"],
        "feature_flags": {
            "api_access": True,
            "advanced_analytics": True,
            "white_label": True,
        },
    },
}

# B2B_START
WEBHOOK_EVENTS: dict[str, dict] = {
    "user.created": {
        "description": "Fired when a new user account is created.",
        "example_payload": {"user_id": 1, "email": "user@example.com"},
    },
    "subscription.updated": {
        "description": "Fired when a user's subscription status changes.",
        "example_payload": {"user_id": 1, "plan": "pro", "status": "active"},
    },
    "org.member_added": {
        "description": "Fired when a user accepts an org invitation.",
        "example_payload": {"org_slug": "acme", "user_id": 2, "role": "member"},
    },
}

WEBHOOK_DELIVERY_RETENTION_DAYS: int = 30
WEBHOOK_CIRCUIT_BREAKER_THRESHOLD: int = 5
# B2B_END
# ---------------------------------------------------------------------------
# END BILLING MODULE
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# EMAIL MODULE
# ---------------------------------------------------------------------------
RESEND_API_KEY: str = env("RESEND_API_KEY", default="")

EMAIL_BACKEND = (
    "anymail.backends.resend.EmailBackend"
    if RESEND_API_KEY
    else "django.core.mail.backends.console.EmailBackend"
)

ANYMAIL = {
    "RESEND_API_KEY": RESEND_API_KEY,
}

DEFAULT_FROM_EMAIL: str = env("DEFAULT_FROM_EMAIL", default="noreply@example.com")
# ---------------------------------------------------------------------------
# END EMAIL MODULE
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
