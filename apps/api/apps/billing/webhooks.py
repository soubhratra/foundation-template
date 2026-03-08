"""
Stripe webhook receiver — plain Django view (not Django Ninja).

Why plain Django view (not Ninja):
- Stripe requires raw request body bytes for HMAC verification.
  Django Ninja may parse/transform the body before it reaches the view.
- Webhook endpoints must return quickly (200/400/500) without JSON schemas.
- CSRF exemption is straightforward with standard Django decorators.

Security:
- HMAC signature is verified by the adapter before any processing occurs.
- If verification fails, 400 is returned immediately.
- Processing is delegated to a Celery task so this view returns synchronously.
- If Celery dispatch fails (broker down), 500 is returned so Stripe retries.
"""

import logging

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .tasks import process_stripe_event
from .utils import get_adapter

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def stripe_webhook(request: HttpRequest) -> HttpResponse:
    """Receive a Stripe webhook event, verify the HMAC, and dispatch to Celery.

    Returns:
        200: Event accepted and queued for processing.
        400: Signature verification failed — Stripe will NOT retry.
        500: Dispatch failed (broker down) — Stripe WILL retry.
    """
    payload: bytes = request.body
    signature: str = request.META.get("HTTP_STRIPE_SIGNATURE", "")

    adapter = get_adapter()

    try:
        event = adapter.construct_webhook_event(
            payload=payload,
            signature_header=signature,
            webhook_secret=settings.STRIPE_WEBHOOK_SECRET,
        )
    except ValueError:
        logger.warning("Stripe webhook signature verification failed")
        return HttpResponse(status=400)

    try:
        process_stripe_event.delay(
            event_id=event["id"],
            event_type=event["type"],
            event_data=event["data"]["object"],
        )
    except Exception:
        logger.critical(
            "Failed to dispatch webhook task — broker may be down",
            extra={"event_id": event.get("id"), "event_type": event.get("type")},
        )
        return HttpResponse(status=500)

    return HttpResponse(status=200)
