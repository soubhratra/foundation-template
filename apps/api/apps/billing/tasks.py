"""
Celery tasks for billing event processing.

process_stripe_event:
- Idempotency guard: ProcessedWebhookEvent.get_or_create prevents duplicate processing.
- Tier-1 handlers: 6 event types that update Subscription/Payment model state.
- Unknown events: silently acknowledged at DEBUG level.
- Retry: autoretry_for=(Exception,) with exponential backoff (2^retries seconds).
- Dead-letter: after max_retries exceeded, logs at CRITICAL level.
"""

import datetime
import logging
import random
from typing import Any

from celery import shared_task
from django.core.cache import cache

logger = logging.getLogger(__name__)


def _unix_to_datetime(ts: int | None) -> datetime.datetime | None:
    """Convert a Unix timestamp (int) to a timezone-aware datetime, or None."""
    if ts is None:
        return None
    return datetime.datetime.fromtimestamp(ts, tz=datetime.UTC)


def _handle_checkout_session_completed(event_data: dict[str, Any]) -> None:
    """checkout.session.completed → create/update Subscription with ACTIVE status."""
    from apps.billing.models import Customer, Subscription, SubscriptionStatus

    stripe_customer_id: str = event_data.get("customer", "")
    stripe_subscription_id: str = event_data.get("subscription", "")

    try:
        customer = Customer.objects.get(stripe_customer_id=stripe_customer_id)
    except Customer.DoesNotExist:
        logger.warning(
            "checkout.session.completed: no Customer for stripe_customer_id=%s",
            stripe_customer_id,
        )
        return

    Subscription.objects.update_or_create(
        customer=customer,
        defaults={
            "status": SubscriptionStatus.ACTIVE,
            "stripe_subscription_id": stripe_subscription_id,
        },
    )


def _handle_subscription_created(event_data: dict[str, Any]) -> None:
    """customer.subscription.created → create/update Subscription with all fields."""
    from apps.billing.models import Customer, Subscription

    stripe_customer_id: str = event_data.get("customer", "")
    stripe_subscription_id: str = event_data.get("id", "")

    try:
        customer = Customer.objects.get(stripe_customer_id=stripe_customer_id)
    except Customer.DoesNotExist:
        logger.warning(
            "customer.subscription.created: no Customer for stripe_customer_id=%s",
            stripe_customer_id,
        )
        return

    Subscription.objects.update_or_create(
        customer=customer,
        defaults={
            "stripe_subscription_id": stripe_subscription_id,
            "status": event_data.get("status", "incomplete"),
            "cancel_at_period_end": event_data.get("cancel_at_period_end", False),
            "current_period_start": _unix_to_datetime(event_data.get("current_period_start")),
            "current_period_end": _unix_to_datetime(event_data.get("current_period_end")),
        },
    )


def _extract_price_id_from_event(event_data: dict[str, Any]) -> str:
    """Extract the active price ID from a subscription.updated event payload.

    Stripe wraps price data inside items.data[0].price.id — not a top-level field.
    Guards against subscriptions with no items (returns empty string).

    Note: Uses data[0] — designed for single-plan subscriptions.
    Multi-item (metered billing) subscriptions would require iterating items.
    """
    items = event_data.get("items", {})
    data_list = items.get("data", [])
    if not data_list:
        return ""
    return data_list[0].get("price", {}).get("id", "")


def _handle_subscription_updated(event_data: dict[str, Any]) -> None:
    """customer.subscription.updated → update status, cancel_at_period_end, period dates."""
    from apps.billing.models import Customer, Subscription

    stripe_customer_id: str = event_data.get("customer", "")

    try:
        customer = Customer.objects.get(stripe_customer_id=stripe_customer_id)
    except Customer.DoesNotExist:
        logger.warning(
            "customer.subscription.updated: no Customer for stripe_customer_id=%s",
            stripe_customer_id,
        )
        return

    try:
        subscription = Subscription.objects.get(customer=customer)
    except Subscription.DoesNotExist:
        logger.warning(
            "customer.subscription.updated: no Subscription for customer=%s",
            customer.pk,
        )
        return

    subscription.status = event_data.get("status", subscription.status)
    subscription.cancel_at_period_end = event_data.get(
        "cancel_at_period_end", subscription.cancel_at_period_end
    )
    period_start = event_data.get("current_period_start")
    period_end = event_data.get("current_period_end")
    if period_start is not None:
        subscription.current_period_start = _unix_to_datetime(period_start)
    if period_end is not None:
        subscription.current_period_end = _unix_to_datetime(period_end)
    subscription.save()

    # --- ENT-02: Resolve plan_id and invalidate entitlement cache ---
    price_id = _extract_price_id_from_event(event_data)
    if price_id:
        from apps.billing.models import PlanProviderMapping

        try:
            mapping = PlanProviderMapping.objects.get(
                price_id=price_id, provider="stripe", is_active=True
            )
            subscription.plan_id = mapping.plan_id
            subscription.save(update_fields=["plan_id", "updated_at"])
        except PlanProviderMapping.DoesNotExist:
            logger.warning(
                "customer.subscription.updated: no PlanProviderMapping for price_id=%s",
                price_id,
            )

    # Invalidate entitlement cache unconditionally — covers both successful plan resolution
    # and cases where PlanProviderMapping is missing (downgrade to unmapped plan).
    # cache.delete() is a no-op on cache miss — no extra round-trip.
    cache.delete(f"entitlements:{customer.user.pk}")
    # B2B_START
    _try_invalidate_org_member_caches(stripe_customer_id)
    # B2B_END


def _handle_subscription_deleted(event_data: dict[str, Any]) -> None:
    """customer.subscription.deleted → set Subscription.status = CANCELED."""
    from apps.billing.models import Customer, Subscription, SubscriptionStatus

    stripe_customer_id: str = event_data.get("customer", "")

    try:
        customer = Customer.objects.get(stripe_customer_id=stripe_customer_id)
    except Customer.DoesNotExist:
        logger.warning(
            "customer.subscription.deleted: no Customer for stripe_customer_id=%s",
            stripe_customer_id,
        )
        return

    Subscription.objects.filter(customer=customer).update(status=SubscriptionStatus.CANCELED)


def _handle_invoice_payment_succeeded(event_data: dict[str, Any]) -> None:
    """invoice.payment_succeeded → create Payment with status 'succeeded'."""
    from apps.billing.models import Customer, Payment

    stripe_customer_id: str = event_data.get("customer", "")
    payment_intent_id: str = event_data.get("payment_intent") or ""
    # Stripe sends amount_paid in cents; store as decimal (divide by 100)
    amount_cents: int = event_data.get("amount_paid", 0) or 0
    currency: str = event_data.get("currency", "usd")

    try:
        customer = Customer.objects.get(stripe_customer_id=stripe_customer_id)
    except Customer.DoesNotExist:
        logger.warning(
            "invoice.payment_succeeded: no Customer for stripe_customer_id=%s",
            stripe_customer_id,
        )
        return

    Payment.objects.create(
        customer=customer,
        stripe_payment_intent_id=payment_intent_id,
        amount=amount_cents / 100,
        currency=currency,
        status="succeeded",
    )


def _handle_invoice_payment_failed(event_data: dict[str, Any]) -> None:
    """invoice.payment_failed → create Payment('failed') + set Subscription to PAST_DUE."""
    from apps.billing.models import Customer, Payment, Subscription, SubscriptionStatus

    stripe_customer_id: str = event_data.get("customer", "")
    payment_intent_id: str = event_data.get("payment_intent") or ""
    # Stripe sends amount_due in cents
    amount_cents: int = event_data.get("amount_due", 0) or 0
    currency: str = event_data.get("currency", "usd")

    try:
        customer = Customer.objects.get(stripe_customer_id=stripe_customer_id)
    except Customer.DoesNotExist:
        logger.warning(
            "invoice.payment_failed: no Customer for stripe_customer_id=%s",
            stripe_customer_id,
        )
        return

    Payment.objects.create(
        customer=customer,
        stripe_payment_intent_id=payment_intent_id,
        amount=amount_cents / 100,
        currency=currency,
        status="failed",
    )

    Subscription.objects.filter(customer=customer).update(status=SubscriptionStatus.PAST_DUE)


# B2B_START
def _try_invalidate_org_member_caches(stripe_customer_id: str) -> None:
    """Invalidate org-scoped entitlement caches for all members of the org.

    Called at the end of _handle_subscription_updated() to keep org member
    entitlement caches consistent when an org's Stripe subscription changes.

    Uses lazy imports inside the try block to avoid circular imports at Django
    startup (orgs models depend on billing; billing tasks must not import orgs
    at module top-level).

    Silently returns when OrgCustomer is not found — this is normal for personal
    subscription events where stripe_customer_id belongs to a user-level Customer,
    not an OrgCustomer.

    Args:
        stripe_customer_id: The Stripe customer ID from the subscription event.
    """
    try:
        from django.core.cache import cache

        from apps.orgs.models import Membership, OrgCustomer

        org_customer = OrgCustomer.objects.get(stripe_customer_id=stripe_customer_id)
        org = org_customer.org
        member_ids = Membership.objects.filter(org=org).values_list("user_id", flat=True)
        for user_id in member_ids:
            cache.delete(f"entitlements:org:{org.pk}:{user_id}")
    except Exception:
        pass  # OrgCustomer not found — personal subscription, not org


# B2B_END


# Mapping of Stripe event types to handler functions
_TIER1_HANDLERS = {
    "checkout.session.completed": _handle_checkout_session_completed,
    "customer.subscription.created": _handle_subscription_created,
    "customer.subscription.updated": _handle_subscription_updated,
    "customer.subscription.deleted": _handle_subscription_deleted,
    "invoice.payment_succeeded": _handle_invoice_payment_succeeded,
    "invoice.payment_failed": _handle_invoice_payment_failed,
}


@shared_task(
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    default_retry_delay=2,
)
def generate_invoice_pdf(self, invoice_data: dict) -> bytes:
    """Generate invoice PDF bytes asynchronously.

    Returns raw bytes stored via django-celery-results backend.
    Client polls GET /billing/invoices/pdf-status/{task_id} until state=SUCCESS.

    NOTE: PDF bytes stored in django_celery_results_taskresult TEXT column.
    Bounded by MAX_PDF_BYTES guard in render_invoice_pdf (512KB max).

    Lazy import avoids importing render_invoice_pdf (and weasyprint) at module
    load time — required to prevent Celery fork deadlocks (WeasyPrint issue #684).
    """
    from apps.billing.pdf import render_invoice_pdf  # lazy import avoids circular

    return render_invoice_pdf(invoice_data)


@shared_task(
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    default_retry_delay=2,
)
def process_stripe_event(
    self,
    event_id: str,
    event_type: str,
    event_data: dict[str, Any],
) -> None:
    """Process a Stripe webhook event asynchronously.

    Idempotency: Uses ProcessedWebhookEvent.get_or_create to ensure each
    event_id is only processed once, even if Stripe delivers it multiple times.

    Retry: On failure, retries with exponential backoff (2^retries ± jitter).
    After max_retries, logs at CRITICAL level for alerting.

    Args:
        event_id: Stripe event ID (e.g. "evt_xxx")
        event_type: Stripe event type (e.g. "customer.subscription.updated")
        event_data: The event's data.object dict from the Stripe payload
    """
    from apps.billing.models import ProcessedWebhookEvent

    # Idempotency guard — get_or_create is atomic via UNIQUE constraint
    _, created = ProcessedWebhookEvent.objects.get_or_create(
        provider="stripe",
        event_id=event_id,
    )

    if not created:
        logger.debug(
            "Skipping already-processed event: provider=stripe event_id=%s type=%s",
            event_id,
            event_type,
        )
        return

    handler = _TIER1_HANDLERS.get(event_type)

    if handler is None:
        logger.debug(
            "Unrecognized Stripe event type — silently acknowledged: %s (event_id=%s)",
            event_type,
            event_id,
        )
        return

    try:
        handler(event_data)
    except Exception as exc:
        # Determine retry countdown with exponential backoff + jitter
        retries = self.request.retries
        countdown = (2**retries) + random.uniform(-1, 1)  # noqa: S311

        if retries >= self.max_retries:
            logger.critical(
                "Stripe event processing failed after max retries: "
                "event_id=%s event_type=%s error=%s",
                event_id,
                event_type,
                exc,
                exc_info=True,
            )
            return

        logger.warning(
            "Retrying Stripe event (attempt %d/%d): event_id=%s event_type=%s error=%s",
            retries + 1,
            self.max_retries,
            event_id,
            event_type,
            exc,
        )
        raise self.retry(exc=exc, countdown=countdown) from exc
