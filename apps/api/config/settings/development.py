from .base import *  # noqa: F401, F403

DEBUG = True

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Allow login without email verification in development.
# Production keeps ACCOUNT_EMAIL_VERIFICATION = "mandatory" from base.py.
ACCOUNT_EMAIL_VERIFICATION = "optional"

# Use StubAdapter in development/testing — no Stripe API keys required.
# Switch to StripeAdapter in production settings.
BILLING_ADAPTER = "apps.billing.stub_adapter.StubAdapter"

# --- django-debug-toolbar (DEV-06) — development only ---
INSTALLED_APPS = [*INSTALLED_APPS, "debug_toolbar"]  # noqa: F405
MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware", *MIDDLEWARE]  # noqa: F405
INTERNAL_IPS = ["127.0.0.1"]
