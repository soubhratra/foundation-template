from .base import *  # noqa: F401, F403

DEBUG = True

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Allow login without email verification in development.
# Production keeps ACCOUNT_EMAIL_VERIFICATION = "mandatory" from base.py.
ACCOUNT_EMAIL_VERIFICATION = "optional"

# Always use the console email backend in development so signup/verification
# flows don't fail when RESEND_API_KEY is present in the local .env.
# Base.py picks Anymail when RESEND_API_KEY is set, which would fail without
# a live API key — E2E tests call signup, so this override prevents 500 errors.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Use StubAdapter in development/testing — no Stripe API keys required.
# Switch to StripeAdapter in production settings.
BILLING_ADAPTER = "apps.billing.stub_adapter.StubAdapter"

# Disable rate limiting in development — avoids interference with E2E test suites
# that make multiple login requests from the same IP in quick succession.
# Rate limiting is enforced in production only.
RATELIMIT_ENABLE = False

# Disable allauth's built-in rate limiting in development so E2E test suites
# running multiple parallel workers don't hit the login_failed rate limit
# (default: 5 failures per 300s per email key).
# Setting to False triggers allauth's explicit "return {}" branch in AppSettings.RATE_LIMITS,
# which skips all rate limit checks. Empty dict ({}) does NOT disable rate limits —
# it just merges with defaults, leaving them all active.
ACCOUNT_RATE_LIMITS = False

# --- django-debug-toolbar (DEV-06) — development only ---
INSTALLED_APPS = [*INSTALLED_APPS, "debug_toolbar"]  # noqa: F405
MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware", *MIDDLEWARE]  # noqa: F405
INTERNAL_IPS = ["127.0.0.1"]
