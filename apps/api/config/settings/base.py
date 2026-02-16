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

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "ninja_extra",
    "corsheaders",
    "apps.accounts",
    "apps.core",
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
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS", default=["http://localhost:3000"]
)

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
            "\n"
            + "=" * 60
            + "\n"
            "MISSING REQUIRED ENVIRONMENT VARIABLES\n"
            + "=" * 60
            + "\n"
            + "\n".join(f"  - {var}" for var in _missing)
            + "\n\n"
            "Set these in your .env file or environment.\n"
            "See apps/api/.env.example for reference.\n"
            + "=" * 60
            + "\n",
            file=sys.stderr,
        )
        raise ImproperlyConfigured(
            f"Missing required environment variables: {', '.join(_missing)}"
        )
