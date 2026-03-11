"""Example periodic task scaffold.

Demonstrates the recommended pattern for scheduled tasks:
- bind=True for access to self (retry, task metadata)
- max_retries with exponential backoff
- Internal _do_work() helper to keep task body testable

Register in CELERY_BEAT_SCHEDULE (settings/base.py) using:
    "task": "apps.core.tasks.example_periodic_task"
"""

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


def _do_work() -> dict:
    """Internal work unit — extracted for testability.

    Replace with real logic in product projects.
    Raises on failure so the task retry logic is exercised.
    """
    logger.info("example_periodic_task: running")
    return {"status": "ok"}


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # seconds; overridden by countdown below
    name="apps.core.tasks.example_periodic_task",
)
def example_periodic_task(self) -> dict:
    """Noop periodic task demonstrating retry + error handling scaffold.

    Pattern:
    1. Delegate work to _do_work() — keeps task body thin and testable
    2. Catch transient errors and retry with exponential backoff
    3. Log both success and failure outcomes via structlog/stdlib logger

    Replace _do_work() contents with real business logic.
    """
    try:
        result = _do_work()
        logger.info("example_periodic_task: completed", extra=result)
        return result
    except Exception as exc:
        logger.warning(
            "example_periodic_task: transient failure, retrying",
            exc_info=exc,
            extra={"retries": self.request.retries},
        )
        # Exponential backoff: 60s, 120s, 240s
        raise self.retry(exc=exc, countdown=60 * (2**self.request.retries)) from exc
