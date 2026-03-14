"""Celery tasks for outbound webhook delivery.

deliver_webhook: Sends signed HTTP POST to endpoint URL, records attempt,
retries on failure with exponential backoff (max 7 retries), and activates
circuit breaker after WEBHOOK_CIRCUIT_BREAKER_THRESHOLD consecutive exhausted deliveries.

webhook_delivery_cleanup: Periodic task pruning WebhookDelivery records
older than WEBHOOK_DELIVERY_RETENTION_DAYS (default 30).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
from datetime import timedelta
from typing import Any

import httpx
from celery import shared_task
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

_RESPONSE_BODY_LIMIT = 10 * 1024  # 10KB


def _sign_payload(signing_key: str, payload_bytes: bytes, timestamp: int) -> str:
    """Compute HMAC-SHA256 signature.

    Convention: sha256=HMAC-SHA256(signing_key, f"{timestamp}.{payload_bytes}")
    Mirrors Stripe/GitHub webhook signature format.
    signing_key is endpoint.signing_key — the raw shared secret known to both sides.
    Recipients who received the secret at registration use this exact value.
    Do NOT use secret_hash here — that is SHA-256 of signing_key and would produce
    a different HMAC than recipients expect.
    """
    msg = f"{timestamp}.".encode() + payload_bytes
    sig = hmac.new(signing_key.encode(), msg, hashlib.sha256).hexdigest()
    return f"sha256={sig}"


@shared_task(
    bind=True,
    max_retries=7,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    default_retry_delay=5,
    acks_late=True,
)
def deliver_webhook(self, delivery_id: str) -> None:  # type: ignore[no-untyped-def]
    """Deliver a single webhook event to its target endpoint.

    Loads the WebhookDelivery, sends the signed POST, records the attempt,
    updates delivery status, and handles circuit breaker logic on terminal failure.
    """
    from apps.webhooks.models import (
        DeliveryStatus,
        WebhookDelivery,
        WebhookDeliveryAttempt,
    )

    try:
        delivery = WebhookDelivery.objects.select_related("endpoint").get(id=delivery_id)
    except WebhookDelivery.DoesNotExist:
        logger.error("deliver_webhook: delivery %s not found — skipping", delivery_id)
        return

    endpoint = delivery.endpoint
    if not endpoint.is_active:
        logger.info(
            "deliver_webhook: endpoint %s is disabled — skipping delivery %s",
            endpoint.id,
            delivery_id,
        )
        return

    attempt_number = delivery.attempts.count() + 1
    payload_bytes = json.dumps(delivery.request_body, separators=(",", ":")).encode()
    timestamp = int(time.time())
    signature = _sign_payload(endpoint.signing_key, payload_bytes, timestamp)

    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Id": str(delivery.id),
        "X-Webhook-Timestamp": str(timestamp),
        "X-Webhook-Signature": signature,
    }

    http_status: int | None = None
    response_body = ""
    response_headers: dict = {}
    error_message = ""
    start_ms = time.monotonic()

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                endpoint.url,
                content=payload_bytes,
                headers=headers,
            )
        duration_ms = int((time.monotonic() - start_ms) * 1000)
        http_status = response.status_code
        response_body = response.text[:_RESPONSE_BODY_LIMIT]
        response_headers = dict(response.headers)

        WebhookDeliveryAttempt.objects.create(
            delivery=delivery,
            attempt_number=attempt_number,
            http_status_code=http_status,
            response_body=response_body,
            response_headers=response_headers,
            duration_ms=duration_ms,
            error_message="",
        )

        if 200 <= http_status < 300:
            delivery.status = DeliveryStatus.SUCCESS
            delivery.save(update_fields=["status"])
            # Reset circuit breaker on success
            endpoint.consecutive_failures = 0
            endpoint.save(update_fields=["consecutive_failures"])
            return

        # Non-2xx — will retry
        delivery.status = DeliveryStatus.RETRYING
        delivery.save(update_fields=["status"])
        raise Exception(f"Non-2xx response: HTTP {http_status}")

    except httpx.RequestError as exc:
        duration_ms = int((time.monotonic() - start_ms) * 1000)
        error_message = str(exc)
        WebhookDeliveryAttempt.objects.create(
            delivery=delivery,
            attempt_number=attempt_number,
            http_status_code=None,
            response_body="",
            response_headers={},
            duration_ms=duration_ms,
            error_message=error_message,
        )
        delivery.status = DeliveryStatus.RETRYING
        delivery.save(update_fields=["status"])
        raise  # triggers autoretry_for=(Exception,)

    except Exception:
        # autoretry handles scheduling; if this is the final retry, handle terminal failure.
        retries = self.request.retries
        if retries >= self.max_retries:
            _handle_terminal_failure(delivery, endpoint, error_message or f"HTTP {http_status}")
        raise


def _handle_terminal_failure(
    delivery: Any,
    endpoint: Any,
    last_reason: str,
) -> None:
    """Called when a delivery has exhausted all retries with no 2xx response."""
    from apps.notifications.utils import send_email
    from apps.orgs.models import Membership
    from apps.webhooks.models import DeliveryStatus

    delivery.status = DeliveryStatus.FAILED
    delivery.save(update_fields=["status"])

    endpoint.consecutive_failures += 1
    endpoint.save(update_fields=["consecutive_failures"])

    threshold = getattr(settings, "WEBHOOK_CIRCUIT_BREAKER_THRESHOLD", 5)
    if endpoint.consecutive_failures >= threshold:
        endpoint.is_active = False
        endpoint.save(update_fields=["is_active"])
        logger.warning(
            "deliver_webhook: endpoint %s auto-disabled after %d consecutive failures",
            endpoint.id,
            endpoint.consecutive_failures,
        )
        # Notify org admin(s)
        admin_memberships = Membership.objects.filter(
            org=endpoint.org,
            role__in=[Membership.Role.OWNER, Membership.Role.ADMIN],
        ).select_related("user")
        for membership in admin_memberships:
            send_email(
                to=membership.user.email,
                template_name="webhooks/endpoint_disabled.html",
                context={
                    "endpoint_url": endpoint.url,
                    "endpoint_name": endpoint.name or endpoint.url,
                    "last_failure_reason": last_reason,
                    "org_name": endpoint.org.name,
                },
            )


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def webhook_delivery_cleanup(self) -> dict:  # type: ignore[no-untyped-def]
    """Delete WebhookDelivery records older than WEBHOOK_DELIVERY_RETENTION_DAYS.

    Cascade delete removes associated WebhookDeliveryAttempt records automatically.
    Scheduled via Celery beat (daily).
    """
    from apps.webhooks.models import WebhookDelivery

    retention_days = getattr(settings, "WEBHOOK_DELIVERY_RETENTION_DAYS", 30)
    cutoff = timezone.now() - timedelta(days=retention_days)
    deleted_count, _ = WebhookDelivery.objects.filter(created_at__lt=cutoff).delete()
    logger.info("webhook_delivery_cleanup: deleted %d delivery records", deleted_count)
    return {"deleted": deleted_count}
