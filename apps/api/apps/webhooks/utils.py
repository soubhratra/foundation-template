"""Public interface for firing outbound webhook events.

fire_webhook_event() enqueues one Celery deliver_webhook task per matching active
endpoint via transaction.on_commit() — no delivery if the calling transaction rolls back.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from django.conf import settings
from django.db import connection, transaction

if TYPE_CHECKING:
    from apps.orgs.models import Organization


def fire_webhook_event(org: Organization, event_type: str, payload: dict) -> None:
    """Dispatch a webhook event to all active org endpoints subscribed to event_type.

    Validates event_type against WEBHOOK_EVENTS settings dict.
    Enqueues one Celery deliver_webhook task per matching active endpoint,
    dispatched via transaction.on_commit() so no delivery occurs if the
    triggering transaction rolls back.

    Raises ValueError if event_type is not in settings.WEBHOOK_EVENTS.
    """
    webhook_events: dict = getattr(settings, "WEBHOOK_EVENTS", {})
    if event_type not in webhook_events:
        raise ValueError(f"Unknown webhook event type: {event_type}")

    from apps.webhooks.models import WebhookDelivery, WebhookEndpoint
    from apps.webhooks.tasks import deliver_webhook

    # Build payload envelope — always includes webhook_version: "v1"
    envelope: dict = {
        "webhook_version": "v1",
        "event_type": event_type,
        "data": payload,
        "timestamp": int(time.time()),
    }

    endpoints = WebhookEndpoint.objects.filter(
        org=org,
        is_active=True,
    )
    # Filter in Python to check JSONField list membership
    matching = [ep for ep in endpoints if event_type in ep.event_types]

    for endpoint in matching:
        delivery = WebhookDelivery.objects.create(
            endpoint=endpoint,
            event_type=event_type,
            status="pending",
            request_body=envelope,
            request_headers={},
        )
        delivery_id = str(delivery.id)

        def enqueue(did: str = delivery_id) -> None:
            deliver_webhook.delay(did)

        if connection.in_atomic_block:
            transaction.on_commit(enqueue)
        else:
            enqueue()
