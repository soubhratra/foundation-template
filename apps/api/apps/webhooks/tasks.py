"""Celery tasks for outbound webhook delivery.

deliver_webhook: implemented in Plan 27-03.
This stub exists so fire_webhook_event() in utils.py can import it without error.
"""

from celery import shared_task


@shared_task(
    bind=True,
    max_retries=7,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
)
def deliver_webhook(self, delivery_id: str) -> None:  # type: ignore[no-untyped-def]
    """Deliver a single WebhookDelivery to its endpoint URL.

    Full implementation in Plan 27-03. Stub ensures importability for
    fire_webhook_event() dispatch wiring.
    """
    raise NotImplementedError(  # pragma: no cover
        "deliver_webhook task is not yet implemented — see Plan 27-03."
    )
