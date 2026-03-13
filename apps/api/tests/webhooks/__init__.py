# Module-level import causes immediate ImportError at collection time
# until apps.webhooks is implemented — this is the intended RED state.
from apps.webhooks.models import (  # noqa: F401
    WebhookDelivery,
    WebhookDeliveryAttempt,
    WebhookEndpoint,
)
