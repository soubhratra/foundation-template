"""Tests for fire_webhook_event() utility function.

HOOK-01: validation (unknown event, HTTP URL) and dispatch behaviour
(one task per matching endpoint, on_commit dispatch).
"""

import pytest


@pytest.mark.django_db
def test_fire_unknown_event_raises(org):
    """fire_webhook_event raises ValueError when event_type is not in WEBHOOK_EVENTS."""
    pytest.fail("RED — not yet implemented")


@pytest.mark.django_db
def test_fire_valid_event_enqueues_per_endpoint(org, endpoint):
    """fire_webhook_event enqueues exactly one deliver_webhook task per active endpoint."""
    pytest.fail("RED — not yet implemented")


@pytest.mark.django_db
def test_fire_http_only_url_raises(org, endpoint):
    """fire_webhook_event (or endpoint creation) rejects non-HTTPS URLs."""
    pytest.fail("RED — not yet implemented")


@pytest.mark.django_db
def test_no_dispatch_on_rollback(org, endpoint):
    """Delivery tasks are NOT dispatched when the triggering transaction rolls back."""
    pytest.fail("RED — not yet implemented")


@pytest.mark.django_db
def test_fire_skips_inactive_endpoint(org, endpoint):
    """fire_webhook_event does not enqueue tasks for inactive endpoints."""
    pytest.fail("RED — not yet implemented")


@pytest.mark.django_db
def test_fire_skips_unsubscribed_endpoint(org, endpoint):
    """fire_webhook_event does not enqueue tasks for endpoints not subscribed to the event."""
    pytest.fail("RED — not yet implemented")
