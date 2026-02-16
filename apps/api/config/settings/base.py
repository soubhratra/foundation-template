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
    "django.contrib.sites",
    "ninja_extra",
    "corsheaders",
    "allauth",
    "allauth.account",
    "allauth.headless",
    "allauth.socialaccount",
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
    "allauth.account.middleware.AccountMiddleware",
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

CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=[
        "http://localhost:3000",
        "http://localhost:19006",
    ],
)
CORS_ALLOW_CREDENTIALS = True

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
HEADLESS_TOKEN_STRATEGY = (
    "allauth.headless.tokens.strategies.jwt.JWTTokenStrategy"
)
HEADLESS_JWT_ALGORITHM = "HS256"
HEADLESS_JWT_ACCESS_TOKEN_EXPIRES_IN = 900
HEADLESS_JWT_ROTATE_REFRESH_TOKEN = True
HEADLESS_JWT_STATEFUL_VALIDATION_ENABLED = True

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
