"""GDPR-01: Celery tasks for account management.

delete_user_account — asynchronously deletes a user account and all associated
external records (Stripe customer, PostHog person) in the correct GDPR cascade order.

The task imports BillingService, PaymentAdapter, and ObservabilityAdapter at module
level so tests can patch them via apps.accounts.tasks.* without affecting other modules.
"""

import logging

from celery import shared_task

from apps.billing.services import BillingService
from apps.billing.utils import get_adapter as PaymentAdapter
from apps.core.observability import get_observability_adapter as ObservabilityAdapter

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    default_retry_delay=2,
    name="apps.accounts.tasks.delete_user_account",
)
def delete_user_account(self, user_id: int) -> None:
    """Permanently delete a user account and all associated external records.

    Cascade order (GDPR Article 17):
      1. BillingService.cancel_subscription() — cancel active Stripe sub immediately
      2. PaymentAdapter.delete_customer() — delete Stripe customer object
      3. ObservabilityAdapter.delete_person() — delete PostHog person record
      4. user.delete() — Django ORM cascade for all related tables

    Each step is wrapped in try/except so that downstream steps always run even
    if an upstream step fails. user.delete() is always called last.

    Args:
        user_id: Primary key of the user to delete.
    """
    from django.contrib.auth import get_user_model

    User = get_user_model()

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.warning("delete_user_account: user not found, user_id=%s", user_id)
        return None

    from apps.billing.models import Customer

    # Step 1: Cancel Stripe subscription immediately
    try:
        BillingService().cancel_subscription(user, cancel_at_period_end=False)
    except Exception as exc:
        logger.warning(
            "delete_user_account: cancel_subscription failed user_id=%s error=%s",
            user_id,
            exc,
        )

    # Step 2: Delete Stripe customer object
    try:
        stripe_customer_id = user.billing_customer.stripe_customer_id
        PaymentAdapter().delete_customer(stripe_customer_id)
    except Customer.DoesNotExist:
        pass
    except Exception as exc:
        logger.warning(
            "delete_user_account: delete_customer failed user_id=%s error=%s",
            user_id,
            exc,
        )

    # Step 3: Delete PostHog person record
    try:
        ObservabilityAdapter().delete_person(str(user.pk))
    except Exception as exc:
        logger.warning(
            "delete_user_account: delete_person failed user_id=%s error=%s",
            user_id,
            exc,
        )

    # Step 4: Permanently delete the user — Django ORM cascades all related tables
    user.delete()
    logger.info("delete_user_account: user_id=%s permanently deleted", user_id)
    return None
