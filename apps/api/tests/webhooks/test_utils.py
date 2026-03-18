"""Tests for fire_webhook_event() utility function.

HOOK-01: validation (unknown event, HTTP URL) and dispatch behaviour
(one task per matching endpoint, on_commit dispatch).
"""

from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.test import override_settings

WEBHOOK_EVENTS_SETTINGS = {
    "user.created": {
        "description": "Fired when a new user account is created.",
        "example_payload": {"user_id": 1, "email": "user@example.com"},
    },
}


@pytest.mark.req("HOOK-02")
@pytest.mark.django_db
@override_settings(WEBHOOK_EVENTS=WEBHOOK_EVENTS_SETTINGS)
def test_fire_unknown_event_raises(org):
    """fire_webhook_event raises ValueError when event_type is not in WEBHOOK_EVENTS."""
    from apps.webhooks.utils import fire_webhook_event

    with pytest.raises(ValueError, match="Unknown webhook event type: bad.event"):
        fire_webhook_event(org, "bad.event", {})


@pytest.mark.req("HOOK-02")
@pytest.mark.django_db(transaction=True)
@override_settings(WEBHOOK_EVENTS=WEBHOOK_EVENTS_SETTINGS)
def test_fire_valid_event_enqueues_per_endpoint(org, endpoint):
    """fire_webhook_event enqueues exactly one deliver_webhook task per active endpoint."""
    from apps.webhooks.utils import fire_webhook_event

    with patch("apps.webhooks.tasks.deliver_webhook.delay") as mock_delay:
        fire_webhook_event(org, "user.created", {"user_id": 42})

    mock_delay.assert_called_once()


@pytest.mark.req("HOOK-01")
@pytest.mark.django_db
def test_fire_http_only_url_raises(org):
    """WebhookEndpoint creation rejects non-HTTPS URLs via model clean()."""
    from apps.webhooks.models import WebhookEndpoint

    endpoint = WebhookEndpoint(
        org=org,
        url="http://evil.com/hooks",
        name="Bad Hook",
        event_types=["user.created"],
        signing_key="abc",
        secret_hash="def",
    )
    with pytest.raises(ValidationError, match="HTTPS"):
        endpoint.full_clean()


@pytest.mark.req("HOOK-02")
@pytest.mark.django_db(transaction=True)
@override_settings(WEBHOOK_EVENTS=WEBHOOK_EVENTS_SETTINGS)
def test_no_dispatch_on_rollback(org, endpoint):
    """Delivery tasks are NOT dispatched when the triggering transaction rolls back."""
    from django.db import transaction

    from apps.webhooks.utils import fire_webhook_event

    with patch("apps.webhooks.tasks.deliver_webhook.delay") as mock_delay:
        try:
            with transaction.atomic():
                fire_webhook_event(org, "user.created", {})
                raise RuntimeError("Intentional rollback")
        except RuntimeError:
            pass

    mock_delay.assert_not_called()


@pytest.mark.req("HOOK-02")
@pytest.mark.django_db(transaction=True)
@override_settings(WEBHOOK_EVENTS=WEBHOOK_EVENTS_SETTINGS)
def test_fire_skips_inactive_endpoint(org, endpoint):
    """fire_webhook_event does not enqueue tasks for inactive endpoints."""
    from apps.webhooks.utils import fire_webhook_event

    endpoint.is_active = False
    endpoint.save()

    with patch("apps.webhooks.tasks.deliver_webhook.delay") as mock_delay:
        fire_webhook_event(org, "user.created", {})

    mock_delay.assert_not_called()


@pytest.mark.req("HOOK-02")
@pytest.mark.django_db(transaction=True)
def test_fire_skips_unsubscribed_endpoint(org, endpoint):
    """fire_webhook_event does not enqueue tasks for endpoints not subscribed to the event."""
    from apps.webhooks.utils import fire_webhook_event

    # endpoint is subscribed to "user.created" but we fire "subscription.updated"
    with patch("apps.webhooks.tasks.deliver_webhook.delay") as mock_delay:
        with override_settings(
            WEBHOOK_EVENTS={
                **WEBHOOK_EVENTS_SETTINGS,
                "subscription.updated": {
                    "description": "Test",
                    "example_payload": {},
                },
            }
        ):
            fire_webhook_event(org, "subscription.updated", {})

    mock_delay.assert_not_called()
