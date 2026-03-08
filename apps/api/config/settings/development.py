from .base import *  # noqa: F401, F403

DEBUG = True

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Use StubAdapter in development/testing — no Stripe API keys required.
# Switch to StripeAdapter in production settings.
BILLING_ADAPTER = "apps.billing.stub_adapter.StubAdapter"
