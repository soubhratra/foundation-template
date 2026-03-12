"""Public interface for sending transactional emails.

send_email() enqueues a Celery task via transaction.on_commit() so the email
is never dispatched if the calling transaction rolls back.

Usage:
    from apps.notifications.utils import send_email

    send_email(
        to="user@example.com",
        template_name="welcome.html",
        context={"name": "Alice"},
    )
"""

import structlog
from django.db import transaction

logger = structlog.get_logger(__name__)


def send_email(
    to: str,
    template_name: str,
    context: dict,
    *,
    from_email: str | None = None,
    reply_to: str | None = None,
) -> None:
    """Queue a transactional email via Celery after the current transaction commits.

    Email is never sent if the triggering transaction rolls back.
    All context dict values must be JSON-serializable primitives (str, int, bool, list, dict).
    """
    from apps.notifications.tasks import send_email_task

    def enqueue() -> None:
        send_email_task.delay(
            to=to,
            template_name=template_name,
            context=context,
            from_email=from_email,
            reply_to=reply_to,
        )
        logger.info("email_queued", to=to, template_name=template_name)

    try:
        transaction.on_commit(enqueue)
    except RuntimeError:
        # No active DB connection (e.g. during unit tests without @pytest.mark.django_db).
        # In this context, there is no transaction to wait for, so fire immediately.
        enqueue()
