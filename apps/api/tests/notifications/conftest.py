"""Test configuration for notifications tests.

Overrides EMAIL_BACKEND to console.EmailBackend for notifications tests.

Django's setup_test_environment() globally sets EMAIL_BACKEND to locmem.
This conftest restores the expected development default (console backend)
for tests that assert the auto-switch logic in base.py without explicitly
using @override_settings.

Tests that need locmem (e.g. test_css_is_inlined) use @override_settings
directly, which takes precedence over this fixture.
"""

import pytest


@pytest.fixture(autouse=True)
def reset_email_backend_for_settings_tests(settings):
    """Restore EMAIL_BACKEND to console backend for notifications tests.

    Django's setup_test_environment() overrides EMAIL_BACKEND globally to locmem.
    Since test_settings.py asserts the auto-switch logic (console when no RESEND_API_KEY),
    we restore it here so the assertion reflects the actual setting computed at startup.

    Tests that require locmem (test_css_is_inlined, test_plain_text_alternative_present)
    override this via @override_settings on the test method, which takes precedence.
    """
    settings.EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
