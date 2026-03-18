"""Tests for the WEBHOOK_EVENTS system check registered with Django.

HOOK-01: manage.py check validates the WEBHOOK_EVENTS setting at startup.
"""

import pytest
from django.core.management import call_command
from django.test import override_settings


@pytest.mark.req("HOOK-04")
def test_webhook_events_check_valid():
    """System check passes when WEBHOOK_EVENTS is a correctly shaped dict."""
    valid_events = {
        "user.created": {
            "description": "A user was created.",
            "example_payload": {"user_id": 1},
        }
    }
    with override_settings(WEBHOOK_EVENTS=valid_events):
        from io import StringIO

        out = StringIO()
        # call_command("check") raises SystemCheckError if errors (not warnings) found.
        # With valid settings, it should complete without raising.
        call_command("check", "--deploy", stdout=out, stderr=out, fail_level="ERROR")


@pytest.mark.req("HOOK-04")
def test_webhook_events_check_missing_key():
    """System check raises a warning when WEBHOOK_EVENTS entry is missing 'description'."""
    from apps.webhooks.checks import check_webhook_events

    bad_events = {
        "user.created": {
            # Missing 'description'
            "example_payload": {"user_id": 1},
        }
    }
    with override_settings(WEBHOOK_EVENTS=bad_events):
        errors = check_webhook_events(app_configs=None)

    warning_ids = [e.id for e in errors]
    assert "webhooks.W002" in warning_ids


@pytest.mark.req("HOOK-04")
def test_webhook_events_check_invalid_type():
    """System check returns a warning when WEBHOOK_EVENTS is not a dict."""
    from apps.webhooks.checks import check_webhook_events

    with override_settings(WEBHOOK_EVENTS="not-a-dict"):
        errors = check_webhook_events(app_configs=None)

    warning_ids = [e.id for e in errors]
    assert "webhooks.W004" in warning_ids
