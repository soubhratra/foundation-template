"""
@require_active_subscription — gate decorator for subscription-protected views.

Apply to any Django view function or Ninja endpoint. Raises PermissionDenied
(HTTP 403) for users without an active subscription. The existing
permission_denied_handler in config/urls.py formats the response.

Passing statuses: ACTIVE, TRIALING.
Users with cancel_at_period_end=True still pass — they are paid through the period.
Users with no Customer or Subscription record are blocked.
"""

import functools
import logging

from django.core.exceptions import PermissionDenied

from apps.billing.models import SubscriptionStatus

logger = logging.getLogger(__name__)

_PASSING_STATUSES = {SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING}


def require_active_subscription(view_func):
    """Decorator that gates a view behind an active subscription check."""

    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = request.user

        # No Customer record → blocked
        try:
            customer = user.billing_customer
        except Exception:
            logger.debug("require_active_subscription: no Customer for user %s", user.pk)
            raise PermissionDenied("No active subscription.") from None

        # No Subscription record → blocked
        try:
            subscription = customer.subscription
        except Exception:
            logger.debug(
                "require_active_subscription: no Subscription for customer %s",
                customer.pk,
            )
            raise PermissionDenied("No active subscription.") from None

        # Status check — cancel_at_period_end=True with ACTIVE status passes through
        # because status is still ACTIVE. No extra conditional required: when the
        # billing period ends the webhook handler sets status=CANCELED and
        # subsequent requests are then blocked by the check below.
        if subscription.status not in _PASSING_STATUSES:
            logger.debug(
                "require_active_subscription: blocked user %s with status=%s",
                user.pk,
                subscription.status,
            )
            raise PermissionDenied("No active subscription.")

        return view_func(request, *args, **kwargs)

    return wrapper
