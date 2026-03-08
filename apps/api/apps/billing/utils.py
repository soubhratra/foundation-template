"""
Billing utility helpers.

Placed in utils.py (not __init__.py) to avoid circular imports since
webhooks.py and tasks.py both import from here.
"""

from django.conf import settings
from django.utils.module_loading import import_string

from apps.billing.adapters import PaymentAdapter


def get_adapter() -> PaymentAdapter:
    """Resolve and return the configured payment adapter instance.

    The adapter class is resolved via the BILLING_ADAPTER Django setting,
    which must be a dotted path to a PaymentAdapter subclass.

    Example setting:
        BILLING_ADAPTER = "apps.billing.adapters.StripeAdapter"
    """
    adapter_class = import_string(settings.BILLING_ADAPTER)
    return adapter_class()
