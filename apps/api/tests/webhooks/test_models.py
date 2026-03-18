"""Model field and cascade delete tests for apps.webhooks.

These tests fail at collection time (ImportError from __init__.py) until
apps.webhooks.models is created — correct RED state.

HOOK-01: endpoint registration fields, delivery cascade behaviour, attempt truncation.
"""

import pytest


@pytest.mark.req("HOOK-01")
@pytest.mark.django_db
def test_endpoint_fields(endpoint):
    """WebhookEndpoint has expected default field values after creation."""
    assert endpoint.url == "https://example.com/hooks"
    assert endpoint.is_active is True
    assert endpoint.consecutive_failures == 0
    assert endpoint.secret_hash != ""


@pytest.mark.req("HOOK-01")
@pytest.mark.django_db
def test_endpoint_event_types_stored(endpoint):
    """WebhookEndpoint.event_types persists the list of event type strings."""
    assert endpoint.event_types == ["user.created"]


@pytest.mark.req("HOOK-01")
@pytest.mark.django_db
def test_delivery_cascade_delete(delivery, endpoint):
    """Deleting an endpoint cascades to its deliveries and attempts."""
    from apps.webhooks.models import WebhookDelivery

    # Sanity: delivery exists before deletion
    delivery_id = delivery.id
    assert WebhookDelivery.objects.filter(id=delivery_id).exists()

    endpoint.delete()

    assert not WebhookDelivery.objects.filter(id=delivery_id).exists()


@pytest.mark.req("HOOK-01")
@pytest.mark.django_db
def test_attempt_response_body_truncated(delivery):
    """WebhookDeliveryAttempt.response_body is truncated to 10 KB."""
    from apps.webhooks.models import WebhookDeliveryAttempt

    large_body = "x" * 20_000  # 20 KB string

    attempt = WebhookDeliveryAttempt.objects.create(
        delivery=delivery,
        attempt_number=1,
        http_status_code=500,
        response_body=large_body,
        response_headers={},
        duration_ms=123,
    )

    # Stored value must not exceed 10 KB (10_240 chars)
    stored = WebhookDeliveryAttempt.objects.get(id=attempt.id)
    assert len(stored.response_body) <= 10_240


@pytest.mark.req("HOOK-01")
@pytest.mark.django_db
def test_delivery_status_transitions(delivery):
    """WebhookDelivery.status can be updated through the defined states."""
    from apps.webhooks.models import WebhookDelivery

    delivery.status = "retrying"
    delivery.save()
    refreshed = WebhookDelivery.objects.get(id=delivery.id)
    assert refreshed.status == "retrying"

    delivery.status = "success"
    delivery.save()
    refreshed = WebhookDelivery.objects.get(id=delivery.id)
    assert refreshed.status == "success"
