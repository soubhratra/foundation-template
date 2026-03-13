"""Tests for the WEBHOOK_EVENTS system check registered with Django.

HOOK-01: manage.py check validates the WEBHOOK_EVENTS setting at startup.
"""

import pytest


def test_webhook_events_check_valid():
    """System check passes when WEBHOOK_EVENTS is a correctly shaped dict."""
    pytest.fail("RED — not yet implemented")


def test_webhook_events_check_missing_key():
    """System check raises a warning when WEBHOOK_EVENTS entry is missing required keys."""
    pytest.fail("RED — not yet implemented")


def test_webhook_events_check_invalid_type():
    """System check fails when WEBHOOK_EVENTS is not a dict."""
    pytest.fail("RED — not yet implemented")
